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

from utils.geo import haversine_distance_km, check_zone_membership
from utils.scoring import compute_property_match_score, TIER_1_BUILDERS, TIER_2_BUILDERS
from utils.storage import (
    get_user_preferences,
    save_user_preferences,
    get_properties,
    get_rental_properties,
    get_market_zones,
    get_anchors,
    get_historical_prices_df,
    get_tracker_log
)

# Set page configuration
st.set_page_config(
    page_title="East Bengaluru Real Estate Radar",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown("""
<style>
    /* Metric Card Styling */
    div[data-testid="stMetricValue"] {
        font-size: 1.6rem !important;
        font-weight: 700;
        color: #0D9488;
    }
    .main-header {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        padding: 1.4rem 1.8rem;
        border-radius: 12px;
        border-left: 6px solid #0D9488;
        margin-bottom: 1.5rem;
    }
    .main-title {
        color: #F8FAFC;
        font-size: 1.9rem;
        font-weight: 800;
        margin: 0;
    }
    .sub-title {
        color: #94A3B8;
        font-size: 1.0rem;
        margin-top: 0.3rem;
    }
    .badge-green {
        background-color: #065F46;
        color: #A7F3D0;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-red {
        background-color: #991B1B;
        color: #FECACA;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-deal {
        background-color: #1E3A8A;
        color: #BFDBFE;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 700;
    }
    .property-card {
        background: #1E293B;
        border-radius: 12px;
        padding: 1.2rem;
        margin-bottom: 1.2rem;
        border: 1px solid #334155;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .property-card:hover {
        border-color: #0D9488;
    }
    .platform-pill {
        display: inline-block;
        background: #334155;
        color: #F1F5F9;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.85rem;
        margin: 2px 4px 2px 0px;
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
market_zones = get_market_zones()
anchors = get_anchors()
hist_df = get_historical_prices_df()
tracker_log = get_tracker_log()

# -------------------------------------------------------------
# Header Banner
# -------------------------------------------------------------
st.markdown("""
<div class="main-header">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
        <div>
            <h1 class="main-title">🧭 East Bengaluru Real Estate Radar</h1>
            <p class="sub-title">Bellandur • Green Glen Layout • Kadubeesanahalli (Gurukul Side) | Blue Line Metro Corridor</p>
        </div>
        <div style="margin-top: 5px;">
            <span class="badge-green">🛡️ Panathur Choke Filter Active</span>
            <span class="badge-green" style="margin-left: 6px;">🚇 Blue Line Transit Evaluator</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# KPI Quick Stats Row
# -------------------------------------------------------------
col_k1, col_k2, col_k3, col_k4 = st.columns(4)
with col_k1:
    st.metric(label="Purchase Radar Assets", value=f"{len(properties)} Properties", delta="Top Tier Curated")
with col_k2:
    st.metric(label="Active Rental Units", value=f"{len(rental_properties)} Units", delta="Zero-Brokerage Tracked")
with col_k3:
    st.metric(label="Green Glen vs Panathur Gap", value="+48.0%", delta="Bottleneck Penalty Delta", delta_color="normal")
with col_k4:
    last_run = tracker_log.get("last_run_utc", "2026-10-02")[:10]
    st.metric(label="Daily Tracker Sync", value=f"{last_run}", delta="Automated 06:00 UTC")

# -------------------------------------------------------------
# Sidebar: Scoring Weights & Preference Customization
# -------------------------------------------------------------
st.sidebar.header("⚙️ Radar Configuration")

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
st.sidebar.subheader("⚖️ Parameter Scoring Weights")
st.sidebar.caption("Customizable multi-criteria sum matrix (Default Blueprint: 100%)")

w_metro = st.sidebar.slider("Metro Proximity", 0, 40, int(weights.get("metro_proximity", 15)), step=5, help="<1km=100%, 1-2km=75%, >3km=30%")
w_traffic = st.sidebar.slider("Traffic & Route Integrity", 0, 40, int(weights.get("traffic_integrity", 20)), step=5, help="Zero Panathur routing = 100%, Panathur choke = -50 pts")
w_dist = st.sidebar.slider("Exact Distances to Anchors", 0, 30, int(weights.get("exact_distances", 15)), step=5, help="Travel time & linear distance to Office, School, Hospital, Mall, Airport")
w_builder = st.sidebar.slider("Builder Pedigree", 0, 30, int(weights.get("builder_pedigree", 15)), step=5, help="Tier 1 Top 10 = 100%, Tier 2 = 80%, Local = 20%")
w_water = st.sidebar.slider("Water Logging & Drainage", 0, 25, int(weights.get("water_logging", 10)), step=5, help="Elevation check & lake buffer storm runoff protection")
w_fin = st.sidebar.slider("Financials & Appreciation", 0, 30, int(weights.get("financials_appreciation", 15)), step=5, help="Price/sqft, historical YoY appreciation & rental yield")
w_legal = st.sidebar.slider("Land Title & Gated Tech", 0, 25, int(weights.get("land_title_quality", 10)), step=5, help="A-Khata BBMP/BDA, RERA approved, Mivan monolithic tech")

active_weights = {
    "metro_proximity": w_metro,
    "traffic_integrity": w_traffic,
    "exact_distances": w_dist,
    "builder_pedigree": w_builder,
    "water_logging": w_water,
    "financials_appreciation": w_fin,
    "land_title_quality": w_legal
}
current_sum = sum(active_weights.values())

if current_sum == 100:
    st.sidebar.success(f"Total Weight: {current_sum}% (Balanced)")
else:
    st.sidebar.warning(f"Total Weight: {current_sum}% (Auto-normalizing to 100%)")

col_sb1, col_sb2 = st.sidebar.columns(2)
with col_sb1:
    if st.button("💾 Save Prefs", use_container_width=True):
        st.session_state.preferences["weights"] = active_weights
        st.session_state.preferences["search_center"]["radius_km"] = custom_radius
        save_user_preferences(st.session_state.preferences)
        st.sidebar.success("Preferences Saved!")
with col_sb2:
    if st.button("🔄 Defaults", use_container_width=True):
        default_prefs = get_user_preferences()
        st.session_state.preferences["weights"] = {
            "metro_proximity": 15,
            "traffic_integrity": 20,
            "exact_distances": 15,
            "builder_pedigree": 15,
            "water_logging": 10,
            "financials_appreciation": 15,
            "land_title_quality": 10
        }
        st.session_state.preferences["search_center"] = {"lat": 12.9325, "lng": 77.6850, "radius_km": 3.5}
        save_user_preferences(st.session_state.preferences)
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Critical Anchors Configuration")
st.sidebar.caption("Office: RMZ Ecospace / PTP | School: New Horizon Gurukul | Hospital: Sakra World")

# -------------------------------------------------------------
# Main Application Tabs
# -------------------------------------------------------------
tab_purchase, tab_rental, tab_trends, tab_pedigree, tab_architecture = st.tabs([
    "🏢 Purchase & Investment Radar",
    "🏡 Rental House Discovery Radar",
    "📊 Price Trends & Market Analytics",
    "⚖️ Builder Pedigree & Legal Verification",
    "⚙️ Daily Tracker & Architecture"
])

# =============================================================
# TAB 1: PURCHASE & INVESTMENT RADAR
# =============================================================
with tab_purchase:
    st.subheader("🗺️ Micro-Market Interactive Geofence & Property Radar")
    st.markdown(
        "Explore the East Bengaluru corridor with **strict geofencing constraint enforcement**. "
        "Allowed **Green Zones** (Bellandur Core, Green Glen Layout, Kadubeesanahalli Gurukul side) are protected, "
        "while **Red Zones** (Panathur Main Road choke point and railway underpass) incur an automatic **-50 pts penalty**."
    )

    # Calculate scores for all properties
    scored_properties = []
    for p in properties:
        breakdown = compute_property_match_score(p, weights=active_weights)
        p_copy = dict(p)
        p_copy.update(breakdown)
        scored_properties.append(p_copy)

    # Quick Filters Bar
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        zone_filter = st.selectbox(
            "Filter by Zone",
            ["All Zones", "Green Zones Only (Safe from Panathur)", "Red Zones (Choke Point Contrast)"]
        )
    with col_f2:
        builder_filter = st.selectbox(
            "Builder Pedigree",
            ["All Builders", "Tier 1 (Top 10 Premier)", "Tier 2 (Secondary)", "Local"]
        )
    with col_f3:
        min_score = st.slider("Minimum Match Score", 0, 100, 40, step=5)
    with col_f4:
        budget_filter = st.slider("Budget Max (₹ Cr)", 0.5, 6.0, 6.0, step=0.25)

    # Filter properties
    filtered_props = []
    for p in scored_properties:
        if zone_filter == "Green Zones Only (Safe from Panathur)" and p["zone_type"] != "Green":
            continue
        if zone_filter == "Red Zones (Choke Point Contrast)" and p["zone_type"] != "Red":
            continue
        if builder_filter != "All Builders" and builder_filter.split()[0].lower() not in p["builder_tier_label"].lower():
            continue
        if p["final_match_score"] < min_score:
            continue
        if p["total_price_cr"] > budget_filter:
            continue
        filtered_props.append(p)

    # Sort descending by Match Score
    filtered_props.sort(key=lambda x: x["final_match_score"], reverse=True)

    # Build Interactive Folium Map
    center_lat = search_center.get("lat", 12.9325)
    center_lng = search_center.get("lng", 77.6850)
    
    m = folium.Map(location=[center_lat, center_lng], zoom_start=13, tiles="cartodbpositron")

    # Add Green Zones
    for gz in market_zones.get("green_zones", []):
        poly = gz.get("polygon")
        if poly:
            folium.Polygon(
                locations=poly,
                color="#10B981",
                weight=2,
                fill=True,
                fill_color="#10B981",
                fill_opacity=0.18,
                tooltip=f"<b>Allowed Green Zone</b>: {gz['name']}<br>{gz['description']}"
            ).add_to(m)

    # Add Red Zones (Panathur Bottlenecks)
    for rz in market_zones.get("red_zones", []):
        poly = rz.get("polygon")
        if poly:
            folium.Polygon(
                locations=poly,
                color="#EF4444",
                weight=3,
                fill=True,
                fill_color="#EF4444",
                fill_opacity=0.28,
                tooltip=f"<b>Strict Red Zone (Choke Point)</b>: {rz['name']}<br>⚠️ Penalty: {rz['penalty_points']} pts<br>{rz['reason']}"
            ).add_to(m)

    # Add Metro Line Phase 2A Alignment Polyline
    metro_coords = [
        [12.9170, 77.6740], # Near Central Silk Board link
        [12.9275, 77.6825], # Bellandur Metro
        [12.9380, 77.6950], # Kadubeesanahalli Metro
        [12.9510, 77.7020]  # Marathahalli link
    ]
    folium.PolyLine(
        locations=metro_coords,
        color="#3B82F6",
        weight=4,
        dash_array="6, 6",
        tooltip="<b>ORR Metro Blue Line (Phase 2A)</b> - Silk Board to KR Puram"
    ).add_to(m)

    # Add Metro Stations
    for stn in anchors.get("metro_anchors", []):
        folium.Marker(
            location=[stn["lat"], stn["lng"]],
            popup=f"<b>🚇 {stn['name']}</b><br>{stn['line']}<br>Status: {stn['status']}",
            tooltip=f"🚇 {stn['name']}",
            icon=folium.Icon(color="blue", icon="subway", prefix="fa")
        ).add_to(m)

    # Add Critical Anchors
    for office in anchors.get("office_anchors", []):
        folium.Marker(
            location=[office["lat"], office["lng"]],
            popup=f"<b>💼 {office['name']}</b><br>Key Tenants: {', '.join(office.get('companies', []))}",
            tooltip=f"💼 {office['name']}",
            icon=folium.Icon(color="purple", icon="briefcase", prefix="fa")
        ).add_to(m)

    for school in anchors.get("school_anchors", []):
        folium.Marker(
            location=[school["lat"], school["lng"]],
            popup=f"<b>🎓 {school['name']}</b><br>{school.get('highlights', '')}",
            tooltip=f"🎓 {school['name']}",
            icon=folium.Icon(color="cadetblue", icon="graduation-cap", prefix="fa")
        ).add_to(m)

    for hosp in anchors.get("hospital_anchors", []):
        folium.Marker(
            location=[hosp["lat"], hosp["lng"]],
            popup=f"<b>🏥 {hosp['name']}</b><br>{hosp.get('highlights', '')}",
            tooltip=f"🏥 {hosp['name']}",
            icon=folium.Icon(color="pink", icon="heartbeat", prefix="fa")
        ).add_to(m)

    # Add Property Pins with Match Score Badges
    for prop in filtered_props:
        score = prop["final_match_score"]
        if score >= 80:
            pin_color = "green"
            pin_icon = "star"
        elif score >= 60:
            pin_color = "orange"
            pin_icon = "home"
        else:
            pin_color = "red"
            pin_icon = "exclamation-triangle"

        popup_html = f"""
        <div style="font-family: sans-serif; width: 220px;">
            <h4 style="margin: 0; color: #0F172A;">{prop['name']}</h4>
            <p style="margin: 3px 0; font-size: 12px; color: #475569;"><b>Builder:</b> {prop['builder']} ({prop['builder_tier']})</p>
            <p style="margin: 3px 0; font-size: 13px; font-weight: bold; color: {'#16A34A' if score >= 75 else '#DC2626'};">
                Radar Match Score: {score} / 100
            </p>
            <p style="margin: 3px 0; font-size: 12px;"><b>Rate:</b> ₹{prop['price_per_sqft']:,} / sqft</p>
            <p style="margin: 3px 0; font-size: 12px;"><b>Avg Unit:</b> {prop['avg_bhk']} (~₹{prop['total_price_cr']} Cr)</p>
            <p style="margin: 3px 0; font-size: 11px; color: #64748B;"><b>Metro Distance:</b> {prop['dist_metro_km']} km</p>
            {f"<p style='margin: 4px 0; font-size: 11px; color: #DC2626; font-weight: bold;'>⚠️ {prop['traffic_notes'][:80]}...</p>" if prop['panathur_routing'] else "<p style='margin: 4px 0; font-size: 11px; color: #16A34A;'>✅ Zero Panathur Choke Dependency</p>"}
        </div>
        """

        folium.Marker(
            location=[prop["lat"], prop["lng"]],
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"{prop['name']} - Score: {score}",
            icon=folium.Icon(color=pin_color, icon=pin_icon, prefix="fa")
        ).add_to(m)

    # Render Folium Map in Streamlit
    map_col, info_col = st.columns([7, 3])
    with map_col:
        map_output = st_folium(m, width="100%", height=520, returned_objects=["last_clicked"])
    
    with info_col:
        st.markdown("#### 🧭 Map Legend & Proximity")
        st.markdown("""
        - 🟢 **Green Polygons**: Allowed Prime Zones (Bellandur Core, Green Glen, Kadubeesanahalli Gurukul)
        - 🔴 **Red Polygons**: Strictly Blacklisted Bottlenecks (Panathur Main Rd & Underpass)
        - 🔵 **Dashed Line**: ORR Blue Line Metro Phase 2A
        - 💼 **Purple Pins**: Major Tech Parks (Ecospace, PTP, ETV)
        - 🎓 **Blue Pins**: Schools (New Horizon Gurukul)
        - 🏥 **Pink Pins**: Sakra World Hospital
        """)

        if map_output and map_output.get("last_clicked"):
            lat_c = map_output["last_clicked"]["lat"]
            lng_c = map_output["last_clicked"]["lng"]
            st.info(f"📍 **Clicked Pin:** Lat `{lat_c:.4f}`, Lng `{lng_c:.4f}`")
            if st.button("Set as Custom Search Center"):
                st.session_state.preferences["search_center"]["lat"] = lat_c
                st.session_state.preferences["search_center"]["lng"] = lng_c
                save_user_preferences(st.session_state.preferences)
                st.toast("Updated corridor search center!")
                st.rerun()

    st.markdown("---")
    st.subheader(f"📋 Evaluated Properties ({len(filtered_props)} Matching Criteria)")

    # Property Cards & Radar Breakdown
    for prop in filtered_props:
        is_red = prop["panathur_routing"]
        score = prop["final_match_score"]
        border_color = "#DC2626" if is_red else ("#10B981" if score >= 80 else "#F59E0B")
        
        with st.container():
            st.markdown(f"""
            <div class="property-card" style="border-left: 6px solid {border_color};">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap;">
                    <div>
                        <h3 style="margin: 0; color: #F8FAFC; display: inline-block;">{prop['name']}</h3>
                        <span class="{ 'badge-red' if is_red else 'badge-green' }" style="margin-left: 10px;">
                            {'⚠️ Panathur Bottleneck Penalized (-50 pts)' if is_red else '🛡️ Green Route Compliant'}
                        </span>
                        <p style="margin: 4px 0; color: #94A3B8; font-size: 0.95rem;">
                            <b>Developer:</b> {prop['builder']} &nbsp;|&nbsp; 
                            <b>Hierarchy:</b> <span style="color: #38BDF8;">{prop['builder_tier_label']}</span> &nbsp;|&nbsp; 
                            <b>Micro-Market:</b> {prop['micro_market']}
                        </p>
                    </div>
                    <div style="text-align: right;">
                        <span style="font-size: 1.8rem; font-weight: 800; color: {'#EF4444' if is_red else ('#10B981' if score >= 80 else '#F59E0B')};">
                            {score}
                        </span>
                        <span style="color: #64748B; font-size: 1.0rem;"> / 100</span>
                        <div style="font-size: 0.8rem; color: #94A3B8;">Dynamic Match Score</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            c_info1, c_info2, c_chart = st.columns([3, 3, 4])
            
            with c_info1:
                st.markdown("**💰 Financials & Pricing:**")
                st.markdown(f"- **Price / sqft:** ₹{prop['price_per_sqft']:,} / sqft")
                st.markdown(f"- **Typical Config:** {prop['avg_bhk']} ({prop['sqft_range']} sqft)")
                st.markdown(f"- **Est. Capital Outlay:** ~₹{prop['total_price_cr']} Cr")
                st.markdown(f"- **YoY Price Growth:** `+{prop['yoy_growth_pct']}%`")
                st.markdown(f"- **Rental Yield:** `{prop['rental_yield_pct']}%`")
                st.markdown(f"- **Maintenance:** ₹{prop['maintenance_sqft']}/sqft/mo")

            with c_info2:
                st.markdown("**🛡️ Compliance & Route Integrity:**")
                st.markdown(f"- **Land Title:** {prop['land_title']}")
                st.markdown(f"- **RERA Status:** `{prop['rera_status']}` ({prop['rera_number']})")
                st.markdown(f"- **Construction:** {prop['construction_tech']}")
                st.markdown(f"- **Water Supply:** {prop['water_source']}")
                st.markdown(f"- **Drainage/Flood Risk:** {prop['water_logging_risk']}")
                st.markdown(f"- **Metro Distance:** `{prop['dist_metro_km']} km` (Blue Line)")
                st.markdown(f"- **Prestige Tech Park:** `{prop['dist_office_km']} km`")

            with c_chart:
                # Radar Chart of 7 Score Components
                categories = [
                    "Metro (15%)", "Traffic (20%)", "Distances (15%)", 
                    "Builder (15%)", "Drainage (10%)", "Financials (15%)", "Legal Title (10%)"
                ]
                values = [
                    prop["metro_proximity"],
                    prop["traffic_integrity"],
                    prop["exact_distances"],
                    prop["builder_pedigree"],
                    prop["water_logging"],
                    prop["financials_appreciation"],
                    prop["land_title_quality"]
                ]

                fig = go.Figure()
                fig.add_trace(go.Scatterpolar(
                    r=values + [values[0]],
                    theta=categories + [categories[0]],
                    fill='toself',
                    name=prop['name'],
                    line_color="#0D9488" if score >= 70 else "#EF4444",
                    fillcolor="rgba(13, 148, 136, 0.25)" if score >= 70 else "rgba(239, 68, 68, 0.2)"
                ))
                fig.update_layout(
                    polar=dict(
                        radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=8, color="#94A3B8")),
                        angularaxis=dict(tickfont=dict(size=9, color="#E2E8F0"))
                    ),
                    showlegend=False,
                    margin=dict(l=25, r=25, t=20, b=20),
                    height=200,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)"
                )
                st.plotly_chart(fig, use_container_width=True, key=f"radar_{prop['id']}")

            if is_red:
                st.error(f"🛑 **Bottleneck Alert:** {prop['traffic_notes']}")
            else:
                st.success(f"✨ **Route & Quality Verdict:** {prop['highlights']}")
            st.markdown("---")

# =============================================================
# TAB 2: RENTAL HOUSE DISCOVERY RADAR (Special Feature)
# =============================================================
with tab_rental:
    st.subheader("🏡 Rental House Discovery Radar (Vicinity Configured)")
    st.markdown(
        "Find high-caliber rental apartments specifically in the **Bellandur Core, Green Glen Layout, "
        "and Kadubeesanahalli (Gurukul side)** corridor. "
        "Compare prices across platforms (**NoBroker, 99acres, MagicBricks, Housing.com, Direct Owner**), "
        "calculate **Direct-from-Owner Brokerage Savings**, verify water/power infrastructure, and connect directly via WhatsApp!"
    )

    # Rental Filter Controls
    r_col1, r_col2, r_col3, r_col4 = st.columns(4)
    with r_col1:
        rent_vicinity = st.selectbox(
            "Target Rental Vicinity",
            ["All Configured Vicinities", "Green Glen Layout", "Bellandur Core", "Kadubeesanahalli (Gurukul Side)", "Panathur Road"]
        )
    with r_col2:
        rent_bhk = st.selectbox(
            "BHK Configuration",
            ["All BHKs", "2 BHK", "3 BHK", "4 BHK"]
        )
    with r_col3:
        rent_budget = st.slider("Max Monthly Rent (₹)", 30000, 160000, 100000, step=5000)
    with r_col4:
        furnishing_opt = st.selectbox(
            "Furnishing Status",
            ["All Furnishing", "Fully Furnished", "Semi Furnished", "Unfurnished"]
        )

    # Advanced Rental Checkboxes
    cb_col1, cb_col2, cb_col3, cb_col4 = st.columns(4)
    with cb_col1:
        exclude_panathur_rentals = st.checkbox("🚫 Zero-Panathur Bottlenecks Only", value=True)
    with cb_col2:
        direct_owner_only = st.checkbox("🔑 Direct Owner Only (0 Brokerage)", value=False)
    with cb_col3:
        bachelor_friendly_opt = st.checkbox("🧑‍🤝‍🧑 Bachelor Friendly", value=False)
    with cb_col4:
        pet_friendly_opt = st.checkbox("🐾 Pet Friendly", value=False)

    # Filter rental inventory
    filtered_rentals = []
    for r in rental_properties:
        if rent_vicinity != "All Configured Vicinities" and rent_vicinity.lower() not in r["micro_market"].lower():
            continue
        if rent_bhk != "All BHKs" and r["bhk"] != rent_bhk:
            continue
        if r["rent_pm"] > rent_budget:
            continue
        if furnishing_opt != "All Furnishing" and r["furnishing"] != furnishing_opt:
            continue
        if exclude_panathur_rentals and not r["panathur_bottleneck_free"]:
            continue
        if direct_owner_only and r["contact"]["type"] != "Direct Owner":
            continue
        if bachelor_friendly_opt and not r.get("bachelor_friendly", False):
            continue
        if pet_friendly_opt and not r.get("pet_friendly", False):
            continue
        filtered_rentals.append(r)

    st.markdown(f"**Found {len(filtered_rentals)} Curated Rental Properties matching your lifestyle preferences**")

    # Render Rental Property Cards
    for r in filtered_rentals:
        is_safe_traffic = r["panathur_bottleneck_free"]
        card_border = "#10B981" if is_safe_traffic else "#EF4444"
        savings = r.get("brokerage_savings_inr", 0)

        with st.container():
            st.markdown(f"""
            <div class="property-card" style="border-left: 6px solid {card_border};">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap;">
                    <div>
                        <h3 style="margin: 0; color: #F8FAFC;">{r['unit_title']}</h3>
                        <p style="margin: 4px 0; color: #38BDF8; font-weight: 600;">
                            🏢 {r['society_name']} &nbsp;|&nbsp; 📍 {r['micro_market']} &nbsp;|&nbsp; 📐 {r['area_sqft']} sqft &nbsp;|&nbsp; 🛋️ {r['furnishing']}
                        </p>
                    </div>
                    <div style="text-align: right;">
                        <span style="font-size: 1.8rem; font-weight: 800; color: #10B981;">₹{r['rent_pm']:,}</span>
                        <span style="color: #94A3B8; font-size: 0.95rem;"> / month</span>
                        <div style="color: #64748B; font-size: 0.85rem;">+ ₹{r['maintenance_pm']:,} Maint. | {r['security_deposit_months']} Months Deposit</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            r_info, r_platforms, r_contact = st.columns([3, 4, 3])

            with r_info:
                st.markdown("**Commute & Infrastructure:**")
                st.markdown(f"- **RMZ Ecospace:** `{r['commute_time_mins'].get('RMZ Ecospace', 10)} mins`")
                st.markdown(f"- **Prestige Tech Park:** `{r['commute_time_mins'].get('Prestige Tech Park', 10)} mins`")
                st.markdown(f"- **Embassy TechVillage:** `{r['commute_time_mins'].get('Embassy TechVillage', 8)} mins`")
                st.markdown(f"- **Water Supply:** {r['water_supply']}")
                st.markdown(f"- **Power Backup:** {r['power_backup']}")
                st.markdown(f"- **Tenant Profile:** {r['tenant_preference']}")
                if is_safe_traffic:
                    st.success(f"✅ {r['traffic_verdict']}")
                else:
                    st.error(f"⚠️ {r['traffic_verdict']}")

            with r_platforms:
                st.markdown("**📊 Listed Prices Across Platforms:**")
                
                # Multi-platform pricing table
                plat_rows = []
                for p_name, p_data in r.get("platforms", {}).items():
                    plat_rows.append({
                        "Platform": p_name.replace("_", " "),
                        "Listed Rent": f"₹{p_data['price']:,}/mo",
                        "Brokerage": "₹0 (Direct)" if p_data["brokerage"] == 0 else f"₹{p_data['brokerage']:,}",
                        "Status": p_data.get("badge", "")
                    })
                st.dataframe(pd.DataFrame(plat_rows), use_container_width=True, hide_index=True)

                if savings > 0:
                    st.markdown(f"""
                    <div class="badge-deal" style="margin-top: 6px; text-align: center;">
                        🎉 Connect via Direct Owner to Save ₹{savings:,} in Brokerage Fees!
                    </div>
                    """, unsafe_allow_html=True)

            with r_contact:
                contact = r.get("contact", {})
                st.markdown("**📞 Contact & Schedule Site Visit:**")
                st.markdown(f"- **Contact:** `{contact.get('name', 'Owner')}` ({contact.get('type')})")
                st.markdown(f"- **Phone:** `{contact.get('phone')}`")
                st.markdown(f"- **Best Time:** {contact.get('preferred_time')}")
                st.markdown(f"- **Availability:** `{r['available_from']}`")

                # Direct WhatsApp Link with pre-filled message
                wa_msg = urllib.parse.quote(
                    f"Hi {contact.get('name')}, I saw your rental listing for {r['bhk']} in {r['society_name']} "
                    f"on the East Bengaluru Real Estate Radar. Is it currently available for site visit?"
                )
                wa_url = f"https://wa.me/{contact.get('whatsapp')}?text={wa_msg}"
                
                st.markdown(f"""
                <a href="{wa_url}" target="_blank" style="text-decoration: none;">
                    <div style="background-color: #25D366; color: white; text-align: center; padding: 10px; border-radius: 8px; font-weight: 700; margin-top: 8px;">
                        💬 Chat on WhatsApp with Owner
                    </div>
                </a>
                """, unsafe_allow_html=True)

                # Visit Scheduler interactive widget
                visit_key = f"visit_{r['id']}"
                with st.expander("📅 Schedule Site Visit"):
                    visit_date = st.date_input("Visit Date", key=f"date_{r['id']}")
                    visit_time = st.selectbox("Preferred Slot", ["Morning (10 AM - 12 PM)", "Afternoon (2 PM - 4 PM)", "Evening (5 PM - 7 PM)"], key=f"time_{r['id']}")
                    if st.button("Confirm Visit Reminder", key=f"btn_{r['id']}"):
                        st.session_state.scheduled_visits[r['id']] = {
                            "society": r['society_name'],
                            "date": str(visit_date),
                            "slot": visit_time,
                            "contact": contact.get('phone')
                        }
                        st.success(f"Visit reminder noted for {visit_date} ({visit_time})!")

            st.markdown("---")

    # Interactive Rental Fair Rent Estimator
    st.subheader("🧮 Micro-Market Fair Rent & Landlord Yield Estimator")
    st.caption("Calculate fair rental price benchmark based on micro-market square-foot data and furnishing grade.")
    
    calc_c1, calc_c2, calc_c3, calc_c4 = st.columns(4)
    with calc_c1:
        calc_market = st.selectbox("Micro-Market", ["Green Glen Layout", "Bellandur Core", "Kadubeesanahalli (Gurukul)", "Panathur Choke Zone"])
    with calc_c2:
        calc_sqft = st.number_input("Super Built-up Area (sqft)", min_value=600, max_value=4000, value=1500, step=50)
    with calc_c3:
        calc_furnishing = st.selectbox("Furnishing Level", ["Semi Furnished (Wardrobes/Kitchen)", "Fully Furnished (With Appliances)", "Unfurnished"])
    with calc_c4:
        calc_prop_val = st.number_input("Property Asset Value (₹ Cr)", min_value=0.5, max_value=8.0, value=2.0, step=0.1)

    # Base rent rates per sqft for 2026
    rates_map = {
        "Green Glen Layout": 38.0,
        "Bellandur Core": 40.0,
        "Kadubeesanahalli (Gurukul)": 37.0,
        "Panathur Choke Zone": 27.0
    }
    base_rate = rates_map.get(calc_market, 35.0)
    if "Fully" in calc_furnishing:
        base_rate += 8.0
    elif "Unfurnished" in calc_furnishing:
        base_rate -= 5.0

    est_monthly_rent = round(calc_sqft * base_rate)
    est_annual_rent = est_monthly_rent * 12
    est_yield = round((est_annual_rent / (calc_prop_val * 10000000)) * 100, 2)
    fair_deposit = est_monthly_rent * 4

    st.info(
        f"💡 **Estimated Fair Market Rent:** `₹{est_monthly_rent:,} / month` &nbsp;|&nbsp; "
        f"**Standard 4-Month Deposit:** `₹{fair_deposit:,}` &nbsp;|&nbsp; "
        f"**Gross Rental Yield:** `{est_yield}%` (Corridor Avg: 3.8% - 4.4%)"
    )

# =============================================================
# TAB 3: PRICE TRENDS & MARKET ANALYTICS
# =============================================================
with tab_trends:
    st.subheader("📈 Micro-Market Price Appreciation & Bottleneck Discount Analytics")
    st.markdown(
        "Historical tracking from **2020 through 2026** demonstrates how infrastructure and traffic integrity "
        "drive severe price divergence. Projects in **Green Glen Layout** and **Kadubeesanahalli (Gurukul)** "
        "have appreciated **+115% to +122%**, whereas **Panathur Road** has suffered a persistent bottleneck discount."
    )

    if not hist_df.empty:
        # Time-Series Chart
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
            x=hist_df["date"], y=hist_df["sarjapur_road_psqft"],
            mode="lines+markers", name="Sarjapur Road Link", line=dict(color="#A855F7", width=2, dash="dash")
        ))
        fig_trend.add_trace(go.Scatter(
            x=hist_df["date"], y=hist_df["panathur_road_choke_psqft"],
            mode="lines+markers", name="Panathur Road (Choke Zone)", line=dict(color="#EF4444", width=2.5, dash="dot")
        ))

        fig_trend.update_layout(
            title="Capital Appreciation Per Square Foot (2020 - 2026)",
            xaxis_title="Timeline / Quarter",
            yaxis_title="Price (₹ / sqft)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=40, r=40, t=50, b=40),
            height=450,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=True, gridcolor="#334155"),
            yaxis=dict(showgrid=True, gridcolor="#334155")
        )
        st.plotly_chart(fig_trend, use_container_width=True)

        # Comparative Metrics
        first_row = hist_df.iloc[0]
        latest_row = hist_df.iloc[-1]

        def calc_cagr(start_val, end_val, years=6.5):
            return round(((end_val / start_val) ** (1 / years) - 1) * 100, 2)

        m_c1, m_c2, m_c3, m_c4 = st.columns(4)
        with m_c1:
            cagr_bell = calc_cagr(first_row['bellandur_core_psqft'], latest_row['bellandur_core_psqft'])
            st.metric("Bellandur Core CAGR", f"{cagr_bell}%", f"₹{latest_row['bellandur_core_psqft']:,} /sqft")
        with m_c2:
            cagr_glen = calc_cagr(first_row['green_glen_layout_psqft'], latest_row['green_glen_layout_psqft'])
            st.metric("Green Glen CAGR", f"{cagr_glen}%", f"₹{latest_row['green_glen_layout_psqft']:,} /sqft")
        with m_c3:
            cagr_kadu = calc_cagr(first_row['kadubeesanahalli_gurukul_psqft'], latest_row['kadubeesanahalli_gurukul_psqft'])
            st.metric("Gurukul Corridor CAGR", f"{cagr_kadu}%", f"₹{latest_row['kadubeesanahalli_gurukul_psqft']:,} /sqft")
        with m_c4:
            cagr_pana = calc_cagr(first_row['panathur_road_choke_psqft'], latest_row['panathur_road_choke_psqft'])
            st.metric("Panathur Choke CAGR", f"{cagr_pana}%", f"₹{latest_row['panathur_road_choke_psqft']:,} /sqft", delta_color="inverse")

        # Download CSV
        csv_data = hist_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Full Historical Rates CSV",
            data=csv_data,
            file_name="east_bengaluru_historical_prices.csv",
            mime="text/csv"
        )
    else:
        st.warning("Historical prices dataset not loaded.")

# =============================================================
# TAB 4: BUILDER PEDIGREE & LEGAL VERIFICATION HUB
# =============================================================
with tab_pedigree:
    st.subheader("⚖️ Builder Hierarchy & Legal Land Title Verification")
    st.markdown(
        "To guarantee structural longevity, flawless resale liquidity, and zero litigation risk, "
        "the application strictly benchmarks developers against our **Tier 1 (Top 10) and Tier 2** hierarchy, "
        "and validates projects against the **4 Mandatory Pillars of Due Diligence**."
    )

    col_ped1, col_ped2 = st.columns(2)
    with col_ped1:
        st.markdown("### 🏆 Primary Choices: Top 10 Tier 1 Developers")
        tier1_list = [
            ("1. Sobha Limited", "German engineering standards, in-house precast & interior fit-out factory, zero tolerance on title."),
            ("2. Prestige Group", "Largest listed developer in South India, institutional maintenance, benchmark liquidity."),
            ("3. Brigade Group", "World Trade Center & Orion Mall developer, strong legal vetting and punctual delivery."),
            ("4. Total Environment", "Ultra-luxury earth-sheltered roofs, handcrafted terracotta brick, supreme living aesthetics."),
            ("5. Godrej Properties", "Nationwide brand governance, publicly traded, strict RERA escrow management."),
            ("6. Embassy Group", "Pioneer of Indian REITs (Embassy Office Parks), institutional grade asset upkeep."),
            ("7. Puravankara Limited", "Over 45 years track record, Purva World-class precast engineering."),
            ("8. Assetz Property Group", "Smart contemporary architecture, high green cover, Singaporean capital backing."),
            ("9. Century Real Estate", "One of Bengaluru's largest land owners, clean titles and master-planned layouts."),
            ("10. Salarpuria Sattva Group", "ORR corporate park builder with extensive residential track record.")
        ]
        for name, desc in tier1_list:
            st.markdown(f"- **{name}**: {desc}")

    with col_ped2:
        st.markdown("### 🥈 Secondary Choices (Tier 2 Renowned)")
        tier2_list = [
            ("Sumadhura Infracon", "Strong regional footprint in Whitefield & ORR, punctual project execution."),
            ("Rohan Builders", "Renowned for 'Plus Home' concept — zero common walls, cross ventilation, Green Glen presence."),
            ("Arvind SmartSpaces", "Lalbhai Group pedigree, high corporate governance, master-planned townships."),
            ("Vajram Group", "Boutique high-spec residential developments in East and North Bengaluru."),
            ("Shriram Properties", "Established mid-market developer with institutional private equity investors."),
            ("NCC Urban", "Construction powerhouse with robust engineering (e.g. Nagarjuna Green Woods).")
        ]
        for name, desc in tier2_list:
            st.markdown(f"- **{name}**: {desc}")

    st.markdown("---")
    st.subheader("📋 4 Mandatory Due Diligence Pillars (Interactive Audit)")
    
    chk1 = st.checkbox("1. Verified BBMP / BDA A-Khata Title (Strictly avoid Panchayat / transitional B-Khata land)", key="chk_akhata")
    chk2 = st.checkbox("2. Active Karnataka RERA Verification (Check litigation history, delayed delivery, escrow accounts on rera.karnataka.gov.in)", key="chk_rera")
    chk3 = st.checkbox("3. Dual Water Source Assurance (Active Cauvery BWSSB connection + High-yield borewells + Dual piping STP)", key="chk_water")
    chk4 = st.checkbox("4. Storm-Water Drain (Rajakaluve) Setback Buffer Safety (No infringement on 30m primary / 15m secondary storm drain buffers)", key="chk_buffer")

    if chk1 and chk2 and chk3 and chk4:
        st.success("🎉 **100% Legal & Quality Compliance Verified!** This property satisfies all 4 core blueprint pillars.")
    else:
        st.warning("⚠️ Property is pending full 4-pillar verification. Complete all 4 audits prior to making a booking advance.")

    st.markdown("#### 🔗 Official Verification Portals:")
    col_l1, col_l2, col_l3 = st.columns(3)
    with col_l1:
        st.markdown("[Karnataka RERA Portal ↗](https://rera.karnataka.gov.in)")
    with col_l2:
        st.markdown("[BBMP e-Aasthi Property Record ↗](https://eaasthi.karnataka.gov.in)")
    with col_l3:
        st.markdown("[BMRDA Master Plan & Rajakaluve Maps ↗](https://bmrda.karnataka.gov.in)")

# =============================================================
# TAB 5: DAILY TRACKER & SYSTEM ARCHITECTURE
# =============================================================
with tab_architecture:
    st.subheader("⚙️ Automated Daily Tracker & System Architecture")
    st.markdown(
        "This project integrates automated daily micro-market tracking via **GitHub Actions**, "
        "executing every day at **06:00 UTC (11:30 AM IST)** to update rate snapshots and log price divergence."
    )

    t_col1, t_col2 = st.columns(2)
    with t_col1:
        st.markdown("### 🤖 GitHub Actions Cron Configuration")
        st.code("""
name: Daily Real Estate Price & Rental Radar Tracker

on:
  schedule:
    - cron: '0 6 * * *' # Executes daily at 06:00 UTC
  workflow_dispatch:

jobs:
  track-and-commit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python scripts/daily_tracker.py
      - run: |
          git config --global user.name "github-actions[bot]"
          git add data/historical_prices.csv data/daily_tracker_log.json
          git commit -m "chore(data): automated daily market rate snapshot [skip ci]"
          git push origin main
        """, language="yaml")

    with t_col2:
        st.markdown("### 📝 Latest Automated Daily Snapshot Log")
        st.json(tracker_log if tracker_log else {"status": "Awaiting initial run"})

        if st.button("⚡ Trigger Local Snapshot Update Now"):
            from scripts.daily_tracker import run_daily_tracker
            success = run_daily_tracker(dry_run=False, force=True)
            if success:
                st.success("Snapshot successfully generated and recorded!")
                st.rerun()

    st.markdown("---")
    st.markdown("### ☁️ Streamlit Cloud Deployment Guide")
    st.markdown("""
    1. **Repository Setup**: Push this codebase to [GitHub](https://github.com/purntripathi-cmd/South-east-bengaluru-real-estate-radar).
    2. **Connect Streamlit Cloud**: Go to [share.streamlit.io](https://share.streamlit.io), connect your GitHub account.
    3. **Deploy App**: Select `purntripathi-cmd/South-east-bengaluru-real-estate-radar`, branch `main`, main file path `app.py`.
    4. **Automatic Daily Sync**: The GitHub Action runs autonomously every day at 06:00 UTC and keeps your live Streamlit app updated!
    """)
