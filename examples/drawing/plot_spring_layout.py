"""
=============
Spring Layout
=============

Draw graphs using the three different spring layout algorithms.

Adapted for nx_sql — uses SQLAlchemy persistence instead of in-memory graphs.
Note: sfdp (GraphViz) layout skipped as it requires pygraphviz.
"""

import time
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
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
def demo_spring_layout():
    """Compare spring layout methods on different graph types."""

    with Session() as session:
        negative_weight_graph = nx.complete_graph(4)
        negative_weight_graph[0][2]["weight"] = -1

        graphs = [
            (nx.grid_2d_graph(15, 15), "grid_2d"),
            (negative_weight_graph, "negative_weight"),
            (nx.gnp_random_graph(100, 0.005, seed=0), "gnp_random"),
        ]

        fig, axes = plt.subplots(3, 3, figsize=(9, 9))
        colors_map = {"force": "tab:blue", "energy": "tab:orange"}

        for i, (G_nx, name) in enumerate(graphs):
            G = nx_sql.Graph(session, name=f"spring_{name}_demo")
            G.add_nodes_from(G_nx.nodes())
            G.add_edges_from(G_nx.edges(data=True))

            t0 = time.perf_counter()
            pos = nx.spring_layout(G, method="force", seed=0)
            dt_force = time.perf_counter() - t0

            t0 = time.perf_counter()
            pos_energy = nx.spring_layout(G, method="energy", seed=0)
            dt_energy = time.perf_counter() - t0

            nx.draw(G, pos=pos, ax=axes[0, i], node_color=colors_map["force"], node_size=20)
            axes[0, i].set_title(f"{name}\nforce: {dt_force:.2f}s", fontsize=12)

            nx.draw(G, pos=pos_energy, ax=axes[1, i], node_color=colors_map["energy"], node_size=20)
            axes[1, i].set_title(f"energy: {dt_energy:.2f}s", fontsize=12)

        handles = [mpatches.Patch(color=color, label=key) for key, color in colors_map.items()]
        fig.legend(handles=handles, loc="upper center", ncol=3, fontsize=12)
        plt.tight_layout(rect=(0, 0, 1, 0.9))
        plt.savefig("examples/drawing/plot_spring_layout_output.png")
        plt.close()
        print("Plot saved to examples/drawing/plot_spring_layout_output.png")

        session.commit()


if __name__ == "__main__":
    demo_spring_layout()
