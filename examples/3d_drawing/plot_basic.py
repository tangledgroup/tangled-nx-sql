"""
================
Basic matplotlib
================

A basic example of 3D Graph visualization using `mpl_toolkits.mplot_3d`.

Adapted for nx_sql — uses SQLAlchemy persistence instead of in-memory graphs.
"""

import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
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
def demo_3d_basic():
    """Create a 3D visualization of a cycle graph."""

    with Session() as session:
        G = nx_sql.Graph(session, name="3d_basic_demo")
        G_nx = nx.cycle_graph(20)
        G.add_nodes_from(G_nx.nodes())
        G.add_edges_from(G_nx.edges())

        # 3d spring layout
        pos = nx.spring_layout(G, dim=3, seed=779)
        # Extract node and edge positions from the layout
        node_xyz = np.array([pos[v] for v in sorted(G)])
        edge_xyz = np.array([(pos[u], pos[v]) for u, v in G.edges()])

        # Create the 3D figure
        fig = plt.figure()
        ax = fig.add_subplot(111, projection="3d")

        # Plot the nodes - alpha is scaled by "depth" automatically
        ax.scatter(*node_xyz.T, s=100, ec="w")

        # Plot the edges
        for vizedge in edge_xyz:
            ax.plot(*vizedge.T, color="tab:gray")

        def _format_axes(ax):
            """Visualization options for the 3D axes."""
            ax.grid(False)
            for dim in (ax.xaxis, ax.yaxis, ax.zaxis):
                dim.set_ticks([])
            ax.set_xlabel("x")
            ax.set_ylabel("y")
            ax.set_zlabel("z")

        _format_axes(ax)
        fig.tight_layout()
        plt.savefig("examples/3d_drawing/plot_basic_output.png")
        plt.close()
        print("3D plot saved to examples/3d_drawing/plot_basic_output.png")

        session.commit()


if __name__ == "__main__":
    demo_3d_basic()
