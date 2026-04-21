"""
=================
Custom node icons
=================

Example of using custom node styles to represent different node types.

Adapted for nx_sql — uses SQLAlchemy persistence instead of in-memory graphs.
Original used external image files; this version uses colored nodes as alternatives.
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
def demo_custom_node_icons():
    """Visualize a network with different node types (router, switch, PC)."""

    with Session() as session:
        G = nx_sql.Graph(session, name="custom_icons_demo")

        # Add nodes with type attributes
        G.add_node("router", node_type="router")
        for i in range(1, 4):
            G.add_node(f"switch_{i}", node_type="switch")
            for j in range(1, 4):
                G.add_node("PC_" + str(i) + "_" + str(j), node_type="pc")

        # Add edges
        G.add_edge("router", "switch_1")
        G.add_edge("router", "switch_2")
        G.add_edge("router", "switch_3")
        for u in range(1, 4):
            for v in range(1, 4):
                G.add_edge("switch_" + str(u), "PC_" + str(u) + "_" + str(v))

        pos = nx.spring_layout(G, seed=1734289230)

        # Color by node type
        routers = [n for n, d in G.nodes(data=True) if d.get("node_type") == "router"]
        switches = [n for n, d in G.nodes(data=True) if d.get("node_type") == "switch"]
        pcs = [n for n, d in G.nodes(data=True) if d.get("node_type") == "pc"]

        nx.draw_networkx_nodes(G, pos, nodelist=routers, node_color="red", node_size=500)
        nx.draw_networkx_nodes(G, pos, nodelist=switches, node_color="blue", node_size=300)
        nx.draw_networkx_nodes(G, pos, nodelist=pcs, node_color="green", node_size=100)
        nx.draw_networkx_edges(G, pos)

        plt.savefig("examples/drawing/plot_custom_node_icons_output.png")
        plt.close()
        print("Plot saved to examples/drawing/plot_custom_node_icons_output.png")

        session.commit()


if __name__ == "__main__":
    demo_custom_node_icons()
