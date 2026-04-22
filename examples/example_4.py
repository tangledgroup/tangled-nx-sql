"""Example 4 – generate 1000 random nodes across 4 entity types with rich attributes.

Entity types:
  - CarManufacturer (company bio, founded year, headquarters city, country)
  - CarModel (name, type, engine, horsepower, torque, weight, fuel_economy)
  - OwnerProfile (age, gender, occupation, income_bracket, hobbies)
  - City (population, country, timezone, area_km2, climate)

No edges are created. All nodes are persisted to the database."""

import random
import networkx as nx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import nx_sql
from nx_sql.models import Base


engine = create_engine("sqlite:///nx_sql.db")
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

GENDERS = ["male", "female", "non-binary"]


def random_company() -> dict:
    city = random.choice(CITIES)
    return {
        "name": random.choice(COMPANIES),
        "founded": random.randint(1900, 1990),
        "headquarters": {"city": city[0], "country": city[1]},
        "employee_count": random.randint(500, 200000),
        "revenue_billion_usd": round(random.uniform(1, 300), 1),
        "market": random.choice(["domestic", "international", "global"]),
    }


def random_car() -> dict:
    template = random.choice(CARS)
    return {
        "name": template[0],
        "type": template[1],
        "engine": template[2],
        "horsepower": template[3],
        "torque_nm": template[4],
        "weight_kg": template[5],
        "fuel_economy_l_per_100km": template[6],
    }


def random_owner() -> dict:
    return {
        "age": random.randint(18, 85),
        "gender": random.choice(GENDERS),
        "occupation": random.choice(OCCUPATIONS),
        "income_bracket": random.choice(["low", "middle", "upper_middle", "high", "ultra_high"]),
        "hobbies": random.choice(HOBBIES),
        "years_of_ownership": random.randint(0, 30),
    }


def random_city() -> dict:
    template = random.choice(CITIES)
    return {
        "name": template[0],
        "country": template[1],
        "timezone": template[2],
        "area_km2": template[3],
        "climate": template[4],
        "population": random.randint(10000, 15000000),
    }


def demo4():
    """Generate 1000 random nodes across 4 entity types with no edges."""

    with Session() as session:
        G = nx_sql.DiGraph(session, name="example4_random_nodes")

        # Distribution: 250 companies, 300 cars, 250 owners, 200 cities
        node_counts = [250, 300, 250, 200]
        generators = [random_company, random_car, random_owner, random_city]
        labels = ["CarManufacturer", "CarModel", "OwnerProfile", "City"]

        for label, count, gen in zip(labels, node_counts, generators):
            for i in range(count):
                attrs = gen()
                # Use a unique string key so random collisions don't merge nodes
                node_key = f"{label}_{i}"
                G.add_node(node_key, **attrs)

        print(f"Graph: {G.name}")
        print(f"Nodes: {G.number_of_nodes()}")
        print(f"Edges: {G.number_of_edges()}")

        # Print sample of each type
        samples_per_type = 2
        for label, count, gen in zip(labels, node_counts, generators):
            matching = [n for n in G.nodes(data=True) if n[1].get("entity_type") == label]
            sampled = random.sample(matching, min(samples_per_type, len(matching)))
            print(f"\n--- {label} (sample of {min(samples_per_type, count)}) ---")
            for node, data in sampled:
                print(f"  {data}")

        session.commit()


if __name__ == "__main__":
    demo4()
