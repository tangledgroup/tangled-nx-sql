"""Demonstrate k-core decomposition with nx_sql.

Tests extracting the k-core subgraph for different values of k.
The k-core is the maximal subgraph where every node has degree >= k.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def demo_k_core():
    """Compute k-core decomposition on a social network graph."""

    with Session() as session:
        # Use karate club as a social network proxy
        G_nx = nx.karate_club_graph()
        G = nx_sql.Graph(session, name="kcore_demo")
        G.add_nodes_from(G_nx.nodes())
        G.add_edges_from(G_nx.edges())

        print(f"=== K-Core Decomposition ===")
        print(f"Full graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        print(f"Max degree: {max(d for n, d in G.degree())}")

        # Compute k-core decomposition (returns dict node -> k)
        core_number = nx.core_number(G)
        print(f"\nCore numbers: {dict(sorted(core_number.items()))}")

        # Extract k-cores for increasing k
        max_k = max(core_number.values())
        for k in range(max_k + 1):
            kcore = nx.k_core(G, k=k)
            if kcore.number_of_nodes() > 0:
                print(f"\nk-core (k={k}): {kcore.number_of_nodes()} nodes, {kcore.number_of_edges()} edges")
                min_deg = min(d for n, d in kcore.degree()) if kcore.number_of_nodes() > 0 else 0
                print(f"  Min degree in k-core: {min_deg}")

        # Compare with k-shell (nodes exactly at core number k)
        print(f"\n=== K-Shell (exact core number) ===")
        for k in range(max_k + 1):
            kshell = nx.k_shell(G, k=k)
            if kshell.number_of_nodes() > 0:
                print(f"k-shell (k={k}): {sorted(kshell.nodes())} ({kshell.number_of_nodes()} nodes)")

        # K-2 core is the most tightly connected core
        k2 = nx.k_core(G, k=2)
        print(f"\nK-2 core (most interconnected): {sorted(k2.nodes())}")

        session.commit()


if __name__ == "__main__":
    demo_k_core()
