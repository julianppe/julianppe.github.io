"""
Export Shapley Excel data → assets/json/shapley_data.json
Run from the repo root:  python export_shapley_data.py
Requires:  pip install pandas openpyxl
"""

import pandas as pd
import re
import glob
import os
import json

# ── Config ─────────────────────────────────────────────────────────────────────
DATA_FOLDER = r"D:\Dropbox\A-work\D-Consultorias\2026\LACGIL\analysis\interactive_graphs"
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "assets", "json", "shapley_data.json")

# ── Load ───────────────────────────────────────────────────────────────────────
def load_all_countries(folder):
    all_xlsx = glob.glob(os.path.join(folder, "*.xlsx"))
    files = [f for f in all_xlsx if "shapley" in os.path.basename(f).lower()]
    if not files:
        raise FileNotFoundError(
            f"No Shapley xlsx files found in:\n  {folder}\n"
            "Check DATA_FOLDER at the top of this script."
        )

    result = {}
    for fpath in sorted(files):
        country = os.path.basename(fpath).split("_")[0].upper()
        xl = pd.ExcelFile(fpath)
        sheets_2016 = [s for s in xl.sheet_names if s.startswith("2016")]
        if not sheets_2016:
            print(f"  [skip] {os.path.basename(fpath)} — no sheet starting with 2016")
            continue

        target = max(sheets_2016, key=lambda s: int(re.findall(r"\d{4}", s)[-1]))
        raw = xl.parse(target, header=None)

        hdr_row = None
        for i, row in raw.iterrows():
            if "component" in [str(v).lower().strip() for v in row.values]:
                hdr_row = i
                break
        if hdr_row is None:
            print(f"  [skip] {os.path.basename(fpath)} — 'component' column not found in sheet {target}")
            continue

        df = xl.parse(target, header=hdr_row)
        df.columns = [str(c).strip() for c in df.columns]
        df = df.dropna(subset=["component"])

        years = re.findall(r"\d{4}", target)
        y1, y2 = int(years[0]), int(years[-1])

        def pkey(s):
            s = str(s)
            if "8.30" in s or "8,30" in s:
                return "$8.30"
            if "17" in s:
                return "$17.00"
            return None

        records = {}
        for _, row in df.iterrows():
            comp = str(row.get("component", "")).strip()
            pl   = pkey(row.get("pline", ""))
            if pl is None:
                continue
            try:
                val = float(row["rate"])
            except (ValueError, TypeError, KeyError):
                continue
            records.setdefault(pl, {})[comp] = round(val, 6)

        result[country] = {"y1": y1, "y2": y2, "data": records}
        print(f"  [ok]   {country}  ({y1}–{y2})  sheets: {', '.join(sheets_2016)}")

    return result


# ── Main ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"Reading from: {DATA_FOLDER}")
    data = load_all_countries(DATA_FOLDER)
    countries = sorted(data.keys())

    output = {"countries": countries, "data": data}

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nExported {len(countries)} countries: {', '.join(countries)}")
    print(f"Output:  {OUTPUT_FILE}")
