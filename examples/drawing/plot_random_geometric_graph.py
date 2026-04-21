"""
======================
Random Geometric Graph
======================

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
def demo_random_geometric():
    """Create and visualize a random geometric graph."""

    with Session() as session:
        G_nx = nx.random_geometric_graph(200, 0.125, seed=896803)
        # Get positions from in-memory graph
        pos = nx.get_node_attributes(G_nx, "pos")

        # Build nx_sql graph
        G = nx_sql.Graph(session, name="random_geometric_demo")
        for n, d in G_nx.nodes(data=True):
            G.add_node(n, **d)
        G.add_edges_from(G_nx.edges())

        # find node near center (0.5,0.5)
        dmin = 1
        ncenter = 0
        for n in pos:
            x, y = pos[n]
            d = (x - 0.5) ** 2 + (y - 0.5) ** 2
            if d < dmin:
                ncenter = n
                dmin = d

        p = nx.single_source_shortest_path_length(G, ncenter)

        plt.figure(figsize=(8, 8))
        nx.draw_networkx_edges(G, pos, alpha=0.4)
        nx.draw_networkx_nodes(
            G, pos, nodelist=list(p.keys()), node_size=80,
            node_color=list(p.values()), cmap=plt.cm.Reds_r,
        )

        plt.xlim(-0.05, 1.05)
        plt.ylim(-0.05, 1.05)
        plt.axis("off")
        plt.savefig("examples/drawing/plot_random_geometric_graph_output.png")
        plt.close()
        print("Plot saved to examples/drawing/plot_random_geometric_graph_output.png")

        session.commit()


if __name__ == "__main__":
    demo_random_geometric()
