"""Demonstrate dominating set with nx_sql.

Tests finding a dominating set — a subset of nodes such that every node
not in the set is adjacent to at least one member of the set.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def demo_dominating_set():
    """Find a dominating set in a graph."""

    with Session() as session:
        G_nx = nx.karate_club_graph()
        G = nx_sql.Graph(session, name="dominating_set_demo")
        G.add_nodes_from(G_nx.nodes())
        G.add_edges_from(G_nx.edges())

        print(f"=== Dominating Set ===")
        print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

        # Find a dominating set (greedy approximation)
        ds = nx.algorithms.dominating_set(G)
        print(f"\nDominating set ({len(ds)} nodes): {sorted(ds)}")

        # Verify it's a valid dominating set
        all_nodes = set(G.nodes())
        dominated = set(ds)
        for node in ds:
            dominated.update(G.neighbors(node))

        print(f"Dominated nodes: {len(dominated)}/{G.number_of_nodes()}")
        assert dominated == all_nodes, "Every node must be in or adjacent to the dominating set"
        print("✓ Verified: valid dominating set")

        # Check if it's a connected dominating set
        is_connected_dominating = nx.algorithms.dominating.is_connected_dominating_set(G, ds)
        print(f"Is connected dominating set: {is_connected_dominating}")

        # Check minimality
        is_dominating = nx.algorithms.dominating.is_dominating_set(G, ds)
        print(f"Is dominating set: {is_dominating}")

        # Try with a smaller graph for clarity
        print(f"\n=== Small Graph Example ===")
        G_small_nx = nx.path_graph(5)  # 0-1-2-3-4
        G_small = nx_sql.Graph(session, name="dominating_set_small")
        G_small.add_nodes_from(G_small_nx.nodes())
        G_small.add_edges_from(G_small_nx.edges())

        ds_small = nx.algorithms.dominating_set(G_small)
        print(f"Path P5 dominating set: {sorted(ds_small)}")
        # For a path of 5 nodes, node 1 or 2 is enough to dominate everything
        print(f"Size: {len(ds_small)} (optimal for P5 is ceil(5/3) = 2)")

        session.commit()


if __name__ == "__main__":
    demo_dominating_set()
