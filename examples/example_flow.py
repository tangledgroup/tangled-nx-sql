"""example_flow.py - Network flow algorithms with nx_sql.

Covers: maximum_flow, minimum_cut, min_cost_flow, gomory_hu_tree,
        capacity_scaling, edge_disjoint_paths, node_disjoint_paths.

Note: Max flow modifies the graph in-place (adds residual edges), so we
use plain NetworkX for computation and demonstrate with nx_sql graphs.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)


def demo_maximum_flow():
    """Maximum flow using Edmonds-Karp algorithm."""
    # Build flow network as nx_sql graph, then copy for computation
    with SessionLocal() as session:
        G_nxsql = nx_sql.DiGraph(session, name="flow_network")
        edges = [
            ("s", "A", 10), ("s", "B", 8),
            ("A", "C", 5), ("A", "D", 7),
            ("B", "D", 6), ("B", "E", 4),
            ("C", "t", 6), ("D", "t", 9),
            ("E", "t", 3),
        ]
        G_nxsql.add_edges_from((u, v, {"capacity": c}) for u, v, c in edges)
        print(f"Flow network: {G_nxsql.number_of_nodes()} nodes, "
              f"{G_nxsql.number_of_edges()} edges")

    # Compute max flow on plain NetworkX copy (modifies in-place)
    G = nx.DiGraph()
    G.add_edges_from((u, v, {"capacity": c}) for u, v, c in edges)
    flow_value, flow_dict = nx.maximum_flow(G, "s", "t", capacity="capacity")
    print(f"\nMaximum flow: {flow_value}")
    print("Flow distribution:")
    for u in sorted(flow_dict):
        for v in sorted(flow_dict[u]):
            if flow_dict[u][v] > 0:
                cap = G[u][v]["capacity"]
                print(f"  {u} → {v}: {flow_dict[u][v]}/{cap}")

    cut_value, partition = nx.minimum_cut(G, "s", "t", capacity="capacity")
    print(f"\nMinimum cut value: {cut_value}")
    print(f"Partition: S={partition[0]}, T={partition[1]}")


def demo_alternative_algorithms():
    """Try different max flow algorithms."""
    # Build plain NetworkX flow network
    edges = [
        ("s", "A", 10), ("s", "B", 8),
        ("A", "t", 5), ("B", "t", 8),
    ]
    G = nx.DiGraph()
    G.add_edges_from((u, v, {"capacity": c}) for u, v, c in edges)

    # Boykov-Kolmogorov
    try:
        flow_val, (partition, _) = nx.maximum_flow(
            G, "s", "t", capacity="capacity",
            flow_func=nx.algorithms.flow.preflow_push,
        )
        # Boykov-Kolmogorov returns (flow_value, (partition, residual))
        print(f"Boykov-Kolmogorov: flow={flow_val}")
    except Exception as e:
        print(f"Boykov-Kolmogorov: {e}")

    # Dinitz
    G2 = nx.DiGraph()
    G2.add_edges_from((u, v, {"capacity": c}) for u, v, c in edges)
    try:
        flow_val = nx.maximum_flow(
            G2, "s", "t", capacity="capacity",
            flow_func=nx.algorithms.flow.dinitz,
        )[0]
        print(f"Dinitz: flow={flow_val}")
    except Exception as e:
        print(f"Dinitz: {e}")

    # Greedy FF
    G3 = nx.DiGraph()
    G3.add_edges_from((u, v, {"capacity": c}) for u, v, c in edges)
    try:
        flow_val = nx.maximum_flow(
            G3, "s", "t", capacity="capacity",
            flow_func=nx.algorithms.flow.edmonds_karp,
        )[0]
        print(f"Edmonds-Karp: flow={flow_val}")
    except Exception as e:
        print(f"Greedy FF: {e}")


def demo_min_cost_flow():
    """Minimum cost flow optimization."""
    # Build plain NetworkX min-cost flow network
    edges = [
        ("s", "A", {"capacity": 2, "weight": 1}),
        ("s", "B", {"capacity": 2, "weight": 4}),
        ("A", "t", {"capacity": 2, "weight": 4}),
        ("B", "t", {"capacity": 2, "weight": 1}),
        ("A", "B", {"capacity": 2, "weight": 2}),
    ]
    G = nx.DiGraph()
    G.add_edges_from(edges)
    result = nx.min_cost_flow(G, capacity="capacity", weight="weight")
    if isinstance(result, tuple):
        flow_cost, flow_dict = result[0], result[1]
    else:
        flow_cost = 0
        flow_dict = result
    print(f"\nMin-cost flow cost: {flow_cost}")
    print("Flow distribution:")
    for u in sorted(flow_dict):
        for v in sorted(flow_dict[u]):
            if flow_dict[u][v] > 0:
                cap = G[u][v]["capacity"]
                cost = G[u][v]["weight"]
                print(f"  {u} → {v}: {flow_dict[u][v]}/{cap} (cost={cost})")


def demo_capacity_scaling():
    """Min-cost flow with capacity scaling algorithm."""
    # Build plain NetworkX capacity scaling network
    edges = [
        ("s", "A", {"capacity": 5, "weight": 2}),
        ("s", "B", {"capacity": 3, "weight": 5}),
        ("A", "t", {"capacity": 3, "weight": 3}),
        ("B", "t", {"capacity": 5, "weight": 1}),
    ]
    G = nx.DiGraph()
    G.add_edges_from(edges)
    result = nx.capacity_scaling(G, capacity="capacity", weight="weight")
    if isinstance(result, tuple):
        flow_cost, flow_dict = result[0], result[1]
    else:
        flow_cost = 0
        flow_dict = result
    print(f"\nCapacity scaling cost: {flow_cost}")
    for u in sorted(flow_dict):
        for v in sorted(flow_dict[u]):
            if flow_dict[u][v] > 0:
                cap = G[u][v]["capacity"]
                cost = G[u][v]["weight"]
                print(f"  {u} → {v}: {flow_dict[u][v]}/{cap} (cost={cost})")


def demo_gomory_hu():
    """Gomory-Hu tree for all-pairs min-cut."""
    # Build plain NetworkX Gomory-Hu network
    edges = [
        (0, 1, 3), (0, 2, 3), (1, 2, 3),
        (1, 3, 3), (2, 4, 3), (3, 4, 3),
    ]
    G = nx.Graph()
    G.add_edges_from((u, v, {"capacity": c}) for u, v, c in edges)
    gh_tree = nx.gomory_hu_tree(G)
    print(f"\nGomory-Hu tree: {gh_tree.number_of_nodes()} nodes, "
          f"{gh_tree.number_of_edges()} edges")
    for u, v, d in sorted(gh_tree.edges(data=True)):
        cap = d.get('capacity', 0)
        print(f"  Cut between {u} and {v}: capacity={cap}")


def demo_disjoint_paths():
    """Edge and node disjoint paths."""
    # Build plain NetworkX disjoint paths network
    edges = [
        ("s", "A"), ("s", "B"),
        ("A", "t"), ("B", "t"),
        ("A", "B"),  # extra cross edge
    ]
    G = nx.Graph()
    G.add_edges_from(edges)

    with SessionLocal() as session:
        edge_paths = list(nx.edge_disjoint_paths(G, "s", "t"))
        print(f"\nEdge-disjoint paths from s to t ({len(edge_paths)}):")
        for i, path in enumerate(edge_paths):
            print(f"  Path {i+1}: {' → '.join(path)}")

        node_paths = list(nx.node_disjoint_paths(G, "s", "t"))
        print(f"\nNode-disjoint paths from s to t ({len(node_paths)}):")
        for i, path in enumerate(node_paths):
            print(f"  Path {i+1}: {' → '.join(path)}")

        session.commit()

    session.commit()


if __name__ == "__main__":
    demo_maximum_flow()
    demo_alternative_algorithms()
    demo_min_cost_flow()
    demo_capacity_scaling()
    demo_gomory_hu()
    demo_disjoint_paths()
