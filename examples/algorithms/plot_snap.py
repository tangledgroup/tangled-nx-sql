"""Demonstrate SNAP graph summarization with nx_sql.

Mirrors networkx/examples/algorithms/plot_snap.py but uses
SQLAlchemy persistence. Tests grouping nodes by attributes and edge types
to produce a summary graph via snap_aggregation.
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
def demo_snap():
    """Summarize a graph using SNAP (Summarization by Grouping Nodes on
    Attributes and Pairwise edges)."""

    with Session() as session:
        # Build a graph with node and edge attributes
        nodes_data = {
            "A": {"color": "Red"},
            "B": {"color": "Red"},
            "C": {"color": "Red"},
            "D": {"color": "Red"},
            "E": {"color": "Blue"},
            "F": {"color": "Blue"},
            "G": {"color": "Blue"},
            "H": {"color": "Blue"},
            "I": {"color": "Yellow"},
            "J": {"color": "Yellow"},
            "K": {"color": "Yellow"},
            "L": {"color": "Yellow"},
        }

        edges_data = [
            ("A", "B", "Strong"),
            ("A", "C", "Weak"),
            ("A", "E", "Strong"),
            ("A", "I", "Weak"),
            ("B", "D", "Weak"),
            ("B", "J", "Weak"),
            ("B", "F", "Strong"),
            ("C", "G", "Weak"),
            ("D", "H", "Weak"),
            ("I", "J", "Strong"),
            ("J", "K", "Strong"),
            ("I", "L", "Strong"),
        ]

        G_nx = nx.Graph()
        for node, attrs in nodes_data.items():
            G_nx.add_node(node, **attrs)
        for u, v, label in edges_data:
            G_nx.add_edge(u, v, type=label)

        G = nx_sql.Graph(session, name="snap_demo")
        for node, attrs in nodes_data.items():
            G.add_node(node, **attrs)
        for u, v, label in edges_data:
            G.add_edge(u, v, type=label)

        print("=== Original Graph ===")
        print(f"Nodes: {G.number_of_nodes()}")
        print(f"Edges: {G.number_of_edges()}")
        print("\nNode attributes:")
        for node in sorted(G.nodes()):
            attrs = dict(G.nodes[node])
            print(f"  {node}: {attrs}")
        print("\nEdge types:")
        edge_types = {}
        for u, v, d in G.edges(data=True):
            t = d.get("type", "unknown")
            edge_types.setdefault(t, []).append((u, v))
        for t, edges in sorted(edge_types.items()):
            print(f"  {t}: {len(edges)} edges ({edges})")

        # Compute SNAP aggregation
        node_attributes = ("color",)
        edge_attributes = ("type",)
        summary_graph = nx.snap_aggregation(
            G, node_attributes, edge_attributes, prefix="S-"
        )

        print(f"\n=== SNAP Aggregation ===")
        print(f"Summary graph: {summary_graph.number_of_nodes()} nodes, {summary_graph.number_of_edges()} edges")
        print("\nSummary nodes:")
        for node in sorted(summary_graph.nodes()):
            attrs = dict(summary_graph.nodes[node])
            print(f"  {node}: {attrs}")
        print("\nSummary edges:")
        for u, v, d in sorted(summary_graph.edges(data=True)):
            types_info = d.get("types", [])
            type_labels = [t.get("type", "?") for t in types_info]
            count = d.get("count", 0)
            print(f"  {u} -- {v}: types={type_labels}, count={count}")

        # Compute statistics
        print(f"\n=== Summary Statistics ===")
        print(f"Original -> Summary compression ratio: "
              f"{G.number_of_nodes()}/{summary_graph.number_of_nodes()} = "
              f"{G.number_of_nodes()/max(summary_graph.number_of_nodes(),1):.1f}x")
        print(f"Edge compression: {G.number_of_edges()}/{summary_graph.number_of_edges()} = "
              f"{G.number_of_edges()/max(summary_graph.number_of_edges(),1):.1f}x")

        session.commit()


if __name__ == "__main__":
    demo_snap()
