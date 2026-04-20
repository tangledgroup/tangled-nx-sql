"""example_numpy_nodes.py - Graphs with numpy array and complex node types.

Covers: np.ndarray nodes, list[float] nodes, dict/set nodes,
        custom hashable types, node normalization.
"""

import numpy as np
import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)


def demo_ndarray_nodes():
    """Use numpy arrays as graph nodes."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="ndarray_graph")

        # Create feature vectors as nodes
        point_a = np.array([1.0, 2.0, 3.0])
        point_b = np.array([4.0, 5.0, 6.0])
        point_c = np.array([1.0, 2.0, 3.0])  # Same as A!

        G.add_node(point_a, label="Point A")
        G.add_node(point_b, label="Point B")
        G.add_node(point_c, label="Point C (duplicate)")

        print(f"Number of nodes: {G.number_of_nodes()}")
        print("(Note: np.array([1,2,3]) and np.array([1,2,3]) are the same node)")

        # Add edge using list form
        G.add_edge([1.0, 2.0, 3.0], [4.0, 5.0, 6.0], distance=np.linalg.norm(point_b - point_a))

        print(f"Edges: {list(G.edges(data=True))}")

        session.commit()


def demo_mixed_node_types():
    """Mix different hashable types as nodes."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="mixed_types")

        # Various hashable types
        nodes = [
            ("string", {"type": "str"}),
            (42, {"type": "int"}),
            (3.14, {"type": "float"}),
            ((1, 2, 3), {"type": "tuple"}),
            ({1, 2}, {"type": "set"}),
            ({"key": "val"}, {"type": "dict"}),
        ]

        for node, attrs in nodes:
            G.add_node(node, **attrs)

        # Connect some nodes
        G.add_edge("string", 42)
        G.add_edge(42, (1, 2, 3))
        G.add_edge((1, 2, 3), {1, 2})

        print(f"Nodes ({G.number_of_nodes()}):")
        for n, d in sorted(G.nodes(data=True), key=lambda x: str(x[0])):
            print(f"  {n!r} ({d['type']})")

        print(f"\nEdges: {list(G.edges())}")

        session.commit()


def demo_vector_similarity():
    """Build a similarity graph from vector features."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="similarity")

        # Feature vectors for 5 items
        vectors = {
            "apple": np.array([1.0, 0.0, 0.0]),
            "banana": np.array([0.9, 0.1, 0.0]),
            "carrot": np.array([0.0, 1.0, 0.0]),
            "orange": np.array([0.85, 0.15, 0.0]),
            "potato": np.array([0.1, 0.9, 0.1]),
        }

        # Add nodes
        for name, vec in vectors.items():
            G.add_node(vec, label=name)

        # Connect similar items (threshold-based)
        threshold = 0.85
        vecs = list(vectors.values())
        labels = list(vectors.keys())
        for i in range(len(vecs)):
            for j in range(i + 1, len(vecs)):
                sim = np.dot(vecs[i], vecs[j])
                if sim >= threshold:
                    G.add_edge(vecs[i], vecs[j], similarity=round(sim, 2))

        print("Similarity graph (threshold ≥ 0.85):")
        for u, v, d in G.edges(data=True):
            label_u = G.nodes[u]["label"]
            label_v = G.nodes[v]["label"]
            print(f"  {label_u} —{d['similarity']}→ {label_v}")

        session.commit()


def demo_numpy_operations():
    """Combine numpy computations with graph algorithms."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="numpy_ops")

        # Create a graph of points in 2D space
        np.random.seed(42)
        points = np.random.rand(10, 2)

        for i in range(len(points)):
            G.add_node(tuple(points[i]), index=i)

        # Connect nearest neighbors
        for i in range(len(points)):
            dists = []
            for j in range(len(points)):
                if i != j:
                    d = np.linalg.norm(points[i] - points[j])
                    dists.append((j, d))
            dists.sort(key=lambda x: x[1])
            # Connect to 2 nearest neighbors
            for j, d in dists[:2]:
                G.add_edge(tuple(points[i]), tuple(points[j]), distance=round(d, 3))

        print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        print(f"Diameter: {nx.diameter(G)}")
        print(f"Average clustering: {nx.average_clustering(G):.4f}")

        session.commit()


if __name__ == "__main__":
    demo_ndarray_nodes()
    demo_mixed_node_types()
    demo_vector_similarity()
    demo_numpy_operations()
