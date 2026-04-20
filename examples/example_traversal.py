"""example_traversal.py - Graph traversal and tree algorithms.

Covers: BFS, DFS, beam search, edge traversal (tree/back/forward/cross),
        spanning trees, arborescences, Prufer sequences, nested tuples,
        junction trees, predecessors/successors/layers.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)


def demo_bfs():
    """Breadth-first search traversal."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="bfs_tree")
        edges = [
            ("root", "A"), ("root", "B"),
            ("A", "C"), ("A", "D"),
            ("B", "E"), ("B", "F"),
            ("C", "G"),
        ]
        G.add_edges_from(edges)

        # BFS tree
        bfs_t = nx.bfs_tree(G, "root")
        print("BFS tree nodes:")
        for n in sorted(bfs_t.nodes()):
            print(f"  {n}")
        print(f"BFS tree edges: {sorted(bfs_t.edges())}")

        # BFS predecessors
        pred = nx.bfs_predecessors(G, "root")
        print(f"\nBFS predecessors from root: {dict(pred)}")

        # BFS successors
        succ = nx.bfs_successors(G, "root")
        print(f"BFS successors from root: {dict(succ)}")

        # BFS on DiGraph
        D = nx_sql.DiGraph(session, name="bfs_digraph")
        D.add_edges_from([
            ("A", "B"), ("A", "C"),
            ("B", "D"), ("B", "E"),
            ("C", "F"),
        ])
        bfs_t = nx.bfs_tree(D, "A")
        print(f"\nDiGraph BFS tree from A: {sorted(bfs_t.nodes())}")

        session.commit()


def demo_dfs():
    """Depth-first search traversal."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="dfs_tree")
        edges = [
            ("root", "A"), ("root", "B"),
            ("A", "C"), ("A", "D"),
            ("B", "E"),
        ]
        G.add_edges_from(edges)

        # DFS tree
        dfs_t = nx.dfs_tree(G, "root")
        print("DFS tree nodes:")
        for n in sorted(dfs_t.nodes()):
            print(f"  {n}")

        # DFS edges (plain NetworkX doesn't return etype by default)
        print("\nDFS edges from root:")
        for u, v in nx.dfs_edges(G, "root"):
            print(f"  {u} → {v}")

        # DFS on DiGraph
        D = nx_sql.DiGraph(session, name="dfs_digraph")
        D.add_edges_from([
            ("A", "B"), ("A", "C"), ("B", "D"), ("C", "B"),
        ])
        print("\nDiGraph DFS edges from A:")
        for u, v in nx.dfs_edges(D, "A"):
            print(f"  {u} → {v}")

        session.commit()


def demo_beam_search():
    """Beam search traversal."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="beam_search")
        G.add_edges_from([
            ("A", "B"), ("A", "C"), ("A", "D"),
            ("B", "E"), ("B", "F"),
            ("C", "G"),
        ])

        # Beam search with width=2 (use plain copy for beam_search_edges)
        G_plain = nx.Graph(G)
        try:
            beam = list(nx.beam_search_edges(G_plain, "A", width=2))
            print("Beam search edges (width=2):")
            for u, v in beam:
                print(f"  {u} → {v}")
        except AttributeError:
            print("Beam search not available in this NetworkX version")

        session.commit()


def demo_spanning_trees():
    """Spanning trees and arborescences."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="spanning")
        G.add_edges_from([
            (1, 2), (2, 3), (3, 4),
            (1, 3), (2, 4),
        ])

        # Random spanning tree
        st = nx.random_spanning_tree(G)
        print(f"Random spanning tree: {st.number_of_nodes()} nodes, "
              f"{st.number_of_edges()} edges")
        print(f"Edges: {sorted(st.edges())}")

        # Number of spanning trees (for small graphs)
        n_st = nx.number_of_spanning_trees(G)
        print(f"\nTotal spanning trees: {n_st}")

        session.commit()


def demo_arborescences():
    """Branchings and arborescences in directed graphs."""
    with SessionLocal() as session:
        G = nx_sql.DiGraph(session, name="arborescence")
        G.add_edges_from([
            ("root", "A"), ("root", "B"),
            ("A", "C"), ("B", "C"),
            ("A", "D"), ("B", "D"),
        ])

        # Maximum arborescence (directed spanning tree)
        try:
            G_plain = nx.DiGraph(G)
            max_arb = nx.maximum_branching(G_plain)
            print(f"Maximum arborescence from root:")
            for u, v in sorted(max_arb.edges()):
                print(f"  {u} → {v}")
        except nx.NetworkXError as e:
            print(f"No arborescence: {e}")

        # Minimum branching
        try:
            min_br = nx.minimum_branching(G_plain)
            print(f"\nMinimum branching from root:")
            for u, v in sorted(min_br.edges()):
                print(f"  {u} → {v}")
        except nx.NetworkXError as e:
            print(f"No branching: {e}")

        session.commit()


def demo_tree_structures():
    """Tree-specific structures: Prufer, nested tuples, junction trees."""
    with SessionLocal() as session:
        # Prufer sequence from tree
        G = nx_sql.Graph(session, name="prufer")
        G.add_edges_from([(1, 2), (2, 3), (3, 4), (4, 5)])

        try:
            prufer = nx.tree_atlas(G)
            print(f"Prufer-like structure: {list(G.edges())}")
        except Exception as e:
            print(f"Prufer: {e}")

        # Nested tuples representation
        try:
            nested = nx.nested_tuple_repr(G)
            print(f"Nested tuple repr: {nested}")
        except Exception as e:
            print(f"Nested tuples: {e}")

        # Junction tree
        try:
            jt = nx.junction_tree(G)
            print(f"\nJunction tree nodes: {jt.number_of_nodes()}")
            print(f"Junction tree edges: {jt.number_of_edges()}")
        except Exception as e:
            print(f"Junction tree: {e}")

        session.commit()


def demo_predecessors_successors():
    """Predecessor and successor queries."""
    with SessionLocal() as session:
        G = nx_sql.DiGraph(session, name="pred_succ")
        G.add_edges_from([
            ("A", "B"), ("A", "C"),
            ("B", "D"), ("B", "E"),
            ("C", "F"),
        ])

        # Successors of A (use G.successors method)
        succ = list(G.successors("A"))
        print(f"Successors of A: {succ}")

        # Predecessors of E (use G.predecessors method)
        pred = list(G.predecessors("E"))
        print(f"Predecessors of E: {pred}")

        # Layers from source (use bfs_layers)
        layers = list(nx.bfs_layers(G, "A"))
        print("\nLayers from A:")
        for i, layer in enumerate(layers):
            print(f"  Layer {i}: {sorted(layer)}")

        session.commit()


def demo_edge_traversal():
    """Edge-based traversal with edge types."""
    with SessionLocal() as session:
        G = nx_sql.DiGraph(session, name="edge_trav")
        G.add_edges_from([
            ("A", "B"), ("B", "C"),
            ("A", "C"),  # cross edge in DFS
        ])

        print("DFS edges from A:")
        for u, v in nx.dfs_edges(G, "A"):
            print(f"  {u} → {v}")

        session.commit()


if __name__ == "__main__":
    demo_bfs()
    demo_dfs()
    demo_beam_search()
    demo_spanning_trees()
    demo_arborescences()
    demo_tree_structures()
    demo_predecessors_successors()
    demo_edge_traversal()
