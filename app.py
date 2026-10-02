import os
import json
import urllib.parse
from datetime import datetime
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import folium
from streamlit_folium import st_folium
import streamlit.components.v1 as components

from utils.geo import haversine_distance_km, check_zone_membership, check_custom_pins
from utils.scoring import compute_property_match_score, TIER_1_BUILDERS, TIER_2_BUILDERS
from utils.storage import (
    get_user_preferences,
    save_user_preferences,
    get_properties,
    get_rental_properties,
    get_nearby_properties,
    get_market_zones,
    get_custom_zones,
    save_custom_zones,
    get_anchors,
    get_historical_prices_df,
    get_tracker_log,
    get_parameter_changes_df,
    ALL_PURCHASE_CSV,
    ALL_RENTAL_CSV,
    TOP_10_PURCHASE_CSV,
    TOP_5_RENTAL_CSV,
    CHANGES_CSV_FILE
)

# Set page configuration
st.set_page_config(
    page_title="East Bengaluru Real Estate & Rental Radar",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="collapsed", # Better UX on mobile devices
)

# Client-side daily auto-refresh component (continues refreshing radar even when unattended)
components.html("""
<script>
let lastCheckedDay = new Date().toDateString();
setInterval(function() {
    let currentDay = new Date().toDateString();
    if (currentDay !== lastCheckedDay) {
        console.log("Calendar date changed (" + currentDay + "). Auto-refreshing Real Estate Radar...");
        lastCheckedDay = currentDay;
        window.parent.location.reload();
    }
}, 45000);
</script>
""", height=0, width=0)

# -------------------------------------------------------------
# Mobile-First & Desktop Responsive CSS
# -------------------------------------------------------------
st.markdown("""
<style>
    /* Responsive Global Styles */
    div[data-testid="stMetricValue"] {
        font-size: 1.5rem !important;
        font-weight: 700;
        color: #0D9488;
    }
    .main-header {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        padding: 1.2rem 1.4rem;
        border-radius: 12px;
        border-left: 6px solid #0D9488;
        margin-bottom: 1.2rem;
    }
    .main-title {
        color: #F8FAFC;
        font-size: 1.8rem;
        font-weight: 800;
        margin: 0;
        line-height: 1.2;
    }
    .sub-title {
        color: #94A3B8;
        font-size: 0.95rem;
        margin-top: 0.3rem;
    }
    .badge-green {
        background-color: #065F46;
        color: #A7F3D0;
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
        margin: 2px 2px;
    }
    .badge-red {
        background-color: #991B1B;
        color: #FECACA;
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
        margin: 2px 2px;
    }
    .badge-age {
        background-color: #312E81;
        color: #C7D2FE;
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
        margin: 2px 2px;
    }
    .badge-rating {
        background-color: #78350F;
        color: #FDE68A;
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 700;
        display: inline-block;
        margin: 2px 2px;
    }
    .badge-deal {
        background-color: #1E3A8A;
        color: #BFDBFE;
        padding: 5px 10px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 700;
    }
    .property-card {
        background: #1E293B;
        border-radius: 12px;
        padding: 1.1rem;
        margin-bottom: 1.2rem;
        border: 1px solid #334155;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .property-card:hover {
        border-color: #0D9488;
    }
    .cost-box {
        background: #0F172A;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 0.8rem;
        margin-top: 0.5rem;
    }
    .complaint-box {
        background: #1E1B4B;
        border-left: 4px solid #F59E0B;
        border-radius: 6px;
        padding: 0.8rem;
        margin-top: 0.6rem;
    }
    .nearby-box {
        background: #064E3B;
        border-left: 4px solid #10B981;
        border-radius: 6px;
        padding: 0.8rem;
        margin-top: 0.6rem;
    }
    .mobile-btn {
        display: inline-block;
        width: 100%;
        text-align: center;
        padding: 10px 14px;
        border-radius: 8px;
        font-weight: 700;
        text-decoration: none;
        margin-top: 6px;
    }

    /* Mobile Media Queries (< 768px) */
    @media (max-width: 768px) {
        .main-title {
            font-size: 1.35rem !important;
        }
        .sub-title {
            font-size: 0.82rem !important;
        }
        div[data-testid="stMetricValue"] {
            font-size: 1.2rem !important;
        }
        .property-card {
            padding: 0.8rem !important;
            margin-bottom: 0.9rem !important;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 2px;
            overflow-x: auto;
            white-space: nowrap;
        }
        .stTabs [data-baseweb="tab"] {
            font-size: 0.82rem !important;
            padding: 6px 8px !important;
        }
        iframe {
            height: 380px !important;
            max-height: 55vh !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# Initialize Session State & Preferences
# -------------------------------------------------------------
if "preferences" not in st.session_state:
    st.session_state.preferences = get_user_preferences()

if "scheduled_visits" not in st.session_state:
    st.session_state.scheduled_visits = {}

if "audit_checklist" not in st.session_state:
    st.session_state.audit_checklist = {}

if "custom_zones" not in st.session_state:
    st.session_state.custom_zones = get_custom_zones()

prefs = st.session_state.preferences
search_center = prefs.get("search_center", {"lat": 12.9325, "lng": 77.6850, "radius_km": 3.5})
weights = prefs.get("weights", {
    "metro_proximity": 15,
    "traffic_integrity": 20,
    "exact_distances": 15,
    "builder_pedigree": 15,
    "water_logging": 10,
    "financials_appreciation": 15,
    "land_title_quality": 10
})

properties = get_properties()
rental_properties = get_rental_properties()
nearby_properties = get_nearby_properties()
market_zones = get_market_zones()
anchors = get_anchors()
hist_df = get_historical_prices_df()
tracker_log = get_tracker_log()

# -------------------------------------------------------------
# Header Banner
# -------------------------------------------------------------
st.markdown("""
<div class="main-header">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
        <div>
            <h1 class="main-title">🧭 East Bengaluru Real Estate Radar</h1>
            <p class="sub-title">Bellandur • Green Glen Layout • Kadubeesanahalli (Gurukul Side) & Nearby Micro-Markets</p>
        </div>
        <div>
            <span class="badge-green">🛡️ Panathur Choke Filter</span>
            <span class="badge-rating">⭐ Resident Feedback & Complaints</span>
            <span class="badge-age">⏳ Age Evaluator</span>
            <span class="badge-green">⏰ 5:00 PM IST Tracker</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# KPI Quick Stats Row (Mobile-Responsive Columns)
# -------------------------------------------------------------
col_k1, col_k2, col_k3, col_k4 = st.columns([1, 1, 1, 1])
with col_k1:
    st.metric(label="Purchase Assets", value=f"{len(properties)} Properties", delta="Curated Tier 1/2")
with col_k2:
    st.metric(label="Rental Listings", value=f"{len(rental_properties)} Units", delta="Zero-Brokerage")
with col_k3:
    st.metric(label="Nearby Scanned", value=f"{len(nearby_properties)} Properties", delta="Sarjapur, HSR, Varthur")
with col_k4:
    st.metric(label="Daily Sync", value="5:00 PM IST", delta="Automated Cron (11:30 UTC)")

# -------------------------------------------------------------
# Sidebar: Scoring Weights, Map Provider & Preferences
# -------------------------------------------------------------
st.sidebar.header("⚙️ Radar Controls")

# Map Provider Selection
st.sidebar.subheader("🗺️ Map Engine & Provider")
map_provider = st.sidebar.selectbox(
    "Base Map Layer",
    [
        "Google Maps (Roadmap)",
        "Google Maps (Satellite / Hybrid)",
        "Google Maps (Terrain)",
        "OpenStreetMap (Standard)",
        "CartoDB Positron"
    ],
    index=0,
    help="Google Maps tile layers render high-resolution Google imagery without requiring an API key!"
)

show_nearby_on_map = st.sidebar.checkbox(
    "Show Nearby Areas on Map (Sarjapur, HSR, Varthur)",
    value=True,
    help="Plots worth-considering properties in adjacent micro-markets as purple pins on the map."
)

google_api_key = st.sidebar.text_input(
    "Optional: Google Maps API Key",
    type="password",
    help="Enter an optional Google Cloud API Key if you wish to use Google Places or JS SDK."
)

st.sidebar.markdown("---")
st.sidebar.subheader("📍 Search Radius & Geofence")
custom_radius = st.sidebar.slider(
    "Corridor Search Radius (km)",
    min_value=1.0,
    max_value=6.0,
    value=float(search_center.get("radius_km", 3.5)),
    step=0.5
)
search_center["radius_km"] = custom_radius

st.sidebar.markdown("---")
st.sidebar.subheader("⚖️ Parameter Scoring Weights (0-100%)")
w_metro = st.sidebar.slider("Metro Proximity", 0, 40, int(weights.get("metro_proximity", 15)), step=5)
w_traffic = st.sidebar.slider("Traffic & Route Integrity", 0, 40, int(weights.get("traffic_integrity", 20)), step=5)
w_dist = st.sidebar.slider("Exact Distances to Anchors", 0, 30, int(weights.get("exact_distances", 15)), step=5)
w_builder = st.sidebar.slider("Builder Pedigree", 0, 30, int(weights.get("builder_pedigree", 15)), step=5)
w_water = st.sidebar.slider("Water Logging & Drainage", 0, 25, int(weights.get("water_logging", 10)), step=5)
w_fin = st.sidebar.slider("Financials & Appreciation", 0, 30, int(weights.get("financials_appreciation", 15)), step=5)
w_legal = st.sidebar.slider("Land Title & Gated Tech", 0, 25, int(weights.get("land_title_quality", 10)), step=5)

active_weights = {
    "metro_proximity": w_metro,
    "traffic_integrity": w_traffic,
    "exact_distances": w_dist,
    "builder_pedigree": w_builder,
    "water_logging": w_water,
    "financials_appreciation": w_fin,
    "land_title_quality": w_legal
}

col_sb1, col_sb2 = st.sidebar.columns(2)
with col_sb1:
    if st.button("💾 Save Prefs", use_container_width=True):
        st.session_state.preferences["weights"] = active_weights
        st.session_state.preferences["search_center"]["radius_km"] = custom_radius
        save_user_preferences(st.session_state.preferences)
        st.sidebar.success("Saved!")
with col_sb2:
    if st.button("🔄 Defaults", use_container_width=True):
        st.session_state.preferences["weights"] = {
            "metro_proximity": 15, "traffic_integrity": 20, "exact_distances": 15,
            "builder_pedigree": 15, "water_logging": 10, "financials_appreciation": 15,
            "land_title_quality": 10
        }
        st.session_state.preferences["search_center"] = {"lat": 12.9325, "lng": 77.6850, "radius_km": 3.5}
        save_user_preferences(st.session_state.preferences)
        st.rerun()

# -------------------------------------------------------------
# Main Application Tabs
# -------------------------------------------------------------
tab_purchase, tab_rental, tab_nearby, tab_trends, tab_pedigree, tab_architecture = st.tabs([
    "🏢 Purchase / Investment",
    "🏡 Rental Discovery (Tab 2)",
    "🧭 Nearby Areas (Worth Considering)",
    "📊 Price Trends",
    "⚖️ Builder & Due Diligence",
    "⚙️ 5 PM Tracker & Downloads"
])

# =============================================================
# TAB 1: PURCHASE & INVESTMENT RADAR
# =============================================================
with tab_purchase:
    st.subheader("🗺️ Micro-Market Geofenced Radar (Bellandur • Green Glen • Gurukul)")
    st.caption("Allowed Green Zones are protected. Red Zones (Panathur Choke Corridor) receive an instant -50 points penalty.")

    # ---------------------------------------------------------
    # AREA ZONING & CUSTOM PINNING CONTROLS
    # ---------------------------------------------------------
    corridor_mode = st.radio(
        "Zoning & Radar Check Vicinity Mode:",
        [
            "🟢 Default Corridor (Bellandur Core • Green Glen • Gurukul vs Panathur Choke)",
            "🛠️ Custom Vicinities & Pins (Define Where to Check with Green Pins & Exclude with Red Pins)"
        ],
        horizontal=True,
        help="Default mode uses East Bengaluru corridor boundaries. Custom mode allows defining target areas anywhere across Bengaluru via custom Green & Red pins."
    )

    with st.expander("📍 Custom Area Pinning & Geofence Manager (Add Green / Red Pins)", expanded=(corridor_mode.startswith("🛠️"))):
        st.markdown("""
        Customize where the radar performs its property check:
        - 🟢 **Green Pins**: Target vicinities where check is to be done (allowed safe zones).
        - 🔴 **Red Pins**: Bottlenecks / choke areas to heavily penalize or exclude (-50 pts).
        """)

        c_pin_col1, c_pin_col2 = st.columns(2)
        with c_pin_col1:
            st.markdown("##### 🟢 Active Green Pins (Target Check Areas)")
            active_gp = st.session_state.custom_zones.get("green_pins", [])
            if not active_gp:
                st.info("No active green pins. Click below or tap map to add.")
            for i, gp in enumerate(active_gp):
                gp_c1, gp_c2 = st.columns([4, 1])
                with gp_c1:
                    st.markdown(f"**{gp['name']}** (`{gp['lat']:.4f}, {gp['lng']:.4f}`) - Radius: `{gp['radius_meters']}m`")
                with gp_c2:
                    if st.button("🗑️", key=f"del_gp_{gp.get('id', i)}_{i}", help="Delete Green Pin"):
                        st.session_state.custom_zones["green_pins"].pop(i)
                        save_custom_zones(st.session_state.custom_zones)
                        st.rerun()

        with c_pin_col2:
            st.markdown("##### 🔴 Active Red Pins (Excluded Choke Points)")
            active_rp = st.session_state.custom_zones.get("red_pins", [])
            if not active_rp:
                st.info("No active red pins. Click below or tap map to add.")
            for i, rp in enumerate(active_rp):
                rp_c1, rp_c2 = st.columns([4, 1])
                with rp_c1:
                    st.markdown(f"**{rp['name']}** (`{rp['lat']:.4f}, {rp['lng']:.4f}`) - Radius: `{rp['radius_meters']}m` (Penalty: `{rp.get('penalty_points', -50)}` pts)")
                with rp_c2:
                    if st.button("🗑️", key=f"del_rp_{rp.get('id', i)}_{i}", help="Delete Red Pin"):
                        st.session_state.custom_zones["red_pins"].pop(i)
                        save_custom_zones(st.session_state.custom_zones)
                        st.rerun()

        st.markdown("---")
        st.markdown("##### ➕ Add New Custom Vicinity Pin")

        pin_presets = {
            "-- Choose Bengaluru Landmark Preset or Enter Custom --": None,
            "Bellandur Core Grid": (12.9325, 77.6795),
            "Green Glen Layout": (12.9288, 77.6750),
            "Kadubeesanahalli / Gurukul": (12.9390, 77.6950),
            "Panathur Railway Underpass Choke": (12.9335, 77.7045),
            "Panathur Main Road Choke": (12.9360, 77.7085),
            "Sarjapur Road / Kaikondrahalli Lake": (12.9140, 77.6710),
            "HSR Layout Sector 1 / 2": (12.9110, 77.6520),
            "Outer Ring Road Ecospace": (12.9260, 77.6830),
            "Marathahalli Bridge Junction": (12.9560, 77.7010),
            "Silk Board Junction": (12.9175, 77.6235),
            "Carmelaram Railway Gate Choke": (12.9105, 77.7015),
            "Varthur Kodi Junction": (12.9420, 77.7450),
            "Whitefield Hope Farm": (12.9830, 77.7510)
        }

        form_c1, form_c2 = st.columns(2)
        with form_c1:
            pin_type = st.radio("Pin Type", ["🟢 Green Pin (Target Area to Check)", "🔴 Red Pin (Excluded / Blacklist Choke)"], horizontal=True)
            preset_choice = st.selectbox("Landmark Preset", list(pin_presets.keys()))
            default_name = preset_choice if preset_choice != "-- Choose Bengaluru Landmark Preset or Enter Custom --" else "Custom Bengaluru Vicinity"
            pin_name = st.text_input("Pin Name / Label", value=default_name)

        with form_c2:
            if preset_choice and pin_presets[preset_choice]:
                p_lat, p_lng = pin_presets[preset_choice]
            else:
                p_lat = search_center.get("lat", 12.9325)
                p_lng = search_center.get("lng", 77.6850)

            in_lat = st.number_input("Latitude", value=float(p_lat), format="%.5f")
            in_lng = st.number_input("Longitude", value=float(p_lng), format="%.5f")
            default_rad = 1200 if "Green" in pin_type else 800
            in_radius = st.slider("Zone Radius (meters)", 300, 5000, default_rad, step=100)
            in_penalty = -50 if "Red" in pin_type else 0

        action_c1, action_c2, action_c3 = st.columns([2, 1, 1])
        with action_c1:
            if st.button("➕ Add Pin to Radar Vicinity", use_container_width=True):
                new_id = f"pin_{int(datetime.now().timestamp())}"
                if "Green" in pin_type:
                    st.session_state.custom_zones["green_pins"].append({
                        "id": new_id,
                        "name": pin_name,
                        "lat": in_lat,
                        "lng": in_lng,
                        "radius_meters": in_radius,
                        "description": "User defined target check area"
                    })
                else:
                    st.session_state.custom_zones["red_pins"].append({
                        "id": new_id,
                        "name": pin_name,
                        "lat": in_lat,
                        "lng": in_lng,
                        "radius_meters": in_radius,
                        "penalty_points": in_penalty,
                        "reason": "User defined traffic choke point"
                    })
                save_custom_zones(st.session_state.custom_zones)
                st.success(f"Added {pin_name}!")
                st.rerun()

        with action_c2:
            if st.button("💾 Save Custom Pins", use_container_width=True):
                save_custom_zones(st.session_state.custom_zones)
                st.success("Custom pins persisted to disk!")

        with action_c3:
            if st.button("🔄 Reset Corridor", use_container_width=True):
                st.session_state.custom_zones = {
                    "use_custom": False,
                    "green_pins": [
                        {"id": "gp_1", "name": "Bellandur Core Grid", "lat": 12.9325, "lng": 77.6795, "radius_meters": 1300},
                        {"id": "gp_2", "name": "Green Glen Layout", "lat": 12.9288, "lng": 77.6750, "radius_meters": 900},
                        {"id": "gp_3", "name": "Kadubeesanahalli (Gurukul)", "lat": 12.9390, "lng": 77.6950, "radius_meters": 1100}
                    ],
                    "red_pins": [
                        {"id": "rp_1", "name": "Panathur Main Road Choke", "lat": 12.9360, "lng": 77.7085, "radius_meters": 1000, "penalty_points": -50},
                        {"id": "rp_2", "name": "Panathur Railway Underpass", "lat": 12.9335, "lng": 77.7045, "radius_meters": 550, "penalty_points": -50}
                    ]
                }
                save_custom_zones(st.session_state.custom_zones)
                st.rerun()

    # Active pins for live scoring
    active_green = st.session_state.custom_zones.get("green_pins", [])
    active_red = st.session_state.custom_zones.get("red_pins", [])

    # Calculate dynamic scores for all properties
    scored_properties = []
    for p in properties:
        p_copy = dict(p)
        # Check against active custom Red & Green pins first
        zone_status, zone_label, zone_penalty = check_custom_pins(p["lat"], p["lng"], active_green, active_red)

        if zone_status == "Red":
            p_copy["zone_type"] = "Red"
            p_copy["panathur_routing"] = True
            p_copy["zone_notes"] = f"Flagged in Excluded Red Zone: {zone_label}"
        elif zone_status == "Green":
            p_copy["zone_type"] = "Green"
            p_copy["panathur_routing"] = False
            p_copy["zone_notes"] = f"In Target Green Zone: {zone_label}"
        else:
            if corridor_mode.startswith("🟢"):
                # Use default polygon boundary
                def_status, def_name, def_pen = check_zone_membership(p["lat"], p["lng"], market_zones)
                p_copy["zone_type"] = def_status
                p_copy["panathur_routing"] = (def_status == "Red")
                p_copy["zone_notes"] = def_name
            else:
                p_copy["zone_type"] = "Neutral"
                p_copy["panathur_routing"] = False
                p_copy["zone_notes"] = "Outside Configured Green Pins"

        breakdown = compute_property_match_score(p_copy, weights=active_weights)
        p_copy.update(breakdown)
        scored_properties.append(p_copy)

    # Filter Bar with Age, Rating & Budget Filters
    f_c1, f_c2, f_c3, f_c4, f_c5 = st.columns([1, 1, 1, 1, 1])
    with f_c1:
        zone_filter = st.selectbox(
            "Zone Filter",
            ["All Zones", "Green Target Pins Only (Safe Vicinities)", "Red Zones (Excluded Choke Points)"]
        )
    with f_c2:
        builder_filter = st.selectbox(
            "Builder Tier",
            ["All Developers", "Tier 1 (Top 10 Premier)", "Tier 2 (Secondary)", "Local"]
        )
    with f_c3:
        age_filter = st.selectbox(
            "Property Age",
            ["Any Property Age", "Brand New (0-3 yrs)", "Prime Modern (4-7 yrs)", "Mature Gated (8+ yrs)"]
        )
    with f_c4:
        min_rating_filter = st.selectbox(
            "Min Resident Rating",
            ["Any Rating", "4.5★ & Above (Top Rated)", "4.0★ & Above", "3.5★ & Above"]
        )
    with f_c5:
        budget_filter = st.slider("Max Budget (₹ Cr)", 0.5, 7.0, 7.0, step=0.25)

    # Filter properties
    filtered_props = []
    for p in scored_properties:
        if zone_filter == "Green Target Pins Only (Safe Vicinities)" and p["zone_type"] != "Green":
            continue
        if zone_filter == "Red Zones (Excluded Choke Points)" and p["zone_type"] != "Red":
            continue
        if builder_filter != "All Developers" and builder_filter.split()[0].lower() not in p["builder_tier_label"].lower():
            continue
        if age_filter == "Brand New (0-3 yrs)" and p.get("age_years", 0) > 3:
            continue
        if age_filter == "Prime Modern (4-7 yrs)" and not (4 <= p.get("age_years", 0) <= 7):
            continue
        if age_filter == "Mature Gated (8+ yrs)" and p.get("age_years", 0) < 8:
            continue
        if min_rating_filter == "4.5★ & Above (Top Rated)" and p.get("resident_rating", 0) < 4.5:
            continue
        if min_rating_filter == "4.0★ & Above" and p.get("resident_rating", 0) < 4.0:
            continue
        if min_rating_filter == "3.5★ & Above" and p.get("resident_rating", 0) < 3.5:
            continue
        if p["total_price_cr"] > budget_filter:
            continue
        filtered_props.append(p)

    filtered_props.sort(key=lambda x: x["final_match_score"], reverse=True)

    # ---------------------------------------------------------
    # FOLIUM / GOOGLE MAPS INTEGRATION
    # ---------------------------------------------------------
    center_lat = search_center.get("lat", 12.9325)
    center_lng = search_center.get("lng", 77.6850)

    # Configure Map Tile Layer based on user selection
    if "Google Maps (Roadmap)" in map_provider:
        tiles_url = "https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}"
        tiles_attr = "Google Maps"
    elif "Google Maps (Satellite" in map_provider:
        tiles_url = "https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}"
        tiles_attr = "Google Maps Satellite"
    elif "Google Maps (Terrain)" in map_provider:
        tiles_url = "https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}"
        tiles_attr = "Google Maps Terrain"
    elif "OpenStreetMap" in map_provider:
        tiles_url = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        tiles_attr = "&copy; OpenStreetMap contributors"
    else:
        tiles_url = "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
        tiles_attr = "&copy; CartoDB Positron"

    m = folium.Map(
        location=[center_lat, center_lng],
        zoom_start=13,
        tiles=tiles_url,
        attr=tiles_attr,
        control_scale=True
    )

    # Add Default Polygons if in Default Corridor mode
    if corridor_mode.startswith("🟢"):
        for gz in market_zones.get("green_zones", []):
            poly = gz.get("polygon")
            if poly:
                folium.Polygon(
                    locations=poly,
                    color="#10B981",
                    weight=2,
                    fill=True,
                    fill_color="#10B981",
                    fill_opacity=0.15,
                    tooltip=f"<b>Allowed Green Zone</b>: {gz['name']}"
                ).add_to(m)

        for rz in market_zones.get("red_zones", []):
            poly = rz.get("polygon")
            if poly:
                folium.Polygon(
                    locations=poly,
                    color="#EF4444",
                    weight=3,
                    fill=True,
                    fill_color="#EF4444",
                    fill_opacity=0.25,
                    tooltip=f"<b>Strict Red Zone (Choke Point)</b>: {rz['name']}<br>⚠️ Penalty: {rz['penalty_points']} pts"
                ).add_to(m)

    # Render All Active Custom Green Pins on Map
    for gp in active_green:
        folium.Circle(
            location=[gp["lat"], gp["lng"]],
            radius=gp["radius_meters"],
            color="#10B981",
            weight=2,
            fill=True,
            fill_color="#10B981",
            fill_opacity=0.20,
            tooltip=f"🟢 Target Check Area: {gp['name']} ({gp['radius_meters']}m radius)"
        ).add_to(m)
        folium.Marker(
            location=[gp["lat"], gp["lng"]],
            popup=f"<b>🟢 Target Check Area</b><br>{gp['name']}<br>Radius: {gp['radius_meters']}m",
            tooltip=f"🟢 {gp['name']}",
            icon=folium.Icon(color="green", icon="check-circle", prefix="fa")
        ).add_to(m)

    # Render All Active Custom Red Pins on Map
    for rp in active_red:
        folium.Circle(
            location=[rp["lat"], rp["lng"]],
            radius=rp["radius_meters"],
            color="#EF4444",
            weight=2,
            fill=True,
            fill_color="#EF4444",
            fill_opacity=0.28,
            dash_array="6, 6",
            tooltip=f"🔴 Excluded Choke Point: {rp['name']} (Penalty: {rp.get('penalty_points', -50)} pts)"
        ).add_to(m)
        folium.Marker(
            location=[rp["lat"], rp["lng"]],
            popup=f"<b>🔴 Excluded Choke Zone</b><br>{rp['name']}<br>Radius: {rp['radius_meters']}m<br>Penalty: {rp.get('penalty_points', -50)} pts",
            tooltip=f"🔴 {rp['name']}",
            icon=folium.Icon(color="red", icon="ban", prefix="fa")
        ).add_to(m)

    # Add Metro Line Phase 2A Polyline
    metro_coords = [
        [12.9170, 77.6740],
        [12.9275, 77.6825],
        [12.9380, 77.6950],
        [12.9510, 77.7020]
    ]
    folium.PolyLine(
        locations=metro_coords,
        color="#3B82F6",
        weight=4,
        dash_array="6, 6",
        tooltip="ORR Blue Line Metro Phase 2A (Silk Board - KR Puram)"
    ).add_to(m)

    # Add Metro Stations
    for stn in anchors.get("metro_anchors", []):
        folium.Marker(
            location=[stn["lat"], stn["lng"]],
            popup=f"<b>🚇 {stn['name']}</b><br>{stn['line']}",
            tooltip=f"🚇 {stn['name']}",
            icon=folium.Icon(color="blue", icon="subway", prefix="fa")
        ).add_to(m)

    # Add Key Anchors
    for office in anchors.get("office_anchors", []):
        folium.Marker(
            location=[office["lat"], office["lng"]],
            popup=f"<b>💼 {office['name']}</b>",
            tooltip=f"💼 {office['name']}",
            icon=folium.Icon(color="purple", icon="briefcase", prefix="fa")
        ).add_to(m)

    for school in anchors.get("school_anchors", []):
        folium.Marker(
            location=[school["lat"], school["lng"]],
            popup=f"<b>🎓 {school['name']}</b>",
            tooltip=f"🎓 {school['name']}",
            icon=folium.Icon(color="cadetblue", icon="graduation-cap", prefix="fa")
        ).add_to(m)

    # Add Property Pins with Age & Match Score
    for prop in filtered_props:
        score = prop["final_match_score"]
        pin_color = "green" if score >= 80 else ("orange" if score >= 60 else "red")
        pin_icon = "star" if score >= 80 else ("home" if score >= 60 else "exclamation-triangle")

        popup_html = f"""
        <div style="font-family: sans-serif; width: 230px;">
            <h4 style="margin: 0; color: #0F172A;">{prop['name']}</h4>
            <p style="margin: 3px 0; font-size: 12px; color: #475569;"><b>Builder:</b> {prop['builder']} ({prop['builder_tier']})</p>
            <p style="margin: 3px 0; font-size: 12px; color: #B45309;"><b>⭐ Resident Rating:</b> {prop.get('resident_rating', 4.5)} / 5.0</p>
            <p style="margin: 3px 0; font-size: 12px; color: #312E81;"><b>Age:</b> {prop.get('age_years', 5)} Yrs ({prop.get('year_built', 2021)})</p>
            <p style="margin: 3px 0; font-size: 13px; font-weight: bold; color: {'#16A34A' if score >= 75 else '#DC2626'};">
                Radar Match Score: {score} / 100
            </p>
            <p style="margin: 3px 0; font-size: 12px;"><b>Rate:</b> ₹{prop['price_per_sqft']:,} / sqft (~₹{prop['total_price_cr']} Cr)</p>
            <a href="https://www.google.com/maps/search/?api=1&query={prop['lat']},{prop['lng']}" target="_blank" style="font-size: 11px; color: #0D9488; font-weight: bold;">
                📍 Open in Google Maps ↗
            </a>
        </div>
        """

        folium.Marker(
            location=[prop["lat"], prop["lng"]],
            popup=folium.Popup(popup_html, max_width=260),
            tooltip=f"{prop['name']} - Score: {score} | ⭐ {prop.get('resident_rating', 4.5)}",
            icon=folium.Icon(color=pin_color, icon=pin_icon, prefix="fa")
        ).add_to(m)

    # Optionally Plot Nearby Worth Considering Properties as Purple Pins
    if show_nearby_on_map:
        for nb in nearby_properties:
            nb_html = f"""
            <div style="font-family: sans-serif; width: 230px;">
                <h4 style="margin: 0; color: #6D28D9;">🧭 Nearby: {nb['name']}</h4>
                <p style="margin: 3px 0; font-size: 12px; color: #475569;"><b>Area:</b> {nb['micro_market']}</p>
                <p style="margin: 3px 0; font-size: 12px; color: #B45309;"><b>⭐ Rating:</b> {nb.get('resident_rating', 4.5)} / 5.0</p>
                <p style="margin: 3px 0; font-size: 12px;"><b>Rate:</b> ₹{nb['price_per_sqft']:,}/sqft (~₹{nb['total_price_cr']} Cr)</p>
                <p style="margin: 3px 0; font-size: 11px; color: #64748B;"><b>Dist to Bellandur:</b> {nb['distance_to_bellandur_km']} km</p>
                <a href="https://www.google.com/maps/search/?api=1&query={nb['lat']},{nb['lng']}" target="_blank" style="font-size: 11px; color: #6D28D9; font-weight: bold;">
                    📍 Open in Google Maps ↗
                </a>
            </div>
            """
            folium.Marker(
                location=[nb["lat"], nb["lng"]],
                popup=folium.Popup(nb_html, max_width=250),
                tooltip=f"Nearby: {nb['name']} ({nb['micro_market']})",
                icon=folium.Icon(color="darkpurple", icon="bookmark", prefix="fa")
            ).add_to(m)

    # Render Folium Map (Use container width for responsive mobile view)
    map_col, info_col = st.columns([7, 3])
    with map_col:
        map_output = st_folium(m, use_container_width=True, height=450, returned_objects=["last_clicked"])

    with info_col:
        st.markdown("#### 🗺️ Map Guide & Quick Pins")
        st.markdown(f"**Layer:** `{map_provider}`")
        st.markdown("""
        - 🟢 **Green Zones / Pins**: Target radar check areas
        - 🔴 **Red Zones / Pins**: Choke points / excluded (-50 pts)
        - 🟣 **Purple Pins**: Nearby Worth-Considering
        - 🚇 **Blue Line**: ORR Metro Alignment
        - 📍 Tap map or any pin to inspect/interact.
        """)

        # Fallback Direct Google Maps link for mobile users
        gmaps_corridor_url = f"https://www.google.com/maps/search/?api=1&query=Green+Glen+Layout+Bellandur+Bengaluru"
        st.markdown(f"""
        <a href="{gmaps_corridor_url}" target="_blank" style="text-decoration: none;">
            <div style="background-color: #0F172A; border: 1px solid #334155; color: #38BDF8; text-align: center; padding: 7px; border-radius: 8px; font-weight: 600; font-size: 0.82rem; margin-bottom: 8px;">
                📍 Open Corridor in Google Maps ↗
            </div>
        </a>
        """, unsafe_allow_html=True)

        if map_output and map_output.get("last_clicked"):
            lat_c = map_output["last_clicked"]["lat"]
            lng_c = map_output["last_clicked"]["lng"]
            st.markdown(f"""
            <div style="background:#1E293B; border:1px solid #0D9488; border-radius:8px; padding:8px; margin-bottom:8px;">
                <b style="color:#38BDF8; font-size:0.85rem;">📍 Map Coordinate Selected:</b><br>
                <code style="font-size:0.8rem;">Lat: {lat_c:.4f}, Lng: {lng_c:.4f}</code>
            </div>
            """, unsafe_allow_html=True)

            col_q_g, col_q_r = st.columns(2)
            with col_q_g:
                if st.button("🟢 Pin as Green Target", key="quick_add_green_pin", use_container_width=True):
                    new_id = f"gp_{int(datetime.now().timestamp())}"
                    st.session_state.custom_zones["green_pins"].append({
                        "id": new_id,
                        "name": f"Target Area ({lat_c:.3f}, {lng_c:.3f})",
                        "lat": lat_c,
                        "lng": lng_c,
                        "radius_meters": 1200,
                        "description": "User defined target check area"
                    })
                    save_custom_zones(st.session_state.custom_zones)
                    st.toast("🟢 Added new Green Pin target area!")
                    st.rerun()

            with col_q_r:
                if st.button("🔴 Pin as Red Choke", key="quick_add_red_pin", use_container_width=True):
                    new_id = f"rp_{int(datetime.now().timestamp())}"
                    st.session_state.custom_zones["red_pins"].append({
                        "id": new_id,
                        "name": f"Choke Point ({lat_c:.3f}, {lng_c:.3f})",
                        "lat": lat_c,
                        "lng": lng_c,
                        "radius_meters": 800,
                        "penalty_points": -50,
                        "reason": "User defined traffic choke point"
                    })
                    save_custom_zones(st.session_state.custom_zones)
                    st.toast("🔴 Added new Red Pin exclusion zone!")
                    st.rerun()

            if st.button("🎯 Set as Radar Center", use_container_width=True):
                st.session_state.preferences["search_center"]["lat"] = lat_c
                st.session_state.preferences["search_center"]["lng"] = lng_c
                save_user_preferences(st.session_state.preferences)
                st.rerun()

    # =========================================================
    # COMPREHENSIVE COMPARISON TABLE (PURCHASE PROPERTIES)
    # =========================================================
    st.markdown("---")
    st.subheader("📊 Comprehensive Purchase Comparison Table (All Parameters & Ratings)")
    st.caption("Side-by-side comparison across all financial, structural, age, maintenance, rating, and legal parameters.")

    table_data = []
    for p in filtered_props:
        base_cost = p.get("base_cost_inr", int(p["total_price_cr"] * 10000000))
        stamp_duty = round(base_cost * (p.get("stamp_duty_pct", 5.6) / 100.0))
        reg_fee = round(base_cost * (p.get("registration_fee_pct", 1.0) / 100.0))
        legal_fee = p.get("legal_advocate_fees_inr", 45000)
        khata_fee = p.get("khata_transfer_fee_inr", 15000)
        corpus_fund = p.get("corpus_sinking_fund_inr", 200000)
        interiors = p.get("interiors_estimate_inr", 1500000)
        m_maint = p.get("monthly_maintenance_inr", int(p.get("maintenance_sqft", 4.0) * p.get("avg_sqft", 1500)))
        a_maint = m_maint * 12
        
        down_payment_20pct = round(base_cost * 0.20)
        upfront_advance_required = down_payment_20pct + stamp_duty + reg_fee + legal_fee + khata_fee + corpus_fund
        total_ownership_cost = base_cost + stamp_duty + reg_fee + legal_fee + khata_fee + corpus_fund + interiors + a_maint
        
        complaints_short = "; ".join(p.get("common_complaints", []))

        table_data.append({
            "Property Name": p["name"],
            "Builder": p["builder"],
            "Tier": p["builder_tier"],
            "Micro-Market": p["micro_market"],
            "Zone": "🟢 Green" if p["zone_type"] == "Green" else "🔴 Red (Choke)",
            "Age (Yrs)": f"{p.get('age_years', 8)} yrs ({p.get('year_built', 2018)})",
            "Resident Rating": f"⭐ {p.get('resident_rating', 4.5)} / 5",
            "Feedback Score": f"{p.get('feedback_score', 90)} / 100",
            "Match Score": f"{p['final_match_score']} / 100",
            "Rate / sqft": f"₹{p['price_per_sqft']:,}",
            "Config": p["avg_bhk"],
            "Area (sqft)": p["avg_sqft"],
            "Base Price (Cr)": f"₹{p['total_price_cr']} Cr",
            "Monthly Maint": f"₹{m_maint:,}",
            "Annual Maint": f"₹{a_maint:,}",
            "Upfront Cash Req. (Lakhs)": f"₹{round(upfront_advance_required/100000, 2)} L",
            "Total Cost of Ownership (Cr)": f"₹{round(total_ownership_cost/10000000, 3)} Cr",
            "Metro Dist (km)": f"{p['dist_metro_km']} km",
            "PTP / Ecospace Dist (km)": f"{p['dist_office_km']} km",
            "Land Title": p["land_title"],
            "Validation URL": p.get("validation_url", "https://rera.karnataka.gov.in"),
            "RERA Portal Link": p.get("rera_portal_url", "https://rera.karnataka.gov.in"),
            "Common Complaints": complaints_short
        })

    df_purchase_table = pd.DataFrame(table_data)
    st.dataframe(df_purchase_table, use_container_width=True, hide_index=True)

    # Interactive Side-by-Side Property Head-to-Head Comparison
    with st.expander("🔍 Interactive Head-to-Head Property Comparator (Select 2-4 Properties)"):
        prop_options = [p["name"] for p in filtered_props]
        selected_for_compare = st.multiselect(
            "Select Properties to Compare Side-by-Side",
            options=prop_options,
            default=prop_options[:2] if len(prop_options) >= 2 else prop_options
        )

        if selected_for_compare:
            compare_records = []
            for name in selected_for_compare:
                p = next((item for item in filtered_props if item["name"] == name), None)
                if p:
                    base_cost = p.get("base_cost_inr", int(p["total_price_cr"] * 10000000))
                    stamp_duty = round(base_cost * (p.get("stamp_duty_pct", 5.6) / 100.0))
                    reg_fee = round(base_cost * (p.get("registration_fee_pct", 1.0) / 100.0))
                    legal_fee = p.get("legal_advocate_fees_inr", 45000)
                    khata_fee = p.get("khata_transfer_fee_inr", 15000)
                    corpus_fund = p.get("corpus_sinking_fund_inr", 200000)
                    interiors = p.get("interiors_estimate_inr", 1500000)
                    m_maint = p.get("monthly_maintenance_inr", int(p.get("maintenance_sqft", 4.0) * p.get("avg_sqft", 1500)))
                    a_maint = m_maint * 12
                    down_payment_20pct = round(base_cost * 0.20)
                    upfront_advance_required = down_payment_20pct + stamp_duty + reg_fee + legal_fee + khata_fee + corpus_fund
                    total_ownership_cost = base_cost + stamp_duty + reg_fee + legal_fee + khata_fee + corpus_fund + interiors + a_maint
                    
                    compare_records.append({
                        "Metric / Parameter": "Builder & Hierarchy",
                        name: f"{p['builder']} ({p['builder_tier']})"
                    })
                    compare_records.append({
                        "Metric / Parameter": "Micro-Market Location",
                        name: p["micro_market"]
                    })
                    compare_records.append({
                        "Metric / Parameter": "Traffic Route Status",
                        name: "🟢 Panathur-Free Green Route" if not p["panathur_routing"] else "🔴 Panathur Bottleneck (-50 pts)"
                    })
                    compare_records.append({
                        "Metric / Parameter": "Property Age & Year Built",
                        name: f"{p.get('age_years', 8)} Years (Built {p.get('year_built', 2018)})"
                    })
                    compare_records.append({
                        "Metric / Parameter": "⭐ Resident Rating",
                        name: f"⭐ {p.get('resident_rating', 4.5)} / 5.0 (Score: {p.get('feedback_score', 90)}/100)"
                    })
                    compare_records.append({
                        "Metric / Parameter": "Radar Match Score",
                        name: f"{p['final_match_score']} / 100"
                    })
                    compare_records.append({
                        "Metric / Parameter": "Rate per Sqft",
                        name: f"₹{p['price_per_sqft']:,} / sqft"
                    })
                    compare_records.append({
                        "Metric / Parameter": "Average Config & Area",
                        name: f"{p['avg_bhk']} ({p['avg_sqft']} sqft)"
                    })
                    compare_records.append({
                        "Metric / Parameter": "Base Flat Agreement Price",
                        name: f"₹{p['total_price_cr']} Cr (₹{base_cost:,})"
                    })
                    compare_records.append({
                        "Metric / Parameter": "Monthly / Annual Maintenance",
                        name: f"₹{m_maint:,} / mo (₹{a_maint:,} / yr)"
                    })
                    compare_records.append({
                        "Metric / Parameter": "Stamp Duty & Registration (6.6%)",
                        name: f"₹{(stamp_duty + reg_fee):,}"
                    })
                    compare_records.append({
                        "Metric / Parameter": "👉 Upfront Advance Cash Required (20% + Reg)",
                        name: f"₹{round(upfront_advance_required/100000, 2)} Lakhs (₹{upfront_advance_required:,})"
                    })
                    compare_records.append({
                        "Metric / Parameter": "🏆 Grand Total Cost of Ownership (TOC)",
                        name: f"₹{round(total_ownership_cost/10000000, 3)} Cr (₹{total_ownership_cost:,})"
                    })
                    compare_records.append({
                        "Metric / Parameter": "Metro Blue Line Distance",
                        name: f"{p['dist_metro_km']} km"
                    })
                    compare_records.append({
                        "Metric / Parameter": "PTP / Ecospace Distance",
                        name: f"{p['dist_office_km']} km"
                    })
                    compare_records.append({
                        "Metric / Parameter": "Water Source Security",
                        name: p["water_source"]
                    })
                    compare_records.append({
                        "Metric / Parameter": "⚠️ Resident Complaints / Warnings",
                        name: "; ".join(p.get("common_complaints", []))
                    })

            # Merge records into dataframe
            df_comp = pd.DataFrame(compare_records)
            df_comp_pivot = df_comp.groupby("Metric / Parameter", as_index=False).first()
            st.dataframe(df_comp_pivot, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader(f"📋 Evaluated Purchase Property Cards ({len(filtered_props)} Matching)")

    # ---------------------------------------------------------
    # PROPERTY CARDS WITH AGE, RATINGS, COMPLAINTS & TOC
    # ---------------------------------------------------------
    for prop in filtered_props:
        is_red = prop["panathur_routing"]
        score = prop["final_match_score"]
        border_color = "#DC2626" if is_red else ("#10B981" if score >= 80 else "#F59E0B")
        
        # Financial Calculations
        base_cost = prop.get("base_cost_inr", int(prop["total_price_cr"] * 10000000))
        stamp_duty = round(base_cost * (prop.get("stamp_duty_pct", 5.6) / 100.0))
        reg_fee = round(base_cost * (prop.get("registration_fee_pct", 1.0) / 100.0))
        legal_fee = prop.get("legal_advocate_fees_inr", 45000)
        khata_fee = prop.get("khata_transfer_fee_inr", 15000)
        corpus_fund = prop.get("corpus_sinking_fund_inr", 200000)
        interiors = prop.get("interiors_estimate_inr", 1500000)
        
        m_maint = prop.get("monthly_maintenance_inr", int(prop.get("maintenance_sqft", 4.0) * prop.get("avg_sqft", 1500)))
        a_maint = m_maint * 12
        
        down_payment_20pct = round(base_cost * 0.20)
        upfront_advance_required = down_payment_20pct + stamp_duty + reg_fee + legal_fee + khata_fee + corpus_fund
        total_ownership_cost = base_cost + stamp_duty + reg_fee + legal_fee + khata_fee + corpus_fund + interiors + a_maint
        total_ownership_cost_cr = round(total_ownership_cost / 10000000, 3)

        with st.container():
            st.markdown(f"""
            <div class="property-card" style="border-left: 6px solid {border_color};">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 8px;">
                    <div>
                        <h3 style="margin: 0; color: #F8FAFC; font-size: 1.3rem;">{prop['name']}</h3>
                        <div style="margin-top: 4px;">
                            <span class="{ 'badge-red' if is_red else 'badge-green' }">
                                {'⚠️ Panathur Bottleneck (-50 pts)' if is_red else '🛡️ Green Route Compliant'}
                            </span>
                            <span class="badge-rating">
                                ⭐ {prop.get('resident_rating', 4.5)} / 5.0 (Score: {prop.get('feedback_score', 90)}/100)
                            </span>
                            <span class="badge-age">
                                ⏳ Age: {prop.get('age_years', 8)} Years (Built {prop.get('year_built', 2018)}) • {prop.get('age_category', '')}
                            </span>
                        </div>
                        <p style="margin: 5px 0 0 0; color: #94A3B8; font-size: 0.9rem;">
                            <b>Developer:</b> {prop['builder']} &nbsp;|&nbsp; 
                            <b>Hierarchy:</b> <span style="color: #38BDF8;">{prop['builder_tier_label']}</span> &nbsp;|&nbsp; 
                            <b>Micro-Market:</b> {prop['micro_market']}
                        </p>
                    </div>
                    <div style="text-align: right;">
                        <span style="font-size: 1.7rem; font-weight: 800; color: {'#EF4444' if is_red else ('#10B981' if score >= 80 else '#F59E0B')};">
                            {score}
                        </span>
                        <span style="color: #64748B; font-size: 0.95rem;"> / 100</span>
                        <div style="font-size: 0.8rem; color: #94A3B8;">Radar Match Score</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            p_col1, p_col2, p_chart = st.columns([1, 1, 1])

            with p_col1:
                st.markdown("**💰 Pricing, Config & Age:**")
                st.markdown(f"- **Property Age:** `Built {prop.get('year_built', 2018)} ({prop.get('age_years', 8)} yrs)`")
                st.markdown(f"- **Rate:** ₹{prop['price_per_sqft']:,} / sqft")
                st.markdown(f"- **Avg Config:** {prop['avg_bhk']} ({prop['avg_sqft']} sqft)")
                st.markdown(f"- **Base Flat Price:** `₹{prop['total_price_cr']} Cr` (₹{base_cost:,})")
                st.markdown(f"- **YoY Price Growth:** `+{prop['yoy_growth_pct']}%`")

            with p_col2:
                st.markdown("**🛠️ Maintenance & Connectivity:**")
                st.markdown(f"- **Monthly Maintenance:** `₹{m_maint:,} / month` (₹{prop['maintenance_sqft']}/sqft)")
                st.markdown(f"- **Annual Maintenance:** `₹{a_maint:,} / year`")
                st.markdown(f"- **Metro Blue Line:** `{prop['dist_metro_km']} km`")
                st.markdown(f"- **Tech Parks (Ecospace / PTP):** `{prop['dist_office_km']} km`")
                st.markdown(f"- **Land Title:** `{prop['land_title']}`")

            with p_chart:
                # 1-Click Google Maps Deep Link
                gmaps_pin_url = f"https://www.google.com/maps/search/?api=1&query={prop['lat']},{prop['lng']}"
                st.markdown(f"""
                <a href="{gmaps_pin_url}" target="_blank" style="text-decoration: none;">
                    <div style="background-color: #0D9488; color: white; text-align: center; padding: 8px 12px; border-radius: 8px; font-weight: 700; font-size: 0.9rem; margin-bottom: 6px;">
                        📍 Open Exact Pin in Google Maps ↗
                    </div>
                </a>
                """, unsafe_allow_html=True)

                val_url = prop.get("validation_url", "https://rera.karnataka.gov.in")
                rera_url = prop.get("rera_portal_url", "https://rera.karnataka.gov.in")
                st.markdown(f"""
                <div style="display: flex; gap: 6px; margin-bottom: 8px; flex-wrap: wrap;">
                    <a href="{val_url}" target="_blank" style="flex: 1; text-decoration: none; min-width: 130px;">
                        <div style="background-color: #1E3A8A; color: #BFDBFE; text-align: center; padding: 7px 8px; border-radius: 6px; font-weight: 700; font-size: 0.78rem; border: 1px solid #3B82F6;">
                            🔗 Verify Official Post / Site ↗
                        </div>
                    </a>
                    <a href="{rera_url}" target="_blank" style="flex: 1; text-decoration: none; min-width: 130px;">
                        <div style="background-color: #334155; color: #F1F5F9; text-align: center; padding: 7px 8px; border-radius: 6px; font-weight: 700; font-size: 0.78rem; border: 1px solid #64748B;">
                            📋 Karnataka RERA Portal ↗
                        </div>
                    </a>
                </div>
                """, unsafe_allow_html=True)

                st.markdown(f"""
                <div class="cost-box">
                    <div style="font-size: 0.85rem; color: #94A3B8;">Total Upfront Cash Required (20% + Reg)</div>
                    <div style="font-size: 1.3rem; font-weight: 800; color: #F59E0B;">₹{upfront_advance_required:,}</div>
                    <div style="font-size: 0.85rem; color: #94A3B8; margin-top: 4px;">Total Cost of Ownership (TOC)</div>
                    <div style="font-size: 1.3rem; font-weight: 800; color: #38BDF8;">₹{total_ownership_cost_cr} Cr <span style="font-size: 0.8rem; color: #64748B;">(₹{total_ownership_cost:,})</span></div>
                </div>
                """, unsafe_allow_html=True)

            # Resident Complaints & Feedback Box
            complaints = prop.get("common_complaints", [])
            ratings_bd = prop.get("rating_breakdown", {})
            st.markdown(f"""
            <div class="complaint-box">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                    <b style="color: #FDE68A;">⭐ Resident Feedback Score: {prop.get('feedback_score', 90)}/100</b>
                    <span style="font-size: 0.85rem; color: #CBD5E1;">
                        Construction: {ratings_bd.get('construction_quality', 4.5)}/5 | Maint: {ratings_bd.get('maintenance_amenities', 4.5)}/5 | Location: {ratings_bd.get('location_connectivity', 4.5)}/5 | Water: {ratings_bd.get('water_utilities', 4.5)}/5
                    </span>
                </div>
                <div style="margin-top: 6px; font-size: 0.88rem; color: #E2E8F0;">
                    <b>⚠️ Verified Common Complaints & Resident Warnings:</b>
                    <ul style="margin: 4px 0 0 16px; padding: 0;">
                        {''.join([f"<li>{c}</li>" for c in complaints])}
                    </ul>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Detailed Acquisition & Ownership Cost Expander
            with st.expander("💼 View Complete Legal, Registration, Advance & Ownership Cost Breakdown"):
                cost_t1, cost_t2 = st.columns(2)
                with cost_t1:
                    st.markdown("#### 🏛️ Government Registration & Legal Charges")
                    st.markdown(f"- **Base Flat Agreement Cost:** ₹{base_cost:,}")
                    st.markdown(f"- **Stamp Duty (5.6% Karnataka):** ₹{stamp_duty:,}")
                    st.markdown(f"- **Registration Fee (1.0% Govt):** ₹{reg_fee:,}")
                    st.markdown(f"- **Total Stamp Duty & Registration (6.6%):** `₹{(stamp_duty + reg_fee):,}`")
                    st.markdown(f"- **Advocate Legal Title & EC Vetting:** ₹{legal_fee:,}")
                    st.markdown(f"- **BBMP e-Aasthi Khata Transfer & Mutation:** ₹{khata_fee:,}")
                    st.markdown(f"- **One-time Society Sinking / Corpus Fund:** ₹{corpus_fund:,}")

                with cost_t2:
                    st.markdown("#### 💵 Advance Cash Required & Total Ownership (TOC)")
                    st.markdown(f"- **Bank Home Loan Down Payment (20%):** ₹{down_payment_20pct:,}")
                    st.markdown(f"- **Govt Registration & Taxes (Upfront 100% Cash):** ₹{(stamp_duty + reg_fee):,}")
                    st.markdown(f"- **Legal, Khata & Corpus (Upfront):** ₹{(legal_fee + khata_fee + corpus_fund):,}")
                    st.markdown(f"👉 **TOTAL UPFRONT CASH ADVANCE REQUIRED:** <b style='color:#F59E0B; font-size:1.1rem;'>₹{upfront_advance_required:,} (~₹{round(upfront_advance_required/100000, 2)} Lakhs)</b>", unsafe_allow_html=True)
                    st.markdown("---")
                    st.markdown(f"- **Interiors & Fit-out Provision (Est.):** ₹{interiors:,}")
                    st.markdown(f"- **1st Year Annual Maintenance:** ₹{a_maint:,}")
                    st.markdown(f"🏆 **GRAND TOTAL OWNERSHIP COST (TOC):** <b style='color:#38BDF8; font-size:1.2rem;'>₹{total_ownership_cost_cr} Cr (₹{total_ownership_cost:,})</b>", unsafe_allow_html=True)

            if is_red:
                st.error(f"🛑 **Bottleneck Penalty Warning:** {prop['traffic_notes']}")
            st.markdown("---")

# =============================================================
# TAB 2: RENTAL HOUSE DISCOVERY RADAR
# =============================================================
with tab_rental:
    st.subheader("🏡 Rental House Discovery Radar (Vicinity Configured)")
    st.caption("Compare prices across NoBroker, 99acres, MagicBricks, Housing.com, & Direct Owner with total maintenance, ratings, and common complaints.")

    r_col1, r_col2, r_col3, r_col4, r_col5 = st.columns([1, 1, 1, 1, 1])
    with r_col1:
        rent_vicinity = st.selectbox(
            "Rental Vicinity",
            ["All Vicinities", "Green Glen Layout", "Bellandur Core", "Kadubeesanahalli (Gurukul Side)", "Panathur Road"]
        )
    with r_col2:
        rent_bhk = st.selectbox("BHK", ["All BHKs", "2 BHK", "3 BHK", "4 BHK"])
    with r_col3:
        rent_age_filter = st.selectbox(
            "Rental Age",
            ["Any Age", "< 5 Years Old", "< 8 Years Old"]
        )
    with r_col4:
        rent_rating_filter = st.selectbox(
            "Min Rating",
            ["Any Rating", "4.5★ & Above", "4.0★ & Above"]
        )
    with r_col5:
        rent_budget = st.slider("Max Monthly Rent (₹)", 30000, 160000, 100000, step=5000)

    cb1, cb2 = st.columns(2)
    with cb1:
        exclude_panathur_rentals = st.checkbox("🚫 Zero-Panathur Bottlenecks Only", value=True)
    with cb2:
        direct_owner_only = st.checkbox("🔑 Direct Owner Only (0 Brokerage)", value=False)

    filtered_rentals = []
    for r in rental_properties:
        if rent_vicinity != "All Vicinities" and rent_vicinity.lower() not in r["micro_market"].lower():
            continue
        if rent_bhk != "All BHKs" and r["bhk"] != rent_bhk:
            continue
        if rent_age_filter == "< 5 Years Old" and r.get("age_years", 0) > 5:
            continue
        if rent_age_filter == "< 8 Years Old" and r.get("age_years", 0) > 8:
            continue
        if rent_rating_filter == "4.5★ & Above" and r.get("resident_rating", 0) < 4.5:
            continue
        if rent_rating_filter == "4.0★ & Above" and r.get("resident_rating", 0) < 4.0:
            continue
        if r["rent_pm"] > rent_budget:
            continue
        if exclude_panathur_rentals and not r["panathur_bottleneck_free"]:
            continue
        if direct_owner_only and r["contact"]["type"] != "Direct Owner":
            continue
        filtered_rentals.append(r)

    st.markdown(f"**Found {len(filtered_rentals)} Verified Rental Listings in Vicinity**")

    # =========================================================
    # COMPREHENSIVE RENTAL COMPARISON TABLE
    # =========================================================
    st.markdown("### 📊 Comprehensive Rental Comparison Table (All Parameters & Ratings)")
    st.caption("Side-by-side comparison of rent, maintenance, total monthly outflow, deposit, brokerages, ratings, and complaints.")

    rental_table_rows = []
    for r in filtered_rentals:
        rent_pm = r["rent_pm"]
        maint_pm = r["maintenance_pm"]
        tot_outflow = r.get("total_monthly_outflow", rent_pm + maint_pm)
        dep_inr = r.get("security_deposit_inr", rent_pm * r.get("security_deposit_months", 4))
        dep_interest_pm = round((dep_inr * 0.075) / 12)
        effective_monthly = tot_outflow + dep_interest_pm
        complaints_short = "; ".join(r.get("common_complaints", []))
        contact = r.get("contact", {})

        rental_table_rows.append({
            "Society Name": r["society_name"],
            "Unit Title": r["unit_title"],
            "Micro-Market": r["micro_market"],
            "BHK": r["bhk"],
            "Area (sqft)": r["area_sqft"],
            "Age (Yrs)": f"{r.get('age_years', 7)} yrs ({r.get('year_built', 2019)})",
            "Resident Rating": f"⭐ {r.get('resident_rating', 4.5)} / 5",
            "Feedback Score": f"{r.get('feedback_score', 90)} / 100",
            "Monthly Rent": f"₹{rent_pm:,}",
            "Monthly Maint": f"₹{maint_pm:,}",
            "Total Monthly Outflow": f"₹{tot_outflow:,}",
            "Deposit Interest (7.5% p.a.)": f"+₹{dep_interest_pm:,}/- pm",
            "Total Monthly (with Deposit Note)": f"Total Monthly: ₹{tot_outflow:,} (+{dep_interest_pm:,}/- pm due to deposit)",
            "Effective Monthly Cost": f"₹{effective_monthly:,}",
            "Security Deposit": f"₹{dep_inr:,} ({r['security_deposit_months']} mos)",
            "Brokerage Savings": f"₹{r.get('brokerage_savings_inr', 0):,}",
            "Best Platform": r.get("best_platform", "Direct Owner"),
            "Panathur Free": "🟢 Yes (Safe)" if r["panathur_bottleneck_free"] else "🔴 No (Choke)",
            "Validation URL": r.get("validation_url", "#"),
            "Community Post": r.get("source_post_url", "#"),
            "Contact Person": f"{contact.get('name', 'Owner')} ({contact.get('type')})",
            "Common Complaints": complaints_short
        })

    df_rental_table = pd.DataFrame(rental_table_rows)
    st.dataframe(df_rental_table, use_container_width=True, hide_index=True)

    # Side-by-Side Rental Comparator
    with st.expander("🔍 Interactive Head-to-Head Rental Comparator (Select 2-3 Societies)"):
        rent_options = [r["society_name"] + " - " + r["bhk"] for r in filtered_rentals]
        selected_rent_compare = st.multiselect(
            "Select Rental Units to Compare Side-by-Side",
            options=rent_options,
            default=rent_options[:2] if len(rent_options) >= 2 else rent_options
        )

        if selected_rent_compare:
            rent_comp_records = []
            for sel_label in selected_rent_compare:
                r_item = next((item for item in filtered_rentals if (item["society_name"] + " - " + item["bhk"]) == sel_label), None)
                if r_item:
                    rent_item = r_item["rent_pm"]
                    maint_item = r_item["maintenance_pm"]
                    tot_outflow = r_item.get("total_monthly_outflow", rent_item + maint_item)
                    dep_inr = r_item.get("security_deposit_inr", rent_item * r_item.get("security_deposit_months", 4))
                    dep_interest_pm = round((dep_inr * 0.075) / 12)
                    effective_monthly = tot_outflow + dep_interest_pm
                    annual_dep_interest = round(dep_inr * 0.075)

                    rent_comp_records.append({
                        "Metric / Parameter": "Monthly Rent",
                        sel_label: f"₹{rent_item:,} / mo"
                    })
                    rent_comp_records.append({
                        "Metric / Parameter": "Monthly Maintenance",
                        sel_label: f"₹{maint_item:,} / mo"
                    })
                    rent_comp_records.append({
                        "Metric / Parameter": "Base Monthly Outflow (Rent + Maint)",
                        sel_label: f"₹{tot_outflow:,} / mo"
                    })
                    rent_comp_records.append({
                        "Metric / Parameter": "Security Deposit Locked",
                        sel_label: f"₹{dep_inr:,} ({r_item['security_deposit_months']} months)"
                    })
                    rent_comp_records.append({
                        "Metric / Parameter": "7.5% Annual Interest on Security Deposit (Opportunity Cost)",
                        sel_label: f"+₹{dep_interest_pm:,}/- pm (₹{annual_dep_interest:,}/yr locked)"
                    })
                    rent_comp_records.append({
                        "Metric / Parameter": "👉 Total Monthly (with Deposit Note)",
                        sel_label: f"Total Monthly: ₹{tot_outflow:,} (+{dep_interest_pm:,}/- pm due to deposit)"
                    })
                    rent_comp_records.append({
                        "Metric / Parameter": "Effective Economic Monthly Cost",
                        sel_label: f"₹{effective_monthly:,} / mo"
                    })
                    rent_comp_records.append({
                        "Metric / Parameter": "⭐ Resident Rating & Feedback",
                        sel_label: f"⭐ {r_item.get('resident_rating', 4.5)}/5 (Score: {r_item.get('feedback_score', 90)}/100)"
                    })
                    rent_comp_records.append({
                        "Metric / Parameter": "Property Age",
                        sel_label: f"{r_item.get('age_years', 7)} Years (Built {r_item.get('year_built', 2019)})"
                    })
                    rent_comp_records.append({
                        "Metric / Parameter": "Brokerage Savings via Direct Owner",
                        sel_label: f"₹{r_item.get('brokerage_savings_inr', 0):,}"
                    })
                    rent_comp_records.append({
                        "Metric / Parameter": "Commute to RMZ Ecospace",
                        sel_label: f"{r_item.get('commute_time_mins', {}).get('RMZ Ecospace', 10)} mins"
                    })
                    rent_comp_records.append({
                        "Metric / Parameter": "Commute to Prestige Tech Park (PTP)",
                        sel_label: f"{r_item.get('commute_time_mins', {}).get('Prestige Tech Park', 10)} mins"
                    })
                    rent_comp_records.append({
                        "Metric / Parameter": "Water Source & Backup",
                        sel_label: f"{r_item['water_supply']} | {r_item['power_backup']}"
                    })
                    rent_comp_records.append({
                        "Metric / Parameter": "⚠️ Resident Complaints / Restrictions",
                        sel_label: "; ".join(r_item.get("common_complaints", []))
                    })

            df_r_comp = pd.DataFrame(rent_comp_records)
            df_r_comp_pivot = df_r_comp.groupby("Metric / Parameter", as_index=False).first()
            st.dataframe(df_r_comp_pivot, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("### 📋 Rental House Details & Direct Contact Cards")

    # Render Rental Cards
    for r in filtered_rentals:
        is_safe_traffic = r["panathur_bottleneck_free"]
        card_border = "#10B981" if is_safe_traffic else "#EF4444"
        savings = r.get("brokerage_savings_inr", 0)
        rent_val = r["rent_pm"]
        maint_val = r["maintenance_pm"]
        tot_outflow = r.get("total_monthly_outflow", rent_val + maint_val)
        ann_maint = r.get("annual_maintenance_inr", maint_val * 12)
        dep_val = r.get("security_deposit_inr", rent_val * r.get("security_deposit_months", 4))
        dep_interest_pm = round((dep_val * 0.075) / 12)
        effective_monthly = tot_outflow + dep_interest_pm
        annual_dep_interest = round(dep_val * 0.075)

        with st.container():
            st.markdown(f"""
            <div class="property-card" style="border-left: 6px solid {card_border};">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 8px;">
                    <div>
                        <h3 style="margin: 0; color: #F8FAFC; font-size: 1.25rem;">{r['unit_title']}</h3>
                        <div style="margin-top: 4px;">
                            <span class="badge-rating">⭐ {r.get('resident_rating', 4.5)} / 5.0 (Feedback: {r.get('feedback_score', 90)}/100)</span>
                            <span class="badge-age">⏳ Age: {r.get('age_years', 7)} Years (Built {r.get('year_built', 2019)})</span>
                            <span class="badge-deal">🏢 {r['society_name']}</span>
                            <span class="badge-green">📍 {r['micro_market']}</span>
                        </div>
                        <p style="margin: 6px 0 0 0; color: #38BDF8; font-weight: 600; font-size: 0.9rem;">
                            📐 {r['area_sqft']} sqft &nbsp;|&nbsp; 🛋️ {r['furnishing']} &nbsp;|&nbsp; 🏢 Floor: {r['floor']} &nbsp;|&nbsp; 🧭 Facing: {r['facing']}
                        </p>
                    </div>
                    <div style="text-align: right;">
                        <span style="font-size: 1.6rem; font-weight: 800; color: #10B981;">₹{rent_val:,}</span>
                        <span style="color: #94A3B8; font-size: 0.9rem;"> / mo rent</span>
                        <div style="color: #F59E0B; font-weight: 700; font-size: 0.95rem; margin-top: 3px;">
                            Total Monthly: ₹{tot_outflow:,} <span style="font-size: 0.82rem; color: #FDE68A; font-weight: 600;">(+{dep_interest_pm:,}/- pm due to deposit)</span>
                        </div>
                        <div style="color: #38BDF8; font-size: 0.83rem; font-weight: 600;">
                            Effective Monthly Outflow: ₹{effective_monthly:,} / mo
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            r_info, r_platforms, r_contact = st.columns([1, 1, 1])

            with r_info:
                st.markdown("**🛠️ Outflow & Maintenance Breakdown:**")
                st.markdown(f"- **Monthly Rent:** `₹{rent_val:,} / mo`")
                st.markdown(f"- **Monthly Maintenance:** `₹{maint_val:,} / mo`")
                st.markdown(f"- **Total Monthly Outflow (Rent + Maint):** <b style='color:#F59E0B;'>₹{tot_outflow:,} / mo</b>", unsafe_allow_html=True)
                st.markdown(f"- **Security Deposit:** `₹{dep_val:,}` ({r['security_deposit_months']} months)")
                st.markdown(f"- **7.5% Annual Interest on Deposit (Opportunity Cost):** <b style='color:#FCD34D;'>+₹{dep_interest_pm:,} / mo</b> <span style='font-size:0.8rem; color:#94A3B8;'>(₹{annual_dep_interest:,}/yr)</span>", unsafe_allow_html=True)
                st.markdown(f"👉 **TOTAL MONTHLY WITH DEPOSIT NOTE:** <b style='color:#38BDF8; font-size:1.02rem;'>Total Monthly: ₹{tot_outflow:,} (+{dep_interest_pm:,}/- pm due to deposit)</b>", unsafe_allow_html=True)
                st.markdown(f"- **Effective Economic Outflow:** `₹{effective_monthly:,} / mo`")
                st.markdown(f"- **Total Annual Maintenance:** `₹{ann_maint:,} / yr`")
                st.markdown(f"- **Water Supply:** {r['water_supply']}")

            with r_platforms:
                st.markdown("**📊 Listed Prices Across Platforms:**")
                plat_rows = []
                for p_name, p_data in r.get("platforms", {}).items():
                    plat_rows.append({
                        "Platform": p_name.replace("_", " "),
                        "Rent": f"₹{p_data['price']:,}",
                        "Brokerage": "₹0" if p_data["brokerage"] == 0 else f"₹{p_data['brokerage']:,}",
                        "Status": p_data.get("badge", "")
                    })
                st.dataframe(pd.DataFrame(plat_rows), use_container_width=True, hide_index=True)

                if savings > 0:
                    st.markdown(f"""
                    <div class="badge-deal" style="margin-top: 4px; text-align: center; display: block;">
                        🎉 Connect via Direct Owner to Save ₹{savings:,} Brokerage!
                    </div>
                    """, unsafe_allow_html=True)

            with r_contact:
                contact = r.get("contact", {})
                st.markdown("**📞 Contact & Schedule Site Visit:**")
                st.markdown(f"- **Contact:** `{contact.get('name', 'Owner')}` ({contact.get('type')})")
                st.markdown(f"- **Phone:** `{contact.get('phone')}`")
                st.markdown(f"- **Available:** `{r['available_from']}`")

                # Direct WhatsApp Link
                wa_msg = urllib.parse.quote(
                    f"Hi {contact.get('name')}, I saw your rental listing for {r['bhk']} in {r['society_name']} "
                    f"on the East Bengaluru Real Estate Radar. Is it currently available for site visit?"
                )
                wa_url = f"https://wa.me/{contact.get('whatsapp')}?text={wa_msg}"
                
                st.markdown(f"""
                <a href="{wa_url}" target="_blank" style="text-decoration: none;">
                    <div style="background-color: #25D366; color: white; text-align: center; padding: 10px; border-radius: 8px; font-weight: 700; margin-top: 4px; margin-bottom: 6px;">
                        💬 Chat on WhatsApp with Owner
                    </div>
                </a>
                """, unsafe_allow_html=True)

                # Google Maps Link to Society
                gmaps_society_url = f"https://www.google.com/maps/search/?api=1&query={r['lat']},{r['lng']}"
                st.markdown(f"""
                <a href="{gmaps_society_url}" target="_blank" style="text-decoration: none;">
                    <div style="background-color: #0F172A; border: 1px solid #334155; color: #38BDF8; text-align: center; padding: 6px; border-radius: 6px; font-weight: 600; font-size: 0.8rem; margin-bottom: 5px;">
                        📍 View Society on Google Maps ↗
                    </div>
                </a>
                """, unsafe_allow_html=True)

                val_url = r.get("validation_url", "#")
                source_post = r.get("source_post_url", "#")
                st.markdown(f"""
                <div style="display: flex; gap: 6px; margin-bottom: 6px; flex-wrap: wrap;">
                    <a href="{val_url}" target="_blank" style="flex: 1; text-decoration: none; min-width: 120px;">
                        <div style="background-color: #1E3A8A; color: #BFDBFE; text-align: center; padding: 6px; border-radius: 6px; font-weight: 700; font-size: 0.78rem; border: 1px solid #3B82F6;">
                            🔗 Verify Post / Listing ↗
                        </div>
                    </a>
                    <a href="{source_post}" target="_blank" style="flex: 1; text-decoration: none; min-width: 120px;">
                        <div style="background-color: #065F46; color: #A7F3D0; text-align: center; padding: 6px; border-radius: 6px; font-weight: 700; font-size: 0.78rem; border: 1px solid #10B981;">
                            💬 Community Listing ↗
                        </div>
                    </a>
                </div>
                """, unsafe_allow_html=True)

            # Common Complaints Box for Rental
            r_complaints = r.get("common_complaints", [])
            st.markdown(f"""
            <div class="complaint-box">
                <b style="color: #FDE68A;">⚠️ Common Tenant Complaints & Society Rules:</b>
                <ul style="margin: 4px 0 0 16px; padding: 0; font-size: 0.88rem; color: #E2E8F0;">
                    {''.join([f"<li>{c}</li>" for c in r_complaints])}
                </ul>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("---")

# =============================================================
# TAB 3: NEARBY AREAS (WORTH CONSIDERING SCANNER)
# =============================================================
with tab_nearby:
    st.subheader("🧭 Nearby Micro-Markets Scanner (Worth Considering Beyond Core Radar)")
    st.markdown(
        "While **Bellandur Core**, **Green Glen Layout**, and **Kadubeesanahalli (Gurukul)** offer maximum walking proximity "
        "to ORR tech parks and the Blue Line Metro, several adjacent micro-markets offer compelling trade-offs: "
        "**significantly lower price per sqft**, **integrated mega-townships**, or **superior planned layouts**."
    )

    # Summary metric cards for nearby areas
    n_col1, n_col2, n_col3 = st.columns(3)
    with n_col1:
        st.markdown("""
        <div class="nearby-box">
            <h4 style="margin:0; color:#A7F3D0;">Sarjapur Road / Kaikondrahalli</h4>
            <p style="margin:4px 0 0 0; font-size:0.85rem; color:#E2E8F0;">
                <b>Avg Rate:</b> ₹10,500 - ₹12,000 / sqft<br>
                <b>Distance:</b> 3.5 - 4.5 km to Bellandur<br>
                <b>Highlight:</b> Kaikondrahalli lakeside walking, 20-25% price discount vs Bellandur.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with n_col2:
        st.markdown("""
        <div class="nearby-box">
            <h4 style="margin:0; color:#A7F3D0;">HSR Layout (Sectors 1 & 2)</h4>
            <p style="margin:4px 0 0 0; font-size:0.85rem; color:#E2E8F0;">
                <b>Avg Rate:</b> ₹15,500 - ₹17,500 / sqft<br>
                <b>Distance:</b> 3.0 - 3.5 km to Bellandur<br>
                <b>Highlight:</b> Bengaluru's elite planned sector, broad tree-lined avenues, top restaurants.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with n_col3:
        st.markdown("""
        <div class="nearby-box">
            <h4 style="margin:0; color:#A7F3D0;">Varthur / Gunjur Corridor</h4>
            <p style="margin:4px 0 0 0; font-size:0.85rem; color:#E2E8F0;">
                <b>Avg Rate:</b> ₹9,500 - ₹11,000 / sqft<br>
                <b>Distance:</b> 6.0 - 7.5 km to Bellandur<br>
                <b>Highlight:</b> 40+ to 100+ acre mega-townships with schools & high-street retail inside.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📋 Table of Worth-Considering Properties Nearby")
    st.caption("Full parameter matrix comparing price, age, maintenance, upfront advance, resident rating, advantages vs core, and real resident tradeoffs.")

    nearby_table_rows = []
    for nb in nearby_properties:
        nearby_table_rows.append({
            "Property Name": nb["name"],
            "Developer": f"{nb['builder']} ({nb['builder_tier']})",
            "Micro-Market": nb["micro_market"],
            "Dist to Core (km)": f"{nb['distance_to_bellandur_km']} km",
            "Age (Yrs)": f"{nb.get('age_years', 5)} yrs ({nb.get('year_built', 2021)})",
            "Resident Rating": f"⭐ {nb.get('resident_rating', 4.5)} / 5",
            "Feedback Score": f"{nb.get('feedback_score', 90)} / 100",
            "Rate / sqft": f"₹{nb['price_per_sqft']:,}",
            "Base Flat Price": f"₹{nb['total_price_cr']} Cr",
            "Config & Area": f"{nb['avg_bhk']} ({nb['avg_sqft']} sqft)",
            "Monthly Maint": f"₹{nb['monthly_maintenance_inr']:,}",
            "Upfront Cash Req.": f"₹{round(nb.get('upfront_cash_required_cr', 0.5) * 100, 2)} L",
            "Total Cost of Ownership": f"₹{nb.get('total_ownership_cost_cr', 2.0)} Cr",
            "Commute to Ecospace": f"{nb['commute_to_ecospace_mins']} mins",
            "Commute to PTP": f"{nb['commute_to_ptp_mins']} mins",
            "Validation URL": nb.get("validation_url", "#"),
            "Why Worth Considering (Pros)": nb["why_worth_considering"],
            "Key Trade-offs / Complaints (Cons)": nb["key_tradeoffs_complaints"]
        })

    df_nearby = pd.DataFrame(nearby_table_rows)
    st.dataframe(df_nearby, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("### 🏢 Detailed Profiles: Worth-Considering Nearby Properties")

    for nb in nearby_properties:
        gmaps_nb_url = f"https://www.google.com/maps/search/?api=1&query={nb['lat']},{nb['lng']}"
        with st.container():
            st.markdown(f"""
            <div class="property-card" style="border-left: 6px solid #8B5CF6;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 8px;">
                    <div>
                        <h3 style="margin: 0; color: #F8FAFC; font-size: 1.25rem;">{nb['name']}</h3>
                        <div style="margin-top: 4px;">
                            <span class="badge-deal">📍 {nb['micro_market']} ({nb['distance_to_bellandur_km']} km to Bellandur Core)</span>
                            <span class="badge-rating">⭐ {nb.get('resident_rating', 4.5)} / 5.0 (Feedback: {nb.get('feedback_score', 90)}/100)</span>
                            <span class="badge-age">⏳ Age: {nb.get('age_years', 5)} Years (Built {nb.get('year_built', 2021)})</span>
                        </div>
                        <p style="margin: 5px 0 0 0; color: #94A3B8; font-size: 0.9rem;">
                            <b>Developer:</b> {nb['builder']} &nbsp;|&nbsp; 
                            <b>Hierarchy:</b> <span style="color: #A78BFA;">{nb['builder_tier']}</span> &nbsp;|&nbsp; 
                            <b>Status:</b> {nb.get('status', 'Ready to Move')}
                        </p>
                    </div>
                    <div style="text-align: right;">
                        <span style="font-size: 1.6rem; font-weight: 800; color: #A78BFA;">₹{nb['total_price_cr']} Cr</span>
                        <div style="font-size: 0.85rem; color: #CBD5E1;">₹{nb['price_per_sqft']:,} / sqft</div>
                        <div style="font-size: 0.8rem; color: #94A3B8;">TOC: ~₹{nb.get('total_ownership_cost_cr', 2.0)} Cr</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            nb_c1, nb_c2 = st.columns([1, 1])
            with nb_c1:
                st.markdown("**🌟 Why Worth Considering (Value Proposition):**")
                st.info(nb["why_worth_considering"])
                st.markdown(f"- **Avg Configuration:** `{nb['avg_bhk']}` ({nb['avg_sqft']} sqft)")
                st.markdown(f"- **Monthly Maintenance:** `₹{nb['monthly_maintenance_inr']:,} / mo` (₹{nb['annual_maintenance_inr']:,} / yr)")
                st.markdown(f"- **Upfront Advance Cash Required:** `~₹{round(nb.get('upfront_cash_required_cr', 0.5) * 100, 2)} Lakhs`")

            with nb_c2:
                st.markdown("**⚠️ Real Resident Trade-offs & Common Complaints:**")
                st.warning(nb["key_tradeoffs_complaints"])
                st.markdown(f"- **Commute to RMZ Ecospace:** `{nb['commute_to_ecospace_mins']} mins`")
                st.markdown(f"- **Commute to Prestige Tech Park (PTP):** `{nb['commute_to_ptp_mins']} mins`")
                st.markdown(f"- **Water Source:** `{nb['water_source']}`")

                val_nb_url = nb.get("validation_url", "#")
                st.markdown(f"""
                <div style="display: flex; gap: 6px; margin-top: 8px; flex-wrap: wrap;">
                    <a href="{gmaps_nb_url}" target="_blank" style="flex: 1; text-decoration: none; min-width: 120px;">
                        <div style="background-color: #6D28D9; color: white; text-align: center; padding: 7px; border-radius: 6px; font-weight: 700; font-size: 0.82rem;">
                            📍 Google Maps ↗
                        </div>
                    </a>
                    <a href="{val_nb_url}" target="_blank" style="flex: 1; text-decoration: none; min-width: 120px;">
                        <div style="background-color: #1E3A8A; color: #BFDBFE; text-align: center; padding: 7px; border-radius: 6px; font-weight: 700; font-size: 0.82rem; border: 1px solid #3B82F6;">
                            🔗 Verify Project Post ↗
                        </div>
                    </a>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("---")

# =============================================================
# TAB 4: PRICE TRENDS & MARKET ANALYTICS
# =============================================================
with tab_trends:
    st.subheader("📈 Micro-Market Price Appreciation (2020 - 2026)")
    st.caption("Visualizing the widening capital appreciation divergence between Green Glen Layout and Panathur Road.")

    if not hist_df.empty:
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(
            x=hist_df["date"], y=hist_df["bellandur_core_psqft"],
            mode="lines+markers", name="Bellandur Core", line=dict(color="#0D9488", width=3)
        ))
        fig_trend.add_trace(go.Scatter(
            x=hist_df["date"], y=hist_df["green_glen_layout_psqft"],
            mode="lines+markers", name="Green Glen Layout", line=dict(color="#10B981", width=3)
        ))
        fig_trend.add_trace(go.Scatter(
            x=hist_df["date"], y=hist_df["kadubeesanahalli_gurukul_psqft"],
            mode="lines+markers", name="Kadubeesanahalli (Gurukul)", line=dict(color="#3B82F6", width=2.5)
        ))
        fig_trend.add_trace(go.Scatter(
            x=hist_df["date"], y=hist_df["panathur_road_choke_psqft"],
            mode="lines+markers", name="Panathur Road (Choke Zone)", line=dict(color="#EF4444", width=2.5, dash="dot")
        ))

        fig_trend.update_layout(
            title="Capital Appreciation Per Square Foot",
            xaxis_title="Date / Snapshot",
            yaxis_title="Price (₹ / sqft)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=20, r=20, t=50, b=20),
            height=420,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=True, gridcolor="#334155"),
            yaxis=dict(showgrid=True, gridcolor="#334155")
        )
        st.plotly_chart(fig_trend, use_container_width=True)

        st.download_button(
            label="📥 Download Full Historical CSV",
            data=hist_df.to_csv(index=False).encode('utf-8'),
            file_name="east_bengaluru_historical_prices.csv",
            mime="text/csv",
            use_container_width=True
        )

# =============================================================
# TAB 5: BUILDER PEDIGREE & DUE DILIGENCE
# =============================================================
with tab_pedigree:
    st.subheader("⚖️ Builder Pedigree & Legal Verification Checklist")
    
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.markdown("### 🏆 Top 10 Tier 1 Developers")
        st.markdown("""
        1. **Sobha Limited** (German engineering, in-house precast)
        2. **Prestige Group** (Largest South Indian listed developer)
        3. **Brigade Group** (Punctual delivery, institutional upkeep)
        4. **Total Environment** (Earth-sheltered roofs, terracotta brick)
        5. **Godrej Properties** (Nationwide governance, strict RERA escrow)
        6. **Embassy Group** (Commercial & residential benchmark)
        7. **Puravankara Limited** (45+ years engineering heritage)
        8. **Assetz Property Group** (Contemporary design, high green cover)
        9. **Century Real Estate** (Clean title land banks)
        10. **Salarpuria Sattva Group** (Major ORR corporate developer)
        """)

    with col_p2:
        st.markdown("### 📋 4 Mandatory Due Diligence Pillars")
        st.checkbox("1. Verified BBMP / BDA A-Khata Title", key="due_1")
        st.checkbox("2. Active Karnataka RERA Verification (rera.karnataka.gov.in)", key="due_2")
        st.checkbox("3. Dual Water Source (Cauvery + Deep Borewells + STP)", key="due_3")
        st.checkbox("4. Storm-Water Drain (Rajakaluve) Buffer Clearance (30m/15m)", key="due_4")

# =============================================================
# TAB 6: DAILY TRACKER (5 PM IST) & ALL OPTIONS CSV ARCHIVE
# =============================================================
with tab_architecture:
    st.subheader("⚙️ Automated Daily Tracker & Parameter Delta Validation (5:00 PM IST)")
    st.markdown("""
    The radar maintains strict daily synchronization running automatically at **5:00 PM IST (11:30 UTC)**:
    - 📋 **All Available Options**: Records full snapshots of **all purchase properties** (`data/all_purchase_properties_daily.csv`) and **all rental options** (`data/all_rental_properties_daily.csv`).
    - 🏆 **Ranked Selections**: Records **Top 10 Purchase** and **Top 5 Rental** lists.
    - 🔍 **Parameter Delta Validation**: Compares live rates, maintenance, outflows, resident ratings, feedback scores, and bottleneck statuses against `data/property_audit_ledger.json`.
    - ⚡ **Intelligent Storage**: If today's record exists and no parameters have changed, it validates the data without redundant duplicate writes. If any parameter changes, it updates the snapshot and logs an entry to the audit trail.
    - 🔄 **Autonomous Page Auto-Refresh**: The dashboard automatically checks date rollover every 45s and refreshes to reflect today's data even if left unattended on a screen or mobile device.
    """)

    # Validation Engine & Last Execution Summary Box
    t_status = tracker_log.get("status", "Awaiting initial execution") if tracker_log else "Awaiting initial execution"
    t_time = tracker_log.get("timestamp", "N/A") if tracker_log else "N/A"
    t_date = tracker_log.get("date", "N/A") if tracker_log else "N/A"
    t_changes = tracker_log.get("changes_count", 0) if tracker_log else 0

    status_color = "#10B981" if "VALIDATED" in t_status or "RECORDED" in t_status else "#38BDF8"

    st.markdown(f"""
    <div style="background: #1E293B; border-left: 6px solid {status_color}; padding: 12px 16px; border-radius: 8px; margin-bottom: 16px;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
            <div>
                <b style="color: #F8FAFC; font-size: 1rem;">🛡️ Daily Validation Engine Status: <span style="color: {status_color};">{t_status}</span></b>
                <div style="font-size: 0.85rem; color: #94A3B8; margin-top: 3px;">
                    Last Validated Date: <code>{t_date}</code> | Audit Timestamp: <code>{t_time}</code>
                </div>
            </div>
            <div>
                <span class="badge-deal">📊 Detected Changes: {t_changes}</span>
                <span class="badge-age">✅ All Options Monitored</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ---------------------------------------------------------
    # MANUAL SNAPSHOT CAPTURE & VALIDATION
    # ---------------------------------------------------------
    st.markdown("### ⚡ Manual Daily Capture & Validation Trigger")
    man_c1, man_c2 = st.columns([3, 2])
    with man_c1:
        force_snapshot = st.checkbox("Force Re-recording (Overwrite even if all parameters are identical)", value=False)
        if st.button("🚀 Validate & Capture Today's Snapshot Now", use_container_width=True):
            from scripts.daily_tracker import run_daily_tracker
            with st.spinner("Auditing property parameters and validating snapshot..."):
                res = run_daily_tracker(dry_run=False, force=force_snapshot)
                if res["status"] == "VALIDATED_NO_CHANGES":
                    st.info(f"✅ **State Verified & Intact**: Existing snapshot for {res['date']} contains all {res['purchase_count']} purchase and {res['rental_count']} rental options. Zero parameter divergence detected. Redundant re-recording safely skipped.")
                elif res["status"] == "UPDATED_ON_PARAMETER_CHANGE":
                    st.success(f"⚡ **Parameter Changes Detected ({res['changes_count']})**! Updated all daily CSV files and logged change audit trail.")
                else:
                    st.success(f"🚀 **Successfully Recorded New Daily Snapshot** ({res['purchase_count']} purchase options, {res['rental_count']} rental options)!")
                st.rerun()

    with man_c2:
        st.markdown("""
        <div style="font-size: 0.82rem; color: #94A3B8; background: #0F172A; padding: 10px; border-radius: 8px; border: 1px solid #334155;">
            <b>Automated Cron Schedule:</b><br>
            Runs daily at <b>11:30 UTC (5:00 PM IST)</b> via GitHub Actions.<br>
            Commits directly to the GitHub repository: <code>data/all_purchase_properties_daily.csv</code>, <code>data/all_rental_properties_daily.csv</code>.
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ---------------------------------------------------------
    # DOWNLOAD ALL DATASETS
    # ---------------------------------------------------------
    st.markdown("### 📥 Download Daily CSV Datasets (All Options & Ranked Lists)")
    
    dl_col1, dl_col2, dl_col3, dl_col4 = st.columns(4)

    with dl_col1:
        if os.path.exists(ALL_PURCHASE_CSV):
            with open(ALL_PURCHASE_CSV, "rb") as f:
                st.download_button(
                    "📥 ALL Purchase CSV",
                    f,
                    file_name="all_purchase_properties_daily.csv",
                    mime="text/csv",
                    use_container_width=True,
                    help="Records all available purchase properties in corridor"
                )
        else:
            st.button("📥 ALL Purchase CSV (Pending)", disabled=True, use_container_width=True)

    with dl_col2:
        if os.path.exists(ALL_RENTAL_CSV):
            with open(ALL_RENTAL_CSV, "rb") as f:
                st.download_button(
                    "📥 ALL Rental CSV",
                    f,
                    file_name="all_rental_properties_daily.csv",
                    mime="text/csv",
                    use_container_width=True,
                    help="Records all available rental properties in corridor"
                )
        else:
            st.button("📥 ALL Rental CSV (Pending)", disabled=True, use_container_width=True)

    with dl_col3:
        if os.path.exists(TOP_10_PURCHASE_CSV):
            with open(TOP_10_PURCHASE_CSV, "rb") as f:
                st.download_button(
                    "📥 Top 10 Purchase CSV",
                    f,
                    file_name="top_10_purchase_daily.csv",
                    mime="text/csv",
                    use_container_width=True,
                    help="Top 10 purchase properties scored by radar"
                )
        else:
            st.button("📥 Top 10 Purchase (Pending)", disabled=True, use_container_width=True)

    with dl_col4:
        if os.path.exists(TOP_5_RENTAL_CSV):
            with open(TOP_5_RENTAL_CSV, "rb") as f:
                st.download_button(
                    "📥 Top 5 Rental CSV",
                    f,
                    file_name="top_5_rental_daily.csv",
                    mime="text/csv",
                    use_container_width=True,
                    help="Top 5 rental properties scored by radar"
                )
        else:
            st.button("📥 Top 5 Rental (Pending)", disabled=True, use_container_width=True)

    # ---------------------------------------------------------
    # DATA PREVIEWS: ALL OPTIONS
    # ---------------------------------------------------------
    st.markdown("---")
    pv_c1, pv_c2 = st.columns(2)
    with pv_c1:
        st.markdown("#### 🏢 All Available Purchase Properties Monitored")
        if os.path.exists(ALL_PURCHASE_CSV):
            df_all_p = pd.read_csv(ALL_PURCHASE_CSV)
            p_show_cols = [c for c in ["Property_Name", "Resident_Rating", "Feedback_Score", "Age_Years", "Rate_Per_Sqft_INR", "Base_Price_Cr", "Upfront_Cash_Required_INR", "Total_Ownership_Cost_Cr", "Validation_Status"] if c in df_all_p.columns]
            st.dataframe(df_all_p[p_show_cols], use_container_width=True, hide_index=True)
            st.caption(f"Total monitored purchase options: {len(df_all_p)}")

    with pv_c2:
        st.markdown("#### 🏡 All Available Rental Properties Monitored")
        if os.path.exists(ALL_RENTAL_CSV):
            df_all_r = pd.read_csv(ALL_RENTAL_CSV)
            r_show_cols = [c for c in ["Society_Name", "Resident_Rating", "Feedback_Score", "Age_Years", "Monthly_Rent_INR", "Total_Monthly_Outflow_INR", "Monthly_Summary_With_Deposit", "Effective_Monthly_Cost_INR", "Best_Platform"] if c in df_all_r.columns]
            st.dataframe(df_all_r[r_show_cols], use_container_width=True, hide_index=True)
            st.caption(f"Total monitored rental options: {len(df_all_r)}")

    # ---------------------------------------------------------
    # PARAMETER CHANGE AUDIT TRAIL
    # ---------------------------------------------------------
    st.markdown("---")
    st.markdown("### 🔍 Parameter Change Detection Audit Trail")
    df_changes = get_parameter_changes_df()
    if not df_changes.empty:
        st.dataframe(df_changes, use_container_width=True, hide_index=True)
        if os.path.exists(CHANGES_CSV_FILE):
            with open(CHANGES_CSV_FILE, "rb") as f:
                st.download_button(
                    "📥 Download Parameter Changes Audit Log CSV",
                    f,
                    file_name="property_parameter_changes.csv",
                    mime="text/csv",
                    use_container_width=True
                )
    else:
        st.info("No parameter deltas recorded yet. Parameters are currently in lock-step with base records.")

    st.markdown("---")
    st.markdown("#### 📜 Live Tracker Execution Log JSON")
    st.json(tracker_log if tracker_log else {"status": "Awaiting initial cron execution"})
