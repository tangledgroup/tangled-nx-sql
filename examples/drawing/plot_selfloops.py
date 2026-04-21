"""
==========
Self-loops
==========

A self-loop is an edge that originates from and terminates the same node.

Adapted for nx_sql — uses SQLAlchemy persistence instead of in-memory graphs.
"""

import networkx as nx
import matplotlib.pyplot as plt
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
def demo_selfloops():
    """Draw a graph with self-loops."""

    with Session() as session:
        G_nx = nx.complete_graph(3, create_using=nx.DiGraph)
        G = nx_sql.DiGraph(session, name="selfloops_demo")
        G.add_nodes_from(G_nx.nodes())
        G.add_edges_from(G_nx.edges())
        G.add_edge(0, 0)
        pos = nx.circular_layout(G)

        nx.draw(G, pos, with_labels=True)

        edgelist = [(1, 1), (2, 2)]
        G.add_edges_from(edgelist)
        nx.draw_networkx_edges(G, pos, edgelist=edgelist, arrowstyle="<|-", style="dashed")

        plt.savefig("examples/drawing/plot_selfloops_output.png")
        plt.close()
        print("Plot saved to examples/drawing/plot_selfloops_output.png")

        session.commit()


if __name__ == "__main__":
    demo_selfloops()
