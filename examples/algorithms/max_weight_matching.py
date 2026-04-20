"""Demonstrate maximum weight matching with nx_sql.

Tests finding a maximum weight matching — a set of edges without common vertices
that maximizes the total weight. Useful for assignment problems.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def demo_max_weight_matching():
    """Find maximum weight matching in a bipartite-like graph."""

    with Session() as session:
        # Create a weighted graph
        G_nx = nx.Graph()
        G_nx.add_edge('A1', 'B1', weight=3)
        G_nx.add_edge('A1', 'B2', weight=2)
        G_nx.add_edge('A2', 'B1', weight=4)
        G_nx.add_edge('A2', 'B2', weight=5)
        G_nx.add_edge('A2', 'B3', weight=6)
        G_nx.add_edge('A3', 'B2', weight=7)
        G_nx.add_edge('A3', 'B3', weight=1)

        G = nx_sql.Graph(session, name="max_weight_matching_demo")
        G.add_nodes_from(G_nx.nodes())
        G.add_edges_from(G_nx.edges(data=True))

        print(f"=== Maximum Weight Matching ===")
        print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        print(f"Edge weights:")
        for u, v, data in sorted(G.edges(data=True)):
            print(f"  {u} -- {v}: weight={data.get('weight', 1)}")

        # Find maximum weight matching
        matching = nx.algorithms.matching.max_weight_matching(G)
        print(f"\nMaximum weight matching ({len(matching)} edges):")
        total_weight = 0
        for u, v in sorted(matching):
            w = G[u][v].get('weight', 1)
            total_weight += w
            print(f"  {u} ↔ {v}: weight={w}")
        print(f"Total weight: {total_weight}")

        # Verify no shared vertices
        matched_nodes = set()
        for u, v in matching:
            assert u not in matched_nodes, "Each node should appear at most once"
            assert v not in matched_nodes, "Each node should appear at most once"
            matched_nodes.add(u)
            matched_nodes.add(v)
        print(f"✓ Verified: no shared vertices in matching")

        # Compare with maximum cardinality matching (unweighted)
        matching_card = nx.algorithms.matching.max_weight_matching(G, maxcardinality=True)
        print(f"\nMaximum cardinality matching ({len(matching_card)} edges):")
        for u, v in sorted(matching_card):
            w = G[u][v].get('weight', 1)
            print(f"  {u} ↔ {v}: weight={w}")

        # Verify on a simple case
        print(f"\n=== Simple Case ===")
        G_simple = nx_sql.Graph(session, name="max_weight_matching_simple")
        G_simple.add_edge(0, 1, weight=1)
        G_simple.add_edge(1, 2, weight=5)
        G_simple.add_edge(2, 3, weight=1)
        G_simple.add_edge(0, 3, weight=1)

        matching_simple = nx.algorithms.matching.max_weight_matching(G_simple)
        print(f"Path graph with weights: {list(G_simple.edges(data='weight'))}")
        print(f"Max weight matching: {matching_simple}")

        session.commit()


if __name__ == "__main__":
    demo_max_weight_matching()
