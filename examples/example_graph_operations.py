"""example_graph_operations.py - Graph manipulation and set operations.

Covers: add_node, remove_node, add_edge, remove_edge, copy, subgraph,
        complement, to_directed, to_undirected, reverse, isomorphism,
        node/edge attributes, relabeling.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)


def demo_modify_graph():
    """Add and remove nodes and edges."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="modify")

        # Add nodes
        G.add_node("A", color="red")
        G.add_node("B", color="blue")
        G.add_node("C", color="green")
        print(f"After adding nodes: {list(G.nodes(data=True))}")

        # Add edges
        G.add_edge("A", "B", weight=1.0)
        G.add_edge("B", "C", weight=2.0)
        print(f"After adding edges: {list(G.edges(data=True))}")

        # Update attributes
        G.nodes["A"]["color"] = "yellow"
        G["A"]["B"]["weight"] = 1.5
        print(f"Updated A attrs: {G.nodes['A']}")
        print(f"Updated edge A-B: {G['A']['B']}")

        # Remove edge
        G.remove_edge("B", "C")
        print(f"After removing B-C: {list(G.edges(data=True))}")

        # Remove node
        G.remove_node("C")
        print(f"After removing C: {list(G.nodes(data=True))}, {list(G.edges(data=True))}")

        session.commit()


def demo_copy_subgraph():
    """Copy and subgraph operations."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="copy_sub")

        edges = [(1, 2), (2, 3), (3, 4), (4, 5), (5, 1)]
        G.add_edges_from(edges)

        # Copy
        H = G.copy()
        print(f"Copy - same nodes: {set(G.nodes()) == set(H.nodes())}")
        print(f"Copy - same edges: {set(G.edges()) == set(H.edges())}")

        # Subgraph
        SG = G.subgraph([1, 2, 3, 4])
        print(f"\nSubgraph [1,2,3,4]:")
        print(f"  Nodes: {sorted(SG.nodes())}")
        print(f"  Edges: {sorted(SG.edges())}")

        # Complement (requires in-memory graph)
        G_plain = nx.Graph(G)
        CG = nx.complement(G_plain)
        print(f"\nComplement of C5 ({G.number_of_edges()} edges):")
        print(f"  Edges: {sorted(CG.edges())} ({CG.number_of_edges()} edges)")

        session.commit()


def demo_conversion():
    """Convert between graph types."""
    with SessionLocal() as session:
        # Graph → DiGraph
        G = nx_sql.Graph(session, name="conv_graph")
        G.add_edge(1, 2)
        G.add_edge(2, 3)

        DG = G.to_directed()
        print(f"Graph edges: {sorted(G.edges())}")
        print(f"As DiGraph edges: {sorted(DG.edges())}")

        # DiGraph → Graph
        D = nx_sql.DiGraph(session, name="conv_digraph")
        D.add_edge(1, 2)
        D.add_edge(3, 2)

        U = D.to_undirected()
        print(f"\nDiGraph edges: {sorted(D.edges())}")
        print(f"As Graph edges: {sorted(U.edges())}")

        # DiGraph reverse
        R = D.reverse()
        print(f"\nReversed DiGraph edges: {sorted(R.edges())}")

        session.commit()


def demo_isomorphism():
    """Check graph isomorphism."""
    with SessionLocal() as session:
        G1 = nx_sql.Graph(session, name="iso_a")
        G1.add_edges_from([(1, 2), (2, 3), (3, 4)])

        G2 = nx_sql.Graph(session, name="iso_b")
        G2.add_edges_from([("a", "b"), ("b", "c"), ("c", "d")])

        G3 = nx_sql.Graph(session, name="iso_c")
        G3.add_edges_from([(1, 2), (2, 3), (1, 3)])  # triangle, not isomorphic

        print(f"Path4 ≅ Path4 (different labels): {nx.is_isomorphic(G1, G2)}")
        print(f"Path4 ≅ Triangle: {nx.is_isomorphic(G1, G3)}")

        # Subgraph isomorphism
        large = nx_sql.Graph(session, name="iso_large")
        large.add_edges_from([(1, 2), (2, 3), (3, 4), (4, 5), (5, 1), (1, 3)])

        matcher = nx.algorithms.isomorphism.GraphMatcher(large, G1)
        print(f"Path4 is subgraph of C5+chord: {matcher.subgraph_isomorphisms_iter().__next__() if matcher.subgraph_isomorphisms_iter() else 'None'}")

        session.commit()


def demo_node_edge_data():
    """Node and edge attribute management."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="attrs")

        # Set node attributes
        G.add_node(1, name="Alice", dept="Engineering", level=5)
        G.add_node(2, name="Bob", dept="Marketing", level=3)
        G.add_node(3, name="Carol", dept="Engineering", level=4)

        # Set edge attributes
        G.add_edge(1, 2, relation="friend", since=2020)
        G.add_edge(1, 3, relation="colleague", since=2021)

        print("All nodes with data:")
        for n, d in sorted(G.nodes(data=True)):
            print(f"  {n}: {d}")

        print("\nAll edges with data:")
        for u, v, d in sorted(G.edges(data=True)):
            print(f"  {u} → {v}: {d}")

        # Query by attribute
        eng_nodes = [n for n, d in G.nodes(data=True) if d.get("dept") == "Engineering"]
        print(f"\nEngineering nodes: {eng_nodes}")

        session.commit()


def demo_bfs_dfs():
    """BFS and DFS traversals."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="traversal")

        # Tree-like structure
        edges = [
            ("root", "A"), ("root", "B"),
            ("A", "C"), ("A", "D"),
            ("B", "E"), ("B", "F"),
        ]
        G.add_edges_from(edges)

        print("BFS from root:")
        for node in nx.bfs_tree(G, "root").nodes():
            print(f"  {node}")

        print("\nDFS edges from root:")
        for u, v in nx.dfs_edges(G, "root"):
            print(f"  {u} → {v}")

        print("\nBFS order:")
        print(f"  {list(nx.bfs_predecessors(G, 'root'))}")

        # BFS/DFS on DiGraph
        D = nx_sql.DiGraph(session, name="traversal_dg")
        D.add_edges_from([("A", "B"), ("A", "C"), ("B", "D")])
        print("\nDiGraph DFS edges from A:")
        for u, v in nx.dfs_edges(D, "A"):
            print(f"  {u} → {v}")

        session.commit()


if __name__ == "__main__":
    demo_modify_graph()
    demo_copy_subgraph()
    demo_conversion()
    demo_isomorphism()
    demo_node_edge_data()
    demo_bfs_dfs()
