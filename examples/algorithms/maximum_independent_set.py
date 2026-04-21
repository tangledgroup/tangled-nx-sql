"""Demonstrate maximum independent set with nx_sql.

Mirrors networkx/examples/algorithms/plot_maximum_independent_set.py but uses
SQLAlchemy persistence. Tests finding maximum independent sets on graphs.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base
import sys; sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent.parent.parent))
from examples.utils import print_docstring

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


@print_docstring
def demo_maximum_independent_set():
    """Find maximum independent sets on various graphs."""

    with Session() as session:
        # Use a path graph for a simple example
        G_nx = nx.path_graph(10)
        G = nx_sql.Graph(session, name="max_independent_set_demo")
        for node in G_nx.nodes():
            G.add_node(node)
        G.add_edges_from(G_nx.edges())

        print("=== Maximum Independent Set ===")
        print(f"Graph: path graph P_10 ({G.number_of_nodes()} nodes, {G.number_of_edges()} edges)")

        # Find maximum independent set
        mis = nx.algorithms.approximation.maximum_independent_set(G)
        print(f"\nMaximum independent set: {sorted(mis)}")
        print(f"Size: {len(mis)}")

        # Verify it's independent (no two nodes share an edge)
        is_independent = True
        for u, v in G.edges():
            if u in mis and v in mis:
                print(f"  ERROR: Edge ({u}, {v}) connects two set members!")
                is_independent = False
        if is_independent:
            print("✓ Verified: No two nodes in the set share an edge")

        # For P_10, expected MIS size is ceil(10/2) = 5
        print(f"Expected size for P_10: 5 (ceil(n/2))")

    with Session() as session:
        # Try on a cycle graph
        G_nx = nx.cycle_graph(11)
        G = nx_sql.Graph(session, name="max_independent_set_demo2")
        for node in G_nx.nodes():
            G.add_node(node)
        G.add_edges_from(G_nx.edges())

        print(f"\n=== Cycle Graph C_11 ===")
        print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

        mis = nx.algorithms.approximation.maximum_independent_set(G)
        print(f"Maximum independent set: {sorted(mis)}")
        print(f"Size: {len(mis)}")

        # Verify independence
        is_independent = True
        for u, v in G.edges():
            if u in mis and v in mis:
                is_independent = False
        print(f"✓ Independent set valid: {is_independent}")

    with Session() as session:
        # Try on a random graph
        G_nx = nx.gnp_random_graph(20, 0.3, seed=42)
        G = nx_sql.Graph(session, name="max_independent_set_demo3")
        for node in G_nx.nodes():
            G.add_node(node)
        G.add_edges_from(G_nx.edges())

        print(f"\n=== Random Graph G(20, 0.3) ===")
        print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

        mis = nx.algorithms.approximation.maximum_independent_set(G)
        print(f"Maximum independent set size: {len(mis)}")
        print(f"Fraction of nodes: {len(mis) / G.number_of_nodes():.0%}")

        # Note: approximation.maximum_independent_set returns an approximate (not exact)
        # maximum independent set. The exact MIS on the complement equals the max clique,
        # but the approximation may differ.
        print(f"\n=== Comparison: MIS vs Max Clique on Complement ===")
        G_complement = nx.complement(G)
        max_clique = max(nx.algorithms.clique.find_cliques(G_complement), key=len)
        print(f"MIS size (approximation): {len(mis)}")
        print(f"Max clique in complement (exact): {len(max_clique)}")
        print(f"Note: MIS is an approximation; exact MIS would equal max clique size")

        session.commit()


if __name__ == "__main__":
    demo_maximum_independent_set()
