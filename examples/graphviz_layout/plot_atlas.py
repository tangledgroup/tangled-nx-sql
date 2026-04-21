"""
=====
Atlas
=====

Atlas of all connected graphs with up to 6 nodes.

Adapted for nx_sql — uses pydot for DOT layout instead of pygraphviz.
The image should show 142 graphs. We don't plot the empty graph nor the
single node graph.
"""

import random

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
def demo_atlas():
    """Generate the atlas of connected graphs and visualize with DOT layout."""

    with Session() as session:
        Atlas = nx.graph_atlas_g()[3:209]  # 0, 1, 2 => no edges. 208 is last 6 node graph
        U = nx.Graph()  # graph for union of all graphs in atlas
        GraphMatcher = nx.isomorphism.vf2userfunc.GraphMatcher

        for G in Atlas:
            if nx.number_connected_components(G) == 1:
                if not GraphMatcher(U, G).subgraph_is_isomorphic():
                    U = nx.disjoint_union(U, G)

        print(U)
        print(nx.number_connected_components(U), "connected components")

        # Try pydot_layout (requires graphviz CLI), fall back to spring_layout
        try:
            pos = nx.drawing.nx_pydot.pydot_layout(U, prog="neato")
        except OSError:
            print("graphviz CLI not found, using spring_layout as fallback")
            pos = nx.spring_layout(U, seed=42)

        plt.figure(1, figsize=(8, 8))
        C = (U.subgraph(c) for c in nx.connected_components(U))
        for g in C:
            c = [random.random()] * nx.number_of_nodes(g)
            # Compute subgraph positions
            g_pos = {n: pos[n] for n in g.nodes()}
            nx.draw(g, g_pos, node_size=40, node_color=c, vmin=0.0, vmax=1.0,
                    with_labels=False)
        plt.savefig("examples/graphviz_layout/plot_atlas_output.png")
        plt.close()
        print("Saved: plot_atlas_output.png")

        session.commit()


if __name__ == "__main__":
    demo_atlas()
