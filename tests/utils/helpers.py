"""Test helper functions ported from NetworkX."""

from __future__ import annotations


def graphs_equal_g(nG1, nG2):
    """Compare two NetworkX-compatible graphs (both must have .nodes and .edges)."""
    if not nodes_equal(nG1.nodes(data=True), nG2.nodes(data=True)):
        return False
    edges1 = sorted((u, v, d) for u, v, d in nG1.edges(data=True))
    edges2 = sorted((u, v, d) for u, v, d in nG2.edges(data=True))
    return edges1 == edges2


def nodes_equal(nodes1, nodes2):
    """Compare two node data iterables."""
    return sorted(nodes1, key=lambda x: str(x[0])) == sorted(nodes2, key=lambda x: str(x[0]))


def edges_equal(edges1, edges2):
    """Compare two edge lists (order-independent)."""
    return sorted(edges1) == sorted(edges2)
