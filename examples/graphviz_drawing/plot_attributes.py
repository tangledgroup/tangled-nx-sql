"""
Attributes
----------

An example showing how to use pydot for Graphviz DOT format with
node and edge attributes.

Adapted for nx_sql — uses SQLAlchemy persistence and pydot instead of pygraphviz.
"""

import matplotlib.pyplot as plt
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
def demo_attributes():
    """Create a graph with attributes and export to DOT format."""

    with Session() as session:
        G = nx_sql.Graph(session, name="attributes_demo")

        # Add nodes with various attributes
        G.add_node(1, label="Node 1", color="red", size=3000)
        G.add_node(2, label="Node 2", color="blue", size=2000)
        G.add_node(3, label="Node 3", color="green", size=1500)
        G.add_node(4, label="Node 4", color="orange", size=1000)

        # Add edges with attributes
        G.add_edge(1, 2, label="edge A-B", weight=3)
        G.add_edge(2, 3, label="edge B-C", weight=5)
        G.add_edge(3, 4, label="edge C-D", weight=2)
        G.add_edge(1, 4, label="edge A-D", weight=7)

        # Export to DOT with attributes
        dot_str = nx.drawing.nx_pydot.to_pydot(G).to_string()
        print("DOT with attributes:")
        print(dot_str)

        # Write DOT file
        with open("examples/graphviz_drawing/attributes.dot", "w") as f:
            f.write(dot_str)

        # Visualize with matplotlib
        pos = nx.spring_layout(G, seed=42)
        nx.draw_networkx_nodes(G, pos, node_size=[G.nodes[n].get("size", 1000) for n in G])
        nx.draw_networkx_labels(G, pos)
        edge_labels = nx.get_edge_attributes(G, "label")
        nx.draw_networkx_edge_labels(G, pos, edge_labels)
        plt.axis("off")
        plt.savefig("examples/graphviz_drawing/plot_attributes_output.png")
        plt.close()

        # Convert to pydot and save as PNG via graphviz if available
        dot_obj = nx.drawing.nx_pydot.to_pydot(G)
        try:
            dot_obj.write_png("examples/graphviz_drawing/attributes_graphviz.png", prog="dot")
            print("Also saved via graphviz: attributes_graphviz.png")
        except Exception:
            pass  # graphviz CLI may not be installed

        print("Saved: attributes.dot, plot_attributes_output.png")

        session.commit()


if __name__ == "__main__":
    demo_attributes()
