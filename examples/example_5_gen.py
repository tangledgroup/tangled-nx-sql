"""Generate example_5.db – a car-ecosystem graph with clustered, color-coded nodes.

Entity types: CarManufacturer, CarModel, OwnerProfile, City
Edge types: headquarters, produces, owns, sold_in, resides_in, competes_with,
            shares_hobby, neighboring_country, same_hq

Creates ~1000 nodes and ~3000 edges with deterministic randomness (SEED=42).
"""

import random
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

SEED = 42
rng = random.Random(SEED)

engine = create_engine("sqlite:///example_5.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


# ── Data pools ───────────────────────────────────────────────────────────────
COMPANIES = [
    "Toyota", "Volkswagen", "Ford", "General Motors", "Honda",
    "Stellantis", "Hyundai", "BMW", "Mercedes-Benz", "Audi",
    "Nissan", "Mazda", "Subaru", "Tesla", "Porsche",
    "Ferrari", "Lamborghini", "McLaren", "Bentley", "Rolls-Royce",
    "Jaguar", "Land Rover", "Volvo", "Kia", "Suzuki",
    "Mitsubishi", "Chevrolet", "Cadillac", "Lexus", "Infiniti",
    "Acura", "Alfa Romeo", "Fiat", "Jeep", "Dodge",
    "Ram", "Mini", "Smart", "Maserati", "Aston Martin",
]

HQ_CITIES = [
    ("Tokyo", "Japan", "Asia/Tokyo", 1596, "humid_subtropical"),
    ("Wolfsburg", "Germany", "Europe/Berlin", 204, "oceanic"),
    ("Dearborn", "USA", "America/New_York", 62, "humid_continental"),
    ("Detroit", "USA", "America/New_York", 361, "humid_continental"),
    ("Toyota City", "Japan", "Asia/Tokyo", 158, "humid_subtropical"),
    ("Munich", "Germany", "Europe/Berlin", 310, "oceanic"),
    ("Stuttgart", "Germany", "Europe/Berlin", 207, "oceanic"),
    ("Seoul", "South Korea", "Asia/Seoul", 605, "humid_continental"),
    ("Ulsan", "South Korea", "Asia/Seoul", 836, "humid_continental"),
    ("London", "UK", "Europe/London", 1572, "oceanic"),
    ("Los Angeles", "USA", "America/Los_Angeles", 1302, "mediterranean"),
    ("Nagoya", "Japan", "Asia/Tokyo", 329, "humid_subtropical"),
    ("Milan", "Italy", "Europe/Rome", 181, "humid_subtropical"),
    ("Turin", "Italy", "Europe/Rome", 130, "humid_subtropical"),
    ("Maranello", "Italy", "Europe/Rome", 36, "humid_subtropical"),
    ("Sant'Agata Bolognese", "Italy", "Europe/Rome", 24, "humid_subtropical"),
    ("Woking", "UK", "Europe/London", 29, "oceanic"),
    ("Crewe", "UK", "Europe/London", 60, "oceanic"),
    ("Goodwood", "UK", "Europe/London", 12, "oceanic"),
    ("Roveredo", "Switzerland", "Europe/Zurich", 5, "continental"),
]

ALL_CITIES = [
    ("Tokyo", "Japan"), ("Osaka", "Japan"), ("Nagoya", "Japan"),
    ("Wolfsburg", "Germany"), ("Munich", "Germany"), ("Stuttgart", "Germany"),
    ("Berlin", "Germany"), ("Frankfurt", "Germany"),
    ("Detroit", "USA"), ("Dearborn", "USA"), ("Los Angeles", "USA"),
    ("New York", "USA"), ("Chicago", "USA"), ("San Francisco", "USA"),
    ("Seoul", "South Korea"), ("Ulsan", "South Korea"),
    ("London", "UK"), ("Manchester", "UK"),
    ("Roveredo", "Switzerland"),
    ("Milan", "Italy"), ("Turin", "Italy"), ("Rome", "Italy"),
    ("Paris", "France"), ("Lyon", "France"),
    ("Beijing", "China"), ("Shanghai", "China"),
    ("Mumbai", "India"), ("Delhi", "India"),
]

COUNTRIES = ["Japan", "Germany", "USA", "South Korea", "UK", "Switzerland",
             "Italy", "France", "China", "India"]

HOBBIES = ["cycling", "hiking", "photography", "cooking", "gardening",
           "reading", "swimming", "running", "yoga", "chess",
           "fishing", "camping", "skiing", "surfing", "painting"]

MODELS_PER_COMPANY = {
    "Toyota": ["Corolla", "Camry", "RAV4", "Highlander", "Yaris"],
    "Volkswagen": ["Golf", "Passat", "Tiguan", "Polo", "ID.4"],
    "Ford": ["F-150", "Mustang", "Bronco", "Explorer", "Escape"],
    "General Motors": ["Silverado", "Equinox", "Malibu", "Camaro", "Blazer"],
    "Honda": ["Civic", "Accord", "CR-V", "Pilot", "Fit"],
    "Hyundai": ["Elantra", "Tucson", "Santa Fe", "Sonata", "Kona"],
    "BMW": ["3 Series", "5 Series", "X3", "X5", "i4"],
    "Mercedes-Benz": ["C-Class", "E-Class", "GLC", "GLE", "EQS"],
    "Tesla": ["Model 3", "Model Y", "Model S", "Model X", "Cybertruck"],
    "Nissan": ["Altima", "Rogue", "Maxima", "Sentra", "Leaf"],
    "Kia": ["Forte", "Sportage", "Sorento", "Telluride", "EV6"],
    "Mazda": ["Mazda3", "CX-5", "CX-9", "Mazda6", "MX-5"],
    "Subaru": ["Outback", "Forester", "Crosstrek", "Impreza", "Legacy"],
    "Porsche": ["911", "Cayenne", "Macan", "Taycan", "Panamera"],
    "Ferrari": ["Roma", "F8 Tributo", "SF90", "296 GTB", "Portofino"],
    "Lamborghini": ["Huracán", "Urus", "Aventador", "Revuelto", "Countach"],
    "McLaren": ["GT", "720S", "Artura", "570S", "P1"],
    "Audi": ["A4", "A6", "Q5", "Q7", "e-tron"],
    "Volvo": ["XC60", "XC90", "S60", "S90", "C40"],
    "Jaguar": ["F-PACE", "E-PACE", "XE", "XF", "F-TYPE"],
}

# ── Build graph ──────────────────────────────────────────────────────────────
with Session() as session:
    G = nx_sql.DiGraph(session, name="example5_random_nodes")

    # 1. Create CarManufacturer nodes
    companies = []
    for name in COMPANIES:
        hq_city, country, tz, area, climate = rng.choice(HQ_CITIES)
        G.add_node(
            name,
            entity_type="CarManufacturer",
            headquarters=hq_city,
            country=country,
            timezone=tz,
            founded_year=rng.randint(1900, 1975),
            employee_count=rng.randint(5000, 200000),
        )
        companies.append(name)

    # 2. Create City nodes
    for city_name, country in ALL_CITIES:
        G.add_node(
            city_name,
            entity_type="City",
            country=country,
            population=rng.randint(50000, 15000000),
            area_km2=rng.randint(10, 2000),
        )

    # 3. Create CarModel nodes and produces edges
    for comp in companies:
        models = MODELS_PER_COMPANY.get(comp, [])
        if not models:
            continue
        for model_name in models:
            G.add_node(
                f"{comp} {model_name}",
                entity_type="CarModel",
                manufacturer=comp,
                body_type=rng.choice(["sedan", "suv", "hatchback", "sports_car", "truck"]),
                engine=rng.choice(["1.5L I4", "2.0L I4 Turbo", "2.5L V6", "3.0L V8",
                                   "Electric", "Hybrid"]),
                horsepower=rng.randint(100, 700),
                weight_kg=rng.randint(1200, 2500),
            )
            G.add_edge(comp, f"{comp} {model_name}", edge_type="produces")

    # 4. Create OwnerProfile nodes
    NUM_OWNERS = 600
    first_names = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace",
                   "Henry", "Ivy", "Jack", "Karen", "Leo", "Mia", "Noah",
                   "Olivia", "Paul", "Quinn", "Rosa", "Sam", "Tina"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia",
                  "Miller", "Davis", "Rodriguez", "Martinez", "Lee", "Kim",
                  "Patel", "Chen", "Singh", "Mueller", "Tanaka", "Silva"]

    for i in range(NUM_OWNERS):
        fname = rng.choice(first_names)
        lname = rng.choice(last_names)
        owner_name = f"{fname} {lname}_{i}"
        city, country = rng.choice(ALL_CITIES)
        G.add_node(
            owner_name,
            entity_type="OwnerProfile",
            age=rng.randint(18, 80),
            gender=rng.choice(["M", "F", "Non-binary"]),
            occupation=rng.choice(["Engineer", "Teacher", "Doctor", "Artist",
                                   "Manager", "Student", "Retired", "Entrepreneur"]),
            income_bracket=rng.choice(["low", "middle", "upper_middle", "high"]),
            hobbies=rng.sample(HOBBIES, k=rng.randint(1, 4)),
            city=city,
            country=country,
        )

    # 5. owns edges: each owner owns 1-2 cars
    all_car_models = [n for n in G.nodes() if G.nodes[n].get("entity_type") == "CarModel"]
    for node in G.nodes():
        if G.nodes[node].get("entity_type") != "OwnerProfile":
            continue
        num_owns = rng.randint(1, 2)
        owned = rng.sample(all_car_models, min(num_owns, len(all_car_models)))
        for car in owned:
            G.add_edge(node, car, edge_type="owns", year_owned=rng.randint(2015, 2025))

    # 6. sold_in edges: manufacturers sell in multiple cities
    for comp in companies:
        num_cities = rng.randint(3, 8)
        target_cities = rng.sample(ALL_CITIES, min(num_cities, len(ALL_CITIES)))
        for city, _ in target_cities:
            G.add_edge(comp, city, edge_type="sold_in")

    # 7. headquarters edges
    for comp in companies:
        hq_city = G.nodes[comp].get("headquarters", "")
        if hq_city:
            G.add_edge(comp, hq_city, edge_type="headquarters")

    # 8. resides_in edges: owners reside in their city
    for node in G.nodes():
        if G.nodes[node].get("entity_type") == "OwnerProfile":
            city = G.nodes[node].get("city", "")
            if city:
                G.add_edge(node, city, edge_type="resides_in")

    # 9. competes_with edges between manufacturers in same country
    for i, c1 in enumerate(companies):
        for c2 in companies[i+1:]:
            if (G.nodes[c1].get("country") == G.nodes[c2].get("country") and
                    rng.random() < 0.3):
                G.add_edge(c1, c2, edge_type="competes_with")

    # 10. shares_hobby edges between owners with common hobbies
    owners = [n for n in G.nodes() if G.nodes[n].get("entity_type") == "OwnerProfile"]
    for _ in range(200):
        o1, o2 = rng.sample(owners, 2)
        h1, h2 = set(G.nodes[o1].get("hobbies", [])), set(G.nodes[o2].get("hobbies", []))
        if h1 & h2:
            G.add_edge(o1, o2, edge_type="shares_hobby", shared_hobbies=list(h1 & h2))

    # 11. neighboring_country edges
    country_list = list(set(G.nodes[n].get("country", "") for n in G.nodes() if G.nodes[n].get("entity_type") == "City"))
    country_list = [c for c in country_list if c]
    for _ in range(30):
        c1, c2 = rng.sample(country_list, 2)
        if c1 != c2:
            G.add_edge(c1, c2, edge_type="neighboring_country")

    # 12. same_hq edges: manufacturers with same HQ city
    hq_groups = {}
    for comp in companies:
        hq = G.nodes[comp].get("headquarters", "")
        if hq:
            hq_groups.setdefault(hq, []).append(comp)
    for hq, members in hq_groups.items():
        if len(members) > 1:
            for i, m1 in enumerate(members):
                for m2 in members[i+1:]:
                    G.add_edge(m1, m2, edge_type="same_hq")

    session.commit()
    print(f"Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")
    print("Saved to example_5.db")
