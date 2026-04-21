"""
==============
Cluster Layout
==============

This example illustrates how to combine multiple layouts to visualize node
clusters.

Adapted for nx_sql — uses SQLAlchemy persistence instead of in-memory graphs.
"""

import networkx as nx
import matplotlib.pyplot as plt
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
def demo_cluster_layout():
    """Visualize node clusters using combined layouts."""

    with Session() as session:
        G_nx = nx.davis_southern_women_graph()
        G = nx_sql.Graph(session, name="cluster_layout_demo")
        G.add_nodes_from(G_nx.nodes())
        G.add_edges_from(G_nx.edges())

        communities = nx.community.greedy_modularity_communities(G)

        supergraph = nx.cycle_graph(len(communities))
        superpos = nx.spring_layout(supergraph, scale=2, seed=429)

        centers = list(superpos.values())
        pos = {}
        for center, comm in zip(centers, communities):
            pos.update(nx.spring_layout(nx.subgraph(G, comm), center=center, seed=1430))

        for nodes, clr in zip(communities, ("tab:blue", "tab:orange", "tab:green")):
            nx.draw_networkx_nodes(G, pos=pos, nodelist=nodes, node_color=clr, node_size=100)
        nx.draw_networkx_edges(G, pos=pos)

        plt.tight_layout()
        plt.savefig("examples/drawing/plot_clusters_output.png")
        plt.close()
        print("Plot saved to examples/drawing/plot_clusters_output.png")

        session.commit()


if __name__ == "__main__":
    demo_cluster_layout()
