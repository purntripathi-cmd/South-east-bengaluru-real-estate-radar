import folium
import streamlit as st
from streamlit_folium import st_folium

st.title("East Bengaluru Real Estate Radar & Map Configurator")

# Session State for Saving/Resetting Preferences
if "search_coords" not in st.session_state:
  st.session_state.search_coords = {"lat": 12.9350, "lng": 77.6850, "radius": 3}

st.sidebar.header("Map & Zone Settings")
if st.sidebar.button("Reset Preferences"):
  st.session_state.search_coords = {
      "lat": 12.9350,
      "lng": 77.6850,
      "radius": 3,
  }
  st.rerun()

# Create Folium Map centered around Bellandur / Green Glen Layout
m = folium.Map(location=[12.9350, 77.6850], zoom_start=14)

# Add Green Zone (Allowed Area: Green Glen / Kadubeesanahalli Gurukul side)
folium.Circle(
    location=[12.9350, 77.6850],
    radius=2000,
    color="green",
    fill=True,
    fill_color="green",
    fill_opacity=0.15,
    tooltip="Allowed Zone (Green Glen / Kadubeesanahalli)",
).add_to(m)

# Add Red Zone (Blacklisted Area: Panathur Main Road choke point)
folium.Circle(
    location=[12.9300, 77.7050],
    radius=1200,
    color="red",
    fill=True,
    fill_color="red",
    fill_opacity=0.2,
    tooltip="Restricted / Blacklisted Zone (Panathur Bottleneck)",
).add_to(m)

# Render map in Streamlit and capture interaction
output = st_folium(m, width=700, height=500)

if output and output.get("last_clicked"):
  clicked_lat = output["last_clicked"]["lat"]
  clicked_lng = output["last_clicked"]["lng"]
  st.success(f"Selected Target Pin: Lat {clicked_lat:.4f}, Lng {clicked_lng:.4f}")
  if st.button("Save as Search Center"):
    st.session_state.search_coords["lat"] = clicked_lat
    st.session_state.search_coords["lng"] = clicked_lng
    st.toast("Search center preference saved successfully!")
