"""
======================================
Plotting MultiDiGraph Edges and Labels
======================================

This example shows how to plot edges and labels for a MultiDiGraph class object.

Adapted for nx_sql — uses SQLAlchemy persistence instead of in-memory graphs.
"""

import itertools as it
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base
import sys; sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent.parent.parent))
from examples.utils import print_docstring

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def draw_labeled_multigraph(G, attr_name, ax=None):
    connectionstyle = [f"arc3,rad={r}" for r in it.accumulate([0.15] * 4)]
    pos = nx.shell_layout(G)
    nx.draw_networkx_nodes(G, pos, ax=ax)
    nx.draw_networkx_labels(G, pos, font_size=20, ax=ax)
    nx.draw_networkx_edges(
        G, pos, edge_color="grey", connectionstyle=connectionstyle, ax=ax
    )
    # Build labels from multi-edge data
    labels = {}
    for u, v, key_data in G.edges(data=True):
        for k, d in key_data.items():
            labels[(u, v, k)] = f"{attr_name}={d.get(attr_name, '')}"
    nx.draw_networkx_edge_labels(
        G, pos, labels, connectionstyle=connectionstyle, label_pos=0.3,
        font_color="blue", bbox={"alpha": 0}, ax=ax,
    )


@print_docstring
def demo_multigraphs():
    """Visualize MultiDiGraph with multiple edges between node pairs."""

    with Session() as session:
        nodes = "ABC"
        prod = list(it.product(nodes, repeat=2))
        pair_dict = {f"Product x {i}": prod * i for i in range(1, 5)}

        fig, axes = plt.subplots(2, 2)
        for (name, pairs), ax in zip(pair_dict.items(), np.ravel(axes)):
            G = nx_sql.MultiDiGraph(session, name=f"multigraph_{name.replace(' ', '_')}")
            for i, (u, v) in enumerate(pairs):
                G.add_edge(u, v, w=round(i / 3, 2))
            draw_labeled_multigraph(G, "w", ax)
            ax.set_title(name)
        fig.tight_layout()
        plt.savefig("examples/drawing/plot_multigraphs_output.png")
        plt.close()
        print("Plot saved to examples/drawing/plot_multigraphs_output.png")

        session.commit()


if __name__ == "__main__":
    demo_multigraphs()
