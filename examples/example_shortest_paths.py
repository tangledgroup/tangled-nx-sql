"""example_shortest_paths.py - Shortest path algorithms.

Covers: shortest_path, all_shortest_paths, single_source_shortest_path,
        all_pairs_shortest_path_length, shortest_path_length,
        weighted shortest paths (Dijkstra), k_shortest_paths.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)


def demo_unweighted():
    """Unweighted shortest path (BFS-based)."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="unweighted_path")

        # Build a grid-like graph
        edges = [
            (1, 2), (2, 3), (3, 4),
            (1, 5), (5, 6), (6, 4),
            (2, 7), (7, 8), (8, 4),
        ]
        G.add_edges_from(edges)

        path = nx.shortest_path(G, 1, 4)
        print(f"Shortest path 1→4: {path}")
        print(f"Length: {nx.shortest_path_length(G, 1, 4)}")

        all_paths = list(nx.all_shortest_paths(G, 1, 4))
        print(f"All shortest paths: {all_paths}")

        session.commit()


def demo_weighted():
    """Weighted shortest path (Dijkstra)."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="weighted_path")

        # City distance network
        cities = [
            ("NewYork", "Boston", 215),
            ("NewYork", "Philadelphia", 95),
            ("Philadelphia", "Washington", 140),
            ("Boston", "Hartford", 130),
            ("Philadelphia", "Hartford", 180),
            ("Hartford", "Boston", 130),
        ]
        G.add_edges_from((u, v, {"distance": d}) for u, v, d in cities)

        # Direct vs indirect
        direct = nx.shortest_path(G, "NewYork", "Boston", weight="distance")
        print(f"Direct path NY→BOS: {direct} ({nx.shortest_path_length(G, 'NewYork', 'Boston', weight='distance')} mi)")

        all_ways = list(nx.all_shortest_paths(G, "NewYork", "Washington", weight="distance"))
        print(f"All shortest paths NY→DC: {all_ways}")

        session.commit()


def demo_all_pairs():
    """All-pairs shortest paths."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="all_pairs")

        edges = [(1, 2, {"weight": 1}), (2, 3, {"weight": 2}), (1, 3, {"weight": 10}), (3, 4, {"weight": 1})]
        G.add_edges_from(edges)

        # All pairs shortest path lengths
        lengths = dict(nx.all_pairs_shortest_path_length(G))
        print("All pairs shortest path lengths:")
        for src, lens in lengths.items():
            print(f"  From {src}: {dict(lens)}")

        # Single source shortest paths (tree)
        paths = nx.single_source_shortest_path(G, 1)
        print(f"\nShortest path tree from 1: {paths}")

        session.commit()


def demo_dag_paths():
    """Shortest/longest paths in DAGs."""
    with SessionLocal() as session:
        G = nx_sql.DiGraph(session, name="dag_paths")

        # Task dependency graph with durations
        tasks = [
            ("A", "B", 3), ("A", "C", 5),
            ("B", "D", 2), ("C", "D", 1),
            ("C", "E", 4), ("D", "F", 2),
            ("E", "F", 1),
        ]
        G.add_edges_from((u, v, {"duration": d}) for u, v, d in tasks)

        print(f"Shortest path A→F: {nx.shortest_path(G, 'A', 'F')}")
        print(f"Longest path A→F (critical path): {nx.dag_longest_path(G, weight='duration')}")
        print(f"Longest path length: {nx.dag_longest_path_length(G, weight='duration')}")

        session.commit()


if __name__ == "__main__":
    demo_unweighted()
    demo_weighted()
    demo_all_pairs()
    demo_dag_paths()
