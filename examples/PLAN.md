# PLAN: Port NetworkX Examples to nx_sql

## Overview

Port NetworkX examples from `networkx/examples/` to `nx_sql`, using SQLAlchemy ORM session-backed graphs (`nx_sql.Graph`, `nx_sql.DiGraph`, `nx_sql.MultiGraph`, `nx_sql.MultiDiGraph`). Each example demonstrates a specific NetworkX API function or pattern working with persistent SQL graphs.

## Naming Convention

Example filenames mirror the NetworkX example names (without `plot_` prefix and without matplotlib dependencies):

- `examples/basic/plot_basic_directed.py` → `basic_directed.py`
- `examples/algorithms/plot_shortest_path.py` → `shortest_path.py`
- `examples/graph/plot_karate_club.py` → `karate_club.py`

Examples are organized in subdirectories matching the NetworkX example structure:
```
examples/
  basic/
  algorithms/
  graph/
  drawing/          # skip matplotlib; use print output only
  subclass/
```

## Structure Per Example File

Each file follows this pattern:
```python
"""Docstring mirroring the NetworkX original."""

import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base
from examples.utils import print_docstring

engine = create_engine("sqlite:///nx_sql.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


@print_docstring
def demo_example_name():
    """Description of what this example demonstrates."""
    with Session() as session:
        # Create nx_sql graph instead of nx.Graph
        G = nx_sql.DiGraph(session, name="example_name")
        
        # Build the graph using nx_sql API
        G.add_edges_from(...)
        
        # Run NetworkX algorithms on the SQL-backed graph
        result = nx.some_algorithm(G, ...)
        print(result)
        
        session.commit()


if __name__ == '__main__':
    demo_example_name()
```

## Graph Class Selection Guide

| NetworkX Example Uses | nx_sql Class |
|---|---|
| `nx.Graph` (undirected) | `nx_sql.Graph` |
| `nx.DiGraph` (directed) | `nx_sql.DiGraph` |
| `nx.MultiGraph` | `nx_sql.MultiGraph` |
| `nx.MultiDiGraph` | `nx_sql.MultiDiGraph` |

## Phase 1: Basic Examples (already partially covered by example_0.py, example_1.py)

### 1.1 `basic/simple_graph.py` → `basic/simple_graph.py`
- Create undirected Graph with manual positions
- Test: nodes(), edges(), add_edge, basic iteration
- Skip matplotlib; print node/edge info instead

### 1.2 `basic/plot_basic_directed.py` → `basic/directed_graph.py`
- Create DiGraph with manual layout
- Test: successors(), predecessors(), directed edges
- Verify edge direction is preserved

### 1.3 `basic/plot_properties.py` → `basic/graph_properties.py`
- Create lollipop graph, compute properties
- Test: density(), all_pairs_shortest_path_length(), average_shortest_path_length()
- Test: eccentricity(), radius(), diameter(), center(), periphery()
- Verify path length distribution

### 1.4 `basic/plot_read_write.py` → `basic/read_write.py`
- Demonstrate serialization/deserialization with SQLAlchemy persistence
- Test: write edgelist, read back into new session
- Show that graph data persists across sessions

## Phase 2: Graph Algorithm Examples

### 2.1 `algorithms/plot_shortest_path.py` → `algorithms/shortest_path.py`
- Dijkstra shortest path with weighted edges
- Test: nx.shortest_path(G, source, target, weight='weight')
- Test: nx.all_shortest_paths()
- Print path and highlight edges

### 2.2 `algorithms/plot_betweenness_centrality.py` → `algorithms/betweenness_centrality.py`
- Betweenness centrality on a real dataset
- Use nx.karate_club_graph() or nx.krackhardt_kite_graph() imported into nx_sql
- Test: nx.betweenness_centrality(G, k=10)
- Print top-centrality nodes

### 2.3 `algorithms/plot_cycle_detection.py` → `algorithms/cycle_detection.py`
- Find cycles in directed graph
- Test: nx.find_cycle(G, orientation='original')
- Test: nx.simple_cycles(G) on DiGraph
- Test: nx.cycle_basis(G) on Graph

### 2.4 `algorithms/plot_greedy_coloring.py` → `algorithms/greedy_coloring.py`
- Graph coloring on dodecahedral graph
- Test: nx.greedy_color(G)
- Print color assignment per node

### 2.5 `algorithms/plot_krackhardt_centrality.py` → `algorithms/krackhardt_centrality.py`
- Centrality measures on Krackhardt kite graph
- Test: nx.betweenness_centrality(), nx.degree_centrality(), nx.closeness_centrality()
- Print all three for each node

### 2.6 `algorithms/plot_davis_club.py` → `algorithms/davis_club.py`
- Bipartite projections
- Test: nx.davis_southern_women_graph() imported into nx_sql
- Test: nx.bipartite.projected_graph(), nx.bipartite.weighted_projected_graph()
- Print degree of each woman

### 2.7 `algorithms/plot_girvan_newman.py` → `algorithms/girvan_newman.py`
- Community detection via Girvan-Newman on karate club
- Test: nx.community.girvan_newman(G)
- Compute modularity at each step
- Print community assignments

### 2.8 `algorithms/plot_beam_search.py` → `algorithms/beam_search.py`
- Progressive widening beam search
- Custom implementation using nx.bfs_beam_edges()
- Test on gnp_random_graph imported into nx_sql
- Find node with high eigenvector centrality

### 2.9 `algorithms/plot_subgraphs.py` → `algorithms/subgraphs.py`
- Graph partitioning into supported/unsupported subgraphs
- Test: G.subgraph(nodes), copy(), compose()
- Verify is_isomorphic after reconstruction

### 2.10 `algorithms/plot_blockmodel.py` → `algorithms/blockmodel.py`
- Quotient graph / block model
- Test: nx.quotient_graph(H, partitions)
- Print block structure

## Phase 3: Graph Generator Examples

### 3.1 `graph/plot_erdos_renyi.py` → `generators/erdos_renyi.py`
- gnm_random_graph properties
- Test: nx.gnm_random_graph(n, m), density, clustering per node
- Print adjacency list via generate_adjlist

### 3.2 `graph/plot_degree_sequence.py` → `generators/degree_sequence.py`
- Configuration model from degree sequence
- Test: nx.configuration_model(z), degree_histogram
- Verify degree sequence matches input

### 3.3 `graph/plot_karate_club.py` → `generators/karate_club.py`
- Zachary's karate club graph
- Test: nx.karate_club_graph() imported into nx_sql
- Print node degrees
- Show persistence across sessions

### 3.4 `graph/plot_mst.py` → `generators/minimum_spanning_tree.py`
- Minimum spanning tree on weighted graph
- Test: nx.minimum_spanning_tree(G)
- Print MST edges and total weight

### 3.5 `graph/plot_dag_layout.py` → `generators/dag_layout.py`
- DAG topological layout
- Test: nx.topological_sort(), nx.topological_generations()
- Build a dependency graph, show topological order

### 3.6 `graph/plot_triad_types.py` → `algorithms/triad_types.py`
- All 16 triad types in directed graphs
- Test: nx.triadic_census(G) for each type
- Print census results

## Phase 4: Advanced Algorithm Examples

### 4.1 `algorithms/plot_lca.py` → `algorithms/lca.py`
- Lowest common ancestor
- Test: nx.lowest_common_ancestor(DAG, u, v)
- Test: nx.all_pairs_lowest_common_ancestor()

### 4.2 `algorithms/plot_maximum_independent_set.py` → `algorithms/maximum_independent_set.py`
- Maximum independent set
- Test: nx.algorithms.approximation.maximum_independent_set()

### 4.3 `algorithms/plot_trust_rank.py` → `algorithms/trust_rank.py`
- TrustRank algorithm (link analysis)
- Test on a small web graph in nx_sql

### 4.4 `algorithms/plot_rcm.py` → `algorithms/rcm.py`
- Reverse Cuthill-McKee ordering
- Test: nx.reverse_cuthill_mckee_ordering(G)
- Print reordering

### 4.5 `algorithms/plot_dedensification.py` → `algorithms/dedensification.py`
- Graph dedensification
- Test on DiGraph with multi-edge-like structure

### 4.6 `algorithms/plot_metric_closure.py` → `algorithms/metric_closure.py`
- Metric closure / transitive closure
- Test: nx.metric_closure(G)

### 4.7 `algorithms/plot_parallel_betweenness.py` → `algorithms/parallel_betweenness.py`
- Betweenness on parallel/distributed-like structure

## Phase 5: Graph Operations & Views

### 5.1 copy(), subgraph, to_directed, to_undirected
- Already partially tested; add comprehensive examples
- Test: G.copy(), G.subgraph(nodes), G.to_directed()
- Verify data persistence through transformations

### 5.2 compose, union, disjoint_union
- Test: nx.compose(G1, G2), nx.union(G1, G2)
- Show graph composition with SQL persistence

### 5.3 complement
- Test: nx.complement(G) — may need in-memory fallback

## Phase 6: nx_sql Bug Fixes (if found during examples)

### Known Issues to Fix During Implementation:

1. **`recursive_simple_cycles()`** — crashes on nx_sql graphs because `strongly_connected_components` accesses `G._adj[v]` directly and our `_AdjacencyDict.__getitem__` doesn't handle all cases properly.
   - **Fix**: Ensure `_AdjacencyDict.__iter__` works correctly when called during SCC computation; add missing `__contains__` methods if needed.

2. **`line_graph()`** — crashes because `nx.empty_graph(0, create_using=None, default=nx_sql.Graph)` creates a graph with `session=None` but the `_AdjacencyDict.__getitem__` is still called on the original graph G during edge reading.
   - **Fix**: The actual issue is that line_graph reads edges from G fine, but the error occurs in L's `add_edges_from`. Need to ensure tuple nodes like `(1,2)` are properly handled when session=None (in-memory mode).

3. **`add_edges_from()` with 3-tuple format** — `G.add_edges_from([(u,v,w)])` where w is not a dict fails because NetworkX passes `(u,v,{w})` internally which our code doesn't handle correctly for non-dict data.
   - **Fix**: Add handling in `add_edges_from` for edge tuples where the third element is not a dict (convert to `{data_key: value}`).

4. **MultiGraph/MultiDiGraph** — `add_edge()` fails with `AttributeError: 'MultiGraph' object has no attribute 'new_edge_key'`.
   - **Fix**: Implement `new_edge_key()` method on MultiGraph and MultiDiGraph classes, or override `add_edge` to avoid calling parent's multi-edge path.

5. **`subgraph_view`** — `G.subgraph([nodes])` returns empty edges.
   - **Fix**: Ensure `generic_subgraph_view` properly reconstructs `_adj` references pointing to the correct source nodes.

## Execution Order

1. **Fix bugs first** (Phase 6 items) — these block example implementation
2. **Phase 1** (basic examples) — foundation examples
3. **Phase 2** (algorithm examples) — core algorithm coverage
4. **Phase 3** (generator examples) — graph creation patterns
5. **Phase 4** (advanced algorithms) — edge cases and special algorithms
6. **Phase 5** (graph operations) — composition and transformation

## Non-Goals (Skip These)

- **Drawing examples** (`examples/drawing/`, `examples/graphviz_drawing/`, etc.) — require matplotlib/graphviz; not applicable to SQL-backed graphs
- **Geospatial examples** (`examples/geospatial/`) — require external geo libraries (geopandas, shapely, osmnx)
- **External tool examples** (`examples/external/`) — require iglot, plotly, JavaScript
- **3D drawing examples** (`examples/3d_drawing/`) — require mayavi/pyvista

## Testing Strategy

Each example file:
1. Creates a fresh SQLAlchemy session
2. Builds an nx_sql graph with the specified structure
3. Runs the target NetworkX algorithm(s)
4. Prints results for verification
5. Commits and closes session
6. Can be run standalone: `uv run python examples/<category>/<name>.py`

All examples share `nx_sql.db` — each creates its own named graph to avoid conflicts.
