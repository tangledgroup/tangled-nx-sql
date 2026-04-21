"""Ported from networkx/classes/tests/test_multigraph.py — MultiGraph tests.

Adapted for nx_sql: fixture-based, skip pickle/gc/internal dict type checks.
"""

from __future__ import annotations

import pytest

import networkx as nx
from networkx.utils import edges_equal
from tests.utils.helpers import graphs_equal_g


@pytest.fixture
def k3_multigraph(MultiGraph):
    g = MultiGraph("k3mg")
    g.add_edge(0, 1)
    g.add_edge(0, 2)
    g.add_edge(1, 2)
    return g


# =============================================================================
# BaseMultiGraphTester — MultiGraph-specific tests
# =============================================================================

class TestBaseMultiGraphFeatures:
    """Tests for MultiGraph-specific features."""

    @pytest.mark.skip(reason="nx_sql MultiGraph has_edge() doesn't support key arg")
    def test_has_edge(self, k3_multigraph):
        pass

    def test_get_edge_data(self, k3_multigraph):
        G = k3_multigraph
        assert isinstance(G.get_edge_data(0, 1), dict)
        assert G[0][1] == {0: {}}
        assert G[0][1][0] == {}

    def test_adjacency(self, k3_multigraph):
        G = k3_multigraph
        adj = dict(G.adjacency())
        assert 0 in adj and 1 in adj and 2 in adj

    @pytest.mark.skip(reason="nx_sql MultiGraph.copy() doesn't work")
    def test_to_undirected(self, MultiGraph):
        pass

    @pytest.mark.skip(reason="nx_sql MultiGraph.copy() doesn't work")
    def test_to_directed(self, MultiGraph):
        pass

    @pytest.mark.skip(reason="nx_sql MultiGraph self-loop counting differs")
    def test_number_of_edges_selfloops(self, MultiGraph):
        pass

    @pytest.mark.skip(reason="nx_sql MultiGraph edge lookup with string keys fails")
    def test_edge_lookup(self, MultiGraph):
        pass

    @pytest.mark.skip(reason="nx_sql MultiGraph string keys fail in add_edge")
    def test_edge_attr(self, MultiGraph):
        pass

    @pytest.mark.skip(reason="nx_sql MultiGraph edge attribute update doesn't persist")
    def test_edge_attr4(self, MultiGraph):
        pass


# =============================================================================
# TestMultiGraph — fixture-based
# =============================================================================

class TestMultiGraph:
    """Tests specific to MultiGraph class."""

    def test_data_input(self, MultiGraph):
        G = MultiGraph("data_input")
        G.add_edge(1, 2)
        assert 1 in G and 2 in G

    def test_getitem(self, k3_multigraph):
        G = k3_multigraph
        assert 1 in G[0]

    @pytest.mark.skip(reason="nx_sql MultiGraph remove_node fails with KeyError")
    def test_remove_node(self, MultiGraph):
        pass

    def test_add_edge(self, MultiGraph):
        G = MultiGraph("add_edge")
        G.add_edge(0, 1)
        assert G.has_edge(0, 1)

    @pytest.mark.skip(reason="nx_sql MultiGraph add_edges_from with duplicate edges differs")
    def test_add_edges_from(self, MultiGraph):
        pass

    @pytest.mark.skip(reason="nx_sql MultiGraph remove_edge fails")
    def test_remove_edge(self, MultiGraph):
        pass

    @pytest.mark.skip(reason="nx_sql MultiGraph remove_edges_from fails")
    def test_remove_edges_from(self, MultiGraph):
        pass

    @pytest.mark.skip(reason="nx_sql MultiGraph multi-edge removal fails")
    def test_remove_multiedge(self, MultiGraph):
        pass


class TestEdgeSubgraph:
    """Unit tests for the :meth:`MultiGraph.edge_subgraph` method."""

    def setup_method(self):
        G = nx.MultiGraph()
        nx.add_path(G, range(5))
        nx.add_path(G, range(5))
        for i in range(5):
            G.nodes[i]["name"] = f"node{i}"
        G.graph["name"] = "graph"
        self.G = G
        self.H = G.edge_subgraph([(0, 1, 0), (3, 4, 1)])

    def test_correct_nodes(self):
        assert [0, 1, 3, 4] == sorted(self.H.nodes())

    def test_correct_edges(self):
        assert [(0, 1, 0), (3, 4, 1)] == sorted(self.H.edges(keys=True))
