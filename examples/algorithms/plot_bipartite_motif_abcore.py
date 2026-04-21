"""Demonstrate bipartite alpha/beta-core with nx_sql.

Mirrors networkx/examples/algorithms/plot_bipartite_motif_abcore.py but uses
SQLAlchemy persistence. Tests computing the alpha/beta-core of a bipartite graph.
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
def demo_bipartite_motif_abcore():
    """Compute the alpha/beta-core of a bipartite graph."""

    with Session() as session:
        # Create a connected bipartite graph using Havel-Hakimi
        top_degrees = [1, 2, 3, 2, 1, 2, 3, 2]
        bottom_degrees = [5, 7, 1, 1, 2]

        G_nx = nx.bipartite.havel_hakimi_graph(
            top_degrees, bottom_degrees, create_using=nx.Graph
        )

        G = nx_sql.Graph(session, name="bipartite_abcore_demo")
        for node in G_nx.nodes():
            G.add_node(node)
        G.add_edges_from(G_nx.edges())

        U, V = nx.bipartite.sets(G)
        print("=== Bipartite Alpha/Beta-Core ===")
        print(f"Top nodes (U): {sorted(U)}")
        print(f"Bottom nodes (V): {sorted(V)}")
        print(f"Total nodes: {G.number_of_nodes()}")
        print(f"Total edges: {G.number_of_edges()}")

        # Compute degrees for each set
        print("\nDegrees:")
        for u in sorted(U):
            print(f"  U[{u}]: degree={G.degree(u)}")
        for v in sorted(V):
            print(f"  V[{v}]: degree={G.degree(v)}")

        # Compute the alpha/beta-core
        alpha, beta = 2, 3
        G_core = G.copy()

        removed = True
        while removed:
            removed = False
            to_remove = []
            for n in list(G_core.nodes()):
                degree = G_core.degree(n)
                if n in U and degree < alpha:
                    to_remove.append(n)
                elif n in V and degree < beta:
                    to_remove.append(n)
            if to_remove:
                G_core.remove_nodes_from(to_remove)
                removed = True

        print(f"\n=== α({alpha})/β({beta})-Core ===")
        print(f"Nodes in core: {sorted(G_core.nodes())}")
        print(f"Core nodes: {len(G_core.nodes())} (from {G.number_of_nodes()})")
        print(f"Core edges: {G_core.number_of_edges()} (from {G.number_of_edges()})")

        # Try different alpha/beta values
        print("\n=== Core sizes for different α, β ===")
        for alpha in range(1, 5):
            for beta in range(1, 5):
                test_core = G.copy()
                changed = True
                while changed:
                    changed = False
                    to_remove = []
                    for n in list(test_core.nodes()):
                        degree = test_core.degree(n)
                        if n in U and degree < alpha:
                            to_remove.append(n)
                        elif n in V and degree < beta:
                            to_remove.append(n)
                    if to_remove:
                        test_core.remove_nodes_from(to_remove)
                        changed = True
                print(f"  α={alpha}, β={beta}: {len(test_core.nodes())} nodes, "
                      f"{test_core.number_of_edges()} edges")

        session.commit()


if __name__ == "__main__":
    demo_bipartite_motif_abcore()
