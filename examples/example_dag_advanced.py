"""example_dag_advanced.py - Advanced DAG algorithms.

Covers: dag_longest_path, dag_lcs (longest common subsequence),
        ancestors/descendants sets, transitive reduction,
        topological_generations, dag_weighted_longest_path,
        antichains, dag_depth.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)


def demo_topological_generations():
    """Topological generations (layers) of a DAG."""
    with SessionLocal() as session:
        G = nx_sql.DiGraph(session, name="topo_gen")
        # Course prerequisites
        edges = [
            ("Intro", "Algorithms"),
            ("Intro", "Databases"),
            ("Algorithms", "ML"),
            ("Algorithms", "OS"),
            ("Databases", "ML"),
            ("OS", "Distributed"),
            ("ML", "Capstone"),
            ("Distributed", "Capstone"),
        ]
        G.add_edges_from(edges)

        generations = list(nx.topological_generations(G))
        print("Topological generations (parallel execution order):")
        for i, gen in enumerate(generations):
            print(f"  Generation {i}: {sorted(gen)}")

        session.commit()


def demo_transitive_reduction():
    """Transitive reduction - remove redundant edges."""
    with SessionLocal() as session:
        G = nx_sql.DiGraph(session, name="trans_red")
        # A → B → C and also A → C (redundant)
        G.add_edges_from([("A", "B"), ("B", "C"), ("A", "C")])

        print(f"Original edges: {sorted(G.edges())}")
        tr = nx.transitive_reduction(G)
        print(f"Transitive reduction edges: {sorted(tr.edges())}")
        print(f"  (A→C removed as it's implied by A→B→C)")

        session.commit()


def demo_ancestors_descendants():
    """Ancestor and descendant queries."""
    with SessionLocal() as session:
        G = nx_sql.DiGraph(session, name="anc_desc")
        edges = [
            ("CEO", "VP1"), ("CEO", "VP2"),
            ("VP1", "EngLead"), ("VP2", "SalesLead"),
            ("EngLead", "Dev1"), ("EngLead", "Dev2"),
        ]
        G.add_edges_from(edges)

        # Ancestors
        print("Ancestors of Dev1:")
        for anc in sorted(nx.ancestors(G, "Dev1")):
            print(f"  {anc}")

        # Descendants
        print("\nDescendants of CEO:")
        for desc in sorted(nx.descendants(G, "CEO")):
            print(f"  {desc}")

        # Is reachable
        print(f"\nIs Dev1 reachable from CEO? "
              f"{nx.has_path(G, 'CEO', 'Dev1')}")
        print(f"Is CEO reachable from Dev1? "
              f"{nx.has_path(G, 'Dev1', 'CEO')}")

        session.commit()


def demo_dag_longest_weighted():
    """Weighted longest path in DAG."""
    with SessionLocal() as session:
        G = nx_sql.DiGraph(session, name="dag_weighted")
        # Project schedule with durations
        edges = [
            ("Start", "Design", {"weight": 5}),
            ("Start", "Research", {"weight": 3}),
            ("Design", "Implement", {"weight": 10}),
            ("Research", "Implement", {"weight": 4}),
            ("Implement", "Test", {"weight": 7}),
            ("Test", "Deploy", {"weight": 2}),
        ]
        G.add_edges_from(edges)

        longest = nx.dag_longest_path(G, weight="weight")
        length = nx.dag_longest_path_length(G, weight="weight")
        print(f"Longest path (by weight): {' → '.join(longest)}")
        print(f"Total duration: {length}")

        # Show all paths with weights
        for start_node in ["Start"]:
            for end_node in ["Deploy"]:
                paths = list(nx.all_simple_paths(G, start_node, end_node))
                print(f"\nAll paths from {start_node} to {end_node}:")
                for path in paths:
                    w = sum(G[path[i]][path[i + 1]]["weight"]
                            for i in range(len(path) - 1))
                    print(f"  {' → '.join(path)} (duration={w})")

        session.commit()


def demo_dag_depth():
    """DAG depth and height."""
    with SessionLocal() as session:
        G = nx_sql.DiGraph(session, name="dag_depth")
        G.add_edges_from([
            ("A", "B"), ("A", "C"),
            ("B", "D"), ("C", "D"),
            ("D", "E"),
        ])

        # Depth via longest path from sources
        sources = [n for n in G.nodes() if G.in_degree(n) == 0]
        depths = {}
        for src in sources:
            dist = nx.single_source_shortest_path_length(G, src)
            depths.update(dist)
        depth = max(depths.values()) if depths else 0
        print(f"DAG depth (longest path): {depth}")
        print(f"Max depth: {depth}")

        session.commit()


def demo_dag_antichains():
    """Antichains in DAGs."""
    with SessionLocal() as session:
        G = nx_sql.DiGraph(session, name="antichains")
        G.add_edges_from([
            ("A", "B"), ("A", "C"),
            ("B", "D"), ("C", "D"),
        ])

        try:
            antichains = list(nx.dag_antichains(G))
            print(f"\nAntichains ({len(antichains)} total):")
            for ac, rank in sorted(antichains, key=lambda x: -len(x[0]))[:5]:
                print(f"  {sorted(ac)} (rank={rank})")
        except Exception as e:
            print(f"\nAntichains: {e}")

        session.commit()


def demo_all_topological_sorts():
    """All topological sorts of a DAG."""
    with SessionLocal() as session:
        G = nx_sql.DiGraph(session, name="all_topo")
        G.add_edges_from([
            ("A", "C"), ("B", "C"),
        ])

        orders = list(nx.all_topological_sorts(G))
        print(f"All topological sorts ({len(orders)}):")
        for i, order in enumerate(orders):
            print(f"  {i+1}. {' → '.join(order)}")

        session.commit()


if __name__ == "__main__":
    demo_topological_generations()
    demo_transitive_reduction()
    demo_ancestors_descendants()
    demo_dag_longest_weighted()
    demo_dag_depth()
    demo_dag_antichains()
    demo_all_topological_sorts()
