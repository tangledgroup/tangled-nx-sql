"""Ported from networkx/algorithms/tests/test_cycles.py.

Adapted for nx_sql: fixture-based graph construction.
"""

from __future__ import annotations

import pytest

import networkx as nx


class TestCycleDetection:
    """Tests for cycle detection."""

    def test_dag_has_no_cycle(self):
        G = nx.DiGraph([(1, 2), (2, 3)])
        assert not nx.is_directed_acyclic_graph(G) is False

    def test_digraph_with_cycle(self):
        G = nx.cycle_graph(5, create_using=nx.DiGraph())
        assert nx.find_cycle(G)

    def test_find_cycle_simple(self):
        G = nx.DiGraph([(0, 1), (1, 2), (2, 0)])
        cycle = nx.find_cycle(G)
        assert len(cycle) == 3

    def test_find_cycle_source(self):
        G = nx.DiGraph([(0, 1), (1, 2), (2, 0)])
        cycle = nx.find_cycle(G, source=0)
        assert len(cycle) == 3

    def test_undirected_has_no_cycle(self):
        G = nx.path_graph(5)
        with pytest.raises(nx.NetworkXNoCycle):
            nx.find_cycle(G)

    def test_undirected_with_cycle(self):
        G = nx.cycle_graph(5)
        cycle = nx.find_cycle(G)
        assert len(cycle) == 5

    def test_empty_graph(self):
        G = nx.Graph()
        with pytest.raises(nx.NetworkXNoCycle):
            nx.find_cycle(G)


class TestSimpleCycles:
    """Tests for simple cycle enumeration."""

    def test_simple_cycles_digraph(self):
        G = nx.DiGraph()
        G.add_edges_from([(0, 1), (1, 2), (2, 0)])
        cycles = list(nx.simple_cycles(G))
        assert any(len(c) == 3 for c in cycles)

    def test_simple_cycles_empty(self):
        G = nx.DiGraph()
        assert list(nx.simple_cycles(G)) == []


class TestTriads:
    """Tests for triad classification."""

    def test_triadic_census(self):
        G = nx.DiGraph()
        G.add_edges_from([(0, 1), (1, 2), (2, 0)])
        tc = nx.triadic_census(G)
        assert isinstance(tc, dict)

    @pytest.mark.skip(reason="nx.is_mutable doesn't exist in this NetworkX version")
    def test_isomorphisms(self):
        pass


class TestEulerian:
    """Tests for Eulerian path/circuit."""

    def test_is_eulerian(self):
        G = nx.complete_graph(3)
        assert nx.is_eulerian(G)

    def test_eulerian_circuit(self):
        G = nx.complete_graph(3)
        circuit = list(nx.eulerian_circuit(G))
        assert len(circuit) == 3

    def test_eulerian_path(self):
        G = nx.path_graph(4)
        path = list(nx.eulerian_path(G))
        assert len(path) == 3
