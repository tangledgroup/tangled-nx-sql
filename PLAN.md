# PLAN: Idempotent Graph Operations

## Problem

### 1. Graph creation always INSERTs — crashes on duplicate name

`Graph.name` has a unique constraint on the DB column. Every call to
`nx_sql.DiGraph(session, name="demo0")` does an `INSERT`, which fails with
`UNIQUE constraint failed: graphs.name` if that name was used in a previous
run. This defeats the purpose of a persistent SQL backend — users must manually
delete `nx_sql.db` between runs.

### 2. Nodes and edges already idempotent (no change needed)

Both `_NodeDict.__setitem__` and `_SimpleInnerAdjDict._upsert_single` already
check for existence and UPDATE rather than INSERT when a duplicate is found.
Multi-edge paths (`_add_multi_edge`, `_MultiInnerAdjDict._upsert_edge`) also
handle this correctly.

---

## Solution: Load-or-create semantics for `Graph.__init__`

**File:** `nx_sql/nx_sql.py` — single edit, one block replacement (~15 lines).

### Current flow (lines 690–702)

```
graph_id is None
  → always INSERT GraphModel
  → crash on duplicate name
```

### New flow

```
graph_id is None
  if name provided:
    SELECT by name
      found → reuse graph_id, merge stored attrs (user attr overrides stored)
      not found → fall through to INSERT
  else:
    INSERT new (existing behavior)
```

### Code change

Replace the `if graph_id is None:` block with:

```python
        if graph_id is None:
            # Try to load by name for persistent reuse
            existing = None
            if name is not None:
                existing = self.session.scalar(
                    select(GraphModel).where(GraphModel.name == name)
                )
            if existing:
                self.graph_id = existing.graph_id
                if existing.attributes:
                    attr = {**existing.attributes, **(attr or {})}
            else:
                all_attrs = {**(attr or {})}
                if name is not None:
                    all_attrs["name"] = name
                gmodel = GraphModel(
                    graph_type=self._graph_type,
                    name=name,
                    attributes=all_attrs or None,
                )
                self.session.add(gmodel)
                self.session.commit()
                self.graph_id = gmodel.graph_id
```

### Attr merge semantics

When a graph is **loaded** from DB:
- Stored attrs + user-provided `attr` → merged (user `attr` wins on conflict)
- The merged dict is passed to `super().__init__()` for NetworkX's graph-level
  attributes
- The DB row itself is **not modified** — this is a read-only view

When a graph is **created** new:
- Existing behavior unchanged: all attrs (including `name`) stored in DB

---

## Behavior after change

```python
# Run 1: creates graph "demo0"
G = nx_sql.DiGraph(session, name="demo0")
G.add_edge('A', 'B', weight=0.1)
session.commit()

# Run 2: reuses same graph — nodes/edges persist
G = nx_sql.DiGraph(session, name="demo0")
list(G.nodes())   # ['A', 'B'] — already existed
list(G.edges())   # [('A', 'B')] — already existed
G.add_edge('C', 'D', weight=0.2)  # appends new
session.commit()

# Run 3: new name → fresh graph
G = nx_sql.DiGraph(session, name="demo1")
list(G.nodes())   # [] — empty, brand new
```

### Graph deletion cascades to nodes and edges (app layer)

When a graph is deleted, all its nodes and edges must be deleted too. This is
implemented at the **application/ORM layer** — no SQL `ON DELETE CASCADE` or
foreign key constraints. Two approaches:

1. **`Graph.delete()` method** on `_NXSQLBase` — when a user calls
   `G.delete()`, it issues `DELETE FROM nodes WHERE graph_id = ?` and
   `DELETE FROM edges WHERE graph_id = ?` before deleting the graph row.

2. **ORM-level `@event.listens_for`** on `Graph.before_delete` — automatically
   cascades delete of child rows when the ORM deletes a `GraphModel` instance.

Either way, the cascade is pure Python/SQLAlchemy, no DB-level FK constraints.
A subsequent `DiGraph(session, name="demo0")` will create a fresh graph since
the old one no longer exists.

### What is NOT done

- No schema changes. `Graph.name` stays `unique=True`.
