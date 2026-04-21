"""
==============
Weighted Graph
==============

An example using Graph as a weighted network.

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
def demo_weighted_graph():
    """Visualize a weighted graph with different edge styles."""

    with Session() as session:
        G = nx_sql.Graph(session, name="weighted_graph_demo")
        G.add_edge("a", "b", weight=0.6)
        G.add_edge("a", "c", weight=0.2)
        G.add_edge("c", "d", weight=0.1)
        G.add_edge("c", "e", weight=0.7)
        G.add_edge("c", "f", weight=0.9)
        G.add_edge("a", "d", weight=0.3)

        elarge = [(u, v) for (u, v, d) in G.edges(data=True) if d["weight"] > 0.5]
        esmall = [(u, v) for (u, v, d) in G.edges(data=True) if d["weight"] <= 0.5]

        pos = nx.spring_layout(G, seed=7)

        nx.draw_networkx_nodes(G, pos, node_size=700)
        nx.draw_networkx_edges(G, pos, edgelist=elarge, width=6)
        nx.draw_networkx_edges(
            G, pos, edgelist=esmall, width=6, alpha=0.5, edge_color="b", style="dashed"
        )
        nx.draw_networkx_labels(G, pos, font_size=20, font_family="sans-serif")
        edge_labels = nx.get_edge_attributes(G, "weight")
        nx.draw_networkx_edge_labels(G, pos, edge_labels)

        ax = plt.gca()
        ax.margins(0.08)
        plt.axis("off")
        plt.tight_layout()
        plt.savefig("examples/drawing/plot_weighted_graph_output.png")
        plt.close()
        print("Plot saved to examples/drawing/plot_weighted_graph_output.png")

        session.commit()


if __name__ == "__main__":
    demo_weighted_graph()
