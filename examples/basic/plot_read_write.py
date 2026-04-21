"""Demonstrate graph persistence with nx_sql (serialization/deserialization).

Mirrors networkx/examples/basic/plot_read_write.py but uses SQLAlchemy persistence.
Shows that graph data persists across sessions and can be reloaded.
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
def demo_read_write():
    """Build a graph, persist it, then reload from a fresh session."""

    # --- Session 1: Build and persist ---
    with Session() as session:
        G = nx_sql.Graph(session, name="read_write_demo")

        # Add nodes and edges
        G.add_node("X", description="source")
        G.add_node("Y", description="intermediate")
        G.add_node("Z", description="sink")
        G.add_edge("X", "Y", weight=2.0)
        G.add_edge("Y", "Z", weight=3.0)
        G.add_edge("X", "Z", weight=10.0)

        # Compute something before committing
        shortest = nx.shortest_path(G, "X", "Z", weight="weight")
        print(f"Session 1 - Shortest path X->Z: {shortest}")

        session.commit()
        graph_id = G.graph_id
        print(f"Session 1 - Graph ID: {graph_id}")

    # --- Session 2: Reload from DB ---
    with Session() as session:
        # Find the persisted graph
        gmodel = session.execute(
            nx_sql.select(GraphModel).where(GraphModel.name == "read_write_demo")
        ).scalar_one()

        G2 = nx_sql.Graph(session, graph_id=gmodel.graph_id)
        print(f"\nSession 2 - Reloaded nodes: {list(G2.nodes())}")
        print(f"Session 2 - Reloaded edges: {list(G2.edges(data=True))}")

        # Verify the same computation works
        shortest2 = nx.shortest_path(G2, "X", "Z", weight="weight")
        print(f"Session 2 - Shortest path X->Z: {shortest2}")

        assert shortest == shortest2, "Shortest paths should match across sessions"
        print("✓ Persistence verified: data matches across sessions")

        session.commit()


if __name__ == "__main__":
    demo_read_write()
