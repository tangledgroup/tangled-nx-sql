"""Demonstrate triad types in directed graphs with nx_sql.

Mirrors networkx/examples/graph/plot_triad_types.py but uses
SQLAlchemy persistence. Tests triadic census on directed graphs.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def demo_triad_types():
    """Analyze triad types in directed graphs."""

    with Session() as session:
        # Create a small directed graph
        G_nx = nx.gnp_random_graph(10, 0.3, directed=True, seed=42)

        G = nx_sql.DiGraph(session, name="triad_demo")
        for node in G_nx.nodes():
            G.add_node(node)
        G.add_edges_from(G_nx.edges())

        print("=== Triadic Census ===")
        print(f"Directed graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

        # Triadic census
        census = nx.triadic_census(G)
        print(f"\nTriadic census (counts of each triad type):")

        # Print all 16 triad types
        triad_names = {
            "003": "003", "012": "012", "102": "102", "021D": "021D",
            "021U": "021U", "021C": "021C", "111D": "111D", "111U": "111U",
            "030T": "030T", "030C": "030C", "201": "201", "120D": "120D",
            "120U": "120U", "120C": "120C", "210": "210", "022H": "022H",
            "022H": "022H", "101H": "101H", "101H": "101H", "012": "012",
        }

        for triad_type in sorted(census.keys()):
            count = census[triad_type]
            bar = "#" * min(count, 50)
            print(f"  {triad_type}: {count:3d} {bar}")

        total_triads = sum(census.values())
        print(f"\nTotal triads: {total_triads}")

        # Show a few example triads
        print("\n=== Example Triads ===")
        nodes = list(G.nodes())
        for i in range(min(3, len(nodes))):
            for j in range(i + 1, len(nodes)):
                for k in range(j + 1, min(j + 4, len(nodes))):
                    triad_nodes = [nodes[i], nodes[j], nodes[k]]
                    edges_in_triad = sum(
                        1 for u, v in G.edges()
                        if u in triad_nodes and v in triad_nodes
                    )
                    if edges_in_triad > 0:
                        subG = G.subgraph(triad_nodes)
                        print(f"  Triad {triad_nodes}: {edges_in_triad} edges, {list(subG.edges())}")

        session.commit()


if __name__ == "__main__":
    demo_triad_types()
