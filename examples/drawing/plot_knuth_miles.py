"""
===========
Knuth Miles
===========

`miles_graph()` returns an undirected graph over 128 US cities. The
cities each have location and population data.  The edges are labeled with the
distance between the two cities.

This example is described in Section 1.1 of

    Donald E. Knuth, "The Stanford GraphBase: A Platform for Combinatorial
    Computing", ACM Press, New York, 1993.
    http://www-cs-faculty.stanford.edu/~knuth/sgb.html

The data file can be found at:

- https://github.com/networkx/networkx/blob/main/examples/drawing/knuth_miles.txt.gz

Adapted for nx_sql — uses SQLAlchemy persistence and saves plot to file.
"""

import gzip
import re
from pathlib import Path

import numpy as np
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


def miles_graph():
    """Return the cites example graph in miles_dat.txt
    from the Stanford GraphBase.
    """
    data_file = Path(__file__).resolve().parent.parent / "data" / "knuth_miles.txt.gz"
    fh = gzip.open(data_file, "r")

    G = nx.Graph()
    G.position = {}
    G.population = {}

    cities = []
    for line in fh.readlines():
        line = line.decode()
        if line.startswith("*"):  # skip comments
            continue

        numfind = re.compile(r"^\d+")

        if numfind.match(line):  # this line is distances
            dist = line.split()
            for d in dist:
                G.add_edge(city, cities[i], weight=int(d))
                i = i + 1
        else:  # this line is a city, position, population
            i = 1
            (city, coordpop) = line.split("[")
            cities.insert(0, city)
            (coord, pop) = coordpop.split("]")
            (y, x) = coord.split(",")

            G.add_node(city)
            # assign position - Convert string to lat/long
            G.position[city] = (-float(x) / 100, float(y) / 100)
            G.population[city] = float(pop) / 1000
    return G


@print_docstring
def demo_knuth_miles():
    """Draw a graph of US cities with distances as edge weights."""

    with Session() as session:
        G = miles_graph()
        print(f"Loaded knuth_miles.txt.gz containing {G.number_of_nodes()} cities.")
        print(G)

        # Make new graph of cites, edge if less than 300 miles between them
        H_nx = nx.Graph()
        for v in G:
            H_nx.add_node(v)
        for u, v, d in G.edges(data=True):
            if d["weight"] < 300:
                H_nx.add_edge(u, v, weight=d["weight"])

        # Store in nx_sql
        H = nx_sql.Graph(session, name="knuth_miles_demo")
        H.add_nodes_from(H_nx.nodes())
        for u, v, data in H_nx.edges(data=True):
            H.add_edge(u, v, **data)

        # Copy position and population attributes
        for city, pos in G.position.items():
            if city in H:
                H.add_node(city, position=pos)
        for city, pop in G.population.items():
            if city in H:
                H.add_node(city, population=pop)

        # draw with matplotlib/pylab
        fig = plt.figure(figsize=(8, 6))

        # nodes colored by degree sized by population
        node_color = [float(H.degree(v)) for v in H]

        # Use cartopy to provide a backdrop for the visualization
        try:
            import cartopy.crs as ccrs
            import cartopy.io.shapereader as shpreader
            use_cartopy = True
        except ImportError:
            use_cartopy = False

        # Use cartopy to provide a backdrop for the visualization
        try:
            import cartopy.crs as ccrs
            import cartopy.io.shapereader as shpreader

            ax = fig.add_axes([0, 0, 1, 1], projection=ccrs.LambertConformal(), frameon=False)
            ax.set_extent([-125, -66.5, 20, 50], ccrs.Geodetic())
            # Add map of countries & US states as a backdrop
            for shapename in ("admin_1_states_provinces_lakes_shp", "admin_0_countries"):
                shp = shpreader.natural_earth(
                    resolution="110m", category="cultural", name=shapename
                )
                ax.add_geometries(
                    shpreader.Reader(shp).geometries(),
                    ccrs.PlateCarree(),
                    facecolor="none",
                    edgecolor="k",
                )
            # NOTE: When using cartopy, use matplotlib directly rather than nx.draw
            ax.scatter(
                *np.array(list(G.position.values())).T,
                s=[G.population[v] for v in H],
                c=node_color,
                transform=ccrs.PlateCarree(),
                zorder=100,  # Ensure nodes lie on top of edges/state lines
            )
            # Plot edges between the cities
            for edge in H.edges():
                edge_coords = np.array([G.position[v] for v in edge])
                ax.plot(
                    edge_coords[:, 0],
                    edge_coords[:, 1],
                    transform=ccrs.PlateCarree(),
                    linewidth=0.75,
                    color="k",
                )
        except Exception:
            # If cartopy is unavailable or network fails, the backdrop
            # for the plot will be blank; though you should still be able
            # to discern the general shape of the US from graph nodes and edges!
            nx.draw(
                H,
                G.position,
                node_size=[G.population[v] for v in H],
                node_color=node_color,
                with_labels=False,
            )

        plt.savefig("examples/drawing/plot_knuth_miles_output.png")
        plt.close()
        print(f"Saved plot to examples/drawing/plot_knuth_miles_output.png")

        session.commit()


if __name__ == "__main__":
    demo_knuth_miles()
