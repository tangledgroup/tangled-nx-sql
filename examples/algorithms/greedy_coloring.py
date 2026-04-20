"""Demonstrate graph coloring with nx_sql.

Mirrors networkx/examples/algorithms/plot_greedy_coloring.py but uses
SQLAlchemy persistence. Tests greedy coloring on the dodecahedral graph.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def demo_greedy_coloring():
    """Color the dodecahedral graph using greedy coloring."""

    with Session() as session:
        # Create dodecahedral graph
        G_nx = nx.dodecahedral_graph()
        G = nx_sql.Graph(session, name="coloring_demo")
        G.add_nodes_from(G_nx.nodes())
        G.add_edges_from(G_nx.edges())

        print("=== Graph Coloring ===")
        print(f"Graph: dodecahedral ({G.number_of_nodes()} nodes, {G.number_of_edges()} edges)")

        # Greedy coloring
        coloring = nx.greedy_color(G)
        num_colors = max(coloring.values()) + 1
        print(f"\nNumber of colors used: {num_colors}")

        # Print color assignment
        print("\nColor assignments:")
        for node in sorted(coloring.keys()):
            print(f"  Node {node}: color {coloring[node]}")

        # Verify no adjacent nodes share the same color
        valid = True
        for u, v in G.edges():
            if coloring[u] == coloring[v]:
                print(f"  ERROR: Nodes {u} and {v} have same color!")
                valid = False
        if valid:
            print("\n✓ All adjacent nodes have different colors")

        # Degree-based ordering (often gives better results)
        print(f"\n=== Degree-Ordered Coloring ===")
        coloring_deg = nx.greedy_color(G, strategy="largest_first")
        num_colors_deg = max(coloring_deg.values()) + 1
        print(f"Colors used (largest_first): {num_colors_deg}")

        # Independent sets per color
        for color in range(num_colors_deg):
            nodes_in_color = [n for n, c in coloring_deg.items() if c == color]
            print(f"  Color {color}: {nodes_in_color}")

        session.commit()


if __name__ == "__main__":
    demo_greedy_coloring()
