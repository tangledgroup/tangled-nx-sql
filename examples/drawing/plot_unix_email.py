"""
==========
Unix Email
==========

Create a directed graph from a unix mailbox.

Adapted for nx_sql — uses SQLAlchemy persistence instead of in-memory graphs.
"""

from email.utils import getaddresses, parseaddr
import mailbox

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


def mbox_graph():
    """Parse unix mailbox and return edges as list of (from, to, subject)."""
    mbox = mailbox.mbox("examples/drawing/unix_email.mbox")
    edges = []
    for msg in mbox:
        (source_name, source_addr) = parseaddr(msg["From"])
        tos = msg.get_all("to", [])
        ccs = msg.get_all("cc", [])
        resent_tos = msg.get_all("resent-to", [])
        resent_ccs = msg.get_all("resent-cc", [])
        all_recipients = getaddresses(tos + ccs + resent_tos + resent_ccs)
        for target_name, target_addr in all_recipients:
            subject = msg.get("Subject", "No Subject")
            edges.append((source_addr, target_addr, {"subject": subject}))
    return edges


@print_docstring
def demo_unix_email():
    """Build email graph and visualize sender-recipient relationships."""

    with Session() as session:
        G = nx_sql.MultiDiGraph(session, name="unix_email_demo")
        edges = mbox_graph()
        G.add_edges_from(edges)

        print(f"Email graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        for u, v, d in list(G.edges(data=True))[:5]:
            # MultiDiGraph returns {key: attrs}
            if isinstance(d, dict) and 0 in d:
                print(f"  From: {u} To: {v} Subject: {d[0].get('subject', 'N/A')}")
            else:
                print(f"  From: {u} To: {v} Subject: {d.get('subject', 'N/A')}")

        pos = nx.spring_layout(G, iterations=10, seed=227)
        nx.draw(G, pos, node_size=0, alpha=0.4, edge_color="r", font_size=12, with_labels=True)
        ax = plt.gca()
        ax.margins(0.08)
        plt.savefig("examples/drawing/plot_unix_email_output.png")
        plt.close()
        print("Plot saved to examples/drawing/plot_unix_email_output.png")

        session.commit()


if __name__ == "__main__":
    demo_unix_email()
