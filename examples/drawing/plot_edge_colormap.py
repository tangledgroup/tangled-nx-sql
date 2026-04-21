"""
=============
Edge Colormap
=============

Draw a graph with matplotlib, color edges.

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
def demo_edge_colormap():
    """Draw a star graph with colored edges."""

    with Session() as session:
        G_nx = nx.star_graph(20)
        G = nx_sql.Graph(session, name="edge_colormap_demo")
        G.add_nodes_from(G_nx.nodes())
        G.add_edges_from(G_nx.edges())

        pos = nx.spring_layout(G, seed=63)
        colors = list(range(20))
        options = {
            "node_color": "#A0CBE2",
            "edge_color": colors,
            "width": 4,
            "edge_cmap": plt.cm.Blues,
            "with_labels": False,
        }
        nx.draw(G, pos, **options)
        plt.savefig("examples/drawing/plot_edge_colormap_output.png")
        plt.close()
        print("Plot saved to examples/drawing/plot_edge_colormap_output.png")

        session.commit()


if __name__ == "__main__":
    demo_edge_colormap()
