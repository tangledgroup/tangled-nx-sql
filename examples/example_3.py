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

engine = create_engine("sqlite:///nx_sql.db")
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

OWNS_DATA = {
    20: {"corolla": 12, "civic": 11, "golf": 8, "tucson": 6, "model3": 7, "outback": 3},
    30: {"modely": 9, "tucson": 8, "golf": 6, "civic": 5, "corolla": 4, "model3": 8, "outback": 5, "f150": 4},
    40: {"gle": 8, "f150": 6, "modely": 8, "outback": 7, "bmw3": 6},
    50: {"f150": 12, "gle": 8, "bmw3": 8},
    60: {"corolla": 10, "civic": 9, "outback": 8, "model3": 7},
}

LIVES_IN_DATA = {
    "US": {
        "newyork":   {20: 16, 30: 22, 40: 21, 50: 20, 60: 21},
        "losangeles":{20: 18, 30: 24, 40: 20, 50: 19, 60: 19},
        "chicago":   {20: 15, 30: 21, 40: 22, 50: 21, 60: 21},
        "detroit":   {20: 14, 30: 20, 40: 24, 50: 22, 60: 20},
    },
    "Europe": {
        "london":   {20: 15, 30: 21, 40: 22, 50: 21, 60: 21},
        "berlin":   {20: 16, 30: 22, 40: 22, 50: 20, 60: 20},
        "paris":    {20: 14, 30: 20, 40: 23, 50: 22, 60: 21},
    },
    "Serbia": {
        "belgrade":   {20: 20, 30: 26, 40: 22, 50: 18, 60: 14},
        "novisad":    {20: 19, 30: 25, 40: 23, 50: 18, 60: 15},
        "nis":        {20: 22, 30: 24, 40: 21, 50: 18, 60: 15},
    },
}

LOCATED_IN_CARS_BY_REGION = {
    "US": [c["id"] for c in CARS],  # all 10
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

MANUFACTURED_IN = [
    ("corolla",  "Toyota City, Japan"),
    ("civic",    "Greensburg, IN"),
    ("f150",     "Dearborn, MI"),
    ("bmw3",     "Munich, Germany"),
    ("gle",      "Tuscaloosa, AL"),
    ("tucson",   "Montgomery, AL"),
    ("model3",   "Fremont, CA"),
    ("modely",   "Fremont, CA"),
    ("golf",     "Wolfsburg, Germany"),
    ("outback",  "Lafayette, IN"),
]

# ── Indexes ──────────────────────────────────────────────────────────────────

CAR_BY_ID = {c["id"]: c for c in CARS}
CITY_BY_ID = {c["id"]: c for c in CITIES}


def _pick_cities_for_age(age: int) -> list[str]:
    if age <= 30:
        return ["newyork", "losangeles"]
    elif age == 40:
        return ["chicago", "detroit"]
    elif age == 50:
        return ["houston", "phoenix"]
    else:
        return ["miami", "losangeles"]


def _income_for_region_age(region: str, age: int) -> float:
    base = {"US": 65, "Europe": 50, "Serbia": 18}[region]
    return round(base + (40 - age) * 0.5, 1)


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
        for age, cars_dict in OWNS_DATA.items():
            for car_id in cars_dict:
                G.add_edge(age, car_id, relation_type="owns")

        # connected: city ↔ car (car is sold in this city)
        for region, car_ids in LOCATED_IN_CARS_BY_REGION.items():
            for city_id in LIVES_IN_DATA[region]:
                for car_id in car_ids:
                    G.add_edge(city_id, car_id, relation_type="connected")

        # connected: city ↔ age (age group present in this city)
        for region, cities_dict in LIVES_IN_DATA.items():
            for city_id in cities_dict:
                for age in cities_dict[city_id]:
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

        # 4. Visualize ──────────────────────────────────────────────────────
        _plot_demographics(G, rel_counts, car_nodes, city_nodes, age_nodes)


# ── Visualization ────────────────────────────────────────────────────────────

def _plot_demographics(G, rel_counts, car_nodes, city_nodes, age_nodes):
    """Render the demographic network as a PNG with color-coded nodes and edges."""

    fig, ax = plt.subplots(figsize=(16, 12))

    # ── Edge colors by relation_type ──────────────────────────────────
    EDGE_STYLES = {
        "owns":            {"color": "#d62728", "style": "-",   "width": 2.0, "label": "owns"},
        "connected":       {"color": "#1f77b4", "style": ":",   "width": 0.8, "label": "connected"},
        "compares_with":   {"color": "#9467bd", "style": "-",   "width": 2.5, "label": "compares_with"},
    }

    # ── Layout: force-directed with type-based bias ───────────────────
    # Use a wider layout to separate the three node layers clearly
    pos = nx.spring_layout(G, seed=42, k=3.0, iterations=80, dim=2)

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
        edges = [(u, v) for u, v, d in G.edges(data=True) if d.get("relation_type") == rel_type]
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
    for n in G.nodes():
        if isinstance(n, int):
            node_sizes.append(800)
        elif n in car_nodes:
            node_sizes.append(400)
        else:
            node_sizes.append(250)  # city

    nx.draw_networkx_nodes(G, pos, node_color=[node_colors[n] for n in G.nodes()],
                           node_size=node_sizes, alpha=0.9, ax=ax)

    # ── Labels ────────────────────────────────────────────────────────
    age_labels = {n: f"{int(n)}s" for n in age_nodes}
    nx.draw_networkx_labels(G, pos, labels=age_labels, font_size=12, font_weight="bold",
                            font_family="sans-serif", ax=ax)

    # Car model labels — top 12 by degree
    car_degrees = {n: G.degree(n) for n in car_nodes}
    top_cars = sorted(car_degrees, key=car_degrees.get, reverse=True)[:12]
    car_labels = {n: CAR_BY_ID[n]["model"] for n in top_cars if n in pos}
    nx.draw_networkx_labels(G, pos, labels=car_labels, font_size=7,
                            font_family="monospace", ax=ax)

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

    ax.set_title("Car × City × Age Demographic Network\n10 cars · 10 cities · 5 age groups",
                 fontsize=14, fontweight="bold", pad=20)
    ax.axis("off")
    plt.tight_layout()
    plt.savefig("examples/example_3_demographics.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("\nPlot saved to examples/example_3_demographics.png")


if __name__ == "__main__":
    demo_demographics()
