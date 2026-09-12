#!/usr/bin/env python3
"""
STEP 1 — Build the merged state-year panel.

Reads the eight curated files in data/ (READ-ONLY, never modified) and writes one
merged table to output/panel_raw.csv.

Applies, in order:
  D2  merge Jammu & Kashmir + Ladakh, and Dadra & Nagar Haveli + Daman + Diu,
      in every year -- summing raw counts BEFORE any ratio is taken
  D1  drop Lakshadweep and the merged DNH/Daman & Diu (no income data published)
  D8  window is fy_end 2018..2023
  D9  join on fy_end, never on the native year columns

Only the columns named in data/README.md are taken. The rupee columns inside
files 03 and 04 are deliberately ignored -- amounts come from 05/06 (D8).

Asserts hard: exactly 33 states, 6 years, 198 rows, no nulls, no non-positive values.
"""

import re
import sys
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent   # this hypothesis folder
SHARED = ROOT_DIR.parent                            # ps647_final/: data/ and raw/ are shared

DATA = SHARED / "data"
OUT = ROOT_DIR / "output"

YEARS = list(range(2018, 2024))

# Units that carry no income data and are dropped entirely (D1).
DROP = {"DNH_DD", "LAKSHADWEEP"}

# Rows that are regional aggregates or national totals, not states.
NON_STATE = re.compile(r"REGION$|^ALL INDIA$|^INDIA$")


def state_key(raw) -> str:
    """
    Canonical state name.

    Word-boundary matching is deliberate. A naive substring test folds
    "ANDAMAN" into the Daman & Diu group, because "AN-DAMAN" contains "DAMAN".
    That bug silently pools two unrelated units; it is guarded here and
    asserted against in check_andaman_not_folded().
    """
    s = str(raw).upper().replace("&", " AND ")
    s = re.sub(r"\bTHE\b", "", s)
    s = re.sub(r"\(UT\)", "", s)
    s = re.sub(r"\bNCT OF\b", "", s)
    s = re.sub(r"[^A-Z ]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    s = s.replace("ANDMAN", "ANDAMAN").replace("NOCOBAR", "NICOBAR")
    s = s.replace("UTTRAKHAND", "UTTARAKHAND")

    if re.search(r"\bANDAMAN\b", s):
        return "ANDAMAN AND NICOBAR ISLANDS"
    if re.search(r"\bLADAKH\b", s):                      # D2: fold into J&K
        return "JAMMU AND KASHMIR"
    if re.search(r"\bDADRA\b|\bDAMAN\b|\bDIU\b", s):     # D2: one UT
        return "DNH_DD"
    return s


def load(fname: str, state_col: str, value_col: str, out_name: str) -> pd.DataFrame:
    """Load one file, canonicalise states, sum D2 merges, restrict to the window."""
    df = pd.read_csv(DATA / fname)
    df["state_key"] = df[state_col].map(state_key)
    df = df[df["fy_end"].between(YEARS[0], YEARS[-1])]
    df = df[~df["state_key"].isin(DROP)]
    df = df[~df["state_key"].str.contains(NON_STATE)]
    # Sum, not mean: D2 requires raw counts added before any ratio.
    g = df.groupby(["state_key", "fy_end"], as_index=False)[value_col].sum()
    return g.rename(columns={value_col: out_name})


SOURCES = [
    ("01_branches.csv",         "state_raw",  "value",                 "branches"),
    ("02_atms.csv",             "state_raw",  "atms",                  "atms"),
    ("03_loan_accounts.csv",    "state_name", "no_of_credit_accounts", "credit_accounts"),
    ("04_deposit_accounts.csv", "state_key",  "no_of_deposit_accounts", "deposit_accounts"),
    ("05_deposit_amounts.csv",  "state_raw",  "value",                 "deposits_rs_crore"),
    ("06_loan_amounts.csv",     "state_raw",  "value",                 "credit_rs_crore"),
    ("07_income_per_person.csv", "state_raw", "value",                 "nsdp_pc_rs"),
]


def check_andaman_not_folded(panel: pd.DataFrame) -> None:
    keys = set(panel["state_key"])
    assert "ANDAMAN AND NICOBAR ISLANDS" in keys, \
        "Andaman & Nicobar missing -- it was probably folded into DNH_DD by a substring match"
    assert "DNH_DD" not in keys, "DNH_DD should have been dropped (D1)"


def main() -> int:
    OUT.mkdir(exist_ok=True)

    panel = None
    for fname, scol, vcol, name in SOURCES:
        part = load(fname, scol, vcol, name)
        print(f"  {fname:26s} -> {name:18s} {len(part):>4} rows, {part.state_key.nunique()} states")
        panel = part if panel is None else panel.merge(part, on=["state_key", "fy_end"], how="inner")

    # Population carries BOTH denominators (A4): 18+ for Access, total for Usage.
    pop = pd.read_csv(DATA / "08_adult_population.csv")
    pop["state_key"] = pop["state"].map(state_key)
    pop = pop[pop["fy_end"].between(YEARS[0], YEARS[-1])]
    pop = pop[~pop["state_key"].isin(DROP)]
    pop = pop[~pop["state_key"].str.contains(NON_STATE)]
    pop = pop.groupby(["state_key", "fy_end"], as_index=False)[["pop_18plus_000", "pop_total_000"]].sum()
    print(f"  08_adult_population.csv    -> population       {len(pop):>4} rows, {pop.state_key.nunique()} states")
    panel = panel.merge(pop, on=["state_key", "fy_end"], how="inner")

    panel = panel.sort_values(["state_key", "fy_end"]).reset_index(drop=True)

    # ---- assertions: fail loudly rather than analyse a broken table ----
    check_andaman_not_folded(panel)
    n_states, n_years = panel.state_key.nunique(), panel.fy_end.nunique()
    assert n_states == 33, f"expected 33 states, got {n_states}"
    assert n_years == 6, f"expected 6 years, got {n_years}"
    assert len(panel) == 198, f"expected 198 rows, got {len(panel)}"
    assert not panel.isna().any().any(), "nulls present"
    num = panel.select_dtypes("number")
    assert (num > 0).all().all(), "non-positive values present"

    panel.to_csv(OUT / "panel_raw.csv", index=False)
    print(f"\n  -> {OUT/'panel_raw.csv'}  {panel.shape[0]} rows x {panel.shape[1]} cols")
    print(f"     {n_states} states x {n_years} years, no nulls, all values positive")

    # ---- D9 spot-check must survive the merge ----
    mh = panel[(panel.state_key == "MAHARASHTRA") & (panel.fy_end == 2018)].iloc[0]
    print("\n  D9 spot-check, Maharashtra fy_end=2018:")
    for label, got, want in [("branches", mh.branches, 12545),
                             ("ATMs", mh.atms, 25651),
                             ("income/person", mh.nsdp_pc_rs, 172663)]:
        ok = "OK" if int(got) == want else "MISMATCH"
        print(f"     {label:14s} {int(got):>8,}  expected {want:>8,}   {ok}")
        assert int(got) == want, f"{label} spot-check failed"
    return 0


if __name__ == "__main__":
    sys.exit(main())
