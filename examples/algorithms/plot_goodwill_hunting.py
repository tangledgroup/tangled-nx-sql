"""Solve the Good Will Hunting problem: find all homeomorphically irreducible trees.

The movie scene presents a challenge: draw all homeomorphically irreducible trees
of size n=10. A tree is connected and acyclic. Homeomorphically irreducible means
no node has degree 2 (series-reduced).

Two approaches are demonstrated:
1. Qualitative — manually construct examples starting from star_graph,
   then move leaves to create deeper structures, checking for isomorphism.
2. Brute-force — generate all nonisomorphic trees of order 10 (106 total),
   filter those with no degree-2 nodes, plot the 10 results.

Adapted from NetworkX Guides:
https://networkx.org/nx-guides/content/applications/goodwillhunting.html
"""

import matplotlib.pyplot as plt
import networkx as nx


def demo_qualitative_approach():
    """Manually construct homeomorphically irreducible trees of size 10.

    Start with star_graph (root + leaves), verify it has no degree-2 nodes,
    then move pairs of leaves to a new child of the root to create deeper
    trees. Demonstrate that some constructions are isomorphic despite
    different appearances.
    """
    print("=== Qualitative Approach ===\n")

    # --- Step 1: Verify star_graph works ---
    print("Step 1: Star graph (root + 9 leaves)")
    G = nx.star_graph(9)
    print(f"  Is tree: {nx.is_tree(G)}")
    print(f"  Has degree-2 nodes: {any(d == 2 for _, d in G.degree())}")
    print(f"  Degrees: {dict(G.degree())}")

    fig, ax = plt.subplots(figsize=(6, 6))
    nx.draw(G, pos=nx.bfs_layout(G, 0), ax=ax, with_labels=True,
            node_color="lightblue", edge_color="gray", node_size=300)
    ax.set_title("Star Graph (9)")
    plt.tight_layout()
    plt.savefig("examples/algorithms/plot_goodwill_hunting_star.png", dpi=150)
    plt.close()
    print("  Saved: plot_goodwill_hunting_star.png\n")

    # --- Step 2: Move two leaves to a new child of root ---
    print("Step 2: Move nodes 1, 2 from root to node 3")
    H = G.copy()
    H.remove_edges_from([(0, 1), (0, 2)])
    H.add_edges_from([(3, 1), (3, 2)])
    print(f"  Is tree: {nx.is_tree(H)}")
    print(f"  Has degree-2 nodes: {any(d == 2 for _, d in H.degree())}")
    print(f"  Degrees: {dict(H.degree())}")

    pos_h = nx.bfs_layout(H, 0)
    fig, ax = plt.subplots(figsize=(6, 6))
    nx.draw(H, pos=pos_h, ax=ax, with_labels=True,
            node_color="lightgreen", edge_color="gray", node_size=300)
    ax.set_title("Move leaves 1,2 to node 3")
    plt.tight_layout()
    plt.savefig("examples/algorithms/plot_goodwill_hunting_move.png", dpi=150)
    plt.close()

    # --- Step 3: Same move but to node 4 (isomorphic!) ---
    print("\nStep 3: Move nodes 1, 2 from root to node 4 (isomorphic to H?)")
    H1 = G.copy()
    H1.remove_edges_from([(0, 1), (0, 2)])
    H1.add_edges_from([(4, 1), (4, 2)])
    print(f"  Is tree: {nx.is_tree(H1)}")
    print(f"  Isomorphic to H: {nx.is_isomorphic(H, H1)}")

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for graph, ax, ttl in zip((H, H1), axes, ("H (to node 3)", "H1 (to node 4)")):
        nx.draw(graph, pos=nx.spring_layout(graph, seed=1000),
                ax=ax, with_labels=False, node_color="lightcoral",
                edge_color="gray", node_size=300)
        ax.set_title(ttl)
    plt.tight_layout()
    plt.savefig("examples/algorithms/plot_goodwill_hunting_isomorphic.png", dpi=150)
    plt.close()
    print("  Saved: plot_goodwill_hunting_isomorphic.png\n")

    # --- Step 4: Show the two are different with BFS layout ---
    print("Step 4: Visualizing H vs H1 with BFS layout (appear different)")
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for graph, ax, ttl in zip((H, H1), axes, ("H (to node 3)", "H1 (to node 4)")):
        nx.draw(graph, pos=nx.bfs_layout(graph, 0),
                ax=ax, with_labels=True, node_color="lightyellow",
                edge_color="gray", node_size=300)
        ax.set_title(ttl)
    plt.tight_layout()
    plt.savefig("examples/algorithms/plot_goodwill_hunting_bfs_compare.png", dpi=150)
    plt.close()
    print("  Saved: plot_goodwill_hunting_bfs_compare.png\n")


def demo_brute_force():
    """Generate all nonisomorphic trees of order 10, filter homeomorphically irreducible ones.

    NetworkX provides nx.nonisomorphic_trees(n) which generates all unlabeled
    trees of order n. For n=10 there are 106 such trees. Filter for those
    with no degree-2 nodes to find the 10 homeomorphically irreducible trees.
    """
    print("=== Brute-Force Approach ===\n")

    n = 10
    print(f"Generating all nonisomorphic trees of order {n}...")
    all_trees = list(nx.nonisomorphic_trees(n))
    print(f"Total: {len(all_trees)} nonisomorphic trees\n")

    # Filter: no node with degree 2
    nhi_trees = [
        G for G in all_trees
        if not any(d == 2 for _, d in G.degree())
    ]
    print(f"Homeomorphically irreducible: {len(nhi_trees)}\n")

    # Sanity check: verify they are pairwise nonisomorphic
    print("Verifying pairwise non-isomorphism...")
    checked = []
    for G in nhi_trees:
        assert not any(nx.is_isomorphic(G, H) for H in checked), "Duplicate found!"
        checked.append(G)
    print("  All pairwise non-isomorphic ✓\n")

    # Print degrees for each tree
    print("Tree details (node counts per BFS layer):")
    for i, G in enumerate(nhi_trees):
        layers = [len(lyr) for lyr in nx.bfs_layers(G, 0)]
        degrees = sorted(dict(G.degree()).values())
        print(f"  #{i+1}: layers={layers} degrees={degrees}")

    # --- Plot 1: BFS layout (hierarchical) with layer labels ---
    print("\nPlotting all 10 trees (BFS layout)...")
    fig, axes = plt.subplots(2, 5, figsize=(20, 8))
    for G, ax in zip(nhi_trees, axes.ravel()):
        pos = nx.bfs_layout(G, 0)
        layers = [len(lyr) for lyr in nx.bfs_layers(G, 0)]
        nx.draw(G, pos=pos, ax=ax, with_labels=True,
                node_color="lightblue", edge_color="gray",
                node_size=250, font_size=8)
        ax.set_title(f"Layers: {layers}", fontsize=9)
        ax.axis("off")
    plt.tight_layout()
    plt.savefig("examples/algorithms/plot_goodwill_hunting_all_bfs.png", dpi=150)
    plt.close()
    print("  Saved: plot_goodwill_hunting_all_bfs.png")

    # --- Plot 2: Spring layout (movie-style) ---
    print("Plotting all 10 trees (spring layout)...")
    fig, axes = plt.subplots(2, 5, figsize=(20, 8))
    for G, ax in zip(nhi_trees, axes.ravel()):
        pos = nx.spring_layout(G, seed=1010, iterations=200)
        nx.draw(G, pos=pos, ax=ax, with_labels=True,
                node_color="lightgreen", edge_color="gray",
                node_size=250, font_size=8)
    plt.tight_layout()
    plt.savefig("examples/algorithms/plot_goodwill_hunting_all_spring.png", dpi=150)
    plt.close()
    print("  Saved: plot_goodwill_hunting_all_spring.png")

    # --- Plot 3: Individual trees with spring layout, numbered ---
    print("Plotting individual trees...")
    fig, axes = plt.subplots(2, 5, figsize=(20, 8))
    for i, (G, ax) in enumerate(zip(nhi_trees, axes.ravel())):
        pos = nx.spring_layout(G, seed=1010 + i, iterations=200)
        nx.draw(G, pos=pos, ax=ax, with_labels=True,
                node_color="lightcoral", edge_color="gray",
                node_size=250, font_size=8)
        layers = [len(lyr) for lyr in nx.bfs_layers(G, 0)]
        ax.set_title(f"#{i+1}: {layers}", fontsize=9)
    plt.tight_layout()
    plt.savefig("examples/algorithms/plot_goodwill_hunting_individual.png", dpi=150)
    plt.close()
    print("  Saved: plot_goodwill_hunting_individual.png")


if __name__ == "__main__":
    demo_qualitative_approach()
    print()
    demo_brute_force()
