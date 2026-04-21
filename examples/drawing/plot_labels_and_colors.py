"""
=================
Labels And Colors
=================

Use `nodelist` and `edgelist` to apply custom coloring and labels to various
components of a graph.

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
def demo_labels_and_colors():
    """Draw a cubical graph with custom colored nodes and edges."""

    with Session() as session:
        G_nx = nx.cubical_graph()
        G = nx_sql.Graph(session, name="labels_colors_demo")
        G.add_nodes_from(G_nx.nodes())
        G.add_edges_from(G_nx.edges())

        pos = nx.spring_layout(G, seed=3113794652)

        options = {"edgecolors": "tab:gray", "node_size": 800, "alpha": 0.9}
        nx.draw_networkx_nodes(G, pos, nodelist=[0, 1, 2, 3], node_color="tab:red", **options)
        nx.draw_networkx_nodes(G, pos, nodelist=[4, 5, 6, 7], node_color="tab:blue", **options)

        nx.draw_networkx_edges(G, pos, width=1.0, alpha=0.5)
        nx.draw_networkx_edges(
            G, pos, edgelist=[(0, 1), (1, 2), (2, 3), (3, 0)],
            width=8, alpha=0.5, edge_color="tab:red",
        )
        nx.draw_networkx_edges(
            G, pos, edgelist=[(4, 5), (5, 6), (6, 7), (7, 4)],
            width=8, alpha=0.5, edge_color="tab:blue",
        )

        labels = {
            0: r"$a$", 1: r"$b$", 2: r"$c$", 3: r"$d$",
            4: r"$\alpha$", 5: r"$\beta$", 6: r"$\gamma$", 7: r"$\delta$",
        }
        nx.draw_networkx_labels(G, pos, labels, font_size=22, font_color="whitesmoke")

        plt.tight_layout()
        plt.axis("off")
        plt.savefig("examples/drawing/plot_labels_and_colors_output.png")
        plt.close()
        print("Plot saved to examples/drawing/plot_labels_and_colors_output.png")

        session.commit()


if __name__ == "__main__":
    demo_labels_and_colors()
