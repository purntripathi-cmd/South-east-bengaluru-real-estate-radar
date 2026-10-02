"""
Bellandur Local Technicians & Services Helper
Provides verified technicians, pricing breakups, ratings, and proximity
from the user's residence benchmark: Bellandur Post Office (12.9288, 77.6758).
"""

import json
import math
import os
from typing import Dict, List, Optional

SERVICES_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "local_services.json")

# User's Home Vicinity Benchmark
BELLANDUR_POST_OFFICE = {
    "name": "Bellandur Post Office",
    "lat": 12.9288,
    "lng": 77.6758,
    "pincode": "560103",
    "landmark": "Bellandur Main Road / Green Glen Layout Junction"
}


def calculate_haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate geodesic distance in kilometers between two lat/lng pairs."""
    R = 6371.0  # Earth's radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)


def calculate_road_distance_from_post_office(lat: Optional[float], lng: Optional[float]) -> float:
    """Estimates realistic urban road distance (km) from Bellandur Post Office with detour factor."""
    if lat is None or lng is None:
        return 0.5
    straight_line = calculate_haversine_km(lat, lng, BELLANDUR_POST_OFFICE["lat"], BELLANDUR_POST_OFFICE["lng"])
    # Bengaluru urban winding roads have a 1.25x-1.35x detour factor
    road_km = max(0.15, round(straight_line * 1.3, 2))
    return road_km


def load_local_services() -> List[Dict]:
    """Loads verified technicians and services with calculated road distance from Bellandur Post Office."""
    if not os.path.exists(SERVICES_DATA_PATH):
        return []
    with open(SERVICES_DATA_PATH, "r", encoding="utf-8") as f:
        services = json.load(f)

    for s in services:
        dist = calculate_road_distance_from_post_office(s.get("lat"), s.get("lng"))
        s["road_distance_km"] = dist
    return services


def get_service_categories() -> List[str]:
    """Returns list of unique service categories available."""
    services = load_local_services()
    categories = sorted(list(set(s.get("category", "") for s in services if s.get("category"))))
    return ["All Categories"] + categories
