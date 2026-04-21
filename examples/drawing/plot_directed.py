"""
==============
Directed Graph
==============

Draw a graph with directed edges using a colormap and different node sizes.

Adapted for nx_sql — uses SQLAlchemy persistence instead of in-memory graphs.
"""

import matplotlib as mpl
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
def demo_directed_graph():
    """Draw a directed graph with colored edges."""

    with Session() as session:
        seed = 13648
        G_nx = nx.random_k_out_graph(10, 3, 0.5, seed=seed)
        G = nx_sql.DiGraph(session, name="directed_graph_demo")
        G.add_nodes_from(G_nx.nodes())
        G.add_edges_from(G_nx.edges())

        pos = nx.spring_layout(G, seed=seed)

        node_sizes = [3 + 10 * i for i in range(len(G))]
        M = G.number_of_edges()
        edge_colors = list(range(2, M + 2))
        edge_alphas = [(5 + i) / (M + 4) for i in range(M)]
        cmap = plt.cm.plasma

        nodes = nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color="indigo")
        edges = nx.draw_networkx_edges(
            G,
            pos,
            node_size=node_sizes,
            arrowstyle="->",
            arrowsize=10,
            edge_color=edge_colors,
            edge_cmap=cmap,
            width=2,
        )
        for i in range(M):
            edges[i].set_alpha(edge_alphas[i])

        pc = mpl.collections.PatchCollection(edges, cmap=cmap)
        pc.set_array(edge_colors)

        ax = plt.gca()
        ax.set_axis_off()
        plt.colorbar(pc, ax=ax)
        plt.savefig("examples/drawing/plot_directed_output.png")
        plt.close()
        print("Plot saved to examples/drawing/plot_directed_output.png")

        session.commit()


if __name__ == "__main__":
    demo_directed_graph()
