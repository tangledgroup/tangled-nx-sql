"""Example 5 – visualize the example_5 graph with clustered, color-coded nodes.

Reads the same database as example_5 (example_5.db), loads the graph, detects
communities via Louvain, and produces a publication-quality SVG plot where:

  - Node type → color (CarManufacturer=blue, CarModel=green, OwnerProfile=orange, City=purple)
  - Community → marker style / size for an extra visual layer
  - Edge type → distinct colors with transparency so overlap is readable
  - Layout → force-directed with community-aware spring placement

Output: example_5_graph.svg (and prints to console if --show is passed).
"""

import os
import sys
import random
import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import matplotlib
matplotlib.use("Agg")  # non-interactive backend for headless / file-only output
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

import community as community_louvain


# ── Paths ────────────────────────────────────────────────────────────────────
SEED = 42
# Resolve DB path relative to the repo root (one level above examples/)
_DB_DIR = os.path.abspath(os.path.dirname(__file__))  # .../examples/
DB_PATH = os.path.join(_DB_DIR, "..", "example_5.db")
OUTPUT_SVG = os.path.join(os.path.dirname(__file__), "example_5_graph.svg")

# ── Color palette ────────────────────────────────────────────────────────────
TYPE_COLORS = {
    "CarManufacturer": "#3B82F6",  # blue
    "CarModel": "#10B981",        # emerald green
    "OwnerProfile": "#F59E0B",    # amber
    "City": "#8B5CF6",            # purple
}

EDGE_COLORS = {
    "headquarters":      "#3B82F6",
    "produces":          "#10B981",
    "owns":              "#F59E0B",
    "sold_in":           "#8B5CF6",
    "resides_in":        "#A78BFA",
    "competes_with":     "#EF4444",
    "shares_hobby":      "#F97316",
    "neighboring_country": "#06B6D4",
    "same_hq":           "#60A5FA",
}

# ── Load graph from DB ───────────────────────────────────────────────────────
def load_graph():
    """Rebuild the in-memory graph from the SQLAlchemy-backed DB."""
    engine = create_engine(f"sqlite:///{DB_PATH}")
    import nx_sql
    from nx_sql.models import Base
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    with Session() as session:
        # Load the existing graph from example_5
        G = nx_sql.DiGraph(session, name="example5_random_nodes")
        return G


# ── Community detection ──────────────────────────────────────────────────────
def detect_communities(G):
    """Run Louvain on the undirected version for community assignment."""
    U = G.to_undirected()
    partition = community_louvain.best_partition(U, random_state=SEED)
    return partition


# ── Layout: force-directed per community cluster ─────────────────────────────
def compute_layout(G, partition):
    """Compute a force-directed layout with community-aware initial positions."""
    U = G.to_undirected()
    node_ids = list(G.nodes())
    communities = sorted(set(partition.values()))
    n_communities = len(communities)

    # Seed each community in a distinct region of the plane
    radius = max(len(node_ids), 100) ** 0.5 * 1.5
    rng = random.Random(SEED + 1)
    comm_centers = {}
    for i, c in enumerate(communities):
        angle = 2 * 3.14159 * i / n_communities
        cx = radius * 0.7 * (0.5 + 0.5 * rng.random()) * (1 if rng.random() > 0.5 else -1)
        cy = radius * 0.7 * (0.5 + 0.5 * rng.random()) * (1 if rng.random() > 0.5 else -1)
        comm_centers[c] = (cx, cy)

    # Initial positions: community centroid + jitter
    pos_init = {}
    for node in node_ids:
        c = partition[node]
        cx, cy = comm_centers[c]
        pos_init[node] = [cx + rng.gauss(0, radius * 0.15),
                          cy + rng.gauss(0, radius * 0.15)]

    # Run spring layout using initial positions as starting point
    # Large k value to spread 1000 nodes apart; more iterations for stability
    pos = nx.spring_layout(
        U,
        pos=pos_init,
        iterations=300,
        k=5.0,
        seed=SEED,
    )

    return pos


# ── Plotting ─────────────────────────────────────────────────────────────────
def plot_graph(G, partition, pos):
    """Create a publication-quality clustered, color-coded graph visualization."""
    fig, ax = plt.subplots(figsize=(24, 18), dpi=150)
    fig.patch.set_facecolor("#FAFAFA")
    ax.set_facecolor("#FFFFFF")

    node_ids = list(G.nodes())
    num_nodes = len(node_ids)

    # ── Node sizes: hubs get bigger ──────────────────────────────────────
    degrees = dict(G.degree())

    # Community sizes for label sizing
    comm_sizes = {}
    for c in partition.values():
        comm_sizes[c] = comm_sizes.get(c, 0) + 1
    max_comm_size = max(comm_sizes.values()) if comm_sizes else 1

    # ── Draw edges by type with distinct colors ──────────────────────────
    edge_groups = {}
    for u, v, data in G.edges(data=True):
        etype = data.get("edge_type", "unknown")
        edge_groups.setdefault(etype, []).append((u, v))

    # Draw edges: high-volume types get very low alpha to avoid visual clutter.
    # Important semantic edges (owns, produces) are thicker and more opaque.
    edge_order = ["same_hq", "neighboring_country",  # background noise first
                  "shares_hobby", "competes_with",
                  "sold_in", "resides_in",
                  "headquarters", "produces", "owns"]  # most important on top

    edge_style = {
        "same_hq":           ("#60A5FA", 0.04, 0.3),
        "neighboring_country": ("#06B6D4", 0.08, 0.4),
        "shares_hobby":      ("#F97316", 0.10, 0.5),
        "competes_with":     ("#EF4444", 0.12, 0.6),
        "sold_in":           ("#8B5CF6", 0.12, 0.5),
        "resides_in":        ("#A78BFA", 0.15, 0.6),
        "headquarters":      ("#3B82F6", 0.30, 1.0),
        "produces":          ("#10B981", 0.35, 1.2),
        "owns":              ("#F59E0B", 0.40, 1.5),
    }

    for etype in edge_order:
        edges = edge_groups.get(etype, [])
        if not edges:
            continue
        color, alpha, width = edge_style.get(etype, ("#999999", 0.15, 0.5))

        xs = [pos[u][0] for u, v in edges]
        ys = [pos[u][1] for u, v in edges]
        ax.plot(xs, ys, color=color, alpha=alpha, linewidth=width,
                zorder=1, solid_capstyle="round")

    # ── Draw type-cluster boundary ellipses ────────────────────────────
    import numpy as np
    for etype, color in TYPE_COLORS.items():
        mask = [i for i, n in enumerate(node_ids)
                if G.nodes[n].get("entity_type") == etype]
        if len(mask) < 3:
            continue
        pts = np.array([[pos[node_ids[i]][0], pos[node_ids[i]][1]] for i in mask])
        mean = pts.mean(axis=0)
        cov = np.cov(pts.T)
        eigenvals, eigenvecs = np.linalg.eigh(cov)
        angle = np.degrees(np.arctan2(eigenvecs[1, -1], eigenvecs[0, -1]))
        width = 4 * np.sqrt(eigenvals[-1])
        height = 4 * np.sqrt(max(eigenvals[-2], 0.01)) if len(eigenvals) > 1 else width
        ellipse = mpatches.Ellipse(
            mean, width=width, height=height, angle=angle,
            facecolor="none", edgecolor=color, linewidth=1.5,
            linestyle="--", alpha=0.5, zorder=2, capstyle="round",
        )
        ax.add_patch(ellipse)

    # ── Draw Louvain community ellipses for largest communities only ───
    top_communities = sorted(comm_sizes.items(), key=lambda x: -x[1])[:8]
    comm_colors = plt.cm.Set3(np.linspace(0, 1, len(top_communities)))
    for (comm_id, size), cc in zip(top_communities, comm_colors):
        mask = [i for i, n in enumerate(node_ids) if partition[n] == comm_id]
        if len(mask) < 3:
            continue
        pts = np.array([[pos[node_ids[i]][0], pos[node_ids[i]][1]] for i in mask])
        mean = pts.mean(axis=0)
        cov = np.cov(pts.T)
        eigenvals, eigenvecs = np.linalg.eigh(cov)
        angle = np.degrees(np.arctan2(eigenvecs[1, -1], eigenvecs[0, -1]))
        width = 4 * np.sqrt(max(eigenvals[-1], 0.01))
        height = 4 * np.sqrt(max(eigenvals[-2] if len(eigenvals) > 1 else eigenvals[-1], 0.01))
        ellipse = mpatches.Ellipse(
            mean, width=width, height=height, angle=angle,
            facecolor="none", edgecolor=cc, linewidth=0.8,
            linestyle="-.", alpha=0.35, zorder=2, capstyle="round",
        )
        ax.add_patch(ellipse)

    # ── Draw nodes by type with community-aware sizing ───────────────────
    for etype in TYPE_COLORS:
        mask = [i for i, n in enumerate(node_ids)
                if G.nodes[n].get("entity_type") == etype]
        if not mask:
            continue

        xs = [pos[node_ids[i]][0] for i in mask]
        ys = [pos[node_ids[i]][1] for i in mask]
        # Keep sizes relatively uniform so clusters are visible
        base_size = 40
        ax.scatter(xs, ys, s=base_size, c=TYPE_COLORS[etype],
                   alpha=0.65, edgecolors="white", linewidth=0.3,
                   zorder=3, rasterized=True)

    # ── Legend ───────────────────────────────────────────────────────────
    type_patches = [
        mpatches.Patch(color=c, label=f"{t} ({sum(1 for n in node_ids if G.nodes[n].get('entity_type') == t)})")
        for t, c in TYPE_COLORS.items()
    ]

    edge_patches = []
    for etype, color in EDGE_COLORS.items():
        count = len(edge_groups.get(etype, []))
        if count > 0:
            edge_patches.append(mpatches.Patch(color=color, label=f"{etype}: {count}",
                                               alpha=0.8, fill=False, linewidth=2))

    ax.legend(handles=type_patches + edge_patches,
              loc="upper right", fontsize=9, framealpha=0.9,
              borderpad=0.8, columnspacing=1.5, labelspacing=0.4)

    # ── Title & styling ─────────────────────────────────────────────────
    ax.set_title(
        f"Car Ecosystem Graph  •  {num_nodes} nodes  •  {G.number_of_edges()} edges  •  "
        f"{len(set(partition.values()))} communities",
        fontsize=16, fontweight="bold", pad=20
    )

    ax.set_xlabel("x (community-aware layout)", fontsize=11, labelpad=10)
    ax.set_ylabel("y (community-aware layout)", fontsize=11, labelpad=10)

    # Remove axes for cleaner look
    ax.set_xticks([])
    ax.set_yticks([])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.spines["left"].set_visible(False)

    plt.tight_layout(pad=1.5)
    return fig


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    print("Loading graph from DB...")
    G = load_graph()
    print(f"  Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")

    print("Detecting communities (Louvain)...")
    partition = detect_communities(G)
    n_communities = len(set(partition.values()))
    print(f"  Found {n_communities} communities")

    print("Computing layout...")
    pos = compute_layout(G, partition)

    print("Plotting...")
    fig = plot_graph(G, partition, pos)

    out_path = OUTPUT_SVG
    fig.savefig(out_path, format="svg", bbox_inches="tight")
    plt.close(fig)
    print(f"Saved → {out_path}")
    print("Done.")


if __name__ == "__main__":
    main()
