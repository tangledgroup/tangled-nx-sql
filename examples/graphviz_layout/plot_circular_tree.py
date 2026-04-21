"""
=============
Circular Tree
=============

This example shows a balanced tree with circular layout.

Adapted for nx_sql — uses spring/spectral layout as fallback when
graphviz CLI is unavailable.
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
def demo_circular_tree():
    """Visualize a balanced tree with circular layout."""

    with Session() as session:
        G_nx = nx.balanced_tree(3, 5)
        G = nx_sql.Graph(session, name="circular_tree_demo")
        G.add_nodes_from(G_nx.nodes())
        G.add_edges_from(G_nx.edges())

        # Try graphviz twopi layout, fall back to spectral
        try:
            pos = nx.drawing.nx_pydot.pydot_layout(G, prog="twopi")
        except OSError:
            print("graphviz CLI not found, using spectral_layout as fallback")
            pos = nx.spectral_layout(G)

        plt.figure(figsize=(8, 8))
        nx.draw(G, pos, node_size=20, alpha=0.5, node_color="blue", with_labels=False)
        plt.axis("equal")
        plt.savefig("examples/graphviz_layout/plot_circular_tree_output.png")
        plt.close()
        print("Saved: plot_circular_tree_output.png")

        session.commit()


if __name__ == "__main__":
    demo_circular_tree()
