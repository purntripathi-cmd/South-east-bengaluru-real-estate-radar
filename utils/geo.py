import math

def haversine_distance_km(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees).
    """
    R = 6371.0 # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)


def is_point_in_polygon(point, polygon):
    """
    Ray-casting algorithm to determine if a point (lat, lng) is inside a polygon.
    polygon is a list of [lat, lng] coordinates.
    """
    lat, lng = point
    n = len(polygon)
    inside = False
    
    p1_lat, p1_lng = polygon[0]
    for i in range(n + 1):
        p2_lat, p2_lng = polygon[i % n]
        if min(p1_lat, p2_lat) < lat <= max(p1_lat, p2_lat):
            if lng <= max(p1_lng, p2_lng):
                if p1_lat != p2_lat:
                    xinters = (lat - p1_lat) * (p2_lng - p1_lng) / (p2_lat - p1_lat) + p1_lng
                if p1_lng == p2_lng or lng <= xinters:
                    inside = not inside
        p1_lat, p1_lng = p2_lat, p2_lng
        
    return inside


def check_zone_membership(lat, lng, market_zones):
    """
    Determines if a location falls into Green Zone, Red Zone, or Neutral.
    Returns: (zone_type, zone_name, penalty)
    """
    point = (lat, lng)
    
    # Check Red Zones first (Panathur bottlenecks)
    for rz in market_zones.get("red_zones", []):
        poly = rz.get("polygon", [])
        center = rz.get("center", [])
        radius_km = rz.get("radius_meters", 800) / 1000.0
        
        in_poly = is_point_in_polygon(point, poly) if poly else False
        dist = haversine_distance_km(lat, lng, center[0], center[1]) if center else 999.0
        
        if in_poly or dist <= radius_km:
            return "Red", rz.get("name", "Blacklisted Choke Point"), rz.get("penalty_points", -50)
            
    # Check Green Zones
    for gz in market_zones.get("green_zones", []):
        poly = gz.get("polygon", [])
        center = gz.get("center", [])
        radius_km = gz.get("radius_meters", 1000) / 1000.0
        
        in_poly = is_point_in_polygon(point, poly) if poly else False
        dist = haversine_distance_km(lat, lng, center[0], center[1]) if center else 999.0
        
        if in_poly or dist <= radius_km:
            return "Green", gz.get("name", "Allowed Green Zone"), 0
            
    return "Neutral", "Corridor Buffer", 0
