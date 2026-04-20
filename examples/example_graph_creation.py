"""example_graph_creation.py - Graph creation and basic operations.

Covers: Graph, DiGraph, MultiGraph (constructor), add_node, add_edge,
        nodes, edges, degree, number_of_nodes, number_of_edges, density.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)


def demo_graph():
    """Create a Graph, add nodes/edges, query basic properties."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="social_network")

        # Add nodes with attributes
        G.add_node("Alice", age=30, role="manager")
        G.add_node("Bob", age=25, role="developer")
        G.add_node("Carol", age=35, role="designer")
        G.add_node("Dave", age=28, role="developer")

        # Add edges with attributes
        G.add_edge("Alice", "Bob", weight=0.8, since="2020")
        G.add_edge("Alice", "Carol", weight=0.6, since="2019")
        G.add_edge("Bob", "Dave", weight=0.9, since="2021")
        G.add_edge("Carol", "Dave", weight=0.5, since="2022")

        print(f"Nodes ({G.number_of_nodes()}): {list(G.nodes(data=True))}")
        print(f"Edges ({G.number_of_edges()}): {list(G.edges(data=True))}")
        print(f"Density: {nx_sql.nx.density(G):.4f}")
        print(f"Degree of Alice: {dict(G.degree(['Alice']))}")
        print(f"Neighbors of Alice: {list(G.neighbors('Alice'))}")
        print(f"Alice's attributes: {G.nodes['Alice']}")
        print(f"Edge Alice-Bob: {G['Alice']['Bob']}")

        session.commit()


def demo_digraph():
    """Create a DiGraph, add directed edges, check directionality."""
    with SessionLocal() as session:
        G = nx_sql.DiGraph(session, name="workflow")

        G.add_edge("Design", "Code", duration=5)
        G.add_edge("Code", "Test", duration=3)
        G.add_edge("Test", "Deploy", duration=2)
        G.add_edge("Code", "Review", duration=1)
        G.add_edge("Review", "Code", duration=2)  # feedback loop

        print(f"Directed edges: {list(G.edges(data=True))}")
        print(f"In-degree: {dict(G.in_degree())}")
        print(f"Out-degree: {dict(G.out_degree())}")
        print(f"Is directed: {G.is_directed()}")

        session.commit()


def demo_node_types():
    """Demonstrate various node types: strings, ints, tuples, dicts."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="mixed_nodes")

        # Different hashable types as nodes
        G.add_node(1, label="int")
        G.add_node("A", label="str")
        G.add_node((1, 2), label="tuple")
        G.add_node({"x": 1}, label="dict")

        G.add_edge(1, "A")
        G.add_edge("A", (1, 2))
        G.add_edge((1, 2), {"x": 1})

        print(f"Nodes: {list(G.nodes(data=True))}")
        print(f"Edges: {list(G.edges(data=True))}")

        session.commit()


if __name__ == "__main__":
    demo_graph()
    demo_digraph()
    demo_node_types()
