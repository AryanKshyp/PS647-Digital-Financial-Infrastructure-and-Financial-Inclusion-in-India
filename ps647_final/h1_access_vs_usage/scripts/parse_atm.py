#!/usr/bin/env python3
"""
Parse RBI "State wise and Region wise Deployment of ATMs" workbooks into a tidy CSV.

Source: https://www.rbi.org.in/Scripts/StateRegionATMView.aspx (quarterly release)
Files : raw/atm_deployment/rbi_statewise_atm_march<YYYY>.xlsx

Each workbook's "Statewise" sheet is bank x state: rows are individual banks and
entity-group subtotals, columns are states/UTs. We take the final grand-total row
(all banks + White Label ATM Operators) as the state's ATM count.

Two things vary across years and are handled explicitly:
  - the grand-total row is labelled "Grand Total" in most years but
    "Total (Banks+WLAOs)" in the Revised March-2022 release;
  - state column labels drift (ORISSA/ODISHA, PONDICHERRY/PUDUCHERRY, ...) and
    Dadra & Nagar Haveli / Daman / Diu are three columns before 2022 and one after.

Output is LONG and *unharmonised* except for spelling: one row per
(state_raw, year, atms). Boundary merges happen downstream, not here.
"""

import json
import re
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent   # this hypothesis folder
SHARED = ROOT_DIR.parent                            # ps647_final/: data/ and raw/ are shared

RAW = SHARED / "raw/atm_deployment"
YEARS = range(2018, 2025)

# Spelling drift only -- these are the SAME unit, just spelled differently.
SPELLING = {
    "ANDAMAN & NICOBAR": "ANDAMAN & NICOBAR ISLANDS",
    "ANDAMAN AND NICOBAR": "ANDAMAN & NICOBAR ISLANDS",
    "ANDAMAN & NICOBAR ISLAND": "ANDAMAN & NICOBAR ISLANDS",
    "ORISSA": "ODISHA",
    "PONDICHERRY": "PUDUCHERRY",
    "CHHATISGARH": "CHHATTISGARH",
    "NCT OF DELHI": "DELHI",
    "LAKSHWADEEP": "LAKSHADWEEP",
    "LAKHSHADWEEP": "LAKSHADWEEP",
    "JAMMU AND KASHMIR": "JAMMU & KASHMIR",
    "JAMMU  & KASHMIR": "JAMMU & KASHMIR",
    "UTTARAKHAND": "UTTARAKHAND",
    "UTTARANCHAL": "UTTARAKHAND",
    "DADRA AND NAGAR HAVELI AND DAMAN AND DIU": "DADRA & NAGAR HAVELI AND DAMAN & DIU",
    "DADRA & NAGAR HAVELI AND DAMAN & DIU": "DADRA & NAGAR HAVELI AND DAMAN & DIU",
    "DADRA NAGAR HAVELI": "DADRA & NAGAR HAVELI",
    "DADRA AND NAGAR HAVELI": "DADRA & NAGAR HAVELI",
    "TELENGANA": "TELANGANA",
}

TOTAL_PAT = re.compile(r"^\s*(grand\s*total|total\s*\(banks\s*\+\s*wlaos?\)|total\s*\(banks\+wlaos?\))\s*$", re.I)
NOT_STATE = re.compile(r"total|all\s*india|^nan$|^\s*$|name of|bank", re.I)


def norm(s: str) -> str:
    s = re.sub(r"\s+", " ", str(s).replace("\n", " ")).strip().upper()
    s = s.replace("*", "").replace("#", "").strip()
    return SPELLING.get(s, s)


def find_header_row(df: pd.DataFrame) -> int:
    """Header is the row containing recognisable state names across many columns."""
    for i in range(min(10, len(df))):
        vals = [norm(v) for v in df.iloc[i].tolist()]
        hits = sum(1 for v in vals if v in {"ANDHRA PRADESH", "ASSAM", "BIHAR", "GUJARAT", "KERALA", "PUNJAB"})
        if hits >= 3:
            return i
    raise RuntimeError("header row not found")


def find_total_row(df: pd.DataFrame, hdr: int) -> int:
    """Last row whose label column matches a grand-total pattern."""
    cands = []
    for i in range(hdr + 1, len(df)):
        for c in range(0, min(3, df.shape[1])):
            if TOTAL_PAT.match(str(df.iat[i, c])):
                cands.append(i)
                break
    if not cands:
        raise RuntimeError("grand-total row not found")
    return cands[-1]


def main():
    recs, report = [], []

    for y in YEARS:
        f = RAW / f"rbi_statewise_atm_march{y}.xlsx"
        xl = pd.ExcelFile(f)
        sheet = [s for s in xl.sheet_names if re.search(r"state", s, re.I)][0]
        df = pd.read_excel(f, sheet_name=sheet, header=None)

        hdr = find_header_row(df)
        tot = find_total_row(df, hdr)
        label = next(str(df.iat[tot, c]) for c in range(3) if TOTAL_PAT.match(str(df.iat[tot, c])))

        n = 0
        for c in range(df.shape[1]):
            st = norm(df.iat[hdr, c])
            if not st or NOT_STATE.search(st):
                continue
            v = df.iat[tot, c]
            if pd.isna(v):
                continue
            try:
                val = float(str(v).replace(",", ""))
            except ValueError:
                continue
            recs.append({"state_raw": st, "year": y, "atms": val,
                         "source_sheet": sheet, "total_row_label": label.strip()})
            n += 1

        allindia = sum(r["atms"] for r in recs if r["year"] == y)
        report.append((y, sheet, label.strip(), n, allindia))
        print(f"{y}: sheet={sheet!r:26s} total_row={label.strip()!r:22s} states={n:3d} all-India={allindia:,.0f}")

    out = pd.DataFrame(recs)
    out.to_csv(RAW / "atm_statewise_long.csv", index=False)
    print(f"\nwrote {RAW/'atm_statewise_long.csv'}  rows={len(out)}")

    # Which states are present in which years -- exposes the boundary changes.
    piv = out.pivot_table(index="state_raw", columns="year", values="atms")
    print("\n=== ATMs by state x year (blank = column absent that year) ===")
    print(piv.to_string(na_rep="  --"))


if __name__ == "__main__":
    main()
