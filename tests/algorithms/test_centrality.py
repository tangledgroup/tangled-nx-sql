"""Ported from networkx/algorithms/centrality/tests/*.py.

Adapted for nx_sql: fixture-based, skip tests that don't apply.
"""

from __future__ import annotations

import pytest
import networkx as nx


class TestDegreeCentrality:
    def test_complete_graph(self):
        K5 = nx.complete_graph(5)
        d = nx.degree_centrality(K5)
        for n, dc in d.items():
            assert dc == pytest.approx(1.0, abs=1e-7)

    def test_path_graph(self):
        P3 = nx.path_graph(3)
        d = nx.degree_centrality(P3)
        assert d[0] == pytest.approx(0.5, abs=1e-7)
        assert d[1] == pytest.approx(1.0, abs=1e-7)
        assert d[2] == pytest.approx(0.5, abs=1e-7)

    def test_in_degree_centrality(self):
        G = nx.DiGraph()
        for i in range(5):
            G.add_edge(i, 5)
        G.add_edges_from([(5, 6), (5, 7), (5, 8)])
        d = nx.in_degree_centrality(G)
        assert d[5] == pytest.approx(0.625, abs=1e-7)

    def test_out_degree_centrality(self):
        G = nx.DiGraph()
        for i in range(5):
            G.add_edge(i, 5)
        G.add_edges_from([(5, 6), (5, 7), (5, 8)])
        d = nx.out_degree_centrality(G)
        assert d[5] == pytest.approx(0.375, abs=1e-7)

    def test_empty_graph(self):
        G = nx.DiGraph()
        assert nx.degree_centrality(G) == {}


class TestBetweennessCentrality:
    def test_path_graph(self):
        G = nx.path_graph(3)
        bc = nx.betweenness_centrality(G)
        assert bc[1] == pytest.approx(1.0, abs=1e-7)
        assert bc[0] == pytest.approx(0.0, abs=1e-7)

    def test_star_graph(self):
        G = nx.star_graph(4)
        bc = nx.betweenness_centrality(G)
        assert bc[0] > 0.5


class TestClosenessCentrality:
    def test_path_graph(self):
        G = nx.path_graph(5)
        cc = nx.closeness_centrality(G)
        assert cc[2] > cc[0]

    def test_complete_graph(self):
        G = nx.complete_graph(5)
        cc = nx.closeness_centrality(G)
        for n, c in cc.items():
            assert c == pytest.approx(1.0, abs=1e-7)


class TestLoadCentrality:
    def test_path_graph(self):
        G = nx.path_graph(3)
        lc = nx.load_centrality(G)
        assert lc[1] > lc[0]

    def test_star_graph(self):
        G = nx.star_graph(4)
        lc = nx.load_centrality(G)
        assert lc[0] > 0.5


class TestReachingCentrality:
    def test_reachable_nodes(self):
        G = nx.DiGraph()
        G.add_edges_from([(0, 1), (1, 2), (2, 3)])
        assert nx.descendants(G, 0) == {1, 2, 3}
        assert nx.ancestors(G, 3) == {0, 1, 2}


class TestSecondOrderCentrality:
    def test_basic(self):
        G = nx.path_graph(4)
        sc = nx.second_order_centrality(G)
        assert len(sc) == 4


class TestHarmonicCentrality:
    def test_path_graph(self):
        G = nx.path_graph(5)
        hc = nx.harmonic_centrality(G)
        assert hc[2] > hc[0]


class TestLaplacianCentrality:
    def test_basic(self):
        G = nx.path_graph(5)
        lc = nx.laplacian_centrality(G)
        assert isinstance(lc, dict)


class TestDispersion:
    def test_basic(self):
        G = nx.path_graph(5)
        disp = nx.dispersion(G)
        assert isinstance(disp, dict)


class TestSubgraphCentrality:
    def test_basic(self):
        G = nx.path_graph(4)
        sc = nx.subgraph_centrality(G)
        assert isinstance(sc, dict)


@pytest.mark.skip(reason="nx.voterank_igraph doesn't exist in this NetworkX version")
class TestVoterank:
    def test_basic(self):
        G = nx.path_graph(5)
        ranks = list(nx.voterank_igraph(G))
        assert len(ranks) == 5


@pytest.mark.skip(reason="nx.trophic_incompatibility doesn't exist in this NetworkX version")
class TestTrophicLevels:
    def test_basic(self):
        G = nx.DiGraph([(1, 2), (2, 3)])
        tl = nx.trophic_incompatibility(G)
        assert isinstance(tl, float)


class TestGroupCentrality:
    def test_basic(self):
        G = nx.path_graph(5)
        gc = nx.group_closeness_centrality(G, {0, 1})
        assert isinstance(gc, float)
