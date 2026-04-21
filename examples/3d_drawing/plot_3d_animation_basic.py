"""
===============
Basic Animation
===============

NetworkX supports several 3D layout functions for visualization.
These layouts can be combined with matplotlib animation for 3D graph
visualization.

Adapted for nx_sql — uses SQLAlchemy persistence and saves animation
as GIF instead of showing interactively.
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
def demo_3d_animation_basic():
    """Create a rotating 3D graph animation saved as GIF."""

    with Session() as session:
        G_nx = nx.dodecahedral_graph()
        G = nx_sql.Graph(session, name="3d_animation_basic_demo")
        G.add_nodes_from(G_nx.nodes())
        G.add_edges_from(G_nx.edges())

        pos = nx.spectral_layout(G, dim=3)
        nodes = np.array([pos[v] for v in G])
        edges = np.array([(pos[u], pos[v]) for u, v in G.edges()])

        fig = plt.figure()
        ax = fig.add_subplot(111, projection="3d")
        ax.grid(False)
        ax.set_axis_off()

        def init():
            ax.clear()
            ax.scatter(*nodes.T, alpha=0.2, s=100, color="blue")
            for vizedge in edges:
                ax.plot(*vizedge.T, color="gray")
            ax.grid(False)
            ax.set_axis_off()

        def _frame_update(index):
            ax.view_init(index * 0.2, index * 0.5)

        fig.tight_layout()
        ani = animation.FuncAnimation(
            fig, _frame_update, init_func=init,
            interval=50, cache_frame_data=False, frames=100,
        )
        ani.save("examples/3d_drawing/plot_3d_animation_basic_output.gif",
                 writer="pillow", fps=20)
        plt.close()
        print("Animation saved to examples/3d_drawing/plot_3d_animation_basic_output.gif")

        session.commit()


if __name__ == "__main__":
    demo_3d_animation_basic()
