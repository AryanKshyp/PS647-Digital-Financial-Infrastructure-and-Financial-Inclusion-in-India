#!/usr/bin/env python3
"""
D12 — Build the extended FY2012-FY2023 panel (12 years), branches only.

Same construction as scripts/build_panel.py + build_variables.py, with two changes:
  - window is 2012..2023 instead of 2018..2023
  - ATMs are dropped (RBI's state-wise ATM release starts 2018)
  - deposit accounts are spliced: 2012-2018 from the IDP bank-group file (thousands),
    2019-2023 from data/04 (DBIE). Verified exact at the 2018 overlap.

data/ is read-only. Writes output/panel_long_analysis.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from build_panel import state_key as _base_state_key, DROP, NON_STATE

ROOT_DIR = Path(__file__).resolve().parent.parent   # this hypothesis folder
SHARED = ROOT_DIR.parent                            # ps647_final/: data/ and raw/ are shared


def state_key(raw) -> str:
    """
    D13 — as build_panel.state_key, plus Andhra Pradesh + Telangana merged.

    Telangana was carved out of AP in June 2014 (FY2015). Before that its data sits
    inside AP, so the separate series are discontinuous and the combined one is not.
    Same treatment as the D2 merges. Applies to the 12-year panel only; the 6-year
    build is left untouched so F1-F8 stay reproducible.
    """
    k = _base_state_key(raw)
    if k in ("ANDHRA PRADESH", "TELANGANA"):
        return "ANDHRA PRADESH AND TELANGANA"
    return k

DATA = SHARED / "data"
RAW = SHARED / "raw/bsr_accounts"
OUT = ROOT_DIR / "output"

YEARS = list(range(2012, 2024))
CRORE = 1e7
ACCESS_IND = ["deposit_accts_per_adult", "credit_accts_per_adult"]
USAGE_IND = ["deposits_per_capita", "credit_per_capita"]


def tidy(df, scol, ycol, vcol, name):
    df = df.copy()
    df["state_key"] = df[scol].map(state_key)
    df = df[df[ycol].between(YEARS[0], YEARS[-1])]
    df = df[~df["state_key"].isin(DROP)]
    df = df[~df["state_key"].str.contains(NON_STATE)]
    g = df.groupby(["state_key", ycol], as_index=False)[vcol].sum()
    return g.rename(columns={ycol: "fy_end", vcol: name})


def minmax(s):
    lo, hi = s.min(), s.max()
    return (s - lo) / (hi - lo)


def main() -> int:
    parts = [
        tidy(pd.read_csv(DATA / "01_branches.csv"),        "state_raw",  "fy_end", "value", "branches"),
        tidy(pd.read_csv(DATA / "03_loan_accounts.csv"),   "state_name", "fy_end", "no_of_credit_accounts", "credit_accounts"),
        tidy(pd.read_csv(DATA / "05_deposit_amounts.csv"), "state_raw",  "fy_end", "value", "deposits_rs_crore"),
        tidy(pd.read_csv(DATA / "06_loan_amounts.csv"),    "state_raw",  "fy_end", "value", "credit_rs_crore"),
        tidy(pd.read_csv(DATA / "07_income_per_person.csv"), "state_raw", "fy_end", "value", "nsdp_pc_rs"),
    ]
    panel = parts[0]
    for p in parts[1:]:
        panel = panel.merge(p, on=["state_key", "fy_end"], how="inner")

    # --- deposit accounts: splice IDP (<=2018) with DBIE (>=2019) ---
    early = pd.read_csv(RAW / "derived_state_year_deposit_accounts_2010_2018.csv")
    early["no_of_deposit_accounts"] = early["no_of_deposit_accounts_thousand"] * 1000
    early = tidy(early[early.march_year <= 2018], "state_name", "march_year",
                 "no_of_deposit_accounts", "deposit_accounts")
    late = pd.read_csv(DATA / "04_deposit_accounts.csv")
    late = tidy(late[late.fy_end >= 2019], "state_key", "fy_end",
                "no_of_deposit_accounts", "deposit_accounts")
    dep = pd.concat([early, late], ignore_index=True)
    print(f"  deposit accounts spliced: IDP {early.fy_end.min()}-{early.fy_end.max()} "
          f"+ DBIE {late.fy_end.min()}-{late.fy_end.max()}")
    panel = panel.merge(dep, on=["state_key", "fy_end"], how="inner")

    pop = pd.read_csv(DATA / "08_adult_population.csv")
    pop["state_key"] = pop["state"].map(state_key)
    pop = pop[pop.fy_end.between(YEARS[0], YEARS[-1])]
    pop = pop[~pop.state_key.isin(DROP) & ~pop.state_key.str.contains(NON_STATE)]
    pop = pop.groupby(["state_key", "fy_end"], as_index=False)[["pop_18plus_000", "pop_total_000"]].sum()
    panel = panel.merge(pop, on=["state_key", "fy_end"], how="inner")

    panel = panel.sort_values(["state_key", "fy_end"]).reset_index(drop=True)

    # --- variables, identical construction to the 6-year build ---
    adults = panel.pop_18plus_000 * 1000
    everyone = panel.pop_total_000 * 1000
    panel["branches_per_lakh_adults"] = panel.branches / (adults / 1e5)
    panel["deposit_accts_per_adult"] = panel.deposit_accounts / adults
    panel["credit_accts_per_adult"] = panel.credit_accounts / adults
    panel["deposits_per_capita"] = panel.deposits_rs_crore * CRORE / everyone
    panel["credit_per_capita"] = panel.credit_rs_crore * CRORE / everyone
    for c in ACCESS_IND + USAGE_IND:
        panel["norm_" + c] = minmax(panel[c])
    panel["Access"] = panel[["norm_" + c for c in ACCESS_IND]].mean(axis=1)
    panel["Usage"] = panel[["norm_" + c for c in USAGE_IND]].mean(axis=1)
    panel["AUG"] = panel.Access - panel.Usage
    panel["ln_nsdp_pc"] = np.log(panel.nsdp_pc_rs)

    ns, ny = panel.state_key.nunique(), panel.fy_end.nunique()
    assert not panel.isna().any().any(), "nulls present"
    # positivity applies to the raw source columns only; min-max normalisation
    # legitimately produces an exact 0 at each indicator's minimum.
    raw_cols = ["branches", "credit_accounts", "deposit_accounts", "deposits_rs_crore",
                "credit_rs_crore", "nsdp_pc_rs", "pop_18plus_000", "pop_total_000"]
    assert (panel[raw_cols] > 0).all().all(), "non-positive values in raw columns"
    assert len(panel) == ns * ny, f"unbalanced: {len(panel)} != {ns}x{ny}"

    panel.to_csv(OUT / "panel_long_analysis.csv", index=False)
    print(f"\n  -> {OUT/'panel_long_analysis.csv'}")
    print(f"     {ns} states x {ny} years = {len(panel)} rows, balanced, no nulls")
    print(f"     years {panel.fy_end.min()}-{panel.fy_end.max()}")

    # within-state variation, the reason for the extension
    print("\n  within-state variation (Step 4 diagnostic, re-run on 12 years):")
    for c in ["branches_per_lakh_adults", "Access", "Usage", "AUG"]:
        x = panel[c]; g = x.mean()
        mi = panel.groupby("state_key")[c].transform("mean")
        share = (x - mi + g).std(ddof=1) / x.std(ddof=1)
        tag = "FAIL" if share < .10 else "WEAK" if share < .25 else "PASS"
        print(f"    {c:28s} {100*share:5.1f}%   {tag if c=='branches_per_lakh_adults' else ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
