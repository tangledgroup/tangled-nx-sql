"""
==========
Four Grids
==========

Draw a 4x4 graph with matplotlib.

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
def demo_four_grids():
    """Draw a 4x4 grid graph in four different styles."""

    with Session() as session:
        G_nx = nx.grid_2d_graph(4, 4)
        G = nx_sql.Graph(session, name="four_grids_demo")
        G.add_nodes_from(G_nx.nodes())
        G.add_edges_from(G_nx.edges())

        pos = nx.spring_layout(G, iterations=100, seed=39775)

        fig, all_axes = plt.subplots(2, 2)
        ax = all_axes.flat

        nx.draw(G, pos, ax=ax[0], font_size=8)
        nx.draw(G, pos, ax=ax[1], node_size=0, with_labels=False)
        nx.draw(
            G,
            pos,
            ax=ax[2],
            node_color="tab:green",
            edgecolors="tab:gray",
            edge_color="tab:gray",
            node_size=250,
            with_labels=False,
            width=6,
        )
        H = nx.DiGraph(G)
        nx.draw(
            H,
            pos,
            ax=ax[3],
            node_color="tab:orange",
            node_size=20,
            with_labels=False,
            arrowsize=10,
            width=2,
        )

        for a in ax:
            a.margins(0.10)
        fig.tight_layout()
        plt.savefig("examples/drawing/plot_four_grids_output.png")
        plt.close()
        print("Plot saved to examples/drawing/plot_four_grids_output.png")

        session.commit()


if __name__ == "__main__":
    demo_four_grids()
