"""
==========================
Traveling Salesman Problem
==========================

This is an example of a drawing solution of the traveling salesman problem.

Adapted for nx_sql — uses SQLAlchemy persistence instead of in-memory graphs.
"""

import math
import matplotlib.pyplot as plt
import networkx as nx
import networkx.algorithms.approximation as nx_app
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
def demo_tsp():
    """Solve TSP using Christofides algorithm on a geometric graph."""

    with Session() as session:
        G_nx = nx.random_geometric_graph(20, radius=0.4, seed=3)
        pos = nx.get_node_attributes(G_nx, "pos")
        pos[0] = (0.5, 0.5)

        # Build complete graph with edge weights
        edges_with_weights = []
        for i in range(len(pos)):
            for j in range(i + 1, len(pos)):
                dist = math.hypot(pos[i][0] - pos[j][0], pos[i][1] - pos[j][1])
                edges_with_weights.append((i, j, {"weight": dist}))

        G = nx_sql.Graph(session, name="tsp_demo")
        G.add_nodes_from(G_nx.nodes())
        G.add_edges_from(edges_with_weights)

        cycle = nx_app.christofides(G, weight="weight")
        edge_list = list(nx.utils.pairwise(cycle))

        print("The route of the traveller is:", cycle)

        nx.draw_networkx(
            G, pos, with_labels=True, edgelist=edge_list,
            edge_color="red", node_size=200, width=3,
        )
        plt.savefig("examples/drawing/plot_tsp_output.png")
        plt.close()
        print("Plot saved to examples/drawing/plot_tsp_output.png")

        session.commit()


if __name__ == "__main__":
    demo_tsp()
