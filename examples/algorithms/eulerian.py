"""Demonstrate Eulerian path/circuit with nx_sql.

Tests finding Eulerian circuits and paths — trails that visit every edge
exactly once. An undirected graph has an Eulerian circuit iff all vertices
have even degree and the graph is connected.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def demo_eulerian():
    """Test Eulerian path and circuit detection."""

    with Session() as session:
        # Eulerian circuit: all nodes have even degree
        print(f"=== Eulerian Circuit ===")
        G_circuit_nx = nx.Graph()
        G_circuit_nx.add_edges_from([(0, 1), (1, 2), (2, 0), (0, 3), (3, 4), (4, 0)])
        # Degrees: 0=4, 1=2, 2=2, 3=2, 4=2 — all even
        G_circuit = nx_sql.Graph(session, name="eulerian_circuit_demo")
        G_circuit.add_nodes_from(G_circuit_nx.nodes())
        G_circuit.add_edges_from(G_circuit_nx.edges())

        print(f"Graph: {G_circuit.number_of_nodes()} nodes, {G_circuit.number_of_edges()} edges")
        print(f"Degrees: {dict(G_circuit.degree())}")
        print(f"Is Eulerian: {nx.is_eulerian(G_circuit)}")

        if nx.is_eulerian(G_circuit):
            circuit = list(nx.eulerian_circuit(G_circuit))
            print(f"Eulerian circuit ({len(circuit)} edges):")
            edge_strs = [f"({u},{v})" for u, v in circuit]
            print(f"  {' -> '.join(edge_strs)}")

        # Eulerian path: exactly 0 or 2 nodes with odd degree
        print(f"\n=== Eulerian Path ===")
        G_path_nx = nx.Graph()
        G_path_nx.add_edges_from([(0, 1), (1, 2), (2, 3)])
        # Degrees: 0=1, 1=2, 2=2, 3=1 — exactly 2 odd-degree nodes
        G_path = nx_sql.Graph(session, name="eulerian_path_demo")
        G_path.add_nodes_from(G_path_nx.nodes())
        G_path.add_edges_from(G_path_nx.edges())

        print(f"Graph: {G_path.number_of_nodes()} nodes, {G_path.number_of_edges()} edges")
        print(f"Degrees: {dict(G_path.degree())}")
        odd_degree_nodes = [n for n, d in G_path.degree() if d % 2 == 1]
        print(f"Odd-degree nodes: {odd_degree_nodes} (count={len(odd_degree_nodes)})")
        print(f"Is Eulerian: {nx.is_eulerian(G_path)}")

        # Not Eulerian — has odd degree nodes
        if not nx.is_eulerian(G_path):
            print("  (Not Eulerian — has 2 odd-degree nodes, so only a path exists)")

        # Non-Eulerian graph
        print(f"\n=== Non-Eulerian Graph ===")
        G_non = nx_sql.Graph(session, name="eulerian_non_demo")
        G_non.add_edges_from([(0, 1), (1, 2), (2, 3), (3, 4)])
        # Degrees: 0=1, 1=2, 2=2, 3=2, 4=1 — still 2 odd
        # Add one more edge to make it non-Eulerian
        G_non.add_edge(0, 2)
        print(f"Degrees: {dict(G_non.degree())}")
        odd_nodes = [n for n, d in G_non.degree() if d % 2 == 1]
        print(f"Odd-degree nodes: {odd_nodes} (count={len(odd_nodes)})")
        print(f"Is Eulerian: {nx.is_eulerian(G_non)}")

        session.commit()


if __name__ == "__main__":
    demo_eulerian()
