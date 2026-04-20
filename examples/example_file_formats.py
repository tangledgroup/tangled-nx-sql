"""example_file_formats.py - Graph import/export in various formats.

Covers: GraphML, GEXF, GML, JSON (node-link/tree/adjacency/cytoscape),
        edge lists, adjacency lists, Graph6/Sparse6, DOT/Graphviz export.
"""

import json
from pathlib import Path

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)

EXAMPLES_DIR = Path(__file__).resolve().parent


def demo_graphml():
    """Export to/from GraphML (XML-based, preserves attributes)."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="graphml_demo")
        G.add_node("A", label="Node A", color="red")
        G.add_node("B", label="Node B", color="blue")
        G.add_edge("A", "B", weight=1.5, relation="friend")

        # Export to GraphML
        path = EXAMPLES_DIR / "output_graphml.graphml"
        nx.write_graphml(G, str(path))
        print(f"Exported GraphML: {path}")

        # Re-import into a plain NetworkX graph
        G_reimported = nx.read_graphml(str(path))
        print(f"Reimported nodes: {list(G_reimported.nodes(data=True))}")
        print(f"Reimported edges: {list(G_reimported.edges(data=True))}")

        session.commit()


def demo_gexf():
    """Export to GEXF (Gephi format)."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="gexf_demo")
        G.add_node("A", label="Node A")
        G.add_node("B", label="Node B")
        G.add_edge("A", "B", weight=1.0)

        path = EXAMPLES_DIR / "output_gexf.gexf"
        nx.write_gexf(G, str(path))
        print(f"\nExported GEXF: {path}")

        G_reimported = nx.read_gexf(str(path))
        print(f"Reimported nodes: {list(G_reimported.nodes(data=True))}")

        session.commit()


def demo_gml():
    """Export to GML (Graph Description Language)."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="gml_demo")
        G.add_node("A", label="Node A")
        G.add_edge("A", "B", weight=2.0)

        path = EXAMPLES_DIR / "output_gml.gml"
        nx.write_gml(G, str(path))
        print(f"\nExported GML: {path}")

        G_reimported = nx.read_gml(str(path))
        print(f"Reimported edges: {list(G_reimported.edges(data=True))}")

        session.commit()


def demo_json_formats():
    """Export to various JSON formats."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="json_demo")
        G.add_node("A", label="Node A")
        G.add_node("B", label="Node B")
        G.add_edge("A", "B", weight=1.0)

        # Node-link format (default)
        path = EXAMPLES_DIR / "output_json_nodelink.json"
        data = nx.node_link_data(G)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"\nExported JSON (node-link): {path}")

        G_reimported = nx.node_link_graph(json.load(open(path)))
        print(f"Reimported nodes: {list(G_reimported.nodes(data=True))}")

        # Adjacency format
        path = EXAMPLES_DIR / "output_json_adjacency.json"
        data = nx.adjacency_data(G)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Exported JSON (adjacency): {path}")

        # Tree format (requires directed tree)
        path = EXAMPLES_DIR / "output_json_tree.json"
        DT = nx.balanced_tree(2, 2, create_using=nx.DiGraph)
        data = nx.tree_data(DT, root=0)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Exported JSON (tree): {path}")

        # Cytoscape format
        path = EXAMPLES_DIR / "output_json_cytoscape.json"
        data = nx.cytoscape_data(G)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Exported JSON (cytoscape): {path}")

        session.commit()


def demo_edge_list():
    """Export to/from edge list format."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="edgelist_demo")
        G.add_edges_from([(1, 2), (2, 3), (3, 4)])

        path = EXAMPLES_DIR / "output_edgelist.edgelist"
        nx.write_edgelist(G, str(path), delimiter=",")
        print(f"\nExported edge list: {path}")

        G_reimported = nx.read_edgelist(str(path), delimiter=",")
        print(f"Reimported edges: {list(G_reimported.edges())}")

        session.commit()


def demo_adjacency_list():
    """Export to adjacency list format."""
    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="adjlist_demo")
        G.add_edges_from([(1, 2), (1, 3), (2, 4)])

        path = EXAMPLES_DIR / "output_adjlist.adjlist"
        nx.write_adjlist(G, str(path))
        print(f"\nExported adjacency list: {path}")

        G_reimported = nx.read_adjlist(str(path))
        print(f"Reimported edges: {list(G_reimported.edges())}")

        session.commit()


def demo_graph6():
    """Export to Graph6/Sparse6 format."""
    with SessionLocal() as session:
        G_nxsql = nx_sql.Graph(session, name="graph6_demo")
        G_nxsql.add_edges_from([(0, 1), (1, 2), (2, 3)])

        # Convert to plain NetworkX for format export
        G = nx.Graph(G_nxsql)

        # Graph6
        path = EXAMPLES_DIR / "output_graph6.graph6"
        nx.write_graph6(G, str(path))
        print(f"\nExported Graph6: {path}")
        print(f"Content: {open(path).read().strip()}")

        session.commit()


def demo_dot():
    """Export to DOT/Graphviz format."""
    with SessionLocal() as session:
        G_nxsql = nx_sql.DiGraph(session, name="dot_demo")
        G_nxsql.add_edge("A", "B", label="edge1")
        G_nxsql.add_edge("B", "C", label="edge2")

        # Convert to plain NetworkX for DOT export
        G = nx.DiGraph(G_nxsql)

        try:
            path = EXAMPLES_DIR / "output_dot.dot"
            dot_str = nx.nx_pydot.to_pydot(G).to_string()
            with open(path, "w") as f:
                f.write(dot_str)
            print(f"\nExported DOT: {path}")
            print(f"Content: {dot_str[:200]}...")
        except ImportError:
            # Fallback: use to_agraph if pydot not available
            try:
                import pygraphviz as pgv
                path = EXAMPLES_DIR / "output_dot.dot"
                A = nx.nx_agraph.to_agraph(G)
                A.write(str(path))
                print(f"\nExported DOT (via pygraphviz): {path}")
            except ImportError:
                # Manual DOT
                path = EXAMPLES_DIR / "output_dot.dot"
                dot_lines = ['digraph G {']
                for u, v, d in G.edges(data=True):
                    attrs = ", ".join(f'{k}="{v}"' for k, v in d.items())
                    attr_str = f" [{attrs}]" if attrs else ""
                    dot_lines.append(f'  "{u}" -> "{v}"{attr_str};')
                dot_lines.append('}')
                dot_str = "\n".join(dot_lines)
                with open(path, "w") as f:
                    f.write(dot_str)
                print(f"\nExported DOT (manual): {path}")
                print(f"Content: {dot_str}")

        session.commit()


if __name__ == "__main__":
    demo_graphml()
    demo_gexf()
    demo_gml()
    demo_json_formats()
    demo_edge_list()
    demo_adjacency_list()
    demo_graph6()
    demo_dot()
