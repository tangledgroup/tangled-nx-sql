"""Demonstrate expected degree sequence graph generation with nx_sql.

Mirrors networkx/examples/graph/plot_expected_degree_sequence.py but uses
SQLAlchemy persistence. Tests expected_degree_graph and degree histogram.
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
def demo_expected_degree_sequence():
    """Create a random graph from an expected degree sequence."""

    with Session() as session:
        # Create a graph with expected degree ~50 for each of 500 nodes
        n = 500
        p = 0.1
        w = [p * n for _ in range(n)]

        print("=== Expected Degree Sequence ===")
        print(f"n={n}, expected degree per node={w[0]}")

        G_nx = nx.expected_degree_graph(w, seed=42)

        G = nx_sql.Graph(session, name="expected_degree_demo")
        for node in G_nx.nodes():
            G.add_node(node)
        G.add_edges_from(G_nx.edges())

        print(f"\nGenerated graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

        # Degree histogram
        degrees = [d for _, d in G.degree()]
        from collections import Counter
        degree_counts = Counter(degrees)

        print("\nDegree histogram")
        print(f"degree (#nodes) ****")
        for deg in sorted(degree_counts.keys()):
            count = degree_counts[deg]
            bar = "*" * min(count, 100)
            print(f"{deg:2d} ({count:3d}) {bar}")

        # Compare expected vs actual average degree
        avg_actual = sum(degrees) / len(degrees)
        print(f"\nExpected average degree: {sum(w)/len(w):.1f}")
        print(f"Actual average degree: {avg_actual:.1f}")

        # Graph properties
        print(f"\nDensity: {nx.density(G):.6f}")
        print(f"Min degree: {min(degrees)}")
        print(f"Max degree: {max(degrees)}")

        session.commit()


if __name__ == "__main__":
    demo_expected_degree_sequence()
