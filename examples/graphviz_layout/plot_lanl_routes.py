"""
===========
Lanl Routes
===========

Routes to LANL from 186 sites on the Internet.

Adapted for nx_sql — uses pydot/spring layout as fallback when
graphviz CLI is unavailable.
"""

import random

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


def _try_graphviz_layout(G, prog="twopi", root=None):
    try:
        return nx.drawing.nx_pydot.pydot_layout(G, prog=prog)
    except OSError:
        print("  graphviz CLI not found, using spectral_layout")
        return nx.spectral_layout(G)


@print_docstring
def demo_lanl_routes():
    """Visualize the LANL internet routes graph."""

    with Session() as session:
        # Use synthetic data (similar structure to lanl_routes)
        G_nx = nx.random_regular_graph(3, 186, seed=42)
        # Ensure connected
        while not nx.is_connected(G_nx):
            G_nx = nx.random_regular_graph(3, 186, seed=None)

        # Assign rtt-like attributes
        G = nx_sql.Graph(session, name="lanl_routes_demo")
        G.add_nodes_from(G_nx.nodes())
        G.add_edges_from(G_nx.edges())
        for n in G:
            G.add_node(n, rtt=random.random())

        print(G)
        print(nx.number_connected_components(G), "connected components")

        # Use twopi-like radial layout (spectral as fallback)
        pos = _try_graphviz_layout(G, prog="twopi", root=0)

        plt.figure(figsize=(8, 8))
        options = {"with_labels": False, "alpha": 0.5, "node_size": 15}
        rtt_vals = [G.nodes[v].get("rtt", 0) for v in G]
        nx.draw(G, pos, node_color=rtt_vals, **options)

        xmax = 1.02 * max(xx for xx, yy in pos.values())
        ymax = 1.02 * max(yy for xx, yy in pos.values())
        plt.xlim(0, xmax)
        plt.ylim(0, ymax)
        plt.savefig("examples/graphviz_layout/plot_lanl_routes_output.png")
        plt.close()
        print("Saved: plot_lanl_routes_output.png")

        session.commit()


if __name__ == "__main__":
    demo_lanl_routes()
