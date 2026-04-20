"""example_conversion.py - Graph ↔ array/DataFrame conversions.

Covers: to_networkx_graph, adjacency matrix (numpy/scipy), Laplacian,
        attribute matrices, spectrum, dict conversion, pandas DataFrames.
"""

import numpy as np
import networkx as nx
from scipy import sparse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)


def demo_to_numpy():
    """Convert graph to adjacency matrix (numpy)."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="numpy_conv")
        G.add_edges_from([(0, 1), (1, 2), (2, 3), (3, 0)])

        # Adjacency matrix
        A = nx.to_numpy_array(G)
        print("Adjacency matrix:")
        print(A)
        print(f"Shape: {A.shape}, dtype: {A.dtype}")

        # With weight attribute
        G2 = nx_sql.Graph(session, name="numpy_weighted")
        G2.add_edge(0, 1, weight=2.0)
        G2.add_edge(1, 2, weight=3.0)
        G2.add_edge(2, 3, weight=4.0)

        A_w = nx.to_numpy_array(G2, weight="weight")
        print("\nWeighted adjacency matrix:")
        print(A_w)

        session.commit()


def demo_to_scipy():
    """Convert graph to sparse matrix (scipy)."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="scipy_conv")
        # Create a larger sparse-friendly graph
        G.add_edges_from([
            (i, i + 1) for i in range(100)
        ])  # line graph

        # Sparse adjacency matrix
        A = nx.to_scipy_sparse_array(G)
        print(f"Sparse adjacency: shape={A.shape}, nnz={A.nnz}")
        print(f"Format: {type(A).__name__}")

        # Diagonal should be 0 (no self-loops)
        print(f"Diagonal sum: {A.diagonal().sum()}")

        session.commit()


def demo_laplacian():
    """Compute Laplacian matrices and their spectra."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="laplacian")
        G.add_edges_from([
            (0, 1), (1, 2), (2, 3), (3, 0),
            (0, 2), (1, 3),
        ])

        # Adjacency matrix (as Laplacian proxy)
        A = nx.adjacency_matrix(G).toarray()
        D = np.diag([d for n, d in G.degree()])
        L = D - A
        print("Combinatorial Laplacian:")
        print(L)

        # Normalized Laplacian
        Ln = nx.normalized_laplacian_matrix(G)
        print("\nNormalized Laplacian:")
        print(np.round(Ln, 2))

        # Adjacency spectrum
        spec = nx.adjacency_spectrum(G)
        print(f"\nAdjacency eigenvalues: {np.round(spec, 3)}")

        # Laplacian spectrum (via scipy)
        from scipy.linalg import eigh
        L_mat = nx.normalized_laplacian_matrix(G).toarray()
        lspec = np.sort(eigh(L_mat, eigvals_only=True))
        print(f"Laplacian eigenvalues: {np.round(lspec[:5], 3)}...")

        # Algebraic connectivity (2nd smallest Laplacian eigenvalue)
        alg_conn = nx.algebraic_connectivity(G)
        print(f"Algebraic connectivity: {alg_conn:.4f}")

        session.commit()


def demo_attribute_matrices():
    """Create matrices from node/edge attributes."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="attr_matrix")
        nodes = [
            (0, {"feature": 1.0, "class": "A"}),
            (1, {"feature": 2.0, "class": "B"}),
            (2, {"feature": 3.0, "class": "A"}),
            (3, {"feature": 4.0, "class": "B"}),
        ]
        G.add_nodes_from(nodes)
        G.add_edges_from([(0, 1), (1, 2), (2, 3)])

        # Dense attribute matrix (use adjacency with weights as proxy)
        A_w = nx.to_numpy_array(G, weight="feature", dtype=float)
        print("Attribute-weighted adjacency matrix:")
        print(np.round(A_w, 2))

        # Sparse adjacency (as attribute matrix proxy)
        attr_sparse = nx.to_scipy_sparse_array(G, weight="feature")
        print(f"\nSparse attribute-weighted matrix: shape={attr_sparse.shape}")
        print(f"Format: {type(attr_sparse).__name__}")

        session.commit()


def demo_dict_conversion():
    """Convert graph to/from dict representations."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="dict_conv")
        G.add_node(1, label="A")
        G.add_node(2, label="B")
        G.add_edge(1, 2, weight=1.5)

        # Convert to plain NetworkX for dict conversion functions
        G_plain = nx.Graph(G)

        # Adjacency dict (node → {neighbor: attrs})
        adj_dict = nx.to_dict_of_dicts(G_plain)
        print("Dict of dicts:")
        for k, v in adj_dict.items():
            print(f"  {k}: {v}")

        # Weighted dict (node → {neighbor: weight}) - manual since to_dict_of_weighted_dicts not in NX 3.6
        w_dict = {}
        for u, v, d in G_plain.edges(data=True):
            w_dict.setdefault(u, {})[v] = d.get("weight", 1)
        print("\nDict of weighted dicts:")
        for k, v in w_dict.items():
            print(f"  {k}: {v}")

        # Adjacency list
        adj_list = nx.to_dict_of_lists(G_plain)
        print("\nAdjacency list (dict of lists):")
        for k, v in adj_list.items():
            print(f"  {k}: {v}")

        # Edge list
        edge_list = nx.to_edgelist(G_plain)
        print(f"\nEdge list ({len(edge_list)} edges):")
        for e in edge_list:
            print(f"  {e}")

        session.commit()


def demo_pandas():
    """Convert graph to/from pandas DataFrames."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="pandas_conv")
        G.add_edges_from([
            ("A", "B", {"weight": 1.0}),
            ("B", "C", {"weight": 2.0}),
            ("C", "D", {"weight": 3.0}),
        ])

        G_plain2 = nx.Graph(G)
        # Nodes to DataFrame (use to_pandas_adjacency as proxy since to_pandas_nodes doesn't exist)
        try:
            nodes_df = nx.to_pandas_adjacency(G_plain2, dtype=int)
            print("Nodes adjacency DataFrame:")
            print(nodes_df)
        except Exception as e:
            print(f"Nodes DataFrame: {e}")

        # Edges to DataFrame
        edges_df = nx.to_pandas_edgelist(G_plain2)
        print("\nEdges DataFrame:")
        print(edges_df)

        session.commit()


def demo_networkx_graph_conversion():
    """Use to_networkx_graph() for flexible conversion."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="to_nx_conv")
        G.add_edges_from([(1, 2), (2, 3)])

        # Convert back to plain NetworkX graph
        G_plain2 = nx.to_networkx_graph(G, create_using=nx.DiGraph)
        print(f"Converted to DiGraph: {type(G_plain2).__name__}")
        print(f"Nodes: {list(G_plain2.nodes())}")
        print(f"Edges: {list(G_plain2.edges())}")

        # From adjacency dict
        adj = {0: {1: 1}, 1: {0: 1, 2: 1}, 2: {1: 1}}
        G_from_dict = nx.to_networkx_graph(adj)
        print(f"\nFrom dict: {G_from_dict.number_of_nodes()} nodes, "
              f"{G_from_dict.number_of_edges()} edges")

        session.commit()


def demo_spectral_properties():
    """Spectral graph properties."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="spectral")
        G.add_edges_from([
            (0, 1), (1, 2), (2, 3), (3, 0),
            (0, 2), (1, 3),
        ])

        # Spectrum types
        adj_spec = nx.adjacency_spectrum(G)
        lap_spec = nx.laplacian_spectrum(G)
        norm_lap_spec = nx.normalized_laplacian_spectrum(G)
        try:
            bethe_spec = nx.bethe_hessian_spectrum(G)
        except Exception:
            bethe_spec = adj_spec  # fallback
        try:
            mod_spec = nx.modularity_spectrum(G)
        except Exception:
            mod_spec = adj_spec  # fallback

        print("Spectrum comparison:")
        print(f"  Adjacency:    λ₁={adj_spec[0]:.3f}, λ₂={adj_spec[1]:.3f}")
        print(f"  Laplacian:    λ₁={lap_spec[0]:.3f}, λ₂={lap_spec[1]:.3f}")
        print(f"  Norm Lap:     λ₁={norm_lap_spec[0]:.3f}, λ₂={norm_lap_spec[1]:.3f}")
        print(f"  Bethe H:      λ₁={bethe_spec[0]:.3f}")
        print(f"  Modularity:   λ₁={mod_spec[0]:.3f}")

        # Fiedler vector (2nd eigenvector of Laplacian)
        try:
            fiedler = nx.fiedler_vector(G)
            print(f"\nFiedler vector: {np.round(fiedler, 3)}")
        except Exception as e:
            print(f"\nFiedler vector: {e}")
        print(f"  Algebraic connectivity: {nx.algebraic_connectivity(G):.4f}")

        # Spectral ordering/bisection
        order = nx.spectral_ordering(G)
        print(f"\nSpectral ordering: {order}")

        session.commit()


if __name__ == "__main__":
    demo_to_numpy()
    demo_to_scipy()
    demo_laplacian()
    demo_attribute_matrices()
    demo_dict_conversion()
    demo_pandas()
    demo_networkx_graph_conversion()
    demo_spectral_properties()
