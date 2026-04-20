"""Demonstrate graph composition and union operations with nx_sql.

Tests compose, union, disjoint_union on SQL-backed graphs.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def demo_compose_union():
    """Test compose, union, and disjoint_union operations."""

    with Session() as session:
        # Create two graphs with overlapping nodes
        G1_nx = nx.path_graph(5, create_using=nx.Graph)
        G1 = nx_sql.Graph(session, name="compose_union_demo")
        for node in G1_nx.nodes():
            G1.add_node(node)
        G1.add_edges_from(G1_nx.edges())

        # Second graph with overlapping nodes
        G2_nx = nx.path_graph(3, create_using=nx.Graph)
        G2 = nx_sql.Graph(session, name="compose_union_demo2")
        for node in G2_nx.nodes():
            G2.add_node(node)
        G2.add_edges_from(G2_nx.edges())

        print("=== Graph Composition (nx.compose) ===")
        print(f"G1: {G1.number_of_nodes()} nodes, {G1.number_of_edges()} edges")
        print(f"G2: {G2.number_of_nodes()} nodes, {G2.number_of_edges()} edges")

        # Compose merges overlapping nodes
        composed = nx.compose(G1, G2)
        print(f"Composed: {composed.number_of_nodes()} nodes, {composed.number_of_edges()} edges")
        assert composed.number_of_nodes() <= G1.number_of_nodes() + G2.number_of_nodes()
        print("✓ Compose merges overlapping nodes")

    with Session() as session:
        # Create two graphs with disjoint node sets
        G3_nx = nx.path_graph(5, create_using=nx.Graph)
        G3 = nx_sql.Graph(session, name="compose_union_demo3")
        for node in G3_nx.nodes():
            G3.add_node(node + 100)  # offset to avoid overlap
        G3.add_edges_from((u + 100, v + 100) for u, v in G3_nx.edges())

        # Recreate G1 for union test
        G1_nx = nx.path_graph(5, create_using=nx.Graph)
        G1 = nx_sql.Graph(session, name="compose_union_demo6")
        for node in G1_nx.nodes():
            G1.add_node(node)
        G1.add_edges_from(G1_nx.edges())

        print("\n=== Union (nx.union) ===")
        print(f"G1: {G1.number_of_nodes()} nodes, {G1.number_of_edges()} edges")
        print(f"G3: {G3.number_of_nodes()} nodes, {G3.number_of_edges()} edges")

        union = nx.union(G1, G3)
        print(f"Union: {union.number_of_nodes()} nodes, {union.number_of_edges()} edges")
        expected_nodes = G1.number_of_nodes() + G3.number_of_nodes()
        assert union.number_of_nodes() == expected_nodes
        print("✓ Union preserves all nodes from both graphs")

    with Session() as session:
        # Recreate G for disjoint union test
        G_nx = nx.path_graph(5, create_using=nx.Graph)
        G = nx_sql.Graph(session, name="compose_union_demo7")
        for node in G_nx.nodes():
            G.add_node(node)
        G.add_edges_from(G_nx.edges())

        # Disjoint union (automatically relabels)
        print("\n=== Disjoint Union ===")
        G4_nx = nx.cycle_graph(5, create_using=nx.Graph)
        G4 = nx_sql.Graph(session, name="compose_union_demo4")
        for node in G4_nx.nodes():
            G4.add_node(node)
        G4.add_edges_from(G4_nx.edges())

        DU = nx.disjoint_union(G, G4)
        print(f"Disjoint union: {DU.number_of_nodes()} nodes, {DU.number_of_edges()} edges")
        assert DU.number_of_nodes() == G.number_of_nodes() + G4.number_of_nodes()
        assert DU.number_of_edges() == G.number_of_edges() + G4.number_of_edges()
        print("✓ Disjoint union works correctly")

        # Show that nodes are relabeled
        print(f"Original G nodes: {sorted(G.nodes())}")
        print(f"G4 nodes: {sorted(G4.nodes())}")
        print(f"DU nodes: {sorted(DU.nodes())}")

    with Session() as session:
        # Test complement
        print("\n=== Complement ===")
        G5_nx = nx.path_graph(5, create_using=nx.Graph)
        G5 = nx_sql.Graph(session, name="compose_union_demo5")
        for node in G5_nx.nodes():
            G5.add_node(node)
        G5.add_edges_from(G5_nx.edges())

        print(f"Original: {G5.number_of_nodes()} nodes, {G5.number_of_edges()} edges")
        comp = nx.complement(G5)
        expected_edges = G5.number_of_nodes() * (G5.number_of_nodes() - 1) // 2
        print(f"Complement: {comp.number_of_nodes()} nodes, {comp.number_of_edges()} edges")
        assert comp.number_of_nodes() == G5.number_of_nodes()
        # For path graph P_5: original has 4 edges, complement should have 10-4=6
        assert comp.number_of_edges() == expected_edges - G5.number_of_edges()
        print("✓ Complement works correctly")

        session.commit()


if __name__ == "__main__":
    demo_compose_union()
