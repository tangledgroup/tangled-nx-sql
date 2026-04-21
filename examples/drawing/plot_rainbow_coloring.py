"""
================
Rainbow Coloring
================

Generate a complete graph with 13 nodes in a circular layout with the
edges colored by node distance.

Adapted for nx_sql — uses SQLAlchemy persistence instead of in-memory graphs.
"""

import matplotlib.pyplot as plt
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
def demo_rainbow_coloring():
    """Color edges of a complete graph by node distance."""

    with Session() as session:
        nnodes = 13
        G_nx = nx.complete_graph(nnodes)

        # Build edge list with colors
        node_dist_to_color = {
            1: "tab:red", 2: "tab:orange", 3: "tab:olive",
            4: "tab:green", 5: "tab:blue", 6: "tab:purple",
        }

        n = (nnodes - 1) // 2
        ndist_iter = list(range(1, n + 1))
        ndist_iter += ndist_iter[::-1]

        def cycle(nlist, n):
            return nlist[-n:] + nlist[:-n]

        nodes = list(G_nx.nodes())
        edges_with_colors = []
        for i, nd in enumerate(ndist_iter):
            for u, v in zip(nodes, cycle(nodes, i + 1)):
                edges_with_colors.append((u, v, {"color": node_dist_to_color[nd]}))

        G = nx_sql.Graph(session, name="rainbow_coloring_demo")
        G.add_nodes_from(G_nx.nodes())
        G.add_edges_from(edges_with_colors)

        pos = nx.circular_layout(G)
        fig, ax = plt.subplots(figsize=(8, 8))
        node_opts = {"node_size": 500, "node_color": "w", "edgecolors": "k", "linewidths": 2.0}
        nx.draw_networkx_nodes(G, pos, **node_opts)
        nx.draw_networkx_labels(G, pos, font_size=14)
        edge_colors = [d.get("color", "black") for _, _, d in G.edges(data=True)]
        nx.draw_networkx_edges(G, pos, width=2.0, edge_color=edge_colors)

        ax.set_axis_off()
        fig.tight_layout()
        plt.savefig("examples/drawing/plot_rainbow_coloring_output.png")
        plt.close()
        print("Plot saved to examples/drawing/plot_rainbow_coloring_output.png")

        session.commit()


if __name__ == "__main__":
    demo_rainbow_coloring()
