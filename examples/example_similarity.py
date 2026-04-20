"""example_similarity.py - Graph similarity and edit distance.

Covers: graph_edit_distance, optimal edit paths, SimRank, Panther
        similarity, random path generation, node classification,
        communicability, chain decomposition.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)


def demo_graph_edit_distance():
    """Graph edit distance (approximate)."""
    with SessionLocal() as session:
        G1_plain = nx.Graph()
        G1_plain.add_edges_from([(1, 2), (2, 3)])

        G2_plain = nx.Graph()
        G2_plain.add_edges_from([(1, 2), (2, 3), (3, 4)])

        # Graph edit distance (requires networkx-algorithms or approximate)
        try:
            ged = nx.graph_edit_distance(G1_plain, G2_plain)
            print(f"Graph edit distance: {ged:.4f}")
        except Exception as e:
            print(f"GED not available: {e}")

        # SimRank similarity (requires connected graph)
        try:
            sim = nx.simrank_similarity(G1_plain, G2_plain)
            print(f"\nSimRank similarity matrix:")
            for u in sorted(sim):
                row = " ".join(f"{sim[u][v]:.4f}" for v in sorted(sim[u]))
                print(f"  {u}: {row}")
        except Exception as e:
            print(f"\nSimRank: {e} (graphs need to be connected)")

        session.commit()


def demo_node_classification():
    """Semi-supervised node classification."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="node_class")
        G.add_edges_from([
            (1, 2), (2, 3), (3, 4), (4, 5),
            (1, 3), (2, 4),
        ])

        # Label some nodes
        labeled = {1: "A", 3: "B", 5: "A"}
        unlabeled = {2, 4}

        # Harmonic function labeling
        try:
            labels = nx.harmonic_function(G, labeled, unlabeled)
            print(f"\nHarmonic function labels:")
            for node, label in sorted(labels.items()):
                print(f"  {node}: class={label}")
        except Exception as e:
            print(f"\nHarmonic function: {e}")

        # Local and global consistency
        try:
            labels2 = nx.local_and_global_consistency(
                G, labeled, unlabeled
            )
            print(f"\nLocal & global consistency:")
            for node, label in sorted(labels2.items()):
                print(f"  {node}: class={label}")
        except Exception as e:
            print(f"\nLocal & global: {e}")

        session.commit()


def demo_communicability():
    """Graph communicability measures."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="communicability")
        G.add_edges_from([
            (1, 2), (2, 3), (3, 4),
            (1, 3),
        ])

        # Communicability between centrality
        try:
            comm = nx.communicability_betweenness_centrality(G)
            print(f"\nCommunicability betweenness:")
            for node, score in sorted(comm.items(), key=lambda x: -x[1]):
                print(f"  {node}: {score:.4f}")
        except Exception as e:
            print(f"\nCommunicability: {e}")

        # Node communicability
        try:
            nc = nx.communicability_alg_centrality(G)
            print(f"\nNode communicability (ALG):")
            for node, score in sorted(nc.items(), key=lambda x: -x[1]):
                print(f"  {node}: {score:.4f}")
        except Exception as e:
            print(f"\nNode communicability: {e}")

        session.commit()


def demo_chain_decomposition():
    """Chain decomposition of a graph."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="chain_dec")
        G.add_edges_from([
            (1, 2), (2, 3), (3, 1),  # triangle
            (3, 4), (4, 5),
        ])

        try:
            chains = nx.chain_decomposition(G)
            print(f"\nChain decomposition ({len(chains)} chains):")
            for i, chain in enumerate(chains):
                print(f"  Chain {i+1}: {chain}")
        except Exception as e:
            print(f"\nChain decomposition: {e}")

        session.commit()


def demo_random_walks():
    """Random walk analysis."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="rand_walk")
        G.add_edges_from([
            (1, 2), (2, 3), (3, 4),
            (1, 3),
        ])

        # Number of walks
        A = nx.adjacency_matrix(G)
        num_walks_2 = A.power(2).nnz
        print(f"\nWalks of length 2: {num_walks_2}")

        # Random walk centrality
        try:
            rwc = nx.random_walk_centrality(G, personalization=None)
            print(f"\nRandom walk centrality:")
            for node, score in sorted(rwc.items(), key=lambda x: -x[1]):
                print(f"  {node}: {score:.4f}")
        except Exception as e:
            print(f"\nRandom walk centrality: {e}")

        session.commit()


def demo_distance_measures():
    """Distance-based measures."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="dist_meas")
        G.add_edges_from([
            (1, 2), (2, 3), (3, 4), (4, 5),
        ])

        # Eccentricity
        ecc = nx.eccentricity(G)
        print(f"\nEccentricity:")
        for node, e in sorted(ecc.items()):
            print(f"  {node}: {e}")

        # Center and periphery
        center = nx.center(G)
        periphery = nx.periphery(G)
        print(f"\nCenter: {center}")
        print(f"Periphery: {periphery}")
        print(f"Radius: {nx.radius(G)}")
        print(f"Diameter: {nx.diameter(G)}")

        # Resistance distance
        try:
            rd = nx.resistance_distance(G)
            print(f"\nResistance distance 1-5: {rd[1][5]:.4f}")
        except Exception as e:
            print(f"\nResistance distance: {e}")

        session.commit()


if __name__ == "__main__":
    demo_graph_edit_distance()
    demo_node_classification()
    demo_communicability()
    demo_chain_decomposition()
    demo_random_walks()
    demo_distance_measures()
