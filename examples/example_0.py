import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from nx_sql.models import Base

import nx_sql

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)


def demo0():
    print('demo0')
    with SessionLocal() as session:
        G = nx_sql.DiGraph(session)
        G.add_edge('A', 'B', weight=0.1)
        G.add_edge('B', 'C', weight=0.1)
        G.add_edge('C', 'D', weight=0.1)
        G.add_edge('A', 'D', weight=0.3)

        path = nx.shortest_path(G, 'A', 'D', weight='weight')
        print(path)

        paths = list(nx.all_shortest_paths(G, 'A', 'D', weight='weight'))
        print(paths)


def demo1():
    print('demo1')
    with SessionLocal() as session:
        G = nx_sql.DiGraph(session)
        G.add_edge('A', 'B', weight=0.1)
        G.add_edge('B', 'C', weight=0.1)
        G.add_edge('C', 'D', weight=0.1)
        G.add_edge('A', 'D', weight=0.4)

        path = nx.shortest_path(G, 'A', 'D', weight='weight')
        print(path)

        paths = list(nx.all_shortest_paths(G, 'A', 'D', weight='weight'))
        print(paths)


if __name__ == '__main__':
    demo0()
    demo1()
