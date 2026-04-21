"""
========================
OpenStreetMap with OSMnx
========================

This example shows how to use OSMnx to download and model a street network
from OpenStreetMap, visualize centrality, then save the graph as a GeoPackage,
or GraphML file.

Adapted for nx_sql — uses SQLAlchemy persistence, saves outputs to files
instead of displaying interactively.
"""

import networkx as nx
import osmnx as ox
import matplotlib.pyplot as plt
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
def demo_osmnx():
    """Download a street network from OSM, compute centrality, save results."""

    with Session() as session:
        ox.settings.use_cache = True

        # Download street network data from OSM and construct a MultiDiGraph
        print("Downloading street network from OpenStreetMap (San Francisco)...")
        G = ox.graph.graph_from_point((37.79, -122.41), dist=750, network_type="drive")
        print(f"Downloaded graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

        # Impute edge (driving) speeds and calculate edge travel times
        G = ox.routing.add_edge_speeds(G)
        G = ox.routing.add_edge_travel_times(G)

        # Convert MultiDiGraph to GeoDataFrames and back
        gdf_nodes, gdf_edges = ox.convert.graph_to_gdfs(G)
        G = ox.convert.graph_from_gdfs(gdf_nodes, gdf_edges, graph_attrs=G.graph)

        # Convert MultiDiGraph to DiGraph for centrality computation
        D = ox.convert.to_digraph(G, weight="travel_time")

        # Calculate node betweenness centrality, weighted by travel time
        bc = nx.betweenness_centrality(D, weight="travel_time", normalized=True)
        nx.set_node_attributes(G, values=bc, name="bc")

        # Store in nx_sql
        G_nx = nx.Graph()  # Convert to undirected for nx_sql storage
        # Strip shapely geometries (not JSON serializable) before storing
        for n, d in G.nodes(data=True):
            clean_d = {k: v for k, v in d.items()
                       if not hasattr(v, '__geo_interface__')}
            G_nx.add_node(n, **clean_d)
        for u, v, data in G.edges(data=True):
            # Keep minimum travel_time if multiple edges exist
            clean_d = {k: v for k, v in data.items()
                       if not hasattr(v, '__geo_interface__')}
            G_nx.add_edge(u, v, **clean_d)

        Stn = nx_sql.Graph(session, name="osmnx_sf_demo")
        Stn.add_nodes_from(G_nx.nodes())
        for u, v, data in G_nx.edges(data=True):
            Stn.add_edge(u, v, **data)

        # Plot the graph, coloring nodes by betweenness centrality
        nc = ox.plot.get_node_colors_by_attr(G, "bc", cmap="plasma")
        fig, ax = ox.plot.plot_graph(
            G, bgcolor="k", node_color=nc, node_size=50,
            edge_linewidth=2, edge_color="#333333", show=False,
        )
        plt.savefig("examples/geospatial/plot_osmnx_output.png")
        plt.close()

        # Save graph as geopackage or graphml file
        output_dir = Path(__file__).resolve().parent.parent / "data" / "geospatial"
        ox.io.save_graph_geopackage(G, filepath=output_dir / "sf_street_network.gpkg")
        ox.io.save_graphml(G, filepath=output_dir / "sf_street_network.graphml")

        print(f"Saved: plot_osmnx_output.png, sf_street_network.gpkg, sf_street_network.graphml")

        session.commit()


if __name__ == "__main__":
    demo_osmnx()
