import json
import os

BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
BASE_DIR = os.path.abspath(BASE_DIR)

# 1. Enrich Purchase Properties
props_file = os.path.join(BASE_DIR, "properties.json")
with open(props_file, "r", encoding="utf-8") as f:
    props = json.load(f)

p_extra = {
    "prop_01": {
        "occupancy_certificate": "100% OC Received (BBMP Ref #2018/144)",
        "open_space_pct": "78% Open Green Area",
        "ev_charging_facility": "Installed (4 Dedicated EV Bays + 15A Pods)",
        "power_backup": "100% Full DG Backup (Including ACs & Appliances)",
        "lake_buffer_compliance": "Fully Compliant (>60m from Green Glen Storm Drain)",
        "encumbrance_certificate": "30-Year Nil Encumbrance Certificate Verified"
    },
    "prop_02": {
        "occupancy_certificate": "100% OC Received (All Towers Delivered)",
        "open_space_pct": "75% Landscaped Central Court",
        "ev_charging_facility": "Installed (Basement Level 1 EV Station)",
        "power_backup": "100% DG Power Backup for All Apartments",
        "lake_buffer_compliance": "Clear of Lake Buffer Zone (>250m to Bellandur Lake)",
        "encumbrance_certificate": "Clean Title & 30-Year Form 15 Nil EC"
    },
    "prop_03": {
        "occupancy_certificate": "100% OC Received (BDA / BBMP Approved)",
        "open_space_pct": "70% Open Space & Sports Grounds",
        "ev_charging_facility": "Sanctioned BESCOM 11kW Fast Charger",
        "power_backup": "100% Full Auto DG Backup",
        "lake_buffer_compliance": "Safe Gurukul Side Elevation; Zero Buffer Encroachment",
        "encumbrance_certificate": "Verified Nil Encumbrance (A-Khata Registered)"
    },
    "prop_04": {
        "occupancy_certificate": "100% OC Received (Delivered Gated Society)",
        "open_space_pct": "72% Sky Openness & Courtyards",
        "ev_charging_facility": "Basement 15A Charging Sockets Available",
        "power_backup": "100% DG Backup for Essential Circuits & Lifts",
        "lake_buffer_compliance": "Verified Clear of All Rajakaluves",
        "encumbrance_certificate": "30-Year Clean Legal Title & Nil EC"
    },
    "prop_05": {
        "occupancy_certificate": "100% OC Received (Ultra Luxury Benchmark)",
        "open_space_pct": "80% Landscaped Gardens & Water Features",
        "ev_charging_facility": "Private Wallbox EV Provision for Each Penthouse/3BHK",
        "power_backup": "100% Uninterrupted Full Load DG Generator",
        "lake_buffer_compliance": "Complies Fully with 30m NGT Lake Zone Guidelines",
        "encumbrance_certificate": "Flawless Tier 1 Legal Title Documentation"
    },
    "prop_06": {
        "occupancy_certificate": "RERA Phased OC Received (Active Handover)",
        "open_space_pct": "82% Waterfront Lawns & Parkland",
        "ev_charging_facility": "Shared Fast Charging Hub (Tata Power EZ Charge)",
        "power_backup": "100% Full Load DG Power Backup",
        "lake_buffer_compliance": "Designed with Elevated Promenade above Lake Buffer",
        "encumbrance_certificate": "BDA Sanctioned Plan & Nil Encumbrance"
    },
    "prop_07": {
        "occupancy_certificate": "Wings 1 to 40 OC Received; Remaining Wings Under RERA",
        "open_space_pct": "81% 81-Acre Mega Township Open Greenery",
        "ev_charging_facility": "50+ EV Charging Stations Across Campus",
        "power_backup": "100% DG Backup in All Towers",
        "lake_buffer_compliance": "Clear of Varthur Buffer (Strictly Bottleneck Route Trap)",
        "encumbrance_certificate": "Master Title Clean; Issue is Panathur Bottleneck Access"
    },
    "prop_08": {
        "occupancy_certificate": "100% OC Received (Brigade Standard Delivery)",
        "open_space_pct": "74% Themed Parks & Playfields",
        "ev_charging_facility": "Dedicated 15A Metered Sockets in Basement",
        "power_backup": "100% Full DG Backup with Auto-Switch",
        "lake_buffer_compliance": "Completely Safe Arterial Corridor Elevation",
        "encumbrance_certificate": "Verified BBMP A-Khata with 30-Year Nil EC"
    },
    "prop_09": {
        "occupancy_certificate": "100% OC Received (Integrated Commercial/Residential)",
        "open_space_pct": "70% Central Plaza & Terraces",
        "ev_charging_facility": "Fast Charging Plaza with 6 AC/DC Guns",
        "power_backup": "Industrial Grade Dual DG Generator System",
        "lake_buffer_compliance": "Full Rajakaluve Setback Clearance Certified",
        "encumbrance_certificate": "Clean Corporate Title with Institutional Legal Audit"
    },
    "prop_10": {
        "occupancy_certificate": "100% OC Received (Delivered Gated Enclave)",
        "open_space_pct": "76% Lush Coconut Grove Landscape",
        "ev_charging_facility": "15A EV Charging Plugs per Parking Slot",
        "power_backup": "100% DG Backup with Individual Sub-meters",
        "lake_buffer_compliance": "High Crest Location; Zero Flood or Lake Buffer Risk",
        "encumbrance_certificate": "Verified BBMP e-Aasthi A-Khata & Nil EC"
    }
}

for p in props:
    pid = p.get("id")
    if pid in p_extra:
        p.update(p_extra[pid])

with open(props_file, "w", encoding="utf-8") as f:
    json.dump(props, f, indent=2)

print(f"Enriched {len(props)} purchase properties with additional parameters.")

# 2. Enrich Rental Properties
rental_file = os.path.join(BASE_DIR, "rental_properties.json")
with open(rental_file, "r", encoding="utf-8") as f:
    rentals = json.load(f)

r_extra = {
    "rent_01": {
        "pet_friendly": "🐶 Pets Allowed (Dedicated Park Trail)",
        "bachelor_friendly": "Families & Corporate Working Professionals",
        "lock_in_period_months": 6,
        "notice_period_months": 1,
        "ev_charging_facility": "Dedicated 15A EV Socket in Basement Parking",
        "occupancy_certificate": "100% OC Received (Zero Legal Risk)"
    },
    "rent_02": {
        "pet_friendly": "Conditional (Cats & Small Dogs Allowed)",
        "bachelor_friendly": "Working Tech Professionals Welcome (ID Required)",
        "lock_in_period_months": 6,
        "notice_period_months": 1,
        "ev_charging_facility": "Public EV Charging Station in Clubhouse Parking",
        "occupancy_certificate": "100% OC Received"
    },
    "rent_03": {
        "pet_friendly": "🐶 Highly Pet Friendly (Open Lawn Areas)",
        "bachelor_friendly": "Families & Senior Techies Preferred",
        "lock_in_period_months": 11,
        "notice_period_months": 2,
        "ev_charging_facility": "Dedicated EV Wall-plug in Private Parking",
        "occupancy_certificate": "100% OC Received"
    },
    "rent_04": {
        "pet_friendly": "No Pets Allowed as per Landlord Rule",
        "bachelor_friendly": "Family Preferred by Society Guidelines",
        "lock_in_period_months": 6,
        "notice_period_months": 1,
        "ev_charging_facility": "15A Plug Point Available on Request",
        "occupancy_certificate": "100% OC Received"
    },
    "rent_05": {
        "pet_friendly": "🐶 Pet Friendly (Spacious Balconies & Garden)",
        "bachelor_friendly": "Families Preferred; Quiet Enclave Bylaws",
        "lock_in_period_months": 11,
        "notice_period_months": 2,
        "ev_charging_facility": "Dedicated Private EV Charger Provision",
        "occupancy_certificate": "100% OC Received"
    },
    "rent_06": {
        "pet_friendly": "🐶 Pet Friendly (Lake Promenade Access)",
        "bachelor_friendly": "Young IT Professionals & Couples Welcomed",
        "lock_in_period_months": 6,
        "notice_period_months": 1,
        "ev_charging_facility": "Tata Power EZ Fast EV Hub at Gate",
        "occupancy_certificate": "Phased OC Verified"
    },
    "rent_07": {
        "pet_friendly": "Allowed with Society Pet Registration Tag",
        "bachelor_friendly": "Bachelors & Bachelorettes Welcomed with HR Letter",
        "lock_in_period_months": 6,
        "notice_period_months": 1,
        "ev_charging_facility": "50+ EV Charging Bays Across Township",
        "occupancy_certificate": "OC Received for Assigned Tower"
    }
}

for r in rentals:
    rid = r.get("id")
    if rid in r_extra:
        r.update(r_extra[rid])

with open(rental_file, "w", encoding="utf-8") as f:
    json.dump(rentals, f, indent=2)

print(f"Enriched {len(rentals)} rental properties with additional parameters.")
