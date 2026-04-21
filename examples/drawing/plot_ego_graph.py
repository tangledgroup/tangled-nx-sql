"""
=========
Ego Graph
=========

Example using the NetworkX ego_graph() function to return the main egonet of
the largest hub in a Barabási-Albert network.

Adapted for nx_sql — uses SQLAlchemy persistence instead of in-memory graphs.
"""

from operator import itemgetter

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
def demo_ego_graph():
    """Create an ego graph of the largest hub in a BA network."""

    with Session() as session:
        n = 1000
        m = 2
        seed = 20532
        G_nx = nx.barabasi_albert_graph(n, m, seed=seed)
        G = nx_sql.Graph(session, name="ego_graph_demo")
        G.add_nodes_from(G_nx.nodes())
        G.add_edges_from(G_nx.edges())

        node_and_degree = G.degree()
        (largest_hub, degree) = sorted(node_and_degree, key=itemgetter(1))[-1]

        hub_ego = nx.ego_graph(G, largest_hub)

        pos = nx.spring_layout(hub_ego, seed=seed)
        nx.draw(hub_ego, pos, node_color="b", node_size=50, with_labels=False)

        options = {"node_size": 300, "node_color": "r"}
        nx.draw_networkx_nodes(hub_ego, pos, nodelist=[largest_hub], **options)
        plt.savefig("examples/drawing/plot_ego_graph_output.png")
        plt.close()
        print(f"Ego graph of node {largest_hub} (degree={degree}) saved.")

        session.commit()


if __name__ == "__main__":
    demo_ego_graph()
