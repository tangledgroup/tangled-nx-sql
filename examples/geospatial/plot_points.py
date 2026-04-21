"""
=============================
Graphs from geographic points
=============================

This example shows how to build a graph from a set of points
using PySAL and geopandas. In this example, we'll use the famous
set of cholera cases at the Broad Street Pump, recorded by John Snow in 1853.
The methods shown here can also work directly with polygonal data using their
centroids as representative points.

Adapted for nx_sql — uses SQLAlchemy persistence and saves plots to files.
"""

from libpysal import weights
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
def demo_points():
    """Build KNN and distance-band graphs from geographic points."""

    with Session() as session:
        data_dir = Path(__file__).resolve().parent.parent / "data" / "geospatial"
        cases = geopandas.read_file(data_dir / "cholera_cases.gpkg")

        coordinates = np.column_stack((cases.geometry.x, cases.geometry.y))

        # 3-nearest neighbor graph
        knn3 = weights.KNN.from_dataframe(cases, k=3)
        knn_graph = knn3.to_networkx()

        # 50-meter distance band graph
        dist = weights.DistanceBand.from_array(coordinates, threshold=50)
        dist_graph = dist.to_networkx()

        positions = dict(zip(knn_graph.nodes, coordinates))

        # Store in nx_sql
        G_knn = nx_sql.Graph(session, name="points_knn_demo")
        G_knn.add_nodes_from(knn_graph.nodes())
        G_knn.add_edges_from(knn_graph.edges())

        G_dist = nx_sql.Graph(session, name="points_dist_demo")
        G_dist.add_nodes_from(dist_graph.nodes())
        G_dist.add_edges_from(dist_graph.edges())

        # Plot
        fig, ax = plt.subplots(1, 2, figsize=(8, 4))
        for i, (G_plot, title) in enumerate(zip([knn_graph, dist_graph],
                                                  ["KNN-3", "50-meter Distance Band"])):
            cases.plot(marker=".", color="orangered", ax=ax[i])
            ax[i].set_title(title)
            ax[i].axis("off")
            nx.draw(G_plot, positions, ax=ax[i], node_size=5, node_color="b")

        plt.savefig("examples/geospatial/plot_points_output.png")
        plt.close()
        print(f"KNN-3 graph: {knn_graph.number_of_nodes()} nodes, "
              f"{knn_graph.number_of_edges()} edges")
        print(f"Distance-band graph: {dist_graph.number_of_nodes()} nodes, "
              f"{dist_graph.number_of_edges()} edges")
        print("Saved: plot_points_output.png")

        session.commit()


if __name__ == "__main__":
    demo_points()
