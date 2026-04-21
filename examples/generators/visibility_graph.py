"""Demonstrate visibility graph from time series with nx_sql.

Mirrors networkx/examples/graph/plot_visibility_graph.py but uses
SQLAlchemy persistence. Tests constructing a visibility graph where nodes
are connected if they have line-of-sight in the time series plot.
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


def visibility_graph(time_series):
    """Build a visibility graph from a 1D time series.

    Two points i and j have visibility if all intermediate points k
    satisfy: y[k] < y[i] + (y[j] - y[i]) * (k - i) / (j - i)
    """
    n = len(time_series)
    G = nx.Graph()

    for i in range(n):
        G.add_node(i, value=time_series[i], index=i)

    for i in range(n):
        for j in range(i + 1, n):
            # Check visibility between i and j
            visible = True
            xi, yi = i, time_series[i]
            xj, yj = j, time_series[j]

            for k in range(i + 1, j):
                xk = k
                yk = time_series[k]
                # Line equation: height at k on line from i to j
                line_height = yi + (yj - yi) * (xk - xi) / (xj - xi)
                if yk >= line_height:
                    visible = False
                    break

            if visible:
                G.add_edge(i, j, value_i=yi, value_yj=yj)

    return G


@print_docstring
def demo_visibility_graph():
    """Construct a visibility graph from a time series."""

    with Session() as session:
        # Simple example
        time_series = [0, 2, 1, 3, 2, 1, 3, 2, 1, 3, 2, 1, 3, 4, 0]

        G_nx = visibility_graph(time_series)
        G = nx_sql.Graph(session, name="visibility_demo")
        for node, data in G_nx.nodes(data=True):
            G.add_node(node, value=data["value"], index=data["index"])
        for u, v, d in G_nx.edges(data=True):
            G.add_edge(u, v, value_i=d["value_i"], value_yj=d["value_yj"])

        print("=== Visibility Graph ===")
        print(f"Time series: {time_series}")
        print(f"Nodes: {G.number_of_nodes()}")
        print(f"Edges: {G.number_of_edges()}")

        # Show node values
        print("\nNode values:")
        for node in sorted(G.nodes()):
            val = G.nodes[node]["value"]
            bar = "#" * val
            print(f"  [{node}] value={val} {bar}")

        # Show edges
        print("\nVisibility edges (i, j, height_i, height_j):")
        for u, v, d in sorted(G.edges(data=True)):
            print(f"  {u}(v={d['value_i']}) <-> {v}(v={d['value_yj']})")

        # Analyze degree distribution
        print("\n=== Degree Analysis ===")
        degrees = [d for _, d in G.degree()]
        from collections import Counter
        degree_counts = Counter(degrees)
        for deg in sorted(degree_counts.keys()):
            bar = "#" * degree_counts[deg]
            print(f"  Degree {deg}: {degree_counts[deg]} nodes {bar}")

        # Node with most connections
        max_deg_node = max(G.nodes(), key=lambda n: G.degree(n))
        max_deg = G.degree(max_deg_node)
        print(f"\nMost connected node: {max_deg_node} (degree={max_deg})")
        neighbors = sorted(G.neighbors(max_deg_node))
        print(f"  Neighbors: {neighbors}")

        # Try a random-looking series
        print("\n=== Random-Looking Series ===")
        time_series2 = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5, 8]
        G2_nx = visibility_graph(time_series2)
        G2 = nx_sql.Graph(session, name="visibility_demo2")
        for node, data in G2_nx.nodes(data=True):
            G2.add_node(node, value=data["value"], index=data["index"])
        for u, v, d in G2_nx.edges(data=True):
            G2.add_edge(u, v, value_i=d["value_i"], value_yj=d["value_yj"])

        print(f"Time series: {time_series2}")
        print(f"Nodes: {G2.number_of_nodes()}, Edges: {G2.number_of_edges()}")

        # Average degree
        avg_deg = 2 * G2.number_of_edges() / G2.number_of_nodes() if G2.number_of_nodes() > 0 else 0
        print(f"Average degree: {avg_deg:.2f}")

        session.commit()


if __name__ == "__main__":
    demo_visibility_graph()
