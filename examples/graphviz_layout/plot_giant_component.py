"""
===============
Giant Component
===============

This example illustrates the sudden appearance of a
giant connected component in a binomial random graph.

Adapted for nx_sql — uses pydot/spring layout as fallback.
"""

import math

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


def _try_graphviz_layout(G):
    try:
        return nx.drawing.nx_pydot.pydot_layout(G, prog="neato")
    except OSError:
        return nx.spring_layout(G, seed=42)


@print_docstring
def demo_giant_component():
    """Visualize the giant component transition in random graphs."""

    with Session() as session:
        n = 150
        p_giant = 1.0 / (n - 1)
        p_conn = math.log(n) / n
        pvals = [0.003, 0.006, 0.008, 0.015]

        fig, axes = plt.subplots(2, 2)
        for p, ax, seed in zip(pvals, axes.ravel(), range(len(pvals))):
            G_nx = nx.binomial_graph(n, p, seed=seed)
            G = nx_sql.Graph(session, name=f"giant_p{p}")
            G.add_nodes_from(G_nx.nodes())
            G.add_edges_from(G_nx.edges())

            connected = [nd for nd, d in G.degree() if d > 0]
            disconnected = list(set(G.nodes()) - set(connected))
            Gcc = sorted(nx.connected_components(G), key=len, reverse=True)
            G0 = G.subgraph(Gcc[0])

            pos = _try_graphviz_layout(G)
            ax.set_title(f"p = {p:.3f}")
            options = {"ax": ax, "edge_color": "tab:red"}
            nx.draw_networkx_edges(G0, pos, width=6.0, **options)
            for Gi in Gcc[1:]:
                if len(Gi) > 1:
                    nx.draw_networkx_edges(G.subgraph(Gi), pos, alpha=0.3, width=5.0, **options)
            options = {"ax": ax, "node_size": 30, "edgecolors": "white"}
            nx.draw(G, pos, nodelist=connected, **options)
            nx.draw(G, pos, nodelist=disconnected, alpha=0.25, **options)

        fig.tight_layout()
        plt.savefig("examples/graphviz_layout/plot_giant_component_output.png")
        plt.close()
        print("Saved: plot_giant_component_output.png")

        session.commit()


if __name__ == "__main__":
    demo_giant_component()
