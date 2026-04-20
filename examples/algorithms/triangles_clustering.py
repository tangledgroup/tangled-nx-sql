"""Demonstrate triangles and clustering with nx_sql.

Tests triangle counting, local clustering coefficient, and average clustering.
Clustering measures how close nodes are to forming a clique.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def demo_triangles_clustering():
    """Compute triangles and clustering coefficients."""

    with Session() as session:
        G_nx = nx.karate_club_graph()
        G = nx_sql.Graph(session, name="triangles_clustering_demo")
        G.add_nodes_from(G_nx.nodes())
        G.add_edges_from(G_nx.edges())

        print(f"=== Triangles & Clustering ===")
        print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

        # Triangle count per node
        triangles = nx.triangles(G)
        print(f"\nTriangles per node:")
        for node, count in sorted(triangles.items(), key=lambda x: x[1], reverse=True):
            print(f"  Node {node}: {count} triangles")

        total_triangles = sum(triangles.values()) // 3
        print(f"\nTotal triangles: {total_triangles}")

        # Local clustering coefficient per node
        clustering = nx.clustering(G)
        print(f"\nClustering coefficients (top 10):")
        for node, cc in sorted(clustering.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  Node {node}: {cc:.4f}")

        # Average clustering
        avg_cc = nx.average_clustering(G)
        print(f"\nAverage clustering coefficient: {avg_cc:.4f}")

        # Weighted clustering
        G_weighted = nx_sql.Graph(session, name="weighted_clustering")
        G_weighted.add_nodes_from(G_nx.nodes())
        for u, v in G_nx.edges():
            G_weighted.add_edge(u, v, weight=1.0 / (1 + G_nx[u][v].get('weight', 1)))
        weighted_cc = nx.average_clustering(G_weighted, weight='weight')
        print(f"Average weighted clustering: {weighted_cc:.4f}")

        # Degree vs clustering correlation
        degrees = [d for n, d in G.degree()]
        cc_values = list(clustering.values())
        print(f"\nDegree stats:")
        print(f"  Mean degree: {sum(degrees)/len(degrees):.2f}")
        print(f"  CC stats: mean={sum(cc_values)/len(cc_values):.4f}, "
              f"min={min(cc_values):.4f}, max={max(cc_values):.4f}")

        session.commit()


if __name__ == "__main__":
    demo_triangles_clustering()
