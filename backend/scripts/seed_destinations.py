"""
Seed script for PackVote's destination catalog.

IMPORTANT: All entries below are curated TEST/PLACEHOLDER data for
development purposes. They are not sourced from a verified travel
dataset. Replace or validate against a real, documented source
before using this catalog for production recommendations.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.database.database import SessionLocal
from app.models.destination import Destination
from app.schemas.destination import DestinationCreate
from app.crud.destination import create_destination_row, get_destination_by_identity


TEST_DESTINATIONS = [
    {
        "name": "Manali",
        "country": "India",
        "region": "Himachal Pradesh",
        "latitude": 32.2432,
        "longitude": 77.1892,
        "climate": "cold",
        "cost_tier": "mid",
        "suitable_travel_styles": ["adventure", "nature"],
        "suitable_activities": ["trekking", "camping", "sightseeing"],
        "suitable_traveler_types": ["friends", "solo", "couple"],
        "description": "Himalayan hill station known for trekking and mountain scenery. [Curated test data]",
    },
    {
        "name": "Goa",
        "country": "India",
        "region": "Goa",
        "latitude": 15.2993,
        "longitude": 74.1240,
        "climate": "tropical",
        "cost_tier": "mid",
        "suitable_travel_styles": ["relaxation", "nightlife", "food"],
        "suitable_activities": ["beach", "water_sports", "local_food", "nightlife"],
        "suitable_traveler_types": ["friends", "couple", "solo"],
        "description": "Coastal state known for beaches, nightlife, and Portuguese heritage. [Curated test data]",
    },
    {
        "name": "Jaipur",
        "country": "India",
        "region": "Rajasthan",
        "latitude": 26.9124,
        "longitude": 75.7873,
        "climate": "warm",
        "cost_tier": "mid",
        "suitable_travel_styles": ["cultural"],
        "suitable_activities": ["historical_places", "shopping", "local_food", "photography"],
        "suitable_traveler_types": ["family", "friends", "couple"],
        "description": "The Pink City, known for forts, palaces, and Rajasthani culture. [Curated test data]",
    },
    {
        "name": "Rishikesh",
        "country": "India",
        "region": "Uttarakhand",
        "latitude": 30.0869,
        "longitude": 78.2676,
        "climate": "moderate",
        "cost_tier": "budget",
        "suitable_travel_styles": ["adventure", "relaxation", "nature"],
        "suitable_activities": ["water_sports", "trekking", "camping", "sightseeing"],
        "suitable_traveler_types": ["solo", "friends"],
        "description": "Riverside town known for yoga, rafting, and spirituality. [Curated test data]",
    },
    {
        "name": "Kerala",
        "country": "India",
        "region": "Kerala",
        "latitude": 10.8505,
        "longitude": 76.2711,
        "climate": "tropical",
        "cost_tier": "mid",
        "suitable_travel_styles": ["relaxation", "nature"],
        "suitable_activities": ["sightseeing", "local_food", "wildlife", "spa_wellness"],
        "suitable_traveler_types": ["family", "couple", "solo"],
        "description": "Backwaters, houseboats, and lush greenery in South India. [Curated test data]",
    },
    {
        "name": "Shimla",
        "country": "India",
        "region": "Himachal Pradesh",
        "latitude": 31.1048,
        "longitude": 77.1734,
        "climate": "cold",
        "cost_tier": "mid",
        "suitable_travel_styles": ["relaxation", "nature"],
        "suitable_activities": ["sightseeing", "shopping", "photography"],
        "suitable_traveler_types": ["family", "couple"],
        "description": "Colonial-era hill station in the Himalayan foothills. [Curated test data]",
    },
    {
        "name": "Udaipur",
        "country": "India",
        "region": "Rajasthan",
        "latitude": 24.5854,
        "longitude": 73.7125,
        "climate": "warm",
        "cost_tier": "luxury",
        "suitable_travel_styles": ["cultural", "relaxation"],
        "suitable_activities": ["historical_places", "sightseeing", "photography"],
        "suitable_traveler_types": ["couple", "family"],
        "description": "The City of Lakes, known for palaces and romantic scenery. [Curated test data]",
    },
    {
        "name": "Andaman",
        "country": "India",
        "region": "Andaman and Nicobar Islands",
        "latitude": 11.7401,
        "longitude": 92.6586,
        "climate": "tropical",
        "cost_tier": "luxury",
        "suitable_travel_styles": ["relaxation", "adventure"],
        "suitable_activities": ["beach", "water_sports", "wildlife"],
        "suitable_traveler_types": ["couple", "friends", "family"],
        "description": "Remote tropical islands known for pristine beaches and diving. [Curated test data]",
    },
]


def seed():
    db = SessionLocal()
    created_count = 0
    skipped_count = 0

    try:
        for raw in TEST_DESTINATIONS:
            existing = get_destination_by_identity(
                db,
                name=raw["name"],
                country=raw["country"],
                region=raw["region"],
            )
            if existing is not None:
                print(f"SKIP (already exists): {raw['name']}")
                skipped_count += 1
                continue

            validated = DestinationCreate(**raw)
            destination = Destination(**validated.model_dump())
            create_destination_row(db, destination)
            print(f"ADDED: {raw['name']}")
            created_count += 1

        db.commit()
        print(f"\nDone. Created: {created_count}, Skipped: {skipped_count}")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()