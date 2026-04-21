"""
======
igraph
======

igraph (https://igraph.org/) is a popular network analysis package that
provides (among many other things) functions to convert to/from NetworkX.

Adapted for nx_sql — uses SQLAlchemy persistence, saves plots as files.
"""

import matplotlib.pyplot as plt
import networkx as nx
import igraph as ig
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
def demo_igraph():
    """Convert between NetworkX and igraph, compare layouts."""

    with Session() as session:
        # NetworkX to igraph
        G_nx = nx.dense_gnm_random_graph(30, 40, seed=42)
        G = nx_sql.Graph(session, name="igraph_demo")
        G.add_nodes_from(G_nx.nodes())
        G.add_edges_from(G_nx.edges())

        # Largest connected component
        components = nx.connected_components(G)
        largest_component = max(components, key=len)
        H = G.subgraph(largest_component)

        # Convert to igraph
        h = ig.Graph.from_networkx(H)

        print(f"igraph graph: {h.vcount()} vertices, {h.ecount()} edges")

        # Plot both with matplotlib
        fig, (ax0, ax1) = plt.subplots(nrows=1, ncols=2, figsize=(12, 6))

        # NetworkX draw
        ax0.set_title("Plot with NetworkX draw")
        nx.draw_kamada_kawai(H, node_size=50, ax=ax0)

        # igraph draw
        ax1.set_title("Plot with igraph plot")
        layout = h.layout_kamada_kawai()
        ig.plot(h, layout=layout, target=ax1)
        plt.axis("off")

        plt.savefig("examples/external/plot_igraph_output.png")
        plt.close()
        print("Plot saved to examples/external/plot_igraph_output.png")

        # igraph to NetworkX
        g = ig.Graph.GRG(30, 0.2)
        G2 = g.to_networkx()
        H2 = nx_sql.Graph(session, name="igraph_to_nx_demo")
        H2.add_nodes_from(G2.nodes())
        H2.add_edges_from(G2.edges())
        print(f"igraph GRG -> NetworkX: {H2.number_of_nodes()} nodes, {H2.number_of_edges()} edges")

        session.commit()


if __name__ == "__main__":
    demo_igraph()
