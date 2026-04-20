"""Demonstrate MultiGraph and MultiDiGraph with nx_sql.

Tests multi-edge support, key-based edge access, and parallel edges.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def demo_multigraph():
    """Test MultiGraph multi-edge functionality."""

    with Session() as session:
        G = nx_sql.MultiGraph(session, name="multigraph_demo")

        print("=== MultiGraph ===")

        # Add multiple edges between same nodes
        G.add_edge(1, 2, weight=5, color="red")
        G.add_edge(1, 2, weight=7, color="blue")
        G.add_edge(1, 2, weight=3, color="green")
        G.add_edge(2, 3, weight=10)
        G.add_edge(2, 3, weight=8)

        print(f"Nodes: {list(G.nodes())}")
        print(f"Edge count: {G.number_of_edges()}")

        # Check multi-edges
        print(f"\nEdges between 1 and 2:")
        for key, data in G[1][2].items():
            print(f"  Key {key}: {data}")

        print(f"\nEdges between 2 and 3:")
        for key, data in G[2][3].items():
            print(f"  Key {key}: {data}")

        # Edge keys should be auto-generated
        assert len(G[1][2]) == 3, "Should have 3 edges between 1 and 2"
        assert len(G[2][3]) == 2, "Should have 2 edges between 2 and 3"
        print("✓ Multi-edge count correct")

        # Test iteration — iterate over adjacency dict for multi-edges
        print(f"\nAll edges:")
        seen = set()
        for u in G.nodes():
            for v, key_data in G[u].items():
                if isinstance(key_data, dict):
                    for key, data in sorted(key_data.items()):
                        edge_key = tuple(sorted([u, v])) + (key,)
                        if edge_key not in seen:
                            seen.add(edge_key)
                            print(f"  {u} --{key}--> {v}: {data}")

        session.commit()

    with Session() as session:
        # Test MultiDiGraph
        print("\n=== MultiDiGraph ===")
        G = nx_sql.MultiDiGraph(session, name="multidigraph_demo")

        G.add_edge("A", "B", weight=1, flight="AA100")
        G.add_edge("A", "B", weight=2, flight="BB200")
        G.add_edge("B", "A", weight=3, flight="CC300")  # reverse direction
        G.add_edge("B", "C", weight=4, flight="DD400")

        print(f"Nodes: {list(G.nodes())}")
        print(f"Edge count: {G.number_of_edges()}")

        # Check directed multi-edges
        print(f"\nA -> B edges:")
        for key, data in G["A"]["B"].items():
            print(f"  Key {key}: {data}")

        print(f"\nB -> A edges:")
        for key, data in G["B"]["A"].items():
            print(f"  Key {key}: {data}")

        assert len(G["A"]["B"]) == 2, "Should have 2 edges from A to B"
        assert len(G["B"]["A"]) == 1, "Should have 1 edge from B to A"
        print("✓ MultiDiGraph multi-edges correct")

        session.commit()


if __name__ == "__main__":
    demo_multigraph()
