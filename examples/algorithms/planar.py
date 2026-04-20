"""Demonstrate planarity testing with nx_sql.

Tests whether a graph can be drawn on a plane without edge crossings.
Uses the Kuratowski theorem: a graph is non-planar iff it contains
a subgraph homeomorphic to K5 or K3,3.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def demo_planar():
    """Test planarity on various graphs."""

    with Session() as session:
        # Planar graph: a tree
        print(f"=== Planarity Testing ===")
        G_tree = nx_sql.Graph(session, name="planar_tree_demo")
        G_tree.add_edges_from([(0, 1), (0, 2), (1, 3), (1, 4)])
        is_planar, _ = nx.check_planarity(G_tree)
        print(f"Tree: planar={is_planar}")

        # Planar graph: cycle
        G_cycle = nx_sql.Graph(session, name="planar_cycle_demo")
        G_cycle.add_edges_from([(0, 1), (1, 2), (2, 3), (3, 0)])
        is_planar, _ = nx.check_planarity(G_cycle)
        print(f"Cycle C4: planar={is_planar}")

        # Planar graph: outerplanar
        G_outer = nx_sql.Graph(session, name="planar_outer_demo")
        G_outer.add_edges_from([(0, 1), (1, 2), (2, 3), (3, 4), (4, 0), (0, 2), (2, 4)])
        is_planar, _ = nx.check_planarity(G_outer)
        print(f"Outerplanar graph: planar={is_planar}")

        # Non-planar graph: K5 (complete graph on 5 nodes)
        G_k5 = nx_sql.Graph(session, name="planar_k5_demo")
        for i in range(5):
            for j in range(i + 1, 5):
                G_k5.add_edge(i, j)
        is_planar, _ = nx.check_planarity(G_k5)
        print(f"\nK5 (complete, 5 nodes, 10 edges): planar={is_planar}")

        # Non-planar graph: K3,3 (complete bipartite)
        G_k33 = nx_sql.Graph(session, name="planar_k33_demo")
        for i in range(3):
            for j in range(3, 6):
                G_k33.add_edge(i, j)
        is_planar, _ = nx.check_planarity(G_k33)
        print(f"K3,3 (complete bipartite, 6 nodes, 9 edges): planar={is_planar}")

        # Karate club: non-planar
        G_nx = nx.karate_club_graph()
        G_kc = nx_sql.Graph(session, name="planar_karate_demo")
        G_kc.add_nodes_from(G_nx.nodes())
        G_kc.add_edges_from(G_nx.edges())
        is_planar, _ = nx.check_planarity(G_kc)
        print(f"\nKarate club ({G_kc.number_of_nodes()} nodes, {G_kc.number_of_edges()} edges): planar={is_planar}")

        # Planar embedding of K4
        G_k4 = nx_sql.Graph(session, name="planar_k4_demo")
        G_k4.add_edges_from([(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)])
        is_planar, _ = nx.check_planarity(G_k4)
        print(f"\nK4 (complete, 4 nodes, 6 edges): planar={is_planar}")

        session.commit()


if __name__ == "__main__":
    demo_planar()
