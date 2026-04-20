"""Demonstrate graph connectivity with nx_sql.

Tests connected components, articulation points, bridges, and biconnected components.
Shows how to identify critical nodes and edges in a network.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def demo_connectivity():
    """Test connectivity properties on a graph."""

    with Session() as session:
        G_nx = nx.karate_club_graph()
        G = nx_sql.Graph(session, name="connectivity_demo")
        G.add_nodes_from(G_nx.nodes())
        G.add_edges_from(G_nx.edges())

        print(f"=== Graph Connectivity ===")
        print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

        # Check connectivity
        print(f"Is connected: {nx.is_connected(G)}")
        print(f"Number of connected components: {nx.number_connected_components(G)}")

        # Connected components
        components = list(nx.connected_components(G))
        print(f"Components: {len(components)} component(s)")
        for i, comp in enumerate(sorted(components, key=len, reverse=True)):
            print(f"  Component {i+1}: {len(comp)} nodes")

        # Articulation points (critical nodes)
        articulation_points = list(nx.articulation_points(G))
        print(f"\nArticulation points ({len(articulation_points)}): {sorted(articulation_points)}")

        # Bridges (critical edges)
        bridges_list = list(nx.bridges(G))
        print(f"Bridges ({len(bridges_list)}): {bridges_list}")

        # Biconnected components
        biconnected = list(nx.biconnected_components(G))
        print(f"\nBiconnected components: {len(biconnected)}")
        for i, comp in enumerate(sorted(biconnected, key=len, reverse=True)[:5]):
            print(f"  Component {i+1}: {sorted(comp)} ({len(comp)} nodes)")

        # Test on a disconnected graph
        print(f"\n=== Disconnected Graph ===")
        G_disc = nx_sql.Graph(session, name="connectivity_disconnected")
        G_disc.add_edge(0, 1)
        G_disc.add_edge(1, 2)
        G_disc.add_edge(5, 6)
        G_disc.add_edge(6, 7)

        print(f"Is connected: {nx.is_connected(G_disc)}")
        print(f"Components: {list(nx.connected_components(G_disc))}")

        session.commit()


if __name__ == "__main__":
    demo_connectivity()
