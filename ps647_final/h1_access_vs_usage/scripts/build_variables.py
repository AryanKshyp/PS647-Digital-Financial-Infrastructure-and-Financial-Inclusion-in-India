#!/usr/bin/env python3
"""
STEP 2 — Construct the analysis variables.

Reads output/panel_raw.csv, writes output/panel_analysis.csv.
data/ is never touched.

INDEPENDENT (D10 — two separate regressors, real units, NO index, NO normalisation):
    branches_per_lakh_adults, atms_per_lakh_adults

DEPENDENT — the PDF uses two different denominators deliberately (A4):
    Access indicators, per ADULT (18+):
        deposit_accts_per_adult, credit_accts_per_adult
    Usage indicators, per CAPITA (total population), in rupees:
        deposits_per_capita, credit_per_capita

Each of the four is min-max normalised 0-1, pooled over all 198 state-years (A2),
then combined with equal weight (A3):
    Access = mean(norm deposit accts/adult, norm credit accts/adult)
    Usage  = mean(norm deposits/capita,     norm credit/capita)
    AUG    = Access - Usage

The PDF's "Access 35%, Usage 45%" weights are NOT applied (A1): they weight RBI's
composite index, which is not built here, and applying them would make
AUG = 0.35A - 0.45U, contradicting the PDF's own definition of AUG.

CONTROL:
    ln_nsdp_pc = ln(per-capita NSDP, current prices)

Un-normalised columns are kept alongside so every number stays auditable.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent

OUT = ROOT_DIR / "output"

CRORE = 1e7  # 1 crore rupees

ACCESS_IND = ["deposit_accts_per_adult", "credit_accts_per_adult"]
USAGE_IND = ["deposits_per_capita", "credit_per_capita"]


def minmax(s: pd.Series) -> pd.Series:
    """Pooled min-max over the whole panel (A2)."""
    lo, hi = s.min(), s.max()
    assert hi > lo, f"{s.name}: zero range, cannot normalise"
    return (s - lo) / (hi - lo)


def main() -> int:
    d = pd.read_csv(OUT / "panel_raw.csv")

    adults = d["pop_18plus_000"] * 1_000      # persons 18+
    everyone = d["pop_total_000"] * 1_000     # total persons

    # --- independent variables: per LAKH adults, real units (D10) ---
    d["branches_per_lakh_adults"] = d["branches"] / (adults / 1e5)
    d["atms_per_lakh_adults"] = d["atms"] / (adults / 1e5)

    # --- Access indicators: per ADULT (A4) ---
    d["deposit_accts_per_adult"] = d["deposit_accounts"] / adults
    d["credit_accts_per_adult"] = d["credit_accounts"] / adults

    # --- Usage indicators: rupees per CAPITA, total population (A4) ---
    d["deposits_per_capita"] = d["deposits_rs_crore"] * CRORE / everyone
    d["credit_per_capita"] = d["credit_rs_crore"] * CRORE / everyone

    # --- normalise the four DV indicators, pooled (A2) ---
    for c in ACCESS_IND + USAGE_IND:
        d["norm_" + c] = minmax(d[c])

    # --- composites, equal weight within each dimension (A3) ---
    d["Access"] = d[["norm_" + c for c in ACCESS_IND]].mean(axis=1)
    d["Usage"] = d[["norm_" + c for c in USAGE_IND]].mean(axis=1)
    d["AUG"] = d["Access"] - d["Usage"]

    # --- control ---
    d["ln_nsdp_pc"] = np.log(d["nsdp_pc_rs"])

    d.to_csv(OUT / "panel_analysis.csv", index=False)

    print(f"  -> {OUT/'panel_analysis.csv'}  {d.shape[0]} rows x {d.shape[1]} cols\n")

    print("  independent (real units, no index — D10):")
    for c in ["branches_per_lakh_adults", "atms_per_lakh_adults"]:
        print(f"    {c:28s} {d[c].min():8.2f} .. {d[c].max():8.2f}   mean {d[c].mean():8.2f}")

    print("\n  Access indicators (per adult):")
    for c in ACCESS_IND:
        print(f"    {c:28s} {d[c].min():8.3f} .. {d[c].max():8.3f}   mean {d[c].mean():8.3f}")

    print("\n  Usage indicators (rupees per capita):")
    for c in USAGE_IND:
        print(f"    {c:28s} {d[c].min():10,.0f} .. {d[c].max():10,.0f}  mean {d[c].mean():10,.0f}")

    print("\n  composites (0-1):")
    for c in ["Access", "Usage", "AUG"]:
        print(f"    {c:28s} {d[c].min():8.3f} .. {d[c].max():8.3f}   mean {d[c].mean():8.3f}")
    print(f"    {'ln_nsdp_pc':28s} {d['ln_nsdp_pc'].min():8.3f} .. {d['ln_nsdp_pc'].max():8.3f}")

    # identity check: AUG must be exactly Access - Usage
    assert np.allclose(d["AUG"], d["Access"] - d["Usage"]), "AUG identity broken"
    # normalised indicators must span exactly [0,1]
    for c in ACCESS_IND + USAGE_IND:
        assert abs(d["norm_" + c].min()) < 1e-12 and abs(d["norm_" + c].max() - 1) < 1e-12, \
            f"norm_{c} does not span [0,1]"
    print("\n  checks: AUG = Access - Usage exactly; all four normalised indicators span [0,1]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
