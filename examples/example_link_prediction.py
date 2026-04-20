"""example_link_prediction.py - Link prediction and analysis.

Covers: Jaccard coefficient, Adamic-Adar index, resource allocation,
        preferential attachment, common neighbors, HITS, PageRank google_matrix,
        common_neighbor_centrality.
"""

import networkx as nx
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)


def demo_jaccard():
    """Jaccard coefficient for link prediction."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="jaccard")
        G.add_edges_from([
            ("A", "B"), ("A", "C"),
            ("B", "C"), ("B", "D"),
            ("C", "D"),
            ("E", "F"),
        ])

        # Jaccard coefficient between unconnected nodes
        pairs = [("A", "D"), ("A", "E"), ("B", "E")]
        print("Jaccard coefficient:")
        for u, v in pairs:
            jc = list(nx.jaccard_coefficient(G, [(u, v)]))
            print(f"  ({u}, {v}): {jc[0][2]:.4f}")

        session.commit()


def demo_adamic_adar():
    """Adamic-Adar index for link prediction."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="adamic_adar")
        G.add_edges_from([
            ("A", "B"), ("A", "C"),
            ("B", "C"), ("B", "D"),
            ("C", "D"), ("C", "E"),
        ])

        pairs = [("A", "D"), ("A", "E"), ("B", "E")]
        print("\nAdamic-Adar index:")
        for u, v in pairs:
            aa = list(nx.adamic_adar_index(G, [(u, v)]))
            print(f"  ({u}, {v}): {aa[0][2]:.4f}")

        session.commit()


def demo_resource_allocation():
    """Resource allocation index."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="ra_index")
        G.add_edges_from([
            ("A", "B"), ("A", "C"),
            ("B", "C"), ("B", "D"),
            ("C", "D"),
        ])

        pairs = [("A", "D"), ("A", "B")]
        print("\nResource allocation index:")
        for u, v in pairs:
            ra = list(nx.resource_allocation_index(G, [(u, v)]))
            print(f"  ({u}, {v}): {ra[0][2]:.4f}")

        session.commit()


def demo_preferential_attachment():
    """Preferential attachment score."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="pref_attach")
        # Scale-free-like graph
        G.add_edges_from([
            ("hub", "a"), ("hub", "b"), ("hub", "c"),
            ("hub", "d"), ("hub", "e"),
            ("a", "f"), ("b", "g"),
        ])

        pairs = [("hub", "a"), ("a", "b")]
        print("\nPreferential attachment score:")
        for u, v in pairs:
            pa = list(nx.preferential_attachment(G, [(u, v)]))
            print(f"  ({u}, {v}): {pa[0][2]:.4f}")

        session.commit()


def demo_common_neighbors():
    """Common neighbor-based link prediction."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="common_nb")
        G.add_edges_from([
            ("A", "B"), ("A", "C"),
            ("B", "C"), ("B", "D"),
            ("C", "D"),
        ])

        pairs = [("A", "D"), ("A", "B")]
        print("\nCommon neighbors:")
        for u, v in pairs:
            cn = list(nx.common_neighbors(G, u, v))
            print(f"  Common({u}, {v}): {cn}")

        # Jaccard as Sørensen proxy
        print("\nJaccard (Sørensen proxy):")
        for u, v in pairs:
            jc = list(nx.jaccard_coefficient(G, [(u, v)]))
            print(f"  ({u}, {v}): {jc[0][2]:.4f}")

        session.commit()


def demo_hits():
    """HITS (Hyperlink-Induced Topic Search) algorithm."""
    with SessionLocal() as session:
        G = nx_sql.DiGraph(session, name="hits")
        # Web-like graph
        edges = [
            ("A", "B"), ("A", "C"),
            ("B", "C"), ("B", "D"),
            ("C", "D"),
            ("D", "E"),
        ]
        G.add_edges_from(edges)

        hubs, authorities = nx.hits(G, max_iter=1000)
        print("\nHITS - Hub scores:")
        for node, score in sorted(hubs.items(), key=lambda x: -x[1]):
            print(f"  {node}: hub={score:.4f}, auth={authorities[node]:.4f}")

        session.commit()


def demo_pagerank_google_matrix():
    """PageRank and Google matrix."""
    with SessionLocal() as session:
        G = nx_sql.DiGraph(session, name="pr_google")
        edges = [
            ("A", "B"), ("A", "C"),
            ("B", "C"), ("B", "D"),
            ("C", "D"),
            ("D", "A"),
        ]
        G.add_edges_from(edges)

        pr = nx.pagerank(G, alpha=0.85)
        print("\nPageRank scores:")
        for node, score in sorted(pr.items(), key=lambda x: -x[1]):
            print(f"  {node}: {score:.4f}")

        # Personalized PageRank
        pp = nx.pagerank(G, personalization={"A": 1.0, "B": 0.25, "C": 0.25, "D": 0.25})
        print("\nPersonalized PageRank (boost A):")
        for node, score in sorted(pp.items(), key=lambda x: -x[1]):
            print(f"  {node}: {score:.4f}")

        # Google matrix
        google_mat = nx.google_matrix(G)
        print(f"\nGoogle matrix shape: {google_mat.shape}")
        row_sums = google_mat.sum(axis=1)
        if hasattr(row_sums, 'A1'):
            print(f"Row sums (should be 1): {row_sums.A1}")
        else:
            print(f"Row sums (should be ~1): {np.asarray(row_sums).flatten()}")

        session.commit()


def demo_ra_index():
    """RA (Resource Allocation) index."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="ra_full")
        G.add_edges_from([
            ("A", "B"), ("A", "C"),
            ("B", "C"), ("B", "D"),
            ("C", "D"),
        ])

        # RA index (alias for resource_allocation_index)
        pairs = [("A", "D")]
        print("\nRA index:")
        for u, v in pairs:
            ra = list(nx.resource_allocation_index(G, [(u, v)]))
            print(f"  ({u}, {v}): {ra[0][2]:.4f}")

        session.commit()


if __name__ == "__main__":
    demo_jaccard()
    demo_adamic_adar()
    demo_resource_allocation()
    demo_preferential_attachment()
    demo_common_neighbors()
    demo_hits()
    demo_pagerank_google_matrix()
    demo_ra_index()
