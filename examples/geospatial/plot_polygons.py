"""
====================
Graphs from Polygons
====================

This example shows how to build a graph from a set of polygons
using PySAL and geopandas. We'll focus on the Queen contiguity
graph, but constructors are also provided for Rook contiguity,
as well as other kinds of graphs from the polygon centroids.

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
def demo_polygons():
    """Build a Queen contiguity graph from polygon data (European regions)."""

    with Session() as session:
        data_dir = Path(__file__).resolve().parent.parent / "data" / "geospatial"
        european_regions = geopandas.read_file(data_dir / "nuts1.geojson")

        centroids = np.column_stack(
            (european_regions.centroid.x, european_regions.centroid.y)
        )

        # Queen adjacency graph (polygons sharing a point or edge)
        queen = weights.Queen.from_dataframe(european_regions)
        graph = queen.to_networkx()

        positions = dict(zip(graph.nodes, centroids))

        # Store in nx_sql
        G = nx_sql.Graph(session, name="polygons_queen_demo")
        G.add_nodes_from(graph.nodes())
        G.add_edges_from(graph.edges())
        for n in graph:
            G.add_node(n, centroid=positions.get(n))

        # Plot
        ax = european_regions.plot(linewidth=1, edgecolor="grey",
                                    facecolor="lightblue")
        ax.axis([-12, 45, 33, 66])
        ax.axis("off")
        nx.draw(graph, positions, ax=ax, node_size=5, node_color="r")

        plt.savefig("examples/geospatial/plot_polygons_output.png")
        plt.close()
        print(f"Queen contiguity graph: {graph.number_of_nodes()} nodes, "
              f"{graph.number_of_edges()} edges")
        print("Saved: plot_polygons_output.png")

        session.commit()


if __name__ == "__main__":
    demo_polygons()
