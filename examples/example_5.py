"""Example 5 – generate a car-ecosystem graph and visualise it.

Deterministic graph generation (SEED=42) with exactly:
  - 10 CarManufacturer nodes
  - 100 CarModel nodes (10 per manufacturer)
  - 100 OwnerProfile nodes
  - 10 City nodes

Edges:
  - headquarters       : CarManufacturer → City
  - produces            : CarManufacturer → CarModel
  - owns                : OwnerProfile → CarModel (1-3 per owner)
  - sold_in             : CarModel → City
  - resides_in          : OwnerProfile → City (home city)
  - works_in            : OwnerProfile → City (work city, different from home)
  - competes_with       : CarModel ↔ CarModel (same type, similar HP)
  - neighboring_country : City ↔ City (same country)
  - same_hq             : CarManufacturer ↔ CarManufacturer (same city)

Output: example_5_graph.png (deterministic every run).
"""

import os
import random
import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ── Matplotlib setup (must be before pyplot import) ──────────────────────────
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

import community as community_louvain

import nx_sql
from nx_sql.models import Base

# ── Constants ────────────────────────────────────────────────────────────────
SEED = 42

_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(_DIR, "..", "example_5.db")
OUTPUT_PNG = os.path.join(_DIR, "example_5_graph.png")

# ── Colour maps ──────────────────────────────────────────────────────────────
TYPE_COLORS = {
    "CarManufacturer": "#3B82F6",
    "CarModel":        "#10B981",
    "OwnerProfile":    "#F59E0B",
    "City":            "#8B5CF6",
}

EDGE_STYLES = {
    "same_hq":           ("#60A5FA", 0.04, 0.3),
    "neighboring_country": ("#06B6D4", 0.08, 0.4),
    "competes_with":     ("#EF4444", 0.12, 0.6),
    "sold_in":           ("#8B5CF6", 0.12, 0.5),
    "resides_in":        ("#A78BFA", 0.15, 0.6),
    "headquarters":      ("#3B82F6", 0.30, 1.0),
    "produces":          ("#10B981", 0.35, 1.2),
    "owns":              ("#F59E0B", 0.40, 1.5),
    "works_in":          ("#EC4899", 0.15, 0.6),
}

# ── Reference data ───────────────────────────────────────────────────────────
COMPANY_NAMES = [
    "Toyota", "Volkswagen", "Ford", "General Motors", "Honda",
    "Stellantis", "Hyundai", "BMW", "Mercedes-Benz", "Audi",
]

COMPANY_DATA = [
    {"headquarters": "Toyota City",  "country": "Japan",       "founded_year": 1937, "employee_count": 372817},
    {"headquarters": "Wolfsburg",    "country": "Germany",     "founded_year": 1937, "employee_count": 675805},
    {"headquarters": "Dearborn",     "country": "USA",         "founded_year": 1903, "employee_count": 403000},
    {"headquarters": "Detroit",      "country": "USA",         "founded_year": 1908, "employee_count": 163000},
    {"headquarters": "Chuo, Tokyo",  "country": "Japan",       "founded_year": 1948, "employee_count": 204000},
    {"headquarters": "Rome",         "country": "Italy",       "founded_year": 2011, "employee_count": 250000},
    {"headquarters": "Seoul",        "country": "South Korea", "founded_year": 1967, "employee_count": 123000},
    {"headquarters": "Munich",       "country": "Germany",     "founded_year": 1916, "employee_count": 109000},
    {"headquarters": "Stuttgart",    "country": "Germany",     "founded_year": 1926, "employee_count": 172000},
    {"headquarters": "Ingolstadt",   "country": "Germany",     "founded_year": 1909, "employee_count": 107000},
]

CAR_TEMPLATES = {
    "Toyota": [
        ("Corolla",  "sedan",       "1.8L I4 Hybrid",    139, 139, 1370),
        ("Camry",    "sedan",       "2.5L I4",           203, 184, 1590),
        ("RAV4",     "suv",         "2.5L I4 Hybrid",    219, 163, 1700),
        ("Highlander","suv",        "3.5L V6",           295, 263, 1995),
        ("Prius",    "hatchback",   "1.8L I4 Hybrid",    121, 142, 1380),
        ("Land Cruiser","suv",      "3.5L Twin-Turbo V6",409, 479, 2560),
        ("Supra",    "sports_car",  "3.0L Turbo I6",     382, 485, 1495),
        ("Yaris",    "hatchback",   "1.5L I3",           106, 138, 1070),
        ("Sienna",   "minivan",     "2.5L I4 Hybrid",    245, 243, 2070),
        ("Tacoma",   "truck",       "3.5L V6",           278, 265, 1900),
    ],
    "Volkswagen": [
        ("Golf",     "hatchback",   "1.4L TSI",          150, 250, 1330),
        ("Passat",   "sedan",       "2.0L TDI",          150, 360, 1470),
        ("Tiguan",   "suv",         "2.0L TSI",          184, 320, 1655),
        ("Arteon",   "sedan",       "2.0L TSI",          268, 350, 1635),
        ("Atlas",    "suv",         "3.6L V6",           276, 360, 2050),
        ("Jetta",    "sedan",       "1.4L TSI",          158, 250, 1345),
        ("Taos",     "suv",         "1.4L TSI",          158, 250, 1470),
        ("ID.4",     "suv",         "Electric",          201, 310, 2075),
        ("GTI",      "hatchback",   "2.0L TSI",          241, 350, 1425),
        ("GTE",      "hatchback",   "1.4L TSI Hybrid",   245, 400, 1610),
    ],
    "Ford": [
        ("F-150",    "truck",       "3.5L V6 EcoBoost",  400, 583, 2100),
        ("Mustang",  "sports_car",  "5.0L V8",           450, 529, 1723),
        ("Bronco",   "suv",         "2.7L V6 EcoBoost",  330, 563, 1960),
        ("Explorer", "suv",         "2.3L Turbo I4",     300, 420, 1990),
        ("Escape",   "suv",         "1.5L Turbo I3",     181, 275, 1635),
        ("Focus",    "hatchback",   "2.0L I4",           160, 240, 1350),
        ("Fusion",   "sedan",       "2.0L Turbo I4",     245, 350, 1650),
        ("Ranger",   "truck",       "2.3L Turbo I4",     270, 420, 1875),
        ("Maverick", "truck",       "2.0L Turbo I4",     250, 350, 1760),
        ("Edge",     "suv",         "2.0L Turbo I4",     250, 350, 1850),
    ],
    "General Motors": [
        ("Silverado","truck",       "6.2L V8",           420, 623, 2350),
        ("Corvette", "sports_car",  "6.2L V8",           490, 637, 1560),
        ("Escalade", "suv",         "6.2L V8",           420, 623, 2780),
        ("Equinox",  "suv",         "1.5L Turbo I4",     175, 260, 1650),
        ("Malibu",   "sedan",       "1.5L Turbo I4",     160, 250, 1480),
        ("Blazer",   "suv",         "3.6L V6",           308, 350, 1900),
        ("Traverse", "suv",         "3.6L V6",           310, 360, 2000),
        ("Camaro",   "sports_car",  "6.2L V8",           455, 617, 1645),
        ("Impala",   "sedan",       "3.6L V6",           305, 360, 1680),
        ("Bolt EV",  "hatchback",   "Electric",          200, 266, 1580),
    ],
    "Honda": [
        ("Civic",    "sedan",       "2.0L I4",           158, 187, 1320),
        ("Accord",   "sedan",       "1.5L Turbo I4",     192, 243, 1440),
        ("CR-V",     "suv",         "1.5L Turbo I4",     190, 243, 1540),
        ("Pilot",    "suv",         "3.5L V6",           280, 262, 1970),
        ("Fit",      "hatchback",   "1.5L I4",           130, 139, 1120),
        ("Odyssey",  "minivan",     "3.5L V6",           280, 262, 1990),
        ("HR-V",     "suv",         "1.8L I4",           141, 170, 1350),
        ("Ridgeline","truck",       "3.5L V6",           280, 262, 1990),
        ("Insight",  "sedan",       "1.5L I4 Hybrid",    151, 197, 1380),
        ("Passport", "suv",         "3.5L V6",           280, 262, 1920),
    ],
    "Stellantis": [
        ("Charger",  "sedan",       "5.7L HEMI V8",      370, 529, 1980),
        ("Challenger","sports_car", "6.4L HEMI V8",      485, 637, 1960),
        ("Durango",  "suv",         "5.7L HEMI V8",      360, 529, 2130),
        ("Jeep Wrangler","suv",     "3.6L V6",           285, 350, 1980),
        ("Grand Cherokee","suv",    "5.7L HEMI V8",      360, 529, 2130),
        ("Pacifica", "minivan",     "3.6L V6 Hybrid",    260, 285, 1990),
        ("Renegade", "suv",         "1.4L Turbo I4",     160, 250, 1480),
        ("Dodge Ram","truck",       "6.4L HEMI V8",      410, 590, 2500),
        ("Jeep Grand Cherokee L","suv","5.7L HEMI V8",  360, 529, 2400),
        ("Alfa Romeo Giulia","sedan","2.0L Turbo I4",    280, 400, 1640),
    ],
    "Hyundai": [
        ("Elantra",  "sedan",       "2.0L I4",           147, 132, 1340),
        ("Tucson",   "suv",         "2.5L I4",           187, 241, 1620),
        ("Santa Fe", "suv",         "2.5L Turbo I4",     277, 422, 1815),
        ("Sonata",   "sedan",       "2.5L I4",           191, 186, 1560),
        ("Kona",     "suv",         "2.0L I4",           147, 132, 1280),
        ("Palisade", "suv",         "3.8L V6",           291, 262, 2050),
        ("Ioniq 5",  "hatchback",   "Electric",          320, 605, 2000),
        ("Venue",    "suv",         "1.6L I4",           121, 138, 1170),
        ("Accent",   "sedan",       "1.6L I4",           120, 134, 1140),
        ("Santa Cruz","truck",      "2.5L I4",           191, 181, 1730),
    ],
    "BMW": [
        ("3 Series", "sedan",       "2.0L Turbo I4",     255, 400, 1530),
        ("X5",       "suv",         "3.0L Turbo I6",     375, 520, 2130),
        ("M3",       "sports_car",  "3.0L Twin-Turbo I6",473, 550, 1630),
        ("X3",       "suv",         "2.0L Turbo I4",     248, 400, 1800),
        ("5 Series", "sedan",       "3.0L Turbo I6",     335, 450, 1800),
        ("X7",       "suv",         "3.0L Turbo I6",     375, 520, 2400),
        ("M5",       "sports_car",  "4.4L Twin-Turbo V8",617, 750, 1900),
        ("iX",       "suv",         "Electric",          516, 765, 2500),
        ("Z4",       "sports_car",  "3.0L Turbo I6",     382, 500, 1530),
        ("4 Series", "coupe",       "2.0L Turbo I4",     255, 400, 1610),
    ],
    "Mercedes-Benz": [
        ("C-Class",  "sedan",       "2.0L Turbo I4",     255, 400, 1625),
        ("GLE",      "suv",         "3.0L Turbo I6",     375, 500, 2130),
        ("AMG GT",   "sports_car",  "4.0L Twin-Turbo V8",523, 650, 1645),
        ("E-Class",  "sedan",       "3.0L Turbo I6",     362, 500, 1840),
        ("GLC",      "suv",         "2.0L Turbo I4",     255, 400, 1800),
        ("S-Class",  "sedan",       "3.0L Turbo I6",     429, 520, 2050),
        ("GLS",      "suv",         "3.0L Turbo I6",     362, 500, 2450),
        ("CLA",      "coupe",       "2.0L Turbo I4",     221, 350, 1580),
        ("A-Class",  "hatchback",   "2.0L Turbo I4",     188, 300, 1420),
        ("G-Class",  "suv",         "4.0L Twin-Turbo V8",416, 610, 2400),
    ],
    "Audi": [
        ("A4",       "sedan",       "2.0L TSI",          201, 320, 1465),
        ("Q5",       "suv",         "2.0TFSI",           261, 370, 1805),
        ("R8",       "sports_car",  "5.2L V10",          562, 540, 1560),
        ("A6",       "sedan",       "3.0T TFSI",         335, 500, 1800),
        ("Q7",       "suv",         "3.0T TFSI",         335, 500, 2200),
        ("A3",       "hatchback",   "2.0T",              228, 350, 1400),
        ("e-tron",   "suv",         "Electric",          402, 664, 2350),
        ("TT",       "sports_car",  "2.0T",              228, 350, 1350),
        ("Q3",       "suv",         "2.0T",              228, 350, 1600),
        ("RS7",      "sports_car",  "4.0TFSI V8",        591, 800, 1850),
    ],
}

CITIES = [
    ("Toyota City",  "Japan",       "Asia/Tokyo",   158, "humid_subtropical"),
    ("Wolfsburg",    "Germany",     "Europe/Berlin", 204, "oceanic"),
    ("Dearborn",     "USA",         "America/New_York", 62, "humid_continental"),
    ("Detroit",      "USA",         "America/New_York", 361, "humid_continental"),
    ("Seoul",        "South Korea", "Asia/Seoul",   605, "humid_continental"),
    ("Munich",       "Germany",     "Europe/Berlin", 310, "oceanic"),
    ("Stuttgart",    "Germany",     "Europe/Berlin", 207, "oceanic"),
    ("Ingolstadt",   "Germany",     "Europe/Berlin", 42, "oceanic"),
    ("Chuo, Tokyo",  "Japan",       "Asia/Tokyo",   11, "humid_subtropical"),
    ("Rome",         "Italy",       "Europe/Rome",  1285, "mediterranean"),
]

OCCUPATIONS = [
    "Software Engineer", "Data Scientist", "Product Manager", "UX Designer",
    "Marketing Director", "Financial Analyst", "Mechanical Engineer",
    "Civil Engineer", "Doctor", "Nurse Practitioner", "Teacher",
    "Lawyer", "Accountant", "Architect", "Chef", "Electrician",
    "Plumber", "Construction Manager", "Sales Representative",
    "Business Consultant", "Project Manager", "Graphic Designer",
    "Content Writer", "Journalist", "Photographer", "Film Director",
    "Music Producer", "Athlete", "Personal Trainer", "Veterinarian",
]

HOBBIES = [
    ["cycling", "hiking"],
    ["photography", "traveling"],
    ["gaming", "coding"],
    ["reading", "cooking"],
    ["yoga", "meditation"],
    ["fishing", "camping"],
    ["painting", "drawing"],
    ["gardening", "bird watching"],
    ["rock climbing", "trail running"],
    ["knitting", "sewing"],
    ["playing guitar", "singing"],
    ["woodworking", "DIY projects"],
    ["skiing", "snowboarding"],
    ["surfing", "swimming"],
    ["birdwatching", "nature photography"],
    ["model building", "board games"],
]

GENDERS = ["M", "F", "Non-binary"]
INCOME_BRACKETS = ["low", "middle", "upper_middle", "high"]


# ── Deterministic graph generation ───────────────────────────────────────────
def generate_graph():
    """Build the deterministic car-ecosystem graph. Returns (G, node_keys)."""
    rng = random.Random(SEED)

    # Remove stale DB to avoid mixing old data
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    engine = create_engine(f"sqlite:///{DB_PATH}")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    with Session() as session:
        G = nx_sql.DiGraph(session, name="example5_car_ecosystem")

        # ── Node generation ───────────────────────────────────────────────
        # 10 CarManufacturers
        manufacturer_keys = []
        for i, name in enumerate(COMPANY_NAMES):
            data = COMPANY_DATA[i]
            attrs = {
                "entity_type": "CarManufacturer",
                "name": name,
                "headquarters": data["headquarters"],
                "country": data["country"],
                "timezone": {"Japan": "Asia/Tokyo", "Germany": "Europe/Berlin",
                             "USA": "America/New_York", "South Korea": "Asia/Seoul",
                             "Italy": "Europe/Rome"}.get(data["country"], "UTC"),
                "founded_year": data["founded_year"],
                "employee_count": data["employee_count"],
            }
            key = f"CarManufacturer_{i}"
            G.add_node(key, **attrs)
            manufacturer_keys.append(key)

        # 100 CarModels (10 per manufacturer)
        car_model_keys = []
        for mi, name in enumerate(COMPANY_NAMES):
            templates = CAR_TEMPLATES[name]
            for ci, tmpl in enumerate(templates):
                key = f"CarModel_{mi}_{ci}"
                attrs = {
                    "entity_type": "CarModel",
                    "name": tmpl[0],
                    "type": tmpl[1],
                    "engine": tmpl[2],
                    "horsepower": tmpl[3],
                    "torque": tmpl[4],
                    "weight_kg": tmpl[5],
                    "manufacturer": name,
                }
                G.add_node(key, **attrs)
                car_model_keys.append(key)

        # 100 OwnerProfiles
        owner_keys = []
        for i in range(100):
            city_idx = i % len(CITIES)
            city = CITIES[city_idx]
            # Pick a different work city (live and work in two different cities)
            work_city_idx = (city_idx + 1) % len(CITIES)
            work_city = CITIES[work_city_idx]
            attrs = {
                "entity_type": "OwnerProfile",
                "age": rng.randint(19, 80),
                "gender": GENDERS[i % len(GENDERS)],
                "occupation": OCCUPATIONS[i % len(OCCUPATIONS)],
                "income_bracket": INCOME_BRACKETS[i % len(INCOME_BRACKETS)],
                "hobbies": HOBBIES[i % len(HOBBIES)] + (rng.sample(
                    ["running", "surfing", "chess", "skiing", "fishing",
                     "painting", "cycling"], min(rng.randint(0, 3), 5 - len(HOBBIES[i % len(HOBBIES)])))
                    if rng.random() > 0.5 else []),
                "city": city[0],
                "country": city[1],
                "work_city": work_city[0],
                "work_country": work_city[1],
            }
            key = f"OwnerProfile_{i}"
            G.add_node(key, **attrs)
            owner_keys.append(key)

        # 10 Cities
        city_keys = []
        for i, city in enumerate(CITIES):
            attrs = {
                "entity_type": "City",
                "name": city[0],
                "country": city[1],
                "timezone": city[2],
                "area_km2": city[3],
                "climate": city[4],
                "population": rng.randint(10000, 15000000),
            }
            key = f"City_{i}"
            G.add_node(key, **attrs)
            city_keys.append(key)

        # ── Edge generation ───────────────────────────────────────────────

        # headquarters: CarManufacturer → City
        for mi, mk in enumerate(manufacturer_keys):
            hq = COMPANY_DATA[mi]["headquarters"]
            for ci, ck in enumerate(city_keys):
                if G.nodes[ck].get("name") == hq:
                    G.add_edge(mk, ck, edge_type="headquarters")
                    break

        # produces: CarManufacturer → CarModel (10 per manufacturer)
        for mi in range(len(COMPANY_NAMES)):
            start = mi * 10
            for ci in range(10):
                G.add_edge(manufacturer_keys[mi], car_model_keys[start + ci],
                           edge_type="produces")

        # owns: OwnerProfile → CarModel (each owner owns 1-3 cars)
        for oi, ok in enumerate(owner_keys):
            num_cars = rng.randint(1, 3)
            for c in range(num_cars):
                car_idx = (oi * 7 + c * 13) % len(car_model_keys)
                G.add_edge(ok, car_model_keys[car_idx], edge_type="owns")

        # sold_in: CarModel → City (each car sold in 3 cities)
        for cm_idx in range(len(car_model_keys)):
            sold_cities = rng.sample(city_keys, min(3, len(city_keys)))
            for ck in sold_cities:
                G.add_edge(car_model_keys[cm_idx], ck, edge_type="sold_in")

        # resides_in: OwnerProfile → City (home)
        for oi, ok in enumerate(owner_keys):
            city_idx = oi % len(city_keys)
            G.add_edge(ok, city_keys[city_idx], edge_type="resides_in")

        # works_in: OwnerProfile → City (work, different from home)
        for oi, ok in enumerate(owner_keys):
            work_city_idx = (oi + 1) % len(city_keys)
            G.add_edge(ok, city_keys[work_city_idx], edge_type="works_in")

        # competes_with: CarModel ↔ CarModel (same type, similar HP)
        car_types = {}
        for idx in range(len(car_model_keys)):
            ctype = G.nodes[car_model_keys[idx]].get("type", "unknown")
            car_types.setdefault(ctype, []).append(idx)

        for ctype, indices in car_types.items():
            sorted_idx = sorted(indices,
                                key=lambda i: G.nodes[car_model_keys[i]]["horsepower"])
            for pos, idx in enumerate(sorted_idx):
                candidates = []
                for offset in [1, 2, 3]:
                    if pos + offset < len(sorted_idx):
                        candidates.append(sorted_idx[pos + offset])
                    if pos - offset >= 0:
                        candidates.insert(0, sorted_idx[pos - offset])
                for cand in candidates[:3]:
                    G.add_edge(car_model_keys[idx], car_model_keys[cand],
                               edge_type="competes_with")

        # neighboring_country: City ↔ City (same country)
        cities_by_country = {}
        for ci in range(len(city_keys)):
            country = G.nodes[city_keys[ci]].get("country", "")
            cities_by_country.setdefault(country, []).append(ci)

        for country, indices in cities_by_country.items():
            sorted_idx = sorted(indices,
                                key=lambda i: G.nodes[city_keys[i]]["population"])
            for pos, ci in enumerate(sorted_idx):
                candidates = []
                for offset in [1, 2, 3]:
                    if pos + offset < len(sorted_idx):
                        candidates.append(sorted_idx[pos + offset])
                    if pos - offset >= 0:
                        candidates.insert(0, sorted_idx[pos - offset])
                for cand in candidates[:3]:
                    G.add_edge(city_keys[ci], city_keys[cand],
                               edge_type="neighboring_country")

        # same_hq: CarManufacturer ↔ CarManufacturer (same city)
        hq_cities = {}
        for mi in range(len(manufacturer_keys)):
            hq = COMPANY_DATA[mi]["headquarters"]
            hq_cities.setdefault(hq, []).append(mi)

        for city, indices in hq_cities.items():
            if len(indices) < 2:
                continue
            for i in range(len(indices)):
                for j in range(i + 1, len(indices)):
                    G.add_edge(manufacturer_keys[indices[i]],
                               manufacturer_keys[indices[j]],
                               edge_type="same_hq")

        session.commit()

    return G


# ── Community detection ──────────────────────────────────────────────────────
def detect_communities(G):
    """Run Louvain on the undirected version for community assignment."""
    U = G.to_undirected()
    partition = community_louvain.best_partition(U, random_state=SEED)
    return partition


# ── Layout: force-directed per community cluster ─────────────────────────────
def compute_layout(G, partition):
    """Compute a force-directed layout with community-aware initial positions."""
    U = G.to_undirected()
    node_ids = list(G.nodes())
    communities = sorted(set(partition.values()))
    n_communities = len(communities)

    radius = max(len(node_ids), 100) ** 0.5 * 1.5
    rng = random.Random(SEED + 1)
    comm_centers = {}
    for i, c in enumerate(communities):
        angle = 2 * 3.14159 * i / n_communities
        cx = radius * 0.7 * (0.5 + 0.5 * rng.random()) * (1 if rng.random() > 0.5 else -1)
        cy = radius * 0.7 * (0.5 + 0.5 * rng.random()) * (1 if rng.random() > 0.5 else -1)
        comm_centers[c] = (cx, cy)

    pos_init = {}
    for node in node_ids:
        c = partition[node]
        cx, cy = comm_centers[c]
        pos_init[node] = [cx + rng.gauss(0, radius * 0.15),
                          cy + rng.gauss(0, radius * 0.15)]

    pos = nx.spring_layout(
        U,
        pos=pos_init,
        iterations=300,
        k=5.0,
        seed=SEED,
    )

    return pos


# ── Plotting ─────────────────────────────────────────────────────────────────
def plot_graph(G, partition, pos):
    """Create a publication-quality clustered, color-coded graph visualization."""
    fig, ax = plt.subplots(figsize=(24, 18), dpi=150)
    fig.patch.set_facecolor("#FAFAFA")
    ax.set_facecolor("#FFFFFF")

    node_ids = list(G.nodes())
    num_nodes = len(node_ids)

    degrees = dict(G.degree())

    comm_sizes = {}
    for c in partition.values():
        comm_sizes[c] = comm_sizes.get(c, 0) + 1
    max_comm_size = max(comm_sizes.values()) if comm_sizes else 1

    # ── Edges by type ───────────────────────────────────────────────────
    edge_groups = {}
    for u, v, data in G.edges(data=True):
        etype = data.get("edge_type", "unknown")
        edge_groups.setdefault(etype, []).append((u, v))

    edge_order = ["same_hq", "neighboring_country",
                  "competes_with",
                  "sold_in", "resides_in", "works_in",
                  "headquarters", "produces", "owns"]

    for etype in edge_order:
        edges = edge_groups.get(etype, [])
        if not edges:
            continue
        color, alpha, width = EDGE_STYLES.get(etype, ("#999999", 0.15, 0.5))

        xs = [pos[u][0] for u, v in edges]
        ys = [pos[u][1] for u, v in edges]
        ax.plot(xs, ys, color=color, alpha=alpha, linewidth=width,
                zorder=1, solid_capstyle="round")

    # ── Type-cluster boundary ellipses ──────────────────────────────────
    for etype, color in TYPE_COLORS.items():
        mask = [i for i, n in enumerate(node_ids)
                if G.nodes[n].get("entity_type") == etype]
        if len(mask) < 3:
            continue
        pts = np.array([[pos[node_ids[i]][0], pos[node_ids[i]][1]] for i in mask])
        mean = pts.mean(axis=0)
        cov = np.cov(pts.T)
        eigenvals, eigenvecs = np.linalg.eigh(cov)
        angle = np.degrees(np.arctan2(eigenvecs[1, -1], eigenvecs[0, -1]))
        width = 4 * np.sqrt(max(eigenvals[-1], 0.01))
        height = 4 * np.sqrt(max(eigenvals[-2] if len(eigenvals) > 1 else eigenvals[-1], 0.01))
        ellipse = mpatches.Ellipse(
            mean, width=width, height=height, angle=angle,
            facecolor="none", edgecolor=color, linewidth=1.5,
            linestyle="--", alpha=0.5, zorder=2, capstyle="round",
        )
        ax.add_patch(ellipse)

    # ── Louvain community ellipses for largest communities ──────────────
    top_communities = sorted(comm_sizes.items(), key=lambda x: -x[1])[:8]
    comm_colors = plt.cm.Set3(np.linspace(0, 1, len(top_communities)))
    for (comm_id, size), cc in zip(top_communities, comm_colors):
        mask = [i for i, n in enumerate(node_ids) if partition[n] == comm_id]
        if len(mask) < 3:
            continue
        pts = np.array([[pos[node_ids[i]][0], pos[node_ids[i]][1]] for i in mask])
        mean = pts.mean(axis=0)
        cov = np.cov(pts.T)
        eigenvals, eigenvecs = np.linalg.eigh(cov)
        angle = np.degrees(np.arctan2(eigenvecs[1, -1], eigenvecs[0, -1]))
        width = 4 * np.sqrt(max(eigenvals[-1], 0.01))
        height = 4 * np.sqrt(max(eigenvals[-2] if len(eigenvals) > 1 else eigenvals[-1], 0.01))
        ellipse = mpatches.Ellipse(
            mean, width=width, height=height, angle=angle,
            facecolor="none", edgecolor=cc, linewidth=0.8,
            linestyle="-.", alpha=0.35, zorder=2, capstyle="round",
        )
        ax.add_patch(ellipse)

    # ── Draw nodes by type ──────────────────────────────────────────────
    for etype in TYPE_COLORS:
        mask = [i for i, n in enumerate(node_ids)
                if G.nodes[n].get("entity_type") == etype]
        if not mask:
            continue

        xs = [pos[node_ids[i]][0] for i in mask]
        ys = [pos[node_ids[i]][1] for i in mask]
        base_size = 40
        ax.scatter(xs, ys, s=base_size, c=TYPE_COLORS[etype],
                   alpha=0.65, edgecolors="white", linewidth=0.3,
                   zorder=3, rasterized=True)

    # ── Legend ──────────────────────────────────────────────────────────
    type_patches = [
        mpatches.Patch(color=c, label=f"{t} ({sum(1 for n in node_ids if G.nodes[n].get('entity_type') == t)})")
        for t, c in TYPE_COLORS.items()
    ]

    edge_patches = []
    for etype, (color, _, _) in EDGE_STYLES.items():
        count = len(edge_groups.get(etype, []))
        if count > 0:
            edge_patches.append(mpatches.Patch(color=color, label=f"{etype}: {count}",
                                               alpha=0.8, fill=False, linewidth=2))

    ax.legend(handles=type_patches + edge_patches,
              loc="upper right", fontsize=9, framealpha=0.9,
              borderpad=0.8, columnspacing=1.5, labelspacing=0.4)

    # ── Title & styling ─────────────────────────────────────────────────
    ax.set_title(
        f"Car Ecosystem Graph  •  {num_nodes} nodes  •  {G.number_of_edges()} edges  •  "
        f"{len(set(partition.values()))} communities",
        fontsize=16, fontweight="bold", pad=20
    )

    ax.set_xlabel("x (community-aware layout)", fontsize=11, labelpad=10)
    ax.set_ylabel("y (community-aware layout)", fontsize=11, labelpad=10)

    ax.set_xticks([])
    ax.set_yticks([])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.spines["left"].set_visible(False)

    plt.tight_layout(pad=1.5)
    return fig


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    print("Generating graph...")
    G = generate_graph()
    print(f"  Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")

    # Print node counts by type
    for etype in ["CarManufacturer", "CarModel", "OwnerProfile", "City"]:
        count = sum(1 for n, d in G.nodes(data=True) if d.get("entity_type") == etype)
        print(f"  {etype}: {count}")

    # Print edge counts by type
    edge_types = {}
    for u, v, data in G.edges(data=True):
        etype = data.get("edge_type", "unknown")
        edge_types[etype] = edge_types.get(etype, 0) + 1
    print(f"\nEdge breakdown:")
    for etype, count in sorted(edge_types.items()):
        print(f"  {etype}: {count}")

    print("\nDetecting communities (Louvain)...")
    partition = detect_communities(G)
    n_communities = len(set(partition.values()))
    print(f"  Found {n_communities} communities")

    print("Computing layout...")
    pos = compute_layout(G, partition)

    print("Plotting...")
    fig = plot_graph(G, partition, pos)

    fig.savefig(OUTPUT_PNG, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved → {OUTPUT_PNG}")
    print("Done.")


if __name__ == "__main__":
    main()
