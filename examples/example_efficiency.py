"""example_efficiency.py - Efficiency, non-randomness, and time-dependent measures.

Covers: local/global/individual efficiency, communicability diffusion (CD index),
        non-randomness measure, time-dependent centrality, s-metric,
        small-world metrics (sigma/omega).
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)


def demo_efficiency():
    """Efficiency measures."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="efficiency")
        G.add_edges_from([
            (1, 2), (2, 3), (3, 4), (4, 5),
            (1, 3), (2, 4),
        ])

        # Global efficiency
        ge = nx.global_efficiency(G)
        print(f"Global efficiency: {ge:.4f}")

        # Local efficiency
        le = nx.local_efficiency(G)
        print(f"Local efficiency: {le:.4f}")

        # Individual efficiency (compute manually from eccentricity)
        ie = {}
        for n in G.nodes():
            try:
                sp = nx.single_source_shortest_path_length(G, n)
                ie[n] = 1.0 / len(sp) if sp else 0.0
            except Exception:
                ie[n] = 0.0
        print(f"\nIndividual efficiency:")
        for node, eff in sorted(ie.items(), key=lambda x: -x[1]):
            print(f"  {node}: {eff:.4f}")

        session.commit()


def demo_communicability():
    """Communicability-based measures."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="comm")
        G.add_edges_from([
            (1, 2), (2, 3), (3, 4),
            (1, 3),
        ])

        # CD index (communicability diffusion centrality)
        try:
            cd = nx.cd_index(G)
            print(f"\nCD index:")
            for node, score in sorted(cd.items(), key=lambda x: -x[1]):
                print(f"  {node}: {score:.4f}")
        except Exception as e:
            print(f"\nCD index: {e}")

        session.commit()


def demo_non_randomness():
    """Non-randomness measure."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="nonrand")
        G.add_edges_from([
            (1, 2), (2, 3), (3, 4),
            (1, 3),
        ])

        try:
            nr = nx.non_randomness(G)
            print(f"\nNon-randomness: {nr:.4f}")
        except Exception as e:
            print(f"\nNon-randomness: {e}")

        session.commit()


def demo_s_metric():
    """s-metric (network robustness)."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="s_metric")
        G.add_edges_from([
            (1, 2), (1, 3), (1, 4), (1, 5),  # star
        ])

        s = nx.s_metric(G)
        print(f"\ns-metric: {s:.4f}")

        session.commit()


def demo_small_world():
    """Small-world metrics (sigma and omega)."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="smallworld")
        # Small-world graph
        G.add_edges_from(nx.watts_strogatz_graph(n=20, k=4, p=0.3, seed=42).edges())

        try:
            sigma = nx.smallworld_metric(G)
            print(f"\nSmall-world metric σ: {sigma:.4f}")
            if sigma > 1:
                print("  → Small-world network")
            elif sigma < 1:
                print("  → Not small-world")
        except Exception as e:
            print(f"\nSmall-world σ: {e}")

        try:
            omega = nx.smallworld_omega(G)
            print(f"\nSmall-world metric ω: {omega:.4f}")
        except Exception as e:
            print(f"\nSmall-world ω: {e}")

        session.commit()


def demo_kemeny_constant():
    """Kemeny's constant."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="kemeny")
        G.add_edges_from([
            (1, 2), (2, 3), (3, 4),
            (1, 3),
        ])

        try:
            kc = nx.kemeny_constant(G)
            print(f"\nKemeny's constant: {kc:.4f}")
        except Exception as e:
            print(f"\nKemeny's constant: {e}")

        session.commit()


def demo_harmonic_diameter():
    """Harmonic diameter."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="harm_diam")
        G.add_edges_from([
            (1, 2), (2, 3), (3, 4),
        ])

        hd = nx.harmonic_diameter(G)
        print(f"\nHarmonic diameter: {hd:.4f}")

        session.commit()


if __name__ == "__main__":
    demo_efficiency()
    demo_communicability()
    demo_non_randomness()
    demo_s_metric()
    demo_small_world()
    demo_kemeny_constant()
    demo_harmonic_diameter()
