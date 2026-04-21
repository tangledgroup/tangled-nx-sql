"""Ported from networkx/algorithms/tests/test_distance_measures.py.

Adapted for nx_sql: fixture-based graph construction.
"""

from __future__ import annotations

import pytest

import networkx as nx


class TestDistance:
    """Tests for distance measures."""

    def test_average_clustering(self):
        G = nx.path_graph(5)
        ac = nx.average_clustering(G)
        assert 0 <= ac <= 1

    def test_density(self):
        G = nx.complete_graph(5)
        assert nx.density(G) == pytest.approx(1.0, abs=1e-7)

    def test_density_digraph(self):
        G = nx.DiGraph(nx.complete_graph(5))
        assert nx.density(G) == pytest.approx(1.0, abs=1e-7)

    def test_density_empty(self):
        G = nx.Graph()
        G.add_nodes_from([0, 1, 2])
        assert nx.density(G) == 0

    def test_diameter(self):
        G = nx.path_graph(5)
        assert nx.diameter(G) == 4

    def test_diameter_disconnected(self):
        G = nx.Graph()
        G.add_edges_from([(0, 1), (2, 3)])
        with pytest.raises(nx.NetworkXError):
            nx.diameter(G)

    def test_radius(self):
        G = nx.path_graph(5)
        r = nx.radius(G)
        assert r == 2

    def test_periphery(self):
        G = nx.path_graph(5)
        periph = nx.periphery(G)
        assert 0 in periph and 4 in periph

    def test_center(self):
        G = nx.path_graph(5)
        center = nx.center(G)
        assert 2 in center

    def test_eccentricity(self):
        G = nx.path_graph(5)
        ecc = nx.eccentricity(G)
        assert ecc[0] == 4
        assert ecc[2] == 2

    def test_eccentricity_directed(self):
        G = nx.DiGraph(nx.path_graph(5))
        ecc = nx.eccentricity(G)
        assert isinstance(ecc, dict)

    def test_wiener_index(self):
        G = nx.path_graph(5)
        w = nx.wiener_index(G)
        assert w == 20
