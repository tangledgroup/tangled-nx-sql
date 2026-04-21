"""
Mini Atlas
----------

An example showing all connected graphs with up to 5 nodes in Graphviz DOT format.

Adapted for nx_sql — uses pydot instead of pygraphviz.
"""

import networkx as nx
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
def demo_mini_atlas():
    """Generate and export the atlas of small connected graphs."""

    with Session() as session:
        Atlas = nx.graph_atlas_g()[3:72]  # Graphs with at least 1 edge, up to 4 nodes
        connected = [G for G in Atlas if nx.number_connected_components(G) == 1]

        print(f"Atlas of {len(connected)} connected graphs (up to 4 nodes)")

        # Store each graph in nx_sql
        for i, G_nx in enumerate(connected[:10]):  # Limit to first 10 for demo
            G = nx_sql.Graph(session, name=f"atlas_{i}")
            G.add_nodes_from(G_nx.nodes())
            G.add_edges_from(G_nx.edges())
            print(f"  Graph {i}: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

        # Export first graph to DOT
        if connected:
            dot_str = nx.drawing.nx_pydot.to_pydot(connected[0]).to_string()
            with open("examples/graphviz_drawing/mini_atlas.dot", "w") as f:
                f.write(dot_str)
            print(f"\nSaved first graph to mini_atlas.dot")

        session.commit()


if __name__ == "__main__":
    demo_mini_atlas()
