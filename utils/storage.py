import os
import json
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
PREFS_FILE = os.path.join(DATA_DIR, "user_preferences.json")
PROPS_FILE = os.path.join(DATA_DIR, "properties.json")
RENTAL_FILE = os.path.join(DATA_DIR, "rental_properties.json")
NEARBY_PROPS_FILE = os.path.join(DATA_DIR, "nearby_properties.json")
GATED_PLOTS_FILE = os.path.join(DATA_DIR, "gated_plots.json")
ZONES_FILE = os.path.join(DATA_DIR, "market_zones.json")
CUSTOM_ZONES_FILE = os.path.join(DATA_DIR, "custom_user_zones.json")
ANCHORS_FILE = os.path.join(DATA_DIR, "anchors.json")
HISTORICAL_CSV = os.path.join(DATA_DIR, "historical_prices.csv")
TRACKER_LOG = os.path.join(DATA_DIR, "daily_tracker_log.json")
AUDIT_LEDGER_FILE = os.path.join(DATA_DIR, "property_audit_ledger.json")
CHANGES_CSV_FILE = os.path.join(DATA_DIR, "property_parameter_changes.csv")
ALL_PURCHASE_CSV = os.path.join(DATA_DIR, "all_purchase_properties_daily.csv")
ALL_RENTAL_CSV = os.path.join(DATA_DIR, "all_rental_properties_daily.csv")
ALL_GATED_PLOTS_CSV = os.path.join(DATA_DIR, "all_gated_plots_daily.csv")
TOP_10_PURCHASE_CSV = os.path.join(DATA_DIR, "top_10_purchase_daily.csv")
TOP_5_RENTAL_CSV = os.path.join(DATA_DIR, "top_5_rental_daily.csv")


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


def get_gated_plots():
    return load_json(GATED_PLOTS_FILE, default=[])


def save_gated_plots(plots):
    return save_json(GATED_PLOTS_FILE, plots)


def get_market_zones():
    return load_json(ZONES_FILE, default={"green_zones": [], "red_zones": []})


def get_custom_zones():
    """
    Returns custom user zones if configured, otherwise initializes from market_zones.json.
    Structure:
    {
        "use_custom": False,
        "green_pins": [...],
        "red_pins": [...]
    }
    """
    if os.path.exists(CUSTOM_ZONES_FILE):
        return load_json(CUSTOM_ZONES_FILE, default=None)
    
    # Default initial green and red pins from market_zones
    mz = get_market_zones()
    default_green = [
        {
            "id": gz.get("id", "gz_default"),
            "name": gz.get("name", "Allowed Zone"),
            "lat": gz.get("center", [12.9325, 77.6795])[0],
            "lng": gz.get("center", [12.9325, 77.6795])[1],
            "radius_meters": gz.get("radius_meters", 1000),
            "description": gz.get("description", "Allowed area for radar check")
        }
        for gz in mz.get("green_zones", [])
    ]
    default_red = [
        {
            "id": rz.get("id", "rz_default"),
            "name": rz.get("name", "Excluded Bottleneck"),
            "lat": rz.get("center", [12.9360, 77.7085])[0],
            "lng": rz.get("center", [12.9360, 77.7085])[1],
            "radius_meters": rz.get("radius_meters", 800),
            "penalty_points": rz.get("penalty_points", -50),
            "reason": rz.get("reason", "Severe traffic choke point")
        }
        for rz in mz.get("red_zones", [])
    ]
    return {
        "use_custom": False,
        "green_pins": default_green,
        "red_pins": default_red
    }


def save_custom_zones(data):
    return save_json(CUSTOM_ZONES_FILE, data)


def get_anchors():
    return load_json(ANCHORS_FILE, default={})


def get_historical_prices_df():
    if os.path.exists(HISTORICAL_CSV):
        return pd.read_csv(HISTORICAL_CSV)
    return pd.DataFrame()


def get_tracker_log():
    return load_json(TRACKER_LOG, default={})


def get_parameter_changes_df():
    if os.path.exists(CHANGES_CSV_FILE):
        return pd.read_csv(CHANGES_CSV_FILE)
    return pd.DataFrame()
