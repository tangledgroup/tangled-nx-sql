"""
==================
Spectral Embedding
==================

The spectral layout positions the nodes of the graph based on the
eigenvectors of the graph Laplacian.

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
def demo_spectral_grid():
    """Visualize spectral embedding of a grid graph with progressive edge removal."""

    with Session() as session:
        options = {"node_color": "C0", "node_size": 100}

        G_nx = nx.grid_2d_graph(6, 6)
        G = nx_sql.Graph(session, name="spectral_grid_demo")
        G.add_nodes_from(G_nx.nodes())
        G.add_edges_from(G_nx.edges())

        fig = plt.figure(figsize=(12, 12))

        # Original grid
        ax = fig.add_subplot(332)
        nx.draw_spectral(G, ax=ax, **options)
        ax.set_title("Original")

        # Remove edges progressively
        G.remove_edge((2, 2), (2, 3))
        ax = fig.add_subplot(334)
        nx.draw_spectral(G, ax=ax, **options)
        ax.set_title("(2,2)-(2,3)")

        G.remove_edge((3, 2), (3, 3))
        ax = fig.add_subplot(335)
        nx.draw_spectral(G, ax=ax, **options)
        ax.set_title("(3,2)-(3,3)")

        G.remove_edge((2, 2), (3, 2))
        ax = fig.add_subplot(336)
        nx.draw_spectral(G, ax=ax, **options)
        ax.set_title("(2,2)-(3,2)")

        G.remove_edge((2, 3), (3, 3))
        ax = fig.add_subplot(337)
        nx.draw_spectral(G, ax=ax, **options)
        ax.set_title("(2,3)-(3,3)")

        G.remove_edge((1, 2), (1, 3))
        ax = fig.add_subplot(338)
        nx.draw_spectral(G, ax=ax, **options)
        ax.set_title("(1,2)-(1,3)")

        G.remove_edge((4, 2), (4, 3))
        ax = fig.add_subplot(339)
        nx.draw_spectral(G, ax=ax, **options)
        ax.set_title("(4,2)-(4,3)")

        fig.tight_layout()
        plt.savefig("examples/drawing/plot_spectral_grid_output.png")
        plt.close()
        print("Plot saved to examples/drawing/plot_spectral_grid_output.png")

        session.commit()


if __name__ == "__main__":
    demo_spectral_grid()
