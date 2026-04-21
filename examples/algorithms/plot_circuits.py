"""Demonstrate Boolean circuit to formula conversion with nx_sql.

Mirrors networkx/examples/algorithms/plot_circuits.py but uses
SQLAlchemy persistence. Tests converting a Boolean circuit DAG to an
equivalent formula tree via dag_to_branching.
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


def circuit_to_formula(circuit):
    """Convert a Boolean circuit DAG to an equivalent formula tree."""
    formula = nx.dag_to_branching(circuit)
    for v in formula:
        source = formula.nodes[v]["source"]
        formula.nodes[v]["label"] = circuit.nodes[source]["label"]
    return formula


def formula_to_string(formula):
    """Convert a formula tree to a readable string."""
    def _to_string(formula, root):
        label = formula.nodes[root]["label"]
        if not formula[root]:
            return label
        children = list(formula[root])
        if len(children) == 1:
            child = children[0]
            return f"{label}({_to_string(formula, child)})"
        left, right = children[0], children[1]
        left_sub = _to_string(formula, left)
        right_sub = _to_string(formula, right)
        return f"({left_sub} {label} {right_sub})"

    root = next(v for v, d in formula.in_degree() if d == 0)
    return _to_string(formula, root)


@print_docstring
def demo_circuits():
    """Convert a Boolean circuit to an equivalent Boolean formula."""

    with Session() as session:
        # Build a Boolean circuit as a DAG
        # Layer 0: output AND gate
        # Layer 1: two OR gates
        # Layer 2: variable x, variable y, NOT z
        # Layer 3: variable z
        circuit_nx = nx.DiGraph()
        circuit_nx.add_node(0, label="∧", layer=0)
        circuit_nx.add_node(1, label="∨", layer=1)
        circuit_nx.add_node(2, label="∨", layer=1)
        circuit_nx.add_edge(0, 1)
        circuit_nx.add_edge(0, 2)
        circuit_nx.add_node(3, label="x", layer=2)
        circuit_nx.add_node(4, label="y", layer=2)
        circuit_nx.add_node(5, label="¬", layer=2)
        circuit_nx.add_edge(1, 3)
        circuit_nx.add_edge(1, 4)
        circuit_nx.add_edge(2, 4)
        circuit_nx.add_edge(2, 5)
        circuit_nx.add_node(6, label="z", layer=3)
        circuit_nx.add_edge(5, 6)

        G = nx_sql.DiGraph(session, name="circuit_demo")
        for node in circuit_nx.nodes():
            G.add_node(node, label=circuit_nx.nodes[node]["label"])
        G.add_edges_from(circuit_nx.edges())

        print("=== Boolean Circuit ===")
        print(f"Circuit: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        print("\nLayer structure:")
        for layer in range(4):
            layer_nodes = [n for n, d in G.nodes(data=True) if d.get("layer") == layer]
            labels = [d["label"] for n, d in G.nodes(data=True) if d.get("layer") == layer]
            print(f"  Layer {layer}: {labels}")

        # Convert circuit to formula
        formula = circuit_to_formula(G)
        formula_str = formula_to_string(formula)
        print(f"\n=== Converted Formula ===")
        print(f"Formula tree: {formula.number_of_nodes()} nodes, {formula.number_of_edges()} edges")
        print(f"String representation: {formula_str}")

        # Verify structure
        print("\n=== Formula Tree Structure ===")
        for node in nx.topological_sort(formula):
            children = list(formula.successors(node))
            label = formula.nodes[node]["label"]
            if not children:
                print(f"  {label} (leaf)")
            elif len(children) == 1:
                child_label = formula.nodes[children[0]]["label"]
                print(f"  {label}({child_label})")
            else:
                left_label = formula.nodes[children[0]]["label"]
                right_label = formula.nodes[children[1]]["label"]
                print(f"  ({left_label} {label} {right_label})")

        # Try a larger circuit
        print("\n=== Larger Circuit ===")
        # (A AND B) OR (C AND D)
        large_circuit = nx.DiGraph()
        large_circuit.add_node(0, label="∨", layer=0)
        large_circuit.add_node(1, label="∧", layer=1)
        large_circuit.add_node(2, label="∧", layer=1)
        large_circuit.add_edge(0, 1)
        large_circuit.add_edge(0, 2)
        for i, var in enumerate(["A", "B", "C", "D"]):
            large_circuit.add_node(i + 3, label=var, layer=2)
        large_circuit.add_edge(1, 3)
        large_circuit.add_edge(1, 4)
        large_circuit.add_edge(2, 5)
        large_circuit.add_edge(2, 6)

        G2 = nx_sql.DiGraph(session, name="circuit_demo2")
        for node in large_circuit.nodes():
            G2.add_node(node, label=large_circuit.nodes[node]["label"])
        G2.add_edges_from(large_circuit.edges())

        formula2 = circuit_to_formula(G2)
        formula_str2 = formula_to_string(formula2)
        print(f"Formula: {formula_str2}")

        session.commit()


if __name__ == "__main__":
    demo_circuits()
