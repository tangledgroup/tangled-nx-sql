"""Demonstrate Napoleon's Russian Campaign graph with nx_sql.

Mirrors networkx/examples/graph/plot_napoleon_russian_campaign.py but uses
SQLAlchemy persistence. Tests building a directed graph from Minard's
historical data about Napoleon's 1812 campaign.
"""

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


def minard_graph():
    """Build Minard's Napoleon campaign graph from embedded data."""
    data1 = """\
24.0,54.9,340000,A,1
24.5,55.0,340000,A,1
25.5,54.5,340000,A,1
26.0,54.7,320000,A,1
27.0,54.8,300000,A,1
28.0,54.9,280000,A,1
28.5,55.0,240000,A,1
29.0,55.1,210000,A,1
30.0,55.2,180000,A,1
30.3,55.3,175000,A,1
32.0,54.8,145000,A,1
33.2,54.9,140000,A,1
34.4,55.5,127100,A,1
35.5,55.4,100000,A,1
36.0,55.5,100000,A,1
37.6,55.8,100000,A,1
37.7,55.7,100000,R,1
37.5,55.7,98000,R,1
37.0,55.0,97000,R,1
36.8,55.0,96000,R,1
35.4,55.3,87000,R,1
34.3,55.2,55000,R,1
33.3,54.8,37000,R,1
32.0,54.6,24000,R,1
30.4,54.4,20000,R,1
29.2,54.3,20000,R,1
28.5,54.2,20000,R,1
28.3,54.3,20000,R,1
27.5,54.5,20000,R,1
26.8,54.3,12000,R,1
26.4,54.4,14000,R,1
25.0,54.4,8000,R,1
24.4,54.4,4000,R,1
24.2,54.4,4000,R,1
24.1,54.4,4000,R,1"""
    data2 = """\
24.0,55.1,60000,A,2
24.5,55.2,60000,A,2
25.5,54.7,60000,A,2
26.6,55.7,40000,A,2
27.4,55.6,33000,A,2
28.7,55.5,33000,R,2
29.2,54.2,30000,R,2
28.5,54.1,30000,R,2
28.3,54.2,28000,R,2"""
    data3 = """\
24.0,55.2,22000,A,3
24.5,55.3,22000,A,3
24.6,55.8,6000,A,3
24.6,55.8,6000,R,3
24.2,54.4,6000,R,3
24.1,54.4,6000,R,3"""
    cities = """\
24.0,55.0,Kowno
25.3,54.7,Wilna
26.4,54.4,Smorgoni
26.8,54.3,Moiodexno
27.7,55.2,Gloubokoe
27.6,53.9,Minsk
28.5,54.3,Studienska
28.7,55.5,Polotzk
29.2,54.4,Bobr
30.2,55.3,Witebsk
30.4,54.5,Orscha
30.4,53.9,Mohilow
32.0,54.8,Smolensk
33.2,54.9,Dorogobouge
34.3,55.2,Wixma
34.4,55.5,Chjat
36.0,55.5,Mojaisk
37.6,55.8,Moscou
36.6,55.3,Tarantino
36.5,55.0,Malo-Jarosewii"""

    city_coords = {}
    for line in cities.split("\n"):
        x, y, name = line.split(",")
        city_coords[name] = (float(x), float(y))

    graphs = []
    for data in [data1, data2, data3]:
        G = nx.Graph()
        i = 0
        last = None
        for line in data.split("\n"):
            x, y, p, r, n = line.split(",")
            G.add_node(i, x=float(x), y=float(y), population=int(p))
            if last is not None:
                G.add_edge(last, i, route=r, troops=int(p))
            last = i
            i += 1
        graphs.append(G)

    return graphs, city_coords


@print_docstring
def demo_napoleon_campaign():
    """Analyze Napoleon's Russian Campaign using graph data."""

    with Session() as session:
        g_list, city_coords = minard_graph()
        all_G = nx.Graph()

        for idx, G in enumerate(g_list):
            # Map nodes to unique IDs across graphs
            offset = idx * 1000
            for old_node in G.nodes():
                new_node = offset + old_node
                all_G.add_node(new_node, **G.nodes[old_node])
            for u, v, d in G.edges(data=True):
                all_G.add_edge(offset + u, offset + v, **d)

        G = nx_sql.Graph(session, name="napoleon_campaign_demo")
        for node, attrs in all_G.nodes(data=True):
            G.add_node(node, **attrs)
        for u, v, d in all_G.edges(data=True):
            G.add_edge(u, v, **d)

        print("=== Napoleon's Russian Campaign (1812) ===")
        print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

        # Analyze each campaign leg
        print("\n=== Campaign Legs ===")
        for idx, G_leg in enumerate(g_list):
            route = "A" if idx == 0 else ("R" if idx == 1 else "A/R")
            nodes_list = list(G_leg.nodes())
            start_pop = G_leg.nodes[nodes_list[0]]["population"]
            end_pop = G_leg.nodes[nodes_list[-1]]["population"]
            print(f"\nLeg {idx + 1} ({route}):")
            print(f"  Nodes: {G_leg.number_of_nodes()}, Edges: {G_leg.number_of_edges()}")
            print(f"  Start population: {start_pop:,}")
            print(f"  End population: {end_pop:,}")
            if start_pop > 0:
                survival = end_pop / start_pop * 100
                print(f"  Survival rate: {survival:.1f}%")

        # Show city coordinates
        print("\n=== Cities ===")
        for name, (x, y) in sorted(city_coords.items()):
            print(f"  ({x:5.1f}, {y:5.1f}): {name}")

        # Find path from start to Moscow
        moscow_nodes = [n for n, d in G.nodes(data=True)
                       if d.get("x", 0) >= 37.0 and d.get("y", 0) >= 55.0]
        start_nodes = [n for n, d in G.nodes(data=True)
                      if d.get("x", 0) <= 24.5 and d.get("y", 0) >= 54.9]

        if moscow_nodes and start_nodes:
            try:
                path = nx.shortest_path(G, start_nodes[0], moscow_nodes[0])
                print(f"\n=== Path to Moscow ===")
                print(f"Path length: {len(path)} nodes")
                for node in path:
                    x = G.nodes[node].get("x", "?")
                    y = G.nodes[node].get("y", "?")
                    pop = G.nodes[node].get("population", "?")
                    print(f"  Node {node}: ({x:.1f}, {y:.1f}) troops={pop:,}")
            except nx.NetworkXNoPath:
                print("\nNo direct path found from start to Moscow in combined graph")

        session.commit()


if __name__ == "__main__":
    demo_napoleon_campaign()
