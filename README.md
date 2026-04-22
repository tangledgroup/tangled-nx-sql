# tangled-nx-sql

Seamlessly adds SQL database as a persistence layer to NetworkX graphs — zero in-memory footprint, full NetworkX API compatibility.

[![PyPI](https://img.shields.io/pypi/v/tangled-nx-sql)](https://pypi.org/project/tangled-nx-sql/)
[![PyPI Downloads](https://img.shields.io/pypi/dm/tangled-nx-sql)](https://pypistats.org/packages/tangled-nx-sql)
[![Supported Versions](https://img.shields.io/pypi/pyversions/tangled-nx-sql)](https://pypi.org/project/tangled-nx-sql)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT)

## What is it?

`nx_sql` wraps NetworkX graphs in SQLAlchemy, storing every node and edge directly in a relational database. You get the full NetworkX API — shortest paths, centrality, clustering, traversal — backed by persistent SQL storage with no manual serialization.

| Feature | Detail |
|---|---|
| **Graph types** | `Graph`, `DiGraph`, `MultiGraph`, `MultiDiGraph` |
| **Backend** | Any SQLAlchemy-compatible database (SQLite, PostgreSQL, MySQL, etc.) |
| **Node keys** | Strings, numbers, tuples, NumPy arrays, dicts, sets — auto-normalized to JSON |
| **API surface** | 100% NetworkX compatible — drop-in replacement for in-memory graphs |
| **Multi-graph isolation** | Named graphs share a session but store data independently |

## Installation

```bash
pip install tangled-nx-sql
```

Requires `networkx` and `sqlalchemy` as dependencies.

## Quick Start

### Basic usage — shortest path on a directed graph

```python
import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///my_graph.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

with Session() as session:
    G = nx_sql.DiGraph(session, name="my_graph")

    G.add_edge('A', 'B', weight=0.1)
    G.add_edge('B', 'C', weight=0.1)
    G.add_edge('C', 'D', weight=0.1)
    G.add_edge('A', 'D', weight=0.3)

    # Full NetworkX API — works against the database-backed graph
    path = nx.shortest_path(G, 'A', 'D', weight='weight')
    print(path)  # ['A', 'D']

    paths = list(nx.all_shortest_paths(G, 'A', 'D', weight='weight'))
    print(paths)  # [['A', 'D']]

    session.commit()
```

### Arbitrary node types — NumPy arrays, tuples, lists

```python
import numpy as np
import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///my_graph.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

with Session() as session:
    G = nx_sql.Graph(session, name="ndarray_demo")

    # Any hashable type works as a node key
    G.add_node(np.array([1.0, 2.0, 3.0]), color="red")
    G.add_node((4.0, 5.0))
    G.add_edge([1.0, 2.0, 3.0], [4.0, 5.0], weight=42)

    print(list(G.nodes(data=True)))
    # [((1.0, 2.0, 3.0), {'color': 'red'}), ((4.0, 5.0), {})]

    path = nx.shortest_path(G, (1.0, 2.0, 3.0), (4.0, 5.0))
    print(path)  # [(1.0, 2.0, 3.0), (4.0, 5.0)]

    session.commit()
```

### Multiple named graphs in one session

```python
with Session() as session:
    G1 = nx_sql.DiGraph(session, name="graph_a")
    G2 = nx_sql.DiGraph(session, name="graph_b")

    G1.add_edge('X', 'Y')
    G2.add_edge('A', 'B')

    # Graphs are isolated — G1 only sees its own nodes/edges
    print(list(G1.nodes()))  # ['X', 'Y']
    print(list(G2.nodes()))  # ['A', 'B']

    session.commit()
```

### Generate, analyze, and draw a random graph

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///my_graph.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

with Session() as session:
    # Generate a random graph and persist it to SQL
    G_nx = nx.erdos_renyi_graph(20, 0.15, seed=42)
    G = nx_sql.Graph(session, name="random_graph")
    G.add_nodes_from(G_nx.nodes())
    G.add_edges_from(G_nx.edges())

    # Compute statistics against the database-backed graph
    print(f"Nodes: {G.number_of_nodes()}")
    print(f"Edges: {G.number_of_edges()}")
    print(f"Avg degree: {sum(dict(G.degree()).values()) / G.number_of_nodes():.2f}")

    # Draw with color-coded node degrees
    pos = nx.spring_layout(G, seed=42, k=0.5)
    degrees = [d for _, d in G.degree()]
    cmap = plt.cm.viridis
    node_colors = [d / max(degrees) for d in degrees]

    fig, ax = plt.subplots(figsize=(10, 8))
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, cmap=cmap,
                           node_size=200, alpha=0.9, ax=ax)
    nx.draw_networkx_edges(G, pos, width=1.0, alpha=0.5, ax=ax)
    nx.draw_networkx_labels(G, pos, font_size=8, ax=ax)
    ax.set_title("Erdős-Rényi Random Graph", fontsize=14)
    ax.axis("off")
    plt.savefig("random_graph.png", dpi=150, bbox_inches="tight")
    plt.close()

    session.commit()
```

### Social network with community detection

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///my_graph.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

with Session() as session:
    # Load a real-world social network
    G_nx = nx.davis_southern_women_graph()
    G = nx_sql.Graph(session, name="social_network")
    G.add_nodes_from(G_nx.nodes())
    G.add_edges_from(G_nx.edges())

    # Detect communities
    communities = nx.community.greedy_modularity_communities(G)
    print(f"Communities: {len(communities)}")

    # Color nodes by community
    palette = ["#e41a1c", "#377eb8", "#4daf4a"]
    color_map = {}
    for i, comm in enumerate(communities):
        for node in comm:
            color_map[node] = palette[i % len(palette)]

    pos = nx.spring_layout(G, seed=1430)
    fig, ax = plt.subplots(figsize=(12, 10))
    nx.draw_networkx_nodes(G, pos,
                           node_color=[color_map[n] for n in G.nodes()],
                           node_size=300, alpha=0.85, ax=ax)
    nx.draw_networkx_edges(G, pos, width=1.5, alpha=0.6, ax=ax)
    nx.draw_networkx_labels(G, pos, font_size=9, ax=ax)
    ax.set_title("Davis Southern Women Network", fontsize=14)
    ax.axis("off")
    plt.savefig("social_network.png", dpi=150, bbox_inches="tight")
    plt.close()

    session.commit()
```

## API Reference

### Graph classes

| Class | Description |
|---|---|
| `nx_sql.Graph` | Undirected graph |
| `nx_sql.DiGraph` | Directed graph |
| `nx_sql.MultiGraph` | Undirected multi-edge graph |
| `nx_sql.MultiDiGraph` | Directed multi-edge graph |

### Constructor

```python
G = nx_sql.DiGraph(session, name="my_graph")
```

- **`session`** — SQLAlchemy `Session` instance
- **`name`** — Optional unique identifier; graphs with the same name are shared across sessions (enables persistence)
- **`graph_id`** — Auto-generated UUID if no name is provided

### Querying persisted graphs

Use SQLAlchemy's `select` to find a graph by name and reload it in a new session:

```python
from nx_sql.models import Graph as GraphModel

with Session() as session:
    gmodel = nx_sql.select(GraphModel).where(
        GraphModel.name == "my_graph"
    ).scalar_one()

    G = nx_sql.DiGraph(session, graph_id=gmodel.graph_id)
    print(list(G.nodes()))  # recovers previously stored nodes
```

### Re-exported utilities

```python
import nx_sql

# NetworkX relabel functions work on any nx_sql graph
nx_sql.relabel_nodes(G, mapping)
nx_sql.convert_node_labels_to_integers(G)
```

## Architecture

```
┌─────────────────────────────────────────────┐
│           Your Python code                  │
│  networkx.shortest_path(G, source, target)  │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│         nx_sql Graph wrapper                │
│  intercepts .nodes(), .edges(), etc.        │
└──────────────────┬──────────────────────────┘
                   │ SQLAlchemy ORM
┌──────────────────▼──────────────────────────┐
│  Database tables: graphs │ nodes │ edges    │
│  JSON attributes · UUID keys · indexes      │
└─────────────────────────────────────────────┘
```

Every node and edge is stored in SQL. The graph holds no in-memory adjacency — operations are executed as queries against the database.

## Database Schema

Three tables with JSON attribute columns:

| Table | Columns |
|---|---|
| `graphs` | `graph_id` (UUID), `name`, `graph_type`, `attributes` (JSON) |
| `nodes` | `node_id` (UUID), `graph_id`, `node_key` (JSON text), `attributes` (JSON) |
| `edges` | `edge_id` (UUID), `graph_id`, `source_id`, `target_id`, `key`, `attributes` (JSON) |

## Running the examples

```bash
uv run python -B examples/example_0.py   # shortest path on directed graphs
uv run python -B examples/example_1.py   # arbitrary node types (NumPy arrays)
uv run python -B examples/example2.py    # random graph generation + plotting
```

Full example suite: [examples/](examples/) — 93 runnable scripts covering algorithms, drawing, geospatial, graphviz, and subclassing.
