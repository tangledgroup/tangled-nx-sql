"""Demonstrate betweenness centrality with nx_sql.

Mirrors networkx/examples/algorithms/plot_betweenness_centrality.py but uses
SQLAlchemy persistence. Tests betweenness centrality on a real dataset.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def demo_betweenness_centrality():
    """Compute betweenness centrality on the karate club graph."""

    with Session() as session:
        # Use karate club graph — a real social network dataset
        G_nx = nx.karate_club_graph()

        G = nx_sql.Graph(session, name="betweenness_demo")
        G.add_nodes_from(G_nx.nodes())
        G.add_edges_from(G_nx.edges())

        print("=== Betweenness Centrality ===")
        bc = nx.betweenness_centrality(G, k=10)
        # Sort by centrality
        top_nodes = sorted(bc.items(), key=lambda x: x[1], reverse=True)[:10]
        print(f"Top 10 nodes by betweenness centrality:")
        for node, score in top_nodes:
            print(f"  Node {node}: {score:.4f}")

        # Also compute degree centrality for comparison
        print("\n=== Degree Centrality (top 10) ===")
        dc = nx.degree_centrality(G)
        top_dc = sorted(dc.items(), key=lambda x: x[1], reverse=True)[:10]
        for node, score in top_dc:
            print(f"  Node {node}: {score:.4f}")

        # Closeness centrality
        print("\n=== Closeness Centrality (top 10) ===")
        cc = nx.closeness_centrality(G)
        top_cc = sorted(cc.items(), key=lambda x: x[1], reverse=True)[:10]
        for node, score in top_cc:
            print(f"  Node {node}: {score:.4f}")

        session.commit()


if __name__ == "__main__":
    demo_betweenness_centrality()
