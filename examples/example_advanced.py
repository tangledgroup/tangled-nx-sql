"""example_advanced.py - Advanced NetworkX algorithms with nx_sql.

Covers: max_flow, matching, coloring, isomorphism (VF2),
        simple_paths, eulerian paths, graph generators.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)


def demo_max_flow():
    """Maximum flow and min-cut.

    Note: Max flow algorithms modify edge capacities in-place (adding
    residual edges), which requires mutable storage. Use plain NetworkX
    for this operation rather than nx_sql's DB-backed graphs.
    """
    G = nx.DiGraph()
    edges = [
        ("s", "A", 10), ("s", "B", 8),
        ("A", "C", 5), ("A", "D", 7),
        ("B", "D", 6), ("B", "E", 4),
        ("C", "t", 6), ("D", "t", 9),
        ("E", "t", 3),
    ]
    G.add_edges_from((u, v, {"capacity": c}) for u, v, c in edges)

    flow_value, flow_dict = nx.maximum_flow(G, "s", "t", capacity="capacity")
    print(f"Max flow: {flow_value}")
    print("Flow distribution:")
    for u in flow_dict:
        for v in flow_dict[u]:
            if flow_dict[u][v] > 0:
                cap = G[u][v]["capacity"]
                print(f"  {u} → {v}: {flow_dict[u][v]}/{cap}")

    cut_value, partition = nx.minimum_cut(G, "s", "t", capacity="capacity")
    print(f"\nMin-cut value: {cut_value}")
    print(f"Partition: S={partition[0]}, T={partition[1]}")


def demo_matching():
    """Maximum matching in bipartite graphs."""
    with SessionLocal() as session:
        # Workers → Tasks
        G = nx_sql.Graph(session, name="matching")

        workers = ["Alice", "Bob", "Carol"]
        tasks = ["Coding", "Testing", "Design"]

        # Alice can code or test
        G.add_edge("Alice", "Coding")
        G.add_edge("Alice", "Testing")
        # Bob can code or design
        G.add_edge("Bob", "Coding")
        G.add_edge("Bob", "Design")
        # Carol can test or design
        G.add_edge("Carol", "Testing")
        G.add_edge("Carol", "Design")

        matching = nx.max_weight_matching(G, maxcardinality=True)
        print("Maximum matching:")
        for w, t in sorted(matching):
            print(f"  {w} → {t}")
        print(f"Matched: {len(matching)}/{min(len(workers), len(tasks))} pairs")

        session.commit()


def demo_graph_coloring():
    """Graph coloring - minimum colors for valid assignment."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="coloring")

        # Map coloring problem
        edges = [
            ("WA", "OR"), ("WA", "ID"),
            ("OR", "CA"), ("OR", "NV"), ("OR", "ID"),
            ("CA", "NV"),
            ("NV", "UT"), ("NV", "AZ"),
            ("ID", "MT"), ("ID", "WY"), ("ID", "UT"),
            ("UT", "CO"), ("UT", "AZ"),
            ("CA", "AZ"),
        ]
        G.add_edges_from(edges)

        coloring = nx.coloring.greedy_color(G, strategy="largest_first")
        print("Graph coloring (states → colors):")
        for node, color in sorted(coloring.items()):
            print(f"  {node}: color={color}")
        print(f"\nColors used: {max(coloring.values()) + 1}")

        session.commit()


def demo_simple_paths():
    """All simple paths between nodes."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="simple_paths")

        edges = [
            (1, 2), (1, 3), (2, 4), (3, 4),
            (2, 5), (4, 5), (5, 6),
        ]
        G.add_edges_from(edges)

        # All simple paths from 1 to 6
        paths = list(nx.all_simple_paths(G, 1, 6))
        print(f"All simple paths from 1 to 6 ({len(paths)}):")
        for p in paths:
            print(f"  {' → '.join(map(str, p))} (length {len(p) - 1})")

        # With depth limit
        limited = list(nx.all_simple_paths(G, 1, 6, cutoff=3))
        print(f"\nPaths with max length 3 ({len(limited)}):")
        for p in limited:
            print(f"  {' → '.join(map(str, p))}")

        session.commit()


def demo_eulerian():
    """Eulerian paths and circuits."""
    with SessionLocal() as session:
        # Eulerian circuit (all even degrees)
        G = nx_sql.Graph(session, name="eulerian")
        edges = [(1, 2), (2, 3), (3, 4), (4, 1), (1, 3), (2, 4)]
        G.add_edges_from(edges)

        print(f"All degrees even: {all(d % 2 == 0 for n, d in G.degree())}")
        try:
            circuit = list(nx.eulerian_circuit(G))
            print(f"Eulerian circuit: {[n for n, _ in circuit]} → {circuit[0][0]}")
        except nx.NetworkXError:
            print("No Eulerian circuit")

        # Eulerian path (exactly 2 odd-degree nodes)
        G2 = nx_sql.Graph(session, name="eulerian_path")
        edges2 = [(1, 2), (2, 3), (3, 4)]
        G2.add_edges_from(edges2)

        odd_nodes = [n for n, d in G2.degree() if d % 2 == 1]
        print(f"\nOdd-degree nodes: {odd_nodes}")
        try:
            path = list(nx.eulerian_path(G2))
            print(f"Eulerian path: {[n for n, _ in path]}")
        except nx.NetworkXError:
            print("No Eulerian path")

        session.commit()


def demo_generators():
    """Use NetworkX graph generators with nx_sql storage."""
    with SessionLocal() as session:
        # Create a graph from a generator, then store in DB
        G_template = nx.barabasi_albert_graph(n=20, m=3, seed=42)

        G = nx_sql.Graph(session, name="ba_network")
        G.add_nodes_from(G_template.nodes())
        G.add_edges_from(G_template.edges())

        print(f"Barabási-Albert network (n=20, m=3):")
        print(f"  Nodes: {G.number_of_nodes()}")
        print(f"  Edges: {G.number_of_edges()}")
        print(f"  Avg degree: {2 * G.number_of_edges() / G.number_of_nodes():.2f}")
        print(f"  Clustering: {nx.average_clustering(G):.4f}")

        # Power-law degree distribution check
        degrees = [d for n, d in G.degree()]
        print(f"  Min degree: {min(degrees)}")
        print(f"  Max degree: {max(degrees)}")
        print(f"  Hub node: {max(G.degree(), key=lambda x: x[1])}")

        session.commit()


if __name__ == "__main__":
    demo_max_flow()
    demo_matching()
    demo_graph_coloring()
    demo_simple_paths()
    demo_eulerian()
    demo_generators()
