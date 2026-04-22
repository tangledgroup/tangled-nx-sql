"""Demonstrate Morse code prefix tree (trie) with nx_sql.

Mirrors networkx/examples/graph/plot_morse_trie.py but uses
SQLAlchemy persistence. Tests building a trie from Morse code mappings
and traversing it for encoding/decoding.
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
def demo_morse_trie():
    """Build a Morse code prefix tree and demonstrate encoding/decoding."""

    with Session() as session:
        # Morse code mapping
        morse_mapping = {
            "a": ".-", "b": "-...", "c": "-.-.", "d": "-..",
            "e": ".", "f": "..-.", "g": "--.", "h": "....",
            "i": "..", "j": ".---", "k": "-.-", "l": ".-..",
            "m": "--", "n": "-.", "o": "---", "p": ".--.",
            "q": "--.-", "r": ".-.", "s": "...", "t": "-",
            "u": "..-", "v": "...-", "w": ".--", "x": "-..-",
            "y": "-.--", "z": "--..",
        }

        # Build the trie
        G_nx = nx.DiGraph()
        root = ""
        G_nx.add_node(root, layer=0)

        # Sort by code length then character for consistent ordering
        sorted_mapping = dict(
            sorted(morse_mapping.items(), key=lambda item: (len(item[1]), item[1]))
        )

        for letter, code in sorted_mapping.items():
            parent = root
            for i, symbol in enumerate(code):
                child = code[:i + 1]
                if not G_nx.has_node(child):
                    G_nx.add_node(child, layer=i + 1)
                    G_nx.add_edge(parent, child, char=symbol)
                parent = child
            # Mark leaf nodes with the letter
            G_nx.nodes[child]["letter"] = letter

        G = nx_sql.DiGraph(session, name="morse_trie_demo")
        for node in G_nx.nodes():
            attrs = dict(G_nx.nodes[node])
            G.add_node(node, **attrs)
        for u, v, d in G_nx.edges(data=True):
            G.add_edge(u, v, **d)

        print("=== Morse Code Trie ===")
        print(f"Nodes: {G.number_of_nodes()}")
        print(f"Edges: {G.number_of_edges()}")
        print(f"Max depth: {max(d.get('layer', 0) for _, d in G.nodes(data=True))}")

        # Show trie structure by layer
        print("\nTrie structure:")
        for layer in sorted(set(d.get("layer", 0) for _, d in G.nodes(data=True))):
            layer_nodes = [(n, d) for n, d in G.nodes(data=True) if d.get("layer") == layer]
            parts = []
            for node, attrs in sorted(layer_nodes):
                letter = attrs.get("letter", "")
                if letter:
                    parts.append(f"{node}='{letter}'")
                else:
                    parts.append(node)
            print(f"  Layer {layer}: {', '.join(parts)}")

        # Encode text to Morse
        print("\n=== Encoding ===")
        def encode(text):
            """Encode text using the Morse trie."""
            results = []
            for char in text.lower():
                if char == " ":
                    results.append("/")
                    continue
                code = morse_mapping.get(char)
                if code is None:
                    continue
                # Traverse the trie to verify
                node = ""
                valid = True
                for symbol in code:
                    next_node = node + symbol
                    if not G.has_node(next_node):
                        valid = False
                        break
                    node = next_node
                if valid:
                    results.append(code)
            return " ".join(results)

        test_words = ["hello", "world", "help", "morse"]
        for word in test_words:
            encoded = encode(word)
            print(f"  {word} -> {encoded}")

        # Decode Morse to text
        print("\n=== Decoding ===")
        def decode(morse_str):
            """Decode Morse code using the trie."""
            result = []
            for code in morse_str.split():
                if code == "/":
                    result.append(" ")
                    continue
                node = ""
                decoded_char = None
                for symbol in code:
                    node += symbol
                    if "letter" in G.nodes.get(node, {}):
                        decoded_char = G.nodes[node]["letter"]
                if decoded_char:
                    result.append(decoded_char)
            return "".join(result)

        test_codes = [".-.. .- -.-.", "-... --- --. ..- .-. -.- -.-",
                      ".-- --- .-. -..", "... .... . .--."]
        for code in test_codes:
            decoded = decode(code)
            print(f"  {code} -> {decoded}")

        session.commit()

    # Verify persistence
    with Session() as session:
        gmodel = session.execute(
            nx_sql.select(GraphModel).where(GraphModel.name == "morse_trie_demo")
        ).scalar_one()
        G2 = nx_sql.DiGraph(session, graph_id=gmodel.graph_id)
        print(f"\nReloaded from DB: {G2.number_of_nodes()} nodes, {G2.number_of_edges()} edges")
        session.commit()


if __name__ == "__main__":
    demo_morse_trie()
