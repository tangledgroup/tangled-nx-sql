"""Generate a synthetic demographic network: Car × City × Age.

Demonstrates multiple relationship types on an undirected nx_sql.Graph,
computing statistics and rendering a multi-style visualization.
"""

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

engine = create_engine("sqlite:///example_3.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


# ── Data Definitions ─────────────────────────────────────────────────────────

CARS = [
    {"id": "corolla",       "manufacturer": "Toyota",   "model": "Corolla",     "year_range": [2020, 2025], "category": "Sedan",       "hp": 139, "fuel_economy_mpg": 32, "price_tier": "economy"},
    {"id": "civic",         "manufacturer": "Honda",    "model": "Civic",       "year_range": [2021, 2025], "category": "Sedan",       "hp": 158, "fuel_economy_mpg": 33, "price_tier": "economy"},
    {"id": "f150",          "manufacturer": "Ford",     "model": "F-150",       "year_range": [2021, 2025], "category": "Pickup",        "hp": 290, "fuel_economy_mpg": 24, "price_tier": "mid"},
    {"id": "bmw3",          "manufacturer": "BMW",      "model": "3 Series",    "year_range": [2021, 2025], "category": "Sedan",       "hp": 255, "fuel_economy_mpg": 29, "price_tier": "premium"},
    {"id": "gle",           "manufacturer": "Mercedes", "model": "GLE",         "year_range": [2021, 2025], "category": "SUV",           "hp": 362, "fuel_economy_mpg": 22, "price_tier": "luxury"},
    {"id": "tucson",        "manufacturer": "Hyundai",  "model": "Tucson",      "year_range": [2021, 2025], "category": "SUV",           "hp": 187, "fuel_economy_mpg": 29, "price_tier": "economy"},
    {"id": "model3",        "manufacturer": "Tesla",    "model": "Model 3",     "year_range": [2021, 2025], "category": "Sedan",       "hp": 283, "fuel_economy_mpg": 132, "price_tier": "premium"},
    {"id": "modely",        "manufacturer": "Tesla",    "model": "Model Y",     "year_range": [2021, 2025], "category": "SUV",           "hp": 283, "fuel_economy_mpg": 111, "price_tier": "premium"},
    {"id": "golf",          "manufacturer": "Volkswagen","model": "Golf",       "year_range": [2021, 2025], "category": "Hatchback",   "hp": 158, "fuel_economy_mpg": 32, "price_tier": "mid"},
    {"id": "outback",       "manufacturer": "Subaru",   "model": "Outback",     "year_range": [2021, 2025], "category": "Wagon",       "hp": 182, "fuel_economy_mpg": 30, "price_tier": "mid"},
]

CITIES = [
    {"id": "newyork",   "name": "New York",   "country": "USA",  "region": "US"},
    {"id": "losangeles","name": "Los Angeles","country": "USA",  "region": "US"},
    {"id": "chicago",   "name": "Chicago",    "country": "USA",  "region": "US"},
    {"id": "detroit",   "name": "Detroit",    "country": "USA",  "region": "US"},
    {"id": "london",    "name": "London",     "country": "UK",   "region": "Europe"},
    {"id": "berlin",    "name": "Berlin",     "country": "Germany","region": "Europe"},
    {"id": "paris",     "name": "Paris",      "country": "France","region": "Europe"},
    {"id": "belgrade",  "name": "Belgrade",   "country": "Serbia","region": "Serbia"},
    {"id": "novisad",   "name": "Novi Sad",   "country": "Serbia","region": "Serbia"},
    {"id": "nis",       "name": "Nis",        "country": "Serbia","region": "Serbia"},
]

AGE_GROUPS = [20, 30, 40, 50, 60]

# ── Relationship Definitions ─────────────────────────────────────────────────

AGE_CAR_CONNECTIONS = {
    20: ["corolla", "civic", "golf", "tucson", "model3", "outback"],
    30: ["modely", "tucson", "golf", "civic", "corolla", "model3", "outback", "f150"],
    40: ["gle", "f150", "modely", "outback", "bmw3"],
    50: ["f150", "gle", "bmw3"],
    60: ["corolla", "civic", "outback", "model3"],
}

CITY_AGE_CONNECTIONS = {
    "US": ["newyork", "losangeles", "chicago", "detroit"],
    "Europe": ["london", "berlin", "paris"],
    "Serbia": ["belgrade", "novisad", "nis"],
}
CITY_CARS_BY_REGION = {
    "US": [c["id"] for c in CARS],
    "Europe": ["corolla", "civic", "bmw3", "gle", "model3", "modely", "golf", "outback"],
    "Serbia": ["corolla", "civic", "tucson", "golf", "model3", "outback"],
}



COMPARES_WITH = [
    ("corolla", "civic"),
    ("f150",),
    ("bmw3",),
    ("gle",),
    ("model3", "modely"),
    ("golf", "outback"),
]

# ── Indexes ──────────────────────────────────────────────────────────────────

CAR_BY_ID = {c["id"]: c for c in CARS}
CITY_BY_ID = {c["id"]: c for c in CITIES}
# ── Demo Function ────────────────────────────────────────────────────────────

def demo_demographics():
    """Build Car × City × Age demographic network with multiple relationship types."""

    with Session() as session:
        G = nx_sql.Graph(session, name="demo_demographics")

        # 1. Add nodes ──────────────────────────────────────────────────────
        print("Adding nodes...")

        # Car nodes (20) — use string IDs, store full data in attributes
        for car in CARS:
            G.add_node(car["id"], **{k: v for k, v in car.items() if k != "id"})

        # City nodes (20)
        for city in CITIES:
            G.add_node(city["id"], **{k: v for k, v in city.items() if k != "id"})

        # Age group nodes (5)
        for age in AGE_GROUPS:
            G.add_node(age, age_group=f"{age}s")

        print(f"  Nodes: {G.number_of_nodes()}")

        # 2. Add edges ──────────────────────────────────────────────────────
        print("Adding edges...")

        # owns: age ↔ car
        for age, car_ids in AGE_CAR_CONNECTIONS.items():
            for car_id in car_ids:
                G.add_edge(age, car_id, relation_type="owns")

        # connected: city ↔ car (limit each city to ~70% of available cars)
        for region, car_ids in CITY_CARS_BY_REGION.items():
            for city_id in CITY_AGE_CONNECTIONS[region]:
                for i, car_id in enumerate(car_ids):
                    if i % 10 < 7:  # ~70% retention
                        G.add_edge(city_id, car_id, relation_type="connected")

        # connected: city ↔ age (each city connects to 3 out of 5 age groups)
        for region, city_ids in CITY_AGE_CONNECTIONS.items():
            for city_id in city_ids:
                for age_idx, age in enumerate(AGE_GROUPS):
                    if (age_idx + hash(city_id) % 5) < 3:  # 3/5 = 60% retention
                        G.add_edge(city_id, age, relation_type="connected")

        # compares_with: car ↔ car
        for comp in COMPARES_WITH:
            for i in range(len(comp)):
                for j in range(i + 1, len(comp)):
                    G.add_edge(comp[i], comp[j], relation_type="compares_with",
                               competition_score=6)


        print(f"  Edges: {G.number_of_edges()}")

        session.commit()

        # 3. Compute statistics ─────────────────────────────────────────────
        print("\n── Statistics ──────────────────────────────────────────────")
        print(f"Nodes:  {G.number_of_nodes()}")
        print(f"Edges:  {G.number_of_edges()}")
        avg_deg = sum(dict(G.degree()).values()) / G.number_of_nodes() if G.number_of_nodes() else 0
        print(f"Avg degree: {avg_deg:.2f}")

        # Breakdown by relation_type
        rel_counts = {}
        for u, v, d in G.edges(data=True):
            rt = d.get("relation_type", "unknown")
            rel_counts[rt] = rel_counts.get(rt, 0) + 1
        print("\nEdges by relation type:")
        for rt, count in sorted(rel_counts.items(), key=lambda x: -x[1]):
            print(f"  {rt:20s}: {count}")

        # Breakdown by node type
        car_nodes = [n for n in G.nodes() if isinstance(n, str) and n in CAR_BY_ID]
        city_nodes = [n for n in G.nodes() if isinstance(n, str) and n in CITY_BY_ID]
        age_nodes = [n for n in G.nodes() if isinstance(n, int)]
        print(f"\nCar nodes:     {len(car_nodes)}")
        print(f"City nodes:    {len(city_nodes)}")
        print(f"Age nodes:     {len(age_nodes)}")

        # 4. Query example: who drives Corolla?
        print("\n── Query: Who drives Corolla? ──────────────────────────────")
        corolla_id = "corolla"
        if corolla_id in G:
            # Age groups that own Corolla
            owns_edges = [(u, v, d) for u, v, d in G.edges(corolla_id, data=True)
                          if d.get("relation_type") == "owns"]
            age_drivers = []
            for u, v, _ in owns_edges:
                other = v if u == corolla_id else u
                if isinstance(other, int):
                    age_drivers.append(f"{other}s")
            print(f"  Age groups that own Corolla: {', '.join(age_drivers)}")

            # Cities where Corolla is sold
            connected_cities = [(u, v, d) for u, v, d in G.edges(corolla_id, data=True)
                                if d.get("relation_type") == "connected"]
            city_names = []
            for u, v, _ in connected_cities:
                other = v if u == corolla_id else u
                if isinstance(other, str) and other in CITY_BY_ID:
                    city_names.append(CITY_BY_ID[other]["name"])
            city_names = sorted(set(city_names))
            print(f"  Cities where Corolla is sold ({len(city_names)}): {', '.join(sorted(city_names))}")
        else:
            print("  Corolla not found in graph.")

        # 5. Visualize ──────────────────────────────────────────────────
        _plot_demographics(G, rel_counts, car_nodes, city_nodes, age_nodes,
                           highlight_node=None)

        # 6. Corolla subgraph view
        _plot_demographics(G, rel_counts, car_nodes, city_nodes, age_nodes,
                           highlight_node="corolla", save_path="examples/example_3_corolla.png")


# ── Visualization ────────────────────────────────────────────────────────────

def _plot_demographics(G, rel_counts, car_nodes, city_nodes, age_nodes,
                       highlight_node=None, save_path="examples/example_3_demographics.png"):
    """Render the demographic network as a PNG with color-coded nodes and edges.

    If highlight_node is provided, only that node's neighbors are shown
    (subgraph view).
    """

    fig, ax = plt.subplots(figsize=(16, 12))

    # Optional: filter to subgraph around a highlighted node
    if highlight_node is not None:
        # Only include nodes directly connected via "owns" or "connected"
        # (exclude "compares_with" which would show competitor cars)
        relevant_edges = [(u, v) for u, v, d in G.edges(data=True)
                          if d.get("relation_type") in ("owns", "connected")
                          and (u == highlight_node or v == highlight_node)]
        neighbors = set()
        for u, v in relevant_edges:
            other = v if u == highlight_node else u
            neighbors.add(other)
        neighbors.add(highlight_node)
        G_show = G.subgraph(neighbors).copy()
    else:
        G_show = G

    # ── Edge colors by relation_type ──────────────────────────────────
    EDGE_STYLES = {
        "owns":            {"color": "#d62728", "style": "-",   "width": 2.0, "label": "owns"},
        "connected":       {"color": "#1f77b4", "style": ":",   "width": 0.8, "label": "connected"},
        "compares_with":   {"color": "#9467bd", "style": "-",   "width": 2.5, "label": "compares_with"},
    }

    # ── Layout: force-directed with type-based bias ───────────────────
    pos = nx.spring_layout(G_show, seed=42, k=3.0, iterations=80, dim=2)

    # Hard-bias x positions so each type forms a distinct vertical band
    for node in pos:
        if isinstance(node, int):
            # Age groups: left column, spread vertically
            age_idx = list(AGE_GROUPS).index(node)
            pos[node][0] = -3.5
            pos[node][1] = 0.75 - age_idx * 0.38  # spread across y
        elif isinstance(node, str) and node in CAR_BY_ID:
            # Cars: center column, spread vertically by category
            car_idx = list(CAR_BY_ID.keys()).index(node)
            pos[node][0] = 0.0
            pos[node][1] = 2.0 - (car_idx / max(len(CARS) - 1, 1)) * 4.0
        elif isinstance(node, str) and node in CITY_BY_ID:
            # Cities: right column, grouped by region
            city_info = CITY_BY_ID[node]
            region_order = {"US": 0, "Europe": 1, "Serbia": 2}
            base_x = 3.5 + region_order.get(city_info["region"], 1) * 0.8
            # Within region, spread vertically
            region_cities = [c for c in CITIES if c["region"] == city_info["region"]]
            city_idx_in_region = next(i for i, rc in enumerate(region_cities) if rc["id"] == node)
            pos[node][0] = base_x
            pos[node][1] = 2.0 - (city_idx_in_region / max(len(region_cities) - 1, 1)) * 4.0

    # ── Draw edges by relation type ───────────────────────────────────
    linestyle_map = {"-": "solid", "--": "dashed", ":": "dotted", "-.": "dashdot"}
    for rel_type, style in EDGE_STYLES.items():
        edges = [(u, v) for u, v, d in G_show.edges(data=True) if d.get("relation_type") == rel_type]
        if not edges:
            continue
        # Draw each edge individually for better control over overlapping segments
        for u, v in edges:
            px = [pos[u][0], pos[v][0]]
            py = [pos[u][1], pos[v][1]]
            ax.plot(px, py, color=style["color"], linestyle=linestyle_map.get(style["style"], "-"),
                    linewidth=style["width"], alpha=0.3)

    # ── Draw nodes by type ───────────────────────────────────────────
    node_colors = {}
    for n in age_nodes:
        node_colors[n] = "#e41a1c"
    for n in car_nodes:
        node_colors[n] = "#377eb8"
    for n in city_nodes:
        node_colors[n] = "#4daf4a"
    node_sizes = []
    for n in G_show.nodes():
        if isinstance(n, int):
            node_sizes.append(800)
        elif n in car_nodes:
            node_sizes.append(400)
        else:
            node_sizes.append(250)  # city

    nx.draw_networkx_nodes(G_show, pos, node_color=[node_colors[n] for n in G_show.nodes()],
                           node_size=node_sizes, alpha=0.9, ax=ax)

    # ── Labels ────────────────────────────────────────────────────────
    age_labels = {n: f"{int(n)}s" for n in age_nodes if n in G_show}
    nx.draw_networkx_labels(G_show, pos, labels=age_labels, font_size=12, font_weight="bold",
                            font_family="sans-serif", ax=ax)

    # Car model labels — all cars in subgraph
    car_labels = {n: CAR_BY_ID[n]["model"] for n in car_nodes if n in G_show}
    nx.draw_networkx_labels(G_show, pos, labels=car_labels, font_size=7,
                            font_family="monospace", ax=ax)

    # City labels — all cities in subgraph
    city_labels = {n: CITY_BY_ID[n]["name"] for n in city_nodes if n in G_show}
    nx.draw_networkx_labels(G_show, pos, labels=city_labels, font_size=7,
                            font_family="sans-serif", ax=ax)

    # ── Legend ────────────────────────────────────────────────────────
    from matplotlib.lines import Line2D

    node_legend = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#e41a1c",
               markersize=10, label=f"Age Group (n={len(age_nodes)})"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#377eb8",
               markersize=8, label=f"Car Model (n={len(car_nodes)})"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#4daf4a",
               markersize=6, label=f"City (n={len(city_nodes)})"),
    ]

    edge_legend = []
    for rel_type, style in EDGE_STYLES.items():
        if rel_counts.get(rel_type, 0) > 0:
            ls = linestyle_map.get(style["style"], "-")
            edge_legend.append(Line2D([0], [0], color=style["color"], linestyle=ls,
                                      linewidth=style["width"], label=f"{rel_type} ({rel_counts[rel_type]})"))
    # Clean up legend labels to just show relation type + count
    for handle in edge_legend:
        old_label = handle.get_label()
        handle.set_label(old_label.split(" (")[0])

    ax.legend(handles=node_legend + edge_legend, loc="lower left", fontsize=8,
              title="Legend", title_fontsize=9, framealpha=0.9)

    if highlight_node is not None:
        node_label = CAR_BY_ID[highlight_node]["model"] if highlight_node in CAR_BY_ID else str(highlight_node)
        ax.set_title(f"Who drives {node_label}?\nNeighbors of {CAR_BY_ID.get(highlight_node, {}).get('model', highlight_node)}",
                     fontsize=14, fontweight="bold", pad=20)
    else:
        ax.set_title("Car × City × Age Demographic Network\n10 cars · 10 cities · 5 age groups",
                     fontsize=14, fontweight="bold", pad=20)
    ax.axis("off")
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\nPlot saved to {save_path}")


if __name__ == "__main__":
    demo_demographics()
