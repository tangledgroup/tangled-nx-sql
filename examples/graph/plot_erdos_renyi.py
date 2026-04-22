"""Demonstrate Erdos-Renyi random graph with nx_sql.

Mirrors networkx/examples/graph/plot_erdos_renyi.py but uses
SQLAlchemy persistence. Tests gnm_random_graph properties.
"""

from collections import Counter

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
def demo_erdos_renyi():
    """Create and analyze an Erdos-Renyi random graph."""

    with Session() as session:
        n, m = 20, 50  # 20 nodes, 50 edges
        G_nx = nx.gnm_random_graph(n, m, seed=42)

        G = nx_sql.Graph(session, name="erdos_renyi_demo")
        for node in G_nx.nodes():
            G.add_node(node)
        G.add_edges_from(G_nx.edges())

        print("=== Erdos-Renyi Random Graph ===")
        print(f"n={n}, m={m}")
        print(f"Nodes: {G.number_of_nodes()}")
        print(f"Edges: {G.number_of_edges()}")

        # Density
        density = nx.density(G)
        expected_density = m / (n * (n - 1) / 2)
        print(f"\nDensity: {density:.4f} (expected: {expected_density:.4f})")

        # Degree sequence
        degrees = [d for n, d in G.degree()]
        print(f"\nDegree sequence: {sorted(degrees)}")
        print(f"Min degree: {min(degrees)}")
        print(f"Max degree: {max(degrees)}")
        print(f"Average degree: {sum(degrees) / len(degrees):.2f}")

        # Clustering coefficient per node
        clustering = nx.clustering(G)
        avg_clustering = sum(clustering.values()) / len(clustering)
        print(f"\nAverage clustering coefficient: {avg_clustering:.4f}")

        # Print adjacency list (first 5 nodes)
        print("\nAdjacency list (first 5 nodes):")
        for i in range(min(5, G.number_of_nodes())):
            neighbors = list(G.neighbors(i))
            print(f"  {i}: {sorted(neighbors)}")

        # Degree histogram
        degree_counts = Counter(degrees)
        print("\nDegree histogram:")
        for deg in sorted(degree_counts.keys()):
            bar = "#" * degree_counts[deg]
            print(f"  Degree {deg}: {degree_counts[deg]} nodes {bar}")

        session.commit()


if __name__ == "__main__":
    demo_erdos_renyi()
