"""Demonstrate lowest common ancestor with nx_sql.

Mirrors networkx/examples/algorithms/plot_lca.py but uses
SQLAlchemy persistence. Tests LCA on directed acyclic graphs.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def demo_lca():
    """Compute lowest common ancestors in a DAG."""

    with Session() as session:
        # Build a DAG (family tree / dependency graph)
        G_nx = nx.DiGraph()
        edges = [
            ("root", "A"), ("root", "B"),
            ("A", "C"), ("A", "D"),
            ("B", "D"), ("B", "E"),
            ("C", "F"), ("D", "F"), ("D", "G"),
            ("E", "G"), ("E", "H"),
        ]
        G_nx.add_edges_from(edges)

        G = nx_sql.DiGraph(session, name="lca_demo")
        for node in G_nx.nodes():
            G.add_node(node)
        G.add_edges_from(G_nx.edges())

        print("=== Lowest Common Ancestor ===")
        print(f"DAG: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

        # Verify it's a DAG
        assert nx.is_directed_acyclic_graph(G), "Graph must be a DAG"
        print("Verified: Graph is a DAG ✓")

        # Single pair LCA
        print("\n=== Single Pair LCA ===")
        pairs = [("F", "G"), ("C", "H"), ("F", "H"), ("A", "B")]
        for u, v in pairs:
            lca = nx.lowest_common_ancestor(G, u, v)
            print(f"  LCA({u}, {v}) = {lca}")

        # All pairs LCA
        print("\n=== All Pairs LCA ===")
        all_lca = dict(nx.all_pairs_lowest_common_ancestor(G))
        nodes = sorted(G.nodes())
        for u in nodes:
            for v in nodes:
                if u < v and (u, v) in all_lca:
                    lca = all_lca[(u, v)]
                    print(f"  LCA({u}, {v}) = {lca}")

        # Visualize the tree structure
        print("\n=== Tree Structure ===")
        topo_order = list(nx.topological_sort(G))
        for node in topo_order:
            preds = sorted(G.predecessors(node))
            succs = sorted(G.successors(node))
            pred_str = f" <- {', '.join(preds)}" if preds else ""
            succ_str = f" -> {', '.join(succs)}" if succs else ""
            print(f"  {node}{pred_str}{succ_str}")

        session.commit()


if __name__ == "__main__":
    demo_lca()
