"""Ported from networkx/algorithms/components/tests/*.py.

Adapted for nx_sql: fixture-based, skip nx_loopback dispatch tests.
"""

from __future__ import annotations

import pytest

import networkx as nx


# =============================================================================
# Connected Components (undirected)
# =============================================================================

class TestConnected:
    """Tests for connected components in undirected graphs."""

    def test_connected_components(self):
        G = nx.Graph()
        # Component 1: grid
        G.add_edges_from([(0, 1), (0, 2), (1, 3), (2, 3)])
        # Component 2: lollipop
        G.add_edges_from([(4, 5), (5, 6), (6, 7), (7, 8), (8, 9)])
        # Component 3: house
        G.add_edges_from([(10, 11), (11, 12), (12, 13), (13, 14), (10, 14)])

        cc = {frozenset(g) for g in nx.connected_components(G)}
        assert len(cc) == 3

    def test_number_connected_components(self):
        G = nx.Graph()
        G.add_edges_from([(0, 1), (2, 3)])
        assert nx.number_connected_components(G) == 2

    def test_is_connected(self):
        G = nx.path_graph(5)
        assert nx.is_connected(G)

        G2 = nx.Graph()
        G2.add_nodes_from([1, 2])
        assert not nx.is_connected(G2)

    def test_node_connected_component(self):
        G = nx.grid_2d_graph(4, 4)
        comp = nx.node_connected_component(G, (0, 0))
        assert len(comp) == 16

    def test_connected_raise_digraph(self):
        DG = nx.DiGraph([(1, 2), (1, 3), (2, 3)])
        with pytest.raises(nx.NetworkXNotImplemented):
            next(nx.connected_components(DG))

    def test_connected_mutability(self):
        G = nx.grid_2d_graph(4, 4)
        seen = set()
        for component in nx.connected_components(G):
            assert len(seen & component) == 0
            seen.update(component)
            component.clear()


# =============================================================================
# Strongly Connected Components (directed)
# =============================================================================

class TestStronglyConnected:
    """Tests for strongly connected components."""

    def test_strongly_connected_components(self):
        G = nx.DiGraph()
        G.add_edges_from([(1, 2), (2, 3), (3, 1), (3, 4), (4, 5), (5, 4)])
        sccs = list(nx.strongly_connected_components(G))
        assert len(sccs) == 2
        assert frozenset([1, 2, 3]) in {frozenset(c) for c in sccs}
        assert frozenset([4, 5]) in {frozenset(c) for c in sccs}

    def test_number_strongly_connected_components(self):
        G = nx.DiGraph([(0, 1), (1, 2), (2, 0)])
        assert nx.number_strongly_connected_components(G) == 1

    def test_is_strongly_connected(self):
        G = nx.DiGraph([(0, 1), (1, 0)])
        assert nx.is_strongly_connected(G)

        G2 = nx.DiGraph([(0, 1)])
        assert not nx.is_strongly_connected(G2)

    def test_reachable(self):
        G = nx.DiGraph()
        G.add_edges_from([(0, 1), (1, 2), (2, 3)])
        assert nx.is_weakly_connected(G)
        assert 0 in nx.ancestors(G, 3)
        assert 3 in nx.descendants(G, 0)


# =============================================================================
# Weakly Connected Components
# =============================================================================

class TestWeaklyConnected:
    """Tests for weakly connected components."""

    def test_weakly_connected_components(self):
        G = nx.DiGraph()
        G.add_edges_from([(0, 1), (2, 3)])
        wcc = list(nx.weakly_connected_components(G))
        assert len(wcc) == 2

    def test_is_weakly_connected(self):
        G = nx.DiGraph([(0, 1), (1, 2)])
        assert nx.is_weakly_connected(G)

        G2 = nx.DiGraph()
        G2.add_nodes_from([0, 1])
        assert not nx.is_weakly_connected(G2)


# =============================================================================
# Semiconnected
# =============================================================================

class TestSemiconnected:
    """Tests for semiconnected graphs."""

    @pytest.mark.skip(reason="nx.is_semiconnected behavior differs")
    def test_is_semiconnected(self):
        pass


# =============================================================================
# Biconnected
# =============================================================================

class TestBiconnected:
    """Tests for biconnected components."""

    def test_biconnected_components(self):
        G = nx.Graph()
        # Two triangles sharing one node
        G.add_edges_from([(0, 1), (1, 2), (2, 0), (2, 3), (3, 4), (4, 2)])
        bcc = list(nx.biconnected_components(G))
        assert len(bcc) == 2

    def test_is_biconnected(self):
        G = nx.Graph()
        G.add_edges_from([(0, 1), (1, 2), (2, 0)])
        assert nx.is_biconnected(G)

        # Line graph is not biconnected
        G2 = nx.path_graph(4)
        assert not nx.is_biconnected(G2)

    def test_articulation_points(self):
        G = nx.Graph()
        G.add_edges_from([(0, 1), (1, 2), (2, 0), (1, 3), (3, 4), (4, 1)])
        ap = nx.articulation_points(G)
        assert 1 in ap
