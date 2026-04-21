"""Demonstrate beam search with nx_sql.

Mirrors networkx/examples/algorithms/plot_beam_search.py but uses
SQLAlchemy persistence. Tests BFS beam search and eigenvector centrality.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base
import sys; sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent.parent.parent))
from examples.utils import print_docstring

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


@print_docstring
def demo_beam_search():
    """Use beam search to find nodes with high eigenvector centrality."""

    with Session() as session:
        # Create a random graph
        G_nx = nx.gnp_random_graph(20, 0.3, seed=42)
        G = nx_sql.Graph(session, name="beam_search_demo")
        G.add_nodes_from(G_nx.nodes())
        G.add_edges_from(G_nx.edges())

        print("=== Beam Search ===")
        print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

        # BFS beam search from node 0 with beam width 3
        source = 0
        beam_width = 3
        print(f"\nBFS beam search from node {source} (width={beam_width}):")
        # value function: use degree as the heuristic
        for u, v in nx.bfs_beam_edges(G, source, lambda n: G.degree(n), width=beam_width):
            print(f"  Edge: {u} -> {v}")

        # Compare with standard BFS
        print(f"\nStandard BFS from node {source}:")
        visited = set()
        queue = [source]
        while queue:
            node = queue.pop(0)
            if node in visited:
                continue
            visited.add(node)
            for neighbor in sorted(G.neighbors(node)):
                if neighbor not in visited:
                    print(f"  Edge: {node} -> {neighbor}")
                    queue.append(neighbor)

        # Eigenvector centrality
        print("\n=== Eigenvector Centrality (top 5) ===")
        ec = nx.eigenvector_centrality(G, max_iter=1000)
        top_nodes = sorted(ec.items(), key=lambda x: abs(x[1]), reverse=True)[:5]
        for node, score in top_nodes:
            print(f"  Node {node}: {score:.4f}")

        # The beam search should tend to find nodes with high centrality
        print("\n=== Beam Search vs Centrality ===")
        visited_by_beam = set()
        for u, v in nx.bfs_beam_edges(G, source, lambda n: G.degree(n), width=beam_width):
            visited_by_beam.add(v)
            if len(visited_by_beam) >= 10:
                break

        print(f"Nodes visited by beam search: {sorted(visited_by_beam)}")
        print("Their eigenvector centralities:")
        for node in sorted(visited_by_beam):
            print(f"  Node {node}: {ec.get(node, 0):.4f}")

        session.commit()


if __name__ == "__main__":
    demo_beam_search()
