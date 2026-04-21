"""
===========
Simple Path
===========

Draw a graph with matplotlib.

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
def demo_simple_path():
    """Draw a simple path graph."""

    with Session() as session:
        G_nx = nx.path_graph(8)
        G = nx_sql.Graph(session, name="simple_path_demo")
        G.add_nodes_from(G_nx.nodes())
        G.add_edges_from(G_nx.edges())

        pos = nx.spring_layout(G, seed=47)
        nx.draw(G, pos=pos)
        plt.savefig("examples/drawing/plot_simple_path_output.png")
        plt.close()
        print("Plot saved to examples/drawing/plot_simple_path_output.png")

        session.commit()


if __name__ == "__main__":
    demo_simple_path()
