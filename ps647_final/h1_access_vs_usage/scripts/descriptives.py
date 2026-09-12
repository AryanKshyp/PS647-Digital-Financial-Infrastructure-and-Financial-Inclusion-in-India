#!/usr/bin/env python3
"""
STEP 3 — Descriptive statistics.

Reads output/panel_analysis.csv, writes output/table1_descriptives.csv.
Also runs a sanity gate against the ranges established during data validation.
"""

import sys
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent

OUT = ROOT_DIR / "output"

VARS = [
    ("branches_per_lakh_adults", "IV       Branches per lakh adults"),
    ("atms_per_lakh_adults",     "IV       ATMs per lakh adults"),
    ("deposit_accts_per_adult",  "Access   Deposit accounts per adult"),
    ("credit_accts_per_adult",   "Access   Credit accounts per adult"),
    ("deposits_per_capita",      "Usage    Deposits per capita (Rs)"),
    ("credit_per_capita",        "Usage    Credit per capita (Rs)"),
    ("Access",                   "DV1      Access (0-1 composite)"),
    ("Usage",                    "DV2      Usage (0-1 composite)"),
    ("AUG",                      "Derived  AUG = Access - Usage"),
    ("ln_nsdp_pc",               "Control  ln(NSDP per capita)"),
]


def main() -> int:
    d = pd.read_csv(OUT / "panel_analysis.csv")

    rows = []
    for col, label in VARS:
        s = d[col]
        rows.append({
            "variable": label, "column": col, "N": int(s.notna().sum()),
            "mean": s.mean(), "sd": s.std(), "min": s.min(),
            "p25": s.quantile(.25), "median": s.median(), "p75": s.quantile(.75),
            "max": s.max(),
        })
    t = pd.DataFrame(rows)
    t.to_csv(OUT / "table1_descriptives.csv", index=False)

    print(f"  Panel: {d.state_key.nunique()} states x {d.fy_end.nunique()} years = {len(d)} rows\n")
    print(f"  {'variable':44s} {'mean':>12s} {'sd':>12s} {'min':>12s} {'max':>12s}")
    print("  " + "-" * 96)
    for r in rows:
        big = abs(r["mean"]) > 1000
        f = ",.0f" if big else ".3f"
        print(f"  {r['variable']:44s} {r['mean']:>12{f}} {r['sd']:>12{f}} "
              f"{r['min']:>12{f}} {r['max']:>12{f}}")

    # ---- sanity gate against ranges established during data validation ----
    print("\n  sanity gate:")
    checks = [
        ("credit accounts per adult in 0.05-1.0",
         d.credit_accts_per_adult.between(0.05, 1.0).all()),
        ("deposit accounts per adult in 0.9-8.1 (upper end = known D7 defect)",
         d.deposit_accts_per_adult.between(0.9, 8.1).all()),
        ("Access and Usage both within [0,1]",
         d.Access.between(0, 1).all() and d.Usage.between(0, 1).all()),
        ("no missing values anywhere",
         not d.isna().any().any()),
    ]
    for label, ok in checks:
        print(f"    [{'PASS' if ok else 'FAIL'}] {label}")
        assert ok, label

    # deposit-accounts outliers flagged in D7 -- confirm which are in-window (A6)
    hi = d[d.deposit_accts_per_adult > 5][["state_key", "fy_end", "deposit_accts_per_adult"]]
    print("\n  deposit accounts per adult above 5 (D7 watch-list):")
    for r in hi.itertuples():
        print(f"    {r.state_key:12s} {r.fy_end}  {r.deposit_accts_per_adult:.2f}")

    print(f"\n  -> {OUT/'table1_descriptives.csv'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
