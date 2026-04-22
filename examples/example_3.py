"""
Example 3 – generate a car-ecosystem graph and visualise it.

Deterministic graph generation (SEED=23) with exactly:
  - 10 CarManufacturer nodes
  - 100 CarModel nodes (10 per manufacturer)
  - 100 OwnerProfile nodes
  - 10 City nodes

Edges (4 types only):
  - produces   : CarManufacturer → CarModel (10 per manufacturer)
  - owns       : OwnerProfile → CarModel (1-2 per owner)
  - resides_in : OwnerProfile → City (home city)
  - works_in   : OwnerProfile → City (can be same or different from home)

No community detection – pure force-directed layout.

Output: example_3_graph.png (deterministic every run).
"""

import os
import random
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

import networkx as nx

import nx_sql
from nx_sql.models import Base

SEED = 23

_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(_DIR, "..", "example_3.db")
OUTPUT_PNG = os.path.join(_DIR, "example_3_graph.png")

EDGE_STYLES = {
    "produces":  ("#10B981", 0.35, 1.2),
    "owns":      ("#F59E0B", 0.40, 1.5),
    "resides_in":("#A78BFA", 0.15, 0.6),
    "works_in":  ("#EC4899", 0.15, 0.6),
}

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

def main() -> None:
    random.seed(SEED)
    np.random.seed(SEED)

    # --- DB setup -----------------------------------------------------------
    engine = create_engine(f"sqlite:///{DB_PATH}")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    with Session() as session:
        # Create nx_sql graph
        G = nx_sql.Graph(session=session, name="car_ecosystem")

        # --- Create nodes -----------------------------------------------------
        # CarManufacturer nodes (by company name)
        manufacturers: dict[str, str] = {}  # name -> node_key
        for name, data in zip(COMPANY_NAMES, COMPANY_DATA):
            G.add_node(name, label=name, type="manufacturer", **data)
            manufacturers[name] = name

        # CarModel nodes (name as key, with attributes from templates)
        car_models: dict[str, str] = {}  # node_key -> manufacturer_name
        for mfr_name in COMPANY_NAMES:
            for template in CAR_TEMPLATES[mfr_name]:
                model_name, body_type, engine_type, hp, torque, weight = template
                node_key = f"{mfr_name} {model_name}"
                G.add_node(
                    node_key,
                    label=model_name,
                    type="car_model",
                    manufacturer=mfr_name,
                    body_type=body_type,
                    engine_type=engine_type,
                    hp=hp,
                    torque=torque,
                    weight_kg=weight,
                )
                car_models[node_key] = mfr_name

        # City nodes
        cities: dict[str, str] = {}  # name -> node_key
        for city_data in CITIES:
            city_name = city_data[0]
            G.add_node(
                city_name,
                label=city_name,
                type="city",
                country=city_data[1],
                timezone=city_data[2],
                population=city_data[3],
                climate=city_data[4],
            )
            cities[city_name] = city_name

        # OwnerProfile nodes
        owners: list[str] = []  # node keys in order
        for i in range(100):
            owner_key = f"Owner_{i:03d}"
            home_city = random.choice(CITIES)[0]
            work_city = random.choice(CITIES)[0]
            occupation = random.choice(OCCUPATIONS)
            G.add_node(
                owner_key,
                label=owner_key,
                type="owner",
                occupation=occupation,
                home_city=home_city,
                work_city=work_city,
            )
            owners.append(owner_key)

        # --- Create edges -----------------------------------------------------
        # produces: CarManufacturer → CarModel (10 per manufacturer)
        for mfr_name in COMPANY_NAMES:
            for template in CAR_TEMPLATES[mfr_name]:
                model_name = template[0]
                node_key = f"{mfr_name} {model_name}"
                G.add_edge(
                    mfr_name,
                    node_key,
                    edge_type="produces",
                )

        # resides_in + works_in: OwnerProfile → City
        for owner_key in owners:
            owner_attrs = G._node[owner_key]
            home_city = owner_attrs.get("home_city", "Toyota City")
            work_city = owner_attrs.get("work_city", "Toyota City")
            G.add_edge(
                owner_key,
                home_city,
                edge_type="resides_in",
            )
            G.add_edge(
                owner_key,
                work_city,
                edge_type="works_in",
            )

        # owns: OwnerProfile → CarModel (1-2 per owner)
        all_model_keys = list(car_models.keys())
        for owner_key in owners:
            n_cars = random.randint(1, 2)
            chosen = random.sample(all_model_keys, min(n_cars, len(all_model_keys)))
            for model_key in chosen:
                G.add_edge(
                    owner_key,
                    model_key,
                    edge_type="owns",
                )

        session.commit()

    # --- Visualise ----------------------------------------------------------
    pos = nx.spring_layout(G, seed=SEED, k=0.5, iterations=50)

    fig, ax = plt.subplots(figsize=(24, 18))

    # Colour map by node type
    type_colors = {
        "manufacturer": "#10B981",
        "car_model": "#3B82F6",
        "owner": "#F59E0B",
        "city": "#EC4899",
    }

    node_types = {
        n: G.nodes[n].get("type", "unknown") for n in G.nodes
    }

    # Draw edges by type
    for edge_type, (color, alpha, width) in EDGE_STYLES.items():
        edges_by_type = [
            (u, v) for u, v, d in G.edges(data=True)
            if d.get("edge_type") == edge_type
        ]
        if edges_by_type:
            nx.draw_networkx_edges(
                G, pos,
                edgelist=edges_by_type,
                edge_color=color,
                alpha=alpha,
                width=width,
                style="dashed",
                ax=ax,
            )

    # Draw nodes grouped by type
    for ntype, color in type_colors.items():
        nodes_of_type = [n for n, t in node_types.items() if t == ntype]
        if nodes_of_type:
            nx.draw_networkx_nodes(
                G, pos,
                nodelist=nodes_of_type,
                node_color=color,
                node_size=120 if ntype == "car_model" else 300,
                alpha=0.85,
                ax=ax,
            )

    # Labels: only manufacturers and cities (too many cars/owners to label)
    label_nodes = [
        n for n, t in node_types.items()
        if t in ("manufacturer", "city")
    ]
    nx.draw_networkx_labels(
        G, pos,
        labels={n: G.nodes[n].get("label", n) for n in label_nodes},
        font_size=8,
        font_weight="bold",
        ax=ax,
    )

    # Legend
    legend_handles = []

    # Node type legend entries
    for ntype, color in type_colors.items():
        legend_handles.append(
            mpatches.Patch(color=color, label=ntype.replace("_", " ").title())
        )

    # Edge type legend entries (dashed lines)
    for edge_type, (color, alpha, width) in EDGE_STYLES.items():
        legend_handles.append(
            plt.Line2D(
                [], [],
                color=color,
                linestyle="--",
                linewidth=width,
                label=edge_type.replace("_", " ").title(),
            )
        )

    ax.legend(handles=legend_handles, loc="upper right", fontsize=10, framealpha=0.9)

    ax.set_axis_off()
    ax.set_title(
        "Car Ecosystem Graph\n"
        f"10 manufacturers · 100 car models · 100 owners · 10 cities",
        fontsize=16,
        fontweight="bold",
        pad=20,
    )

    fig.savefig(OUTPUT_PNG, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Graph saved → {OUTPUT_PNG}")
    print(
        f"  Nodes: {G.number_of_nodes()}  "
        f"Edges: {G.number_of_edges()}"
    )

if __name__ == "__main__":
    main()
