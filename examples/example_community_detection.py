"""example_community_detection.py - Community detection and clustering.

Covers: connected_components, clustering_coefficient, k_core,
        triangle counting, assortativity.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)


def demo_connected_components():
    """Find connected components in an undirected graph."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="components")

        # Three separate clusters
        # Cluster 1: triangle
        G.add_edge("A", "B")
        G.add_edge("B", "C")
        G.add_edge("C", "A")

        # Cluster 2: line
        G.add_edge("D", "E")
        G.add_edge("E", "F")

        # Isolated node
        G.add_node("G")

        components = list(nx.connected_components(G))
        print(f"Connected components ({len(components)}):")
        for i, comp in enumerate(components, 1):
            print(f"  Component {i}: {sorted(comp)}")

        print(f"Is connected: {nx.is_connected(G)}")
        print(f"Number of components: {nx.number_connected_components(G)}")

        session.commit()


def demo_clustering():
    """Clustering coefficient - how tightly knit are neighbors."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="clustering")

        # Triangle + extensions
        G.add_edge("A", "B")
        G.add_edge("B", "C")
        G.add_edge("C", "A")
        G.add_edge("A", "D")
        G.add_edge("B", "E")

        local_cc = nx.clustering(G)
        print("\nLocal clustering coefficients:")
        for node, cc in sorted(local_cc.items(), key=lambda x: -x[1]):
            print(f"  {node}: {cc:.4f}")

        print(f"\nAverage clustering: {nx.average_clustering(G):.4f}")
        print(f"Transitivity (global): {nx.transitivity(G):.4f}")

        session.commit()


def demo_triangles():
    """Count triangles through each node."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="triangles")

        edges = [
            ("A", "B"), ("B", "C"), ("C", "A"),  # triangle ABC
            ("C", "D"), ("D", "E"), ("E", "F"),   # line CDEF
            ("A", "D"),  # connects triangle to line
        ]
        G.add_edges_from(edges)

        triangles = nx.triangles(G)
        print("\nTriangle count per node:")
        for node, count in sorted(triangles.items(), key=lambda x: -x[1]):
            if count > 0:
                print(f"  {node}: {count} triangles")

        # Find all triangles
        tri_list = list(nx.enumerate_all_cliques(G))
        cliques_of_3 = [c for c in tri_list if len(c) == 3]
        print(f"\nAll triangles (cliques of 3):")
        for clique in cliques_of_3:
            print(f"  {sorted(clique)}")

        session.commit()


def demo_k_core():
    """k-core decomposition - find dense subgraphs."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="kcore")

        # Graph with varying density
        edges = [
            # Dense core (k=3)
            ("A", "B"), ("B", "C"), ("C", "D"), ("D", "A"),
            ("A", "C"), ("B", "D"),
            # Medium density (k=2)
            ("A", "E"), ("E", "F"),
            # Tail
            ("F", "G"),
        ]
        G.add_edges_from(edges)

        for k in range(5):
            core = nx.k_core(G, k=k)
            if core.number_of_nodes() > 0:
                print(f"  {k}-core: {sorted(core.nodes())} ({core.number_of_edges()} edges)")

        # Show each node's core number
        cn = nx.core_number(G)
        print("\nCore number per node:")
        for node, k in sorted(cn.items(), key=lambda x: -x[1]):
            print(f"  {node}: k={k}")

        session.commit()


def demo_assortativity():
    """Assortativity - do similar-degree nodes connect to each other?"""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="assort")

        # Preferential attachment style (scale-free-like)
        # Hub connected to many leaves
        G.add_edge("hub", "leaf1")
        G.add_edge("hub", "leaf2")
        G.add_edge("hub", "leaf3")
        G.add_edge("hub", "leaf4")
        # Leaf connected to another leaf
        G.add_edge("leaf1", "leaf5")

        assort = nx.degree_assortativity_coefficient(G)
        print(f"\nDegree assortativity: {assort:.4f}")
        print("(Negative = dissimilar degrees connect, positive = similar)")

        session.commit()


if __name__ == "__main__":
    demo_connected_components()
    demo_clustering()
    demo_triangles()
    demo_k_core()
    demo_assortativity()
