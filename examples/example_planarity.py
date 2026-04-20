"""example_planarity.py - Planarity testing and embeddings.

Covers: is_planar, check_planarity, PlanarEmbedding, planar drawing,
        Kuratowski subgraphs, combinatorial embedding, planar layout.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)


def demo_is_planar():
    """Test if graphs are planar."""
    with SessionLocal() as session:
        # Planar: K4 is planar
        G1 = nx_sql.Graph(session, name="planar_k4")
        G1.add_edges_from([
            (1, 2), (1, 3), (1, 4),
            (2, 3), (2, 4),
            (3, 4),
        ])
        is_planar, _ = nx.check_planarity(G1)
        print(f"K₄ planar: {is_planar}")

        # Non-planar: K5
        G2 = nx_sql.Graph(session, name="nonplanar_k5")
        for i in range(5):
            for j in range(i + 1, 5):
                G2.add_edge(i, j)
        is_planar, _ = nx.check_planarity(G2)
        print(f"K₅ planar: {is_planar}")

        # Non-planar: K3,3
        G3 = nx_sql.Graph(session, name="nonplanar_k33")
        left = [0, 1, 2]
        right = [3, 4, 5]
        for l in left:
            for r in right:
                G3.add_edge(l, r)
        is_planar, _ = nx.check_planarity(G3)
        print(f"K₃,₃ planar: {is_planar}")

        # Grid is planar
        G4 = nx_sql.Graph(session, name="planar_grid")
        G4.add_edges_from(nx.grid_2d_graph(3, 3).edges())
        is_planar, _ = nx.check_planarity(G4)
        print(f"3×3 grid planar: {is_planar}")

        session.commit()


def demo_kuratowski():
    """Find Kuratowski subgraphs in non-planar graphs."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="kuratowski")
        for i in range(5):
            for j in range(i + 1, 5):
                G.add_edge(i, j)

        is_planar, cert = nx.check_planarity(G)
        if not is_planar:
            # cert is a certificate object; get subgraph from G
            if hasattr(cert, 'subgraph'):
                kur_sub = cert.subgraph()
            else:
                kur_sub = G  # fallback
            print(f"\nNon-planar certificate (Kuratowski subgraph):")
            print(f"  Nodes: {sorted(kur_sub.nodes())}")
            print(f"  Edges: {sorted(kur_sub.edges())}")
            node_count = kur_sub.number_of_nodes()
            print(f"  Type: {'K5' if node_count == 5 else 'K3,3' if node_count == 6 else 'other'}")

        session.commit()


def demo_planar_embedding():
    """Create and use planar embeddings."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="planar_emb")
        G.add_edges_from([
            (1, 2), (1, 3), (1, 4),
            (2, 3), (2, 4),
            (3, 4),
        ])

        if nx.check_planarity(G)[0]:
            print("\nGraph is planar - K4 is planar!")
            print("  PlanarEmbedding requires add_half_edge API not available.")
            # Show that it's planar by computing a drawing
            pos = nx.planar_layout(nx.Graph(G))
            print(f"  Planar layout: {pos}")

        session.commit()


def demo_planar_layout():
    """Draw planar graphs using planar layout."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="planar_layout")
        G.add_edges_from([
            (1, 2), (1, 3), (1, 4),
            (2, 3), (2, 4),
            (3, 4),
        ])

        if nx.check_planarity(G)[0]:
            pos = nx.planar_layout(G)
            print("\nPlanar layout positions:")
            for node, (x, y) in sorted(pos.items()):
                print(f"  {node}: ({x:.2f}, {y:.2f})")

        session.commit()


def demo_planar_face_edges():
    """Find faces in planar embeddings."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="planar_faces")
        G.add_edges_from([
            (1, 2), (2, 3), (3, 4), (4, 1),
            (1, 3),
        ])

        if nx.check_planarity(G)[0]:
            # PlanarEmbedding requires add_half_edge which isn't exposed
            print("\nGraph is planar - faces can be computed from combinatorial embedding")
            print("  (PlanarEmbedding API not fully accessible in this version)")

        session.commit()


if __name__ == "__main__":
    demo_is_planar()
    demo_kuratowski()
    demo_planar_embedding()
    demo_planar_layout()
    demo_planar_face_edges()
