"""Demonstrate block model (quotient graph) with nx_sql.

Mirrors networkx/examples/algorithms/plot_blockmodel.py but uses
SQLAlchemy persistence. Tests creating quotient graphs from partitions.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def demo_blockmodel():
    """Create a quotient graph (block model) from node partitions."""

    with Session() as session:
        # Use karate club graph
        G_nx = nx.karate_club_graph()
        G = nx_sql.Graph(session, name="blockmodel_demo")
        for node in G_nx.nodes():
            G.add_node(node)
        G.add_edges_from(G_nx.edges())

        print("=== Block Model (Quotient Graph) ===")
        print(f"Original graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

        # Define partitions (communities)
        # Club Mr. Hi (nodes 0-16) and Prof. Forge (nodes 17-33)
        partition = [
            set(range(0, 17)),   # Club Mr. Hi
            set(range(17, 34)),  # Prof. Forge
        ]

        print(f"\nPartitions: {len(partition)} blocks")
        for i, block in enumerate(partition):
            print(f"  Block {i}: {sorted(block)} ({len(block)} nodes)")

        # Create quotient graph
        H = nx.quotient_graph(G, partition)
        print(f"\nQuotient graph: {H.number_of_nodes()} nodes, {H.number_of_edges()} edges")

        # Show edge weights (number of edges between blocks)
        print("\nInter-block edges:")
        for u, v, d in H.edges(data=True):
            print(f"  Block {u} <-> Block {v}: {d['weight']} edges")

        # More granular partitioning using actual community structure
        communities = [
            {0, 1, 3, 7, 11, 12, 13, 17, 19, 21},
            {4, 5, 6, 10, 16},
            {8, 14, 15, 18, 20, 22, 23, 26, 29, 30, 32, 33},
            {2, 24, 25, 27, 28, 31},
        ]

        H2 = nx.quotient_graph(G, communities)
        print(f"\n=== Finer Partition (4 communities) ===")
        print(f"Quotient graph: {H2.number_of_nodes()} nodes, {H2.number_of_edges()} edges")

        print("\nInter-community edges:")
        for u, v, d in sorted(H2.edges(data=True)):
            print(f"  Block {u} <-> Block {v}: {d['weight']} edges")

        session.commit()


if __name__ == "__main__":
    demo_blockmodel()
