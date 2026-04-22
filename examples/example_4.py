"""Example 4 – generate 1000 random nodes across 4 entity types with rich attributes
and deterministic analytical edges.

Entity types:
  - CarManufacturer (company bio, founded year, headquarters city, country)
  - CarModel (name, type, engine, horsepower, torque, weight, fuel_economy)
  - OwnerProfile (age, gender, occupation, income_bracket, hobbies)
  - City (population, country, timezone, area_km2, climate)

All randomness is driven by a single seeded RNG (SEED=42).
Every run produces the identical graph: same nodes, same attributes, same edges.
"""

import random
import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base

SEED = 42


engine = create_engine("sqlite:///example_4.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


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

CITIES = [
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

CARS = [
    ("Corolla", "sedan", "1.8L I4 Hybrid", 139, 139, 1370, 27.0),
    ("Camry", "sedan", "2.5L I4", 203, 184, 1590, 19.6),
    ("RAV4", "suv", "2.5L I4 Hybrid", 219, 163, 1700, 23.4),
    ("Golf", "hatchback", "1.4L TSI", 150, 250, 1330, 18.1),
    ("Passat", "sedan", "2.0L TDI", 150, 360, 1470, 19.6),
    ("Tiguan", "suv", "2.0L TSI", 184, 320, 1655, 16.8),
    ("F-150", "truck", "3.5L V6 EcoBoost", 400, 583, 2100, 12.4),
    ("Mustang", "sports_car", "5.0L V8", 450, 529, 1723, 11.2),
    ("Bronco", "suv", "2.7L V6 EcoBoost", 330, 563, 1960, 11.2),
    ("Civic", "sedan", "2.0L I4", 158, 187, 1320, 19.6),
    ("Accord", "sedan", "1.5L Turbo I4", 192, 243, 1440, 18.1),
    ("CR-V", "suv", "1.5L Turbo I4", 190, 243, 1540, 17.3),
    ("Elantra", "sedan", "2.0L I4", 147, 132, 1340, 16.8),
    ("Tucson", "suv", "2.5L I4", 187, 241, 1620, 14.7),
    ("Santa Fe", "suv", "2.5L Turbo I4", 277, 422, 1815, 12.4),
    ("3 Series", "sedan", "2.0L Turbo I4", 255, 400, 1530, 15.7),
    ("X5", "suv", "3.0L Turbo I6", 375, 520, 2130, 11.2),
    ("M3", "sports_car", "3.0L Twin-Turbo I6", 473, 550, 1630, 11.2),
    ("C-Class", "sedan", "2.0L Turbo I4", 255, 400, 1625, 15.7),
    ("GLE", "suv", "3.0L Turbo I6 Mild-Hybrid", 375, 500, 2130, 11.2),
    ("AMG GT", "sports_car", "4.0L Twin-Turbo V8", 523, 650, 1645, 9.4),
    ("A4", "sedan", "2.0L TSI", 201, 320, 1465, 17.3),
    ("Q5", "suv", "2.0TFSI", 261, 370, 1805, 14.7),
    ("R8", "sports_car", "5.2L V10", 562, 540, 1560, 9.4),
    ("Altima", "sedan", "2.5L I4", 188, 244, 1490, 17.3),
    ("X-Trail", "suv", "2.5L I4", 171, 234, 1600, 14.7),
    ("Skyline", "sports_car", "3.0L Twin-Turbo V6", 300, 475, 1530, 11.2),
    ("Mazda3", "hatchback", "2.5L I4", 194, 252, 1400, 16.8),
    ("CX-5", "suv", "2.5L I4", 187, 252, 1630, 14.7),
    ("Forester", "suv", "2.5L H4", 182, 240, 1600, 15.7),
    ("WRX", "sports_car", "2.4L Turbo Boxer-4", 271, 392, 1560, 11.2),
    ("Model 3", "sedan", "Electric Dual Motor", 480, 639, 1760, 4.3),
    ("Model Y", "suv", "Electric Dual Motor", 456, 639, 1900, 4.0),
    ("Model S", "sedan", "Electric Tri Motor", 670, 850, 2162, 3.5),
    ("911", "sports_car", "3.0L Twin-Turbo Flat-6", 379, 450, 1430, 11.2),
    ("Cayenne", "suv", "3.0L Turbo V6", 440, 570, 2100, 11.2),
    ("Panamera", "sedan", "2.9L Twin-Turbo V6", 440, 570, 1890, 12.4),
    ("488 Spider", "sports_car", "3.9L Twin-Turbo V8", 670, 760, 1370, 8.6),
    ("SF90", "suv", "4.0L Twin-Turbo V8 Hybrid", 986, 800, 1570, 7.0),
    ("Huracan", "sports_car", "5.2L V10", 631, 550, 1422, 8.6),
    ("Urus", "suv", "4.0L Twin-Turbo V8", 641, 850, 2150, 9.4),
    ("720S", "sports_car", "4.0L Twin-Turbo V8", 710, 780, 1383, 8.6),
    ("Continental GT", "coupe", "6.0L Twin-Turbo W12", 626, 820, 2270, 9.4),
    ("Phantom", "sedan", "6.75L Twin-Turbo V12", 563, 900, 2560, 8.6),
    ("F-Type", "sports_car", "5.0L Supercharged V8", 450, 580, 1665, 11.2),
    ("Defender", "suv", "3.0L Mild-Hybrid I6", 395, 550, 2120, 11.2),
    ("XC90", "suv", "2.0L Turbo/Supercharged I4", 455, 640, 2040, 12.4),
    ("S90", "sedan", "2.0L Turbo/Supercharged I4", 400, 550, 1750, 12.4),
    ("Sportage", "suv", "1.6L Turbo I4", 180, 265, 1600, 14.7),
    ("Ceed", "hatchback", "1.0L Turbo I3", 120, 200, 1250, 17.3),
    ("Swift", "hatchback", "1.2L I4", 90, 113, 900, 19.6),
    ("Outlander", "suv", "2.5L I4", 168, 245, 1670, 13.4),
    ("Silverado", "truck", "6.2L V8", 420, 623, 2350, 10.7),
    ("Corvette", "sports_car", "6.2L V8", 490, 637, 1560, 11.2),
    ("Escalade", "suv", "6.2L V8", 420, 623, 2780, 9.4),
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

GENDERS = ["male", "female"]


def random_company(rng: random.Random) -> dict:
    """Generate a deterministic company from the seeded RNG."""
    city = rng.choice(CITIES)
    return {
        "entity_type": "CarManufacturer",
        "name": rng.choice(COMPANIES),
        "founded": rng.randint(1900, 1990),
        "headquarters": {"city": city[0], "country": city[1]},
        "employee_count": rng.randint(500, 200000),
        "revenue_billion_usd": round(rng.uniform(1, 300), 1),
        "market": rng.choice(["domestic", "international", "global"]),
    }


def random_car(rng: random.Random) -> dict:
    """Generate a deterministic car from the seeded RNG."""
    template = rng.choice(CARS)
    return {
        "entity_type": "CarModel",
        "name": template[0],
        "type": template[1],
        "engine": template[2],
        "horsepower": template[3],
        "torque_nm": template[4],
        "weight_kg": template[5],
        "fuel_economy_l_per_100km": template[6],
    }


def random_owner(rng: random.Random) -> dict:
    """Generate a deterministic owner from the seeded RNG."""
    return {
        "entity_type": "OwnerProfile",
        "age": rng.randint(18, 85),
        "gender": rng.choice(GENDERS),
        "occupation": rng.choice(OCCUPATIONS),
        "income_bracket": rng.choice(["low", "middle", "upper_middle", "high", "ultra_high"]),
        "hobbies": rng.choice(HOBBIES),
        "years_of_ownership": rng.randint(0, 30),
    }


def random_city(rng: random.Random) -> dict:
    """Generate a deterministic city from the seeded RNG."""
    template = rng.choice(CITIES)
    return {
        "entity_type": "City",
        "name": template[0],
        "country": template[1],
        "timezone": template[2],
        "area_km2": template[3],
        "climate": template[4],
        "population": rng.randint(10000, 15000000),
    }


def demo4():
    """Generate 1000 random nodes across 4 entity types with deterministic edges.

    All randomness uses a single seeded RNG (SEED=42).
    Every run produces the identical graph.
    """
    rng = random.Random(SEED)

    # Remove stale DB to avoid mixing old data
    import os
    db_path = "example_4.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    with Session() as session:
        G = nx_sql.DiGraph(session, name="example4_random_nodes")

        # Distribution: 250 companies, 300 cars, 250 owners, 200 cities
        node_counts = [250, 300, 250, 200]
        generators = [random_company, random_car, random_owner, random_city]
        labels = ["CarManufacturer", "CarModel", "OwnerProfile", "City"]

        node_keys = []
        for label, count, gen in zip(labels, node_counts, generators):
            keys = []
            for i in range(count):
                attrs = gen(rng)
                node_key = f"{label}_{i}"
                keys.append(node_key)
                G.add_node(node_key, **attrs)
            node_keys.append(keys)

        # =====================================================================
        # Edge Layer 1: Company → City (headquarters)
        # Each company links to one city based on its HQ attribute.
        # =====================================================================
        for i in range(len(node_keys[0])):
            comp_attrs = G.nodes[f"CarManufacturer_{i}"]
            hq_city = comp_attrs.get("headquarters", {}).get("city", "")
            # Find the closest matching city node
            for city_key in node_keys[3]:
                if G.nodes[city_key].get("name") == hq_city:
                    G.add_edge(f"CarManufacturer_{i}", city_key, edge_type="headquarters")
                    break

        # =====================================================================
        # Edge Layer 2: Company → CarModel (produces)
        # Each company produces 1-3 models.
        # =====================================================================
        for ci in range(len(COMPANIES)):
            num_models = min(len(CARS) // len(COMPANIES) + 1, 3)
            start = ci * num_models
            for j in range(num_models):
                car_idx = (start + j) % len(node_keys[1])
                G.add_edge(f"CarManufacturer_{ci}", f"CarModel_{car_idx}",
                           edge_type="produces")

        # =====================================================================
        # Edge Layer 3: OwnerProfile → CarModel (owns)
        # Each owner owns 1-2 cars.
        # =====================================================================
        for oi in range(len(node_keys[2])):
            num_cars = 1 if oi % 3 != 0 else 2
            for c in range(num_cars):
                car_idx = (oi * 7 + c * 13) % len(node_keys[1])
                G.add_edge(f"OwnerProfile_{oi}", f"CarModel_{car_idx}",
                           edge_type="owns")

        # =====================================================================
        # Edge Layer 4: CarModel → City (sold_in)
        # Each car is sold in 3 cities. Deterministic selection via RNG.
        # =====================================================================
        for car_idx in range(len(node_keys[1])):
            sold_cities = rng.sample(node_keys[3], min(3, len(node_keys[3])))
            for city_key in sold_cities:
                G.add_edge(f"CarModel_{car_idx}", city_key, edge_type="sold_in")

        # =====================================================================
        # Edge Layer 5: OwnerProfile → City (resides_in)
        # Each owner lives in one randomly assigned city.
        # =====================================================================
        for oi in range(len(node_keys[2])):
            city_key = rng.choice(node_keys[3])
            G.add_edge(f"OwnerProfile_{oi}", city_key, edge_type="resides_in")

        # =====================================================================
        # Edge Layer 6: CarModel ↔ CarModel (competes_with)
        # Cars of the same type connect to their 3 closest by horsepower.
        # Bidirectional = 2 directed edges per connection.
        # =====================================================================
        car_types = {}
        for idx in range(len(node_keys[1])):
            car_type = G.nodes[node_keys[1][idx]].get("type", "unknown")
            car_types.setdefault(car_type, []).append(idx)

        for car_type, indices in car_types.items():
            # Sort by horsepower for deterministic nearest-neighbor selection
            sorted_indices = sorted(indices,
                                    key=lambda i: G.nodes[node_keys[1][i]]["horsepower"])
            for pos, idx in enumerate(sorted_indices):
                # Connect to up to 3 nearest neighbors (same type, closest HP)
                candidates = []
                for offset in [1, 2, 3]:
                    if pos + offset < len(sorted_indices):
                        candidates.append(sorted_indices[pos + offset])
                    if pos - offset >= 0:
                        candidates.insert(0, sorted_indices[pos - offset])
                for cand in candidates[:3]:
                    G.add_edge(node_keys[1][idx], node_keys[1][cand],
                               edge_type="competes_with")

        # =====================================================================
        # Edge Layer 7: OwnerProfile ↔ OwnerProfile (shares_hobby)
        # Owners with ≥1 overlapping hobby connect to 3 most similar peers.
        # Bidirectional = 2 directed edges per connection.
        # =====================================================================
        owner_hobbies = {}
        for oi in range(len(node_keys[2])):
            hobbies_set = set(G.nodes[node_keys[2][oi]].get("hobbies", []))
            owner_hobbies[oi] = hobbies_set

        for oi in range(len(node_keys[2])):
            my_hobbies = owner_hobbies[oi]
            if not my_hobbies:
                continue
            # Score other owners by shared hobby count
            scores = []
            for oj in range(len(node_keys[2])):
                if oj == oi:
                    continue
                shared = len(my_hobbies & owner_hobbies[oj])
                if shared > 0:
                    scores.append((shared, oj))
            # Sort by shared count desc, then by index for determinism
            scores.sort(key=lambda x: (-x[0], x[1]))
            for _, oj in scores[:3]:
                shared = my_hobbies & owner_hobbies[oj]
                G.add_edge(f"OwnerProfile_{oi}", f"OwnerProfile_{oj}",
                           edge_type="shares_hobby",
                           shared_hobbies=sorted(shared))

        # =====================================================================
        # Edge Layer 8: City ↔ City (neighboring_country)
        # Cities in the same country connect to 3 nearest by population rank.
        # Bidirectional = 2 directed edges per connection.
        # =====================================================================
        cities_by_country = {}
        for ci in range(len(node_keys[3])):
            country = G.nodes[node_keys[3][ci]].get("country", "")
            cities_by_country.setdefault(country, []).append(ci)

        for country, indices in cities_by_country.items():
            sorted_indices = sorted(indices,
                                    key=lambda i: G.nodes[node_keys[3][i]]["population"])
            for pos, ci in enumerate(sorted_indices):
                candidates = []
                for offset in [1, 2, 3]:
                    if pos + offset < len(sorted_indices):
                        candidates.append(sorted_indices[pos + offset])
                    if pos - offset >= 0:
                        candidates.insert(0, sorted_indices[pos - offset])
                for cand in candidates[:3]:
                    G.add_edge(node_keys[3][ci], node_keys[3][cand],
                               edge_type="neighboring_country")

        # =====================================================================
        # Edge Layer 9: CarManufacturer ↔ CarManufacturer (same_hq)
        # Companies in the same city connect to each other.
        # =====================================================================
        hq_cities = {}
        for ci in range(len(node_keys[0])):
            hq_city = G.nodes[node_keys[0][ci]].get("headquarters", {}).get("city", "")
            hq_cities.setdefault(hq_city, []).append(ci)

        for city, indices in hq_cities.items():
            if len(indices) < 2:
                continue
            for i in range(len(indices)):
                for j in range(i + 1, len(indices)):
                    G.add_edge(node_keys[0][indices[i]],
                               node_keys[0][indices[j]],
                               edge_type="same_hq")

        # =====================================================================
        # Summary
        # =====================================================================
        print(f"Graph: {G.name}")
        print(f"Nodes: {G.number_of_nodes()}")
        print(f"Edges: {G.number_of_edges()}")

        # Count edges by type
        edge_types = {}
        for u, v, data in G.edges(data=True):
            etype = data.get("edge_type", "unknown")
            edge_types[etype] = edge_types.get(etype, 0) + 1
        print(f"\nEdge breakdown:")
        for etype, count in sorted(edge_types.items()):
            print(f"  {etype}: {count}")

        # Print sample of each node type
        samples_per_type = 2
        for label, count, gen in zip(labels, node_counts, generators):
            matching = [(n, d) for n, d in G.nodes(data=True)
                        if d.get("entity_type") == label]
            sampled = rng.sample(matching, min(samples_per_type, len(matching)))
            print(f"\n--- {label} (sample of {min(samples_per_type, count)}) ---")
            for node, data in sorted(sampled, key=lambda x: x[0]):
                print(f"  {data}")

        # Print sample edges per layer
        print("\n--- Sample edges by type ---")
        for etype in ["headquarters", "produces", "owns", "sold_in",
                       "resides_in", "competes_with", "shares_hobby",
                       "neighboring_country", "same_hq"]:
            edges_of_type = [(u, v, d) for u, v, d in G.edges(data=True)
                             if d.get("edge_type") == etype]
            if edges_of_type:
                sample = rng.sample(edges_of_type, min(3, len(edges_of_type)))
                print(f"\n  {etype} (sample of {len(sample)}):")
                for u, v, d in sorted(sample):
                    print(f"    {u} → {v}  |  {d}")

        session.commit()


if __name__ == "__main__":
    demo4()
