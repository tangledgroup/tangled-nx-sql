"""Demonstrate basic undirected Graph operations with nx_sql.

Mirrors networkx/examples/basic/plot_simple_graph.py but uses SQLAlchemy persistence.
Shows node creation, edge addition, iteration, and attribute access.
"""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base, Graph as GraphModel
import sys; sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent.parent.parent))
from examples.utils import print_docstring

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


@print_docstring
def demo_simple_graph():
    """Create undirected Graph with manual positions, test basic operations."""

    with Session() as session:
        G = nx_sql.Graph(session, name="simple_graph_demo")

        # Add nodes with attributes (manual layout positions)
        G.add_node(1, color="red", pos=(0, 0))
        G.add_node(2, color="blue", pos=(1, 0))
        G.add_node(3, color="green", pos=(2, 0))
        G.add_node(4, color="yellow", pos=(3, 0))

        # Add edges
        G.add_edge(1, 2)
        G.add_edge(2, 3)
        G.add_edge(3, 4)
        G.add_edge(1, 4)

        print(f"Nodes ({G.number_of_nodes()}): {list(G.nodes())}")
        print(f"Node data: {list(G.nodes(data=True))}")
        print(f"Edges ({G.number_of_edges()}): {list(G.edges())}")
        print(f"Edge data: {list(G.edges(data=True))}")

        # Test adjacency iteration
        for node in G:
            neighbors = list(G[node])
            print(f"  Node {node} neighbors: {neighbors}")

        # Test edge lookup
        assert (1, 2) in G.edges()
        assert G.has_edge(1, 2)
        assert G[1][2] == {}
        print("Edge lookup G[1][2]:", G[1][2])

        # Test neighbor iteration
        print(f"Neighbors of 2: {list(G.neighbors(2))}")

        session.commit()

    # Verify persistence: load the graph in a new session
    with Session() as session:
        # Find the graph by name
        gmodel = session.execute(
            nx_sql.select(GraphModel).where(GraphModel.name == "simple_graph_demo")
        ).scalar_one()
        G2 = nx_sql.Graph(session, graph_id=gmodel.graph_id)
        print(f"\nReloaded from DB - Nodes: {list(G2.nodes())}")
        print(f"Reloaded from DB - Edges: {list(G2.edges())}")
        session.commit()


if __name__ == "__main__":
    demo_simple_graph()
