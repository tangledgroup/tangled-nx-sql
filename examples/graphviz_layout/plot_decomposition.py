"""
=============
Decomposition
=============

Example of creating a junction tree from a directed graph.

Adapted for nx_sql — uses pydot/spring layout as fallback when
graphviz CLI is unavailable.
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


def _try_graphviz_layout(G, prog="neato"):
    """Try graphviz layout, fall back to spring."""
    try:
        return nx.drawing.nx_pydot.pydot_layout(G, prog=prog)
    except OSError:
        print(f"  graphviz CLI not found, using spring_layout")
        return nx.spring_layout(G, seed=42)


@print_docstring
def demo_decomposition():
    """Create and visualize a Bayesian network decomposition."""

    with Session() as session:
        B_nx = nx.DiGraph()
        B_nx.add_nodes_from(["A", "B", "C", "D", "E", "F"])
        B_nx.add_edges_from(
            [("A", "B"), ("A", "C"), ("B", "D"), ("B", "F"), ("C", "E"), ("E", "F")]
        )

        # Store in nx_sql
        B = nx_sql.DiGraph(session, name="decomposition_bn")
        B.add_nodes_from(B_nx.nodes())
        B.add_edges_from(B_nx.edges())

        options = {"with_labels": True, "node_color": "white", "edgecolors": "blue"}

        fig = plt.figure(figsize=(6, 9))
        axgrid = fig.add_gridspec(3, 2)

        # Bayesian Network
        ax1 = fig.add_subplot(axgrid[0, 0])
        ax1.set_title("Bayesian Network")
        pos = _try_graphviz_layout(B, "neato")
        nx.draw_networkx(B, pos=pos, **options)

        # Moralized Graph
        mg = nx.moral_graph(B)
        ax2 = fig.add_subplot(axgrid[0, 1], sharex=ax1, sharey=ax1)
        ax2.set_title("Moralized Graph")
        nx.draw_networkx(mg, pos=pos, **options)

        # Junction Tree
        jt = nx.junction_tree(B)
        ax3 = fig.add_subplot(axgrid[1:, :])
        ax3.set_title("Junction Tree")
        ax3.margins(0.15, 0.25)
        nsize = [2000 * len(n) for n in list(jt.nodes())]
        jt_pos = _try_graphviz_layout(jt, "neato")
        nx.draw_networkx(jt, pos=jt_pos, node_size=nsize, **options)

        plt.tight_layout()
        plt.savefig("examples/graphviz_layout/plot_decomposition_output.png")
        plt.close()
        print("Saved: plot_decomposition_output.png")

        session.commit()


if __name__ == "__main__":
    demo_decomposition()
