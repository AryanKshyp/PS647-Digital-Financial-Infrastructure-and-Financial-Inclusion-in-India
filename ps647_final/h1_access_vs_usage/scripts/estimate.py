#!/usr/bin/env python3
"""
STEP 5 — Estimate the three equations.

Two-way fixed effects (state + year), standard errors CLUSTERED BY STATE, per project_plan.pdf.
Per D10 the regressors are branches and ATMs separately -- no composite index.

    (1) Access_it = a_i + L_t + b1*branches + b2*ATMs + g*lnNSDP + e
    (2) Usage_it  = a_i + L_t + d1*branches + d2*ATMs + g*lnNSDP + e
    (3) AUG_it    = a_i + L_t + t1*branches + t2*ATMs + g*lnNSDP + e

Equation (3) is NOT a third finding. By linearity t = b - d; its role is to supply the
standard error on that difference, which is the formal test of H1. The identity is asserted.

Writes output/table3_main_results.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from linearmodels.panel import PanelOLS

ROOT_DIR = Path(__file__).resolve().parent.parent

OUT = ROOT_DIR / "output"
X = ["branches_per_lakh_adults", "atms_per_lakh_adults", "ln_nsdp_pc"]


def fit(d: pd.DataFrame, y: str):
    m = PanelOLS(d[y], d[X], entity_effects=True, time_effects=True, drop_absorbed=True)
    return m.fit(cov_type="clustered", cluster_entity=True)


def run(panel: pd.DataFrame, tag: str = "main"):
    d = panel.set_index(["state_key", "fy_end"])
    res = {y: fit(d, y) for y in ["Access", "Usage", "AUG"]}

    rows = []
    for eq, y in [("(1) Access", "Access"), ("(2) Usage", "Usage"), ("(3) AUG", "AUG")]:
        r = res[y]
        for v in X:
            rows.append({
                "spec": tag, "equation": eq, "dependent": y, "regressor": v,
                "coef": r.params[v], "se": r.std_errors[v], "t": r.tstats[v],
                "p": r.pvalues[v],
                "ci_lo": r.conf_int().loc[v, "lower"], "ci_hi": r.conf_int().loc[v, "upper"],
                "N": int(r.nobs), "r2_within": r.rsquared_within,
            })
    return res, pd.DataFrame(rows)


def show(res, tbl, label):
    print(f"\n{'='*94}\n  {label}\n{'='*94}")
    for eq, y in [("(1) Access", "Access"), ("(2) Usage", "Usage"), ("(3) AUG", "AUG")]:
        r = res[y]
        print(f"\n  {eq}   N={int(r.nobs)}   within-R2={r.rsquared_within:.4f}")
        print(f"    {'regressor':28s} {'coef':>12s} {'se':>10s} {'t':>8s} {'p':>8s}   {'95% CI':>22s}")
        for v in X:
            ci = r.conf_int().loc[v]
            star = "***" if r.pvalues[v] < .01 else "**" if r.pvalues[v] < .05 else "*" if r.pvalues[v] < .10 else ""
            print(f"    {v:28s} {r.params[v]:12.5f} {r.std_errors[v]:10.5f} "
                  f"{r.tstats[v]:8.2f} {r.pvalues[v]:8.3f}   "
                  f"[{ci['lower']:9.5f},{ci['upper']:9.5f}] {star}")

    # linearity identity: theta = beta - delta
    print("\n  identity check, equation (3) = (1) - (2):")
    ok = True
    for v in X[:2]:
        b, dd, t = res["Access"].params[v], res["Usage"].params[v], res["AUG"].params[v]
        good = np.isclose(t, b - dd, atol=1e-9)
        ok &= good
        print(f"    {v:28s} beta {b:10.5f} - delta {dd:10.5f} = {b-dd:10.5f}   "
              f"theta {t:10.5f}   {'OK' if good else 'MISMATCH'}")
    assert ok, "linearity identity failed"

    # joint F-test on the two infrastructure regressors (D10)
    print("\n  joint test, branches = ATMs = 0 (D10 — replaces the composite index):")
    for eq, y in [("(1) Access", "Access"), ("(2) Usage", "Usage"), ("(3) AUG", "AUG")]:
        w = res[y].wald_test(formula="branches_per_lakh_adults = atms_per_lakh_adults = 0")
        print(f"    {eq:12s} chi2={w.stat:8.3f}  df={w.df}  p={w.pval:.4f}")


def main() -> int:
    panel = pd.read_csv(OUT / "panel_analysis.csv")
    res, tbl = run(panel, "main")
    show(res, tbl, "STEP 5 — MAIN RESULTS: two-way FE (state + year), SEs clustered by state")
    tbl.to_csv(OUT / "table3_main_results.csv", index=False)
    print(f"\n  -> {OUT/'table3_main_results.csv'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
