import networkx as nx
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from nx_sql.models import Base

import nx_sql

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)

with SessionLocal() as session:
    G = nx_sql.Graph(session)

    G.add_node(np.array([1.0, 2.0, 3.0]), color="red")      # ← works!
    G.add_node([4.0, 5.0])                                    # ← works!
    G.add_edge([1.0, 2.0, 3.0], [4.0, 5.0], weight=42)

    print(list(G.nodes(data=True)))   # → tuples, not lists/arrays
    # Use the normalized (tuple) form for lookups — add_node normalizes keys
    path = nx.shortest_path(G, (1.0, 2.0, 3.0), (4.0, 5.0))
    print(path)
    session.commit()
