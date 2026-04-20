"""Demonstrate PageRank with nx_sql.

Tests the PageRank algorithm — a node ranking algorithm based on link structure.
Shows how to compute personalized PageRank and compare with uniform ranking.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def demo_pagerank():
    """Compute PageRank on a web-like graph."""

    with Session() as session:
        # Create a web-like graph
        G_nx = nx.DiGraph()
        G_nx.add_edges_from([
            ('A', 'B'), ('A', 'C'), ('B', 'C'), ('B', 'D'),
            ('C', 'D'), ('D', 'E'), ('E', 'A'), ('F', 'D'),
            ('F', 'G'), ('G', 'F'),
        ])

        G = nx_sql.DiGraph(session, name="pagerank_demo")
        G.add_nodes_from(G_nx.nodes())
        G.add_edges_from(G_nx.edges())

        print(f"=== PageRank ===")
        print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        print(f"Edges: {list(G.edges())}")

        # Standard PageRank
        pr = nx.pagerank(G, alpha=0.85)
        print(f"\nPageRank scores (alpha=0.85):")
        for node, score in sorted(pr.items(), key=lambda x: x[1], reverse=True):
            print(f"  {node}: {score:.4f}")

        # Damping factor comparison
        print(f"\nPageRank with different alpha values:")
        for alpha in [0.5, 0.75, 0.85]:
            pr_alpha = nx.pagerank(G, alpha=alpha, max_iter=200)
            top_node = max(pr_alpha, key=pr_alpha.get)
            print(f"  alpha={alpha}: top={top_node} ({pr_alpha[top_node]:.4f})")

        # Personalized PageRank
        personalization = {'A': 1.0, 'F': 1.0}
        pr_personalized = nx.pagerank(G, personalization=personalization)
        print(f"\nPersonalized PageRank (boost A and F):")
        for node, score in sorted(pr_personalized.items(), key=lambda x: x[1], reverse=True):
            boost = " *" if node in personalization else ""
            print(f"  {node}: {score:.4f}{boost}")

        # Compare PageRank with in-degree
        in_degree = dict(G.in_degree())
        print(f"\nPageRank vs In-Degree:")
        for node in sorted(pr.keys(), key=lambda n: pr[n], reverse=True):
            print(f"  {node}: PR={pr[node]:.4f}, in-degree={in_degree.get(node, 0)}")

        session.commit()


if __name__ == "__main__":
    demo_pagerank()
