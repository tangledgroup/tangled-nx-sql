"""
=======
Sampson
=======

Sampson's monastery data.

Shows how to read data from a zip file and plot multiple frames.

Adapted for nx_sql — uses SQLAlchemy persistence instead of in-memory graphs.
"""

import zipfile

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
def demo_sampson():
    """Visualize Sampson's monastery data across 3 frames."""

    with Session() as session:
        with zipfile.ZipFile("examples/drawing/sampson_data.zip") as zf:
            G1, G2, G3 = [
                nx.parse_edgelist(
                    zf.read(f"samplike{n}.txt").decode().split("\n"), delimiter="\t"
                )
                for n in (1, 2, 3)
            ]

        pos = nx.spring_layout(G3, iterations=100, seed=173)

        fig, axes = plt.subplots(2, 2)
        plot_opts = {"node_size": 50, "with_labels": False}

        for num, (G, ax) in enumerate(zip((G1, G2, G3), axes.ravel()), start=1):
            nx.draw(G, pos, ax=ax, **plot_opts)
            ax.set_title(f"samplike{num}")

        ax = axes[1, 1]
        nx.draw_networkx_nodes(G3, pos, ax=ax, node_size=50)
        for G, edge_clr in zip((G1, G2, G3), "rgb"):
            nx.draw_networkx_edges(G, pos, ax=ax, edge_color=edge_clr)

        ax.set_title("samplike1,2,3")
        ax.set_axis_off()
        plt.tight_layout()
        plt.savefig("examples/drawing/plot_sampson_output.png")
        plt.close()
        print("Plot saved to examples/drawing/plot_sampson_output.png")


if __name__ == "__main__":
    demo_sampson()
