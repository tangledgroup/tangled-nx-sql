"""
===========
Eigenvalues
===========

Create an G{n,m} random graph and compute the eigenvalues.

Adapted for nx_sql — uses SQLAlchemy persistence instead of in-memory graphs.
"""

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base
import sys; sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent.parent.parent))
from examples.utils import print_docstring

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


@print_docstring
def demo_eigenvalues():
    """Compute and histogram eigenvalues of a random graph."""

    with Session() as session:
        n = 1000
        m = 5000
        G_nx = nx.gnm_random_graph(n, m, seed=5040)
        G = nx_sql.Graph(session, name="eigenvalues_demo")
        G.add_nodes_from(G_nx.nodes())
        G.add_edges_from(G_nx.edges())

        L = nx.normalized_laplacian_matrix(G)
        e = np.linalg.eigvals(L.toarray())
        print("Largest eigenvalue:", max(e))
        print("Smallest eigenvalue:", min(e))
        plt.hist(e, bins=100)
        plt.xlim(0, 2)
        plt.savefig("examples/drawing/plot_eigenvalues_output.png")
        plt.close()
        print("Plot saved to examples/drawing/plot_eigenvalues_output.png")

        session.commit()


if __name__ == "__main__":
    demo_eigenvalues()
