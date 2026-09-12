#!/usr/bin/env python3
"""
Build a state x year ADULT (18+) population panel from the NCP/MoHFW
"Population Projections for India and States 2011-2036" (July 2020).

WHY THIS IS A DERIVED FILE
--------------------------
The report publishes:
  * TOTAL population for EVERY year 2011-2036, per state (Tables 8/11/14,
    as on 1 March / 1 July / 1 October).
  * The 18+ ("18 years and above") count only for the QUINQUENNIAL years
    2011, 2016, 2021, 2026, 2031, 2036 (Table T-17), and only for
    India + 22 states + a combined "North-East states (excluding Assam)".

There is NO published per-year adult figure. This script therefore:
  1. computes the 18+ SHARE of total population at each quinquennial anchor,
  2. linearly interpolates that share across intervening years,
  3. multiplies it by the published annual total.
Every output row carries `share_source` and `share_method` so the
interpolated component is never mistaken for a published number.

Units without their own age structure in the report get a proxy share:
  * 7 north-eastern states (Sikkim, Arunachal Pradesh, Nagaland, Manipur,
    Mizoram, Tripura, Meghalaya) -> the report's own combined NE share.
  * Ladakh -> Jammu & Kashmir (UT) share (Ladakh was part of J&K until 2019).
  * Goa (explicitly excluded from the projection exercise), Chandigarh,
    Daman & Diu, Dadra & Nagar Haveli, Lakshadweep, Puducherry and
    Andaman & Nicobar Islands -> all-India share. These are small and their
    real age structure differs (Chandigarh/D&NH are migrant-heavy); treat
    their adult numbers as rough.
"""

import csv
import os

BASE = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "raw", "population")
)

# reference date of the annual total to use; 1 October is the mid-point of the
# Indian financial year (Apr-Mar), 1 July the mid-point of the calendar year.
SOURCES = {
    "1july": "pop_total_annual_1july_2011_2036.csv",
    "1october": "pop_total_annual_1october_2011_2036.csv",
    "1march": "pop_total_annual_1march_2011_2036.csv",
}

NE = ["SIKKIM", "ARUNACHAL PRADESH", "NAGALAND", "MANIPUR", "MIZORAM",
      "TRIPURA", "MEGHALAYA"]
PROXY = {u: ("NORTH-EAST STATES (Excluding Assam)", "NE_combined_proxy") for u in NE}
PROXY["LADAKH"] = ("JAMMU & KASHMIR (UT)", "jammu_kashmir_proxy")
for u in ["GOA", "CHANDIGARH", "DAMAN & DIU", "DADRA & NAGAR HAVELI",
          "LAKSHADWEEP", "PUDUCHERRY", "ANDAMAN & NICOBAR ISLANDS"]:
    PROXY[u] = ("INDIA", "india_proxy")

ANCHORS = [2011, 2016, 2021, 2026, 2031, 2036]


def load_shares():
    """18+ share of total, per unit, at each quinquennial anchor year."""
    sh = {}
    for r in csv.DictReader(open(os.path.join(BASE, "pop_broad_agegroups_quinquennial.csv"))):
        if r["pop_18plus"] and r["pop_total"]:
            sh.setdefault(r["unit"], {})[int(r["year"])] = (
                float(r["pop_18plus"]) / float(r["pop_total"])
            )
    return sh


def interp(anchor_shares, year):
    ys = sorted(anchor_shares)
    if year <= ys[0]:
        return anchor_shares[ys[0]]
    if year >= ys[-1]:
        return anchor_shares[ys[-1]]
    for a, b in zip(ys, ys[1:]):
        if a <= year <= b:
            w = (year - a) / (b - a)
            return anchor_shares[a] * (1 - w) + anchor_shares[b] * w


def main():
    shares = load_shares()
    for tag, fname in SOURCES.items():
        rows = []
        for r in csv.DictReader(open(os.path.join(BASE, fname))):
            unit, year = r["unit"], int(r["year"])
            total = float(r["persons_000"])
            src_unit, kind = (unit, "own") if unit in shares else PROXY.get(unit, (None, None))
            if src_unit is None:
                print("  no share source for", unit)
                continue
            s = interp(shares[src_unit], year)
            rows.append({
                "state": unit,
                "year": year,
                "ref_date": f"{tag} {year}",
                "pop_total_000": round(total, 1),
                "share_18plus": round(s, 5),
                "pop_18plus_000": round(total * s, 1),
                "share_source_unit": src_unit,
                "share_source": kind,
                "share_method": "published" if year in ANCHORS and kind == "own"
                                else "linear interpolation of 18+ share between "
                                     "quinquennial anchors",
            })
        out = os.path.join(BASE, f"adult_pop_18plus_by_state_year_{tag}.csv")
        with open(out, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print("wrote", out, len(rows), "rows")


if __name__ == "__main__":
    main()
