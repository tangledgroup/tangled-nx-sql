"""example_backend.py - Backend configuration and utilities.

Covers: __networkx_backend__, backend_priority, fallback_to_nx,
        UnionFind, creation decorators, misc utilities,
        random utilities (permutation, reservoir sampling),
        graph generation configs.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)


def demo_backend_info():
    """Check and use __networkx_backend__."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="backend_check")
        print(f"Backend: {G.__networkx_backend__()!r}")
        print(f"Is directed: {G.is_directed()}")
        print(f"Is multigraph: {G.is_multigraph()}")

        # Create different graph types
        D = nx_sql.DiGraph(session, name="backend_dg")
        print(f"\nDiGraph backend: {D.__networkx_backend__()!r}")
        print(f"Is directed: {D.is_directed()}")

        MG = nx_sql.MultiGraph(session, name="backend_mg")
        print(f"\nMultiGraph backend: {MG.__networkx_backend__()!r}")
        print(f"Is multigraph: {MG.is_multigraph()}")

        MDG = nx_sql.MultiDiGraph(session, name="backend_mdg")
        print(f"\nMultiDiGraph backend: {MDG.__networkx_backend__()!r}")
        print(f"Is directed: {MDG.is_directed()}")
        print(f"Is multigraph: {MDG.is_multigraph()}")

        session.commit()


def demo_unionfind():
    """Union-Find (disjoint set) data structure."""
    uf = nx.utils.UnionFind()

    # Union sets
    uf.union(1, 2)
    uf.union(2, 3)
    uf.union(4, 5)

    # UnionFind operations
    uf.union(1, 2)
    uf.union(2, 3)
    uf.union(4, 5)
    # Check equivalence via to_sets
    sets = list(uf.to_sets())
    print(f"Sets: {sets}")
    # 1 and 3 are in the same set
    s1_3 = any(1 in s and 3 in s for s in sets)
    s1_4 = any(1 in s and 4 in s for s in sets)
    print(f"1 in same set as 3: {s1_3}")
    print(f"1 in same set as 4: {s1_4}")
    print(f"Weights: {uf.weights}")


def demo_random_utilities():
    """Random utility functions."""
    import random
    # Random permutation (replaced in NX 3.6)
    items = list(range(10))
    random.shuffle(items)
    perm = items
    print(f"\nRandom permutation (10): {perm[:5]}...")

    # Arbitrary element from collection
    items = ["a", "b", "c", "d"]
    picked = nx.utils.arbitrary_element(items)
    print(f"Arbitrary element: {picked}")

    # Random sample
    sample = nx.utils.random_sample(range(100), 5)
    print(f"Random sample (5 from 100): {sorted(sample)}")

    # Power-law sequence
    pl_seq = nx.utils.powerlaw_sequence(n=20, exponent=2.5, seed=42)
    print(f"\nPower-law sequence (first 5): {[round(x, 2) for x in pl_seq[:5]]}")

    # Reservoir sampling
    reservoir = nx.utils.reservoir(iterable=range(1000), k=5, seed=42)
    print(f"Reservoir sample (5 from 1000): {sorted(reservoir)}")


def demo_config():
    """Backend and drawing configuration."""
    # Set backend priority for algorithms
    nx.set_global_backend_priority("algos", ["nx_sql", "networkx"])
    print(f"\nAlgorithm backend priority: "
          f"{nx.get_global_backend_priority('algos')}")

    # Drawing config
    nx.set_draw_element_limit(100)
    print(f"Element limit: {nx.get_draw_element_limit()}")


def test_multigraph():
    """Test MultiGraph/MultiDiGraph operations."""
    with SessionLocal() as session:
        # Test MultiGraph
        MG = nx_sql.MultiGraph(session, name="test_mg")
        MG.add_edge(1, 2, weight=1)
        MG.add_edge(1, 2, weight=2)  # second edge
        MG.add_edge(1, 2, weight=3)  # third edge

        print(f"\nMultiGraph edges: {list(MG.edges(data=True, keys=True))}")
        print(f"MultiGraph degree of 1: {MG.degree(1)}")

        # Remove one specific edge
        MG.remove_edge(1, 2, key=0)
        print(f"After removing edge 0: {list(MG.edges(data=True, keys=True))}")

        session.commit()


def test_multidigraph():
    """Test MultiDiGraph operations."""
    with SessionLocal() as session:
        MDG = nx_sql.MultiDiGraph(session, name="test_mdg")
        MDG.add_edge("A", "B", weight=1)
        MDG.add_edge("A", "B", weight=2)
        MDG.add_edge("B", "A", weight=3)

        print(f"\nMultiDiGraph edges: {list(MDG.edges(data=True, keys=True))}")
        print(f"Out-degree of A: {MDG.out_degree('A')}")
        print(f"In-degree of B: {MDG.in_degree('B')}")

        session.commit()


if __name__ == "__main__":
    demo_backend_info()
    demo_unionfind()
    demo_random_utilities()
    demo_config()
    test_multigraph()
    test_multidigraph()
