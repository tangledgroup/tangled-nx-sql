"""example_drawing.py - Graph visualization and layouts.

Covers: spring/circular/spectral/kamada_kawai layouts, BFS layout,
        multipartite layout, spiral layout, ARF/ForceAtlas2,
        matplotlib drawing, TikZ/LaTeX export, Graphviz DOT.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)


def demo_layouts():
    """Compute various graph layouts."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="layouts")
        G.add_edges_from([
            (1, 2), (2, 3), (3, 4), (4, 5),
            (1, 5), (1, 3), (2, 4),
        ])

        layouts = {}

        # Spring layout (use plain copy for layout functions)
        G_plain = nx.Graph(G)
        pos = nx.spring_layout(G_plain)
        layouts["spring"] = pos
        print("Spring layout:")
        for node, (x, y) in sorted(pos.items(), key=lambda x: str(x[0])):
            print(f"  {node}: ({x:.3f}, {y:.3f})")

        # Circular layout
        pos = nx.circular_layout(G_plain)
        layouts["circular"] = pos
        print("\nCircular layout:")
        for node, (x, y) in sorted(pos.items(), key=lambda x: str(x[0])):
            print(f"  {node}: ({x:.3f}, {y:.3f})")

        # Spectral layout
        pos = nx.spectral_layout(G_plain)
        layouts["spectral"] = pos
        print("\nSpectral layout:")
        for node, (x, y) in sorted(pos.items(), key=lambda x: str(x[0])):
            print(f"  {node}: ({x:.3f}, {y:.3f})")

        # Kamada-Kawai layout
        pos = nx.kamada_kawai_layout(G_plain)
        layouts["kamada_kawai"] = pos
        print("\nKamada-Kawai layout:")
        for node, (x, y) in sorted(pos.items(), key=lambda x: str(x[0])):
            print(f"  {node}: ({x:.3f}, {y:.3f})")

        # Planar layout (if planar)
        if nx.check_planarity(G_plain)[0]:
            pos = nx.planar_layout(G_plain)
            layouts["planar"] = pos
            print("\nPlanar layout:")
            for node, (x, y) in sorted(pos.items(), key=lambda x: str(x[0])):
                print(f"  {node}: ({x:.3f}, {y:.3f})")

        session.commit()


def demo_bfs_layout():
    """BFS-based layout."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="bfs_layout")
        edges = [
            ("root", "A"), ("root", "B"),
            ("A", "C"), ("A", "D"),
            ("B", "E"), ("B", "F"),
        ]
        G.add_edges_from(edges)

        pos = nx.bfs_layout(G, "root")
        print("\nBFS layout:")
        for node, (x, y) in sorted(pos.items()):
            print(f"  {node}: ({x:.3f}, {y:.3f})")

        session.commit()


def demo_multipartite_layout():
    """Multipartite layout for layered graphs."""
    with SessionLocal() as session:
        G = nx_sql.DiGraph(session, name="multipartite")
        # Three layers
        layer1 = ["A", "B"]
        layer2 = ["C", "D", "E"]
        layer3 = ["F", "G"]

        G.add_edges_from([
            (u, v) for u in layer1 for v in layer2
        ])
        G.add_edges_from([
            (u, v) for u in layer2 for v in layer3
        ])

        # Use partition dict: layer_num -> nodes
        partition = {0: layer1, 1: layer2, 2: layer3}
        pos = nx.multipartite_layout(G, subset_key=partition)
        print("\nMultipartite layout:")
        for node, (x, y) in sorted(pos.items()):
            print(f"  {node}: ({x:.3f}, {y:.3f})")

        session.commit()


def demo_spiral_layout():
    """Spiral layout."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="spiral")
        G.add_edges_from([
            (1, 2), (2, 3), (3, 4), (4, 5),
            (5, 6), (6, 1),
        ])

        pos = nx.spiral_layout(G, scale=1)
        print("\nSpiral layout:")
        for node, (x, y) in sorted(pos.items()):
            print(f"  {node}: ({x:.3f}, {y:.3f})")

        session.commit()


def demo_force_atlas():
    """ForceAtlas2 layout (if available)."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="force_atlas")
        G.add_edges_from([
            (1, 2), (1, 3), (1, 4),
            (2, 3), (3, 4),
        ])

        try:
            pos = nx.forceatlas2_layout(G)
            print("\nForceAtlas2 layout:")
            for node, (x, y) in sorted(pos.items()):
                print(f"  {node}: ({x:.3f}, {y:.3f})")
        except Exception as e:
            print(f"\nForceAtlas2 not available: {e}")

        session.commit()


def demo_tikz_export():
    """Export graph to TikZ/LaTeX."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="tikz")
        G.add_edges_from([(1, 2), (2, 3), (3, 1)])

        try:
            pos = nx.spring_layout(nx.Graph(G))
            tikz = nx.to_latex(nx.Graph(G), pos=pos)
            print(f"\nTikZ output (first 200 chars):")
            print(tikz[:200])
        except Exception as e:
            print(f"\nTikZ export: {e}")

        session.commit()


def demo_dot_export():
    """Export to DOT format for Graphviz."""
    with SessionLocal() as session:
        G = nx_sql.DiGraph(session, name="dot_vis")
        G.add_edge("A", "B", label="edge1")
        G.add_edge("B", "C", label="edge2")
        G.add_node("D", shape="box")

        try:
            dot_str = nx.nx_pydot.to_pydot(G).to_string()
            print(f"\nDOT output:")
            print(dot_str)
        except Exception as e:
            print(f"\nDOT export: {e}")

        session.commit()


if __name__ == "__main__":
    demo_layouts()
    demo_bfs_layout()
    demo_multipartite_layout()
    demo_spiral_layout()
    demo_force_atlas()
    demo_tikz_export()
    demo_dot_export()
