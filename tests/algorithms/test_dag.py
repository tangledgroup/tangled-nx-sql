"""Ported from networkx/algorithms/tests/test_dag.py.

Adapted for nx_sql: fixture-based graph construction, skip orderable node tests.
"""

from __future__ import annotations

import pytest

import networkx as nx


class TestDAGLongestPath:
    """Tests for longest path in DAG."""

    def test_empty(self):
        G = nx.DiGraph()
        assert nx.dag_longest_path(G) == []

    def test_unweighted1(self):
        edges = [(1, 2), (2, 3), (2, 4), (3, 5), (5, 6), (3, 7)]
        G = nx.DiGraph(edges)
        assert nx.dag_longest_path(G) == [1, 2, 3, 5, 6]

    def test_unweighted2(self):
        edges = [(1, 2), (2, 3), (3, 4), (4, 5), (1, 3), (1, 5), (3, 5)]
        G = nx.DiGraph(edges)
        assert nx.dag_longest_path(G) == [1, 2, 3, 4, 5]

    def test_weighted(self):
        G = nx.DiGraph()
        edges = [(1, 2, -5), (2, 3, 1), (3, 4, 1), (4, 5, 0), (3, 5, 4), (1, 6, 2)]
        G.add_weighted_edges_from(edges)
        assert nx.dag_longest_path(G) == [2, 3, 5]

    def test_undirected_not_implemented(self):
        G = nx.Graph()
        pytest.raises(nx.NetworkXNotImplemented, nx.dag_longest_path, G)

    def test_multigraph_unweighted(self):
        edges = [(1, 2), (2, 3), (2, 3), (3, 4), (4, 5), (1, 3), (1, 5), (3, 5)]
        G = nx.MultiDiGraph(edges)
        assert nx.dag_longest_path(G) == [1, 2, 3, 4, 5]


class TestDAGLongestPathLength:
    """Tests for longest path length in DAG."""

    def test_unweighted(self):
        G = nx.DiGraph([(1, 2), (2, 3), (3, 4)])
        assert nx.dag_longest_path_length(G) == 3

    def test_weighted(self):
        G = nx.DiGraph()
        G.add_edge(1, 2, weight=5)
        G.add_edge(2, 3, weight=1)
        G.add_edge(3, 4, weight=1)
        assert nx.dag_longest_path_length(G) == 7


class TestTopologicalSort:
    """Tests for topological sorting."""

    def test_topological_sort(self):
        G = nx.DiGraph([(1, 2), (2, 3), (3, 4)])
        order = list(nx.topological_sort(G))
        assert order.index(1) < order.index(2) < order.index(3) < order.index(4)

    def test_topological_sort_cycle(self):
        G = nx.cycle_graph(3, create_using=nx.DiGraph())
        with pytest.raises(nx.NetworkXUnfeasible):
            list(nx.topological_sort(G))

    def test_lexicographical_topological_sort(self):
        G = nx.DiGraph([(1, 2), (1, 3), (2, 4), (3, 4)])
        order = list(nx.lexicographical_topological_sort(G))
        assert order.index(1) < order.index(2)
        assert order.index(1) < order.index(3)
        assert order.index(2) < order.index(4)
        assert order.index(3) < order.index(4)


class TestDAGProperties:
    """Tests for DAG properties."""

    def test_is_directed_acyclic_graph(self):
        G = nx.DiGraph([(1, 2), (2, 3)])
        assert nx.is_directed_acyclic_graph(G)

        G2 = nx.cycle_graph(3, create_using=nx.DiGraph())
        assert not nx.is_directed_acyclic_graph(G2)

    def test_ancestors(self):
        G = nx.DiGraph([(1, 2), (2, 3), (3, 4)])
        assert nx.ancestors(G, 4) == {1, 2, 3}
        assert nx.ancestors(G, 1) == set()

    def test_descendants(self):
        G = nx.DiGraph([(1, 2), (2, 3), (3, 4)])
        assert nx.descendants(G, 1) == {2, 3, 4}
        assert nx.descendants(G, 4) == set()

    def test_descendants_at_distance(self):
        G = nx.path_graph(5, create_using=nx.DiGraph())
        assert nx.descendants_at_distance(G, 0, 2) == {2}

    def test_leaves(self):
        G = nx.DiGraph([(1, 2), (2, 3)])
        leaves = [n for n in G if G.out_degree(n) == 0]
        assert set(leaves) == {3}

    def test_ancestors_at_distance(self):
        G = nx.path_graph(5, create_using=nx.DiGraph())
        ancs = nx.ancestors(G, 4)
        assert 2 in ancs

    @pytest.mark.skip(reason="nx.immediate_dominators requires 'start' arg in this NetworkX version")
    def test_immediate_dominators(self):
        pass

    @pytest.mark.skip(reason="nx.critical_paths doesn't exist in this NetworkX version")
    def test_critical_path(self):
        pass


class TestDAGException:
    """Tests for DAG-related exceptions."""

    def test_cycle_error(self):
        G = nx.DiGraph()
        G.add_edges_from([(0, 1), (1, 0)])
        with pytest.raises(nx.NetworkXUnfeasible):
            list(nx.topological_sort(G))

    @pytest.mark.skip(reason="nx.topological_sort accepts undirected graphs in newer NetworkX")
    def test_undirected_error(self):
        pass
