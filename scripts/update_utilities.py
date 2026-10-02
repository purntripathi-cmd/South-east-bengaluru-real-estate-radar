"""
Updates utility infrastructure in properties.json, rental_properties.json,
nearby_properties.json, and gated_plots.json:
- Cauvery Line Connection
- STP (Sewage Treatment Plant)
- Water Softener
- Water Meter (Smart / Individual)
- Double Pipe Connection (Dual plumbing)
- Gas Pipe Connection (GAIL Gas PNG)
"""

import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

# 1. Update data/properties.json (Purchase Tab 1)
prop_utilities = {
    "prop_01": { # Sobha Iris
        "cauvery_connection": "BWSSB Cauvery Stage IV (Active - Daily Supply)",
        "stp_details": "220 KLD MBBR Plant (100% Recycled to Flushing & Landscaping)",
        "water_softener": "Centralized Ion-Exchange Softener (TDS reduced 780 -> 160 ppm)",
        "water_meter": "Individual Smart IoT Ultrasonic Meters (Consumption-based billing)",
        "double_pipe_connection": "100% Dual Piping (Fresh water taps + Treated STP toilet flush)",
        "gas_pipe_connection": "GAIL Gas Ltd Piped Natural Gas (PNG) Direct to Kitchen"
    },
    "prop_02": { # Prestige Sunnyside (Oak & Elm)
        "cauvery_connection": "BWSSB Cauvery Connected (Alternate Days Grid Supply)",
        "stp_details": "310 KLD SBR Plant (Zero Liquid Discharge ZLD Certified)",
        "water_softener": "Central Commercial Softener Plant (TDS ~190 ppm)",
        "water_meter": "Individual Digital Water Sub-meters in all units",
        "double_pipe_connection": "100% Dual Piping (Separate overhead flush tank)",
        "gas_pipe_connection": "GAIL Gas Ltd Piped Natural Gas (PNG) Active"
    },
    "prop_03": { # NCC Nagarjuna Green Woods
        "cauvery_connection": "BWSSB Cauvery Piped Line Connected",
        "stp_details": "180 KLD MBBR Biological STP (Treated water for flush & garden)",
        "water_softener": "Central Sand Filter + Softener Unit (TDS ~210 ppm)",
        "water_meter": "Individual Smart Water Meters Installed",
        "double_pipe_connection": "100% Dual Piping Installed & Operational",
        "gas_pipe_connection": "Central Reticulated Cylinder Bank (GAIL pipeline at gate)"
    },
    "prop_04": { # Rohan Jharoka II
        "cauvery_connection": "BWSSB Cauvery Line Active + Borewell Backup",
        "stp_details": "250 KLD Extended Aeration STP (Recycled for flush & lawns)",
        "water_softener": "Central Automated Dual-Bed Softener (TDS ~175 ppm)",
        "water_meter": "Individual IoT Smart Meters (App-based daily tracking)",
        "double_pipe_connection": "100% Dual Plumbing System (Double pipe flush)",
        "gas_pipe_connection": "GAIL Gas Ltd Piped Natural Gas (PNG) Active"
    },
    "prop_05": { # Sobha Marvella
        "cauvery_connection": "BWSSB Cauvery Stage IV (High Pressure Direct Supply)",
        "stp_details": "150 KLD German Membrane Bioreactor (MBR) STP (Ultra-filtration)",
        "water_softener": "Industrial Multi-Stage Water Softener & Iron Filter (TDS 150 ppm)",
        "water_meter": "High-Precision Ultrasonic Smart Water Meters",
        "double_pipe_connection": "100% Dual Piping with Copper Core Risers",
        "gas_pipe_connection": "GAIL Gas Ltd Piped Natural Gas (PNG) Active"
    },
    "prop_06": { # Salarpuria Sattva Senorita
        "cauvery_connection": "BWSSB Cauvery Municipal Line Active",
        "stp_details": "280 KLD MBBR Sewage Treatment Plant",
        "water_softener": "Central Water Softener Unit (TDS ~220 ppm)",
        "water_meter": "Individual Digital Sub-meters in each apartment",
        "double_pipe_connection": "100% Dual Piping for Toilet Flush & Garden",
        "gas_pipe_connection": "GAIL Gas Ltd Piped Natural Gas (PNG) Active"
    },
    "prop_07": { # Total Environment Pursuit of a Radical Rhapsody
        "cauvery_connection": "BWSSB Cauvery Stage IV + 10-Acre Lakeside Rainwater Harvest Reservoirs",
        "stp_details": "450 KLD Eco-Engineered SBR STP with UV Disinfection",
        "water_softener": "Central Automated Multi-Bed Softener + Dedicated RO Drinking Water Line",
        "water_meter": "Individual Smart Ultrasonic IoT Water Meters",
        "double_pipe_connection": "100% Dual Piping (Separate greywater toilet line)",
        "gas_pipe_connection": "GAIL Gas Ltd Piped PNG with Automatic Gas Leak Cut-off Sensor"
    },
    "prop_08": { # Assetz Canvas & Cove
        "cauvery_connection": "BWSSB Cauvery Municipal Line Connected",
        "stp_details": "320 KLD Advanced MBBR Sewage Treatment Plant",
        "water_softener": "Central Water Treatment & Softening Plant (TDS ~190 ppm)",
        "water_meter": "Individual IoT Smart Water Meters",
        "double_pipe_connection": "100% Dual Piping System Active",
        "gas_pipe_connection": "GAIL Gas Ltd Piped Natural Gas (PNG) Active"
    },
    "prop_09": { # Sobha Dream Acres
        "cauvery_connection": "No Direct Cauvery Yet (Tanker + Deep Borewells; Pipeline Laid)",
        "stp_details": "1,200 KLD Mega-Township STP (Treated water for flush & 81 acres)",
        "water_softener": "Central Town-Level Softening Plant (TDS ~280 ppm)",
        "water_meter": "Individual Smart Digital Water Meters",
        "double_pipe_connection": "100% Dual Piping (Treated STP flush active)",
        "gas_pipe_connection": "Centralized Reticulated Piped Gas Bank"
    },
    "prop_10": { # Balagere Lakeview Residency (Local Builder)
        "cauvery_connection": "No Cauvery Connection (100% Private Tanker Dependent)",
        "stp_details": "Basic Septic Tank Only (No STP / No Treated Water Recycling)",
        "water_softener": "No Softener (Raw Hard Borewell/Tanker Water, TDS > 950 ppm)",
        "water_meter": "No Individual Meter (Flat-rate water billing shared among flats)",
        "double_pipe_connection": "Single Pipe Only (No Dual Piping; Fresh tanker water flushed)",
        "gas_pipe_connection": "No Piped Gas (Individual LPG Cylinder delivery only)"
    }
}

with open(os.path.join(DATA_DIR, "properties.json"), "r", encoding="utf-8") as f:
    props = json.load(f)

for p in props:
    u = prop_utilities.get(p["id"], {})
    p.update(u)

with open(os.path.join(DATA_DIR, "properties.json"), "w", encoding="utf-8") as f:
    json.dump(props, f, indent=2, ensure_ascii=False)
print("Updated properties.json with utility infrastructure.")

# 2. Update data/rental_properties.json (Rental Tab 2)
rental_utilities = {
    "rent_01": { # Sobha Iris 3BHK
        "cauvery_connection": "BWSSB Cauvery Active (Daily Direct Supply)",
        "stp_details": "220 KLD MBBR STP (Flushing recycled)",
        "water_softener": "Central Softener Active (TDS ~160 ppm)",
        "water_meter": "Individual Smart Ultrasonic Meter (Billed on exact usage)",
        "double_pipe_connection": "100% Dual Piping (STP Flush)",
        "gas_pipe_connection": "GAIL Piped Gas Active in Kitchen"
    },
    "rent_02": { # Prestige Sunnyside 3BHK
        "cauvery_connection": "BWSSB Cauvery Active (Alternate Days)",
        "stp_details": "310 KLD SBR Plant (Zero Liquid Discharge)",
        "water_softener": "Central Softening Plant Active (TDS ~190 ppm)",
        "water_meter": "Individual Digital Sub-meter",
        "double_pipe_connection": "100% Dual Piping (Dual Flush)",
        "gas_pipe_connection": "GAIL Piped Gas Connected"
    },
    "rent_03": { # NCC Nagarjuna Green Woods 2.5BHK
        "cauvery_connection": "BWSSB Cauvery Piped Supply",
        "stp_details": "180 KLD MBBR STP (100% Recycled to flush)",
        "water_softener": "Central Softener + Sand Filter",
        "water_meter": "Individual Smart Water Meter",
        "double_pipe_connection": "Dual Piping Active",
        "gas_pipe_connection": "Reticulated Gas Bank Active"
    },
    "rent_04": { # Rohan Jharoka II 2BHK
        "cauvery_connection": "BWSSB Cauvery Active + Borewell",
        "stp_details": "250 KLD Aeration STP (Recycled flushing)",
        "water_softener": "Central Automated Dual-Bed Softener",
        "water_meter": "Individual Smart IoT Meter",
        "double_pipe_connection": "100% Dual Piping (Double Pipe)",
        "gas_pipe_connection": "GAIL Piped Gas Active"
    },
    "rent_05": { # Sobha Marvella 4BHK Penthouse
        "cauvery_connection": "BWSSB Cauvery High Pressure Line",
        "stp_details": "150 KLD German MBR Membrane STP",
        "water_softener": "Industrial Multi-Stage Softener (TDS 150 ppm)",
        "water_meter": "Ultrasonic Smart Water Meter",
        "double_pipe_connection": "100% Dual Piping with Copper Lines",
        "gas_pipe_connection": "GAIL Piped Gas Active"
    },
    "rent_06": { # Assetz Canvas & Cove 2BHK
        "cauvery_connection": "BWSSB Cauvery Connected",
        "stp_details": "320 KLD Advanced MBBR STP",
        "water_softener": "Central Softening Plant (TDS ~190 ppm)",
        "water_meter": "Individual IoT Smart Water Meter",
        "double_pipe_connection": "100% Dual Piping Active",
        "gas_pipe_connection": "GAIL Piped Gas Active"
    },
    "rent_07": { # Sobha Dream Acres 2BHK
        "cauvery_connection": "Tanker + Borewell (Cauvery line laid, awaiting meter)",
        "stp_details": "1,200 KLD Central Township STP",
        "water_softener": "Central Softening Unit (TDS ~280 ppm)",
        "water_meter": "Individual Digital Sub-meter",
        "double_pipe_connection": "100% Dual Piping (STP Flush)",
        "gas_pipe_connection": "Central Reticulated Gas Bank"
    }
}

with open(os.path.join(DATA_DIR, "rental_properties.json"), "r", encoding="utf-8") as f:
    rentals = json.load(f)

for r in rentals:
    u = rental_utilities.get(r["id"], {})
    r.update(u)

with open(os.path.join(DATA_DIR, "rental_properties.json"), "w", encoding="utf-8") as f:
    json.dump(rentals, f, indent=2, ensure_ascii=False)
print("Updated rental_properties.json with utility infrastructure.")

# 3. Update data/nearby_properties.json (Nearby Tab 3)
nearby_utilities = {
    "nearby_01": { # Godrej Lake Gardens
        "cauvery_connection": "BWSSB Cauvery Municipal Line Active",
        "stp_details": "210 KLD MBBR STP (100% Recycled for flushing)",
        "water_softener": "Central Water Softener (TDS ~185 ppm)",
        "water_meter": "Individual IoT Smart Ultrasonic Meters",
        "double_pipe_connection": "100% Dual Piping Installed",
        "gas_pipe_connection": "GAIL Gas Ltd Piped PNG Active"
    },
    "nearby_02": { # Brigade Cornerstone Utopia
        "cauvery_connection": "BWSSB Cauvery Main Feeder Line Connected",
        "stp_details": "850 KLD Integrated Township SBR STP",
        "water_softener": "Central Industrial Softening Plant (TDS ~170 ppm)",
        "water_meter": "Individual Smart Digital Water Meters",
        "double_pipe_connection": "100% Dual Piping (STP Flush to all towers)",
        "gas_pipe_connection": "GAIL Gas Ltd Piped PNG Active"
    },
    "nearby_03": { # Purva Fairmont
        "cauvery_connection": "BWSSB Cauvery Active (Daily Municipal Supply)",
        "stp_details": "190 KLD MBBR Sewage Treatment Plant",
        "water_softener": "Central Automated Water Softener (TDS ~195 ppm)",
        "water_meter": "Individual Digital Water Sub-meters",
        "double_pipe_connection": "100% Dual Piping System Active",
        "gas_pipe_connection": "GAIL Gas Ltd Piped PNG Active"
    },
    "nearby_04": { # Purva Riviera
        "cauvery_connection": "BWSSB Cauvery Connection Active",
        "stp_details": "320 KLD Extended Aeration STP (Recycled for landscaping & flush)",
        "water_softener": "Central Softening Plant (TDS ~200 ppm)",
        "water_meter": "Individual Water Sub-meters",
        "double_pipe_connection": "Dual Pipe Plumbing Active",
        "gas_pipe_connection": "GAIL Gas Ltd Piped PNG Active"
    },
    "nearby_05": { # SJR Palazza City
        "cauvery_connection": "BWSSB Cauvery Piped Supply + Borewells",
        "stp_details": "260 KLD MBBR STP",
        "water_softener": "Central Water Treatment & Softening Plant",
        "water_meter": "Individual Smart Digital Meters",
        "double_pipe_connection": "100% Dual Piping Active",
        "gas_pipe_connection": "Reticulated Gas Cylinder Bank (GAIL pipeline in progress)"
    },
    "nearby_06": { # Prestige Lakeside Habitat
        "cauvery_connection": "BWSSB Cauvery Line + 102-Acre Township Rainwater Reservoirs",
        "stp_details": "1,500 KLD SBR Sewage Treatment Plant (Treated water for flush & 80 acres greens)",
        "water_softener": "Centralized Water Softening & Filtration Plant (TDS ~175 ppm)",
        "water_meter": "Individual IoT Smart Ultrasonic Meters",
        "double_pipe_connection": "100% Dual Piping (Separate toilet flush line)",
        "gas_pipe_connection": "GAIL Gas Ltd Piped PNG Active"
    }
}

with open(os.path.join(DATA_DIR, "nearby_properties.json"), "r", encoding="utf-8") as f:
    nearby = json.load(f)

for nb in nearby:
    u = nearby_utilities.get(nb["id"], {})
    nb.update(u)

with open(os.path.join(DATA_DIR, "nearby_properties.json"), "w", encoding="utf-8") as f:
    json.dump(nearby, f, indent=2, ensure_ascii=False)
print("Updated nearby_properties.json with utility infrastructure.")

# 4. Update data/gated_plots.json (Gated Plots Tab 4)
plot_utilities = {
    "plot_prestige_great_acres": {
        "cauvery_connection": "BWSSB Cauvery Pipeline Laid to Plot Boundary",
        "stp_details": "Centralized 600 KLD Township STP (Treated flush line to plot edge)",
        "water_softener": "Central Township Softening Plant (TDS ~180 ppm)",
        "water_meter": "Smart Individual Digital Water Meter Provision per Plot",
        "double_pipe_connection": "Dual Utility Trench (Fresh Cauvery Water + STP Treated Flush Water)",
        "gas_pipe_connection": "Underground GAIL Gas Piped PNG Conduit to Plot Boundary"
    },
    "plot_purva_tivoli_hills": {
        "cauvery_connection": "Cauvery Feeder Grid Connected + 2.5 Lakh L Underground Sump",
        "stp_details": "Central Eco-STP with Underground Drainage Network",
        "water_softener": "Centralized Water Treatment & Softener Plant",
        "water_meter": "Individual Smart IoT Water Connection Points",
        "double_pipe_connection": "Dual Plumbing Utility Corridors Laid along all 40-ft Avenues",
        "gas_pipe_connection": "Piped Gas (GAIL Gas) Underground Utility Ducting"
    },
    "plot_sobha_canvas": {
        "cauvery_connection": "BWSSB Cauvery Connection Point Active at Plot Entrance",
        "stp_details": "Sobha Engineering 350 KLD MBBR Layout STP",
        "water_softener": "Central Multi-Bed Softener Plant (TDS ~165 ppm)",
        "water_meter": "Smart Ultrasonic Individual Plot Meter Inlets",
        "double_pipe_connection": "100% Dual Piping (Separate line for villa landscaping & flushing)",
        "gas_pipe_connection": "Dedicated GAIL Gas Piped PNG Line to Every Plot"
    },
    "plot_sattva_green_groves": {
        "cauvery_connection": "BWSSB Cauvery Municipal Line Active + Borewell Recharge",
        "stp_details": "Centralized SBR Sewage Treatment Plant",
        "water_softener": "Central Softening Plant",
        "water_meter": "Individual Digital Water Meters Provisioned",
        "double_pipe_connection": "Dual Pipe Water Lines to Plot Boundary",
        "gas_pipe_connection": "Underground Piped Gas Provision"
    },
    "plot_classic_featherlite_orchards": {
        "cauvery_connection": "BWSSB Cauvery Municipal Water Connection Active",
        "stp_details": "Modern Underground STP with Odorless Bio-filter",
        "water_softener": "Central Automated Softening Unit",
        "water_meter": "Individual Smart Water Meters",
        "double_pipe_connection": "Dual Line Water Supply (Potable + Recycled Garden)",
        "gas_pipe_connection": "GAIL Gas Pipeline Connected to Layout Gateway"
    },
    "plot_assetz_earth_essence": {
        "cauvery_connection": "BWSSB Cauvery Feeder + 100% Rainwater Harvesting Aquifers",
        "stp_details": "Bio-Engineered Wetland & SBR STP (Zero Chemical Runoff)",
        "water_softener": "Central Multi-Stage Softening Plant",
        "water_meter": "Individual IoT Smart Ultrasonic Water Meters",
        "double_pipe_connection": "Dual Piping Network (Drinking water + Treated landscape water)",
        "gas_pipe_connection": "Piped Natural Gas (GAIL Gas) Network Provisioned"
    }
}

with open(os.path.join(DATA_DIR, "gated_plots.json"), "r", encoding="utf-8") as f:
    plots = json.load(f)

for pl in plots:
    u = plot_utilities.get(pl["id"], {})
    pl.update(u)

with open(os.path.join(DATA_DIR, "gated_plots.json"), "w", encoding="utf-8") as f:
    json.dump(plots, f, indent=2, ensure_ascii=False)
print("Updated gated_plots.json with utility infrastructure.")
