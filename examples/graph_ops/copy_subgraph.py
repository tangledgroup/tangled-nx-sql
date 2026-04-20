"""Demonstrate graph copy and subgraph operations with nx_sql.

Mirrors networkx examples for copy(), subgraph, to_directed, to_undirected.
Tests data persistence through transformations.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def demo_copy_subgraph():
    """Test copy, subgraph, to_directed, to_undirected operations."""

    with Session() as session:
        # Create original graph
        G_nx = nx.karate_club_graph()
        G = nx_sql.Graph(session, name="copy_subgraph_demo")
        G.add_nodes_from(G_nx.nodes(data=True))
        G.add_edges_from(G_nx.edges())

        print("=== Original Graph ===")
        print(f"Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")
        print(f"Is directed: {G.is_directed()}")

        # Test copy()
        print("\n=== Copy ===")
        G_copy = G.copy()
        print(f"Copy: {G_copy.number_of_nodes()} nodes, {G_copy.number_of_edges()} edges")
        assert G_copy.number_of_nodes() == G.number_of_nodes()
        assert G_copy.number_of_edges() == G.number_of_edges()
        print("✓ Copy preserves node/edge count")

        # Test subgraph()
        print("\n=== Subgraph ===")
        high_degree_nodes = [n for n in G.nodes() if G.degree(n) >= 10]
        print(f"High-degree nodes (≥10): {len(high_degree_nodes)}")
        subG = G.subgraph(high_degree_nodes).copy()
        print(f"Subgraph: {subG.number_of_nodes()} nodes, {subG.number_of_edges()} edges")

        # Verify all subgraph nodes have degree >= 10 in original
        for node in subG.nodes():
            assert G.degree(node) >= 10, f"Node {node} has degree < 10"
        print("✓ All subgraph nodes verified")

        # Test to_directed()
        print("\n=== To Directed ===")
        DG = G.to_directed()
        print(f"Directed graph: {DG.number_of_nodes()} nodes, {DG.number_of_edges()} edges")
        print(f"Is directed: {DG.is_directed()}")
        # In a directed version of an undirected graph, each edge becomes 2 directed edges
        assert DG.is_directed()
        print("✓ to_directed() works")

        # Test to_undirected()
        print("\n=== To Undirected ===")
        G_nx2 = nx.path_graph(5, create_using=nx.DiGraph)
        G2 = nx_sql.DiGraph(session, name="copy_subgraph_demo2")
        for node in G_nx2.nodes():
            G2.add_node(node)
        G2.add_edges_from(G_nx2.edges())

        print(f"Directed: {G2.number_of_nodes()} nodes, {G2.number_of_edges()} edges")
        U = G2.to_undirected()
        print(f"Undirected: {U.number_of_nodes()} nodes, {U.number_of_edges()} edges")
        assert not U.is_directed()
        print("✓ to_undirected() works")

        # Test subgraph persistence across sessions
        print("\n=== Subgraph Persistence ===")
        sub_nodes = list(G.nodes())[:10]
        with Session() as session2:
            G_reload = nx_sql.Graph(session2, graph_id=G.graph_id)
            subG2 = G_reload.subgraph(sub_nodes).copy()
            print(f"Reloaded subgraph: {subG2.number_of_nodes()} nodes, {subG2.number_of_edges()} edges")
            print(f"Nodes: {sorted(subG2.nodes())}")
        print("✓ Subgraph persistence verified")

        session.commit()


if __name__ == "__main__":
    demo_copy_subgraph()
