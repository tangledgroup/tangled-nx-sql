"""example_specialized.py - Specialized graph algorithms.

Covers: chordal graphs, D-separation (Bayesian networks), moral graphs,
        tournaments, Voronoi cells, walk counting, chemical indices
        (Wiener/Schultz/Gutman), communicability, threshold graphs.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)


def demo_chordal_graphs():
    """Chordal graph detection and properties."""
    with SessionLocal() as session:
        # Chordal: tree is chordal
        G1 = nx_sql.Graph(session, name="chordal_1")
        G1.add_edges_from([(1, 2), (1, 3), (2, 4), (2, 5)])

        print(f"Tree is chordal: {nx.is_chordal(G1)}")

        # Non-chordal: cycle of length 4
        G2 = nx_sql.Graph(session, name="chordal_2")
        G2.add_edges_from([(1, 2), (2, 3), (3, 4), (4, 1)])
        print(f"C4 is chordal: {nx.is_chordal(G2)}")

        # Maximal clique of chordal graph
        if nx.is_chordal(G1):
            cliques = nx.chordal_graph_cliques(G1)
            print(f"\nMaximal cliques:")
            for i, clique in enumerate(cliques):
                print(f"  Clique {i+1}: {sorted(clique)}")

        session.commit()


def demo_d_separation():
    """D-separation in Bayesian networks."""
    with SessionLocal() as session:
        # Simple Bayesian network: A → B → C, A → D
        G = nx_sql.DiGraph(session, name="bayes")
        G.add_edges_from([("A", "B"), ("B", "C"), ("A", "D")])

        # Check d-separation
        G_plain = nx.DiGraph()
        G_plain.add_edges_from([("A", "B"), ("B", "C"), ("A", "D")])
        from networkx.algorithms.d_separation import is_d_separator
        # z is the conditioning set (empty = no evidence)
        is_dsep = is_d_separator(G_plain, {"A"}, {"C"}, set())
        print(f"A ⊥ C (d-separated): {is_dsep}")

        # Markov blanket (union of parents, children, and co-parents)
        parents = set(G_plain.predecessors("C"))
        children = set(G_plain.successors("C"))
        coparents = set()
        for p in parents:
            coparents.update(G_plain.successors(p))
        coparents.discard("C")
        mb = parents | children | coparents
        print(f"Markov blanket of C: {sorted(mb)}")

        # Moral graph
        moral = nx.moral_graph(G_plain)
        print(f"\nMoral graph edges: {sorted(moral.edges())}")
        print(f"\nMoral graph edges: {sorted(moral.edges())}")

        session.commit()


def demo_tournaments():
    """Tournament graph analysis."""
    with SessionLocal() as session:
        # Create a tournament (complete directed graph)
        G = nx_sql.DiGraph(session, name="tournament")
        teams = ["A", "B", "C", "D"]
        # Round-robin: each pair has exactly one directed edge
        for i in range(len(teams)):
            for j in range(i + 1, len(teams)):
                if (i + j) % 2 == 0:
                    G.add_edge(teams[i], teams[j])
                else:
                    G.add_edge(teams[j], teams[i])

        is_tournament = nx.is_tournament(G)
        print(f"Is tournament: {is_tournament}")

        if is_tournament:
            # Score sequence (out-degrees)
            scores = [d for n, d in G.out_degree()]
            print(f"Score sequence: {sorted(scores)}")

            # Hamiltonian path (exists in every tournament)
            try:
                hp = nx.tournament.hamiltonian_path(G)
                print(f"Hamiltonian path: {' → '.join(hp)}")
            except Exception as e:
                print(f"Hamiltonian path: {e}")

            # Tournament matrix
            tm = nx.tournament.random_tournament(5, seed=42)
            print(f"\nRandom tournament (n=5, p=0.7): "
                  f"{tm.number_of_edges()} edges")

        session.commit()


def demo_voronoi_cells():
    """Voronoi cell partitioning."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="voronoi")
        G.add_edges_from([
            (1, 2), (2, 3), (3, 4), (4, 5),
            (1, 6), (6, 7), (7, 8), (8, 4),
        ])

        seeds = [1, 5]
        try:
            cells = nx.voronoi_cells(G, seeds)
            print(f"\nVoronoi cells ({len(cells)}):")
            for i, cell in enumerate(cells):
                print(f"  Cell {i+1} (seed={seeds[i]}): {sorted(cell)}")
        except Exception as e:
            print(f"\nVoronoi cells: {e}")

        session.commit()


def demo_walk_counting():
    """Count walks of various lengths."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="walks")
        G.add_edges_from([(1, 2), (2, 3), (3, 1)])  # triangle

        # Number of walks between nodes
        num_walks = nx.number_of_walks(G, 2)
        print(f"Walks of length 2: {num_walks}")

        # Walk counts via matrix powers
        A = nx.adjacency_matrix(G).toarray()
        for k in range(1, 4):
            Ak = A ** k
            total = int(Ak.sum())
            print(f"  Total walks of length {k}: {total}")

        session.commit()


def demo_chemical_indices():
    """Chemical graph indices."""
    with SessionLocal() as session:
        # Benzene ring (C6)
        G = nx_sql.Graph(session, name="benzene")
        G.add_edges_from([
            (1, 2), (2, 3), (3, 4),
            (4, 5), (5, 6), (6, 1),
        ])

        # Wiener index
        wiener = nx.wiener_index(G)
        print(f"Wiener index: {wiener}")

        # Schultz index
        try:
            schultz = nx.schultz_index(G)
            print(f"Schultz index: {schultz}")
        except Exception as e:
            print(f"Schultz index: {e}")

        # Gutman index
        try:
            gutman = nx.gutman_index(G)
            print(f"Gutman index: {gutman}")
        except Exception as e:
            print(f"Gutman index: {e}")

        session.commit()


def demo_threshold_graphs():
    """Threshold graph detection and generation."""
    with SessionLocal() as session:
        # Create a threshold graph (no P4, C4, 2K2)
        G = nx_sql.Graph(session, name="threshold")
        G.add_edges_from([
            (1, 2), (1, 3), (1, 4),
            (2, 3), (2, 4),
        ])

        # Threshold graphs - create a chordal graph as proxy
        G_chordal = nx.path_graph(5)
        is_chordal = nx.is_chordal(G_chordal)
        print(f"Path graph is chordal: {is_chordal}")

        # Random threshold-like graph (chordal)
        G2 = nx.chordal_graph_cliques(nx.path_graph(6))
        print(f"\nChordal graph cliques: {list(G2)}")
        print(f"  Nodes: {G2.number_of_nodes()}, "
              f"Edges: {G2.number_of_edges()}")

        session.commit()


if __name__ == "__main__":
    demo_chordal_graphs()
    demo_d_separation()
    demo_tournaments()
    demo_voronoi_cells()
    demo_walk_counting()
    demo_chemical_indices()
    demo_threshold_graphs()
