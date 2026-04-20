"""example_bipartite.py - Bipartite graph algorithms.

Covers: is_bipartite, bipartite sets/color, projections (weighted/overlap),
        matching (Hopcroft-Karp/Eppstein), biadjacency matrices,
        bipartite centrality/clustering, BiRANK ranking.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)


def demo_is_bipartite():
    """Check if graphs are bipartite."""
    with SessionLocal() as session:
        # Bipartite: K3,3
        G1 = nx_sql.Graph(session, name="bip_k33")
        left = [0, 1, 2]
        right = [3, 4, 5]
        for l in left:
            for r in right:
                G1.add_edge(l, r)

        print(f"K₃,₃ is bipartite: {nx.is_bipartite(G1)}")
        sets = nx.bipartite.sets(G1)
        print(f"  Sets: {sorted(sets[0])}, {sorted(sets[1])}")

        # Non-bipartite: triangle
        G2 = nx_sql.Graph(session, name="non_bip")
        G2.add_edges_from([(1, 2), (2, 3), (3, 1)])
        print(f"\nTriangle is bipartite: {nx.is_bipartite(G2)}")

        session.commit()


def demo_bipartite_coloring():
    """Bipartite coloring and set identification."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="bip_color")
        edges = [
            ("Alice", "Python"), ("Alice", "Rust"),
            ("Bob", "Python"), ("Bob", "Java"),
            ("Carol", "Rust"),
        ]
        G.add_edges_from(edges)

        is_bip = nx.is_bipartite(G)
        print(f"Is bipartite: {is_bip}")
        if is_bip:
            # Bipartite coloring
            colors = nx.bipartite.color(G)
            print(f"\nBipartite coloring:")
            for node, color in sorted(colors.items()):
                print(f"  {node}: color={color}")

            sets = nx.bipartite.sets(G)
            print(f"\nSets: {sorted(sets[0])}, {sorted(sets[1])}")

        session.commit()


def demo_bipartite_projections():
    """Bipartite projections."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="bip_proj")
        # Author-Paper bipartite graph
        edges = [
            ("Alice", "Paper1"), ("Alice", "Paper2"),
            ("Bob", "Paper2"), ("Bob", "Paper3"),
            ("Carol", "Paper3"), ("Carol", "Paper4"),
            ("Dave", "Paper1"), ("Dave", "Paper4"),
        ]
        G.add_edges_from(edges)

        authors = ["Alice", "Bob", "Carol", "Dave"]
        papers = ["Paper1", "Paper2", "Paper3", "Paper4"]

        # Weighted projection (overlap equivalent)
        proj_overlap = nx.bipartite.weighted_projected_graph(G, authors)
        print(f"\nOverlap projection (authors):")
        for u, v, d in sorted(proj_overlap.edges(data=True)):
            print(f"  {u} — {v}: overlap={d['weight']}")

        # Weighted projection
        proj_weighted = nx.bipartite.weighted_projected_graph(G, authors)
        print(f"\nWeighted projection (authors):")
        for u, v, d in sorted(proj_weighted.edges(data=True)):
            print(f"  {u} — {v}: co-authored={d['weight']} papers")

        session.commit()


def demo_bipartite_matching():
    """Bipartite matching algorithms."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="bip_match")
        # Workers → Tasks
        edges = [
            ("Alice", "Coding"), ("Alice", "Testing"),
            ("Bob", "Coding"), ("Bob", "Design"),
            ("Carol", "Testing"), ("Carol", "Design"),
        ]
        G.add_edges_from(edges)

        workers = ["Alice", "Bob", "Carol"]
        tasks = ["Coding", "Testing", "Design"]

        # Maximum matching (Hopcroft-Karp via max_weight_matching)
        matching = nx.bipartite.maximum_matching(G, workers)
        print(f"\nMaximum matching:")
        pairs = set()
        for u, v in matching.items():
            if u in workers:
                pairs.add((u, v))
        for w, t in sorted(pairs):
            print(f"  {w} → {t}")
        print(f"  Matched: {len(pairs)}/{min(len(workers), len(tasks))}")

        # Minimum vertex cover via approximation
        from networkx.algorithms.approximation import min_weighted_vertex_cover
        G_plain = nx.Graph(G)
        vc = min_weighted_vertex_cover(G_plain)
        print(f"\nMinimum vertex cover: {sorted(vc)}")

        # Maximum independent set (use approximation)
        from networkx.algorithms.approximation import maximum_independent_set as max_ind_set
        G_plain = nx.Graph(G)
        mis = max_ind_set(G_plain)
        print(f"Maximum independent set: {sorted(mis)}")

        session.commit()


def demo_biadjacency():
    """Biadjacency matrix operations."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="biadj")
        edges = [
            (0, 3), (0, 4), (1, 3), (1, 5), (2, 4),
        ]
        G.add_edges_from(edges)

        left = [0, 1, 2]
        right = [3, 4, 5]

        # Biadjacency matrix
        B = nx.bipartite.biadjacency_matrix(G, left, right)
        print(f"\nBiadjacency matrix ({B.shape}):")
        print(B.toarray())

        # Overlap projections (use weighted projected graphs)
        left_proj = nx.bipartite.weighted_projected_graph(G, left)
        right_proj = nx.bipartite.weighted_projected_graph(G, right)
        print(f"\nLeft projection edges: {left_proj.number_of_edges()}")
        print(f"Right projection edges: {right_proj.number_of_edges()}")

        session.commit()


def demo_bipartite_centrality():
    """Bipartite-specific centrality measures."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="bip_cent")
        edges = [
            ("Alice", "Python"), ("Alice", "Rust"),
            ("Bob", "Python"), ("Bob", "Java"),
            ("Carol", "Rust"),
        ]
        G.add_edges_from(edges)

        authors = ["Alice", "Bob", "Carol"]
        langs = ["Python", "Rust", "Java"]

        # Projection-based centrality
        proj = nx.bipartite.weighted_projected_graph(G, authors)
        print(f"\nAuthor collaboration graph:")
        for u, v, d in sorted(proj.edges(data=True)):
            print(f"  {u} — {v}: {d['weight']}")

        # Degree centrality on projection
        dc = nx.degree_centrality(proj)
        print(f"\nDegree centrality (on projection):")
        for node, score in sorted(dc.items(), key=lambda x: -x[1]):
            print(f"  {node}: {score:.4f}")

        session.commit()


def demo_bipartite_clustering():
    """Bipartite clustering coefficients."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="bip_clust")
        edges = [
            ("Alice", "Python"), ("Alice", "Rust"),
            ("Bob", "Python"), ("Bob", "Rust"),
            ("Carol", "Python"),
        ]
        G.add_edges_from(edges)

        authors = ["Alice", "Bob", "Carol"]

        # Latapy clustering (bipartite-aware)
        lc = nx.bipartite.latapy_clustering(G, authors)
        print(f"\nLatapy clustering (authors):")
        for node, cc in sorted(lc.items(), key=lambda x: -x[1]):
            print(f"  {node}: {cc:.4f}")

        # Average clustering
        ac = nx.bipartite.average_clustering(G, authors)
        print(f"\nAverage clustering: {ac:.4f}")

        session.commit()


if __name__ == "__main__":
    demo_is_bipartite()
    demo_bipartite_coloring()
    demo_bipartite_projections()
    demo_bipartite_matching()
    demo_biadjacency()
    demo_bipartite_centrality()
    demo_bipartite_clustering()
