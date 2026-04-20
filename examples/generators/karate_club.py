"""Demonstrate Zachary's karate club graph with nx_sql.

Mirrors networkx/examples/graph/plot_karate_club.py but uses
SQLAlchemy persistence. Tests the famous social network graph.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def demo_karate_club():
    """Create and analyze the karate club graph."""

    with Session() as session:
        G_nx = nx.karate_club_graph()

        G = nx_sql.Graph(session, name="karate_club_demo")
        for node in G_nx.nodes():
            G.add_node(node)
        G.add_edges_from(G_nx.edges())

        print("=== Zachary's Karate Club Graph ===")
        print(f"Nodes: {G.number_of_nodes()}")
        print(f"Edges: {G.number_of_edges()}")

        # Node degrees
        print("\nNode degrees:")
        for node in sorted(G.nodes()):
            degree = G.degree(node)
            bar = "#" * degree
            print(f"  Node {node:2d}: {degree:2d} {bar}")

        # Graph properties
        print(f"\nDensity: {nx.density(G):.4f}")
        print(f"Diameter: {nx.diameter(G)}")
        print(f"Average shortest path length: {nx.average_shortest_path_length(G):.2f}")
        print(f"Average clustering coefficient: {nx.average_clustering(G):.4f}")

        # Degree distribution
        degrees = [d for n, d in G.degree()]
        from collections import Counter
        degree_counts = Counter(degrees)
        print("\nDegree distribution:")
        for deg in sorted(degree_counts.keys()):
            bar = "#" * degree_counts[deg]
            print(f"  Degree {deg:2d}: {degree_counts[deg]:2d} nodes {bar}")

        session.commit()

    # Verify persistence
    with Session() as session:
        from nx_sql.models import Graph as GraphModel
        gmodel = session.execute(
            nx_sql.select(GraphModel).where(GraphModel.name == "karate_club_demo")
        ).scalar_one()
        G2 = nx_sql.Graph(session, graph_id=gmodel.graph_id)
        print(f"\nReloaded from DB: {G2.number_of_nodes()} nodes, {G2.number_of_edges()} edges")
        session.commit()


if __name__ == "__main__":
    demo_karate_club()
