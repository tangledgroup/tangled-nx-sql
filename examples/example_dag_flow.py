"""example_dag_flow.py - DAG algorithms and network flow.

Covers: topological_sort, longest_path, transitive_closure,
        ancestors/descendants, has_path, condensation.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)


def demo_topological_sort():
    """Topological sorting of a DAG."""
    with SessionLocal() as session:
        G = nx_sql.DiGraph(session, name="topo_sort")

        # Build a course prerequisite graph
        prerequisites = [
            ("Intro", "Algorithms"),
            ("Intro", "Databases"),
            ("Algorithms", "ML"),
            ("Algorithms", "OS"),
            ("Databases", "ML"),
            ("OS", "Distributed"),
            ("ML", "Capstone"),
            ("Distributed", "Capstone"),
        ]
        G.add_edges_from(prerequisites)

        order = list(nx.topological_sort(G))
        print("Topological order (valid course sequence):")
        for i, course in enumerate(order, 1):
            print(f"  {i}. {course}")

        # All topological sorts
        all_orders = list(nx.all_topological_sorts(G))
        print(f"\nTotal valid orderings: {len(all_orders)}")
        if all_orders:
            print(f"First ordering: {all_orders[0]}")

        session.commit()


def demo_longest_path():
    """Longest path in DAG - critical path method."""
    with SessionLocal() as session:
        G = nx_sql.DiGraph(session, name="critical_path")

        # Project tasks with durations
        tasks = [
            ("Requirements", "Design", 5),
            ("Requirements", "Analysis", 3),
            ("Design", "Implementation", 10),
            ("Analysis", "Implementation", 4),
            ("Implementation", "Testing", 7),
            ("Implementation", "CodeReview", 3),
            ("Testing", "Deployment", 2),
            ("CodeReview", "Deployment", 1),
        ]
        G.add_edges_from((u, v, {"duration": d}) for u, v, d in tasks)

        # Critical path
        longest = nx.dag_longest_path(G, weight="duration")
        length = nx.dag_longest_path_length(G, weight="duration")
        print(f"Critical path: {' → '.join(longest)}")
        print(f"Total duration: {length} days")

        # Show all paths from Requirements to Deployment
        paths = list(nx.all_simple_paths(G, "Requirements", "Deployment"))
        print(f"\nAll paths from Requirements to Deployment ({len(paths)}):")
        for path in paths:
            path_len = sum(
                G[u][v]["duration"]
                for u, v in zip(path[:-1], path[1:])
            )
            print(f"  {' → '.join(path)} ({path_len} days)")

        session.commit()


def demo_reachability():
    """Ancestors, descendants, and reachability."""
    with SessionLocal() as session:
        G = nx_sql.DiGraph(session, name="reachability")

        edges = [
            ("CEO", "VP1"), ("CEO", "VP2"),
            ("VP1", "EngLead"), ("VP1", "ProdLead"),
            ("VP2", "SalesLead"),
            ("EngLead", "Dev1"), ("EngLead", "Dev2"),
            ("ProdLead", "Designer"),
        ]
        G.add_edges_from(edges)

        print("Descendants of CEO:")
        desc = nx.descendants(G, "CEO")
        print(f"  {sorted(desc)} ({len(desc)} people)")

        print("\nAncestors of Dev1:")
        anc = nx.ancestors(G, "Dev1")
        print(f"  {sorted(anc)}")

        # Reachability sets
        print("\nReachability from VP1:")
        reachable = nx.descendants(G, "VP1")
        print(f"  Can influence: {sorted(reachable)}")

        # Has path
        print(f"\nCan CEO reach Dev1? {nx.has_path(G, 'CEO', 'Dev1')}")
        print(f"Can SalesLead reach Dev1? {nx.has_path(G, 'SalesLead', 'Dev1')}")

        session.commit()


def demo_transitive_closure():
    """Transitive closure - explicit all-reachability edges."""
    with SessionLocal() as session:
        G = nx_sql.DiGraph(session, name="trans_closure")

        edges = [("A", "B"), ("B", "C"), ("C", "D")]
        G.add_edges_from(edges)

        tc = nx.transitive_closure(G)
        print(f"Original edges: {sorted(G.edges())}")
        print(f"Transitive closure edges ({tc.number_of_edges()}):")
        for u, v in sorted(tc.edges()):
            print(f"  {u} → {v}")

        session.commit()


def demo_dag_properties():
    """DAG-specific properties and operations."""
    with SessionLocal() as session:
        G = nx_sql.DiGraph(session, name="dag_props")

        edges = [
            ("A", "B"), ("A", "C"),
            ("B", "D"), ("C", "D"),
            ("D", "E"),
        ]
        G.add_edges_from(edges)

        # Antichains (sets of mutually unreachable nodes)
        try:
            antichains = list(nx.dag_antichains(G))
            print(f"Antichains ({len(antichains)}):")
            for ac in antichains[:5]:  # Show first 5
                print(f"  {sorted(ac)}")
        except AttributeError:
            print("dag_antichains not available in this NetworkX version")

        # Layers (from topological sort)
        layers = list(nx.topological_generations(G))
        print(f"\nLayers:")
        for i, layer in enumerate(layers):
            print(f"  Layer {i}: {sorted(layer)}")

        session.commit()


if __name__ == "__main__":
    demo_topological_sort()
    demo_longest_path()
    demo_reachability()
    demo_transitive_closure()
    demo_dag_properties()
