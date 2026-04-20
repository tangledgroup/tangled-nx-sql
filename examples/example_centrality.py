"""example_centrality.py - Centrality and importance measures.

Covers: degree_centrality, betweenness_centrality, closeness_centrality,
        eigenvector_centrality, pagerank, katz_centrality, harmonic_centrality.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)


def demo_degree_centrality():
    """Degree centrality - how well-connected each node is."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="degree_cent")

        # Star graph: center node has highest degree
        G.add_edge("hub", "a")
        G.add_edge("hub", "b")
        G.add_edge("hub", "c")
        G.add_edge("hub", "d")
        G.add_edge("e", "f")  # disconnected pair

        dc = nx.degree_centrality(G)
        print("Degree centrality:")
        for node, score in sorted(dc.items(), key=lambda x: -x[1]):
            print(f"  {node}: {score:.4f} (degree={G.degree(node)})")

        session.commit()


def demo_betweenness_centrality():
    """Betweenness centrality - nodes on most shortest paths."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="betweenness_cent")

        # Graph with a bridge
        # A---B---C---D---E
        #       |   |
        #       F---G
        edges = [
            ("A", "B"), ("B", "C"), ("C", "D"), ("D", "E"),
            ("B", "F"), ("F", "G"), ("G", "C"),
        ]
        G.add_edges_from(edges)

        bc = nx.betweenness_centrality(G)
        print("\nBetweenness centrality:")
        for node, score in sorted(bc.items(), key=lambda x: -x[1]):
            print(f"  {node}: {score:.4f}")

        session.commit()


def demo_closeness_centrality():
    """Closeness centrality - how close a node is to all others."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="closeness_cent")

        edges = [
            (1, 2), (2, 3), (3, 4), (4, 5),
            (2, 6), (6, 7),
        ]
        G.add_edges_from(edges)

        cc = nx.closeness_centrality(G)
        print("\nCloseness centrality:")
        for node, score in sorted(cc.items(), key=lambda x: -x[1]):
            print(f"  {node}: {score:.4f}")

        session.commit()


def demo_eigenvector_pagerank():
    """Eigenvector centrality and PageRank."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="eigen_cent")

        # Web-like graph
        edges = [
            ("A", "B"), ("A", "C"),
            ("B", "C"), ("B", "D"),
            ("C", "D"),
            ("D", "E"),
        ]
        G.add_edges_from(edges)

        ec = nx.eigenvector_centrality(G, max_iter=1000)
        print("\nEigenvector centrality:")
        for node, score in sorted(ec.items(), key=lambda x: -x[1]):
            print(f"  {node}: {score:.4f}")

        pr = nx.pagerank(G)
        print("\nPageRank:")
        for node, score in sorted(pr.items(), key=lambda x: -x[1]):
            print(f"  {node}: {score:.4f}")

        session.commit()


def demo_directed_centrality():
    """Centrality on directed graphs."""
    with SessionLocal() as session:
        G = nx_sql.DiGraph(session, name="directed_cent")

        # Influence network
        edges = [
            ("CEO", "CTO"), ("CEO", "CFO"),
            ("CTO", "Eng1"), ("CTO", "Eng2"),
            ("CFO", "Fin1"), ("CFO", "Fin2"),
        ]
        G.add_edges_from(edges)

        print("In-degree (who influences you):")
        for node, deg in sorted(G.in_degree(), key=lambda x: -x[1]):
            print(f"  {node}: {deg}")

        print("\nOut-degree (who you influence):")
        for node, deg in sorted(G.out_degree(), key=lambda x: -x[1]):
            print(f"  {node}: {deg}")

        pr = nx.pagerank(G)
        print("\nPageRank (directed):")
        for node, score in sorted(pr.items(), key=lambda x: -x[1]):
            print(f"  {node}: {score:.4f}")

        session.commit()


if __name__ == "__main__":
    demo_degree_centrality()
    demo_betweenness_centrality()
    demo_closeness_centrality()
    demo_eigenvector_pagerank()
    demo_directed_centrality()
