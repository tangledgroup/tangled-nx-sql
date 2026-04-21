"""Demonstrate iterated dynamical systems with nx_sql.

Mirrors networkx/examples/algorithms/plot_iterated_dynamical_systems.py but uses
SQLAlchemy persistence. Tests sums-of-cubes on 3N and digit-squared cycles.
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


def digitsum_p(n, p=3, b=10):
    """Return sum of digits of n (in base b) raised to power p."""
    if n <= 0:
        return 0
    total = 0
    while n > 0:
        total += (n % b) ** p
        n //= b
    return total


def collatz(n):
    """Next value in Collatz 3n+1 sequence."""
    if n % 2 == 0:
        return n // 2
    return 3 * n + 1


@print_docstring
def demo_iterated_dynamical_systems():
    """Explore integer-valued iterated dynamical systems."""

    with Session() as session:
        # --- Sums of cubes on 3N ---
        print("=== Sums of Cubes on 3N ===")
        print("f(n) = sum of digits cubed, applied iteratively")
        print("All multiples of 3 eventually reach 153 (global attractor)")

        G_nx = nx.DiGraph()
        max_n = 1000
        visited_counts = {}

        for start in range(3, max_n + 1, 3):
            n = start
            path = [n]
            seen = {n}
            while True:
                nxt = digitsum_p(n, p=3, b=10)
                if nxt == 153:
                    path.append(153)
                    break
                if nxt in seen:
                    # Found a cycle not including 153
                    path.append(nxt)
                    break
                seen.add(nxt)
                path.append(nxt)
                n = nxt

            for i in range(len(path) - 1):
                G_nx.add_edge(path[i], path[i + 1])

            visited_counts[start] = len(path) - 1

        G = nx_sql.DiGraph(session, name="iterated_dynamical_demo")
        for node in G_nx.nodes():
            G.add_node(node)
        G.add_edges_from(G_nx.edges())

        print(f"\nGraph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        print(f"Max iterations to reach 153: {max(visited_counts.values())}")
        print(f"Nodes requiring max iterations:")
        for start, steps in sorted(visited_counts.items(), key=lambda x: -x[1]):
            if steps == max(visited_counts.values()):
                print(f"  {start}: {steps} iterations")

        # Show a few example paths
        print("\n=== Example Paths ===")
        for start in [108, 177, 3, 6]:
            n = start
            path = [n]
            seen = {n}
            while len(path) < 20:
                nxt = digitsum_p(n, p=3, b=10)
                if nxt in seen or nxt == 153:
                    path.append(nxt)
                    break
                seen.add(nxt)
                path.append(nxt)
                n = nxt
            print(f"  {start} -> {' -> '.join(str(x) for x in path)}")

        # --- Squaring digits (happy numbers) ---
        print("\n=== Squaring Digits ===")
        print("f(n) = sum of digits squared; finds cycles and fixed points")

        G_nx2 = nx.DiGraph()
        max_n2 = 100

        for start in range(1, max_n2 + 1):
            n = start
            path = [n]
            seen = {n}
            while True:
                nxt = digitsum_p(n, p=2, b=10)
                if nxt == 1:
                    path.append(1)
                    break
                if nxt in seen:
                    path.append(nxt)
                    break
                seen.add(nxt)
                path.append(nxt)
                n = nxt

            for i in range(len(path) - 1):
                G_nx2.add_edge(path[i], path[i + 1])

        G2 = nx_sql.DiGraph(session, name="iterated_dynamical_demo2")
        for node in G_nx2.nodes():
            G2.add_node(node)
        G2.add_edges_from(G_nx2.edges())

        print(f"\nGraph: {G2.number_of_nodes()} nodes, {G2.number_of_edges()} edges")

        # Find which numbers are "happy" (reach 1)
        happy_numbers = []
        for start in range(1, 51):
            n = start
            seen = set()
            is_happy = False
            while len(seen) < 20:
                if n == 1:
                    is_happy = True
                    break
                if n in seen:
                    break
                seen.add(n)
                n = digitsum_p(n, p=2, b=10)
            if is_happy:
                happy_numbers.append(start)

        print(f"Happy numbers (1-50): {happy_numbers}")

        # --- Collatz conjecture ---
        print("\n=== Collatz 3n+1 Conjecture ===")
        G_nx3 = nx.DiGraph()
        max_collatz = 100

        for start in range(1, max_collatz + 1):
            n = start
            path = [n]
            seen = {n}
            while n != 1 and len(path) < 100:
                n = collatz(n)
                if n in seen:
                    path.append(n)
                    break
                seen.add(n)
                path.append(n)

            for i in range(len(path) - 1):
                G_nx3.add_edge(path[i], path[i + 1])

        G3 = nx_sql.DiGraph(session, name="iterated_dynamical_demo3")
        for node in G_nx3.nodes():
            G3.add_node(node)
        G3.add_edges_from(G_nx3.edges())

        print(f"Collatz graph (1-{max_collatz}): {G3.number_of_nodes()} nodes, {G3.number_of_edges()} edges")

        # Longest chain
        max_chain = 0
        max_start = 0
        for start in range(1, max_collatz + 1):
            n = start
            length = 0
            seen = set()
            while n != 1 and n not in seen and length < 100:
                seen.add(n)
                n = collatz(n)
                length += 1
            if length > max_chain:
                max_chain = length
                max_start = start

        print(f"Longest chain from 1-{max_collatz}: {max_start} with {max_chain} steps")

        session.commit()


if __name__ == "__main__":
    demo_iterated_dynamical_systems()
