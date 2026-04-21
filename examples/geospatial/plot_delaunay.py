"""
======================================
Delaunay graphs from geographic points
======================================

This example shows how to build a delaunay graph (plus its dual,
the set of Voronoi polygons) from a set of points.
For this, we will use the set of cholera cases at the Broad Street Pump,
recorded by John Snow in 1853. The methods shown here can also work
directly with polygonal data using their centroids as representative points.

Adapted for nx_sql — uses SQLAlchemy persistence and saves plots to files.
"""

from libpysal import weights, examples
from libpysal.cg import voronoi_frames
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import geopandas
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
def demo_delaunay():
    """Build a Delaunay graph from geographic points (cholera cases)."""

    with Session() as session:
        data_dir = Path(__file__).resolve().parent.parent / "data" / "geospatial"
        cases = geopandas.read_file(data_dir / "cholera_cases.gpkg")

        coordinates = np.column_stack((cases.geometry.x, cases.geometry.y))

        cells, generators = voronoi_frames(coordinates, clip="convex hull")

        delaunay = weights.Rook.from_dataframe(cells)
        delaunay_graph = delaunay.to_networkx()

        positions = dict(zip(delaunay_graph.nodes, coordinates))

        # Store in nx_sql
        G = nx_sql.Graph(session, name="delaunay_demo")
        G.add_nodes_from(delaunay_graph.nodes())
        G.add_edges_from(delaunay_graph.edges())
        for n in delaunay_graph:
            G.add_node(n, position=positions.get(n))

        # Plot
        fig, ax = plt.subplots(figsize=(8, 6))
        cells.plot(facecolor="lightblue", alpha=0.50, edgecolor="cornsilk",
                   linewidth=2, ax=ax)
        nx.draw(delaunay_graph, positions, ax=ax, node_size=10,
                node_color="red")

        plt.savefig("examples/geospatial/plot_delaunay_output.png")
        plt.close()
        print(f"Delaunay graph: {delaunay_graph.number_of_nodes()} nodes, "
              f"{delaunay_graph.number_of_edges()} edges")
        print("Saved: plot_delaunay_output.png")

        session.commit()


if __name__ == "__main__":
    demo_delaunay()
