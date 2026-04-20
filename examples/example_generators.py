"""example_generators.py - Graph generators with nx_sql storage.

Covers: erdos_renyi_graph, barabasi_albert_graph, watts_strogatz_graph,
        complete/cycle/path/grid/lattice graphs, small-world, scale-free,
        random geometric, social models, degree sequence generators.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)


def demo_random_graphs():
    """Generate and store random graphs."""
    with SessionLocal() as session:
        # Erdős-Rényi random graph
        G_er = nx.erdos_renyi_graph(n=30, p=0.15, seed=42)
        G = nx_sql.Graph(session, name="er_random")
        G.add_nodes_from(G_er.nodes())
        G.add_edges_from(G_er.edges())
        print(f"Erdős-Rényi (n=30, p=0.15): {G.number_of_nodes()} nodes, "
              f"{G.number_of_edges()} edges, avg_deg={2*G.number_of_edges()/G.number_of_nodes():.2f}")

        # Barabási-Albert scale-free
        G_ba = nx.barabasi_albert_graph(n=30, m=3, seed=42)
        G = nx_sql.Graph(session, name="ba_scalefree")
        G.add_nodes_from(G_ba.nodes())
        G.add_edges_from(G_ba.edges())
        print(f"\nBarabási-Albert (n=30, m=3): {G.number_of_nodes()} nodes, "
              f"{G.number_of_edges()} edges")
        degrees = [d for n, d in G.degree()]
        print(f"  Degree range: [{min(degrees)}, {max(degrees)}]")
        print(f"  Clustering: {nx.average_clustering(G):.4f}")

        # Watts-Strogatz small-world
        G_ws = nx.watts_strogatz_graph(n=30, k=4, p=0.3, seed=42)
        G = nx_sql.Graph(session, name="ws_smallworld")
        G.add_nodes_from(G_ws.nodes())
        G.add_edges_from(G_ws.edges())
        print(f"\nWatts-Strogatz (n=30, k=4, p=0.3): {G.number_of_nodes()} nodes, "
              f"{G.number_of_edges()} edges")
        print(f"  Avg clustering: {nx.average_clustering(G):.4f}")
        print(f"  Avg path length: {nx.average_shortest_path_length(G):.2f}")

        session.commit()


def demo_classic_graphs():
    """Generate classic graphs."""
    with SessionLocal() as session:
        # Complete graph
        G = nx_sql.Graph(session, name="complete_k10")
        G.add_nodes_from(nx.complete_graph(10).nodes())
        G.add_edges_from(nx.complete_graph(10).edges())
        print(f"K₁₀: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges "
              f"(n*(n-1)/2={10*9//2})")

        # Cycle graph
        G = nx_sql.Graph(session, name="cycle_c10")
        G.add_nodes_from(nx.cycle_graph(10).nodes())
        G.add_edges_from(nx.cycle_graph(10).edges())
        print(f"C₁₀: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        print(f"  Diameter: {nx.diameter(G)}")

        # Path graph
        G = nx_sql.Graph(session, name="path_p10")
        G.add_nodes_from(nx.path_graph(10).nodes())
        G.add_edges_from(nx.path_graph(10).edges())
        print(f"P₁₀: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        print(f"  Diameter: {nx.diameter(G)}")

        # Petersen graph
        G = nx_sql.Graph(session, name="petersen")
        G.add_nodes_from(nx.petersen_graph().nodes())
        G.add_edges_from(nx.petersen_graph().edges())
        print(f"\nPetersen: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        print(f"  Regular (3-regular): {all(d == 3 for n, d in G.degree())}")

        # Grid graph
        G = nx_sql.Graph(session, name="grid_5x5")
        G.add_nodes_from(nx.grid_2d_graph(5, 5).nodes())
        G.add_edges_from(nx.grid_2d_graph(5, 5).edges())
        print(f"\nGrid 5×5: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

        # Hypercube
        G = nx_sql.Graph(session, name="hypercube_4")
        G.add_nodes_from(nx.hypercube_graph(4).nodes())
        G.add_edges_from(nx.hypercube_graph(4).edges())
        print(f"Q₄ (4D hypercube): {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

        session.commit()


def demo_lattice():
    """Generate lattice graphs."""
    with SessionLocal() as session:
        # 1D ring lattice (via WS with p=0)
        G = nx_sql.Graph(session, name="ring_20")
        G.add_nodes_from(nx.watts_strogatz_graph(20, 4, 0.0, seed=42).nodes())
        G.add_edges_from(nx.watts_strogatz_graph(20, 4, 0.0, seed=42).edges())
        print(f"Ring lattice (n=20, k=4): {G.number_of_nodes()} nodes, "
              f"{G.number_of_edges()} edges")

        # Hexagonal lattice
        G2 = nx_sql.Graph(session, name="hex_lattice")
        G2.add_nodes_from(nx.hexagonal_lattice_graph(3, 3).nodes())
        G2.add_edges_from(nx.hexagonal_lattice_graph(3, 3).edges())
        print(f"\nHexagonal lattice (3x3): {G2.number_of_nodes()} nodes, "
              f"{G2.number_of_edges()} edges")

        session.commit()


def demo_tree_graphs():
    """Generate tree structures."""
    with SessionLocal() as session:
        # Binary tree
        G = nx_sql.Graph(session, name="binary_tree")
        G.add_nodes_from(nx.balanced_tree(2, 4).nodes())
        G.add_edges_from(nx.balanced_tree(2, 4).edges())
        print(f"Balanced binary tree (height=4): {G.number_of_nodes()} nodes, "
              f"{G.number_of_edges()} edges")
        print(f"  Diameter: {nx.diameter(G)}")

        # Star tree
        G = nx_sql.Graph(session, name="star_tree")
        G.add_nodes_from(nx.star_graph(10).nodes())
        G.add_edges_from(nx.star_graph(10).edges())
        print(f"\nStar (center + 10 leaves): {G.number_of_nodes()} nodes, "
              f"{G.number_of_edges()} edges")

        session.commit()


def demo_social_models():
    """Generate social network models."""
    with SessionLocal() as session:
        # Krackhardt kite graph (classic social network)
        G = nx_sql.Graph(session, name="krackhardt_kite")
        G.add_nodes_from(nx.krackhardt_kite_graph().nodes())
        G.add_edges_from(nx.krackhardt_kite_graph().edges())
        print(f"Krackhardt kite: {G.number_of_nodes()} nodes, "
              f"{G.number_of_edges()} edges")
        print(f"  Clustering: {nx.average_clustering(G):.4f}")

        # Lollipop graph
        G = nx_sql.Graph(session, name="lollipop")
        G.add_nodes_from(nx.lollipop_graph(8, 4).nodes())
        G.add_edges_from(nx.lollipop_graph(8, 4).edges())
        print(f"\nLollipop (K₈ + path₄): {G.number_of_nodes()} nodes, "
              f"{G.number_of_edges()} edges")

        # Motzkin graph (alias: motzkin_graph → not in this version, use lollipop as stand-in)
        G = nx_sql.Graph(session, name="motzkin")
        G.add_edges_from(nx.lollipop_graph(5, 3).edges())
        print(f"Lollipop (as Motzkin substitute): {G.number_of_nodes()} nodes, "
              f"{G.number_of_edges()} edges")

        session.commit()


def demo_degree_sequences():
    """Generate graphs from degree sequences."""
    with SessionLocal() as session:
        # Configuration model (random graph with given degree sequence)
        degrees = [5, 4, 4, 3, 3, 3, 2, 2, 2, 2]  # sum must be even
        G = nx_sql.Graph(session, name="config_model")
        G.add_nodes_from(range(len(degrees)))
        G.add_edges_from(nx.configuration_model(degrees).edges())
        # Remove self-loops and multiedges for clean storage
        G.remove_edges_from(nx.selfloop_edges(G))
        print(f"Configuration model (degrees={degrees}): "
              f"{G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

        session.commit()


if __name__ == "__main__":
    demo_random_graphs()
    demo_classic_graphs()
    demo_lattice()
    demo_tree_graphs()
    demo_social_models()
    demo_degree_sequences()
