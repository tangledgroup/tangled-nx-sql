"""Demonstrate graph properties computation with nx_sql.

Mirrors networkx/examples/basic/plot_properties.py but uses SQLAlchemy persistence.
Computes density, shortest path lengths, eccentricity, radius, diameter, center, periphery.
"""

import math
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
def demo_graph_properties():
    """Compute various graph properties on a lollipop graph."""

    with Session() as session:
        # Create a lollipop graph (complete graph connected to a path)
        G_nx = nx.lollipop_graph(4, 3)
        edges = list(G_nx.edges(data=True))
        nodes = list(G_nx.nodes(data=True))

        G = nx_sql.Graph(session, name="lollipop_properties")
        # Pass only node IDs to add_nodes_from (not (node, attrs) tuples
        # to avoid key normalization conflicts with tuple keys)
        for n, d in nodes:
            if d:
                G.add_node(n, **d)
            else:
                G.add_node(n)
        G.add_edges_from(edges)

        # Density
        density = nx.density(G)
        print(f"Density: {density:.4f}")

        # All pairs shortest path lengths
        sp_lengths = dict(nx.all_pairs_shortest_path_length(G))
        print(f"\nAll-pairs shortest path lengths:")
        for node, lengths in sorted(sp_lengths.items(), key=lambda x: str(x[0])):
            print(f"  From {node}: {dict(lengths)}")

        # Average shortest path length
        avg_len = nx.average_shortest_path_length(G)
        print(f"\nAverage shortest path length: {avg_len:.2f}")

        # Eccentricity
        ecc = nx.eccentricity(G)
        print(f"\nEccentricities: {ecc}")

        # Radius (min eccentricity)
        radius = nx.radius(G)
        print(f"Radius: {radius}")

        # Diameter (max eccentricity)
        diameter = nx.diameter(G)
        print(f"Diameter: {diameter}")

        # Center (nodes with eccentricity == radius)
        center = nx.center(G)
        print(f"Center nodes: {center}")

        # Periphery (nodes with eccentricity == diameter)
        periphery = nx.periphery(G)
        print(f"Periphery nodes: {periphery}")

        # Path length distribution
        path_lengths = list(sp_lengths.values())
        max_len = max(max(v.values()) for v in path_lengths)
        dist = [0] * (max_len + 1)
        for node_lengths in path_lengths:
            for l in node_lengths.values():
                dist[l] += 1
        # Divide by n*(n-1) to normalize
        n = G.number_of_nodes()
        print(f"\nPath length distribution (normalized):")
        for i, count in enumerate(dist):
            print(f"  Length {i}: {count / (n * (n - 1)):.2%}")

        session.commit()


if __name__ == "__main__":
    demo_graph_properties()
