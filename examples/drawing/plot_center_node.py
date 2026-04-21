"""
==============
Center Node
==============

Draw a graph with the center node.

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
def demo_center_node():
    """Draw a graph with the center node highlighted."""

    with Session() as session:
        # Create in-memory path graph for layout computation
        G_nx = nx.path_graph(25)
        center_nodes = list(nx.center(G_nx))

        # Store in nx_sql
        G = nx_sql.Graph(session, name="center_node_demo")
        G.add_nodes_from(G_nx.nodes())
        G.add_edges_from(G_nx.edges())

        print(f"Center nodes: {center_nodes}")

        pos = nx.spring_layout(G_nx, seed=10396953)
        nx.draw_networkx_nodes(G, pos, node_size=20)
        nx.draw_networkx_nodes(G, pos, nodelist=center_nodes, node_color='r', node_size=100)
        nx.draw_networkx_edges(G, pos, alpha=0.5)
        plt.savefig("examples/drawing/plot_center_node_output.png")
        plt.close()
        print("Plot saved to examples/drawing/plot_center_node_output.png")

        session.commit()


if __name__ == "__main__":
    demo_center_node()
