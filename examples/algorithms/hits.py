"""Demonstrate HITS (Hyperlink-Induced Topic Search) with nx_sql.

Tests the HITS algorithm which computes hub and authority scores.
Authorities are pages with many incoming links from good hubs.
Hubs are pages that point to many good authorities.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def demo_hits():
    """Compute HITS hub and authority scores on a web-like graph."""

    with Session() as session:
        # Create a web-like graph
        G_nx = nx.DiGraph()
        G_nx.add_edges_from([
            ('A', 'B'), ('A', 'C'), ('B', 'C'), ('B', 'D'),
            ('C', 'D'), ('D', 'E'), ('E', 'A'), ('F', 'D'),
            ('F', 'G'), ('G', 'F'),
        ])

        G = nx_sql.DiGraph(session, name="hits_demo")
        G.add_nodes_from(G_nx.nodes())
        G.add_edges_from(G_nx.edges())

        print(f"=== HITS (Hub/Authority) ===")
        print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        print(f"Edges: {list(G.edges())}")

        # Compute HITS
        hubs, authorities = nx.hits(G, max_iter=100)
        print(f"\nAuthority scores (top 5):")
        for node, score in sorted(authorities.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {node}: {score:.4f}")

        print(f"\nHub scores (top 5):")
        for node, score in sorted(hubs.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {node}: {score:.4f}")

        # Compare with PageRank
        pr = nx.pagerank(G, alpha=0.85)
        print(f"\nComparison with PageRank:")
        print(f"  {'Node':<6} {'Authority':<12} {'Hub':<12} {'PageRank':<12}")
        print(f"  {'-'*42}")
        for node in sorted(hubs.keys()):
            print(f"  {node:<6} {authorities[node]:<12.4f} {hubs[node]:<12.4f} {pr.get(node, 0):<12.4f}")

        session.commit()


if __name__ == "__main__":
    demo_hits()
