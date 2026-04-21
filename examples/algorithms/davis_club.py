"""Demonstrate bipartite projections with nx_sql.

Mirrors networkx/examples/algorithms/plot_davis_club.py but uses
SQLAlchemy persistence. Tests bipartite projected graphs on the Davis
Southern Women dataset.
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
def demo_davis_club():
    """Project the Davis Southern Women bipartite graph onto each set of nodes."""

    with Session() as session:
        G_nx = nx.davis_southern_women_graph()
        G = nx_sql.Graph(session, name="davis_club_demo")
        G.add_nodes_from(G_nx.nodes(data=True))
        G.add_edges_from(G_nx.edges())

        print("=== Davis Southern Women Graph ===")
        women = [n for n, d in G_nx.nodes(data=True) if d.get("bipartite") == 0]
        events = [n for n, d in G_nx.nodes(data=True) if d.get("bipartite") == 1]
        print(f"Women: {len(women)}")
        print(f"Events: {len(events)}")
        print(f"Total edges: {G.number_of_edges()}")

        # Project onto women — two women are connected if they attended the same event
        print("\n=== Women's Projection ===")
        W = nx.bipartite.projected_graph(G, women)
        print(f"Projected graph: {W.number_of_nodes()} nodes, {W.number_of_edges()} edges")

        # Print degree of each woman in the projected graph
        print("\nWomen by connections (in projection):")
        for w in sorted(women):
            degree = W.degree(w)
            print(f"  {w}: {degree} connections")

        # Weighted projection
        print("\n=== Weighted Women's Projection ===")
        W_weighted = nx.bipartite.weighted_projected_graph(G, women)
        print(f"Weighted graph: {W_weighted.number_of_nodes()} nodes, {W_weighted.number_of_edges()} edges")

        # Print top connections
        top_edges = sorted(W_weighted.edges(data=True), key=lambda x: x[2].get("weight", 0), reverse=True)[:10]
        print("\nTop 10 weighted connections:")
        for u, v, d in top_edges:
            print(f"  {u} -- {v}: weight={d.get('weight', 0)}")

        # Project onto events
        print("\n=== Events Projection ===")
        E = nx.bipartite.projected_graph(G, events)
        print(f"Projected graph: {E.number_of_nodes()} nodes, {E.number_of_edges()} edges")

        session.commit()


if __name__ == "__main__":
    demo_davis_club()
