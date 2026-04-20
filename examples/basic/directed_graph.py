"""Demonstrate DiGraph (directed graph) operations with nx_sql.

Mirrors networkx/examples/basic/plot_basic_directed.py but uses SQLAlchemy persistence.
Shows directed edges, successors, predecessors, and edge direction preservation.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def demo_directed_graph():
    """Create DiGraph, test successors, predecessors, and directed edge behavior."""

    with Session() as session:
        G = nx_sql.DiGraph(session, name="directed_graph_demo")

        # Build a simple directed graph
        G.add_edge("A", "B", weight=0.5)
        G.add_edge("B", "C", weight=0.3)
        G.add_edge("C", "D", weight=0.2)
        G.add_edge("A", "D", weight=1.0)
        G.add_edge("D", "A", weight=0.8)  # reverse edge

        print(f"Nodes: {list(G.nodes())}")
        print(f"Edges: {list(G.edges(data=True))}")

        # Test successors (out-neighbors)
        print(f"\nSuccessors of A: {list(G.successors('A'))}")
        print(f"Successors of B: {list(G.successors('B'))}")

        # Test predecessors (in-neighbors)
        print(f"Predecessors of D: {list(G.predecessors('D'))}")
        print(f"Predecessors of A: {list(G.predecessors('A'))}")

        # Verify direction is preserved
        assert G.has_edge("A", "B"), "A -> B should exist"
        assert not G.has_edge("B", "A"), "B -> A should NOT exist (directed)"
        print("\nDirection verification: A->B exists, B->A does NOT exist ✓")

        # Test in_edges and out_edges
        print(f"\nOut-edges of A: {list(G.out_edges('A', data=True))}")
        print(f"In-edges of D: {list(G.in_edges('D', data=True))}")

        session.commit()


if __name__ == "__main__":
    demo_directed_graph()
