"""
Core Parameter Matrix & Weighted Scoring Engine
Computes dynamic match score (0-100) using multi-criteria weighted sum formula,
builder hierarchy evaluation, and traffic penalty enforcement.
"""

TIER_1_BUILDERS = [
    "sobha limited",
    "prestige group",
    "brigade group",
    "total environment building systems",
    "godrej properties",
    "embassy group",
    "puravankara limited",
    "assetz property group",
    "century real estate",
    "salarpuria sattva group",
    "salarpuria sattva"
]

TIER_2_BUILDERS = [
    "sumadhura infracon",
    "sumadhura",
    "rohan builders",
    "arvind smartspaces",
    "arvind",
    "vajram group",
    "shriram properties",
    "ncc urban"
]


def score_metro_proximity(dist_km):
    """
    < 1km = 100%, 1-2km = 75%, 2-3km = 50%, > 3km = 30%
    """
    if dist_km is None:
        return 50.0
    if dist_km <= 1.0:
        return 100.0
    elif dist_km <= 2.0:
        return 75.0
    elif dist_km <= 3.0:
        return 50.0
    else:
        return 30.0


def score_traffic_integrity(is_panathur_routed, custom_penalty=-50):
    """
    Traffic & Route Integrity:
    Zero Panathur routing = 100%
    Panathur routing = Heavy penalty (-50 pts base)
    """
    if is_panathur_routed:
        return 0.0, custom_penalty
    return 100.0, 0.0


def score_exact_distances(dist_office, dist_school, dist_hosp, dist_mall, dist_airport):
    """
    Calculates composite proximity score incorporating peak hour congestion multipliers.
    """
    def dist_score(d, ideal_km):
        if d <= ideal_km:
            return 100.0
        elif d <= ideal_km * 2:
            return max(30.0, 100.0 - (d - ideal_km) * 20.0)
        else:
            return max(15.0, 50.0 - (d - ideal_km * 2) * 10.0)

    # Congestion-weighted sub-scores
    s_office = dist_score(dist_office, 1.5)   # Weight 40%
    s_school = dist_score(dist_school, 2.0)   # Weight 25%
    s_hosp   = dist_score(dist_hosp, 2.5)     # Weight 15%
    s_mall   = dist_score(dist_mall, 1.5)     # Weight 10%
    s_air    = dist_score(dist_airport, 45.0) # Weight 10%

    composite = (
        s_office * 0.40 +
        s_school * 0.25 +
        s_hosp * 0.15 +
        s_mall * 0.10 +
        s_air * 0.10
    )
    return round(composite, 1)


def score_builder_pedigree(builder_name, explicit_tier=None):
    """
    Tier 1 (Top 10) = 100%
    Tier 2 Secondary = 80%
    Local / Independent = 20%
    """
    if explicit_tier:
        if "tier 1" in explicit_tier.lower() or "top 10" in explicit_tier.lower():
            return 100.0, "Tier 1 (Top 10 Premier)"
        elif "tier 2" in explicit_tier.lower():
            return 80.0, "Tier 2 (Secondary Renowned)"
        else:
            return 20.0, "Local Developer"
            
    b_lower = builder_name.lower().strip()
    for t1 in TIER_1_BUILDERS:
        if t1 in b_lower:
            return 100.0, "Tier 1 (Top 10 Premier)"
            
    for t2 in TIER_2_BUILDERS:
        if t2 in b_lower:
            return 80.0, "Tier 2 (Secondary Renowned)"
            
    return 20.0, "Local Developer"


def score_water_drainage(elevation_masl, risk_desc, water_source):
    """
    Elevation check, historical monsoon vulnerability & lake buffer elevations.
    """
    score = 70.0
    # Elevation bonus (Green Glen / Gurukul ridge is ~895-905m; low lake basin is <885m)
    if elevation_masl >= 895:
        score += 20.0
    elif elevation_masl < 885:
        score -= 30.0

    r_lower = risk_desc.lower()
    if "none" in r_lower or "crest" in r_lower or "high zone" in r_lower:
        score += 10.0
    elif "high" in r_lower or "severe" in r_lower:
        score -= 30.0
        
    if "cauvery" in water_source.lower() and "dual" in water_source.lower():
        score += 5.0
    elif "tanker" in water_source.lower():
        score -= 20.0

    return max(10.0, min(100.0, score))


def score_financials(yoy_growth_pct, price_per_sqft, rental_yield_pct):
    """
    Evaluates historical micro-market price appreciation and yield.
    """
    # Appreciation score
    if yoy_growth_pct >= 14.0:
        app_score = 100.0
    elif yoy_growth_pct >= 10.0:
        app_score = 85.0
    elif yoy_growth_pct >= 6.0:
        app_score = 65.0
    else:
        app_score = 35.0
        
    # Rental yield score (3.5% - 4.5% is healthy for Bengaluru ORR)
    yield_score = min(100.0, (rental_yield_pct / 4.5) * 100.0)
    
    return round((app_score * 0.70) + (yield_score * 0.30), 1)


def score_land_title(land_title, rera_status, tech_desc):
    """
    Binary legal compliance check + construction tech weight.
    """
    score = 0.0
    # Title
    if "a-khata" in land_title.lower():
        score += 50.0
    else:
        score += 0.0 # B-khata penalty
        
    # RERA
    if "verified" in rera_status.lower() or "delivered" in rera_status.lower():
        score += 30.0
    elif "approved" in rera_status.lower():
        score += 25.0
    else:
        score += 0.0
        
    # Construction Tech (Mivan / Shear wall vs standard brick)
    if "mivan" in tech_desc.lower() or "monolithic" in tech_desc.lower() or "terracotta" in tech_desc.lower():
        score += 20.0
    else:
        score += 10.0
        
    return min(100.0, score)


def compute_property_match_score(prop, weights=None, custom_anchors=None):
    """
    Calculates dynamic Match Score (0-100) using weighted sum formula across 7 categories:
    1. Metro Proximity (Default 15%)
    2. Traffic & Route Integrity (Default 20%)
    3. Exact Distances (Default 15%)
    4. Builder Pedigree (Default 15%)
    5. Water Logging & Drainage (Default 10%)
    6. Financials & Appreciation (Default 15%)
    7. Land Title & Gated Quality (Default 10%)
    """
    if weights is None:
        weights = {
            "metro_proximity": 15,
            "traffic_integrity": 20,
            "exact_distances": 15,
            "builder_pedigree": 15,
            "water_logging": 10,
            "financials_appreciation": 15,
            "land_title_quality": 10
        }
        
    # Normalize weights to 100%
    total_w = sum(weights.values())
    w_norm = {k: v / total_w for k, v in weights.items()}
    
    # Category 1: Metro Proximity
    s_metro = score_metro_proximity(prop.get("dist_metro_km"))
    
    # Category 2: Traffic & Route Integrity
    is_panathur = prop.get("panathur_routing", False)
    s_traffic, traffic_penalty = score_traffic_integrity(is_panathur)
    
    # Category 3: Exact Distances
    s_dist = score_exact_distances(
        prop.get("dist_office_km", 2.0),
        prop.get("dist_school_km", 2.5),
        prop.get("dist_hospital_km", 2.0),
        prop.get("dist_mall_km", 2.0),
        prop.get("dist_airport_km", 46.0)
    )
    
    # Category 4: Builder Pedigree
    s_builder, builder_tier_label = score_builder_pedigree(
        prop.get("builder", ""),
        prop.get("builder_tier")
    )
    
    # Category 5: Water Logging & Drainage
    s_water = score_water_drainage(
        prop.get("elevation_masl", 890),
        prop.get("water_logging_risk", "Moderate"),
        prop.get("water_source", "Dual")
    )
    
    # Category 6: Financials & Appreciation
    s_fin = score_financials(
        prop.get("yoy_growth_pct", 10.0),
        prop.get("price_per_sqft", 10000),
        prop.get("rental_yield_pct", 4.0)
    )
    
    # Category 7: Land Title & Gated Quality
    s_legal = score_land_title(
        prop.get("land_title", "A-Khata"),
        prop.get("rera_status", "Verified"),
        prop.get("construction_tech", "RCC")
    )
    
    # Weighted base score
    base_score = (
        s_metro * w_norm["metro_proximity"] +
        s_traffic * w_norm["traffic_integrity"] +
        s_dist * w_norm["exact_distances"] +
        s_builder * w_norm["builder_pedigree"] +
        s_water * w_norm["water_logging"] +
        s_fin * w_norm["financials_appreciation"] +
        s_legal * w_norm["land_title_quality"]
    )
    
    # Apply penalty
    final_score = max(0.0, min(100.0, base_score + traffic_penalty))
    
    breakdown = {
        "metro_proximity": round(s_metro, 1),
        "traffic_integrity": round(s_traffic, 1),
        "exact_distances": round(s_dist, 1),
        "builder_pedigree": round(s_builder, 1),
        "water_logging": round(s_water, 1),
        "financials_appreciation": round(s_fin, 1),
        "land_title_quality": round(s_legal, 1),
        "traffic_penalty": traffic_penalty,
        "base_score": round(base_score, 1),
        "final_match_score": round(final_score, 1),
        "builder_tier_label": builder_tier_label,
        "is_disqualified": is_panathur
    }
    
    return breakdown
