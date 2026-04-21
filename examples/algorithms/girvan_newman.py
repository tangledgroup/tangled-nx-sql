"""Demonstrate community detection via Girvan-Newman with nx_sql.

Mirrors networkx/examples/algorithms/plot_girvan_newman.py but uses
SQLAlchemy persistence. Tests community detection on the karate club graph.
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
def demo_girvan_newman():
    """Detect communities using Girvan-Newman algorithm on karate club graph."""

    with Session() as session:
        G_nx = nx.karate_club_graph()
        G = nx_sql.Graph(session, name="girvan_newman_demo")
        G.add_nodes_from(G_nx.nodes())
        G.add_edges_from(G_nx.edges())

        print("=== Girvan-Newman Community Detection ===")
        print(f"Graph: karate club ({G.number_of_nodes()} nodes, {G.number_of_edges()} edges)")

        # Run Girvan-Newman
        communities_generator = nx.community.girvan_newman(G)

        # Print first few levels of community decomposition
        for level, communities in enumerate(communities_generator):
            if level >= 5:
                break
            sorted_communities = sorted(map(frozenset, communities))
            print(f"\nLevel {level} ({len(sorted_communities)} communities):")
            for i, comm in enumerate(sorted_communities):
                print(f"  Community {i}: {sorted(comm)}")

            # Compute modularity at this level
            modularity = nx.community.modularity(G, sorted_communities)
            print(f"  Modularity: {modularity:.4f}")

        # Find the best community structure (highest modularity)
        print("\n=== Best Community Structure ===")
        communities_generator = nx.community.girvan_newman(G)
        best_modularity = -1
        best_communities = None
        for level, communities in enumerate(communities_generator):
            sorted_communities = sorted(map(frozenset, communities))
            modularity = nx.community.modularity(G, sorted_communities)
            if modularity > best_modularity:
                best_modularity = modularity
                best_communities = sorted_communities

        print(f"Best modularity: {best_modularity:.4f}")
        print(f"Number of communities: {len(best_communities)}")
        for i, comm in enumerate(best_communities):
            print(f"  Community {i}: {sorted(comm)}")

        session.commit()


if __name__ == "__main__":
    demo_girvan_newman()
