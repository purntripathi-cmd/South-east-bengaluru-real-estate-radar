#!/usr/bin/env python3
"""
Automated Daily Tracker for East Bengaluru Real Estate Radar
Monitors price trends, scrapes/updates price per square foot metrics,
calculates micro-market averages, and commits snapshots to data/historical_prices.csv.
"""

import os
import sys
import json
import random
import argparse
from datetime import datetime
import pandas as pd

# Ensure UTF-8 output on Windows consoles
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
HISTORICAL_CSV = os.path.join(DATA_DIR, "historical_prices.csv")
PROPERTIES_JSON = os.path.join(DATA_DIR, "properties.json")
RENTAL_JSON = os.path.join(DATA_DIR, "rental_properties.json")
SNAPSHOT_LOG = os.path.join(DATA_DIR, "daily_tracker_log.json")


def safe_print(msg):
    try:
        print(msg)
    except UnicodeEncodeError:
        # Fallback to ascii replacement for non-unicode console
        print(msg.encode('ascii', errors='replace').decode('ascii'))


def load_properties():
    if os.path.exists(PROPERTIES_JSON):
        with open(PROPERTIES_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def load_rental_properties():
    if os.path.exists(RENTAL_JSON):
        with open(RENTAL_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def calculate_micro_market_stats(properties):
    """Aggregate average price/sqft per micro market from active inventory."""
    stats = {
        "Bellandur Core": [],
        "Green Glen Layout": [],
        "Kadubeesanahalli (Gurukul Side)": [],
        "Panathur / Balagere Road": []
    }
    
    for p in properties:
        market = p.get("micro_market", "")
        psqft = p.get("price_per_sqft")
        if not psqft:
            continue
        
        if "Bellandur" in market:
            stats["Bellandur Core"].append(psqft)
        elif "Green Glen" in market:
            stats["Green Glen Layout"].append(psqft)
        elif "Kadubeesanahalli" in market:
            stats["Kadubeesanahalli (Gurukul Side)"].append(psqft)
        elif "Panathur" in market or "Balagere" in market:
            stats["Panathur / Balagere Road"].append(psqft)
            
    averages = {}
    for k, v in stats.items():
        if v:
            averages[k] = round(sum(v) / len(v), 2)
        else:
            averages[k] = None
    return averages


def run_daily_tracker(dry_run=False, force=False):
    today = datetime.now()
    today_str = today.strftime("%Y-%m-%d")
    current_quarter = f"{today.year}-Q{(today.month - 1) // 3 + 1}"
    
    safe_print("=" * 65)
    safe_print("[East Bengaluru Real Estate Radar] Daily Tracker Initiated")
    safe_print(f"Timestamp: {today.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    safe_print("Target Corridor: Bellandur, Green Glen Layout, Kadubeesanahalli (Gurukul)")
    safe_print("=" * 65)
    
    properties = load_properties()
    rental_props = load_rental_properties()
    safe_print(f"Loaded {len(properties)} purchase properties and {len(rental_props)} rental listings.")
    
    market_stats = calculate_micro_market_stats(properties)
    safe_print("\nCurrent Micro-Market Live Rate Averages (Active Inventory):")
    for market, avg in market_stats.items():
        safe_print(f"   * {market:32}: Rs {avg:,.0f} / sqft" if avg else f"   * {market:32}: N/A")
    
    # Check historical CSV
    if not os.path.exists(HISTORICAL_CSV):
        safe_print(f"Error: {HISTORICAL_CSV} not found.")
        return False
        
    df = pd.read_csv(HISTORICAL_CSV)
    last_row = df.iloc[-1]
    last_date = str(last_row["date"])
    safe_print(f"\nLast Historical Snapshot Record Date: {last_date} ({last_row['quarter']})")
    
    # Micro-market baseline prices with organic drift
    b_core = market_stats.get("Bellandur Core") or float(last_row.get("bellandur_core_psqft", 16800))
    g_glen = market_stats.get("Green Glen Layout") or float(last_row.get("green_glen_layout_psqft", 15800))
    k_guru = market_stats.get("Kadubeesanahalli (Gurukul Side)") or float(last_row.get("kadubeesanahalli_gurukul_psqft", 14900))
    p_road = market_stats.get("Panathur / Balagere Road") or float(last_row.get("panathur_road_choke_psqft", 9100))
    s_road = float(last_row.get("sarjapur_road_psqft", 13600))
    
    # Calculate price spread and bottleneck discount
    spread_pct = ((b_core - p_road) / b_core) * 100
    safe_print(f"\nMicro-Market Insights:")
    safe_print(f"   * Premium of Bellandur/Green Glen over Panathur Bottleneck: +{spread_pct:.1f}%")
    safe_print(f"   * Chronic Panathur Choke Point Discount: -Rs {(b_core - p_road):,.0f}/sqft")
    
    # Rental yield tracker
    rental_yields = [p.get("rental_yield_pct", 4.0) for p in properties if p.get("rental_yield_pct")]
    avg_yield = round(sum(rental_yields) / len(rental_yields), 2) if rental_yields else 4.2
    safe_print(f"   * Average Corridor Rental Yield: {avg_yield}%")
    
    needs_update = force or (last_date != today_str)
    
    if needs_update and not dry_run:
        new_row = {
            "quarter": current_quarter,
            "date": today_str,
            "bellandur_core_psqft": round(b_core, 0),
            "green_glen_layout_psqft": round(g_glen, 0),
            "kadubeesanahalli_gurukul_psqft": round(k_guru, 0),
            "panathur_road_choke_psqft": round(p_road, 0),
            "sarjapur_road_psqft": round(s_road, 0),
            "avg_rental_yield_pct": avg_yield,
            "notes": f"Automated daily snapshot {today_str} UTC"
        }
        
        # If date already in df, update it, otherwise append
        if today_str in df["date"].values:
            idx = df[df["date"] == today_str].index[0]
            for col, val in new_row.items():
                df.at[idx, col] = val
            safe_print(f"Updated existing row for {today_str}")
        else:
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            safe_print(f"Appended new daily tracker row for {today_str}")
            
        df.to_csv(HISTORICAL_CSV, index=False)
        safe_print(f"Successfully saved updated dataset to {HISTORICAL_CSV}")
    elif dry_run:
        safe_print("Dry run completed - no disk modifications made.")
    else:
        safe_print(f"Snapshot for {today_str} is already up-to-date.")
        
    # Write tracker execution log
    log_data = {
        "last_run_utc": datetime.now().isoformat(),
        "status": "SUCCESS",
        "properties_count": len(properties),
        "rental_count": len(rental_props),
        "rates_snapshot": {
            "bellandur_core": b_core,
            "green_glen_layout": g_glen,
            "kadubeesanahalli_gurukul": k_guru,
            "panathur_choke_zone": p_road
        },
        "panathur_bottleneck_spread_pct": round(spread_pct, 2),
        "avg_rental_yield_pct": avg_yield
    }
    
    with open(SNAPSHOT_LOG, "w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=2)
    safe_print(f"Execution log saved to {SNAPSHOT_LOG}")
    safe_print("=" * 65)
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Daily Price Tracker for East Bengaluru Real Estate Radar")
    parser.add_argument("--dry-run", action="store_true", help="Simulate run without writing to CSV")
    parser.add_argument("--force", action="store_true", help="Force append snapshot even if date matches")
    args = parser.parse_args()
    
    success = run_daily_tracker(dry_run=args.dry_run, force=args.force)
    sys.exit(0 if success else 1)
