"""
==========
JavaScript
==========

Example of writing JSON format graph data for use with D3.js or other
JavaScript visualization libraries.

Adapted for nx_sql — writes node-link JSON to a file instead of serving
via HTTP. Use the output with any JS graph viz library (D3, vis.js, etc.).
"""

import json
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
def demo_javascript_force():
    """Export graph as node-link JSON for JavaScript visualization."""

    with Session() as session:
        G = nx_sql.Graph(session, name="javascript_force_demo")

        # Create a barbell graph (good for force-directed layouts)
        G_nx = nx.barbell_graph(6, 3)
        G.add_nodes_from(G_nx.nodes())
        G.add_edges_from(G_nx.edges())

        # Add name attribute for hover tooltips
        for n in G:
            G.add_node(n, name=str(n))

        # Convert to node-link format (D3 compatible)
        d = nx.json_graph.node_link_data(G, edges="links")

        # Write to file
        output_file = "examples/external/force.json"
        with open(output_file, "w") as f:
            json.dump(d, f, indent=2)

        print(f"Wrote node-link JSON data to {output_file}")
        print(f"  Nodes: {len(d['nodes'])}")
        print(f"  Links: {len(d.get('links', d.get('edges', [])))}")
        print(f"\nTo visualize with D3.js, load force.json and use:")
        print('  d3.json("force.json").then(data => { ... })')

        session.commit()


if __name__ == "__main__":
    demo_javascript_force()
