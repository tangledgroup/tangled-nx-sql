"""example_isomorphism.py - Graph isomorphism and subgraph matching.

Covers: is_isomorphic, GraphMatcher (VF2++), subgraph_isomorphism,
        monomorphisms, edge_coloring isomorphism, Weisfeiler-Lehman hash,
        tree isomorphism, graph hashing.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)


def demo_is_isomorphic():
    """Check if two graphs are isomorphic."""
    with SessionLocal() as session:
        G1 = nx_sql.Graph(session, name="iso_1")
        G1.add_edges_from([(1, 2), (2, 3), (3, 4)])

        G2 = nx_sql.Graph(session, name="iso_2")
        G2.add_edges_from([("A", "B"), ("B", "C"), ("C", "D")])

        G3 = nx_sql.Graph(session, name="iso_3")
        G3.add_edges_from([(1, 2), (2, 3), (1, 3)])  # triangle

        print(f"Path4 ≅ Path4 (different labels): "
              f"{nx.is_isomorphic(G1, G2)}")
        print(f"Path4 ≅ Triangle: {nx.is_isomorphic(G1, G3)}")

        # With node match
        G4 = nx_sql.Graph(session, name="iso_4")
        G4.add_edges_from([(1, 2), (2, 3)])
        G4.nodes[1]["label"] = "start"
        G4.nodes[2]["label"] = "mid"
        G4.nodes[3]["label"] = "end"

        G5 = nx_sql.Graph(session, name="iso_5")
        G5.add_edges_from([(10, 20), (20, 30)])
        G5.nodes[10]["label"] = "start"
        G5.nodes[20]["label"] = "mid"
        G5.nodes[30]["label"] = "end"

        def node_match(n1, n2):
            return n1.get("label") == n2.get("label")

        print(f"\nWith label matching: {nx.is_isomorphic(G4, G5, node_match=node_match)}")

        session.commit()


def demo_graph_matcher():
    """GraphMatcher (VF2++) for detailed isomorphism analysis."""
    with SessionLocal() as session:
        G1 = nx_sql.Graph(session, name="gm_1")
        G1.add_edges_from([(1, 2), (2, 3), (3, 4), (4, 1)])  # C4

        G2 = nx_sql.Graph(session, name="gm_2")
        G2.add_edges_from([(10, 20), (20, 30), (30, 40), (40, 50)])  # P4

        matcher = nx.algorithms.isomorphism.GraphMatcher(G1, G2)
        print(f"C4 ≅ P4: {matcher.subgraph_isomorphisms_iter().__next__() if list(matcher.subgraph_isomorphisms_iter()) else 'No'}")
        print(f"Isomorphic: {matcher.is_isomorphic()}")

        session.commit()


def demo_subgraph_isomorphism():
    """Find subgraph isomorphisms."""
    with SessionLocal() as session:
        # Large graph
        large = nx_sql.Graph(session, name="sub_large")
        large.add_edges_from([
            (1, 2), (2, 3), (3, 4), (4, 5),
            (5, 1), (1, 3), (3, 5),
        ])

        # Pattern: triangle
        pattern = nx_sql.Graph(session, name="sub_tri")
        pattern.add_edges_from([(1, 2), (2, 3), (3, 1)])

        matcher = nx.algorithms.isomorphism.GraphMatcher(large, pattern)
        subgraphs = list(matcher.subgraph_isomorphisms_iter())
        print(f"\nTriangles in large graph ({len(subgraphs)} found):")
        for mapping in subgraphs:
            nodes = sorted(mapping.keys())
            print(f"  {nodes}")

        session.commit()


def demo_edge_color_isomorphism():
    """Edge-colored graph isomorphism."""
    with SessionLocal() as session:
        G1 = nx_sql.Graph(session, name="edge_iso_1")
        G1.add_edges_from([(1, 2), (2, 3), (3, 1)])
        G1[1][2]["color"] = "red"
        G1[2][3]["color"] = "blue"
        G1[3][1]["color"] = "red"

        G2 = nx_sql.Graph(session, name="edge_iso_2")
        G2.add_edges_from([(1, 2), (2, 3), (3, 1)])
        G2[1][2]["color"] = "blue"
        G2[2][3]["color"] = "red"
        G2[3][1]["color"] = "blue"

        def edge_match(e1, e2):
            return e1.get("color") == e2.get("color")

        print(f"\nEdge-colored graphs isomorphic: "
              f"{nx.is_isomorphic(G1, G2, edge_match=edge_match)}")

        session.commit()


def demo_weisfeiler_lehman():
    """Weisfeiler-Lehman graph hashing."""
    with SessionLocal() as session:
        G1 = nx_sql.Graph(session, name="wl_1")
        G1.add_edges_from([(1, 2), (2, 3), (3, 1)])  # triangle

        G2 = nx_sql.Graph(session, name="wl_2")
        G2.add_edges_from([(1, 2), (2, 3), (3, 4)])  # path

        G3 = nx_sql.Graph(session, name="wl_3")
        G3.add_edges_from([(1, 2), (2, 3), (3, 1)])  # triangle (same as G1)

        # Weisfeiler-Lehman hash
        h1 = nx.weisfeiler_lehman_graph_hash(G1)
        h2 = nx.weisfeiler_lehman_graph_hash(G2)
        h3 = nx.weisfeiler_lehman_graph_hash(G3)

        print(f"\nWL hashes:")
        print(f"  Triangle (G1): {h1}")
        print(f"  Path (G2):     {h2}")
        print(f"  Triangle (G3): {h3}")
        print(f"  G1 ≅ G3 (same hash): {h1 == h3}")
        print(f"  G1 ≇ G2 (different hash): {h1 != h2}")

        session.commit()


def demo_tree_isomorphism():
    """Tree isomorphism."""
    with SessionLocal() as session:
        # Two identical binary trees
        t1 = nx.balanced_tree(2, 2)
        t2 = nx.balanced_tree(2, 2)

        # Relabel differently
        mapping = {n: f"t1_{n}" for n in t1.nodes()}
        t1_relabel = nx.relabel_nodes(t1, mapping, copy=True)

        mapping2 = {n: f"t2_{n}" for n in t2.nodes()}
        t2_relabel = nx.relabel_nodes(t2, mapping2, copy=True)

        print(f"\nIsomorphic trees: "
              f"{nx.is_isomorphic(t1_relabel, t2_relabel)}")

        # Non-isomorphic trees
        t3 = nx.path_graph(7)  # line graph
        print(f"Balanced tree ≅ Path7: {nx.is_isomorphic(t1_relabel, t3)}")

        session.commit()


def demo_monomorphisms():
    """Node/edge monomorphisms (generalized isomorphism)."""
    with SessionLocal() as session:
        G1 = nx_sql.Graph(session, name="mono_1")
        G1.add_edges_from([(1, 2), (2, 3), (3, 4)])

        G2 = nx_sql.Graph(session, name="mono_2")
        G2.add_edges_from([(1, 2), (2, 3), (3, 4), (4, 5)])

        matcher = nx.algorithms.isomorphism.GraphMatcher(G1, G2)
        mono_iter = matcher.subgraph_monomorphisms_iter()
        count = 0
        for mapping in mono_iter:
            if count < 3:
                print(f"\nMonomorphism {count+1}: {mapping}")
            count += 1
        print(f"Total monomorphisms: {count}")

        session.commit()


if __name__ == "__main__":
    demo_is_isomorphic()
    demo_graph_matcher()
    demo_subgraph_isomorphism()
    demo_edge_color_isomorphism()
    demo_weisfeiler_lehman()
    demo_tree_isomorphism()
    demo_monomorphisms()
