"""Demonstrate condensation with nx_sql.

Tests condensation of strongly connected components (SCCs) and weakly
connected components into a condensed DAG/graph where each SCC is a single node.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def demo_condensation():
    """Condense SCCs and weakly connected components."""

    with Session() as session:
        # Create a directed graph with clear SCC structure
        G_nx = nx.DiGraph()
        # Cycle 1: A -> B -> C -> A
        G_nx.add_edges_from([('A', 'B'), ('B', 'C'), ('C', 'A')])
        # Cycle 2: D -> E -> F -> D
        G_nx.add_edges_from([('D', 'E'), ('E', 'F'), ('F', 'D')])
        # Bridge between cycles
        G_nx.add_edge('C', 'D')
        # Isolated cycle
        G_nx.add_edges_from([('G', 'H'), ('H', 'G')])

        G = nx_sql.DiGraph(session, name="condensation_demo")
        G.add_nodes_from(G_nx.nodes())
        G.add_edges_from(G_nx.edges())

        print(f"=== Condensation ===")
        print(f"Original graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        print(f"Edges: {list(G.edges())}")

        # Strongly connected components
        sccs = list(nx.strongly_connected_components(G))
        print(f"\nStrongly connected components ({len(sccs)}):")
        for i, scc in enumerate(sorted(sccs, key=len, reverse=True)):
            print(f"  SCC {i+1}: {sorted(scc)}")

        # Condensation graph (SCCs → DAG)
        cond = nx.condensation(G)
        print(f"\nCondensation graph: {cond.number_of_nodes()} nodes, {cond.number_of_edges()} edges")
        print(f"Node mapping:")
        for node in cond.nodes():
            original = list(cond.nodes[node].get('nodes', []))
            print(f"  Condensed node {node}: original nodes = {original}")
        print(f"Condensation edges: {list(cond.edges())}")

        # Weakly connected components
        wccs = list(nx.weakly_connected_components(G))
        print(f"\nWeakly connected components ({len(wccs)}):")
        for i, wcc in enumerate(sorted(wccs, key=len, reverse=True)):
            print(f"  WCC {i+1}: {sorted(wcc)}")

        # Get the mapping from original nodes to SCC indices
        mapping = cond.nodes[0].get('members', []) if cond.number_of_nodes() > 0 else []
        scc_list = list(nx.strongly_connected_components(G))
        print(f"\nSCC membership:")
        for i, scc in enumerate(scc_list):
            print(f"  SCC {i}: {sorted(scc)}")

        session.commit()


if __name__ == "__main__":
    demo_condensation()
