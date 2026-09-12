#!/usr/bin/env python3
"""
STEP 4 — Diagnostic (a): within-state variation.  RUN BEFORE ANY ESTIMATION.

project_plan.pdf: "Within-state variation in the DFI index. Run this first; if DFI
barely moves within states, fixed effects have nothing to estimate from."

Per D10 there is no DFI index: the diagnostic applies to branches per lakh adults and
ATMs per lakh adults SEPARATELY. Those two are the formal gate. The dependent variables
and the control are reported in the same table because it is the identical computation
and the same question -- whether anything is left to estimate from once the fixed
effects are swept out.

Decomposition (Stata xtsum convention):
    overall sd  = sd(x_it)
    between sd  = sd(state means)
    within sd   = sd(x_it - mean_i + grand mean)          <- one-way, state FE only
    twoway sd   = sd(x_it - mean_i - mean_t + grand mean) <- what the model identifies from

THRESHOLDS, fixed before the numbers were seen:
    within share  = within sd / overall sd
      < 0.10  FAIL    -- fixed effects have nothing to work with; stop
    0.10-0.25 WEAK    -- proceed, but coefficients are fragile; flag prominently
      > 0.25  PASS
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent

OUT = ROOT_DIR / "output"

FAIL_BELOW, WEAK_BELOW = 0.10, 0.25

GATE = [
    ("branches_per_lakh_adults", "IV  Branches per lakh adults"),
    ("atms_per_lakh_adults",     "IV  ATMs per lakh adults"),
]
CONTEXT = [
    ("Access",     "DV1 Access"),
    ("Usage",      "DV2 Usage"),
    ("AUG",        "    AUG"),
    ("ln_nsdp_pc", "Ctl ln(NSDP per capita)"),
]


def decompose(d: pd.DataFrame, col: str) -> dict:
    x = d[col]
    grand = x.mean()
    mi = d.groupby("state_key")[col].transform("mean")
    mt = d.groupby("fy_end")[col].transform("mean")

    overall = x.std(ddof=1)
    between = d.groupby("state_key")[col].mean().std(ddof=1)
    within = (x - mi + grand).std(ddof=1)
    twoway = (x - mi - mt + grand).std(ddof=1)

    # how far each state travels over the six years, relative to its own mean
    rng = d.groupby("state_key")[col].agg(lambda s: s.max() - s.min())
    med_swing = (rng / d.groupby("state_key")[col].mean()).median()

    return {
        "column": col, "overall_sd": overall, "between_sd": between,
        "within_sd": within, "twoway_sd": twoway,
        "within_share": within / overall, "twoway_share": twoway / overall,
        "median_within_state_swing_pct": 100 * med_swing,
    }


def verdict(share: float) -> str:
    if share < FAIL_BELOW:
        return "FAIL"
    if share < WEAK_BELOW:
        return "WEAK"
    return "PASS"


def main() -> int:
    d = pd.read_csv(OUT / "panel_analysis.csv")

    rows = []
    for col, label in GATE + CONTEXT:
        r = decompose(d, col)
        r["variable"] = label
        r["role"] = "GATE" if (col, label) in GATE else "context"
        r["verdict"] = verdict(r["within_share"]) if r["role"] == "GATE" else ""
        rows.append(r)

    t = pd.DataFrame(rows)[["variable", "column", "role", "overall_sd", "between_sd",
                            "within_sd", "twoway_sd", "within_share", "twoway_share",
                            "median_within_state_swing_pct", "verdict"]]
    t.to_csv(OUT / "table2_within_variation.csv", index=False)

    print(f"  thresholds fixed in advance: FAIL < {FAIL_BELOW:.2f}, "
          f"WEAK < {WEAK_BELOW:.2f}, PASS above\n")
    print(f"  {'variable':30s} {'overall':>9s} {'between':>9s} {'within':>9s} "
          f"{'2-way':>9s} {'within%':>9s} {'swing%':>8s}  verdict")
    print("  " + "-" * 100)
    for r in rows:
        print(f"  {r['variable']:30s} {r['overall_sd']:9.3f} {r['between_sd']:9.3f} "
              f"{r['within_sd']:9.3f} {r['twoway_sd']:9.3f} "
              f"{100*r['within_share']:8.1f}% {r['median_within_state_swing_pct']:7.1f}%  "
              f"{r['verdict']}")

    gate = [r for r in rows if r["role"] == "GATE"]
    print("\n  GATE (project_plan.pdf diagnostic (a), applied per D10 to each regressor):")
    for r in gate:
        print(f"    {r['variable']:30s} within share {100*r['within_share']:5.1f}%  -> {r['verdict']}")

    if any(r["verdict"] == "FAIL" for r in gate):
        print("\n  *** GATE FAILED — fixed effects have nothing to estimate from. STOP. ***")
        return 1
    if any(r["verdict"] == "WEAK" for r in gate):
        print("\n  Gate passed but WEAK for at least one regressor — flag prominently in results.")
    else:
        print("\n  Gate PASSED for both regressors. Estimation may proceed.")

    print(f"\n  -> {OUT/'table2_within_variation.csv'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
