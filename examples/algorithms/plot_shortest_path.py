"""Demonstrate shortest path algorithms with nx_sql.

Mirrors networkx/examples/algorithms/plot_shortest_path.py but uses SQLAlchemy persistence.
Tests Dijkstra's shortest path, all shortest paths, and weighted edges.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base
import sys; sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent.parent.parent))
from examples.utils import print_docstring

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


@print_docstring
def demo_shortest_path():
    """Test Dijkstra shortest path and all shortest paths on weighted graphs."""

    with Session() as session:
        G = nx_sql.Graph(session, name="shortest_path_demo")

        # Build a weighted graph
        edges = [
            ("A", "B", 7),
            ("A", "C", 9),
            ("A", "F", 14),
            ("B", "C", 10),
            ("B", "D", 15),
            ("C", "D", 11),
            ("C", "F", 2),
            ("D", "E", 6),
            ("E", "F", 9),
        ]
        G.add_edges_from(edges)

        print("=== Dijkstra Shortest Path ===")
        path = nx.shortest_path(G, "A", "E", weight="weight")
        print(f"Shortest path A->E: {path}")

        # Verify with networkx on in-memory graph
        G_nx = nx.Graph(G.edges(data=True))
        nx_path = nx.shortest_path(G_nx, "A", "E", weight="weight")
        assert path == nx_path, f"Mismatch: {path} vs {nx_path}"
        print(f"✓ Matches in-memory NetworkX result")

        # All shortest paths
        print("\n=== All Shortest Paths ===")
        all_paths = list(nx.all_shortest_paths(G, "A", "E", weight="weight"))
        print(f"All shortest paths A->E: {all_paths}")

        # Single source shortest path
        print("\n=== Single Source Shortest Path (from A) ===")
        sp = nx.single_source_shortest_path(G, "A")
        for target, path in sorted(sp.items()):
            if target != "A":
                print(f"  A -> {target}: {' -> '.join(path)}")

        # Single source shortest path length (unweighted)
        print("\n=== Shortest Path Lengths (unweighted) ===")
        spl = nx.single_source_shortest_path_length(G, "A")
        for target, length in sorted(spl.items()):
            if target != "A":
                print(f"  A -> {target}: {length}")

        # All pairs shortest path
        print("\n=== All Pairs Shortest Path ===")
        apsp = dict(nx.all_pairs_shortest_path(G))
        for source in sorted(apsp.keys()):
            for target, path in sorted(apsp[source].items()):
                if source < target:
                    print(f"  {source} -> {target}: {' -> '.join(str(n) for n in path)}")

        session.commit()


if __name__ == "__main__":
    demo_shortest_path()
