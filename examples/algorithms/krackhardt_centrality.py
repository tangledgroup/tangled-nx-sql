"""Demonstrate multiple centrality measures with nx_sql.

Mirrors networkx/examples/algorithms/plot_krackhardt_centrality.py but uses
SQLAlchemy persistence. Tests betweenness, degree, and closeness centrality
on the Krackhardt kite graph.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def demo_krackhardt_centrality():
    """Compute multiple centrality measures on the Krackhardt kite graph."""

    with Session() as session:
        G_nx = nx.krackhardt_kite_graph()
        G = nx_sql.DiGraph(session, name="krackhardt_demo")
        for n in G_nx.nodes():
            G.add_node(n)
        G.add_edges_from(G_nx.edges())

        print("=== Krackhardt Kite Graph ===")
        print(f"Nodes: {G.number_of_nodes()}")
        print(f"Edges: {G.number_of_edges()}")
        print(f"Graph type: {'Directed' if G.is_directed() else 'Undirected'}")

        # Betweenness centrality
        print("\n=== Betweenness Centrality ===")
        bc = nx.betweenness_centrality(G)
        for node in sorted(bc.keys()):
            print(f"  Node {node}: {bc[node]:.4f}")

        # Degree centrality
        print("\n=== Degree Centrality ===")
        dc = nx.degree_centrality(G)
        for node in sorted(dc.keys()):
            print(f"  Node {node}: {dc[node]:.4f} (degree: {G.degree(node)})")

        # Closeness centrality (may be 0 for disconnected directed graphs)
        print("\n=== Closeness Centrality ===")
        try:
            cc = nx.closeness_centrality(G)
            for node in sorted(cc.keys()):
                print(f"  Node {node}: {cc[node]:.4f}")
        except Exception as e:
            print(f"  (closeness centrality requires strongly connected graph: {e})")

        # Print the graph structure
        print("\n=== Graph Structure ===")
        for node in sorted(G.nodes()):
            succs = list(G.successors(node)) if G.is_directed() else list(G.neighbors(node))
            preds = list(G.predecessors(node)) if G.is_directed() else []
            print(f"  Node {node}: successors={succs}, predecessors={preds}")

        session.commit()


if __name__ == "__main__":
    demo_krackhardt_centrality()
