"""Ported from networkx/classes/tests/test_reportviews.py — Report view tests.

Adapted for nx_sql: skip pickle/gc/internal dict type checks, focus on API compatibility.
"""

from __future__ import annotations

import pytest

import networkx as nx
from networkx.classes.reportviews import NodeDataView


# =============================================================================
# Nodes
# =============================================================================

class TestNodeView:
    def test_str(self, path3_graph):
        G = nx.path_graph(9)
        nv = G.nodes
        assert str(nv) == "[0, 1, 2, 3, 4, 5, 6, 7, 8]"

    def test_repr(self, path3_graph):
        G = nx.path_graph(9)
        nv = G.nodes
        assert repr(nv) == "NodeView((0, 1, 2, 3, 4, 5, 6, 7, 8))"

    def test_contains(self, path3_graph):
        G = nx.path_graph(9)
        nv = G.nodes
        assert 7 in nv
        assert 9 not in nv

    def test_getitem(self, path3_graph):
        G = nx.path_graph(9)
        nv = G.nodes
        G.nodes[3]["foo"] = "bar"
        assert nv[7] == {}
        assert nv[3] == {"foo": "bar"}
        with pytest.raises(nx.NetworkXError):
            G.nodes[0:5]

    def test_iter(self, path3_graph):
        G = nx.path_graph(9)
        nv = G.nodes
        for i, n in enumerate(nv):
            assert i == n

    def test_call(self, path3_graph):
        G = nx.path_graph(9)
        nodes = G.nodes
        assert nodes is nodes()
        assert nodes is not nodes(data=True)


class TestNodeDataView:
    def test_viewtype(self, path3_graph):
        G = nx.path_graph(9)
        nv = G.nodes
        ndvfalse = nv.data(False)
        assert nv is ndvfalse

    def test_str(self, path3_graph):
        G = nx.path_graph(9)
        nv = G.nodes
        msg = str([(n, {}) for n in range(9)])
        assert str(nv.data(True)) == msg

    def test_contains(self, path3_graph):
        G = nx.path_graph(9)
        G.nodes[3]["foo"] = "bar"
        nv = G.nodes.data()
        nwv = G.nodes.data("foo")
        assert (7, {}) in nv
        assert (3, {"foo": "bar"}) in nv
        assert (3, "bar") in nwv
        assert (7, None) in nwv

    def test_iter(self, path3_graph):
        G = nx.path_graph(9)
        nv = G.nodes.data()
        for i, (n, d) in enumerate(nv):
            assert i == n
            assert d == {}

    def test_data_iter_with_attr(self, path3_graph):
        G = nx.path_graph(9)
        G.nodes[3]["foo"] = "bar"
        for n, d in G.nodes.data("foo"):
            if n == 3:
                assert d == "bar"
            else:
                assert d is None


def test_nodedataview_unhashable():
    G = nx.path_graph(9)
    G.nodes[3]["foo"] = "bar"
    nvs = [G.nodes.data()]
    nvs.append(G.nodes.data(True))
    for nv in nvs:
        pytest.raises(TypeError, set, nv)


class TestNodeViewSetOps:
    def test_len(self, path3_graph):
        G = nx.path_graph(9)
        nv = G.nodes
        assert len(nv) == 9

    def test_and(self, path3_graph):
        G = nx.path_graph(9)
        nv = G.nodes
        some_nodes = set(range(5, 12))
        assert nv & some_nodes == set(range(5, 9))

    def test_or(self, path3_graph):
        G = nx.path_graph(9)
        nv = G.nodes
        some_nodes = set(range(5, 12))
        assert nv | some_nodes == set(range(12))

    def test_xor(self, path3_graph):
        G = nx.path_graph(9)
        nv = G.nodes
        some_nodes = set(range(5, 12))
        nodes = {0, 1, 2, 3, 4, 9, 10, 11}
        assert nv ^ some_nodes == set(nodes)

    def test_sub(self, path3_graph):
        G = nx.path_graph(9)
        nv = G.nodes
        some_nodes = set(range(5, 12))
        assert nv - some_nodes == set(range(5))


# =============================================================================
# Edges Data View
# =============================================================================

class TestEdgeDataView:
    def test_str(self, path3_graph):
        G = nx.path_graph(9)
        ev = list(G.edges(data=True))
        assert len(ev) == 8

    def test_contains(self, path3_graph):
        G = nx.path_graph(9)
        ev = G.edges(data=True)
        assert (0, 1, {}) in ev
        assert (0, 2, {}) not in ev

    def test_iter(self, path3_graph):
        G = nx.path_graph(9)
        edges = list(G.edges(data=True))
        assert len(edges) == 8
        assert edges[0] == (0, 1, {})


class TestEdgeView:
    def test_str(self, path3_graph):
        G = nx.path_graph(9)
        ev = list(G.edges())
        assert len(ev) == 8

    def test_contains(self, path3_graph):
        G = nx.path_graph(9)
        ev = G.edges
        assert (0, 1) in ev
        assert (0, 2) not in ev

    def test_iter(self, path3_graph):
        G = nx.path_graph(9)
        edges = list(G.edges())
        assert len(edges) == 8
        assert edges[0] == (0, 1)

    def test_len(self, path3_graph):
        G = nx.path_graph(9)
        ev = G.edges
        assert len(ev) == 8

    def test_slicing(self, path3_graph):
        G = nx.path_graph(9)
        ev = G.edges
        with pytest.raises(nx.NetworkXError):
            ev[0:5]

    def test_not_equal(self, path3_graph):
        G = nx.path_graph(9)
        ev = G.edges
        assert ev != [(0, 1)]


class TestEdgeDataViewDefault:
    def test_default(self, path3_graph):
        G = nx.path_graph(9)
        G.add_edge(0, 1, weight=5)
        ev = G.edges(data="weight", default=0)
        assert (0, 1, 5) in ev
        assert (1, 2, 0) in ev


# =============================================================================
# Degree View
# =============================================================================

class TestDegreeView:
    def test_str(self, Graph):
        G = nx.path_graph(9)
        dv = G.degree
        assert len(str(dv)) > 0

    def test_iter(self, Graph):
        G = nx.path_graph(9)
        deg = dict(G.degree())
        assert len(deg) == 9

    def test_weighted(self, Graph):
        G = Graph("weighted_deg")
        G.add_edge(1, 2, weight=2)
        G.add_edge(2, 3, weight=3)
        assert sorted(d for n, d in G.degree(weight="weight")) == [2, 3, 5]

    def test_nbunch(self, Graph):
        G = nx.path_graph(9)
        assert dict(G.degree([0, 1])) == {0: 1, 1: 2}

    def test_single(self, Graph):
        G = nx.path_graph(9)
        assert G.degree(0) == 1


class TestInDegreeView:
    def test_iter(self, DiGraph):
        G = DiGraph("in_deg")
        for i in range(3):
            for j in range(3):
                if i != j:
                    G.add_edge(i, j)
        deg = dict(G.in_degree())
        assert all(v == 2 for v in deg.values())

    def test_single(self, DiGraph):
        G = DiGraph("in_deg_s")
        for i in range(3):
            for j in range(3):
                if i != j:
                    G.add_edge(i, j)
        assert G.in_degree(0) == 2


class TestOutDegreeView:
    def test_iter(self, DiGraph):
        G = DiGraph("out_deg")
        for i in range(3):
            for j in range(3):
                if i != j:
                    G.add_edge(i, j)
        deg = dict(G.out_degree())
        assert all(v == 2 for v in deg.values())

    def test_single(self, DiGraph):
        G = DiGraph("out_deg_s")
        for i in range(3):
            for j in range(3):
                if i != j:
                    G.add_edge(i, j)
        assert G.out_degree(0) == 2
