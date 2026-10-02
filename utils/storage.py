import os
import json
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
PREFS_FILE = os.path.join(DATA_DIR, "user_preferences.json")
PROPS_FILE = os.path.join(DATA_DIR, "properties.json")
RENTAL_FILE = os.path.join(DATA_DIR, "rental_properties.json")
NEARBY_PROPS_FILE = os.path.join(DATA_DIR, "nearby_properties.json")
ZONES_FILE = os.path.join(DATA_DIR, "market_zones.json")
ANCHORS_FILE = os.path.join(DATA_DIR, "anchors.json")
HISTORICAL_CSV = os.path.join(DATA_DIR, "historical_prices.csv")
TRACKER_LOG = os.path.join(DATA_DIR, "daily_tracker_log.json")


def load_json(path, default=None):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default if default is not None else {}
    return default if default is not None else {}


def save_json(path, data):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving JSON to {path}: {e}")
        return False


def get_user_preferences():
    return load_json(PREFS_FILE, default={
        "search_center": {"lat": 12.9325, "lng": 77.6850, "radius_km": 3.5},
        "weights": {
            "metro_proximity": 15,
            "traffic_integrity": 20,
            "exact_distances": 15,
            "builder_pedigree": 15,
            "water_logging": 10,
            "financials_appreciation": 15,
            "land_title_quality": 10
        }
    })


def save_user_preferences(prefs):
    return save_json(PREFS_FILE, prefs)


def get_properties():
    return load_json(PROPS_FILE, default=[])


def get_rental_properties():
    return load_json(RENTAL_FILE, default=[])


def get_nearby_properties():
    return load_json(NEARBY_PROPS_FILE, default=[])


def get_market_zones():
    return load_json(ZONES_FILE, default={"green_zones": [], "red_zones": []})


def get_anchors():
    return load_json(ANCHORS_FILE, default={})


def get_historical_prices_df():
    if os.path.exists(HISTORICAL_CSV):
        return pd.read_csv(HISTORICAL_CSV)
    return pd.DataFrame()


def get_tracker_log():
    return load_json(TRACKER_LOG, default={})
