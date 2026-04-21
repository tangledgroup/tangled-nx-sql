"""
======
iplotx
======

``iplotx`` (https://iplotx.readthedocs.io/) is a network visualisation library
designed to extend the styling options for native NetworkX objects. It uses
``matplotlib`` behind the scenes, just like NetworkX's internal functions.

Adapted for nx_sql — replicates iplotx styling with pure matplotlib
since iplotx is not available in this environment.
"""

from collections import defaultdict
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
def demo_iplotx():
    """Visualize a graph with iplotx-style styling using pure matplotlib."""

    with Session() as session:
        G_nx = nx.dense_gnm_random_graph(30, 40, seed=42)
        G = nx_sql.Graph(session, name="iplotx_demo")
        G.add_nodes_from(G_nx.nodes())
        G.add_edges_from(G_nx.edges())

        # Get largest connected component
        components = nx.connected_components(G)
        largest_component = max(components, key=len)
        H = G.subgraph(largest_component)

        # Compute layout
        layout = nx.kamada_kawai_layout(H)

        fig, ax = plt.subplots(figsize=(8, 8))

        # Draw edges with iplotx-style settings
        nx.draw_networkx_edges(
            H, layout, ax=ax,
            alpha=0.7,
            width=1.5,
        )

        # Per-node styling (iplotx-style)
        node_sizes = defaultdict(lambda: 17, {0: 50, 1: 30, 2: 40})
        node_colors = ["lightblue", "steelblue", "dodgerblue"]
        for i, node in enumerate(H):
            color = node_colors[i % len(node_colors)]
            size = node_sizes[node]
            nx.draw_networkx_nodes(
                H, layout,
                nodelist=[node],
                ax=ax,
                node_size=size,
                node_color=color,
                edgecolors="black",
                linewidths=1.5,
            )

        # Node labels (use single color for all)
        nx.draw_networkx_labels(
            H, layout, ax=ax,
            font_color="black",
            font_size=8,
        )

        ax.margins(0.1)
        fig.tight_layout()
        plt.savefig("examples/external/plot_iplotx_output.png")
        plt.close()
        print("Plot saved to examples/external/plot_iplotx_output.png")

        session.commit()


if __name__ == "__main__":
    demo_iplotx()
