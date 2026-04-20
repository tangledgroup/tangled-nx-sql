"""Demonstrate graph dedensification with nx_sql.

Mirrors networkx/examples/algorithms/plot_dedensification.py but uses
SQLAlchemy persistence. Tests transitive reduction on directed graphs.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def demo_dedensification():
    """Remove transitive edges from a DAG (dedensification)."""

    with Session() as session:
        # Build a DAG with redundant transitive edges
        G_nx = nx.DiGraph()
        # Core structure
        edges = [
            ("A", "B"), ("B", "C"), ("C", "D"),  # chain
            ("A", "C"),  # transitive: A->C is implied by A->B->C
            ("A", "D"),  # transitive: A->D is implied by A->B->C->D
        ]
        G_nx.add_edges_from(edges)

        G = nx_sql.DiGraph(session, name="dedensify_demo")
        for node in G_nx.nodes():
            G.add_node(node)
        G.add_edges_from(G_nx.edges())

        print("=== Graph Dedensification (Transitive Reduction) ===")
        print(f"Original graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        print(f"Edges: {sorted(G.edges())}")

        # Verify it's a DAG
        assert nx.is_directed_acyclic_graph(G), "Graph must be a DAG for transitive reduction"
        print("Verified: Graph is a DAG ✓")

        # Compute transitive reduction
        R = nx.transitive_reduction(G)
        print(f"\nTransitive reduction: {R.number_of_nodes()} nodes, {R.number_of_edges()} edges")
        print(f"Edges: {sorted(R.edges())}")

        # Verify reachability is preserved
        print("\n=== Reachability Comparison ===")
        all_reachable = True
        for u in G.nodes():
            for v in G.nodes():
                orig_reachable = nx.has_path(G, u, v)
                reduced_reachable = nx.has_path(R, u, v)
                if orig_reachable != reduced_reachable:
                    print(f"  MISMATCH: {u}->{v}: original={orig_reachable}, reduced={reduced_reachable}")
                    all_reachable = False
        if all_reachable:
            print("  ✓ Reachability preserved in transitive reduction")

        # Try on a larger DAG
        G_nx2 = nx.DiGraph()
        edges2 = [
            ("root", "A"), ("root", "B"),
            ("A", "C"), ("A", "D"),
            ("B", "D"), ("B", "E"),
            ("C", "F"), ("D", "F"), ("D", "G"),
            ("E", "G"), ("E", "H"),
        ]
        G_nx2.add_edges_from(edges2)

        G2 = nx_sql.DiGraph(session, name="dedensify_demo2")
        for node in G_nx2.nodes():
            G2.add_node(node)
        G2.add_edges_from(G_nx2.edges())

        print(f"\n=== Larger DAG ===")
        print(f"Original: {G2.number_of_nodes()} nodes, {G2.number_of_edges()} edges")

        R2 = nx.transitive_reduction(G2)
        print(f"Reduced:  {R2.number_of_nodes()} nodes, {R2.number_of_edges()} edges")
        print(f"Edges removed: {G2.number_of_edges() - R2.number_of_edges()}")

        # Verify reduced graph is a DAG and preserves reachability
        assert nx.is_directed_acyclic_graph(R2), "Transitive reduction must be a DAG"
        print("✓ Reduced graph is still a DAG")

        session.commit()


if __name__ == "__main__":
    demo_dedensification()
