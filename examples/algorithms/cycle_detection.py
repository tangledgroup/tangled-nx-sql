"""Demonstrate cycle detection with nx_sql.

Mirrors networkx/examples/algorithms/plot_cycle_detection.py but uses
SQLAlchemy persistence. Tests find_cycle, simple_cycles, and cycle_basis.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def demo_cycle_detection():
    """Detect cycles in directed and undirected graphs."""

    # --- Directed graph: find_cycle and simple_cycles ---
    with Session() as session:
        G = nx_sql.DiGraph(session, name="cycle_directed_demo")

        # Create a graph with known cycles
        G.add_edges_from([
            (1, 2), (2, 3), (3, 1),  # cycle: 1->2->3->1
            (3, 4), (4, 5), (5, 3),  # cycle: 3->4->5->3
            (5, 6),                   # no cycle
        ])

        print("=== Directed Graph Cycle Detection ===")
        print(f"Nodes: {list(G.nodes())}")
        print(f"Edges: {list(G.edges())}")

        # find_cycle returns one cycle
        cycle = nx.find_cycle(G, orientation="original")
        print(f"\nFound cycle: {cycle}")

        # simple_cycles finds all elementary cycles
        cycles = list(nx.simple_cycles(G))
        print(f"\nAll simple cycles ({len(cycles)}):")
        for c in cycles:
            print(f"  {' -> '.join(str(n) for n in c)} -> {c[0]}")

        session.commit()

    # --- Undirected graph: cycle_basis ---
    with Session() as session:
        G = nx_sql.Graph(session, name="cycle_undirected_demo")

        # Create a graph with known cycles
        G.add_edges_from([
            (1, 2), (2, 3), (3, 1),  # triangle
            (3, 4), (4, 5), (5, 6), (6, 3),  # square
            (1, 7), (7, 8), (8, 2),  # another triangle
        ])

        print("\n=== Undirected Graph Cycle Detection ===")
        print(f"Nodes: {list(G.nodes())}")
        print(f"Edges: {list(G.edges())}")

        # cycle_basis returns a basis for the cycle space
        basis = nx.cycle_basis(G)
        print(f"\nCycle basis ({len(basis)} cycles):")
        for c in basis:
            print(f"  {c}")

        # Number of independent cycles = E - V + C (cyclomatic number)
        num_cycles = len(basis)
        print(f"\nCyclomatic number: {num_cycles}")

        session.commit()


if __name__ == "__main__":
    demo_cycle_detection()
