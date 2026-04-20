"""example_advanced2.py - Advanced algorithms: polynomials, perfect graphs,
                          approximation, distance-regular, regular graphs.

Covers: chromatic polynomial, Tutte polynomial, is_perfect_graph,
        approximation algorithms (max_clique, vertex_cover, TSP),
        distance_regular, is_k_regular, k_factor, etc.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)


def demo_chromatic_polynomial():
    """Chromatic polynomial evaluation."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="chrom_poly")
        G.add_edges_from([(1, 2), (2, 3), (3, 1)])  # triangle

        try:
            cp = nx.chromatic_polynomial(G)
            print(f"Chromatic polynomial of K₃: {cp}")
            # Evaluate at k=4
            result = cp.subs({nx.get_symbol(): 4})
            print(f"  P(4) = {result} (ways to color with 4 colors)")
        except Exception as e:
            print(f"\nChromatic polynomial: {e}")

        session.commit()


def demo_tutte_polynomial():
    """Tutte polynomial computation."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="tutte")
        G.add_edges_from([(1, 2), (2, 3)])  # path

        try:
            tp = nx.tutte_polynomial(G)
            print(f"\nTutte polynomial of P₃: {tp}")
        except Exception as e:
            print(f"\nTutte polynomial: {e}")

        session.commit()


def demo_perfect_graphs():
    """Perfect graph detection."""
    with SessionLocal() as session:
        # Complete graphs are perfect
        G1 = nx.complete_graph(4)
        is_perfect = nx.is_perfect_graph(G1)
        print(f"K₄ is perfect: {is_perfect}")

        # Bipartite graphs are perfect
        G2 = nx.bipartite.random_graph(5, 5, 0.3, seed=42)
        is_perfect = nx.is_perfect_graph(G2)
        print(f"Random bipartite is perfect: {is_perfect}")

        session.commit()


def demo_approximation():
    """NP-hard approximation algorithms."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="approx")
        G.add_edges_from([
            (1, 2), (1, 3), (1, 4),
            (2, 3), (2, 5),
            (3, 4), (3, 5),
            (4, 5),
        ])

        # Maximum clique approximation
        from networkx.algorithms.approximation.clique import max_clique
        G_plain = nx.Graph(G)
        mc = max_clique(G_plain)
        print(f"\nMax clique: {sorted(mc)}")

        # Clique removal
        cliques = nx.algorithms.approximation.clique_removal(G_plain)
        print(f"Clique removal order:")
        for i, clique in enumerate(cliques):
            print(f"  Step {i+1}: clique={sorted(clique)}")

        # Maximum independent set approximation
        mis = nx.algorithms.approximation.maximum_independent_set(G_plain)
        print(f"\nMax independent set: {sorted(mis)}")

        # Vertex cover approximation
        vc = nx.algorithms.approximation.min_weighted_vertex_cover(G_plain)
        print(f"Vertex cover: {sorted(vc)}")

        session.commit()


def demo_approx_tsp():
    """TSP approximation algorithms."""
    with SessionLocal() as session:
        # Complete graph on 5 nodes
        G = nx.complete_graph(5)
        # Add distances
        import random
        random.seed(42)
        for u, v in G.edges():
            G[u][v]["distance"] = round(random.uniform(1, 10), 1)

        # Christofides' algorithm (for metric TSP)
        try:
            tsp = nx.algorithms.approximation.traveling_salesman_problem
            tour = tsp(G, weight="distance", cycle=True)
            print(f"\nTSP tour (Christofides): {' → '.join(tour)}")
            tour_len = sum(
                G[tour[i]][tour[(i + 1) % len(tour)]]["distance"]
                for i in range(len(tour))
            )
            print(f"  Total distance: {tour_len:.2f}")
        except Exception as e:
            print(f"\nTSP approximation: {e}")

        # Greedy TSP
        try:
            tour = nx.algorithms.approximation.greedy_tsp(
                G, weight="distance", seed=42
            )
            print(f"\nTSP tour (greedy): {' → '.join(tour)}")
        except Exception as e:
            print(f"\nGreedy TSP: {e}")

        session.commit()


def demo_distance_regular():
    """Distance-regular graph properties."""
    with SessionLocal() as session:
        # Hypercube is distance-regular
        G = nx.hypercube_graph(3)
        is_dr = nx.is_distance_regular(G)
        print(f"Q₃ is distance-regular: {is_dr}")

        if is_dr:
            ia = nx.intersection_array(G)
            print(f"Intersection array: {ia}")

        # Complete graph is distance-regular
        G2 = nx.complete_graph(5)
        is_dr2 = nx.is_distance_regular(G2)
        print(f"\nK₅ is distance-regular: {is_dr2}")

        session.commit()


def demo_regular_graphs():
    """Regular graph detection and factorization."""
    with SessionLocal() as session:
        # 3-regular (cubic) graph
        G = nx.petersen_graph()
        is_3reg = nx.is_k_regular(G, k=3)
        print(f"Petersen is 3-regular: {is_3reg}")

        degrees = [d for n, d in G.degree()]
        print(f"Degrees: {sorted(set(degrees))}")

        # Check if 1-factor exists
        try:
            factor = nx.algorithms.matching.max_weight_matching(G, maxcardinality=True)
            print(f"\nMaximum matching (potential 1-factor): {len(factor)} edges")
            print(f"  (A 1-factor would have {G.number_of_nodes() // 2} edges)")
        except Exception as e:
            print(f"\nMatching: {e}")

        session.commit()


def demo_spanners():
    """Graph spanners."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="spanner")
        # Star graph
        G.add_edges_from([(0, i) for i in range(1, 6)])

        try:
            sp = nx.t_spanner(G, stretch=2)
            print(f"\n2-spanner: {sp.number_of_nodes()} nodes, "
                  f"{sp.number_of_edges()} edges")
        except Exception as e:
            print(f"\nSpanners: {e}")

        session.commit()


def demo_summarization():
    """Graph summarization."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="summarize")
        G.add_edges_from([
            (1, 2), (2, 3), (3, 1),  # triangle
            (4, 5), (5, 6), (6, 4),  # another triangle
            (1, 4),
        ])

        try:
            summary = nx.snap_aggregation(G)
            print(f"\nSummarized graph: {summary.number_of_nodes()} nodes, "
                  f"{summary.number_of_edges()} edges")
        except Exception as e:
            print(f"\nSummarization: {e}")

        session.commit()


if __name__ == "__main__":
    demo_chromatic_polynomial()
    demo_tutte_polynomial()
    demo_perfect_graphs()
    demo_approximation()
    demo_approx_tsp()
    demo_distance_regular()
    demo_regular_graphs()
    demo_spanners()
    demo_summarization()
