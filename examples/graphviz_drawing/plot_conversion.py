"""
Conversion
----------

An example showing how to convert NetworkX graphs to/from Graphviz DOT format.

Adapted for nx_sql — uses pydot for DOT I/O instead of pygraphviz.
Also demonstrates nx_sql persistence.
"""

import networkx as nx
import pydot
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
def demo_conversion():
    """Convert between NetworkX and Graphviz DOT format."""

    with Session() as session:
        G_nx = nx.complete_graph(5)

        # Store in nx_sql
        G = nx_sql.Graph(session, name="conversion_demo")
        G.add_nodes_from(G_nx.nodes())
        G.add_edges_from(G_nx.edges())

        # Convert to pydot (Graphviz DOT representation)
        dot_str = nx.drawing.nx_pydot.to_pydot(G).to_string()
        print("DOT format:")
        print(dot_str)

        # Write to .dot file
        dot_file = "examples/graphviz_drawing/k5.dot"
        with open(dot_file, "w") as f:
            f.write(dot_str)
        print(f"\nWrote DOT file to {dot_file}")

        # Read back from DOT using pydot directly
        dot_obj = pydot.graph_from_dot_data(dot_str)[0]
        G2 = nx.drawing.nx_pydot.from_pydot(dot_obj)
        print(f"Read back: {G2.number_of_nodes()} nodes, {G2.number_of_edges()} edges")

        # Fancy conversion: in-memory copy -> pydot -> Graph
        G_copy = nx.Graph(G_nx)
        dot_obj = nx.drawing.nx_pydot.to_pydot(G_copy)
        G1 = nx.drawing.nx_pydot.from_pydot(dot_obj)
        print(f"Fancy conversion: {G1.number_of_nodes()} nodes, {G1.number_of_edges()} edges")

        session.commit()


if __name__ == "__main__":
    demo_conversion()
