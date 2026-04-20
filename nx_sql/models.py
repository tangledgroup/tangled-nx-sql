from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import JSON, String, Text, UUID, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Graph(Base):
    """Graph record with optional user-provided name."""

    __tablename__ = "graphs"

    graph_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=lambda: uuid.uuid7(),
    )
    name: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)
    graph_type: Mapped[str] = mapped_column(String(20), nullable=False)
    attributes: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True, default=dict
    )


class Node(Base):
    """Updated – supports np.ndarray, list[float], dict, set, etc."""

    __tablename__ = "nodes"

    node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=lambda: uuid.uuid7(),
    )
    graph_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    node_key: Mapped[str] = mapped_column(
        Text, nullable=False  # canonical JSON string of the normalized node
    )
    attributes: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True, default=dict
    )

    __table_args__ = (
        Index(  # enforces uniqueness per graph + fast lookup by node value
            "ix_nodes_graph_key_unique",
            "graph_id",
            "node_key",
            unique=True,
        ),
    )


class Edge(Base):
    """Completely unchanged from the first version."""

    __tablename__ = "edges"

    edge_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=lambda: uuid.uuid7(),
    )
    graph_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    source_id: Mapped[uuid.UUID] = mapped_column(  # internal UUID, not the public key
        UUID(as_uuid=True), nullable=False, index=True
    )
    target_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    key: Mapped[str | None] = mapped_column(Text, nullable=True)
    attributes: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True, default=dict
    )

    __table_args__ = (
        Index("ix_edges_lookup", "graph_id", "source_id", "target_id", "key"),
    )