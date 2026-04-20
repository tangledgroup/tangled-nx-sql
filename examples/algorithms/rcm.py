"""Demonstrate Reverse Cuthill-McKee ordering with nx_sql.

Mirrors networkx/examples/algorithms/plot_rcm.py but uses
SQLAlchemy persistence. Tests RCM reordering to reduce bandwidth.
Uses networkx.utils.rcm (not exported at top level in NetworkX 3.x).
"""

import networkx as nx
from networkx.utils import rcm
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def _bandwidth(G, ordering):
    """Compute bandwidth of a graph given an ordering."""
    inv_ordering = {node: i for i, node in enumerate(ordering)}
    max_diff = 0
    for u, v in G.edges():
        diff = abs(inv_ordering[u] - inv_ordering[v])
        max_diff = max(max_diff, diff)
    return max_diff


def demo_rcm():
    """Apply Reverse Cuthill-McKee ordering to reduce matrix bandwidth."""

    with Session() as session:
        # Use a grid graph (good candidate for RCM)
        G_nx = nx.grid_2d_graph(5, 5)
        G = nx_sql.Graph(session, name="rcm_demo")
        for node in G_nx.nodes():
            G.add_node(node)
        G.add_edges_from(G_nx.edges())

        print("=== Reverse Cuthill-McKee Ordering ===")
        print(f"Graph: 5x5 grid ({G.number_of_nodes()} nodes, {G.number_of_edges()} edges)")

        # Standard Cuthill-McKee ordering
        cm_ordering = list(rcm.cuthill_mckee_ordering(G))
        # Reverse Cuthill-McKee ordering
        rcm_ordering = list(rcm.reverse_cuthill_mckee_ordering(G))
        print(f"\nRCM ordering:")
        for i, node in enumerate(rcm_ordering):
            print(f"  {i:2d}: {node}")

        # Natural ordering (sorted by tuple) - not ideal for grid graphs
        natural_ordering = sorted(G.nodes())
        rcm_bandwidth = _bandwidth(G, rcm_ordering)
        cm_bandwidth = _bandwidth(G, cm_ordering)
        natural_bandwidth = _bandwidth(G, natural_ordering)
        print(f"\nBandwidth comparison:")
        print(f"  Natural ordering:  {natural_bandwidth}")
        print(f"  CM ordering:       {cm_bandwidth}")
        print(f"  RCM ordering:      {rcm_bandwidth}")
        if natural_bandwidth > 0:
            improvement = (1 - rcm_bandwidth / natural_bandwidth) * 100
            print(f"  RCM improvement:   {improvement:.0f}%")
        # Note: For grid graphs with tuple nodes, natural ordering is already quite good.
        # RCM shines more on graphs where node labels don't reflect topology.

        # Also try on a Petersen graph
        G_nx2 = nx.petersen_graph()
        G2 = nx_sql.Graph(session, name="rcm_demo2")
        for node in G_nx2.nodes():
            G2.add_node(node)
        G2.add_edges_from(G_nx2.edges())

        print(f"\n=== Petersen Graph ===")
        print(f"Graph: {G2.number_of_nodes()} nodes, {G2.number_of_edges()} edges")

        rcm_ordering2 = list(rcm.reverse_cuthill_mckee_ordering(G2))
        natural_bandwidth2 = _bandwidth(G2, sorted(G2.nodes()))
        rcm_bandwidth2 = _bandwidth(G2, rcm_ordering2)
        print(f"Natural ordering bandwidth:  {natural_bandwidth2}")
        print(f"RCM ordering bandwidth:      {rcm_bandwidth2}")
        if natural_bandwidth2 > 0:
            print(f"Improvement: {(1 - rcm_bandwidth2 / natural_bandwidth2) * 100:.0f}%")

        # Show RCM ordering for Petersen
        print(f"\nRCM ordering (Petersen):")
        for i, node in enumerate(rcm_ordering2):
            print(f"  {i}: {node}")

        session.commit()


if __name__ == "__main__":
    demo_rcm()
