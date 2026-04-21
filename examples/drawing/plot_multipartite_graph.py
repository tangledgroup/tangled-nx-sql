"""
===================
Multipartite Layout
===================

Adapted for nx_sql — uses SQLAlchemy persistence instead of in-memory graphs.
"""

import itertools
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


def multilayered_graph(*subset_sizes):
    extents = nx.utils.pairwise(itertools.accumulate((0,) + subset_sizes))
    layers = [range(start, end) for start, end in extents]
    G = nx.Graph()
    for i, layer in enumerate(layers):
        G.add_nodes_from(layer, layer=i)
    for layer1, layer2 in nx.utils.pairwise(layers):
        G.add_edges_from(itertools.product(layer1, layer2))
    return G


@print_docstring
def demo_multipartite_layout():
    """Visualize a multipartite graph."""

    with Session() as session:
        subset_sizes = [5, 5, 4, 3, 2, 4, 4, 3]
        subset_color = [
            "gold", "violet", "violet", "violet", "violet",
            "limegreen", "limegreen", "darkorange",
        ]

        G_nx = multilayered_graph(*subset_sizes)
        # Build nx_sql graph with node attributes
        G = nx_sql.Graph(session, name="multipartite_demo")
        for n, d in G_nx.nodes(data=True):
            G.add_node(n, **d)
        G.add_edges_from(G_nx.edges())

        color = [subset_color[data["layer"]] for v, data in G.nodes(data=True)]
        pos = nx.multipartite_layout(G, subset_key="layer")
        plt.figure(figsize=(8, 8))
        nx.draw(G, pos, node_color=color, with_labels=False)
        plt.axis("equal")
        plt.savefig("examples/drawing/plot_multipartite_graph_output.png")
        plt.close()
        print("Plot saved to examples/drawing/plot_multipartite_graph_output.png")

        session.commit()


if __name__ == "__main__":
    demo_multipartite_layout()
