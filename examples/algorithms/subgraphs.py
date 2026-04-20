"""Demonstrate subgraph operations with nx_sql.

Mirrors networkx/examples/algorithms/plot_subgraphs.py but uses
SQLAlchemy persistence. Tests subgraph extraction, copying, and isomorphism.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def demo_subgraphs():
    """Extract and compare subgraphs."""

    with Session() as session:
        G_nx = nx.davis_southern_women_graph()
        G = nx_sql.Graph(session, name="subgraphs_demo")
        for n in G_nx.nodes():
            G.add_node(n)
        G.add_edges_from(G_nx.edges())

        print("=== Original Graph ===")
        print(f"Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")

        # Extract subgraph of women who attended at least 3 events
        women = [n for n, d in G_nx.nodes(data=True) if d.get("bipartite") == 0]
        women_high_attendance = [w for w in women if G.degree(w) >= 3]

        print(f"\nWomen with 3+ event attendances: {len(women_high_attendance)}")

        # Create subgraph
        subG = G.subgraph(women_high_attendance).copy()
        print(f"\nSubgraph (high-attendance women):")
        print(f"  Nodes: {subG.number_of_nodes()}, Edges: {subG.number_of_edges()}")

        # The subgraph of women in a bipartite graph has no direct edges
        # between women — they're only connected through events.
        # To see women-women connections, we need the projected graph.
        print(f"  (Women have no direct edges in the bipartite graph)")

        # Test with a different subgraph — all nodes
        full_sub = G.subgraph(list(G.nodes())[:10]).copy()
        print(f"\nSubgraph of first 10 nodes:")
        print(f"  Nodes: {full_sub.number_of_nodes()}, Edges: {full_sub.number_of_edges()}")

        # Test isomorphism on a smaller subgraph
        ref_G = nx.path_graph(5)
        path_sub = G.subgraph(list(women_high_attendance)[:5]).copy()
        is_iso = nx.is_isomorphic(path_sub, ref_G)
        print(f"\nIs 5-women subgraph isomorphic to P_5? {is_iso}")

        session.commit()

    # Union and disjoint union in separate sessions
    with Session() as session:
        G2_nx = nx.gnp_random_graph(5, 0.5, seed=123)
        G2 = nx_sql.Graph(session, name="subgraphs_demo2")
        for n in G2_nx.nodes():
            G2.add_node(n)
        G2.add_edges_from(G2_nx.edges())

        # Compose (union with overlapping nodes merged)
        composed = nx.compose(G, G2)
        print(f"\nComposed graph: {composed.number_of_nodes()} nodes, {composed.number_of_edges()} edges")

        session.commit()

    with Session() as session:
        H_nx = nx.path_graph(5)
        H = nx_sql.Graph(session, name="subgraphs_demo3")
        for n in H_nx.nodes():
            H.add_node(n)
        H.add_edges_from(H_nx.edges())

        # Disjoint union
        print("\n=== Disjoint Union ===")
        DU = nx.disjoint_union(G, H)
        print(f"Disjoint union: {DU.number_of_nodes()} nodes, {DU.number_of_edges()} edges")


if __name__ == "__main__":
    demo_subgraphs()
