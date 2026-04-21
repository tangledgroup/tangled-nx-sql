"""Test fixtures for nx_sql — session, engine, graph factories."""

from __future__ import annotations

import os
import uuid

import networkx as nx
import pytest
import sqlalchemy
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

import nx_sql
from nx_sql.models import Base, Edge as EdgeModel, Graph as GraphModel, Node as NodeModel

DB_PATH = os.path.join(os.path.dirname(__file__), "test_nx_sql.db")


@pytest.fixture(scope="session")
def engine():
    """Single SQLite file-based DB for entire test session.
    
    DB is preserved after tests so you can review data:
        sqlite3 tests/test_nx_sql.db "SELECT name, id FROM graphs ORDER BY name;"
    """
    eng = create_engine(f"sqlite:///{DB_PATH}", echo=False)

    @event.listens_for(eng, "connect")
    def _set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=OFF")
        cursor.close()

    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture(scope="function")
def session(engine):
    """New session per test. Does NOT truncate tables — preserves data for review."""
    SessionLocal = sessionmaker(bind=engine)
    sess = SessionLocal()

    yield sess

    try:
        sess.rollback()
    except Exception:
        pass
    sess.close()


def _sanitize_name(name: str) -> str:
    """Sanitize test name for use as graph name in SQLite."""
    return name.replace(".", "__")


# Graph factory fixtures — each creates a fresh nx_sql graph in the DB
@pytest.fixture
def Graph(session, request):
    test_name = _sanitize_name(
        f"{request.node.cls.__name__}.{request.node.name}"
        if request.node.cls else request.node.name
    )
    return lambda name=None: nx_sql.Graph(session, name=name or test_name)


@pytest.fixture
def DiGraph(session, request):
    test_name = _sanitize_name(
        f"{request.node.cls.__name__}.{request.node.name}"
        if request.node.cls else request.node.name
    )
    def _make_digraph(name=None):
        return nx_sql.DiGraph(session, name=name or test_name)
    return _make_digraph


@pytest.fixture
def MultiGraph(session, request):
    test_name = _sanitize_name(
        f"{request.node.cls.__name__}.{request.node.name}"
        if request.node.cls else request.node.name
    )
    return lambda name=None: nx_sql.MultiGraph(session, name=name or test_name)


@pytest.fixture
def MultiDiGraph(session, request):
    test_name = _sanitize_name(
        f"{request.node.cls.__name__}.{request.node.name}"
        if request.node.cls else request.node.name
    )
    return lambda name=None: nx_sql.MultiDiGraph(session, name=name or test_name)


# Convenience fixtures: pre-built small graphs for each type
@pytest.fixture
def k3_graph(Graph):
    g = Graph("k3")
    g.add_edge(0, 1)
    g.add_edge(0, 2)
    g.add_edge(1, 2)
    return g


@pytest.fixture
def path3_graph(Graph):
    g = Graph("path3")
    g.add_edge(0, 1)
    g.add_edge(1, 2)
    return g


@pytest.fixture
def cycle5_graph(Graph):
    g = Graph("cycle5")
    for i in range(5):
        g.add_edge(i, (i + 1) % 5)
    return g


@pytest.fixture
def petersen_graph(Graph):
    g = Graph("petersen")
    # Petersen graph: outer 5-cycle, inner star, spokes
    for i in range(5):
        g.add_edge(i, (i + 1) % 5)           # outer cycle
        g.add_edge(i + 5, (i + 2) % 5 + 5)    # inner star
        g.add_edge(i, i + 5)                   # spokes
    return g
