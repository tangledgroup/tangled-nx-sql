"""Demonstrate configuration model from degree sequence with nx_sql.

Mirrors networkx/examples/graph/plot_degree_sequence.py but uses
SQLAlchemy persistence. Tests configuration model and degree histogram.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def demo_degree_sequence():
    """Create a graph from a degree sequence using the configuration model."""

    with Session() as session:
        # Define a degree sequence
        z = [5, 4, 4, 3, 3, 3, 3, 2, 2, 2, 2, 2, 2, 2, 3]  # sum = 42 (even)

        print("=== Configuration Model ===")
        print(f"Degree sequence: {z}")
        print(f"Sum of degrees: {sum(z)} (must be even)")
        print(f"Number of nodes: {len(z)}")

        # Create graph using configuration model
        G_nx = nx.configuration_model(z, seed=42)

        G = nx_sql.MultiGraph(session, name="degree_sequence_demo")
        for node in G_nx.nodes():
            G.add_node(node)
        # configuration_model may create self-loops and multi-edges
        edges = list(G_nx.edges())
        G.add_edges_from(edges)

        print(f"\nGenerated graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

        # Verify degree sequence
        actual_degrees = [d for n, d in G.degree()]
        print(f"Actual degree sequence: {sorted(actual_degrees)}")

        # Check if it matches (may differ due to self-loops)
        original_sorted = sorted(z)
        actual_sorted = sorted(actual_degrees)
        match = original_sorted == actual_sorted
        print(f"Degree sequence matches input: {match}")

        # Degree histogram
        from collections import Counter
        degree_counts = Counter(actual_degrees)
        print("\nDegree histogram:")
        for deg in sorted(degree_counts.keys()):
            bar = "#" * degree_counts[deg]
            print(f"  Degree {deg}: {degree_counts[deg]} nodes {bar}")

        # Check for self-loops and multi-edges
        try:
            self_loops = list(G.selfloop_edges())
            print(f"\nSelf-loops: {len(self_loops)}")
        except AttributeError:
            # MultiGraph doesn't have selfloop_edges()
            self_loops = [(u, v) for u, v in G.edges() if u == v]
            print(f"\nSelf-loops: {len(self_loops)}")

        # Count multi-edges (edges appearing more than once)
        edge_counts = Counter((u, v) for u, v in G.edges())
        multi_edges = {e: c for e, c in edge_counts.items() if c > 1}
        print(f"Multi-edges (unique node pairs with multiple edges): {len(multi_edges)}")

        session.commit()


if __name__ == "__main__":
    demo_degree_sequence()
