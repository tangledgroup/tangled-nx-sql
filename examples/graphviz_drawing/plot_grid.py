"""
Grid
----

An example showing how to create and visualize a grid graph with
Graphviz DOT format using pydot.

Adapted for nx_sql — uses SQLAlchemy persistence and pydot instead of pygraphviz.
"""

import matplotlib.pyplot as plt
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
def demo_grid():
    """Create a grid graph and export to Graphviz DOT format."""

    with Session() as session:
        G_nx = nx.grid_2d_graph(4, 4)
        G = nx_sql.Graph(session, name="grid_demo")
        G.add_nodes_from(G_nx.nodes())
        G.add_edges_from(G_nx.edges())

        # Export to DOT
        dot_str = nx.drawing.nx_pydot.to_pydot(G).to_string()
        with open("examples/graphviz_drawing/grid.dot", "w") as f:
            f.write(dot_str)
        print(f"DOT file: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

        # Visualize
        pos = {(x, y): (x, -y) for x, y in G.nodes()}
        nx.draw(G, pos=pos, with_labels=True, node_color="lightblue",
                node_size=500, font_size=8)
        plt.title("4x4 Grid Graph")
        plt.savefig("examples/graphviz_drawing/plot_grid_output.png")
        plt.close()
        print("Saved: grid.dot, plot_grid_output.png")

        session.commit()


if __name__ == "__main__":
    demo_grid()
