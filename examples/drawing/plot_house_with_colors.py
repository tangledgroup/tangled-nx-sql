"""
=================
House With Colors
=================

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
def demo_house_with_colors():
    """Draw a house graph with colored nodes."""

    with Session() as session:
        G_nx = nx.house_graph()
        G = nx_sql.Graph(session, name="house_colors_demo")
        G.add_nodes_from(G_nx.nodes())
        G.add_edges_from(G_nx.edges())

        pos = {0: (0, 0), 1: (1, 0), 2: (0, 1), 3: (1, 1), 4: (0.5, 2.0)}

        nx.draw_networkx_nodes(
            G, pos, node_size=3000, nodelist=[0, 1, 2, 3], node_color="tab:blue"
        )
        nx.draw_networkx_nodes(G, pos, node_size=2000, nodelist=[4], node_color="tab:orange")
        nx.draw_networkx_edges(G, pos, alpha=0.5, width=6)

        ax = plt.gca()
        ax.margins(0.11)
        plt.tight_layout()
        plt.axis("off")
        plt.savefig("examples/drawing/plot_house_with_colors_output.png")
        plt.close()
        print("Plot saved to examples/drawing/plot_house_with_colors_output.png")

        session.commit()


if __name__ == "__main__":
    demo_house_with_colors()
