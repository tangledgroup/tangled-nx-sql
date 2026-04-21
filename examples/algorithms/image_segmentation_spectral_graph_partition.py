"""Demonstrate image segmentation via spectral graph partitioning with nx_sql.

Mirrors networkx/examples/algorithms/plot_image_segmentation_spectral_graph_partition.py
but uses SQLAlchemy persistence. Tests k-neighbor graph construction from RGB data
and spectral clustering for bi-partitioning.

No matplotlib/3D plots — all analysis printed as text.
"""

import numpy as np
import networkx as nx
from sklearn.cluster import SpectralClustering
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base
import sys; sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent.parent.parent))
from examples.utils import print_docstring

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def create_rings_dataset(seed=0, n_samples=128):
    """Create the 'Rings' dataset: two entangled noisy rings in 3D.

    Returns X (n_samples, 3) RGB-like data and Y ground truth labels.
    """
    np.random.seed(seed)
    X = np.random.random((n_samples, 3)) * 0.5
    m = int(np.round(n_samples / 2))

    theta = np.linspace(0, 2 * np.pi, m)

    # First ring (centered roughly at origin)
    X[0:m, 0] += 2 * np.cos(theta)
    X[0:m, 1] += 3 * np.sin(theta) + 1
    X[0:m, 2] += np.sin(theta) + 0.5

    # Second ring (entangled with first)
    X[m:, 0] += 2 * np.sin(theta)
    X[m:, 1] += 2 * np.cos(theta) - 1
    X[m:, 2] += 3 * np.sin(theta)

    Y = np.zeros(n_samples, dtype=np.int8)
    Y[m:] = 1

    # Normalize to 0-255 range for RGB interpretation
    for i in range(X.shape[1]):
        x = X[:, i]
        min_x, max_x = np.min(x), np.max(x)
        X[:, i] = np.round(255 * (x - min_x) / (max_x - min_x))

    return X, Y


@print_docstring
def demo_image_segmentation():
    """Segment an RGB image dataset using spectral graph partitioning."""

    with Session() as session:
        # --- Create the Rings dataset ---
        print("=== Image Segmentation via Spectral Graph Partitioning ===")
        X, Y = create_rings_dataset(seed=0, n_samples=128)
        N = X.shape[0]

        print(f"Dataset: {N} samples in 3D RGB space")
        print(f"Ground truth labels:")
        print(f"  Class 0 (ring A): {np.sum(Y == 0)} samples")
        print(f"  Class 1 (ring B): {np.sum(Y == 1)} samples")

        # Print first few samples
        print("\nFirst 10 samples (R, G, B):")
        for i in range(10):
            label = "A" if Y[i] == 0 else "B"
            print(f"  [{i:3d}] RGB=({int(X[i,0]):3d}, {int(X[i,1]):3d}, {int(X[i,2]):3d}) class={label}")

        # --- Build k-neighbor graph ---
        NUM_CLUSTERS = 2
        sc = SpectralClustering(
            n_clusters=NUM_CLUSTERS,
            affinity="nearest_neighbors",
            random_state=4242,
            n_neighbors=10,
            assign_labels="cluster_qr",
            n_jobs=-1,
        )
        clusters = sc.fit(X)
        pred_labels = clusters.labels_.astype(int)

        # Build graph from affinity matrix
        G_nx = nx.from_scipy_sparse_array(clusters.affinity_matrix_.getH())
        G_nx.remove_edges_from(nx.selfloop_edges(G_nx))

        print(f"\n=== Graph Construction ===")
        print(f"Graph: {G_nx.number_of_nodes()} nodes, {G_nx.number_of_edges()} edges")
        print(f"Average degree: {2 * G_nx.number_of_edges() / G_nx.number_of_nodes():.2f}")

        # --- Store in nx_sql ---
        G = nx_sql.Graph(session, name="spectral_clustering_demo")
        for i in range(N):
            G.add_node(i, r=float(X[i, 0]), g=float(X[i, 1]), b=float(X[i, 2]),
                       true_label=int(Y[i]), pred_label=int(pred_labels[i]))
        for u, v in G_nx.edges():
            weight = clusters.affinity_matrix_[u, v]
            G.add_edge(u, v, weight=float(weight))

        # --- Analyze clustering quality ---
        print(f"\n=== Clustering Results ===")
        print(f"Spectral clustering found {len(set(pred_labels))} cluster(s)")

        # Confusion matrix vs ground truth
        print("\n--- Confusion Matrix (pred vs true) ---")
        tp = np.sum((pred_labels == 0) & (Y == 0))
        tn = np.sum((pred_labels == 1) & (Y == 1))
        fp = np.sum((pred_labels == 1) & (Y == 0))
        fn = np.sum((pred_labels == 0) & (Y == 1))
        print(f"  True 0 | Pred 0: {tp} (TP)")
        print(f"  True 1 | Pred 0: {fn} (FN)")
        print(f"  True 0 | Pred 1: {fp} (FP)")
        print(f"  True 1 | Pred 1: {tn} (TN)")

        accuracy = (tp + tn) / N
        print(f"\nAccuracy: {accuracy:.2%}")

        # Cluster sizes
        for label in sorted(set(pred_labels)):
            members = [i for i in range(N) if pred_labels[i] == label]
            true_counts = {}
            for m in members:
                true_counts[Y[m]] = true_counts.get(Y[m], 0) + 1
            print(f"\nCluster {label}: {len(members)} members")
            for t, c in sorted(true_counts.items()):
                name = "Ring A" if t == 0 else "Ring B"
                print(f"  True {name}: {c} ({c/len(members):.0%})")

        # --- Graph structure analysis ---
        print(f"\n=== Graph Structure ===")
        print(f"Connected components: {nx.number_connected_components(G)}")

        if nx.number_connected_components(G) == 1:
            diameter = nx.diameter(G)
            avg_shortest = nx.average_shortest_path_length(G)
            print(f"Diameter: {diameter}")
            print(f"Average shortest path length: {avg_shortest:.2f}")

        # Edge weight statistics
        weights = [d["weight"] for _, _, d in G.edges(data=True)]
        print(f"\nEdge weight statistics:")
        print(f"  Min: {min(weights):.4f}")
        print(f"  Max: {max(weights):.4f}")
        print(f"  Mean: {np.mean(weights):.4f}")
        print(f"  Std: {np.std(weights):.4f}")

        # Degree distribution
        degrees = [d for _, d in G.degree()]
        from collections import Counter
        degree_counts = Counter(degrees)
        print(f"\nDegree distribution:")
        for deg in sorted(degree_counts.keys())[:10]:
            print(f"  Degree {deg}: {degree_counts[deg]} nodes")
        if len(degree_counts) > 10:
            print(f"  ... ({len(degree_counts)} unique degrees total)")

        # --- Partition quality via edge cuts ---
        print(f"\n=== Partition Quality ===")
        cluster_0 = [i for i in range(N) if pred_labels[i] == 0]
        cluster_1 = [i for i in range(N) if pred_labels[i] == 1]

        # Count edges crossing the cut
        cut_edges = 0
        intra_0 = 0
        intra_1 = 0
        for u, v in G.edges():
            if pred_labels[u] != pred_labels[v]:
                cut_edges += 1
            elif pred_labels[u] == 0:
                intra_0 += 1
            else:
                intra_1 += 1

        total_edges = G.number_of_edges()
        print(f"Total edges: {total_edges}")
        print(f"Intra-cluster edges (cluster 0): {intra_0}")
        print(f"Intra-cluster edges (cluster 1): {intra_1}")
        print(f"Inter-cluster edges (cut): {cut_edges}")
        print(f"Cut ratio: {cut_edges/total_edges:.2%}")

        # --- Per-sample details for a few nodes ---
        print(f"\n=== Sample Details (first 5 per cluster) ===")
        for label in [0, 1]:
            members = [i for i in range(N) if pred_labels[i] == label][:5]
            print(f"\nCluster {label}:")
            for idx in members:
                true_name = "Ring A" if Y[idx] == 0 else "Ring B"
                print(f"  Node {idx:3d}: RGB=({int(X[idx,0]):3d},{int(X[idx,1]):3d},{int(X[idx,2]):3d}) "
                      f"pred={pred_labels[idx]} true={Y[idx]} ({true_name})")

        session.commit()

    # --- Reload from DB and verify ---
    with Session() as session:
        from nx_sql.models import Graph as GraphModel
        gmodel = session.execute(
            nx_sql.select(GraphModel).where(GraphModel.name == "spectral_clustering_demo")
        ).scalar_one()
        G2 = nx_sql.Graph(session, graph_id=gmodel.graph_id)
        print(f"\n=== Persistence Verification ===")
        print(f"Reloaded: {G2.number_of_nodes()} nodes, {G2.number_of_edges()} edges")

        # Verify a few node attributes
        for i in [0, 64]:
            r = G2.nodes[i]["r"]
            g = G2.nodes[i]["g"]
            b = G2.nodes[i]["b"]
            print(f"  Node {i}: RGB=({r:.0f},{g:.0f},{b:.0f})")

        session.commit()


if __name__ == "__main__":
    demo_image_segmentation()
