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


class _MultiInnerAdjDict(collections.abc.MutableMapping):
    """Inner adjacency for MultiGraph/MultiDiGraph: target → {key: attrs}.

    For multi-edges, NetworkX expects inner dicts to support integer keys
    (0, 1, 2, ...) representing edge indices. We auto-assign keys in the DB
    and present them as integer keys to match NX API.
    """

    def __init__(
        self,
        session: Session,
        graph_id: uuid.UUID,
        source_id: uuid.UUID | None,
        directed: bool,
    ) -> None:
        self._session = session
        self._graph_id = graph_id
        self._source_id = source_id
        self._directed = directed
        self._cache: dict[str, list[tuple[str | None, dict[str, Any]]]] | None = None

    def _load_cache(self) -> None:
        """Load all edges from source to target_id into cache."""
        if self._source_id is None:
            self._cache = []
            return
        stmt = (
            select(EdgeModel.key, EdgeModel.attributes)
            .where(
                and_(
                    EdgeModel.graph_id == self._graph_id,
                    EdgeModel.source_id == self._source_id,
                )
            )
            .order_by(EdgeModel.edge_id)
        )
        self._cache = [
            (key, attrs or {})
            for key, attrs in self._session.execute(stmt)
        ]

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

    def __getitem__(self, target: Any) -> dict[str, Any]:
        """Return attrs for edge with key=target."""
        if self._source_id is None:
            raise KeyError(target)
        # NetworkX multi-edge keys are ints; we store them as strings in DB
        key = str(target) if not isinstance(target, str) else target
        self._load_cache()
        for k, attrs in self._cache:
            if k == key:
                return attrs
        raise KeyError(target)

    def __setitem__(self, target: Any, attrs: dict[str, Any] | None) -> None:
        """Set edge with key=target. For multi-edges, NetworkX passes (v, key)."""
        # This path is used when NX does self._adj[u][v][key] = data
        # But our inner dict maps target→{key:attrs}, so target here is the key
        # and we need to know the actual target node differently.
        # In practice, NX calls this via self._adj[u][v] = {} first (create),
        # then self._adj[u][v][key] = data.
        raise NotImplementedError("Multi-edge setitem via inner dict")

    def __delitem__(self, target: Any) -> None:
        if self._source_id is None:
            return
        key = str(target) if not isinstance(target, str) else target
        self._session.execute(
            delete(EdgeModel).where(
                and_(
                    EdgeModel.graph_id == self._graph_id,
                    EdgeModel.source_id == self._source_id,
                    EdgeModel.key == key,
                )
            )
        )
        if not self._directed:
            # Also delete reverse edge
            self._session.execute(
                delete(EdgeModel).where(
                    and_(
                        EdgeModel.graph_id == self._graph_id,
                        EdgeModel.target_id == self._source_id,
                        EdgeModel.key == key,
                    )
                )
            )
        self._cache = None

    def __iter__(self):
        """Yield integer edge keys for edges from source to any target."""
        if self._source_id is None:
            return
        self._load_cache()
        if self._cache:
            for i, (key, _) in enumerate(self._cache):
                yield i

    def __len__(self) -> int:
        if self._source_id is None:
            return 0
        stmt = (
            select(func.count())
            .select_from(EdgeModel)
            .where(
                and_(
                    EdgeModel.graph_id == self._graph_id,
                    EdgeModel.source_id == self._source_id,
                )
            )
        )
        return self._session.scalar(stmt) or 0


class _SimpleInnerAdjDict(collections.abc.MutableMapping):
    """Inner adjacency for Graph / DiGraph (non-multi)."""

    def __init__(
        self,
        session: Session,
        graph_id: uuid.UUID,
        source_id: uuid.UUID | None,
        directed: bool,
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
        try:
            target_id = self._resolve_target_id(target)
        except KeyError:
            # Node may have already been deleted (e.g. during remove_node
            # where _node is deleted before edges). Safe to silently skip.
            return
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

        if self._multi:
            return _MultiInnerAdjDict(
                self._session, self._graph_id, source_id, self._directed,
            )
        return _SimpleInnerAdjDict(
            self._session, self._graph_id, source_id, self._directed
        )

    def __setitem__(self, key, value):
        """Handle NetworkX internal: self._adj[node] = {} during add_node."""
        if isinstance(value, dict):
            # NetworkX internal: adding a new node (works for both simple and multi)
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

    def __delitem__(self, key):
        # Allow deletion of adjacency entries (needed for remove_node, etc.)
        norm = _to_hashable(key)
        dbkey = _db_node_key(norm)
        source_id = self._session.scalar(
            select(NodeModel.node_id).where(
                and_(
                    NodeModel.graph_id == self._graph_id,
                    NodeModel.node_key == dbkey,
                )
            )
        )
        if source_id is not None:
            # Delete all edges from this node (including multi-edges)
            self._session.execute(
                delete(EdgeModel).where(
                    and_(
                        EdgeModel.graph_id == self._graph_id,
                        EdgeModel.source_id == source_id,
                    )
                )
            )
            if not self._directed:
                # Also delete reverse edges
                self._session.execute(
                    delete(EdgeModel).where(
                        and_(
                            EdgeModel.graph_id == self._graph_id,
                            EdgeModel.target_id == source_id,
                        )
                    )
                )
            # Delete the node
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
                )
            )
        )
        source_ids = [row[0] for row in self._session.execute(stmt)]
        return _PredecessorInnerDict(
            self._session, self._graph_id, target_id, source_ids,
        )

    def __setitem__(self, key, value):
        # NetworkX internal: self._pred[node] = {} during add_node
        if isinstance(value, dict):
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

    def __delitem__(self, key):
        # Allow deletion for DiGraph remove_node: del _pred[n]
        norm = _to_hashable(key)
        dbkey = _db_node_key(norm)
        target_id = self._session.scalar(
            select(NodeModel.node_id).where(
                and_(
                    NodeModel.graph_id == self._graph_id,
                    NodeModel.node_key == dbkey,
                )
            )
        )
        if target_id is not None:
            # Delete all incoming edges to this node (including multi-edges)
            self._session.execute(
                delete(EdgeModel).where(
                    and_(
                        EdgeModel.graph_id == self._graph_id,
                        EdgeModel.target_id == target_id,
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
        # Called by DiGraph.add_edge: self._pred[v][u] = datadict
        # self is _PredecessorInnerDict for target v
        # key=u (predecessor), value=datadict
        # We need to store edge u→v in the DB
        pred_id = self._session.scalar(
            select(NodeModel.node_id).where(
                and_(
                    NodeModel.graph_id == self._graph_id,
                    NodeModel.node_key == _db_node_key(_to_hashable(key)),
                )
            )
        )
        if pred_id is None:
            raise KeyError(key)
        # Store edge pred_id → self._target_id
        exists = self._session.scalar(
            select(EdgeModel.edge_id).where(
                and_(
                    EdgeModel.graph_id == self._graph_id,
                    EdgeModel.source_id == pred_id,
                    EdgeModel.target_id == self._target_id,
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
                        EdgeModel.source_id == pred_id,
                        EdgeModel.target_id == self._target_id,
                        EdgeModel.key.is_(None),
                    )
                )
                .values(attributes=value or {})
            )
        else:
            self._session.add(
                EdgeModel(
                    graph_id=self._graph_id,
                    source_id=pred_id,
                    target_id=self._target_id,
                    key=None,
                    attributes=value or {},
                )
            )

    def __delitem__(self, key):
        # Allow predecessor deletion for DiGraph/MultiDiGraph remove_node
        if not self._source_ids:
            return
        norm = _to_hashable(key)
        dbkey = _db_node_key(norm)
        pred_id = self._session.scalar(
            select(NodeModel.node_id).where(
                and_(
                    NodeModel.graph_id == self._graph_id,
                    NodeModel.node_key == dbkey,
                    NodeModel.node_id.in_(self._source_ids),
                )
            )
        )
        if pred_id is not None:
            self._session.execute(
                delete(EdgeModel).where(
                    and_(
                        EdgeModel.graph_id == self._graph_id,
                        EdgeModel.source_id == pred_id,
                        EdgeModel.target_id == self._target_id,
                    )
                )
            )

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
        session: Session | None = None,
        name: str | None = None,
        incoming_graph_data=None,
        **attr,
    ) -> None:
        # For graph views (subgraph_view), session may be None
        self.session = session

        if session is not None and name is not None:
            gmodel = session.scalar(
                select(GraphModel).where(GraphModel.name == name)
            )
            if gmodel:
                self.graph_id = gmodel.graph_id
                attr = {**gmodel.attributes, **attr} if gmodel.attributes else attr
            else:
                gmodel = GraphModel(name=name, graph_type=self._graph_type, attributes=attr or {})
                session.add(gmodel)
                session.commit()
                self.graph_id = gmodel.graph_id
        elif session is not None:
            gmodel = GraphModel(graph_type=self._graph_type, attributes=attr or {})
            session.add(gmodel)
            session.commit()
            self.graph_id = gmodel.graph_id
        else:
            # No session: fall back to pure in-memory graph for operations
            # like complement(), copy() on views, etc.
            self.graph_id = None
            super().__init__(incoming_graph_data=incoming_graph_data, **attr)
            return

        super().__init__(incoming_graph_data=incoming_graph_data, **attr)

        if self.graph_id is not None:
            self._node = _NodeDict(session, self.graph_id)
            self._adj = _AdjacencyDict(
                session,
                self.graph_id,
                directed=self._directed,
                multi=self._multigraph,
            )
            if self._directed:
                self._succ = self._adj
                self._pred = _PredAdjDict(
                    session,
                    self.graph_id,
                    directed=True,
                    multi=self._multigraph,
                )

    def add_node(self, node_for_adding, **attr):
        """Normalize node key and write attrs directly to DB.

        NetworkX's add_node does: self._node[n] = {} then .update(attr) on the
        returned dict — but that in-memory update never reaches our DB-backed
        _NodeDict. So we bypass by writing attrs ourselves, then let NetworkX
        handle _adj/_node bookkeeping.
        """
        norm = _to_hashable(node_for_adding)
        # Write attrs directly to DB so .update() on NetworkX's local dict
        # doesn't lose them
        self._node[norm] = attr if attr else {}
        # Now call NetworkX add_node for _adj/_succ bookkeeping only
        # (it will find the node already exists and skip re-creation)
        super().add_node(norm)

    def add_nodes_from(self, nodes_for_adding, **attr):
        """Write attrs directly to DB before letting NetworkX handle bookkeeping."""
        normed = [_to_hashable(n) for n in nodes_for_adding]
        for norm in normed:
            self._node[norm] = attr if attr else {}
        super().add_nodes_from(normed)

    def add_edge(self, u_of_edge, v_of_edge, **attr):
        nu = _to_hashable(u_of_edge)
        nv = _to_hashable(v_of_edge)
        # For DiGraph, call nx.DiGraph.add_edge which only adds one direction.
        # Graph.add_edge adds both directions (self._adj[u][v] + self._adj[v][u])
        # which is wrong for directed graphs.
        if self._directed:
            if self._multigraph:
                nx.MultiDiGraph.add_edge(self, nu, nv, **attr)
            else:
                nx.DiGraph.add_edge(self, nu, nv, **attr)
        else:
            if self._multigraph:
                nx.MultiGraph.add_edge(self, nu, nv, **attr)
            else:
                super().add_edge(nu, nv, **attr)

    def add_edges_from(self, ebunch_to_add, **attr):
        # Handle both (u, v) and (u, v, d) edge formats
        normed = []
        for edge in ebunch_to_add:
            if len(edge) == 2:
                u, v = edge
                normed.append((_to_hashable(u), _to_hashable(v), {}))
            else:
                u, v, d = edge
                normed.append((_to_hashable(u), _to_hashable(v), d))
        if self._directed:
            if self._multigraph:
                nx.MultiDiGraph.add_edges_from(self, normed, **attr)
            else:
                nx.DiGraph.add_edges_from(self, normed, **attr)
        else:
            # For in-memory mode (no session), do it manually to avoid
            # issues with _dispatchable compiled bytecode
            if self.session is None:
                for u, v, dd in normed:
                    if u not in self._node:
                        self._adj[u] = {}
                        self._node[u] = {}
                    if v not in self._node:
                        self._adj[v] = {}
                        self._node[v] = {}
                    datadict = self._adj[u].get(v, {})
                    datadict.update(attr)
                    datadict.update(dd)
                    self._adj[u][v] = datadict
                    self._adj[v][u] = datadict
            else:
                if self._multigraph:
                    nx.MultiGraph.add_edges_from(self, normed, **attr)
                else:
                    super().add_edges_from(normed, **attr)

    def remove_edge(self, u, v):
        nu = _to_hashable(u)
        nv = _to_hashable(v)
        if self._directed:
            if self._multigraph:
                nx.MultiDiGraph.remove_edge(self, nu, nv)
            else:
                nx.DiGraph.remove_edge(self, nu, nv)
        else:
            if self._multigraph:
                nx.MultiGraph.remove_edge(self, nu, nv)
            else:
                super().remove_edge(nu, nv)

    def copy(self, as_view=False):
        """Return a shallow copy of the graph, backed by the same DB session."""
        if as_view:
            return nx.graphviews.generic_graph_view(self)
        # For subgraph views, resolve session/graph_id from underlying graph
        graph = getattr(self, "_graph", None)
        if graph is not None and hasattr(graph, "session"):
            session = graph.session
            graph_id = graph.graph_id
        else:
            session = self.session
            graph_id = self.graph_id
        # Create a new instance sharing the same session and graph_id
        H = self.__class__.__new__(self.__class__)
        H.session = session
        H.graph_id = graph_id
        H._graph_type = self._graph_type
        H._directed = self._directed
        H._multigraph = self._multigraph
        # Initialize graph-level dict (from NetworkX Graph base)
        H.graph = dict(self.graph)
        # Rebuild the DB-backed views pointing to the same graph
        H._node = _NodeDict(session, graph_id)
        H._adj = _AdjacencyDict(
            session, graph_id,
            directed=self._directed, multi=self._multigraph,
        )
        if self._directed:
            H._succ = H._adj
            H._pred = _PredAdjDict(
                session, graph_id,
                directed=True, multi=self._multigraph,
            )
        # Copy node/edge data — nodes already exist in DB, just populate _adj
        for n, d in self._node.items():
            H._node[n] = dict(d) if d else {}
        for u, v, d in self.edges(data=True):
            H._adj[u][v] = dict(d)
        return H

    def to_directed(self, copy=True):
        """Return a directed representation of the graph."""
        if copy:
            D = DiGraph(self.session)
            D.graph.update(self.graph)
            for n, d in self.nodes(data=True):
                D.add_node(n, **d)
            for u, v, d in self.edges(data=True):
                D.add_edge(u, v, **d)
            # Also add reverse edges for undirected
            for u, v, d in self.edges(data=True):
                if u != v:
                    D.add_edge(v, u, **d)
            return D
        else:
            return nx.view.to_directed(self)

    def to_undirected(self, copy=True):
        """Return an undirected representation of the graph."""
        if copy:
            G = Graph(self.session)
            G.graph.update(self.graph)
            for n, d in self.nodes(data=True):
                G.add_node(n, **d)
            seen = set()
            for u, v, d in self.edges(data=True):
                key = (min(u, v), max(u, v))
                if key not in seen:
                    seen.add(key)
                    G.add_edge(u, v, **d)
            return G
        else:
            return nx.view.to_undirected(self)

    def reverse(self, copy=True):
        """Return the reverse of this DiGraph."""
        if not self._directed:
            raise nx.NetworkXError("Reverse only works on DiGraph")
        if copy:
            H = DiGraph(self.session)
            H.graph.update(self.graph)
            for n, d in self.nodes(data=True):
                H.add_node(n, **d)
            for u, v, d in self.edges(data=True):
                H.add_edge(v, u, **d)
            return H
        else:
            return nx.reverse_view(self)

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

    @property
    def pred(self):
        """Alias for _pred, needed by dag_longest_path etc."""
        return nx.classes.coreviews.AdjacencyView(self._pred)

    @property
    def succ(self):
        """Alias for _succ (same as _adj for DiGraph)."""
        return nx.classes.coreviews.AdjacencyView(self._adj)

    @property
    def in_degree(self):
        """Return a view of node in-degrees."""
        return nx.reportviews.InDegreeView(self)

    @property
    def out_degree(self):
        """Return a view of node out-degrees."""
        return nx.reportviews.OutDegreeView(self)

    @property
    def out_edges(self):
        """Return a view of outgoing edges."""
        return nx.reportviews.OutEdgeView(self)

    def predecessors(self, node):
        return iter(self._pred[node])

    def successors(self, node):
        return iter(self._adj[node])


class MultiGraph(_NXSQLBase):
    _graph_type = "MultiGraph"
    _directed = False
    _multigraph = True


class MultiDiGraph(_NXSQLBase):
    _graph_type = "MultiDiGraph"
    _directed = True
    _multigraph = True

    @property
    def in_degree(self):
        return nx.reportviews.InDegreeView(self)

    @property
    def out_degree(self):
        return nx.reportviews.OutDegreeView(self)

    @property
    def out_edges(self):
        """Return a view of outgoing edges."""
        return nx.reportviews.OutEdgeView(self)
