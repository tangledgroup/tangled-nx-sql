"""Demonstrate ego graph (local neighborhood) with nx_sql.

Tests extracting the subgraph within a given radius of a node.
Shows how to inspect local neighborhoods in SQL-backed graphs.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def demo_ego_graph():
    """Extract ego subgraphs at different radii from a central node."""

    with Session() as session:
        # Create a small world-ish graph
        G_nx = nx.karate_club_graph()
        G = nx_sql.Graph(session, name="ego_graph_demo")
        G.add_nodes_from(G_nx.nodes())
        G.add_edges_from(G_nx.edges())

        center = 0
        print(f"=== Ego Graph for node {center} ===")
        print(f"Full graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        print(f"Node {center} degree: {G.degree(center)}")

        # Ego graph at radius 1 (direct neighbors only)
        ego1 = nx.ego_graph(G, center, radius=1)
        print(f"\nEgo graph (radius=1): {ego1.number_of_nodes()} nodes, {ego1.number_of_edges()} edges")
        print(f"Nodes: {sorted(ego1.nodes())}")
        print(f"Edges: {list(ego1.edges())}")

        # Ego graph at radius 2
        ego2 = nx.ego_graph(G, center, radius=2)
        print(f"\nEgo graph (radius=2): {ego2.number_of_nodes()} nodes, {ego2.number_of_edges()} edges")

        # Ego graph at radius 3
        ego3 = nx.ego_graph(G, center, radius=3)
        print(f"\nEgo graph (radius=3): {ego3.number_of_nodes()} nodes, {ego3.number_of_edges()} edges")

        # Compare local density vs global density
        full_density = nx.density(G)
        ego1_density = nx.density(ego1)
        ego2_density = nx.density(ego2)
        print(f"\nDensity comparison:")
        print(f"  Full graph: {full_density:.4f}")
        print(f"  Ego (r=1):  {ego1_density:.4f}")
        print(f"  Ego (r=2):  {ego2_density:.4f}")

        # Local clustering
        print(f"\nLocal clustering at center {center}: {nx.clustering(G, center):.4f}")
        avg_clustering = nx.average_clustering(G)
        print(f"Average clustering (full graph): {avg_clustering:.4f}")
        avg_clustering_ego = nx.average_clustering(ego2)
        print(f"Average clustering (ego r=2):     {avg_clustering_ego:.4f}")

        session.commit()


if __name__ == "__main__":
    demo_ego_graph()
