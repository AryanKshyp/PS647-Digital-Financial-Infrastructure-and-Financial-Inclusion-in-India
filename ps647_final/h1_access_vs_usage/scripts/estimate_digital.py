#!/usr/bin/env python3
"""
Same two-way FE estimation as Step 5 (scripts/estimate.py), with UPI added as a third
infrastructure regressor. Per D16:

    UPI measure = PhonePe registered users per adult, LEVEL (not log).

    (1) Access_it = a_i + L_t + b1*branches + b2*ATMs + b3*UPI + g*lnNSDP + e
    (2) Usage_it  = a_i + L_t + d1*branches + d2*ATMs + d3*UPI + g*lnNSDP + e
    (3) AUG_it    = a_i + L_t + t1*branches + t2*ATMs + t3*UPI + g*lnNSDP + e

Panel: output/panel_digital.csv, 33 states x FY2019-FY2023 = 165 rows (one year shorter
than Step 5's 198, since PhonePe starts fy_end=2019). Two-way FE (state+year), SEs
clustered by state, linearmodels.PanelOLS -- identical methodology to Step 5.

AUG is estimated only to supply the identity check (theta = beta - delta) as in Step 5;
it is not reported as a fourth finding.

Writes output/table9_digital_results.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from linearmodels.panel import PanelOLS

ROOT_DIR = Path(__file__).resolve().parent.parent

OUT = ROOT_DIR / "output"
X = ["branches_per_lakh_adults", "atms_per_lakh_adults", "pp_users_per_adult", "ln_nsdp_pc"]


def fit(d: pd.DataFrame, y: str):
    m = PanelOLS(d[y], d[X], entity_effects=True, time_effects=True, drop_absorbed=True)
    return m.fit(cov_type="clustered", cluster_entity=True)


def main() -> int:
    panel = pd.read_csv(OUT / "panel_digital.csv")
    d = panel.set_index(["state_key", "fy_end"])
    res = {y: fit(d, y) for y in ["Access", "Usage", "AUG"]}

    print(f"\n{'='*98}\n  UPI-AUGMENTED FE: branches + ATMs + UPI (registered users/adult), "
          f"33 states x FY2019-FY2023, N=165\n{'='*98}")

    rows = []
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
            rows.append({
                "spec": "digital", "equation": eq, "dependent": y, "regressor": v,
                "coef": r.params[v], "se": r.std_errors[v], "t": r.tstats[v], "p": r.pvalues[v],
                "ci_lo": ci["lower"], "ci_hi": ci["upper"],
                "N": int(r.nobs), "r2_within": r.rsquared_within,
            })

    print("\n  identity check, equation (3) = (1) - (2):")
    ok = True
    for v in X[:3]:
        b, dd, t = res["Access"].params[v], res["Usage"].params[v], res["AUG"].params[v]
        good = np.isclose(t, b - dd, atol=1e-9)
        ok &= good
        print(f"    {v:28s} beta {b:10.5f} - delta {dd:10.5f} = {b-dd:10.5f}   "
              f"theta {t:10.5f}   {'OK' if good else 'MISMATCH'}")
    assert ok, "linearity identity failed"

    print("\n  joint test, branches = ATMs = UPI = 0:")
    for eq, y in [("(1) Access", "Access"), ("(2) Usage", "Usage"), ("(3) AUG", "AUG")]:
        w = res[y].wald_test(
            formula="branches_per_lakh_adults = atms_per_lakh_adults = pp_users_per_adult = 0")
        print(f"    {eq:12s} chi2={w.stat:8.3f}  df={w.df}  p={w.pval:.4f}")

    print("\n  H1 decision rule (D10), applied to UPI same as branches/ATMs:")
    for label, v in [("branches", "branches_per_lakh_adults"),
                      ("ATMs", "atms_per_lakh_adults"),
                      ("UPI users/adult", "pp_users_per_adult")]:
        b, dd = res["Access"].params[v], res["Usage"].params[v]
        reading = ("H1 pattern (access>usage>0)" if b > dd > 0 else
                   "genuine deepening (access~=usage, both>0)" if b > 0 and dd > 0 else
                   "no support (not both positive)")
        print(f"    {label:16s} beta_access={b:9.5f}  beta_usage={dd:9.5f}   -> {reading}")

    tbl = pd.DataFrame(rows)
    tbl.to_csv(OUT / "table9_digital_results.csv", index=False)
    print(f"\n  -> {OUT/'table9_digital_results.csv'}")
    same_sample_baseline()
    return 0



def same_sample_baseline():
    """
    Diagnostic, not a specification: the same 165 rows WITHOUT UPI.

    Needed because this panel is FY2019-2023 while F5-F8 was FY2018-2023. Without this
    column there is no way to tell whether a branches/ATMs coefficient moved because UPI
    was added or merely because the sample lost a year.

    Writes output/table10_digital_samplecheck.csv
    """
    d = pd.read_csv(OUT / "panel_digital.csv").set_index(["state_key", "fy_end"])
    X0 = ["branches_per_lakh_adults", "atms_per_lakh_adults", "ln_nsdp_pc"]
    old = pd.read_csv(OUT / "table3_main_results.csv")

    rows = []
    for y in ["Access", "Usage", "AUG"]:
        r0 = PanelOLS(d[y], d[X0], entity_effects=True, time_effects=True).fit(
            cov_type="clustered", cluster_entity=True)
        r1 = fit(d, y)
        for v in X0[:2]:
            o = old[(old.dependent == y) & (old.regressor == v)].iloc[0]
            rows.append({
                "dependent": y, "regressor": v,
                "coef_198_noUPI": o.coef, "p_198_noUPI": o.p,
                "coef_165_noUPI": r0.params[v], "p_165_noUPI": r0.pvalues[v],
                "coef_165_UPI": r1.params[v], "p_165_UPI": r1.pvalues[v],
                "r2w_198_noUPI": o.r2_within,
                "r2w_165_noUPI": r0.rsquared_within,
                "r2w_165_UPI": r1.rsquared_within,
            })
    pd.DataFrame(rows).to_csv(OUT / "table10_digital_samplecheck.csv", index=False)
    print(f"  -> {OUT/'table10_digital_samplecheck.csv'}")


if __name__ == "__main__":
    sys.exit(main())
