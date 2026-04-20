"""Demonstrate parallel betweenness computation with nx_sql.

Mirrors networkx/examples/algorithms/plot_parallel_betweenness.py but uses
SQLAlchemy persistence. Tests computing betweenness centrality on a large graph.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def demo_parallel_betweenness():
    """Compute betweenness centrality with sampling on a larger graph."""

    with Session() as session:
        # Create a larger random graph
        G_nx = nx.gnp_random_graph(50, 0.1, seed=42)
        G = nx_sql.Graph(session, name="parallel_betweenness_demo")
        for node in G_nx.nodes():
            G.add_node(node)
        G.add_edges_from(G_nx.edges())

        print("=== Parallel Betweenness Centrality ===")
        print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

        # Full betweenness (may be slow for large graphs)
        print("\n=== Full Betweenness Centrality ===")
        bc_full = nx.betweenness_centrality(G, normalized=True)
        top5_full = sorted(bc_full.items(), key=lambda x: x[1], reverse=True)[:5]
        print("Top 5 nodes by betweenness:")
        for node, score in top5_full:
            print(f"  Node {node}: {score:.4f}")

        # Sampled betweenness (k=10 samples)
        print("\n=== Sampled Betweenness Centrality (k=10) ===")
        bc_sampled = nx.betweenness_centrality(G, normalized=True, k=10, seed=42)
        top5_sampled = sorted(bc_sampled.items(), key=lambda x: x[1], reverse=True)[:5]
        print("Top 5 nodes by sampled betweenness:")
        for node, score in top5_sampled:
            print(f"  Node {node}: {score:.4f}")

        # Compare top nodes
        print("\n=== Comparison ===")
        full_top_nodes = set(n for n, _ in top5_full)
        sampled_top_nodes = set(n for n, _ in top5_sampled)
        overlap = full_top_nodes & sampled_top_nodes
        print(f"Full top-5:  {sorted(full_top_nodes)}")
        print(f"Sampled top-5: {sorted(sampled_top_nodes)}")
        print(f"Overlap: {len(overlap)}/{len(full_top_nodes)} nodes match")

        # Degree betweenness (only consider nodes with degree > 0)
        print("\n=== Betweenness by Degree ===")
        high_degree = [n for n in G.nodes() if G.degree(n) >= 5]
        low_degree = [n for n in G.nodes() if G.degree(n) < 5]

        avg_bc_high = sum(bc_full[n] for n in high_degree) / len(high_degree) if high_degree else 0
        avg_bc_low = sum(bc_full[n] for n in low_degree) / len(low_degree) if low_degree else 0
        print(f"High-degree nodes (≥5): avg betweenness = {avg_bc_high:.4f} ({len(high_degree)} nodes)")
        print(f"Low-degree nodes (<5):  avg betweenness = {avg_bc_low:.4f} ({len(low_degree)} nodes)")

        session.commit()


if __name__ == "__main__":
    demo_parallel_betweenness()
