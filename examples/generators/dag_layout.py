"""Demonstrate DAG topological layout with nx_sql.

Mirrors networkx/examples/graph/plot_dag_layout.py but uses
SQLAlchemy persistence. Tests topological sort and generations.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def demo_dag_layout():
    """Create a DAG and compute topological ordering."""

    with Session() as session:
        # Create a dependency DAG
        G_nx = nx.DiGraph()
        # Build a simple task dependency graph
        dependencies = [
            ("install", "compile"),
            ("install", "test"),
            ("compile", "link"),
            ("compile", "test"),
            ("link", "package"),
            ("test", "package"),
            ("package", "deploy"),
            ("install", "lint"),
            ("lint", "package"),
        ]
        G_nx.add_edges_from(dependencies)

        G = nx_sql.DiGraph(session, name="dag_demo")
        for node in G_nx.nodes():
            G.add_node(node)
        G.add_edges_from(G_nx.edges())

        print("=== DAG Topological Layout ===")
        print(f"Nodes: {G.number_of_nodes()}")
        print(f"Edges: {G.number_of_edges()}")

        # Verify it's a DAG
        is_dag = nx.is_directed_acyclic_graph(G)
        print(f"Is DAG: {is_dag}")

        # Topological sort
        topo_order = list(nx.topological_sort(G))
        print(f"\nTopological order:")
        for i, node in enumerate(topo_order):
            deps = list(G.predecessors(node))
            print(f"  {i+1}. {node} (depends on: {', '.join(deps) if deps else 'none'})")

        # Topological generations
        print(f"\nTopological generations:")
        for i, generation in enumerate(nx.topological_generations(G)):
            nodes_in_gen = list(generation)
            print(f"  Generation {i}: {nodes_in_gen}")

        # Longest path
        print("\n=== Dependency Analysis ===")
        for node in topo_order:
            preds = list(G.predecessors(node))
            succs = list(G.successors(node))
            print(f"  {node}: {len(preds)} predecessors, {len(succs)} successors")

        session.commit()


if __name__ == "__main__":
    demo_dag_layout()
