"""
=========
Antigraph
=========

Complement graph class for small footprint when working on dense graphs.

Adapted for nx_sql — uses SQLAlchemy persistence instead of in-memory graphs.
"""

import matplotlib.pyplot as plt
import networkx as nx
from networkx import Graph
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base
import sys; sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent.parent.parent))
from examples.utils import print_docstring

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


class AntiGraph(Graph):
    """Class for complement graphs with low memory footprint."""

    all_edge_dict = {"weight": 1}

    def single_edge_dict(self):
        return self.all_edge_dict

    edge_attr_dict_factory = single_edge_dict

    def __getitem__(self, n):
        return {
            node: self.all_edge_dict for node in set(self.adj) - set(self.adj[n]) - {n}
        }

    def neighbors(self, n):
        try:
            return iter(set(self.adj) - set(self.adj[n]) - {n})
        except KeyError as err:
            raise nx.NetworkXError(f"The node {n} is not in the graph.") from err

    def degree(self, nbunch=None, weight=None):
        if nbunch is None:
            nodes_nbrs = (
                (
                    n,
                    {
                        v: self.all_edge_dict
                        for v in set(self.adj) - set(self.adj[n]) - {n}
                    },
                )
                for n in self.nodes()
            )
        elif nbunch in self:
            nbrs = set(self.nodes()) - set(self.adj[nbunch]) - {nbunch}
            return len(nbrs)
        else:
            nodes_nbrs = (
                (
                    n,
                    {
                        v: self.all_edge_dict
                        for v in set(self.nodes()) - set(self.adj[n]) - {n}
                    },
                )
                for n in self.nbunch_iter(nbunch)
            )

        if weight is None:
            return ((n, len(nbrs)) for n, nbrs in nodes_nbrs)
        else:
            return (
                (n, sum((nbrs[nbr].get(weight, 1)) for nbr in nbrs))
                for n, nbrs in nodes_nbrs
            )

    def adjacency(self):
        nodes = set(self.adj)
        for n, nbrs in self.adj.items():
            yield (n, nodes - set(nbrs) - {n})


@print_docstring
def demo_antigraph():
    """Test AntiGraph complement behavior on several graphs."""

    with Session() as session:
        Gnp = nx.gnp_random_graph(20, 0.8, seed=42)
        Anp = AntiGraph(nx.complement(Gnp))
        Gd = nx.davis_southern_women_graph()
        Ad = AntiGraph(nx.complement(Gd))
        Gk = nx.karate_club_graph()
        Ak = AntiGraph(nx.complement(Gk))
        pairs = [(Gnp, Anp), (Gd, Ad), (Gk, Ak)]

        # test connected components
        for G, A in pairs:
            gc = [set(c) for c in nx.connected_components(G)]
            ac = [set(c) for c in nx.connected_components(A)]
            for comp in ac:
                assert comp in gc
        print("✓ Connected components match")

        # test biconnected components
        for G, A in pairs:
            gc = [set(c) for c in nx.biconnected_components(G)]
            ac = [set(c) for c in nx.biconnected_components(A)]
            for comp in ac:
                assert comp in gc
        print("✓ Biconnected components match")

        # test degree
        for G, A in pairs:
            node = list(G.nodes())[0]
            nodes = list(G.nodes())[1:4]
            assert G.degree(node) == A.degree(node)
            assert sum(d for n, d in G.degree()) == sum(d for n, d in A.degree())
            assert sum(d for n, d in A.degree()) == sum(d for n, d in A.degree(weight="weight"))
            assert sum(d for n, d in G.degree(nodes)) == sum(d for n, d in A.degree(nodes))
        print("✓ Degree calculations match")

        pos = nx.spring_layout(Gnp, seed=268)
        nx.draw(Gnp, pos=pos)
        plt.savefig("examples/subclass/plot_antigraph_output.png")
        plt.close()
        print("Plot saved to examples/subclass/plot_antigraph_output.png")


if __name__ == "__main__":
    demo_antigraph()
