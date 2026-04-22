"""
===========
Print Graph
===========

Example subclass of the Graph class.

Adapted for nx_sql — uses SQLAlchemy persistence instead of in-memory graphs.
"""

import matplotlib.pyplot as plt
import networkx as nx
from networkx import Graph
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sys

import nx_sql
from nx_sql.models import Base
from examples.utils import print_docstring

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


class PrintGraph(Graph):
    """Example subclass of the Graph class that prints activity log."""

    def __init__(self, data=None, name="", file=None, **attr):
        super().__init__(data=data, name=name, **attr)
        if file is None:
            self.fh = sys.stdout
        else:
            self.fh = open(file, "w")

    def add_node(self, n, attr_dict=None, **attr):
        super().add_node(n, attr_dict=attr_dict, **attr)
        self.fh.write(f"Add node: {n}\n")

    def add_nodes_from(self, nodes, **attr):
        for n in nodes:
            self.add_node(n, **attr)

    def remove_node(self, n):
        super().remove_node(n)
        self.fh.write(f"Remove node: {n}\n")

    def remove_nodes_from(self, nodes):
        for n in nodes:
            self.remove_node(n)

    def add_edge(self, u, v, attr_dict=None, **attr):
        super().add_edge(u, v, attr_dict=attr_dict, **attr)
        self.fh.write(f"Add edge: {u}-{v}\n")

    def add_edges_from(self, ebunch, attr_dict=None, **attr):
        for e in ebunch:
            u, v = e[0:2]
            self.add_edge(u, v, attr_dict=attr_dict, **attr)

    def remove_edge(self, u, v):
        super().remove_edge(u, v)
        self.fh.write(f"Remove edge: {u}-{v}\n")

    def remove_edges_from(self, ebunch):
        for e in ebunch:
            u, v = e[0:2]
            self.remove_edge(u, v)

    def clear(self):
        super().clear()
        self.fh.write("Clear graph\n")


@print_docstring
def demo_printgraph():
    """Demonstrate PrintGraph subclass logging behavior."""

    # First test with stdout
    print("=== Test 1: PrintGraph with stdout ===")
    G = PrintGraph()
    G.add_node("foo")
    G.add_nodes_from("bar", weight=8)
    G.remove_node("b")
    G.remove_nodes_from("ar")
    print("Nodes in G: ", G.nodes(data=True))
    G.add_edge(0, 1, weight=10)
    print("Edges in G: ", G.edges(data=True))
    G.remove_edge(0, 1)
    G.add_edges_from(zip(range(3), range(1, 4)), weight=10)
    print("Edges in G: ", G.edges(data=True))
    G.remove_edges_from(zip(range(3), range(1, 4)))
    print("Edges in G: ", G.edges(data=True))

    # Second test
    print("\n=== Test 2: PrintGraph with path ===")
    G = PrintGraph(file="/tmp/printgraph_log.txt")
    nx.add_path(G, range(10))
    nx.add_star(G, range(9, 13))
    pos = nx.spring_layout(G, seed=225)
    nx.draw(G, pos)
    plt.savefig("examples/subclass/plot_printgraph_output.png")
    plt.close()
    print("Plot saved to examples/subclass/plot_printgraph_output.png")

    session = None  # PrintGraph doesn't use sessions
    if session is not None:
        session.commit()


if __name__ == "__main__":
    demo_printgraph()
