"""Generate a random graph and draw it to file.

Demonstrates creating an nx_sql graph from a NetworkX random graph,
running algorithms, and rendering a visual plot.
"""

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def demo_random_graph():
    """Generate a random Erdős-Rényi graph, compute statistics, and plot."""

    with Session() as session:
        # Generate a random graph and store it in SQL
        G_nx = nx.erdos_renyi_graph(20, 0.15, seed=42)
        G = nx_sql.Graph(session, name="random_graph_demo")
        G.add_nodes_from(G_nx.nodes())
        G.add_edges_from(G_nx.edges())

        # Compute graph statistics using the database-backed graph
        n_nodes = G.number_of_nodes()
        n_edges = G.number_of_edges()
        avg_degree = sum(dict(G.degree()).values()) / n_nodes if n_nodes else 0
        components = nx.number_connected_components(G)
        clustering = nx.average_clustering(G)

        print(f"Nodes: {n_nodes}")
        print(f"Edges: {n_edges}")
        print(f"Average degree: {avg_degree:.2f}")
        print(f"Connected components: {components}")
        print(f"Average clustering coefficient: {clustering:.4f}")

        # Layout and draw with color-coded degrees
        pos = nx.spring_layout(G, seed=42, k=0.5)
        degrees = [d for _, d in G.degree()]
        cmap = plt.cm.viridis
        node_colors = [d / max(degrees) for d in degrees] if max(degrees) else 1

        fig, ax = plt.subplots(figsize=(10, 8))
        nx.draw_networkx_nodes(G, pos, node_color=node_colors, cmap=cmap,
                               node_size=200, alpha=0.9, ax=ax)
        nx.draw_networkx_edges(G, pos, width=1.0, alpha=0.5, ax=ax)
        nx.draw_networkx_labels(G, pos, font_size=8, font_family="monospace", ax=ax)

        ax.set_title(f"Erdős-Rényi Graph (n={n_nodes}, p=0.15)", fontsize=14)
        ax.axis("off")
        plt.tight_layout()
        plt.savefig("examples/example2_random_graph.png", dpi=150, bbox_inches="tight")
        plt.close()
        print("Plot saved to examples/example2_random_graph.png")

        session.commit()


def demo_davis_southern_women():
    """Load the Davis Southern women network and draw with community colors."""

    with Session() as session:
        # Load a real-world social network
        G_nx = nx.davis_southern_women_graph()
        G = nx_sql.Graph(session, name="davis_women_demo")
        G.add_nodes_from(G_nx.nodes())
        G.add_edges_from(G_nx.edges())

        # Detect communities
        communities = nx.community.greedy_modularity_communities(G)
        print(f"Community count: {len(communities)}")
        for i, comm in enumerate(communities):
            print(f"  Community {i}: {len(comm)} nodes")

        # Assign colors per community
        community_colors = {}
        palette = ["#e41a1c", "#377eb8", "#4daf4a", "#984ea3", "#ff7f00", "#ffff33"]
        for idx, comm in enumerate(communities):
            color = palette[idx % len(palette)]
            for node in comm:
                community_colors[node] = color

        pos = nx.spring_layout(G, seed=1430)
        fig, ax = plt.subplots(figsize=(12, 10))
        nx.draw_networkx_nodes(G, pos, node_color=[community_colors[n] for n in G.nodes()],
                               node_size=300, alpha=0.85, ax=ax)
        nx.draw_networkx_edges(G, pos, width=1.5, alpha=0.6, ax=ax)
        nx.draw_networkx_labels(G, pos, font_size=9, font_family="sans-serif", ax=ax)

        # Legend for communities
        from matplotlib.lines import Line2D
        legend_elements = [Line2D([0], [0], marker='o', color='w',
                                  markerfacecolor=palette[i % len(palette)],
                                  markersize=8, label=f'Community {i}')
                           for i in range(len(communities))]
        ax.legend(handles=legend_elements, loc="upper right", fontsize=10)

        ax.set_title("Davis Southern Women Network", fontsize=14)
        ax.axis("off")
        plt.tight_layout()
        plt.savefig("examples/example2_davis_women.png", dpi=150, bbox_inches="tight")
        plt.close()
        print("Plot saved to examples/example2_davis_women.png")

        session.commit()


if __name__ == "__main__":
    demo_random_graph()
    print()
    demo_davis_southern_women()
