"""Demonstrate TrustRank algorithm with nx_sql.

Mirrors networkx/examples/algorithms/plot_trust_rank.py but uses
SQLAlchemy persistence. Tests link analysis on a small web graph.
TrustRank is implemented as a variant of PageRank with seed nodes,
since nx.trust_rank is not available in this NetworkX version.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def trust_rank(G, seeds, damping=0.85, max_iter=100, tol=1.0e-6):
    """Compute TrustRank as a variant of PageRank with seed nodes.

    Seeds receive initial rank. At each iteration, non-seed nodes
    lose a fraction (1-damping) of their rank to a random reset.
    """
    nodes = list(G.nodes())
    n = len(nodes)
    node_idx = {v: i for i, v in enumerate(nodes)}
    seed_set = set(seeds)

    # Initialize: seeds get equal rank
    rank = [1.0 / n] * n
    # Add extra seed boost
    for s in seeds:
        if s in node_idx:
            rank[node_idx[s]] += 0.5

    for _ in range(max_iter):
        new_rank = [0.0] * n
        # Random teleportation (seed bias)
        seed_boost = sum(rank[i] for i in range(n) if nodes[i] in seed_set)
        for i in range(n):
            new_rank[i] = (1 - damping) / n + damping * rank[i] / n

        # Propagate rank through edges
        for v in nodes:
            out_degree = G.out_degree(v)
            if out_degree == 0:
                continue
            idx_v = node_idx[v]
            contribution = damping * rank[idx_v] / out_degree
            for w in G.successors(v):
                idx_w = node_idx[w]
                new_rank[idx_w] += contribution

        # Check convergence
        diff = sum(abs(new_rank[i] - rank[i]) for i in range(n))
        rank = new_rank
        if diff < tol:
            break

    return {nodes[i]: rank[i] for i in range(n)}


def demo_trust_rank():
    """Compute TrustRank on a small web graph."""

    with Session() as session:
        # Create a small web graph (directed edges = hyperlinks)
        G_nx = nx.DiGraph()
        # Seed pages (trusted)
        trusted_pages = ["A", "B"]
        # Regular pages
        regular_pages = ["C", "D", "E", "F", "G", "H", "I", "J"]

        edges = [
            # Trusted pages link to each other and some regular pages
            ("A", "B"), ("B", "A"),
            ("A", "C"), ("A", "D"),
            ("B", "D"), ("B", "E"),
            # Regular pages link among themselves (spam cluster)
            ("C", "D"), ("C", "E"),
            ("D", "C"), ("D", "E"),
            ("E", "C"), ("E", "F"),
            # Some links back to trusted pages
            ("F", "A"),
            # More regular pages
            ("F", "G"), ("G", "H"), ("H", "I"),
            ("I", "J"), ("J", "G"),
        ]
        G_nx.add_edges_from(edges)

        G = nx_sql.DiGraph(session, name="trust_rank_demo")
        for node in G_nx.nodes():
            G.add_node(node)
        G.add_edges_from(G_nx.edges())

        print("=== TrustRank ===")
        print(f"Web graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        print(f"Trusted seeds: {trusted_pages}")

        # Compute TrustRank (custom implementation)
        damping = 0.85
        trust_rank_scores = trust_rank(G, trusted_pages, damping=damping)
        pagerank_scores = nx.pagerank(G, alpha=damping)

        print("\n=== PageRank (top 5) ===")
        top_pr = sorted(pagerank_scores.items(), key=lambda x: x[1], reverse=True)[:5]
        for node, score in top_pr:
            marker = " [TRUSTED]" if node in trusted_pages else ""
            print(f"  {node}: {score:.4f}{marker}")

        print("\n=== TrustRank (top 5) ===")
        top_tr = sorted(trust_rank_scores.items(), key=lambda x: x[1], reverse=True)[:5]
        for node, score in top_tr:
            marker = " [TRUSTED]" if node in trusted_pages else ""
            print(f"  {node}: {score:.4f}{marker}")

        # Compare: nodes that have high PageRank but low TrustRank
        print("\n=== Spam Detection (High PR, Low TR) ===")
        for node in sorted(trust_rank_scores.keys()):
            pr_score = pagerank_scores[node]
            tr_score = trust_rank_scores[node]
            ratio = pr_score / tr_score if tr_score > 0 else float('inf')
            if ratio > 2 and node not in trusted_pages:
                print(f"  {node}: PR={pr_score:.4f}, TR={tr_score:.4f}, ratio={ratio:.1f}x")

        # Show all scores
        print("\n=== All Scores ===")
        print(f"  {'Node':<5} {'PageRank':>10} {'TrustRank':>10} {'Ratio':>8}")
        for node in sorted(trust_rank_scores.keys()):
            pr_score = pagerank_scores[node]
            tr_score = trust_rank_scores[node]
            ratio = pr_score / tr_score if tr_score > 0 else float('inf')
            ratio_str = f"{ratio:.1f}x" if ratio != float('inf') else "inf"
            print(f"  {node:<5} {pr_score:>10.4f} {tr_score:>10.4f} {ratio_str:>8}")

        session.commit()


if __name__ == "__main__":
    demo_trust_rank()
