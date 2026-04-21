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
            # Check if this is an empty dict (NetworkX internal initialization)
            # or a real update. If attrs is empty, we still need to handle the case
            # where NetworkX will do attr_dict.update(attr) right after.
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
        self, session: Session, graph_id: uuid.UUID, source_id: uuid.UUID, directed: bool
    ) -> None:
        self._session = session
        self._graph_id = graph_id
        self._source_id = source_id
        self._directed = directed

    def __getitem__(self, target: Any) -> dict[str, Any]:
        target_id = self._resolve_target_id(target)
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


class _PredAdjacencyDict(collections.abc.MutableMapping):
    """G._pred – predecessor adjacency for DiGraph.

    For a directed edge u -> v, node v has u as a predecessor.
    This is the reverse view of _adj (successors).
    """

    def __init__(self, session: Session, graph_id: uuid.UUID) -> None:
        self._session = session
        self._graph_id = graph_id

    def __getitem__(self, source: Any) -> dict[str, Any]:
        """Get predecessors of source node."""
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

        # Find all edges where target_id == source_id (i.e., predecessors)
        stmt = select(EdgeModel.attributes, EdgeModel.source_id).where(
            and_(
                EdgeModel.graph_id == self._graph_id,
                EdgeModel.target_id == source_id,
                EdgeModel.key.is_(None),
            )
        )
        result: dict[str, Any] = {}
        for attrs, src_id in self._session.execute(stmt):
            # Get the node key for this predecessor
            node_stmt = select(NodeModel.node_key).where(
                and_(
                    NodeModel.graph_id == self._graph_id,
                    NodeModel.node_id == src_id,
                )
            )
            (node_dbkey,) = self._session.execute(node_stmt).one()
            pred_node = _deserialize_node_key(node_dbkey)
            result[pred_node] = attrs or {}
        return result

    def __setitem__(self, key, value):
        """Handle NetworkX internal: self._pred[node] = {} during add_node."""
        if isinstance(value, dict):
            norm = _to_hashable(key)
            dbkey = _db_node_key(norm)
            # Ensure the node exists in DB
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
        raise NotImplementedError("Direct G._pred deletion not supported")

    def __iter__(self):
        """Iterate over all nodes (predecessors exist for all nodes that have incoming edges)."""
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
    """Inner adjacency for MultiGraph/MultiDiGraph.

    Maps target → {key: edge_data} where key is an int edge identifier.
    Each edge is stored as a separate EdgeModel row with a unique key.
    """

    def __init__(
        self, session: Session, graph_id: uuid.UUID, source_id: uuid.UUID, directed: bool
    ) -> None:
        self._session = session
        self._graph_id = graph_id
        self._source_id = source_id
        self._directed = directed

    def __getitem__(self, target: Any) -> dict[str, Any]:
        target_id = self._resolve_target_id(target)
        stmt = select(EdgeModel.attributes, EdgeModel.key).where(
            and_(
                EdgeModel.graph_id == self._graph_id,
                EdgeModel.source_id == self._source_id,
                EdgeModel.target_id == target_id,
            )
        )
        result: dict[str, Any] = {}
        for attrs, key in self._session.execute(stmt):
            k = int(key) if key is not None else 0
            result[k] = attrs or {}
        return result

    def __setitem__(self, target: Any, attrs: dict[str, Any]) -> None:
        """Not used directly in multi-graph add_edge flow."""
        raise NotImplementedError("Use add_edge with key parameter for MultiGraph")

    def __delitem__(self, target: Any) -> None:
        """Delete all edges between source and target."""
        target_id = self._resolve_target_id(target)
        self._session.execute(
            delete(EdgeModel).where(
                and_(
                    EdgeModel.graph_id == self._graph_id,
                    EdgeModel.source_id == self._source_id,
                    EdgeModel.target_id == target_id,
                )
            )
        )
        if not self._directed:
            # Also remove reverse edges
            target_node_stmt = select(NodeModel.node_id).where(
                and_(
                    NodeModel.graph_id == self._graph_id,
                    NodeModel.node_key == _db_node_key(_to_hashable(target)),
                )
            )
            tid = self._session.scalar(target_node_stmt)
            if tid:
                self._session.execute(
                    delete(EdgeModel).where(
                        and_(
                            EdgeModel.graph_id == self._graph_id,
                            EdgeModel.source_id == tid,
                            EdgeModel.target_id == self._source_id,
                        )
                    )
                )

    def __iter__(self):
        stmt = (
            select(NodeModel.node_key)
            .select_from(EdgeModel)
            .join(NodeModel, NodeModel.node_id == EdgeModel.target_id)
            .where(
                and_(
                    EdgeModel.graph_id == self._graph_id,
                    EdgeModel.source_id == self._source_id,
                )
            )
        )
        for (dbkey,) in self._session.execute(stmt):
            yield _deserialize_node_key(dbkey)

    def __len__(self) -> int:
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

    def __contains__(self, target: Any) -> bool:
        try:
            self._resolve_target_id(target)
            return True
        except KeyError:
            return False

    def get(self, target, default=None):
        try:
            return self[target]
        except KeyError:
            return default

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

    def _upsert_edge(self, target: Any, key: int, attrs: dict[str, Any]) -> uuid.UUID:
        """Add or update a multi-edge. Returns the edge's source_id (self._source_id)."""
        target_id = self._get_or_create_target_id(target)

        # Check if edge with this key already exists
        existing = self._session.scalar(
            select(EdgeModel.edge_id).where(
                and_(
                    EdgeModel.graph_id == self._graph_id,
                    EdgeModel.source_id == self._source_id,
                    EdgeModel.target_id == target_id,
                    EdgeModel.key == str(key),
                )
            )
        ) is not None

        if existing:
            self._session.execute(
                update(EdgeModel)
                .where(
                    and_(
                        EdgeModel.graph_id == self._graph_id,
                        EdgeModel.source_id == self._source_id,
                        EdgeModel.target_id == target_id,
                        EdgeModel.key == str(key),
                    )
                )
                .values(attributes=attrs)
            )
        else:
            self._session.add(
                EdgeModel(
                    graph_id=self._graph_id,
                    source_id=self._source_id,
                    target_id=target_id,
                    key=str(key),
                    attributes=attrs,
                )
            )

        # For undirected graphs, also add reverse edge
        if not self._directed:
            self._session.add(
                EdgeModel(
                    graph_id=self._graph_id,
                    source_id=target_id,
                    target_id=self._source_id,
                    key=str(key),
                    attributes=attrs,
                )
            )

        return self._source_id


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
                self._session, self._graph_id, source_id, self._directed
            )

        return _SimpleInnerAdjDict(
            self._session, self._graph_id, source_id, self._directed
        )

    def __setitem__(self, key, value):
        """Handle NetworkX internal: self._adj[node] = {} during add_node."""
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
        graph_id: uuid.UUID | None = None,
        incoming_graph_data=None,
        name: str | None = None,
        **attr,
    ) -> None:
        # Allow session=None for reverse()/copy() operations that create
        # temporary in-memory graphs
        self.session = session

        if session is None:
            # In-memory mode: just use parent class fully
            init_attr = {**(attr or {})}
            if name is not None:
                init_attr["name"] = name
            super().__init__(incoming_graph_data=incoming_graph_data, **init_attr)
            return

        if graph_id is None:
            # Try to load by name for persistent reuse
            existing = None
            if name is not None:
                existing = self.session.scalar(
                    select(GraphModel).where(GraphModel.name == name)
                )
            if existing:
                self.graph_id = existing.graph_id
                if existing.attributes:
                    attr = {**existing.attributes, **(attr or {})}
            else:
                all_attrs = {**(attr or {})}
                if name is not None:
                    all_attrs["name"] = name
                gmodel = GraphModel(
                    graph_type=self._graph_type,
                    name=name,
                    attributes=all_attrs or None,
                )
                self.session.add(gmodel)
                self.session.commit()
                self.graph_id = gmodel.graph_id
        else:
            self.graph_id = graph_id
            gmodel = self.session.get(GraphModel, graph_id)
            if gmodel and gmodel.attributes:
                attr = {**gmodel.attributes, **attr}

        init_attr = {**(attr or {})}
        if name is not None:
            init_attr["name"] = name
        super().__init__(incoming_graph_data=incoming_graph_data, **init_attr)

        self._node = _NodeDict(self.session, self.graph_id)
        self._adj = _AdjacencyDict(
            self.session,
            self.graph_id,
            directed=self._directed,
            multi=self._multigraph,
        )

        # DiGraph compatibility: NetworkX algorithms access G._succ and G._pred directly
        if self._directed:
            self._succ = self._adj  # type: ignore[misc]
            self._pred = _PredAdjacencyDict(
                self.session,
                self.graph_id,
            )

    def add_node(self, node_for_adding, **attr):
        """Normalize node key and persist attributes directly to DB."""
        if self.session is None:
            return super().add_node(node_for_adding, **attr)
        norm = _to_hashable(node_for_adding)
        if norm is node_for_adding and attr:
            # Normalization didn't change the node — update in-place via parent
            if node_for_adding not in self._node:
                pass  # Will be created by super()
            else:
                self._node[node_for_adding].update(attr)
                return
        if attr:
            # Bypass NetworkX's pattern of creating empty dict then updating in-memory.
            # Write attrs directly to DB so they're persisted on add_node call.
            dbkey = _db_node_key(norm)
            existing_id = self.session.scalar(
                select(NodeModel.node_id).where(
                    and_(
                        NodeModel.graph_id == self.graph_id,
                        NodeModel.node_key == dbkey,
                    )
                )
            )
            if existing_id is not None:
                # Node exists — update attributes
                self.session.execute(
                    update(NodeModel)
                    .where(
                        and_(
                            NodeModel.graph_id == self.graph_id,
                            NodeModel.node_key == dbkey,
                        )
                    )
                    .values(attributes={**self._node[norm], **attr})
                )
            else:
                # New node — create with attrs
                node = NodeModel(
                    graph_id=self.graph_id,
                    node_key=dbkey,
                    attributes=attr,
                )
                self.session.add(node)
                self.session.flush()
        super().add_node(norm, **attr)

    def add_nodes_from(self, nodes_for_adding, **attr):
        if self.session is None:
            return super().add_nodes_from(nodes_for_adding, **attr)
        normed = [_to_hashable(n) for n in nodes_for_adding]
        super().add_nodes_from(normed, **attr)

    def add_edge(self, u_of_edge, v_of_edge, **attr):
        nu = _to_hashable(u_of_edge)
        nv = _to_hashable(v_of_edge)
        if self._multigraph:
            key = attr.pop('key', None)
            self._add_multi_edge(nu, nv, key, attr, {})
        elif self._directed:
            # DiGraph: add only one direction, no reverse edge
            for node_key in (nu, nv):
                if node_key not in self._node:
                    if node_key is None:
                        raise nx.NetworkXError("None cannot be a node")
                    self._adj[node_key] = {}
            datadict = self._adj[nu].get(nv, {})
            datadict.update(attr)
            self._adj[nu][nv] = datadict
        else:
            super().add_edge(nu, nv, **attr)

    def add_edges_from(self, ebunch_to_add, **attr):
        if self._multigraph:
            for e in ebunch_to_add:
                ne = len(e)
                if ne == 2:
                    u, v = e
                    dd: dict[str, Any] = {}
                    key = None
                elif ne == 3:
                    u, v, third = e
                    if isinstance(third, dict):
                        dd = third
                        key = None
                    else:
                        dd = {"weight": third}
                        key = None
                elif ne == 4:
                    u, v, key, dd = e
                    if not isinstance(dd, dict):
                        dd = {"weight": dd}
                else:
                    raise nx.NetworkXError(f"Edge tuple {e} must be a 2/3/4-tuple.")
                nu = _to_hashable(u)
                nv = _to_hashable(v)
                self._add_multi_edge(nu, nv, key, dd, attr)
        elif self._directed:
            # DiGraph: add only one direction per edge
            for e in ebunch_to_add:
                ne = len(e)
                if ne == 2:
                    u, v = e
                    dd: dict[str, Any] = {}
                elif ne == 3:
                    u, v, dd = e
                    if not isinstance(dd, dict):
                        dd = {"weight": dd} if "weight" not in attr else dd
                else:
                    raise nx.NetworkXError(f"Edge tuple {e} must be a 2-tuple or 3-tuple.")
                nu = _to_hashable(u)
                nv = _to_hashable(v)
                # Ensure nodes exist
                if nu not in self._node:
                    self._adj[nu] = {}
                if nv not in self._node:
                    self._adj[nv] = {}
                datadict = self._adj[nu].get(nv, {})
                datadict.update(dd)
                datadict.update(attr)
                self._adj[nu][nv] = datadict
        else:
            normed = []
            for e in ebunch_to_add:
                ne = len(e)
                if ne == 2:
                    u, v = e
                    dd: dict[str, Any] = {}
                elif ne == 3:
                    u, v, dd = e
                    if not isinstance(dd, dict):
                        dd = {"weight": dd} if "weight" not in attr else dd
                else:
                    raise nx.NetworkXError(f"Edge tuple {e} must be a 2-tuple or 3-tuple.")
                normed.append((_to_hashable(u), _to_hashable(v), dd))
            super().add_edges_from(normed, **attr)

    def _add_multi_edge(self, u: Any, v: Any, key, dd: dict[str, Any], attr: dict):
        """Add a single multi-edge without going through parent class."""
        combined = {**dd, **attr}

        # Ensure nodes exist
        if u not in self._node:
            self._node[u] = {}
        if v not in self._node:
            self._node[v] = {}

        # Get source node id
        src_dbkey = _db_node_key(u)
        src_id = self.session.scalar(
            select(NodeModel.node_id).where(
                and_(NodeModel.graph_id == self.graph_id, NodeModel.node_key == src_dbkey)
            )
        )

        # Get or create target node
        tgt_dbkey = _db_node_key(v)
        tgt_id = self.session.scalar(
            select(NodeModel.node_id).where(
                and_(NodeModel.graph_id == self.graph_id, NodeModel.node_key == tgt_dbkey)
            )
        )
        if tgt_id is None:
            new_node = NodeModel(graph_id=self.graph_id, node_key=tgt_dbkey, attributes={})
            self.session.add(new_node)
            self.session.flush()
            tgt_id = new_node.node_id

        # Determine key
        if key is None:
            key = self.new_edge_key(u, v)
        key_str = str(key)

        # Check existing edge with this key
        existing = self.session.scalar(
            select(EdgeModel.edge_id).where(
                and_(
                    EdgeModel.graph_id == self.graph_id,
                    EdgeModel.source_id == src_id,
                    EdgeModel.target_id == tgt_id,
                    EdgeModel.key == key_str,
                )
            )
        ) is not None

        if existing:
            self.session.execute(
                update(EdgeModel)
                .where(
                    and_(
                        EdgeModel.graph_id == self.graph_id,
                        EdgeModel.source_id == src_id,
                        EdgeModel.target_id == tgt_id,
                        EdgeModel.key == key_str,
                    )
                )
                .values(attributes=combined)
            )
        else:
            self.session.add(
                EdgeModel(
                    graph_id=self.graph_id,
                    source_id=src_id,
                    target_id=tgt_id,
                    key=key_str,
                    attributes=combined,
                )
            )

        # For undirected, add reverse
        if not self._directed:
            existing_rev = self.session.scalar(
                select(EdgeModel.edge_id).where(
                    and_(
                        EdgeModel.graph_id == self.graph_id,
                        EdgeModel.source_id == tgt_id,
                        EdgeModel.target_id == src_id,
                        EdgeModel.key == key_str,
                    )
                )
            ) is not None
            if existing_rev:
                self.session.execute(
                    update(EdgeModel)
                    .where(
                        and_(
                            EdgeModel.graph_id == self.graph_id,
                            EdgeModel.source_id == tgt_id,
                            EdgeModel.target_id == src_id,
                            EdgeModel.key == key_str,
                        )
                    )
                    .values(attributes=combined)
                )
            else:
                self.session.add(
                    EdgeModel(
                        graph_id=self.graph_id,
                        source_id=tgt_id,
                        target_id=src_id,
                        key=key_str,
                        attributes=combined,
                    )
                )

        # Update in-memory adjacency
        self._adj[u][v][key] = combined
        if not self._directed:
            self._adj[v][u][key] = combined

    def __networkx_backend__(self) -> str:
        return "nx_sql"

    def is_directed(self) -> bool:
        return self._directed

    def is_multigraph(self) -> bool:
        return self._multigraph

    def delete(self) -> None:
        """Delete this graph and all its nodes and edges from the DB."""
        if self.session is None or not hasattr(self, 'graph_id'):
            return
        gid = self.graph_id
        self.session.execute(
            delete(NodeModel).where(NodeModel.graph_id == gid)
        )
        self.session.execute(
            delete(EdgeModel).where(EdgeModel.graph_id == gid)
        )
        self.session.execute(
            delete(GraphModel).where(GraphModel.graph_id == gid)
        )
        self.session.commit()


class Graph(_NXSQLBase, nx.Graph):
    _graph_type = "Graph"
    _directed = False
    _multigraph = False


class DiGraph(_NXSQLBase, nx.DiGraph):
    _graph_type = "DiGraph"
    _directed = True
    _multigraph = False

    def successors(self, n: Any):
        """Returns an iterator over successor nodes of n."""
        try:
            return iter(self._succ[n])
        except KeyError as err:
            raise nx.NetworkXError(f"The node {n} is not in the digraph.") from err

    def predecessors(self, n: Any):
        """Returns an iterator over predecessor nodes of n."""
        try:
            return iter(self._pred[n])
        except KeyError as err:
            raise nx.NetworkXError(f"The node {n} is not in the digraph.") from err

    def has_successor(self, u: Any, v: Any) -> bool:
        """Return True if u has a directed edge to v."""
        return u in self._succ and v in self._succ[u]

    def has_predecessor(self, u: Any, v: Any) -> bool:
        """Return True if v has a directed edge to u."""
        return u in self._pred and v in self._pred[u]

    def out_edges(self, nbunch=None, data=False, default=None):
        """Return edges outgoing from node(s)."""
        if nbunch is None:
            result = []
            for n in self._succ:
                for m, d in self._succ[n].items():
                    if data:
                        result.append((n, m, dict(d)))
                    else:
                        result.append((n, m))
            return result
        # nbunch is a single node or iterable of nodes
        try:
            nbunch_iter = iter(nbunch)
        except TypeError:
            nbunch_iter = [nbunch]
        result = []
        for n in nbunch_iter:
            if n in self._succ:
                for m, d in self._succ[n].items():
                    if data:
                        result.append((n, m, dict(d)))
                    else:
                        result.append((n, m))
        return result

    def in_edges(self, nbunch=None, data=False, default=None):
        """Return edges incoming to node(s)."""
        try:
            nbunch_iter = iter(nbunch)
            filter_nodes = set(nbunch_iter)
        except TypeError:
            filter_nodes = {nbunch} if nbunch is not None else None

        result = []
        for n in self._pred:
            if filter_nodes is not None and n not in filter_nodes:
                continue
            for m, d in self._pred[n].items():
                if data:
                    result.append((m, n, dict(d)))
                else:
                    result.append((m, n))
        return result

    # Note: in_degree, out_degree, and degree are inherited from nx.DiGraph
    # as cached_properties that return proper view objects.
    # Our override of _succ and _pred ensures they work with our adjacency.


class MultiGraph(_NXSQLBase):
    _graph_type = "MultiGraph"
    _directed = False
    _multigraph = True

    def new_edge_key(self, u: Any, v: Any) -> int:
        """Generate a new unused edge key for multi-edge between u and v."""
        nu, nv = _to_hashable(u), _to_hashable(v)
        try:
            keydict = self._adj[nu][nv]
        except KeyError:
            return 0
        key = len(keydict)
        while key in keydict:
            key += 1
        return key


class MultiDiGraph(_NXSQLBase):
    _graph_type = "MultiDiGraph"
    _directed = True
    _multigraph = True

    def new_edge_key(self, u: Any, v: Any) -> int:
        """Generate a new unused edge key for multi-edge between u and v."""
        nu, nv = _to_hashable(u), _to_hashable(v)
        try:
            keydict = self._adj[nu][nv]
        except KeyError:
            return 0
        key = len(keydict)
        while key in keydict:
            key += 1
        return key
