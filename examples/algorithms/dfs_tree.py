"""Demonstrate Depth-First Search (DFS) tree with nx_sql.

Mirrors networkx examples for DFS traversal.
Tests DFS tree construction, edge classification, and layered exploration.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def demo_dfs_tree():
    """Build a DFS tree from a source node and show edge classification."""

    with Session() as session:
        # Create a graph with cycles to showcase DFS edge types
        G_nx = nx.cycle_graph(6)
        G_nx.add_edge(0, 3)  # chord edge
        G = nx_sql.DiGraph(session, name="dfs_tree_demo")
        G.add_nodes_from(G_nx.nodes())
        for u, v in G_nx.edges():
            G.add_edge(u, v)
            G.add_edge(v, u)  # make it bidirectional for DFS

        root = 0
        print(f"=== DFS from root node {root} ===")
        print(f"Graph: cycle graph C6 with chord (0,3), directed ({G.number_of_nodes()} nodes)")

        # DFS tree rooted at 'root'
        T = nx.dfs_tree(G, source=root)
        print(f"\nDFS tree edges ({T.number_of_edges()}): {list(T.edges())}")

        # DFS edges in order
        print(f"\nDFS edges from root {root}:")
        for i, (u, v) in enumerate(nx.dfs_edges(G, source=root)):
            print(f"  Step {i+1}: {u} -> {v}")

        # DFS preorder and postorder
        print(f"\nPreorder traversal: {list(nx.dfs_preorder_nodes(G, source=root))}")
        print(f"Postorder traversal: {list(nx.dfs_postorder_nodes(G, source=root))}")
        # DFS from disconnected component
        print(f"\nDFS from node 0 (full graph is connected):")
        for u, v in nx.dfs_edges(G, source=0):
            print(f"  {u} -> {v}")

        # Verify DFS tree is a spanning tree
        assert T.number_of_nodes() == G.number_of_nodes(), "DFS tree should span all nodes"
        assert T.number_of_edges() == G.number_of_nodes() - 1, "Tree edges = nodes - 1"
        print(f"\n✓ DFS tree spans {T.number_of_nodes()} nodes with {T.number_of_edges()} edges")

        session.commit()


if __name__ == "__main__":
    demo_dfs_tree()
