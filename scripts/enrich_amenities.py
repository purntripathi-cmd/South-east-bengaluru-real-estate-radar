"""
Enrich properties.json and rental_properties.json with detailed, comparable amenity metrics:
- cycling_track
- jogging_track
- clubhouse_sqft
- swimming_pool
- sports_courts
- fitness_wellness
- amenities_summary
"""

import json
import os

PROPERTIES_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "properties.json")
RENTALS_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "rental_properties.json")

PURCHASE_AMENITIES = {
    "prop_01": {
        "cycling_track": "1.2 km Dedicated Asphalt Cycling Track (Internal Loop)",
        "jogging_track": "1.0 km Rubberized Synthetic Jogging Track",
        "clubhouse_sqft": "28,000 sqft Grand Club Iris",
        "swimming_pool": "Olympic Lap Pool (Heated) + Toddler Splash Pool",
        "sports_courts": "2 Floodlit Tennis, 2 Squash, 2 Badminton Courts",
        "fitness_wellness": "AC Technogym Center, Yoga/Pilates Deck, Steam & Sauna",
        "amenities_summary": "28k sqft Club, 1.2km Cycle Track, 1.0km Jog Track, Heated Pool, Tennis, Squash, Badminton, Gym"
    },
    "prop_02": {
        "cycling_track": "850m Paved Cycling Path (Podium Perimeter)",
        "jogging_track": "1.2 km Tree-Canopied Jogging Track",
        "clubhouse_sqft": "30,000 sqft Multilevel Clubhouse",
        "swimming_pool": "Double-Deck Resort Pool + Jacuzzi Jet Beds",
        "sports_courts": "Tennis Court, 3 Indoor Badminton Courts, Table Tennis Arena",
        "fitness_wellness": "Comprehensive Fitness Center, Aerobics Studio, Health Spa",
        "amenities_summary": "30k sqft Club, 850m Cycle Path, 1.2km Jog Track, Double-Deck Pool, Tennis, 3 Badminton Courts, Spa"
    },
    "prop_03": {
        "cycling_track": "750m Internal Paved Cycle Loop",
        "jogging_track": "900m Perimeter Jogging Track",
        "clubhouse_sqft": "20,000 sqft Resident Clubhouse",
        "swimming_pool": "Standard Outdoor Lap Pool + Kids Splash Pool",
        "sports_courts": "2 Badminton Courts, 1 Tennis Court, Half Basketball Court",
        "fitness_wellness": "Equipped Gymnasium & Multipurpose Activity Studio",
        "amenities_summary": "20k sqft Club, 750m Cycle Loop, 900m Jog Track, Outdoor Pool, Tennis, 2 Badminton Courts, Gym"
    },
    "prop_04": {
        "cycling_track": "800m Dedicated Ground Cycle Track",
        "jogging_track": "1.0 km Landscaped Walking & Jogging Trail",
        "clubhouse_sqft": "22,000 sqft Jharoka Clubhouse",
        "swimming_pool": "Semi-Covered Swimming Pool with Toddler Pool",
        "sports_courts": "Tennis Court, 2 Badminton Courts, Squash Court",
        "fitness_wellness": "Modern Gymnasium, Yoga & Meditation Gazebo",
        "amenities_summary": "22k sqft Club, 800m Cycle Track, 1.0km Jog Trail, Semi-Covered Pool, Tennis, Squash, Badminton, Gym"
    },
    "prop_05": {
        "cycling_track": "1.1 km Interlocking Paver Cycle Track",
        "jogging_track": "1.0 km Reflexology Jogging Track",
        "clubhouse_sqft": "26,000 sqft Signature Clubhouse",
        "swimming_pool": "Heated Indoor Pool + Rooftop Infinity Plunge Pool",
        "sports_courts": "2 Tennis Courts, Squash Court, 2 Badminton Courts, Billiards",
        "fitness_wellness": "State-of-the-Art Fitness Center, Steam/Sauna, Pilates Studio",
        "amenities_summary": "26k sqft Club, 1.1km Cycle Track, 1.0km Jog Track, Heated Indoor Pool, Rooftop Pool, Tennis, Squash, Gym"
    },
    "prop_06": {
        "cycling_track": "900m Internal Bicycle Path",
        "jogging_track": "1.1 km Shaded Greenery Jogging Path",
        "clubhouse_sqft": "24,000 sqft Community Clubhouse",
        "swimming_pool": "Resort-style Swimming Pool + Jacuzzi & Kids Pool",
        "sports_courts": "Tennis Court, 2 Badminton Courts, Cricket Pitch Nets",
        "fitness_wellness": "Health Club, Aerobics Room, Air-Conditioned Gymnasium",
        "amenities_summary": "24k sqft Club, 900m Cycle Path, 1.1km Jog Track, Resort Pool, Tennis, 2 Badminton Courts, Cricket Nets, Gym"
    },
    "prop_07": {
        "cycling_track": "2.2 km Cobbled Nature Cycle Boulevard",
        "jogging_track": "1.8 km Micro-Forest Jogging & Nature Trail",
        "clubhouse_sqft": "45,000 sqft Earth-Sheltered Luxury Clubhouse",
        "swimming_pool": "Bio-Filtered Natural Swimming Lake + Heated 50m Lap Pool",
        "sports_courts": "3 Tennis Courts, 4 Badminton Courts, 2 Squash Courts, Futsal Court",
        "fitness_wellness": "Olympic Gym, Cantilevered Yoga Deck over lake, Wellness Spa",
        "amenities_summary": "45k sqft Earth Club, 2.2km Nature Cycle Track, 1.8km Jog Trail, Bio Lake Pool, 3 Tennis, 4 Badminton, 2 Squash"
    },
    "prop_08": {
        "cycling_track": "1.6 km Dedicated Cycling Trail with Bike Stations",
        "jogging_track": "1.3 km Cushion-Tread Jogging Track",
        "clubhouse_sqft": "35,000 sqft Biophilic Green Clubhouse",
        "swimming_pool": "Olympic Lap Pool + Beach-entry Lagoon Pool",
        "sports_courts": "2 Tennis Courts, 3 Badminton Courts, Basketball Court, Skating Rink",
        "fitness_wellness": "Panoramic Glass Gym, Outdoor Calisthenics, Yoga Lawn",
        "amenities_summary": "35k sqft Club, 1.6km Cycle Trail, 1.3km Jog Track, Beach Lagoon Pool, 2 Tennis, 3 Badminton, Skating Rink"
    },
    "prop_09": {
        "cycling_track": "3.0 km Internal Township Cycle Boulevard",
        "jogging_track": "2.5 km Perimeter Jogging Track",
        "clubhouse_sqft": "50,000 sqft (5 Clubhouses across phases)",
        "swimming_pool": "5 Swimming Pools spread across phases",
        "sports_courts": "Multiple Tennis Courts, 6 Badminton Courts, Volleyball, Basketball",
        "fitness_wellness": "5 Gymnasiums, Aerobics Studios, Yoga Lawns",
        "amenities_summary": "50k sqft Club (5 Clubs), 3.0km Cycle Track, 2.5km Jog Track, 5 Pools, 6 Badminton, Tennis, Basketball"
    },
    "prop_10": {
        "cycling_track": "None (Shared 350m Driveway)",
        "jogging_track": "400m Concrete Walkway around building",
        "clubhouse_sqft": "8,000 sqft Basic Multi-Purpose Hall",
        "swimming_pool": "Small 15m Plunge Pool (Irregular maintenance)",
        "sports_courts": "None (Single Table Tennis in basement)",
        "fitness_wellness": "Basic 600 sqft Gym Room",
        "amenities_summary": "8k sqft Basic Hall, No Cycle Track, 400m Concrete Walkway, Small Plunge Pool, Basic Gym, No Sports Courts"
    }
}

RENTAL_AMENITIES = {
    "rent_01": {
        "cycling_track": "1.2 km Dedicated Asphalt Cycling Track",
        "jogging_track": "1.0 km Rubberized Synthetic Jogging Track",
        "clubhouse_sqft": "28,000 sqft Grand Club Iris",
        "amenities_summary": "28k sqft Club, 1.2km Cycle Track, 1.0km Jog Track, Heated Pool, Tennis, Squash, Badminton, Gym"
    },
    "rent_02": {
        "cycling_track": "850m Paved Cycling Path",
        "jogging_track": "1.2 km Tree-Canopied Jogging Track",
        "clubhouse_sqft": "30,000 sqft Multilevel Clubhouse",
        "amenities_summary": "30k sqft Club, 850m Cycle Path, 1.2km Jog Track, Double-Deck Pool, Tennis, 3 Badminton Courts, Spa"
    },
    "rent_03": {
        "cycling_track": "750m Internal Paved Cycle Loop",
        "jogging_track": "900m Perimeter Jogging Track",
        "clubhouse_sqft": "20,000 sqft Resident Clubhouse",
        "amenities_summary": "20k sqft Club, 750m Cycle Loop, 900m Jog Track, Outdoor Pool, Tennis, 2 Badminton Courts, Gym"
    },
    "rent_04": {
        "cycling_track": "800m Dedicated Ground Cycle Track",
        "jogging_track": "1.0 km Landscaped Walking & Jogging Trail",
        "clubhouse_sqft": "22,000 sqft Jharoka Clubhouse",
        "amenities_summary": "22k sqft Club, 800m Cycle Track, 1.0km Jog Trail, Semi-Covered Pool, Tennis, Squash, Badminton, Gym"
    },
    "rent_05": {
        "cycling_track": "1.1 km Interlocking Paver Cycle Track",
        "jogging_track": "1.0 km Reflexology Jogging Track",
        "clubhouse_sqft": "26,000 sqft Signature Clubhouse",
        "amenities_summary": "26k sqft Club, 1.1km Cycle Track, 1.0km Jog Track, Heated Indoor Pool, Rooftop Pool, Tennis, Squash, Gym"
    },
    "rent_06": {
        "cycling_track": "1.6 km Dedicated Cycling Trail with Bike Stations",
        "jogging_track": "1.3 km Cushion-Tread Jogging Track",
        "clubhouse_sqft": "35,000 sqft Biophilic Green Clubhouse",
        "amenities_summary": "35k sqft Club, 1.6km Cycle Trail, 1.3km Jog Track, Beach Lagoon Pool, 2 Tennis, 3 Badminton, Skating Rink"
    },
    "rent_07": {
        "cycling_track": "3.0 km Internal Township Cycle Boulevard",
        "jogging_track": "2.5 km Perimeter Jogging Track",
        "clubhouse_sqft": "50,000 sqft (5 Clubhouses)",
        "amenities_summary": "50k sqft Club (5 Clubs), 3.0km Cycle Track, 2.5km Jog Track, 5 Pools, 6 Badminton, Tennis, Basketball"
    }
}

def main():
    with open(PROPERTIES_FILE, "r", encoding="utf-8") as f:
        props = json.load(f)

    for p in props:
        pid = p["id"]
        if pid in PURCHASE_AMENITIES:
            p.update(PURCHASE_AMENITIES[pid])

    with open(PROPERTIES_FILE, "w", encoding="utf-8") as f:
        json.dump(props, f, indent=2)
    print(f"Enriched {len(props)} purchase properties with cycling/jogging tracks and amenity metrics.")

    with open(RENTALS_FILE, "r", encoding="utf-8") as f:
        rents = json.load(f)

    for r in rents:
        rid = r["id"]
        if rid in RENTAL_AMENITIES:
            r.update(RENTAL_AMENITIES[rid])

    with open(RENTALS_FILE, "w", encoding="utf-8") as f:
        json.dump(rents, f, indent=2)
    print(f"Enriched {len(rents)} rental properties with cycling/jogging tracks and amenity metrics.")

if __name__ == "__main__":
    main()
