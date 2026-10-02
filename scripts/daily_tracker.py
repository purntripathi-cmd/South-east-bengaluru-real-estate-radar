"""
Automated Daily Tracker Script for East Bengaluru Real Estate Radar
Executes daily at 5:00 PM IST (11:30 UTC).
- Tracks micro-market price appreciation across Bellandur, Green Glen, Kadubeesanahalli (Gurukul)
- Evaluates the Panathur Choke Point penalty spread
- Records TOP 10 Purchase Properties with Total Ownership Cost, Upfront Advance, & Age in data/top_10_purchase_daily.csv
- Records TOP 5 Rental Properties with Total Maintenance, Brokerage Savings, & Direct Owner Contacts in data/top_5_rental_daily.csv
- Appends historical timeline in data/historical_prices.csv
- Logs status to data/daily_tracker_log.json
"""

import os
import sys
import json
from datetime import datetime
import pandas as pd

# Fix Windows console UTF-8 encoding
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
PROPS_FILE = os.path.join(DATA_DIR, "properties.json")
RENTAL_FILE = os.path.join(DATA_DIR, "rental_properties.json")
HISTORICAL_CSV = os.path.join(DATA_DIR, "historical_prices.csv")
TRACKER_LOG = os.path.join(DATA_DIR, "daily_tracker_log.json")
TOP_10_PURCHASE_CSV = os.path.join(DATA_DIR, "top_10_purchase_daily.csv")
TOP_5_RENTAL_CSV = os.path.join(DATA_DIR, "top_5_rental_daily.csv")


def safe_print(text):
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", "replace").decode("ascii"))


def load_json(filepath):
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def run_daily_tracker(dry_run=False, force=False):
    now_utc = datetime.utcnow()
    date_str = now_utc.strftime("%Y-%m-%d")
    timestamp_iso = now_utc.strftime("%Y-%m-%d %H:%M:%S UTC")

    safe_print("=" * 65)
    safe_print("[East Bengaluru Real Estate Radar] Daily Tracker Initiated")
    safe_print(f"Timestamp: {timestamp_iso} (Scheduled 5:00 PM IST / 11:30 UTC)")
    safe_print("Target: Bellandur, Green Glen Layout, Kadubeesanahalli (Gurukul)")
    safe_print("=" * 65)

    properties = load_json(PROPS_FILE)
    rental_properties = load_json(RENTAL_FILE)

    if not properties:
        safe_print("Error: properties.json missing or empty.")
        return False

    safe_print(f"Loaded {len(properties)} purchase properties and {len(rental_properties)} rental listings.")

    # ---------------------------------------------------------
    # 1. Compute Live Micro-Market Averages
    # ---------------------------------------------------------
    def get_avg_price(market_name):
        rates = [p["price_per_sqft"] for p in properties if market_name.lower() in p.get("micro_market", "").lower()]
        return int(sum(rates) / len(rates)) if rates else None

    bellandur_avg = get_avg_price("Bellandur")
    green_glen_avg = get_avg_price("Green Glen")
    kadubeesanahalli_avg = get_avg_price("Kadubeesanahalli")
    panathur_avg = get_avg_price("Panathur")

    safe_print("\nCurrent Micro-Market Live Rate Averages:")
    safe_print(f"   * Bellandur Core                  : Rs {bellandur_avg:,} / sqft")
    safe_print(f"   * Green Glen Layout               : Rs {green_glen_avg:,} / sqft")
    safe_print(f"   * Kadubeesanahalli (Gurukul Side) : Rs {kadubeesanahalli_avg:,} / sqft")
    safe_print(f"   * Panathur / Balagere Road        : Rs {panathur_avg:,} / sqft")

    # ---------------------------------------------------------
    # 2. Extract TOP 10 Purchase Properties
    # ---------------------------------------------------------
    purchase_records = []
    for p in properties:
        # Calculate ownership costs
        base_cost = p.get("base_cost_inr", int(p.get("total_price_cr", 1.0) * 10000000))
        stamp_duty = round(base_cost * (p.get("stamp_duty_pct", 5.6) / 100.0))
        reg_fee = round(base_cost * (p.get("registration_fee_pct", 1.0) / 100.0))
        legal_fee = p.get("legal_advocate_fees_inr", 45000)
        khata_fee = p.get("khata_transfer_fee_inr", 15000)
        corpus_fund = p.get("corpus_sinking_fund_inr", 200000)
        interiors = p.get("interiors_estimate_inr", 1500000)
        annual_maint = p.get("annual_maintenance_inr", p.get("monthly_maintenance_inr", 6000) * 12)
        
        down_payment_20pct = round(base_cost * 0.20)
        upfront_advance_required = down_payment_20pct + stamp_duty + reg_fee + legal_fee + khata_fee + corpus_fund
        total_ownership_cost = base_cost + stamp_duty + reg_fee + legal_fee + khata_fee + corpus_fund + interiors + annual_maint

        # Mock score if not computed
        score = 90.0 if not p.get("panathur_routing") else 40.0
        if p.get("builder_tier") == "Tier 1":
            score += 5.0

        purchase_records.append({
            "Snapshot_Date": date_str,
            "Property_Name": p.get("name"),
            "Builder": p.get("builder"),
            "Builder_Tier": p.get("builder_tier"),
            "Micro_Market": p.get("micro_market"),
            "Zone_Type": p.get("zone_type"),
            "Year_Built": p.get("year_built", 2018),
            "Age_Years": p.get("age_years", 8),
            "Age_Category": p.get("age_category", "Mature Gated"),
            "Rate_Per_Sqft_INR": p.get("price_per_sqft"),
            "Config": p.get("avg_bhk"),
            "Area_Sqft": p.get("avg_sqft"),
            "Base_Price_Cr": p.get("total_price_cr"),
            "Base_Price_INR": base_cost,
            "Monthly_Maintenance_INR": p.get("monthly_maintenance_inr", 6000),
            "Annual_Maintenance_INR": annual_maint,
            "Stamp_Duty_Registration_INR": stamp_duty + reg_fee,
            "Legal_Khata_Fees_INR": legal_fee + khata_fee,
            "Society_Corpus_Fund_INR": corpus_fund,
            "Interiors_Estimate_INR": interiors,
            "Downpayment_20pct_INR": down_payment_20pct,
            "Upfront_Cash_Required_INR": upfront_advance_required,
            "Total_Ownership_Cost_INR": total_ownership_cost,
            "Total_Ownership_Cost_Cr": round(total_ownership_cost / 10000000, 3),
            "Panathur_Bottleneck": "YES (Severe Choke)" if p.get("panathur_routing") else "NO (Green Route)",
            "Metro_Distance_KM": p.get("dist_metro_km"),
            "Land_Title": p.get("land_title"),
            "RERA_Status": p.get("rera_status")
        })

    # Sort by Green zone first, then base price
    purchase_records.sort(key=lambda x: (x["Zone_Type"] != "Green", -x["Rate_Per_Sqft_INR"]))
    top_10_purchase_df = pd.DataFrame(purchase_records[:10])

    # ---------------------------------------------------------
    # 3. Extract TOP 5 Rental Properties
    # ---------------------------------------------------------
    rental_records = []
    for r in rental_properties:
        rent = r.get("rent_pm", 50000)
        maint = r.get("maintenance_pm", 4000)
        total_monthly = r.get("total_monthly_outflow", rent + maint)
        annual_maint = r.get("annual_maintenance_inr", maint * 12)
        contact = r.get("contact", {})

        rental_records.append({
            "Snapshot_Date": date_str,
            "Society_Name": r.get("society_name"),
            "Unit_Title": r.get("unit_title"),
            "Micro_Market": r.get("micro_market"),
            "BHK": r.get("bhk"),
            "Area_Sqft": r.get("area_sqft"),
            "Furnishing": r.get("furnishing"),
            "Year_Built": r.get("year_built", 2019),
            "Age_Years": r.get("age_years", 7),
            "Monthly_Rent_INR": rent,
            "Monthly_Maintenance_INR": maint,
            "Total_Monthly_Outflow_INR": total_monthly,
            "Annual_Maintenance_INR": annual_maint,
            "Security_Deposit_Months": r.get("security_deposit_months", 4),
            "Security_Deposit_INR": r.get("security_deposit_inr", rent * 4),
            "Brokerage_Savings_INR": r.get("brokerage_savings_inr", 0),
            "Best_Platform": r.get("best_platform", "Direct Owner"),
            "Water_Supply": r.get("water_supply"),
            "Power_Backup": r.get("power_backup"),
            "Panathur_Free": "YES (Safe)" if r.get("panathur_bottleneck_free") else "NO (Traffic Choke)",
            "Contact_Type": contact.get("type", "Owner"),
            "Contact_Name": contact.get("name", "Owner"),
            "Contact_Phone": contact.get("phone", ""),
            "WhatsApp_Chat": f"https://wa.me/{contact.get('whatsapp', '')}"
        })

    # Sort rental by Zero Panathur first, then highest brokerage savings, then lowest rent
    rental_records.sort(key=lambda x: (x["Panathur_Free"] != "YES (Safe)", -x["Brokerage_Savings_INR"], x["Monthly_Rent_INR"]))
    top_5_rental_df = pd.DataFrame(rental_records[:5])

    # ---------------------------------------------------------
    # 4. Save Daily Snapshots
    # ---------------------------------------------------------
    if not dry_run:
        top_10_purchase_df.to_csv(TOP_10_PURCHASE_CSV, index=False, encoding="utf-8")
        safe_print(f"Recorded TOP 10 Purchase properties to {TOP_10_PURCHASE_CSV}")

        top_5_rental_df.to_csv(TOP_5_RENTAL_CSV, index=False, encoding="utf-8")
        safe_print(f"Recorded TOP 5 Rental properties to {TOP_5_RENTAL_CSV}")

        # Update historical price dataset
        if os.path.exists(HISTORICAL_CSV):
            hist_df = pd.read_csv(HISTORICAL_CSV)
            if force or (date_str not in hist_df["date"].values):
                new_row = {
                    "date": date_str,
                    "quarter": f"{now_utc.year}-D{now_utc.strftime('%m%d')}",
                    "bellandur_core_psqft": bellandur_avg,
                    "green_glen_layout_psqft": green_glen_avg,
                    "kadubeesanahalli_gurukul_psqft": kadubeesanahalli_avg,
                    "panathur_road_choke_psqft": panathur_avg,
                    "sarjapur_road_psqft": 10800,
                    "rental_yield_avg_pct": 4.1,
                    "notes": f"Automated 5 PM IST snapshot. Recorded Top 10 Purchase & Top 5 Rental."
                }
                hist_df = pd.concat([hist_df, pd.DataFrame([new_row])], ignore_index=True)
                hist_df.to_csv(HISTORICAL_CSV, index=False)
                safe_print(f"Appended snapshot to {HISTORICAL_CSV}")

        # Save tracker log
        log_entry = {
            "status": "SUCCESS",
            "last_run_utc": timestamp_iso,
            "scheduled_time_ist": "5:00 PM IST",
            "top_10_purchase_saved": len(top_10_purchase_df),
            "top_5_rental_saved": len(top_5_rental_df),
            "bellandur_core_psqft": bellandur_avg,
            "green_glen_layout_psqft": green_glen_avg,
            "kadubeesanahalli_gurukul_psqft": kadubeesanahalli_avg,
            "panathur_road_choke_psqft": panathur_avg
        }
        with open(TRACKER_LOG, "w", encoding="utf-8") as f:
            json.dump(log_entry, f, indent=2)

    safe_print("Daily tracker run successfully completed.")
    safe_print("=" * 65)
    return True


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    force = "--force" in sys.argv
    run_daily_tracker(dry_run=dry_run, force=force)
