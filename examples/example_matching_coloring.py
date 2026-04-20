"""example_matching_coloring.py - Matching, coloring, and domination.

Covers: maximum_weight_matching, bipartite matching, vertex cover,
        independent set, graph coloring (greedy + strategies),
        dominating set, edge cover, maximal independent set.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)


def demo_maximum_matching():
    """Maximum cardinality and weight matching."""
    with SessionLocal() as session:
        # Workers → Tasks bipartite matching
        G = nx_sql.Graph(session, name="matching_workers")

        workers = ["Alice", "Bob", "Carol"]
        tasks = ["Coding", "Testing", "Design"]

        edges = [
            ("Alice", "Coding"), ("Alice", "Testing"),
            ("Bob", "Coding"), ("Bob", "Design"),
            ("Carol", "Testing"), ("Carol", "Design"),
        ]
        G.add_edges_from(edges)

        # Maximum cardinality matching
        matching = nx.max_weight_matching(G, maxcardinality=True)
        print("Maximum cardinality matching:")
        for w, t in sorted(matching):
            print(f"  {w} → {t}")
        print(f"  Matched: {len(matching)}/{min(len(workers), len(tasks))} pairs")

        # Maximum weight matching
        G2 = nx_sql.Graph(session, name="matching_weighted")
        G2.add_edge("Alice", "Coding", weight=10)
        G2.add_edge("Alice", "Testing", weight=5)
        G2.add_edge("Bob", "Coding", weight=7)
        G2.add_edge("Bob", "Design", weight=8)
        G2.add_edge("Carol", "Testing", weight=9)
        G2.add_edge("Carol", "Design", weight=6)

        matching = nx.max_weight_matching(G2, maxcardinality=True)
        print(f"\nMax weight matching: {matching}")
        total_weight = sum(G2[w][t]["weight"] for w, t in matching)
        print(f"  Total weight: {total_weight}")

        session.commit()


def demo_bipartite_matching():
    """Bipartite-specific matching algorithms."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="bipartite_match")
        G.add_edges_from([
            (0, 3), (0, 4), (1, 3), (1, 5), (2, 4), (2, 5),
        ])

        is_bip = nx.is_bipartite(G)
        print(f"Is bipartite: {is_bip}")
        if is_bip:
            sets = nx.bipartite.sets(G)
            print(f"Left set: {sorted(sets[0])}")
            print(f"Right set: {sorted(sets[1])}")

        matching = nx.bipartite.maximum_matching(G)
        print(f"\nMaximum matching: {matching}")
        # Deduplicate (each pair appears twice)
        matching_pairs = set()
        for u, v in matching.items():
            pair = tuple(sorted([u, v]))
            matching_pairs.add(pair)
        print(f"Matched pairs: {sorted(matching_pairs)}")

        session.commit()


def demo_vertex_cover_independent_set():
    """Vertex cover and independent set."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="vertex_cover")
        G.add_edges_from([
            (1, 2), (2, 3), (3, 4), (4, 5),
            (1, 3), (2, 4),
        ])

        # Maximum independent set (use plain copy for approximation algos)
        G_plain = nx.Graph(G)
        indep = nx.algorithms.approximation.maximum_independent_set(G_plain)
        print(f"Maximum independent set: {sorted(indep)}")

        # Minimum vertex cover (complement of max independent set)
        vc = nx.algorithms.approximation.min_weighted_vertex_cover(G_plain)
        print(f"Minimum vertex cover: {sorted(vc)}")

        # Maximum matching → minimum vertex cover (Konig's theorem for bipartite)
        matching = nx.max_weight_matching(G, maxcardinality=True)
        print(f"\nMaximum matching: {matching}")
        print(f"|VC| + |IS| = {len(vc)} + {len(indep)} = {len(vc) + len(indep)} "
              f"(should be ≤ n={G.number_of_nodes()})")

        session.commit()


def demo_graph_coloring():
    """Graph coloring with various strategies."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="coloring_map")
        # US states adjacency
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

        strategies = ["largest_first", "random_sequential", "smallest_last",
                       "minimum_degree", "connected_sequential_bfs",
                       "connected_sequential_dfs", "dsatur"]

        print("Graph coloring strategies:")
        for strategy in strategies:
            try:
                coloring = nx.coloring.greedy_color(G, strategy=strategy)
                n_colors = max(coloring.values()) + 1 if coloring else 0
                print(f"  {strategy}: {n_colors} colors")
            except Exception as e:
                print(f"  {strategy}: ERROR - {e}")

        # Show one coloring
        coloring = nx.coloring.greedy_color(G, strategy="largest_first")
        print(f"\nColoring (largest_first):")
        for node, color in sorted(coloring.items()):
            print(f"  {node}: color={color}")

        session.commit()


def demo_dominating_set():
    """Dominating sets and edge covers."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="dominating")
        # Star graph: center dominates all
        G.add_edges_from([(0, i) for i in range(1, 6)])

        # Dominating set
        from networkx.algorithms.approximation.dominating_set import min_weighted_dominating_set
        ds = min_weighted_dominating_set(G)
        print(f"Dominating set (star): {sorted(ds)}")
        # Verify: every node is either in DS or adjacent to a node in DS
        for node in G.nodes():
            if node not in ds:
                neighbors_in_ds = [n for n in G.neighbors(node) if n in ds]
                assert neighbors_in_ds, f"Node {node} not dominated!"
        print(f"  All nodes dominated: ✓")

        # Edge cover
        ec = nx.min_edge_cover(G)
        print(f"\nMin edge cover: {sorted(ec)}")

        # Independent set (using plain copy for approximation)
        G_plain2 = nx.Graph(G)
        mis = nx.algorithms.approximation.maximum_independent_set(G_plain2)
        print(f"Independent set: {sorted(mis)}")

        session.commit()


def demo_bipartite_projections():
    """Bipartite projections and weighted projections."""
    with SessionLocal() as session:
        # Author → Paper bipartite graph
        G = nx_sql.Graph(session, name="bipartite_proj")
        G.add_edge("Alice", "Paper1")
        G.add_edge("Alice", "Paper2")
        G.add_edge("Bob", "Paper2")
        G.add_edge("Bob", "Paper3")
        G.add_edge("Carol", "Paper3")
        G.add_edge("Carol", "Paper4")

        # One-mode projection (authors who co-authored)
        proj = nx.bipartite.weighted_projected_graph(G, ["Alice", "Bob", "Carol"])
        print(f"\nAuthor collaboration graph:")
        for u, v, d in sorted(proj.edges(data=True)):
            print(f"  {u} — {v}: co-authored {d['weight']} paper(s)")

        session.commit()


if __name__ == "__main__":
    demo_maximum_matching()
    demo_bipartite_matching()
    demo_vertex_cover_independent_set()
    demo_graph_coloring()
    demo_dominating_set()
    demo_bipartite_projections()
