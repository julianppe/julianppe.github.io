"""
Export GIC Excel data → assets/json/gic_data.json
Run from repo root:  python export_gic_data.py
Requires:  pip install pandas openpyxl
"""

import pandas as pd
import json
import os

# ── Config ─────────────────────────────────────────────────────────────────────
XLSX_PATH   = r"D:\Dropbox\A-work\D-Consultorias\2026\LACGIL\analysis\outputs\aux_gic.xlsx"
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "assets", "json", "gic_data.json")

P_MIN, P_MAX = 1, 100
LP_830       = 8.30  * 30.42   # USD PPP 2021/month
LP_1700      = 17.00 * 30.42

# ── Helpers ────────────────────────────────────────────────────────────────────
def _pov_pctile(income_series, pct_series, threshold):
    """Last percentile whose mean income is below threshold (None if out of range)."""
    result = None
    for p, inc in zip(pct_series, income_series):
        if inc < threshold:
            result = p
    return result

# ── Load ───────────────────────────────────────────────────────────────────────
print(f"Reading from: {XLSX_PATH}")
xl            = pd.ExcelFile(XLSX_PATH)
DECOMP_SHEETS = [s for s in xl.sheet_names if s.endswith("_decomp")]
COUNTRIES     = [s.replace("_decomp", "") for s in DECOMP_SHEETS]

output = {"countries": COUNTRIES, "data": {}}

for sheet, country in zip(DECOMP_SHEETS, COUNTRIES):
    df_full         = xl.parse(sheet)
    df_full.columns = df_full.columns.str.strip()
    y1 = str(int(df_full["First year"].iloc[0]))
    y2 = str(int(df_full["Last year"].iloc[0]))

    pct_full    = df_full["Percentile"].tolist()
    inc_y1_full = df_full["Mean total income, year 1 (2021 PPP USD/month)"].tolist()
    inc_y2_full = df_full["Mean total income, year 2 (2021 PPP USD/month)"].tolist()

    pov = {
        "lp830_y1":  _pov_pctile(inc_y1_full, pct_full, LP_830),
        "lp830_y2":  _pov_pctile(inc_y2_full, pct_full, LP_830),
        "lp1700_y1": _pov_pctile(inc_y1_full, pct_full, LP_1700),
        "lp1700_y2": _pov_pctile(inc_y2_full, pct_full, LP_1700),
    }

    df = df_full[
        (df_full["Percentile"] >= P_MIN) & (df_full["Percentile"] <= P_MAX)
    ].reset_index(drop=True)

    output["data"][country] = {
        "y1":        y1,
        "y2":        y2,
        "percentile": [round(x, 6) for x in df["Percentile"].tolist()],
        "gic":        [round(x, 6) for x in df["Annualized GIC (%)"].tolist()],
        "male":       [round(x, 6) for x in df["Male labor: annualized contribution (pp)"].tolist()],
        "female":     [round(x, 6) for x in df["Female labor: annualized contribution (pp)"].tolist()],
        "nonlabor":   [round(x, 6) for x in df["Non-labor: annualized contribution (pp)"].tolist()],
        "pov":        pov,
    }
    print(f"  [ok]   {country}  ({y1}–{y2})")

# ── Save ───────────────────────────────────────────────────────────────────────
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\nExported {len(COUNTRIES)} countries: {', '.join(COUNTRIES)}")
print(f"Output:  {OUTPUT_FILE}")
