"""Demonstrate minimum spanning tree with nx_sql.

Mirrors networkx/examples/graph/plot_mst.py but uses
SQLAlchemy persistence. Tests MST on a weighted graph.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def demo_minimum_spanning_tree():
    """Find the minimum spanning tree of a weighted graph."""

    with Session() as session:
        # Create a weighted graph
        G_nx = nx.erdos_renyi_graph(10, 0.5, seed=42)
        # Add weights
        for u, v in G_nx.edges():
            G_nx[u][v]["weight"] = abs(hash((u, v))) % 100 + 1

        G = nx_sql.Graph(session, name="mst_demo")
        for node in G_nx.nodes():
            G.add_node(node)
        for u, v, d in G_nx.edges(data=True):
            G.add_edge(u, v, weight=d["weight"])

        print("=== Minimum Spanning Tree ===")
        print(f"Original graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

        # Find MST
        T = nx.minimum_spanning_tree(G)
        print(f"MST: {T.number_of_nodes()} nodes, {T.number_of_edges()} edges")

        # Print MST edges with weights
        print("\nMST edges:")
        total_weight = 0
        for u, v, d in sorted(T.edges(data=True)):
            w = d.get("weight", 1)
            total_weight += w
            print(f"  {u} -- {v}: weight={w}")
        print(f"\nTotal MST weight: {total_weight}")

        # Compare with original graph edges
        print("\nAll original edges (sorted by weight):")
        all_edges = sorted(G.edges(data=True), key=lambda x: x[2].get("weight", 0))
        for u, v, d in all_edges[:15]:
            w = d.get("weight", 1)
            in_mst = T.has_edge(u, v)
            marker = " <-- MST" if in_mst else ""
            print(f"  {u} -- {v}: weight={w}{marker}")

        # Prim's and Kruskal's should give same result as minimum_spanning_tree
        prim_edges = list(nx.minimum_spanning_edges(G, algorithm='prim'))
        kruskal_edges = list(nx.minimum_spanning_edges(G, algorithm='kruskal'))
        print(f"\nPrim's MST edges: {len(list(prim_edges))}")
        print(f"Kruskal's MST edges: {len(list(kruskal_edges))}")

        # Compare edge sets (ignoring weights)
        t_edges = set((u, v) for u, v in T.edges())
        prim_set = set((u, v) for u, v, _ in nx.minimum_spanning_edges(G, algorithm='prim'))
        kruskal_set = set((u, v) for u, v, _ in nx.minimum_spanning_edges(G, algorithm='kruskal'))
        # Both should have same total weight (may differ in edge selection for equal weights)
        t_weight = sum(d.get("weight", 1) for _, _, d in T.edges(data=True))
        prim_weight = sum(d.get("weight", 1) for _, _, d in nx.minimum_spanning_tree(G, algorithm='prim').edges(data=True))
        kruskal_weight = sum(d.get("weight", 1) for _, _, d in nx.minimum_spanning_tree(G, algorithm='kruskal').edges(data=True))
        print(f"MST weights: T={t_weight}, Prim={prim_weight}, Kruskal={kruskal_weight}")
        assert t_weight == prim_weight == kruskal_weight, "MST algorithms should produce same total weight"
        print("✓ All MST algorithms agree (same total weight)")

        session.commit()


if __name__ == "__main__":
    demo_minimum_spanning_tree()
