"""Demonstrate clique detection with nx_sql.

Tests finding maximal cliques, maximum cliques, and k-cliques in a graph.
A clique is a subset of nodes where every two distinct nodes are adjacent.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def demo_clique():
    """Find cliques and maximal cliques in a graph."""

    with Session() as session:
        # Use a graph with known clique structure
        G_nx = nx.karate_club_graph()
        G = nx_sql.Graph(session, name="clique_demo")
        G.add_nodes_from(G_nx.nodes())
        G.add_edges_from(G_nx.edges())

        print(f"=== Clique Detection ===")
        print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

        # Find all maximal cliques
        cliques = list(nx.find_cliques(G))
        print(f"\nMaximal cliques ({len(cliques)} total):")
        for i, clique in enumerate(sorted(cliques, key=len, reverse=True)):
            print(f"  Clique {i+1} (size={len(clique)}): {sorted(clique)}")

        # Find the maximum clique
        max_clique = max(nx.find_cliques(G), key=len)
        print(f"\nMaximum clique (size={len(max_clique)}): {sorted(max_clique)}")

        # Verify it's a clique
        subgraph = G.subgraph(max_clique)
        expected_edges = len(max_clique) * (len(max_clique) - 1) // 2
        print(f"Edges in max clique: {subgraph.number_of_edges()} (expected {expected_edges})")
        assert subgraph.number_of_edges() == expected_edges, "Max clique should be complete"
        print("✓ Verified: maximum clique is a complete subgraph")

        # Find cliques containing specific nodes
        node = 0
        cliques_with_0 = [c for c in cliques if node in c]
        print(f"\nCliques containing node {node}: {len(cliques_with_0)}")
        for c in sorted(cliques_with_0, key=len, reverse=True):
            print(f"  {sorted(c)} (size={len(c)})")

        # Find all 3-cliques (triangles)
        triangles = list(nx.simple_cycles(G.to_directed()) if G.is_directed() else [])
        # For undirected, use triangle enumeration
        triangle_count = sum(1 for _ in nx.triangles(G, [n for n in G.nodes()]))
        tri_dict = nx.triangles(G)
        total_triangles = sum(tri_dict.values()) // 3  # each triangle counted 3 times
        print(f"\nTotal triangles: {total_triangles}")
        print(f"Triangles per node: {dict(sorted(tri_dict.items()))}")

        session.commit()


if __name__ == "__main__":
    demo_clique()
