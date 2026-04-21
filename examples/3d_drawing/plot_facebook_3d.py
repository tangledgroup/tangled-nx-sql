"""
====================
3D Facebook Network
====================

Visualizing a subsampled subgraph of the Facebook graph in 3D plotting
with matplotlib.

Adapted for nx_sql — uses SQLAlchemy persistence and saves animation
as GIF. Uses synthetic graph instead of downloading external data.
"""

import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib import animation
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
def demo_facebook_3d():
    """Visualize a Facebook-like network subgraph in 3D."""

    with Session() as session:
        # Use a synthetic graph (similar structure to Facebook social network)
        G_nx = nx.erdos_renyi_graph(100, 0.05, seed=42)
        # Extract ego graph for node 0
        node = 0
        radius = 3
        ego = nx.ego_graph(G_nx, node, radius)

        G = nx_sql.Graph(session, name="facebook_3d_demo")
        G.add_nodes_from(ego.nodes())
        G.add_edges_from(ego.edges())

        pos = nx.spring_layout(G, dim=3, seed=25519, method="energy")

        nodes = np.array([pos[v] for v in G])
        edges = np.array([(pos[u], pos[v]) for u, v in G.edges()])
        point_size = 1000 // max(np.sqrt(len(G)), 1)

        fig = plt.figure()
        ax = fig.add_subplot(111, projection="3d")
        ax.grid(False)
        ax.set_axis_off()

        def init():
            ax.clear()
            ax.scatter(*nodes.T, alpha=0.2, s=max(point_size, 5), ec="w")
            for vizedge in edges:
                ax.plot(*vizedge.T, color="tab:gray")
            ax.grid(False)
            ax.set_axis_off()

        def _frame_update(idx):
            ax.view_init(idx * 0.9, idx * 1.8)

        fig.tight_layout()
        ani = animation.FuncAnimation(
            fig, _frame_update, init_func=init,
            interval=50, cache_frame_data=False, frames=40,
        )
        ani.save("examples/3d_drawing/plot_facebook_3d_output.gif",
                 writer="pillow", fps=20)
        plt.close()
        print(f"Animation saved to examples/3d_drawing/plot_facebook_3d_output.gif")
        print(f"Ego graph: {len(G)} nodes, {G.number_of_edges()} edges")

        session.commit()


if __name__ == "__main__":
    demo_facebook_3d()
