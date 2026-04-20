"""example_subgraph.py - Subgraphs, views, and graph operations.

Covers: subgraph, induced_subgraph, edge_subgraph, restricted_view,
        complement, composition, union, intersection, difference,
        disjoint_union, cartesian/tensor/strong/lexicographic products,
        contraction, identified nodes, quotient graph, equivalence classes.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)


def demo_subgraph():
    """Create and query subgraphs."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="subgraph_demo")
        G.add_edges_from([
            (1, 2), (2, 3), (3, 4), (4, 5), (5, 1),
            (1, 3), (2, 4),
        ])

        # Node-induced subgraph
        SG = G.subgraph([1, 2, 3])
        print(f"Subgraph nodes [1,2,3]: {sorted(SG.nodes())}")
        print(f"Subgraph edges: {sorted(SG.edges())}")

        # Edge subgraph (only these edges)
        EG = G.edge_subgraph([(1, 2), (2, 3), (3, 4)])
        print(f"\nEdge subgraph edges: {sorted(EG.edges())}")
        print(f"Edge subgraph nodes: {sorted(EG.nodes())}")

        session.commit()


def demo_graph_views():
    """Create filtered graph views."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="views")
        G.add_node("A", type="hub")
        G.add_node("B", type="hub")
        G.add_node("C", type="leaf")
        G.add_edge("A", "B", weight=10)
        G.add_edge("A", "C", weight=1)

        # Show only hub nodes
        hub_view = nx.subgraph_view(
            G,
            filter_node=lambda n: G.nodes[n].get("type") == "hub",
        )
        print(f"Hub-only view: {list(hub_view.nodes())}")
        print(f"Hub edges: {list(hub_view.edges())}")

        # Hide leaf nodes
        no_leaf = nx.subgraph_view(
            G,
            filter_node=lambda n: G.nodes[n].get("type") != "leaf",
        )
        print(f"\nNo-leaf view: {list(no_leaf.nodes())}")

        # Show only high-weight edges
        heavy = nx.subgraph_view(
            G,
            filter_edge=lambda u, v: G[u][v].get("weight", 0) > 5,
        )
        print(f"\nHeavy edges (w>5): {list(heavy.edges())}")

        session.commit()


def demo_restricted_view():
    """Hide/show specific nodes and edges."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="restricted")
        G.add_edges_from([
            (1, 2), (2, 3), (3, 4), (4, 5),
        ])

        # Hide node 3
        H = nx.restricted_view(G, nodes=[3], edges=[])
        print(f"Original edges: {sorted(G.edges())}")
        print(f"Without node 3: {sorted(H.edges())}")

        # Hide edge (2,3)
        G2_plain = nx_sql.Graph(session, name="restricted2")
        G2_plain.add_edges_from([(1, 2), (2, 3), (3, 4), (4, 5)])
        H2 = nx.restricted_view(G2_plain, nodes=[], edges=[(2, 3)])
        print(f"\nWithout edge (2,3): {sorted(H2.edges())}")

        session.commit()


def demo_complement():
    """Graph complement."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="complement")
        G.add_edges_from([(1, 2), (2, 3)])  # path

        # Complement requires in-memory copy
        G_plain = nx.Graph(G)
        CG = nx.complement(G_plain)
        print(f"Original edges: {sorted(G_plain.edges())}")
        print(f"Complement edges: {sorted(CG.edges())}")
        print(f"Total possible: {len(G_plain.edges()) + len(CG.edges())} "
              f"(= n*(n-1)/2 = {5*4//2})")

        session.commit()


def demo_graph_operations():
    """Union, intersection, difference, composition."""
    with SessionLocal() as session:
        G1_plain = nx.Graph()
        G1_plain.add_edges_from([(1, 2), (2, 3)])

        G2_plain = nx.Graph()
        G2_plain.add_edges_from([(2, 3), (3, 4)])

        # Union
        union = nx.union(G1_plain, G2_plain)
        print(f"Union edges: {sorted(union.edges())}")

        # Intersection
        inter = nx.intersection(G1_plain, G2_plain)
        print(f"Intersection edges: {sorted(inter.edges())}")

        # Difference
        diff = nx.difference(G1_plain, G2_plain)
        print(f"Difference (G1_plain - G2_plain): {sorted(diff.edges())}")

        session.commit()


def demo_disjoint_union():
    """Disjoint union of graphs."""
    with SessionLocal() as session:
        G1_plain = nx_sql.Graph(session, name="du_g1")
        G1_plain.add_edges_from([(1, 2), (2, 3)])

        G2_plain = nx_sql.Graph(session, name="du_g2")
        G2_plain.add_edges_from([(1, 2), (2, 3)])

        du = nx.disjoint_union(G1_plain, G2_plain)
        print(f"Disjoint union: {du.number_of_nodes()} nodes, "
              f"{du.number_of_edges()} edges")
        print(f"Nodes: {sorted(du.nodes())}")
        print(f"Edges: {sorted(du.edges())}")

        session.commit()


def demo_graph_products():
    """Cartesian, tensor, strong, and lexicographic products."""
    with SessionLocal() as session:
        G1_plain = nx_sql.Graph(session, name="prod_g1")
        G1_plain.add_edges_from([(0, 1)])  # K2

        G2_plain = nx_sql.Graph(session, name="prod_g2")
        G2_plain.add_edges_from([(0, 1)])  # K2

        # Cartesian product (K2 × K2 = C4)
        cp = nx.cartesian_product(G1_plain, G2_plain)
        print(f"Cartesian product (K2 □ K2): {cp.number_of_nodes()} nodes, "
              f"{cp.number_of_edges()} edges")
        print(f"  Edges: {sorted(cp.edges())}")

        # Tensor product (K2 × K2 = 2*K2)
        tp = nx.tensor_product(G1_plain, G2_plain)
        print(f"\nTensor product (K2 × K2): {tp.number_of_nodes()} nodes, "
              f"{tp.number_of_edges()} edges")
        print(f"  Edges: {sorted(tp.edges())}")

        # Strong product (K2 ⊠ K2 = C4)
        sp = nx.strong_product(G1_plain, G2_plain)
        print(f"\nStrong product (K2 ⊠ K2): {sp.number_of_nodes()} nodes, "
              f"{sp.number_of_edges()} edges")
        print(f"  Edges: {sorted(sp.edges())}")

        # Lexicographic product (K2 · K2)
        lp = nx.lexicographic_product(G1_plain, G2_plain)
        print(f"\nLexicographic product (K2 · K2): {lp.number_of_nodes()} nodes, "
              f"{lp.number_of_edges()} edges")
        print(f"  Edges: {sorted(lp.edges())}")

        session.commit()


def demo_contraction():
    """Edge and node contraction."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="contraction")
        G.add_edges_from([
            (1, 2), (2, 3), (3, 4), (4, 5),
        ])

        # Contract edge (2,3)
        CG = nx.contracted_edge(G, (2, 3))
        print(f"Original: {G.number_of_nodes()} nodes, "
              f"{G.number_of_edges()} edges")
        print(f"After contracting (2,3): {CG.number_of_nodes()} nodes, "
              f"{CG.number_of_edges()} edges")
        print(f"  Nodes: {sorted(CG.nodes())}")

        # Contract multiple edges
        G2_plain = nx_sql.Graph(session, name="contraction2")
        G2_plain.add_edges_from([(1, 2), (2, 3), (3, 4), (4, 5)])
        CG2_plain = nx.contracted_nodes(G2_plain, 1, 4)
        print(f"\nAfter contracting node 4 into 1:")
        print(f"  Nodes: {sorted(CG2_plain.nodes())}")
        print(f"  Edges: {sorted(CG2_plain.edges())}")

        session.commit()


def demo_quotient():
    """Quotient graph from equivalence classes."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="quotient")
        G.add_edges_from([
            (1, 2), (2, 3), (3, 4),
            (5, 6), (6, 7), (7, 8),
            (1, 5), (2, 6),
        ])

        # Equivalence classes: {1,2,3} and {4}, {5,6,7} and {8}
        eq_classes = [{1, 2, 3}, {4}, {5, 6, 7}, {8}]

        Q = nx.quotient_graph(G, eq_classes)
        print(f"Quotient graph: {Q.number_of_nodes()} nodes, "
              f"{Q.number_of_edges()} edges")
        print(f"  Nodes: {sorted(Q.nodes())}")
        print(f"  Edges: {sorted(Q.edges())}")

        session.commit()


def demo_identified_nodes():
    """Identify (merge) nodes."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="identified")
        G.add_edges_from([
            (1, 2), (2, 3), (3, 4), (4, 5),
        ])

        # Identify nodes 1 and 5
        IG = nx.identified_nodes(G, {1: "merged", 5: "merged"})
        print(f"Original: {G.number_of_nodes()} nodes")
        print(f"After identifying 1,5 → 'merged': {IG.number_of_nodes()} nodes")
        print(f"  Edges: {sorted(IG.edges())}")

        session.commit()


def demo_batch_operations():
    """Batch graph operations."""
    with SessionLocal() as session:
        G1_plain = nx_sql.Graph(session, name="batch_g1")
        G1_plain.add_edges_from([(1, 2), (2, 3)])

        G2_plain = nx_sql.Graph(session, name="batch_g2")
        G2_plain.add_edges_from([(3, 4), (4, 5)])

        G3 = nx_sql.Graph(session, name="batch_g3")
        G3.add_edges_from([(5, 6)])

        # Union all
        union_all = nx.union_all([G1_plain, G2_plain, G3])
        print(f"Union of 3 graphs: {union_all.number_of_nodes()} nodes, "
              f"{union_all.number_of_edges()} edges")

        # Compose all
        compose = nx.compose_all([G1_plain, G2_plain, G3])
        print(f"\nCompose of 3 graphs: {compose.number_of_nodes()} nodes, "
              f"{compose.number_of_edges()} edges")

        session.commit()


if __name__ == "__main__":
    demo_subgraph()
    demo_graph_views()
    demo_restricted_view()
    demo_complement()
    demo_graph_operations()
    demo_disjoint_union()
    demo_graph_products()
    demo_contraction()
    demo_quotient()
    demo_identified_nodes()
    demo_batch_operations()
