"""example_connectivity.py - Connectivity, components, and robustness.

Covers: connected_components, articulation_points, bridges,
        edge/node connectivity, condensation, biconnected_components.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)


def demo_articulation_points():
    """Find articulation points (cut vertices)."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="articulation")

        # Bridge graph: A-B-C-D and C-E-F
        edges = [
            ("A", "B"), ("B", "C"), ("C", "D"),
            ("C", "E"), ("E", "F"),
        ]
        G.add_edges_from(edges)

        aps = list(nx.articulation_points(G))
        print("Articulation points:")
        for ap in aps:
            print(f"  {ap} - removing disconnects the graph")

        # Show what happens when removed
        for ap in aps:
            H = G.copy()
            H.remove_node(ap)
            components = list(nx.connected_components(H))
            if len(components) > 1:
                print(f"  After removing {ap}: {len(components)} components: {[sorted(c) for c in components]}")

        session.commit()


def demo_bridges():
    """Find bridges (critical edges)."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="bridges")

        # Graph with a bridge
        edges = [
            ("A", "B"), ("B", "C"), ("C", "A"),  # triangle
            ("C", "D"),  # bridge
            ("D", "E"), ("E", "F"), ("F", "D"),  # triangle
        ]
        G.add_edges_from(edges)

        bridges = list(nx.bridges(G))
        print("Bridges (critical edges):")
        for u, v in bridges:
            print(f"  {u} — {v}")

        # Show impact
        for u, v in bridges:
            H = G.copy()
            H.remove_edge(u, v)
            comps = list(nx.connected_components(H))
            print(f"  Removing ({u},{v}) → {len(comps)} components: {[sorted(c) for c in comps]}")

        session.commit()


def demo_biconnected():
    """Biconnected components."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="biconnected")

        edges = [
            ("A", "B"), ("B", "C"), ("C", "A"),  # component 1
            ("C", "D"),  # articulation at C
            ("D", "E"), ("E", "F"), ("F", "D"),  # component 2
        ]
        G.add_edges_from(edges)

        components = list(nx.biconnected_components(G))
        print("Biconnected components (sets of nodes):")
        for i, comp in enumerate(components, 1):
            print(f"  Component {i}: {sorted(comp)}")

        session.commit()


def demo_dag_condensation():
    """Condense a DAG into SCCs."""
    with SessionLocal() as session:
        G = nx_sql.DiGraph(session, name="condensation")

        # DAG with some cycles for SCC detection
        edges = [
            ("A", "B"), ("B", "C"), ("C", "A"),  # SCC: {A,B,C}
            ("C", "D"),
            ("D", "E"), ("E", "D"),  # SCC: {D,E}
            ("D", "F"),
        ]
        G.add_edges_from(edges)

        sccs = list(nx.strongly_connected_components(G))
        print("Strongly connected components:")
        for i, scc in enumerate(sccs, 1):
            print(f"  SCC {i}: {sorted(scc)}")

        condensation = nx.condensation(G)
        print(f"\nCondensation graph: {condensation.number_of_nodes()} nodes, {condensation.number_of_edges()} edges")
        for u, v in condensation.edges():
            orig_u = G.nodes[condensation.nodes[u]["graph"]]["label"] if "label" in G.nodes.get(list(G.nodes())[0], {}) else u
            print(f"  SCC {u} → SCC {v}")

        session.commit()


def demo_edge_connectivity():
    """Edge and node connectivity."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="connectivity")

        # Build increasingly connected graphs
        # Line graph (fragile)
        line = nx_sql.Graph(session, name="line")
        line.add_edges_from([(i, i + 1) for i in range(5)])
        print(f"Line graph: edge_connectivity={nx.edge_connectivity(line)}, node_connectivity={nx.node_connectivity(line)}")

        # Cycle (more robust)
        cycle = nx_sql.Graph(session, name="cycle")
        cycle.add_edges_from([(i, i + 1) for i in range(5)])
        cycle.add_edge(4, 0)
        print(f"Cycle C5: edge_connectivity={nx.edge_connectivity(cycle)}, node_connectivity={nx.node_connectivity(cycle)}")

        # Complete graph (maximally robust)
        complete = nx_sql.Graph(session, name="complete")
        complete.add_edges_from([(i, j) for i in range(5) for j in range(i + 1, 5)])
        print(f"Complete K5: edge_connectivity={nx.edge_connectivity(complete)}, node_connectivity={nx.node_connectivity(complete)}")

        session.commit()


if __name__ == "__main__":
    demo_articulation_points()
    demo_bridges()
    demo_biconnected()
    demo_dag_condensation()
    demo_edge_connectivity()
