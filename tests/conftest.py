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
    """Single SQLite file-based DB for entire test session."""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

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
    """New session per test. Truncates all tables before each test."""
    SessionLocal = sessionmaker(bind=engine)
    sess = SessionLocal()

    # Clean tables before each test (edges first due to FK order)
    sess.execute(EdgeModel.__table__.delete())
    sess.execute(NodeModel.__table__.delete())
    sess.execute(GraphModel.__table__.delete())
    sess.commit()

    yield sess

    try:
        sess.rollback()
    except Exception:
        pass
    sess.close()


# Graph factory fixtures — each creates a fresh nx_sql graph in the DB
@pytest.fixture
def Graph(session):
    return lambda name=None: nx_sql.Graph(session, name=name)


@pytest.fixture
def DiGraph(session):
    def _make_digraph(name=None):
        if name is None:
            name = f"digraph_{uuid.uuid4().hex[:8]}"
        return nx_sql.DiGraph(session, name=name)
    return _make_digraph


@pytest.fixture
def MultiGraph(session):
    return lambda name=None: nx_sql.MultiGraph(session, name=name)


@pytest.fixture
def MultiDiGraph(session):
    return lambda name=None: nx_sql.MultiDiGraph(session, name=name)


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
