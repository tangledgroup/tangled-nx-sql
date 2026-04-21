"""Ported from networkx/algorithms/traversal/tests/test_bfs.py and test_dfs.py.

Adapted for nx_sql: fixture-based graph construction.
"""

from __future__ import annotations

import pytest

import networkx as nx


# =============================================================================
# BFS
# =============================================================================

class TestBreadthFirstSearch:
    """Tests for breadth-first search."""

    def test_bfs_edges(self):
        G = nx.path_graph(3)
        assert list(nx.bfs_edges(G, 0)) == [(0, 1), (1, 2)]

    def test_bfs_tree(self):
        G = nx.path_graph(3)
        T = nx.bfs_tree(G, 0)
        assert sorted(T.edges()) == [(0, 1), (1, 2)]

    def test_bfs_predecessors(self):
        G = nx.path_graph(3)
        pred = nx.bfs_predecessors(G, 0)
        assert dict(pred) == {1: 0, 2: 1}

    def test_bfs_successors(self):
        G = nx.path_graph(3)
        succ = nx.bfs_successors(G, 0)
        assert dict(succ) == {0: [1], 1: [2]}

    def test_bfs_order(self):
        G = nx.path_graph(5)
        ordered_nodes = list(nx.bfs_tree(G, 0).nodes())
        assert ordered_nodes == [0, 1, 2, 3, 4]

    def test_bfs_on_digraph(self):
        G = nx.DiGraph()
        G.add_edges_from([(0, 1), (0, 2), (1, 3), (2, 4)])
        edges = list(nx.bfs_edges(G, 0))
        assert (0, 1) in edges and (0, 2) in edges

    def test_bfs_not_connected(self):
        G = nx.Graph()
        G.add_edges_from([(0, 1), (2, 3)])
        T = nx.bfs_tree(G, 0)
        assert sorted(T.nodes()) == [0, 1]

    def test_bfs_cutoff(self):
        G = nx.path_graph(10)
        T = nx.bfs_tree(G, 0, depth_limit=3)
        assert len(T.nodes()) == 4


# =============================================================================
# DFS
# =============================================================================

class TestDepthFirstSearch:
    """Tests for depth-first search."""

    def test_dfs_edges(self):
        G = nx.path_graph(3)
        assert list(nx.dfs_edges(G, 0)) == [(0, 1), (1, 2)]

    def test_dfs_tree(self):
        G = nx.path_graph(3)
        T = nx.dfs_tree(G, 0)
        assert sorted(T.edges()) == [(0, 1), (1, 2)]

    def test_dfs_predecessors(self):
        G = nx.path_graph(3)
        pred = nx.dfs_predecessors(G, 0)
        assert dict(pred) == {1: 0, 2: 1}

    def test_dfs_successors(self):
        G = nx.path_graph(3)
        succ = nx.dfs_successors(G, 0)
        assert dict(succ) == {0: [1], 1: [2]}

    def test_dfs_order(self):
        G = nx.path_graph(5)
        ordered_nodes = list(nx.dfs_tree(G, 0).nodes())
        assert ordered_nodes == [0, 1, 2, 3, 4]

    def test_dfs_on_digraph(self):
        G = nx.DiGraph()
        G.add_edges_from([(0, 1), (0, 2), (1, 3), (2, 4)])
        edges = list(nx.dfs_edges(G, 0))
        assert (0, 1) in edges and (0, 2) in edges

    def test_dfs_not_connected(self):
        G = nx.Graph()
        G.add_edges_from([(0, 1), (2, 3)])
        T = nx.dfs_tree(G, 0)
        assert sorted(T.nodes()) == [0, 1]

    def test_dfs_cutoff(self):
        G = nx.path_graph(10)
        T = nx.dfs_tree(G, 0, depth_limit=3)
        assert len(T.nodes()) == 4


# =============================================================================
# Edge BFS / DFS
# =============================================================================

class TestEdgeBFS:
    """Tests for edge-based BFS."""

    def test_edge_bfs(self):
        G = nx.path_graph(3)
        edges = list(nx.edge_bfs(G, 0))
        assert len(edges) >= 2

    def test_edge_bfs_reverse(self):
        G = nx.DiGraph()
        G.add_edges_from([(0, 1), (1, 2)])
        assert list(nx.edge_bfs(G)) == [(0, 1), (1, 2)]


class TestEdgeDFS:
    """Tests for edge-based DFS."""

    def test_edge_dfs(self):
        G = nx.path_graph(3)
        edges = list(nx.edge_dfs(G, 0))
        assert len(edges) >= 2
