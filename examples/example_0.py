import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

import sys; sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent.parent))
from examples.utils import print_docstring


engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


@print_docstring
def demo0():
    """Demo 0"""

    with Session() as session:
        G = nx_sql.DiGraph(session, name="demo0")
        G.add_edge('A1', 'B1', weight=0.1, marriage="stable")
        G.add_edge('B1', 'C1', weight=0.1, marriage="stable")
        G.add_edge('C1', 'D1', weight=0.1, marriage="stable")
        G.add_edge('A1', 'D1', weight=0.3, marriage="unstable")

        path = nx.shortest_path(G, 'A1', 'D1', weight='weight')
        print(path)

        paths = list(nx.all_shortest_paths(G, 'A1', 'D1', weight='weight'))
        print(paths)

        session.commit()
        session.close()


@print_docstring
def demo1():
    """Demo 1"""

    with Session() as session:
        G = nx_sql.DiGraph(session, name="demo1")
        G.add_edge('A2', 'B2', weight=0.1, marriage="unstable")
        G.add_edge('B2', 'C2', weight=0.1, marriage="unstable")
        G.add_edge('C2', 'D2', weight=0.1, marriage="unstable")
        G.add_edge('A2', 'D2', weight=0.4, marriage="stable")

        path = nx.shortest_path(G, 'A2', 'D2', weight='weight')
        print(path)

        paths = list(nx.all_shortest_paths(G, 'A2', 'D2', weight='weight'))
        print(paths)

        session.commit()
        session.close()


if __name__ == '__main__':
    demo0()
    demo1()
