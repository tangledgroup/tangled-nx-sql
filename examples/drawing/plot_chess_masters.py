"""
=============
Chess Masters
=============

An example of the MultiDiGraph class.

Adapted for nx_sql — uses SQLAlchemy persistence instead of in-memory graphs.
"""

import bz2
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


def chess_pgn_graph(pgn_file="examples/drawing/chess_masters_WCC.pgn.bz2"):
    """Read chess games in pgn format in pgn_file."""
    G = nx.MultiDiGraph()
    game = {}
    with bz2.BZ2File(pgn_file) as datafile:
        lines = [line.decode().rstrip("\r\n") for line in datafile]
    for line in lines:
        if line.startswith("["):
            tag, value = line[1:-1].split(" ", 1)
            game[str(tag)] = value.strip('"')
        else:
            if game:
                white = game.pop("White")
                black = game.pop("Black")
                G.add_edge(white, black, **game)
                game = {}
    return G


@print_docstring
def demo_chess_masters():
    """Load chess games and analyze the graph structure."""

    with Session() as session:
        G = nx_sql.MultiDiGraph(session, name="chess_masters_demo")

        in_memory_G = chess_pgn_graph()
        G.add_nodes_from(in_memory_G.nodes())
        for u, v, data in in_memory_G.edges(data=True):
            G.add_edge(u, v, **data)

        print(f"Loaded {G.number_of_edges()} chess games between {G.number_of_nodes()} players\n")

        H = nx.Graph(G)
        Hcc = [H.subgraph(c) for c in nx.connected_components(H)]
        if len(Hcc) > 1:
            print(f"Note the disconnected component consisting of:\n{list(Hcc[1].nodes())}")

        # MultiDiGraph edges(data=True) returns {key: attrs_dict}
        openings = set()
        for white, black, key_data in G.edges(data=True):
            for d in key_data.values():
                eco = d.get("ECO")
                if eco:
                    openings.add(eco)
        print(f"\nFrom a total of {len(openings)} different openings,")
        print('the following games used the Sicilian opening')
        print('with the Najdorff 7...Qb6 "Poisoned Pawn" variation.\n')

        for white, black, key_data in G.edges(data=True):
            for key, game_info in key_data.items():
                if game_info.get("ECO") == "B97":
                    summary = f"{white} vs {black}\n"
                    for k, v in game_info.items():
                        summary += f"   {k}: {v}\n"
                    summary += "\n"
                    print(summary)

        edgewidth = [len(G.get_edge_data(u, v)) for u, v in H.edges()]
        wins = dict.fromkeys(H.nodes(), 0.0)
        for u, v, key_data in G.edges(data=True):
            for d in key_data.values():
                r = d.get("Result", "0-1").split("-")
                if r[0] == "1":
                    wins[u] += 1.0
                elif r[0] == "1/2":
                    wins[u] += 0.5
                    wins[v] += 0.5
                else:
                    wins[v] += 1.0
        nodesize = [wins[v] * 50 for v in H]

        pos = nx.kamada_kawai_layout(H)
        pos["Reshevsky, Samuel H"] += (0.05, -0.10)
        pos["Botvinnik, Mikhail M"] += (0.03, -0.06)
        pos["Smyslov, Vassily V"] += (0.05, -0.03)

        fig, ax = plt.subplots(figsize=(12, 12))
        nx.draw_networkx_edges(H, pos, alpha=0.3, width=edgewidth, edge_color="m")
        nx.draw_networkx_nodes(H, pos, node_size=nodesize, node_color="#210070", alpha=0.9)
        label_options = {"ec": "k", "fc": "white", "alpha": 0.7}
        nx.draw_networkx_labels(H, pos, font_size=14, bbox=label_options)

        font = {"fontname": "Helvetica", "color": "k", "fontweight": "bold", "fontsize": 14}
        ax.set_title("World Chess Championship Games: 1886 - 1985", font)
        font["color"] = "r"
        ax.text(0.80, 0.10, "edge width = # games played", horizontalalignment="center",
                transform=ax.transAxes, fontdict=font)
        ax.text(0.80, 0.06, "node size = # games won", horizontalalignment="center",
                transform=ax.transAxes, fontdict=font)
        ax.margins(0.1, 0.05)
        fig.tight_layout()
        plt.axis("off")
        plt.savefig("examples/drawing/plot_chess_masters_output.png")
        plt.close()
        print("Plot saved to examples/drawing/plot_chess_masters_output.png")

        session.commit()


if __name__ == "__main__":
    demo_chess_masters()
