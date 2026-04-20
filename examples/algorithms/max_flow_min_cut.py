"""Demonstrate maximum flow / minimum cut with nx_sql.

Tests computing max flow from source to sink and identifying the min-cut.
Uses the push-relabel algorithm for efficient computation.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def demo_max_flow():
    """Compute maximum flow and minimum cut on a flow network."""

    with Session() as session:
        # Create a flow network (directed graph with capacities)
        G_nx = nx.DiGraph()
        G_nx.add_edge('s', 'a', capacity=3)
        G_nx.add_edge('s', 'b', capacity=1)
        G_nx.add_edge('a', 'c', capacity=3)
        G_nx.add_edge('b', 'c', capacity=5)
        G_nx.add_edge('b', 'd', capacity=4)
        G_nx.add_edge('c', 'd', capacity=2)
        G_nx.add_edge('c', 't', capacity=2)
        G_nx.add_edge('d', 't', capacity=3)

        G = nx_sql.DiGraph(session, name="max_flow_demo")
        G.add_nodes_from(G_nx.nodes())
        for u, v, data in G_nx.edges(data=True):
            G.add_edge(u, v, **data)

        source, sink = 's', 't'
        print(f"=== Maximum Flow / Minimum Cut ===")
        print(f"Flow network: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        print(f"Source: {source}, Sink: {sink}")

        # Compute maximum flow
        flow_value, flow_dict = nx.maximum_flow(G, source, sink, capacity='capacity')
        print(f"\nMaximum flow value: {flow_value}")
        print(f"\nFlow dictionary:")
        for u in sorted(flow_dict):
            for v in sorted(flow_dict[u]):
                if flow_dict[u][v] > 0:
                    print(f"  {u} -> {v}: {flow_dict[u][v]}")

        # Compute minimum cut
        cut_value, partition = nx.minimum_cut(G, source, sink, capacity='capacity')
        S, T = partition
        print(f"\nMinimum cut value: {cut_value}")
        print(f"Source side (S): {sorted(S)}")
        print(f"Sink side (T): {sorted(T)}")

        # Verify max-flow min-cut theorem
        assert flow_value == cut_value, "Max flow must equal min cut capacity"
        print("✓ Verified: max-flow min-cut theorem holds")

        # Show bottleneck: edges crossing the min-cut
        print(f"\nBottleneck edges (crossing S→T cut):")
        for u, v, data in G.edges(data=True):
            if u in S and v in T:
                cap = data.get('capacity', 1)
                flow = flow_dict.get(u, {}).get(v, 0)
                print(f"  {u} -> {v}: capacity={cap}, flow={flow}")

        session.commit()


if __name__ == "__main__":
    demo_max_flow()
