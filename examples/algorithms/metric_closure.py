"""Demonstrate metric closure with nx_sql.

Mirrors networkx/examples/algorithms/plot_metric_closure.py but uses
SQLAlchemy persistence. Tests computing the metric closure of a graph.
MetricClosure is implemented manually since it's not in NetworkX 3.x.
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


def metric_closure(G, weight="weight"):
    """Compute the metric closure of a weighted graph.

    The metric closure is a complete graph where the edge weights
    represent the shortest path distance in the original graph.
    """
    MC = nx.Graph()
    for node in G.nodes():
        MC.add_node(node)

    # Compute all-pairs shortest path lengths (weighted)
    # Use nx.shortest_path_length with weight for correct weighted distances
    for u in G.nodes():
        for v in G.nodes():
            if u != v:
                try:
                    dist = nx.shortest_path_length(G, u, v, weight=weight)
                    if not MC.has_edge(u, v):
                        MC.add_edge(u, v, weight=dist)
                except nx.NetworkXNoPath:
                    pass  # No path between u and v

    return MC


@print_docstring
def demo_metric_closure():
    """Compute the metric closure of a weighted graph."""

    with Session() as session:
        # Create a weighted graph
        G_nx = nx.Graph()
        edges = [
            ("A", "B", 1),
            ("B", "C", 2),
            ("C", "D", 3),
            ("A", "D", 10),  # long direct edge
            ("B", "D", 4),
        ]
        G_nx.add_weighted_edges_from(edges)

        G = nx_sql.Graph(session, name="metric_closure_demo")
        for node in G_nx.nodes():
            G.add_node(node)
        for u, v, d in G_nx.edges(data=True):
            G.add_edge(u, v, weight=d["weight"])

        print("=== Metric Closure ===")
        print(f"Original graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        print(f"Edges with weights:")
        for u, v, d in sorted(G.edges(data=True)):
            print(f"  {u} -- {v}: weight={d['weight']}")

        # Compute metric closure
        MC = metric_closure(G, weight="weight")
        print(f"\nMetric closure: {MC.number_of_nodes()} nodes, {MC.number_of_edges()} edges")
        print("Closure edges (all-pairs shortest path distances):")
        for u, v, d in sorted(MC.edges(data=True)):
            print(f"  {u} -- {v}: distance={d['weight']}")

        # Compare original edge weights vs closure shortest path distances
        print("\n=== Distance Comparison ===")
        print(f"  {'Pair':<15} {'Edge Weight':>12} {'Closure Dist':>13} {'Match':>6}")
        for u, v, d in sorted(G.edges(data=True)):
            edge_w = d.get("weight", 1)
            closure_dist = MC[u][v]["weight"]
            match = "OK" if edge_w == closure_dist else f"SP={closure_dist}"
            print(f"  {u}-{v:<13} {edge_w:>12} {closure_dist:>13} {match}")

        # Try on a larger graph
        G_nx2 = nx.erdos_renyi_graph(8, 0.4, seed=42)
        for u, v in G_nx2.edges():
            G_nx2[u][v]["weight"] = abs(hash((u, v))) % 10 + 1

        G2 = nx_sql.Graph(session, name="metric_closure_demo2")
        for node in G_nx2.nodes():
            G2.add_node(node)
        for u, v, d in G_nx2.edges(data=True):
            G2.add_edge(u, v, weight=d["weight"])

        print(f"\n=== Larger Graph ===")
        print(f"Original: {G2.number_of_nodes()} nodes, {G2.number_of_edges()} edges")

        MC2 = metric_closure(G2, weight="weight")
        expected_edges = G2.number_of_nodes() * (G2.number_of_nodes() - 1) // 2
        print(f"Closure:  {MC2.number_of_nodes()} nodes, {MC2.number_of_edges()} edges")
        print(f"Edges added: {MC2.number_of_edges() - G2.number_of_edges()} "
              f"(new edges to make complete; total should be {expected_edges})")

        session.commit()


if __name__ == "__main__":
    demo_metric_closure()
