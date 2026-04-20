"""Demonstrate Breadth-First Search (BFS) tree with nx_sql.

Mirrors networkx/examples/algorithms/plot_bfs.py but uses SQLAlchemy persistence.
Tests BFS traversal, BFS tree construction, and layered exploration.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def demo_bfs_tree():
    """Build a BFS tree from a source node and show layered traversal."""

    with Session() as session:
        # Create a tree-like graph
        G_nx = nx.balanced_tree(3, 3)
        G = nx_sql.Graph(session, name="bfs_tree_demo")
        G.add_nodes_from(G_nx.nodes())
        G.add_edges_from(G_nx.edges())

        root = 0
        print(f"=== BFS from root node {root} ===")
        print(f"Tree: balanced ternary tree of depth 3 ({G.number_of_nodes()} nodes)")

        # BFS tree rooted at 'root'
        B = nx.bfs_tree(G, source=root)
        print(f"\nBFS tree edges ({B.number_of_edges()}): {list(B.edges())}")

        # BFS layers
        print(f"\nBFS layers from root {root}:")
        for depth, layer in enumerate(nx.bfs_layers(G, root)):
            print(f"  Depth {depth}: {layer}")

        # BFS predecessor mapping
        pred, depth = nx.bfs_predecessors(G, source=root), nx.bfs_tree(G, source=root)
        predecessors = dict(nx.bfs_predecessors(G, source=root))
        print(f"\nPredecessors: {predecessors}")

        # BFS edges in order
        print(f"\nBFS edges from root {root}:")
        for i, (u, v) in enumerate(nx.bfs_edges(G, source=root)):
            print(f"  Step {i+1}: {u} -> {v}")

        session.commit()


if __name__ == "__main__":
    demo_bfs_tree()
