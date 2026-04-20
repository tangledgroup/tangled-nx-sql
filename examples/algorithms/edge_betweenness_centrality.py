"""Demonstrate edge betweenness centrality with nx_sql.

Tests computing edge betweenness centrality — the fraction of shortest paths
that pass through each edge. Identifies bottleneck edges in the network.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def demo_edge_betweenness():
    """Compute edge betweenness centrality on a graph."""

    with Session() as session:
        G_nx = nx.karate_club_graph()
        G = nx_sql.Graph(session, name="edge_betweenness_demo")
        G.add_nodes_from(G_nx.nodes())
        G.add_edges_from(G_nx.edges())

        print(f"=== Edge Betweenness Centrality ===")
        print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

        # Compute edge betweenness centrality
        eb = nx.edge_betweenness_centrality(G, k=None)
        print(f"\nTop 10 edges by betweenness:")
        sorted_edges = sorted(eb.items(), key=lambda x: x[1], reverse=True)[:10]
        for (u, v), bc in sorted_edges:
            print(f"  Edge ({u}, {v}): {bc:.4f}")

        # Normalized edge betweenness
        eb_norm = nx.edge_betweenness_centrality(G, normalized=True)
        print(f"\nTop 5 edges by normalized betweenness:")
        sorted_edges_norm = sorted(eb_norm.items(), key=lambda x: x[1], reverse=True)[:5]
        for (u, v), bc in sorted_edges_norm:
            print(f"  Edge ({u}, {v}): {bc:.4f}")

        # Identify bridge-like edges (high betweenness)
        threshold = max(eb.values()) * 0.5
        critical_edges = [(u, v) for (u, v), bc in eb.items() if bc >= threshold]
        print(f"\nCritical edges (betweenness > {threshold:.4f}): {critical_edges}")

        # Compare with node betweenness
        nb = nx.betweenness_centrality(G)
        top_nodes = sorted(nb.items(), key=lambda x: x[1], reverse=True)[:5]
        print(f"\nTop 5 nodes by betweenness centrality:")
        for node, bc in top_nodes:
            print(f"  Node {node}: {bc:.4f}")

        session.commit()


if __name__ == "__main__":
    demo_edge_betweenness()
