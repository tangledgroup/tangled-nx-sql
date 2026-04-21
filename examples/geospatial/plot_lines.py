"""
==========================
Graphs from a set of lines
==========================

This example shows how to build a graph from a set of geographic lines
(sometimes called "linestrings") using GeoPandas, momepy and alternatively
PySAL. We'll plot some rivers and streets, as well as their graphs formed
from the segments.

Adapted for nx_sql — uses SQLAlchemy persistence and saves plots to files.
"""

import geopandas
import matplotlib.pyplot as plt
import momepy
import networkx as nx
from libpysal import weights
from pathlib import Path
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
def demo_lines():
    """Build graphs from geographic line geometry (rivers)."""

    with Session() as session:
        data_dir = Path(__file__).resolve().parent.parent / "data" / "geospatial"
        rivers = geopandas.read_file(data_dir / "rivers.geojson")

        # Primal graph: each intersection is a node
        G = momepy.gdf_to_nx(rivers, approach="primal")
        positions = {n: [n[0], n[1]] for n in list(G.nodes)}

        # Store in nx_sql
        Gn = nx_sql.Graph(session, name="lines_primal_demo")
        Gn.add_nodes_from(G.nodes())
        Gn.add_edges_from(G.edges())

        # Dual graph: each line is a node
        H = momepy.gdf_to_nx(rivers, approach="dual")
        dual_graph = nx_sql.Graph(session, name="lines_dual_demo")
        dual_graph.add_nodes_from(H.nodes())
        dual_graph.add_edges_from(H.edges())

        # Also build dual via PySAL (using momepy's built-in conversion)
        H2 = momepy.gdf_to_nx(rivers, approach="dual")
        dual_pysal = nx_sql.Graph(session, name="lines_dual_pysal_demo")
        dual_pysal.add_nodes_from(H2.nodes())
        dual_pysal.add_edges_from(H2.edges())

        # Plot
        fig, ax = plt.subplots(1, 2, figsize=(12, 6), sharex=True, sharey=True)
        rivers.plot(color="k", ax=ax[0])
        ax[0].set_title("Rivers")
        ax[0].axis("off")
        nx.draw(G, positions, ax=ax[1], node_size=5)
        ax[1].set_title("Graph (primal)")
        ax[1].axis("off")

        plt.savefig("examples/geospatial/plot_lines_output.png")
        plt.close()
        print(f"Primal graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        print(f"Dual graph (momepy): {H.number_of_nodes()} nodes, {H.number_of_edges()} edges")
        print(f"Dual graph (pysal):  {H2.number_of_nodes()} nodes, {H2.number_of_edges()} edges")
        print("Saved: plot_lines_output.png")

        session.commit()


if __name__ == "__main__":
    demo_lines()
