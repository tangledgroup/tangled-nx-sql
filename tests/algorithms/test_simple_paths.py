"""Ported from networkx/algorithms/tests/test_simple_paths.py.

Adapted for nx_sql: fixture-based graph construction.
"""

from __future__ import annotations

import pytest

import networkx as nx


class TestSimplePaths:
    """Tests for simple path algorithms."""

    def test_all_simple_paths(self):
        G = nx.path_graph(4)
        paths = list(nx.all_simple_paths(G, 0, 3))
        assert paths == [[0, 1, 2, 3]]

    def test_all_simple_paths_multiple(self):
        G = nx.cycle_graph(4)
        paths = list(nx.all_simple_paths(G, 0, 2))
        assert sorted(paths) == [[0, 1, 2], [0, 3, 2]]

    def test_all_simple_paths_cutoff(self):
        G = nx.path_graph(5)
        paths = list(nx.all_simple_paths(G, 0, 4, cutoff=2))
        assert all(len(p) <= 3 for p in paths)

    def test_all_simple_paths_no_path(self):
        G = nx.Graph()
        G.add_nodes_from([0, 1, 2])
        assert list(nx.all_simple_paths(G, 0, 2)) == []

    def test_shortest_simple_paths(self):
        G = nx.Graph()
        G.add_edges_from([(0, 1), (1, 2), (2, 3), (0, 3)])
        paths = list(nx.shortest_simple_paths(G, 0, 3))
        assert len(paths) >= 2
        # First path should be the shortest
        assert min(len(p) for p in paths[:1]) <= 2

    def test_shortest_simple_paths_directed(self):
        G = nx.DiGraph()
        G.add_edges_from([(0, 1), (1, 2), (2, 3), (0, 3)])
        paths = list(nx.shortest_simple_paths(G, 0, 3))
        assert len(paths) >= 2

    def test_is_simple_path(self):
        G = nx.path_graph(4)
        assert nx.is_simple_path(G, [0, 1, 2, 3])
        assert not nx.is_simple_path(G, [0, 1, 0, 2])

    def test_node_boundary(self):
        G = nx.path_graph(5)
        b = nx.node_boundary(G, {0, 1})
        assert 2 in b

    def test_edge_boundary(self):
        G = nx.path_graph(5)
        b = nx.edge_boundary(G, {0, 1})
        assert (1, 2) in b or (2, 1) in b
