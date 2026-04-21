"""
=============
Node Colormap
=============

Draw a graph with matplotlib, color by degree.

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
def demo_node_colormap():
    """Draw a cycle graph with nodes colored by degree."""

    with Session() as session:
        G_nx = nx.cycle_graph(24)
        G = nx_sql.Graph(session, name="node_colormap_demo")
        G.add_nodes_from(G_nx.nodes())
        G.add_edges_from(G_nx.edges())

        pos = nx.circular_layout(G)
        nx.draw(G, pos, node_color=range(24), node_size=800, cmap=plt.cm.Blues)
        plt.savefig("examples/drawing/plot_node_colormap_output.png")
        plt.close()
        print("Plot saved to examples/drawing/plot_node_colormap_output.png")

        session.commit()


if __name__ == "__main__":
    demo_node_colormap()
