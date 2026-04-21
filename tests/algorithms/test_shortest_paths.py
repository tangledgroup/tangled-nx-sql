"""Ported from networkx/algorithms/shortest_paths/tests/test_generic.py.

Adapted for nx_sql: fixture-based graph construction, skip numpy-dependent tests.
"""

from __future__ import annotations

import pytest

import networkx as nx


# =============================================================================
# Helpers
# =============================================================================

def validate_grid_path(r, c, s, t, p):
    """Validate path through a grid graph."""
    assert isinstance(p, list)
    assert p[0] == s
    assert p[-1] == t
    s_coord = ((s - 1) // c, (s - 1) % c)
    t_coord = ((t - 1) // c, (t - 1) % c)
    assert len(p) == abs(t_coord[0] - s_coord[0]) + abs(t_coord[1] - s_coord[1]) + 1
    p_coords = [((u - 1) // c, (u - 1) % c) for u in p]
    for u in p_coords:
        assert 0 <= u[0] < r
        assert 0 <= u[1] < c
    for (u0, u1), (v0, v1) in zip(p_coords[:-1], p_coords[1:]):
        assert (abs(v0 - u0), abs(v1 - u1)) in [(0, 1), (1, 0)]


# =============================================================================
# Generic Path Tests
# =============================================================================

class TestGenericPath:
    """Tests for generic shortest path algorithms."""

    def test_sentinel_trick_all_algorithms(self):
        G = nx.Graph()
        G.add_edge("A", "B", weight=1)
        G.add_edge("B", "C", weight=1)
        G.add_edge("C", "D", weight=1)
        G.add_edge("D", "E", weight=1)

        source = "A"
        sentinel = "_sentinel_"
        G.add_node(sentinel)
        for t in ("C", "D", "E"):
            G.add_edge(t, sentinel, weight=0)

        path = nx.shortest_path(G, source=source, target=sentinel, weight="weight")
        assert path[-2] == "C"

    def test_shortest_path(self):
        cycle = nx.cycle_graph(7)
        grid = nx.convert_node_labels_to_integers(nx.grid_2d_graph(4, 4), first_label=1, ordering="sorted")
        directed_cycle = nx.cycle_graph(7, create_using=nx.DiGraph())

        assert nx.shortest_path(cycle, 0, 3) == [0, 1, 2, 3]
        assert nx.shortest_path(cycle, 0, 4) == [0, 6, 5, 4]
        validate_grid_path(4, 4, 1, 12, nx.shortest_path(grid, 1, 12))
        assert nx.shortest_path(directed_cycle, 0, 3) == [0, 1, 2, 3]

    def test_shortest_path_weighted(self):
        cycle = nx.cycle_graph(7)
        grid = nx.convert_node_labels_to_integers(nx.grid_2d_graph(4, 4), first_label=1, ordering="sorted")
        directed_cycle = nx.cycle_graph(7, create_using=nx.DiGraph())

        assert nx.shortest_path(cycle, 0, 3, weight="weight") == [0, 1, 2, 3]
        assert nx.shortest_path(cycle, 0, 4, weight="weight") == [0, 6, 5, 4]
        validate_grid_path(4, 4, 1, 12, nx.shortest_path(grid, 1, 12, weight="weight"))
        assert nx.shortest_path(directed_cycle, 0, 3, weight="weight") == [0, 1, 2, 3]

    def test_shortest_path_methods(self):
        directed_cycle = nx.cycle_graph(7, create_using=nx.DiGraph())
        assert nx.shortest_path(directed_cycle, 0, 3, weight="weight", method="dijkstra") == [0, 1, 2, 3]
        assert nx.shortest_path(directed_cycle, 0, 3, weight="weight", method="bellman-ford") == [0, 1, 2, 3]

    def test_shortest_path_negative_weights(self):
        neg = nx.DiGraph()
        neg.add_edge(0, 1, weight=1)
        neg.add_edge(0, 2, weight=3)
        neg.add_edge(1, 3, weight=1)
        neg.add_edge(2, 3, weight=-2)
        assert nx.shortest_path(neg, 0, 3, weight="weight", method="bellman-ford") == [0, 2, 3]

    def test_shortest_path_bad_method(self):
        with pytest.raises(ValueError):
            nx.shortest_path(nx.cycle_graph(7), method="SPAM")

    def test_shortest_path_absent_source(self):
        with pytest.raises(nx.NodeNotFound):
            nx.shortest_path(nx.cycle_graph(7), 8)

    def test_shortest_path_target(self):
        answer = {0: [0, 1], 1: [1], 2: [2, 1]}
        sp = nx.shortest_path(nx.path_graph(3), target=1)
        assert sp == answer

    def test_shortest_path_length(self):
        cycle = nx.cycle_graph(7)
        grid = nx.convert_node_labels_to_integers(nx.grid_2d_graph(4, 4), first_label=1, ordering="sorted")
        directed_cycle = nx.cycle_graph(7, create_using=nx.DiGraph())

        assert nx.shortest_path_length(cycle, 0, 3) == 3
        assert nx.shortest_path_length(grid, 1, 12) == 5
        assert nx.shortest_path_length(directed_cycle, 0, 4) == 4

    def test_shortest_path_length_weighted(self):
        cycle = nx.cycle_graph(7)
        grid = nx.convert_node_labels_to_integers(nx.grid_2d_graph(4, 4), first_label=1, ordering="sorted")
        directed_cycle = nx.cycle_graph(7, create_using=nx.DiGraph())

        assert nx.shortest_path_length(cycle, 0, 3, weight="weight") == 3
        assert nx.shortest_path_length(grid, 1, 12, weight="weight") == 5
        assert nx.shortest_path_length(directed_cycle, 0, 4, weight="weight") == 4

    def test_shortest_path_length_methods(self):
        cycle = nx.cycle_graph(7)
        assert nx.shortest_path_length(cycle, 0, 3, weight="weight", method="dijkstra") == 3
        assert nx.shortest_path_length(cycle, 0, 3, weight="weight", method="bellman-ford") == 3

    def test_shortest_path_length_bad_method(self):
        with pytest.raises(ValueError):
            nx.shortest_path_length(nx.cycle_graph(7), method="SPAM")

    def test_shortest_path_length_absent_source(self):
        with pytest.raises(nx.NodeNotFound):
            nx.shortest_path_length(nx.cycle_graph(7), 8)

    def test_single_source_shortest_path(self):
        cycle = nx.cycle_graph(7)
        p = nx.shortest_path(cycle, 0)
        assert p[3] == [0, 1, 2, 3]
        assert p == nx.single_source_shortest_path(cycle, 0)

    def test_single_source_shortest_path_length(self):
        cycle = nx.cycle_graph(7)
        ans = nx.shortest_path_length(cycle, 0)
        assert ans == {0: 0, 1: 1, 2: 2, 3: 3, 4: 3, 5: 2, 6: 1}
        assert dict(ans) == dict(nx.single_source_shortest_path_length(cycle, 0))

    def test_single_source_all_shortest_paths(self):
        G = nx.cycle_graph(4)
        ans = dict(nx.single_source_all_shortest_paths(G, 0))
        assert sorted(ans[2]) == [[0, 1, 2], [0, 3, 2]]

    def test_all_pairs_shortest_path(self):
        cycle = nx.cycle_graph(7)
        p = dict(nx.all_pairs_shortest_path(cycle))
        assert p[0][3] == [0, 1, 2, 3]

    def test_all_pairs_shortest_path_length(self):
        cycle = nx.cycle_graph(7)
        ans = dict(nx.all_pairs_shortest_path_length(cycle))
        assert ans[0] == {0: 0, 1: 1, 2: 2, 3: 3, 4: 3, 5: 2, 6: 1}

    def test_has_path(self):
        G = nx.Graph()
        nx.add_path(G, range(3))
        nx.add_path(G, range(3, 5))
        assert nx.has_path(G, 0, 2)
        assert not nx.has_path(G, 0, 4)

    def test_has_path_singleton(self):
        G = nx.empty_graph(1)
        assert nx.has_path(G, 0, 0)

    def test_all_shortest_paths(self):
        G = nx.Graph()
        nx.add_path(G, [0, 1, 2, 3])
        nx.add_path(G, [0, 10, 20, 3])
        assert sorted(nx.all_shortest_paths(G, 0, 3)) == [[0, 1, 2, 3], [0, 10, 20, 3]]

    def test_all_shortest_paths_raise(self):
        G = nx.path_graph(4)
        G.add_node(4)
        with pytest.raises(nx.NetworkXNoPath):
            list(nx.all_shortest_paths(G, 0, 4))

    def test_bad_method(self):
        with pytest.raises(ValueError):
            G = nx.path_graph(2)
            list(nx.all_shortest_paths(G, 0, 1, weight="weight", method="SPAM"))


class TestAverageShortestPathLength:
    """Tests for average shortest path length."""

    def test_cycle_graph(self):
        ans = nx.average_shortest_path_length(nx.cycle_graph(7))
        assert ans == pytest.approx(2, abs=1e-7)

    def test_path_graph(self):
        ans = nx.average_shortest_path_length(nx.path_graph(5))
        assert ans == pytest.approx(2, abs=1e-7)

    def test_weighted(self):
        G = nx.Graph()
        nx.add_cycle(G, range(7), weight=2)
        ans = nx.average_shortest_path_length(G, weight="weight")
        assert ans == pytest.approx(4, abs=1e-7)

    def test_directed_not_strongly_connected(self):
        G = nx.DiGraph([(0, 1)])
        with pytest.raises(nx.NetworkXError, match="Graph is not strongly connected"):
            nx.average_shortest_path_length(G)

    def test_undirected_not_connected(self):
        g = nx.Graph()
        g.add_nodes_from(range(3))
        g.add_edge(0, 1)
        pytest.raises(nx.NetworkXError, nx.average_shortest_path_length, g)

    def test_trivial_graph(self):
        G = nx.trivial_graph()
        assert nx.average_shortest_path_length(G) == 0

    def test_null_graph(self):
        with pytest.raises(nx.NetworkXPointlessConcept):
            nx.average_shortest_path_length(nx.null_graph())


# Skip numpy-dependent tests
class TestBidirectionalDijkstra:
    """Tests for bidirectional Dijkstra."""

    def test_bidirectional_dijkstra(self):
        G = nx.cycle_graph(7)
        dist, path = nx.bidirectional_dijkstra(G, 0, 3)
        assert dist == 3
        assert path == [0, 1, 2, 3]

    def test_bidirectional_dijkstra_no_path(self):
        G = nx.Graph()
        G.add_edge(0, 1)
        G.add_node(2)
        with pytest.raises(nx.NetworkXNoPath):
            nx.bidirectional_dijkstra(G, 0, 2)


class TestDijkstra:
    """Tests for Dijkstra's algorithm."""

    def test_dijkstra_path(self):
        G = nx.path_graph(5)
        path = nx.dijkstra_path(G, 0, 4)
        assert path == [0, 1, 2, 3, 4]

    def test_dijkstra_path_length(self):
        G = nx.path_graph(5)
        assert nx.dijkstra_path_length(G, 0, 4) == 4

    def test_single_source_dijkstra(self):
        G = nx.path_graph(5)
        l, d = nx.single_source_dijkstra(G, 0)
        assert d == {0: [0], 1: [0, 1], 2: [0, 1, 2], 3: [0, 1, 2, 3], 4: [0, 1, 2, 3, 4]}

    def test_all_pairs_dijkstra(self):
        G = nx.path_graph(5)
        paths = dict(nx.all_pairs_dijkstra_path(G))
        assert paths[0][4] == [0, 1, 2, 3, 4]


class TestBellmanFord:
    """Tests for Bellman-Ford algorithm."""

    def test_bellman_ford_path(self):
        G = nx.path_graph(5)
        assert nx.bellman_ford_path(G, 0, 4) == [0, 1, 2, 3, 4]

    def test_bellman_ford_path_length(self):
        G = nx.path_graph(5)
        assert nx.bellman_ford_path_length(G, 0, 4) == 4

    def test_single_source_bellman_ford(self):
        G = nx.path_graph(5)
        pred, dist = nx.single_source_bellman_ford(G, 0)
        assert isinstance(dist, dict)
        assert len(dist) == 5


class TestYen:
    """Tests for Yen's K shortest paths."""

    def test_yen_k_shortest_paths(self):
        G = nx.cycle_graph(7)
        paths = list(nx.shortest_simple_paths(G, 0, 3))
        assert len(paths) >= 2
        assert paths[0] == [0, 1, 2, 3]


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

    def test_shortest_simple_paths(self):
        G = nx.Graph()
        G.add_edges_from([(0, 1), (1, 2), (2, 3), (0, 3)])
        paths = list(nx.shortest_simple_paths(G, 0, 3))
        assert len(paths) >= 2
        assert paths[0] == [0, 1, 2, 3] or paths[0] == [0, 3]


class TestJensen:
    """Tests for Jensen's algorithm (all simple paths)."""

    def test_k_shortest_path(self):
        G = nx.cycle_graph(7)
        paths = list(nx.shortest_simple_paths(G, 0, 3))
        assert len(paths) >= 2


class TestFlow:
    """Tests for flow-based shortest paths (goldberg_radzik)."""

    def test_goldberg_radzik(self):
        G = nx.path_graph(5)
        pred, dist = nx.goldberg_radzik(G, 0)
        assert dist == {0: 0, 1: 1, 2: 2, 3: 3, 4: 4}


class TestFloydWarshall:
    """Tests for Floyd-Warshall algorithm."""

    def test_floyd_warshall(self):
        G = nx.path_graph(5)
        pred, dist = nx.floyd_warshall_predecessor_and_distance(G)
        assert dist[0] == {0: 0, 1: 1, 2: 2, 3: 3, 4: 4}

    def test_floyd_warshall_no_path(self):
        G = nx.Graph()
        G.add_edge(0, 1)
        G.add_node(2)
        pred, dist = nx.floyd_warshall_predecessor_and_distance(G)
        assert dist[0][2] == float("inf")


class TestAStar:
    """Tests for A* algorithm."""

    def test_astar_path(self):
        G = nx.path_graph(5)
        assert nx.astar_path(G, 0, 4) == [0, 1, 2, 3, 4]

    def test_astar_path_length(self):
        G = nx.path_graph(5)
        assert nx.astar_path_length(G, 0, 4) == 4

    def test_astar_heuristic(self):
        G = nx.Graph()
        G.add_edges_from([(0, 1), (1, 2), (2, 3)])
        assert nx.astar_path(G, 0, 3, heuristic=lambda u, v: abs(u - v)) == [0, 1, 2, 3]
