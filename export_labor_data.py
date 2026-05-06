"""
Export Labor Market CSV data → assets/json/labor_data.json
Run from repo root:  python export_labor_data.py
Requires:  pip install pandas
"""

import pandas as pd
import json
import os
import math

# ── Config ─────────────────────────────────────────────────────────────────────
DATA_PATH = (
    r"D:\Dropbox\A-work\D-Consultorias\2026\LACGIL\analysis"
    r"\outputs\descriptives\labor_descriptives.csv"
)
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "assets", "json", "labor_data.json")

VARS      = ["empl", "lfp", "ila", "hours", "informal"]
GENDERS   = ["total", "men", "women"]
SKILLS    = ["total", "low", "med", "high"]
AGE_GROUPS = ["total", "young", "prime", "older"]

# ── Helpers ────────────────────────────────────────────────────────────────────
def safe(v):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    return round(float(v), 6)

# ── Load ───────────────────────────────────────────────────────────────────────
print(f"Reading from: {DATA_PATH}")
df = pd.read_csv(DATA_PATH)
df["year"] = df["year"].astype(int)

COUNTRIES = sorted(df["pais"].unique().tolist())
output = {"countries": COUNTRIES, "data": {}}

for country in COUNTRIES:
    cdf = df[df["pais"] == country]
    country_data = {}

    # Export all (gender, skill, agegroup) combos where skill=total OR agegroup=total
    keys = set()
    for g in GENDERS:
        for s in SKILLS:
            keys.add((g, s, "total"))
        for a in AGE_GROUPS:
            keys.add((g, "total", a))

    for (g, s, a) in sorted(keys):
        sub = cdf[
            (cdf["gender"]   == g) &
            (cdf["skill"]    == s) &
            (cdf["agegroup"] == a)
        ].sort_values("year")

        if sub.empty:
            continue

        key = f"{g}|{s}|{a}"
        country_data[key] = {"years": sub["year"].tolist()}
        for v in VARS:
            country_data[key][v] = [safe(x) for x in sub[v].tolist()] if v in sub.columns \
                                   else [None] * len(sub)

    output["data"][country] = country_data
    print(f"  [ok]   {country}  ({len(country_data)} series)")

# ── Save ───────────────────────────────────────────────────────────────────────
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\nExported {len(COUNTRIES)} countries: {', '.join(COUNTRIES)}")
print(f"Output:  {OUTPUT_FILE}")
