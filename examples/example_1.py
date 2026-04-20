import numpy as np
import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

import sys; sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent.parent))
from examples.utils import print_docstring


engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)


@print_docstring
def demo0():
    """Demo 0"""

    with SessionLocal() as session:
        G = nx_sql.Graph(session, name="ndarray_demo")

        G.add_node(np.array([1.0, 2.0, 3.0]), color="red")
        G.add_node((4.0, 5.0))
        G.add_edge([1.0, 2.0, 3.0], [4.0, 5.0], weight=42)
        session.flush()

        print(list(G.nodes(data=True)))

        # Use the normalized (tuple) form for lookups — add_node normalizes keys
        path = nx.shortest_path(G, (1.0, 2.0, 3.0), (4.0, 5.0))
        print(path)

        session.commit()
        session.close()


if __name__ == '__main__':
    demo0()
