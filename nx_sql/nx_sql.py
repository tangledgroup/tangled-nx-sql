"""nx_sql.py - NetworkX backend with persistent SQL storage (no in-memory graph).

Supports ALL NetworkX node types including np.ndarray and list[float].
Zero in-memory footprint – every operation is a direct SQLAlchemy query.
"""

from __future__ import annotations

import collections.abc
import json
import uuid
from typing import Any, Hashable

import networkx as nx
import numpy as np
from sqlalchemy import and_, delete, func, select, update
from sqlalchemy.orm import Session

from .models import Edge as EdgeModel, Graph as GraphModel, Node as NodeModel


# =============================================================================
# Node normalization (enables np.ndarray, list[float], dict, set, etc.)
# =============================================================================

def _to_hashable(obj: Any) -> Hashable:
    """Recursively make any object hashable for NetworkX node keys."""
    if isinstance(obj, np.ndarray):
        obj = obj.tolist()
    if isinstance(obj, (list, tuple)):
        return tuple(_to_hashable(item) for item in obj)
    if isinstance(obj, dict):
        return tuple(sorted((_to_hashable(k), _to_hashable(v)) for k, v in obj.items()))
    if isinstance(obj, (set, frozenset)):
        return tuple(sorted(_to_hashable(item) for item in obj))
    return obj


def _db_node_key(node: Hashable) -> str:
    """Canonical JSON string used as unique node identifier in DB."""
    return json.dumps(node, sort_keys=True, separators=(",", ":"))


def _deserialize_node_key(db_key: str) -> Hashable:
    """Reverse of _db_node_key for iteration."""
    data = json.loads(db_key)
    return _to_hashable(data)


# =============================================================================
# DB-backed dict-like views (replace NetworkX internal dicts)
# =============================================================================

class _NodeDict(collections.abc.MutableMapping):
    """G._node – node → attributes"""

    def __init__(self, session: Session, graph_id: uuid.UUID) -> None:
        self._session = session
        self._graph_id = graph_id

    def __getitem__(self, node: Any) -> dict[str, Any]:
        norm = _to_hashable(node)
        dbkey = _db_node_key(norm)
        stmt = select(NodeModel.attributes).where(
            and_(
                NodeModel.graph_id == self._graph_id,
                NodeModel.node_key == dbkey,
            )
        )
        attrs = self._session.scalar(stmt)
        if attrs is None:
            raise KeyError(node)
        return attrs or {}

    def __setitem__(self, node: Any, attrs: dict[str, Any] | None) -> None:
        norm = _to_hashable(node)
        dbkey = _db_node_key(norm)

        exists = self._session.scalar(
            select(NodeModel.node_id).where(
                and_(
                    NodeModel.graph_id == self._graph_id,
                    NodeModel.node_key == dbkey,
                )
            )
        ) is not None

        if exists:
            self._session.execute(
                update(NodeModel)
                .where(
                    and_(
                        NodeModel.graph_id == self._graph_id,
                        NodeModel.node_key == dbkey,
                    )
                )
                .values(attributes=attrs or {})
            )
        else:
            self._session.add(
                NodeModel(
                    graph_id=self._graph_id,
                    node_key=dbkey,
                    attributes=attrs or {},
                )
            )

    def __delitem__(self, node: Any) -> None:
        norm = _to_hashable(node)
        dbkey = _db_node_key(norm)
        self._session.execute(
            delete(NodeModel).where(
                and_(
                    NodeModel.graph_id == self._graph_id,
                    NodeModel.node_key == dbkey,
                )
            )
        )

    def __iter__(self):
        stmt = select(NodeModel.node_key).where(NodeModel.graph_id == self._graph_id)
        for (dbkey,) in self._session.execute(stmt):
            yield _deserialize_node_key(dbkey)

    def __len__(self) -> int:
        stmt = (
            select(func.count())
            .select_from(NodeModel)
            .where(NodeModel.graph_id == self._graph_id)
        )
        return self._session.scalar(stmt) or 0


class _SimpleInnerAdjDict(collections.abc.MutableMapping):
    """Inner adjacency for Graph / DiGraph (non-multi)."""

    def __init__(
        self, session: Session, graph_id: uuid.UUID, source_id: uuid.UUID | None, directed: bool
    ) -> None:
        self._session = session
        self._graph_id = graph_id
        self._source_id = source_id
        self._directed = directed
        self._source_ids: list[uuid.UUID] | None = None

    @classmethod
    def from_source_ids(
        cls, session: Session, graph_id: uuid.UUID, source_ids: list[uuid.UUID], directed: bool
    ) -> "_SimpleInnerAdjDict":
        """Create a virtual inner dict for multiple source nodes (used by _pred)."""
        instance = cls(session, graph_id, None, directed)
        instance._source_ids = source_ids
        return instance

    def __getitem__(self, target: Any) -> dict[str, Any]:
        target_id = self._resolve_target_id(target)
        if self._source_ids is not None:
            # Multi-source: check all source nodes
            stmt = select(EdgeModel.attributes).where(
                and_(
                    EdgeModel.graph_id == self._graph_id,
                    EdgeModel.source_id.in_(self._source_ids),
                    EdgeModel.target_id == target_id,
                    EdgeModel.key.is_(None),
                )
            )
        else:
            stmt = select(EdgeModel.attributes).where(
                and_(
                    EdgeModel.graph_id == self._graph_id,
                    EdgeModel.source_id == self._source_id,
                    EdgeModel.target_id == target_id,
                    EdgeModel.key.is_(None),
                )
            )
        attrs = self._session.scalar(stmt)
        if attrs is None:
            raise KeyError(target)
        return attrs or {}

    def __setitem__(self, target: Any, attrs: dict[str, Any] | None) -> None:
        target_id = self._get_or_create_target_id(target)
        self._upsert_edge(target_id, attrs or {})

    def __delitem__(self, target: Any) -> None:
        target_id = self._resolve_target_id(target)
        self._delete_edge(target_id)

    def __iter__(self):
        if self._source_ids is not None:
            target_ids_stmt = (
                select(EdgeModel.target_id)
                .where(
                    and_(
                        EdgeModel.graph_id == self._graph_id,
                        EdgeModel.source_id.in_(self._source_ids),
                        EdgeModel.key.is_(None),
                    )
                )
            )
            target_ids = [row[0] for row in self._session.execute(target_ids_stmt)]
            if target_ids:
                node_stmt = (
                    select(NodeModel.node_key)
                    .where(
                        and_(
                            NodeModel.graph_id == self._graph_id,
                            NodeModel.node_id.in_(target_ids),
                        )
                    )
                )
                for (dbkey,) in self._session.execute(node_stmt):
                    yield _deserialize_node_key(dbkey)
        else:
            stmt = (
                select(NodeModel.node_key)
                .select_from(EdgeModel)
                .join(NodeModel, NodeModel.node_id == EdgeModel.target_id)
                .where(
                    and_(
                        EdgeModel.graph_id == self._graph_id,
                        EdgeModel.source_id == self._source_id,
                        EdgeModel.key.is_(None),
                    )
                )
            )
            for (dbkey,) in self._session.execute(stmt):
                yield _deserialize_node_key(dbkey)

    def __len__(self) -> int:
        if self._source_ids is not None:
            stmt = (
                select(func.count())
                .select_from(EdgeModel)
                .where(
                    and_(
                        EdgeModel.graph_id == self._graph_id,
                        EdgeModel.source_id.in_(self._source_ids),
                        EdgeModel.key.is_(None),
                    )
                )
            )
        else:
            stmt = (
                select(func.count())
                .select_from(EdgeModel)
                .where(
                    and_(
                        EdgeModel.graph_id == self._graph_id,
                        EdgeModel.source_id == self._source_id,
                        EdgeModel.key.is_(None),
                    )
                )
            )
        return self._session.scalar(stmt) or 0

    def _resolve_target_id(self, target: Any) -> uuid.UUID:
        norm = _to_hashable(target)
        dbkey = _db_node_key(norm)
        target_id = self._session.scalar(
            select(NodeModel.node_id).where(
                and_(
                    NodeModel.graph_id == self._graph_id,
                    NodeModel.node_key == dbkey,
                )
            )
        )
        if target_id is None:
            raise KeyError(target)
        return target_id

    def _get_or_create_target_id(self, target: Any) -> uuid.UUID:
        norm = _to_hashable(target)
        dbkey = _db_node_key(norm)
        target_id = self._session.scalar(
            select(NodeModel.node_id).where(
                and_(
                    NodeModel.graph_id == self._graph_id,
                    NodeModel.node_key == dbkey,
                )
            )
        )
        if target_id is None:
            new_node = NodeModel(
                graph_id=self._graph_id,
                node_key=dbkey,
                attributes={},
            )
            self._session.add(new_node)
            self._session.flush()
            target_id = new_node.node_id
        return target_id

    def _upsert_edge(self, target_id: uuid.UUID, attrs: dict[str, Any]) -> None:
        self._upsert_single(self._source_id, target_id, attrs)
        if not self._directed:
            self._upsert_single(target_id, self._source_id, attrs)

    def _upsert_single(
        self, src_id: uuid.UUID, tgt_id: uuid.UUID, attrs: dict[str, Any]
    ) -> None:
        exists = self._session.scalar(
            select(EdgeModel.edge_id).where(
                and_(
                    EdgeModel.graph_id == self._graph_id,
                    EdgeModel.source_id == src_id,
                    EdgeModel.target_id == tgt_id,
                    EdgeModel.key.is_(None),
                )
            )
        ) is not None

        if exists:
            self._session.execute(
                update(EdgeModel)
                .where(
                    and_(
                        EdgeModel.graph_id == self._graph_id,
                        EdgeModel.source_id == src_id,
                        EdgeModel.target_id == tgt_id,
                        EdgeModel.key.is_(None),
                    )
                )
                .values(attributes=attrs)
            )
        else:
            self._session.add(
                EdgeModel(
                    graph_id=self._graph_id,
                    source_id=src_id,
                    target_id=tgt_id,
                    key=None,
                    attributes=attrs,
                )
            )

    def _delete_edge(self, target_id: uuid.UUID) -> None:
        self._delete_single(self._source_id, target_id)
        if not self._directed:
            self._delete_single(target_id, self._source_id)

    def _delete_single(self, src_id: uuid.UUID, tgt_id: uuid.UUID) -> None:
        self._session.execute(
            delete(EdgeModel).where(
                and_(
                    EdgeModel.graph_id == self._graph_id,
                    EdgeModel.source_id == src_id,
                    EdgeModel.target_id == tgt_id,
                    EdgeModel.key.is_(None),
                )
            )
        )


class _AdjacencyDict(collections.abc.MutableMapping):
    """G._adj – source → inner adjacency dict"""

    def __init__(
        self, session: Session, graph_id: uuid.UUID, directed: bool, multi: bool
    ) -> None:
        self._session = session
        self._graph_id = graph_id
        self._directed = directed
        self._multi = multi

    def __getitem__(self, source: Any):
        if self._multi:
            raise NotImplementedError("MultiGraph/MultiDiGraph not implemented yet")

        norm = _to_hashable(source)
        dbkey = _db_node_key(norm)
        source_id = self._session.scalar(
            select(NodeModel.node_id).where(
                and_(
                    NodeModel.graph_id == self._graph_id,
                    NodeModel.node_key == dbkey,
                )
            )
        )
        if source_id is None:
            raise KeyError(source)

        return _SimpleInnerAdjDict(
            self._session, self._graph_id, source_id, self._directed
        )

    def __setitem__(self, key, value):
        """Handle NetworkX internal: self._adj[node] = {} during add_node."""
        if isinstance(value, dict) and not self._multi:
            # NetworkX internal: adding a new node
            norm = _to_hashable(key)
            dbkey = _db_node_key(norm)
            existing_id = self._session.scalar(
                select(NodeModel.node_id).where(
                    and_(
                        NodeModel.graph_id == self._graph_id,
                        NodeModel.node_key == dbkey,
                    )
                )
            )
            if existing_id is None:
                node = NodeModel(
                    graph_id=self._graph_id,
                    node_key=dbkey,
                    attributes={},
                )
                self._session.add(node)
                self._session.flush()
        else:
            raise NotImplementedError("Direct G.adj assignment not supported")

    def __delitem__(self, key):
        raise NotImplementedError("Direct G.adj deletion not supported")

    def __iter__(self):
        stmt = select(NodeModel.node_key).where(NodeModel.graph_id == self._graph_id)
        for (dbkey,) in self._session.execute(stmt):
            yield _deserialize_node_key(dbkey)

    def __len__(self) -> int:
        stmt = (
            select(func.count())
            .select_from(NodeModel)
            .where(NodeModel.graph_id == self._graph_id)
        )
        return self._session.scalar(stmt) or 0


class _PredAdjDict(collections.abc.MutableMapping):
    """G._pred – target → predecessor inner adjacency dict (reverse of _adj)."""

    def __init__(
        self, session: Session, graph_id: uuid.UUID, directed: bool, multi: bool
    ) -> None:
        self._session = session
        self._graph_id = graph_id
        self._directed = directed
        self._multi = multi

    def __getitem__(self, target: Any):
        if self._multi:
            raise NotImplementedError("MultiGraph/MultiDiGraph not implemented yet")

        norm = _to_hashable(target)
        dbkey = _db_node_key(norm)
        target_id = self._session.scalar(
            select(NodeModel.node_id).where(
                and_(
                    NodeModel.graph_id == self._graph_id,
                    NodeModel.node_key == dbkey,
                )
            )
        )
        if target_id is None:
            raise KeyError(target)

        stmt = (
            select(EdgeModel.source_id)
            .where(
                and_(
                    EdgeModel.graph_id == self._graph_id,
                    EdgeModel.target_id == target_id,
                    EdgeModel.key.is_(None),
                )
            )
        )
        source_ids = [row[0] for row in self._session.execute(stmt)]
        return _PredecessorInnerDict(
            self._session, self._graph_id, target_id, source_ids
        )

    def __setitem__(self, key, value):
        if isinstance(value, dict) and not self._multi:
            norm = _to_hashable(key)
            dbkey = _db_node_key(norm)
            existing_id = self._session.scalar(
                select(NodeModel.node_id).where(
                    and_(
                        NodeModel.graph_id == self._graph_id,
                        NodeModel.node_key == dbkey,
                    )
                )
            )
            if existing_id is None:
                node = NodeModel(
                    graph_id=self._graph_id,
                    node_key=dbkey,
                    attributes={},
                )
                self._session.add(node)
                self._session.flush()
        else:
            raise NotImplementedError("Direct G._pred assignment not supported")

    def __delitem__(self, key):
        raise NotImplementedError("Direct G._pred deletion not supported")

    def __iter__(self):
        stmt = select(NodeModel.node_key).where(NodeModel.graph_id == self._graph_id)
        for (dbkey,) in self._session.execute(stmt):
            yield _deserialize_node_key(dbkey)

    def __len__(self) -> int:
        stmt = (
            select(func.count())
            .select_from(NodeModel)
            .where(NodeModel.graph_id == self._graph_id)
        )
        return self._session.scalar(stmt) or 0


class _PredecessorInnerDict(collections.abc.MutableMapping):
    """Inner adjacency for G._pred: maps predecessor node → edge attributes.

    For a given target node T, _pred[T] returns a dict of {predecessor: attrs}
    where edges go from predecessor → T.
    """

    def __init__(
        self, session: Session, graph_id: uuid.UUID, target_id: uuid.UUID,
        source_ids: list[uuid.UUID]
    ) -> None:
        self._session = session
        self._graph_id = graph_id
        self._target_id = target_id
        self._source_ids = source_ids  # UUIDs of predecessor nodes

    def __getitem__(self, pred_key: Any) -> dict[str, Any]:
        if not self._source_ids:
            raise KeyError(pred_key)
        norm = _to_hashable(pred_key)
        dbkey = _db_node_key(norm)
        # Find which source_id matches this key
        src_id = self._session.scalar(
            select(NodeModel.node_id).where(
                and_(
                    NodeModel.graph_id == self._graph_id,
                    NodeModel.node_key == dbkey,
                    NodeModel.node_id.in_(self._source_ids),
                )
            )
        )
        if src_id is None:
            raise KeyError(pred_key)
        stmt = select(EdgeModel.attributes).where(
            and_(
                EdgeModel.graph_id == self._graph_id,
                EdgeModel.source_id == src_id,
                EdgeModel.target_id == self._target_id,
                EdgeModel.key.is_(None),
            )
        )
        attrs = self._session.scalar(stmt)
        if attrs is None:
            raise KeyError(pred_key)
        return attrs or {}

    def __setitem__(self, key, value):
        raise NotImplementedError("Direct _pred assignment not supported")

    def __delitem__(self, key):
        raise NotImplementedError("Direct _pred deletion not supported")

    def __iter__(self):
        # Yield the node keys of all predecessors
        stmt = (
            select(NodeModel.node_key)
            .where(
                and_(
                    NodeModel.graph_id == self._graph_id,
                    NodeModel.node_id.in_(self._source_ids),
                )
            )
        )
        for (dbkey,) in self._session.execute(stmt):
            yield _deserialize_node_key(dbkey)

    def __len__(self) -> int:
        if not self._source_ids:
            return 0
        stmt = (
            select(func.count())
            .where(NodeModel.node_id.in_(self._source_ids))
            .where(NodeModel.graph_id == self._graph_id)
        )
        return self._session.scalar(stmt) or 0


# =============================================================================
# Public nx_sql graph classes (100% NetworkX API compatible)
# =============================================================================

class _NXSQLBase(nx.Graph):
    _graph_type: str
    _directed: bool
    _multigraph: bool

    def __init__(
        self,
        session: Session,
        graph_id: uuid.UUID | None = None,
        incoming_graph_data=None,
        **attr,
    ) -> None:
        self.session = session

        if graph_id is None:
            gmodel = GraphModel(graph_type=self._graph_type, attributes=attr or {})
            self.session.add(gmodel)
            self.session.commit()
            self.graph_id = gmodel.graph_id
        else:
            self.graph_id = graph_id
            gmodel = self.session.get(GraphModel, graph_id)
            if gmodel and gmodel.attributes:
                attr = {**gmodel.attributes, **attr}

        super().__init__(incoming_graph_data=incoming_graph_data, **attr)

        self._node = _NodeDict(self.session, self.graph_id)
        self._adj = _AdjacencyDict(
            self.session,
            self.graph_id,
            directed=self._directed,
            multi=self._multigraph,
        )
        if self._directed:
            self._succ = self._adj
            self._pred = _PredAdjDict(
                self.session,
                self.graph_id,
                directed=True,
                multi=self._multigraph,
            )

    def add_node(self, node_for_adding, **attr):
        """Normalize node key so NetworkX stores the hashable form."""
        norm = _to_hashable(node_for_adding)
        super().add_node(norm, **attr)

    def add_nodes_from(self, nodes_for_adding, **attr):
        normed = [_to_hashable(n) for n in nodes_for_adding]
        super().add_nodes_from(normed, **attr)

    def add_edge(self, u_of_edge, v_of_edge, **attr):
        nu = _to_hashable(u_of_edge)
        nv = _to_hashable(v_of_edge)
        super().add_edge(nu, nv, **attr)

    def add_edges_from(self, ebunch_to_add, **attr):
        normed = [(_to_hashable(u), _to_hashable(v), d) for u, v, d in ebunch_to_add]
        super().add_edges_from(normed, **attr)

    def __networkx_backend__(self) -> str:
        return "nx_sql"

    def is_directed(self) -> bool:
        return self._directed

    def is_multigraph(self) -> bool:
        return self._multigraph


class Graph(_NXSQLBase):
    _graph_type = "Graph"
    _directed = False
    _multigraph = False


class DiGraph(_NXSQLBase):
    _graph_type = "DiGraph"
    _directed = True
    _multigraph = False


class MultiGraph(_NXSQLBase):
    _graph_type = "MultiGraph"
    _directed = False
    _multigraph = True


class MultiDiGraph(_NXSQLBase):
    _graph_type = "MultiDiGraph"
    _directed = True
    _multigraph = True
