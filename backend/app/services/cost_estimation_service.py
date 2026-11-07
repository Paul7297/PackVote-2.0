"""
Rule-based cost estimation service for PackVote trips.

All figures are estimates in INR based on open India travel benchmarks
(2024-2025). External factors modeled include:
- Origin/Departure City (e.g. Delhi, Mumbai, Bengaluru, etc.)
- Flight fares (round-trip per person based on route distance)
- Train fares (AC 3-Tier and Sleeper benchmarks based on route distance)
- Road transit (car mileage at ~14 km/L, petrol at ~₹102.50/L, expressway tolls)
- Hotel/accommodation per room (2 persons/room)
- Daily food & dining (adjusted for vegetarian preferences)
- Sightseeing & adventure activity passes
- Destination suitability verdict & group benefit synthesis
"""

from __future__ import annotations

import math
from collections import Counter
from datetime import date
from typing import Any


# ---------------------------------------------------------------------------
# Internal cost tables (INR)
# ---------------------------------------------------------------------------

_ORIGIN_HUBS: dict[str, tuple[float, float, str]] = {
    "delhi": (28.6139, 77.2090, "Delhi (NCR)"),
    "mumbai": (19.0760, 72.8777, "Mumbai"),
    "bengaluru": (12.9716, 77.5946, "Bengaluru"),
    "kolkata": (22.5726, 88.3639, "Kolkata"),
    "chennai": (13.0827, 80.2707, "Chennai"),
    "hyderabad": (17.3850, 78.4867, "Hyderabad"),
    "pune": (18.5204, 73.8567, "Pune"),
    "ahmedabad": (23.0225, 72.5714, "Ahmedabad"),
    "jaipur": (26.9124, 75.7873, "Jaipur"),
}

_HOTEL_RATES: dict[str, tuple[float, float]] = {
    "budget": (800.0, 1500.0),
    "mid": (2000.0, 4000.0),
    "luxury": (6000.0, 12000.0),
}

_FOOD_RATES: dict[str, tuple[float, float]] = {
    "budget": (300.0, 500.0),
    "mid": (600.0, 900.0),
    "luxury": (1200.0, 2000.0),
}

_TRANSPORT_RATES: dict[str, float] = {
    "budget": 500.0,
    "mid": 1000.0,
    "luxury": 2000.0,
}

_ACTIVITY_RATES: dict[str, float] = {
    "budget": 200.0,
    "mid": 400.0,
    "luxury": 800.0,
}

_FLIGHT_RATES: dict[str, tuple[float, float]] = {
    "budget": (3000.0, 5000.0),
    "mid": (5000.0, 8000.0),
    "luxury": (8000.0, 15000.0),
}

# Road and Fuel benchmarks (India 2024-2025)
_PETROL_PRICE_PER_LITRE = 102.50
_CAR_MILEAGE_KM_PER_LITRE = 14.0
_TOLL_RATE_PER_KM = 1.35
_DEFAULT_DISTANCE_KM = 550.0

# Train Fare benchmarks (Indian Railways)
_TRAIN_SLEEPER_RATE_PER_KM = 0.55
_TRAIN_3AC_RATE_PER_KM = 1.45

# Climates that typically involve hilly / cold terrain → higher local transport
_HIGH_TRANSPORT_CLIMATES: frozenset[str] = frozenset({"cold"})

_DEFAULT_NIGHTS = 3
_PEOPLE_PER_ROOM = 2
_MAX_ACTIVITIES = 5
_VEG_DISCOUNT = 0.10   # veg food is ~10 % cheaper


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _norm(value: Any) -> str:
    """Return a lowercase-stripped string, or '' for None/empty."""
    return str(value).strip().lower() if value is not None else ""


def _midpoint(lo: float, hi: float) -> float:
    return (lo + hi) / 2.0


def _resolve_cost_tier(destination) -> tuple[str, bool]:
    tier = _norm(getattr(destination, "cost_tier", None))
    if tier in _HOTEL_RATES:
        return tier, False
    return "mid", True


def _mode_string(values: list[str]) -> str | None:
    counts = Counter(v for v in values if v)
    return counts.most_common(1)[0][0] if counts else None


def _calculate_transit_options(
    destination,
    cost_tier: str,
    member_count: int,
    origin_city: str = "delhi",
) -> dict:
    """Compute distance, road/fuel/toll expenses, train fares, and flight estimates from origin."""
    city_key = _norm(origin_city)
    hub_info = _ORIGIN_HUBS.get(city_key, _ORIGIN_HUBS["delhi"])
    hub_lat, hub_lon, hub_label = hub_info

    lat = getattr(destination, "latitude", None)
    lon = getattr(destination, "longitude", None)

    if lat is not None and lon is not None:
        try:
            dlat = math.radians(float(lat) - hub_lat)
            dlon = math.radians(float(lon) - hub_lon)
            a = (
                math.sin(dlat / 2.0) ** 2
                + math.cos(math.radians(hub_lat))
                * math.cos(math.radians(float(lat)))
                * math.sin(dlon / 2.0) ** 2
            )
            c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
            distance_km = max(120.0, 6371.0 * c * 1.25)
        except Exception:
            distance_km = _DEFAULT_DISTANCE_KM
    else:
        distance_km = _DEFAULT_DISTANCE_KM

    round_trip_km = round(distance_km * 2.0)

    # 1. Car / Road (Petrol + Expressway Tolls)
    litres_needed = round(round_trip_km / _CAR_MILEAGE_KM_PER_LITRE, 1)
    fuel_cost = round(litres_needed * _PETROL_PRICE_PER_LITRE)
    toll_charges = round(round_trip_km * _TOLL_RATE_PER_KM)
    car_group_total = fuel_cost + toll_charges
    car_per_person = round(car_group_total / member_count)

    # 2. Train (Sleeper & 3AC)
    train_sleeper = round(max(380.0, round_trip_km * _TRAIN_SLEEPER_RATE_PER_KM))
    train_3ac = round(max(950.0, round_trip_km * _TRAIN_3AC_RATE_PER_KM))
    train_per_person = train_3ac

    # 3. Flight
    tier_mult = {"budget": 0.85, "mid": 1.0, "luxury": 1.45}.get(cost_tier, 1.0)
    base_flight = max(3200.0, 2200.0 + (distance_km * 3.4)) * tier_mult
    flight_per_person = round(base_flight)
    flight_group_total = flight_per_person * member_count

    return {
        "origin_city": hub_label,
        "one_way_km": round(distance_km),
        "round_trip_km": round_trip_km,
        "car": {
            "petrol_price_per_litre": _PETROL_PRICE_PER_LITRE,
            "litres_needed": litres_needed,
            "fuel_cost": fuel_cost,
            "toll_charges": toll_charges,
            "total_group": car_group_total,
            "per_person": car_per_person,
        },
        "train": {
            "sleeper_per_person": train_sleeper,
            "ac_3tier_per_person": train_3ac,
            "per_person": train_per_person,
            "total_group": train_per_person * member_count,
        },
        "flight": {
            "per_person_round_trip": flight_per_person,
            "total_group": flight_group_total,
        },
    }


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def estimate_trip_cost(
    trip,
    destination,
    preferences: list,
    member_count: int,
    origin_city: str = "delhi",
) -> dict:
    """Return a rule-based cost estimate for the given trip + destination."""
    assumptions: list[str] = []
    missing_data: list[str] = []

    # 1. Resolve cost tier
    cost_tier, tier_assumed = _resolve_cost_tier(destination)
    if tier_assumed:
        cost_tier_label = "mid (assumed)"
        assumptions.append(
            "Destination cost_tier is missing or unrecognised; 'mid' pricing used."
        )
        missing_data.append("destination.cost_tier")
    else:
        cost_tier_label = cost_tier

    # 2. Trip duration
    start: date | None = getattr(trip, "start_date", None)
    end: date | None = getattr(trip, "end_date", None)

    if start and end and end > start:
        nights = (end - start).days
    else:
        nights = _DEFAULT_NIGHTS
        assumptions.append(
            f"Trip dates not set or invalid; defaulting to {_DEFAULT_NIGHTS} nights."
        )
        missing_data.append("trip.start_date / trip.end_date")

    # 3. Member count
    if member_count < 1:
        member_count = 1
        assumptions.append("Member count was < 1; defaulted to 1.")

    # 4. Food preference
    food_prefs = [_norm(getattr(p, "food_pref", "")) for p in preferences]
    food_mode = _mode_string(food_prefs)
    if not food_mode:
        food_mode = "no_preference"
        assumptions.append(
            "No food preferences found; 'no_preference' assumed (mid food pricing)."
        )
        missing_data.append("trip_preference.food_pref")

    # 5. Activities
    all_activities: list[str] = []
    for pref in preferences:
        acts = getattr(pref, "preferred_activities", None)
        if isinstance(acts, list):
            all_activities.extend(_norm(a) for a in acts if _norm(a))

    distinct_activities = list(dict.fromkeys(all_activities))
    activity_count = min(len(distinct_activities), _MAX_ACTIVITIES)
    if activity_count == 0:
        assumptions.append("No preferred activities found; activity cost is zero.")
        missing_data.append("trip_preference.preferred_activities")

    # 6. Climate
    climate = _norm(getattr(destination, "climate", None))
    hilly_climate = climate in _HIGH_TRANSPORT_CLIMATES
    if not climate:
        missing_data.append("destination.climate")

    # 7. Hotel cost
    hotel_lo, hotel_hi = _HOTEL_RATES[cost_tier]
    hotel_per_room_per_night = _midpoint(hotel_lo, hotel_hi)
    rooms = math.ceil(member_count / _PEOPLE_PER_ROOM)
    hotel_total = hotel_per_room_per_night * rooms * nights

    assumptions.append(
        f"Hotel: {_PEOPLE_PER_ROOM} persons/room assumed; {rooms} room(s) × {nights} night(s)."
    )

    # 8. Food cost
    food_lo, food_hi = _FOOD_RATES[cost_tier]
    food_per_person_per_day = _midpoint(food_lo, food_hi)
    if food_mode == "veg":
        food_per_person_per_day *= (1.0 - _VEG_DISCOUNT)
        assumptions.append("Food: vegetarian preference detected; 10 % discount applied.")

    food_total = food_per_person_per_day * member_count * nights

    # 9. Local transport
    transport_per_person = _TRANSPORT_RATES[cost_tier]
    if hilly_climate:
        transport_per_person *= 1.20
        assumptions.append(
            f"Local transport: 20 % surcharge for hilly/cold climate ('{climate}')."
        )
    transport_total = transport_per_person * member_count

    # 10. Activities cost
    activity_per_person = _ACTIVITY_RATES[cost_tier] * activity_count
    activities_total = activity_per_person * member_count

    # 11. Transit options (Flight, Train, Road/Petrol/Toll)
    transit = _calculate_transit_options(destination, cost_tier, member_count, origin_city=origin_city)
    flight_round_trip = transit["flight"]["per_person_round_trip"]
    flights_total = transit["flight"]["total_group"]

    assumptions.append(
        f"Transit calculated with departure city: {transit['origin_city']} (~{transit['one_way_km']} km one-way). "
        "Fares reflect distance-based fuel, toll, train, and flight benchmarks."
    )

    # 12. Grand total (default balanced with flight)
    total_group_cost = (
        hotel_total
        + food_total
        + transport_total
        + activities_total
        + flights_total
    )
    per_person_cost = total_group_cost / member_count

    # Alternative totals with train or car
    surface_base_group = hotel_total + food_total + transport_total + activities_total
    total_group_train = surface_base_group + transit["train"]["total_group"]
    per_person_train = total_group_train / member_count

    total_group_car = surface_base_group + transit["car"]["total_group"]
    per_person_car = total_group_car / member_count

    transport_options_list = [
        {
            "mode": "flight",
            "label": f"Flight from {transit['origin_city']}",
            "estimated_cost_per_person": round(flight_round_trip),
            "details": f"Airfare from {transit['origin_city']} (~₹{flight_round_trip:,}/person round trip)",
        },
        {
            "mode": "train",
            "label": f"Train from {transit['origin_city']}",
            "estimated_cost_per_person": round(transit["train"]["per_person"]),
            "details": f"AC 3-Tier ({transit['one_way_km']} km, Sleeper ₹{transit['train']['sleeper_per_person']:,})",
        },
        {
            "mode": "car",
            "label": f"Drive from {transit['origin_city']}",
            "estimated_cost_per_person": round(transit["car"]["per_person"]),
            "details": f"Road trip {transit['one_way_km']} km · Petrol ₹{transit['car']['fuel_cost']:,} ({transit['car']['litres_needed']}L @ ₹{transit['car']['petrol_price_per_litre']}/L) + ₹{transit['car']['toll_charges']:,} tolls",
        },
    ]

    return {
        "currency": "INR",
        "origin_city": transit["origin_city"],
        "member_count": member_count,
        "trip_nights": nights,
        "destination_name": getattr(destination, "name", "Unknown"),
        "cost_tier_used": cost_tier_label,
        "estimation_method": "rule_based",
        "assumptions": assumptions,
        "transit_details": transit,
        "transport_options": transport_options_list,
        "components": {
            "hotel": {
                "per_room_per_night": round(hotel_per_room_per_night, 2),
                "rooms": rooms,
                "nights": nights,
                "total": round(hotel_total, 2),
            },
            "food": {
                "per_person_per_day": round(food_per_person_per_day, 2),
                "total": round(food_total, 2),
            },
            "local_transport": {
                "per_person": round(transport_per_person, 2),
                "total": round(transport_total, 2),
            },
            "activities": {
                "per_person": round(activity_per_person, 2),
                "activity_count": activity_count,
                "total": round(activities_total, 2),
            },
            "flights": {
                "per_person_round_trip": round(flight_round_trip, 2),
                "total": round(flights_total, 2),
            },
            "train": {
                "per_person": round(transit["train"]["per_person"], 2),
                "total": round(transit["train"]["total_group"], 2),
            },
            "car_road": {
                "fuel_cost": round(transit["car"]["fuel_cost"], 2),
                "toll_charges": round(transit["car"]["toll_charges"], 2),
                "per_person": round(transit["car"]["per_person"], 2),
                "total": round(transit["car"]["total_group"], 2),
            },
        },
        "total_group_cost": round(total_group_cost, 2),
        "per_person_cost": round(per_person_cost, 2),
        "alternatives": {
            "total_with_train_per_person": round(per_person_train, 2),
            "total_with_car_per_person": round(per_person_car, 2),
        },
        "data_sources": [
            f"Calculated from departure hub: {transit['origin_city']}",
            "Rule-based estimates from PackVote cost model",
            "Indian petrol (~₹102.50/L) and expressway toll benchmarks",
            "Open market benchmarks (India travel, 2024-2025)",
        ],
        "missing_data": missing_data,
    }


def generate_destination_summary(
    trip,
    destination,
    preferences: list,
    member_count: int,
    ml_score: float | None = None,
    origin_city: str = "delhi",
) -> dict:
    """
    Generate an intelligent travel verdict, benefits summary, transport options,
    and budget alignment for a destination candidate or recommendation.
    """
    cost_data = estimate_trip_cost(trip, destination, preferences, member_count, origin_city=origin_city)
    per_person_cost = cost_data["per_person_cost"]
    train_person_cost = cost_data["alternatives"]["total_with_train_per_person"]
    car_person_cost = cost_data["alternatives"]["total_with_car_per_person"]

    budget_max = getattr(trip, "budget_max", None)

    # 1. Evaluate Budget Feasibility
    if budget_max:
        if per_person_cost <= budget_max:
            budget_status = "within_budget"
        elif train_person_cost <= budget_max or car_person_cost <= budget_max:
            budget_status = "stretch"
        else:
            budget_status = "exceeds"
    else:
        budget_status = "within_budget"

    # 2. Extract Matching Benefits ("Why Choose This Place?")
    benefits: list[str] = []
    cautions: list[str] = []

    dest_styles = set(getattr(destination, "suitable_travel_styles", []) or [])
    dest_activities = set(getattr(destination, "suitable_activities", []) or [])
    dest_climate = _norm(getattr(destination, "climate", ""))

    member_styles: set[str] = set()
    member_acts: set[str] = set()
    climates: set[str] = set()
    for p in preferences:
        for s in (getattr(p, "travel_style", []) or []):
            if s: member_styles.add(_norm(s))
        for a in (getattr(p, "preferred_activities", []) or []):
            if a: member_acts.add(_norm(a))
        c = _norm(getattr(p, "climate_preference", ""))
        if c and c != "no_preference":
            climates.add(c)

    matched_styles = [s.replace("_", " ").title() for s in dest_styles if s in member_styles]
    matched_acts = [a.replace("_", " ").title() for a in dest_activities if a in member_acts]

    if matched_styles:
        benefits.append(f"Direct match for group travel style: {', '.join(matched_styles[:3])}")
    if matched_acts:
        benefits.append(f"Top-rated for your requested activities: {', '.join(matched_acts[:3])}")
    if dest_climate and dest_climate in climates:
        benefits.append(f"Ideal {dest_climate.capitalize()} climate aligns with group weather choice")

    # Transport benefit
    transit_info = cost_data["transit_details"]
    origin_name = transit_info["origin_city"]
    if transit_info["car"]["per_person"] < 3000:
        benefits.append(
            f"Road trip friendly from {origin_name}: Petrol (~₹{transit_info['car']['fuel_cost']:,}) + Tolls (~₹{transit_info['car']['toll_charges']:,}) comes to only ₹{transit_info['car']['per_person']:,}/person"
        )
    elif transit_info["train"]["per_person"] < 2500:
        benefits.append(
            f"Convenient train access from {origin_name}: AC 3-Tier fare estimated at ~₹{transit_info['train']['per_person']:,} round trip"
        )

    if not benefits:
        benefits.append(f"Accessible destination from {origin_name} with established group amenities")

    # 3. Cautions
    if transit_info["flight"]["per_person_round_trip"] > 7000:
        cautions.append(f"Flight fares from {origin_name} are relatively high; choosing Train or Car saves over ₹4,000 per person")
    if dest_climate == "cold":
        cautions.append("Cold climate: Warm layers and winter gear recommended for morning/night activities")
    elif dest_climate in ("tropical", "warm"):
        cautions.append("Warm climate: Light cottons, sun protection, and hydration recommended")

    # 4. Verdict & Tone
    if ml_score is not None and ml_score >= 25.0 and budget_status == "within_budget":
        verdict = f"Highly Recommended: Fits group budget from {origin_name} & matches preferences"
        verdict_tone = "success"
    elif budget_status == "stretch":
        verdict = f"Recommended with Surface Travel: Great match if taking Train or Car from {origin_name}"
        verdict_tone = "warning"
    elif budget_status == "exceeds":
        verdict = f"Premium Destination: Strong match from {origin_name} but requires higher budget allocation"
        verdict_tone = "info"
    else:
        verdict = f"Good Candidate Destination: Suitable for travel from {origin_name}"
        verdict_tone = "success" if (ml_score or 0) >= 20.0 else "info"

    return {
        "verdict": verdict,
        "verdict_tone": verdict_tone,
        "benefits": benefits[:4],
        "cautions": cautions[:2],
        "origin_city": origin_name,
        "estimated_budget_per_person": round(per_person_cost),
        "budget_status": budget_status,
        "weather_summary": f"{dest_climate.capitalize()} climate" if dest_climate else "Moderate climate",
        "transport_options": cost_data["transport_options"],
    }
