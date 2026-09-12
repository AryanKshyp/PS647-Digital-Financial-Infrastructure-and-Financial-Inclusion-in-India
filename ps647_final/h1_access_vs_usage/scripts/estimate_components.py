#!/usr/bin/env python3
"""
D17 — Decompose Access and Usage into their four underlying indicators and re-run.

F12 found UPI -> Access = +0.316 (p<0.001). But PhonePe registration requires a KYC-linked
bank account, so pp_users_per_adult and deposit_accts_per_adult (half of Access) are
definitionally entangled. Credit accounts are not: a bank loan is neither required for nor
created by PhonePe registration.

Same spec as D16 throughout: two-way FE (state + year), SEs clustered by state, N=165.

Panel A: each of the four normalised indicators as its own dependent variable.
Panel B: the credit-only H1 triple -- Access_c = credit accounts per adult, Usage unchanged,
         AUG_c = Access_c - Usage.

Writes output/table11_components.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from linearmodels.panel import PanelOLS

ROOT_DIR = Path(__file__).resolve().parent.parent

OUT = ROOT_DIR / "output"
X = ["branches_per_lakh_adults", "atms_per_lakh_adults", "pp_users_per_adult", "ln_nsdp_pc"]
UPI = "pp_users_per_adult"

COMPONENTS = [
    ("Access", "norm_deposit_accts_per_adult", "deposit accounts / adult", "ENTANGLED"),
    ("Access", "norm_credit_accts_per_adult",  "credit accounts / adult",  "clean"),
    ("Usage",  "norm_deposits_per_capita",     "deposits Rs / capita",     "clean"),
    ("Usage",  "norm_credit_per_capita",       "credit Rs / capita",       "clean"),
]


def fit(d, y):
    return PanelOLS(d[y], d[X], entity_effects=True, time_effects=True).fit(
        cov_type="clustered", cluster_entity=True)


def line(label, r, v, note=""):
    star = "***" if r.pvalues[v] < .01 else "**" if r.pvalues[v] < .05 else "*" if r.pvalues[v] < .10 else ""
    return (f"    {label:26s} {r.params[v]:10.5f} {r.std_errors[v]:9.5f} "
            f"{r.pvalues[v]:8.3f} {star:4s} {note}")


def main() -> int:
    panel = pd.read_csv(OUT / "panel_digital.csv")
    d = panel.set_index(["state_key", "fy_end"])
    rows = []

    # ---------------- Panel A: the four components -------------------------
    print(f"\n{'='*92}\n  PANEL A — each indicator as its own DV.  Coefficient on UPI (users/adult)"
          f"\n{'='*92}")
    print(f"    {'dependent variable':26s} {'coef':>10s} {'se':>9s} {'p':>8s}      status")
    res = {}
    for side, col, label, status in COMPONENTS:
        r = fit(d, col)
        res[col] = r
        print(line(label, r, UPI, f"[{side} side, {status}]"))
        for v in X:
            rows.append({"panel": "A", "side": side, "dependent": col, "label": label,
                         "status": status, "regressor": v,
                         "coef": r.params[v], "se": r.std_errors[v], "p": r.pvalues[v],
                         "ci_lo": r.conf_int().loc[v, "lower"],
                         "ci_hi": r.conf_int().loc[v, "upper"],
                         "N": int(r.nobs), "r2_within": r.rsquared_within})

    print(f"\n    within-R2:  " + "   ".join(
        f"{lab.split('/')[0].strip()}={res[c].rsquared_within:.3f}" for _, c, lab, _ in COMPONENTS))

    # linearity: Access coef must equal the mean of its two component coefs (A3)
    print("\n  identity check — composite = mean of its two components (A3):")
    ok = True
    for comp, parts in [("Access", ["norm_deposit_accts_per_adult", "norm_credit_accts_per_adult"]),
                        ("Usage",  ["norm_deposits_per_capita", "norm_credit_per_capita"])]:
        rc = fit(d, comp)
        for v in X[:3]:
            mean_parts = np.mean([fit(d, p).params[v] for p in parts])
            good = np.isclose(rc.params[v], mean_parts, atol=1e-9)
            ok &= good
            if v == UPI:
                print(f"    {comp:8s} {v:22s} composite {rc.params[v]:9.5f} "
                      f"= mean of components {mean_parts:9.5f}   {'OK' if good else 'MISMATCH'}")
    assert ok, "composite is not the mean of its components"

    # ---------------- Panel B: credit-only H1 triple -----------------------
    print(f"\n{'='*92}\n  PANEL B — credit-only H1 triple "
          f"(Access_c = credit accounts/adult; Usage unchanged)\n{'='*92}")
    dd = d.copy()
    dd["Access_c"] = dd["norm_credit_accts_per_adult"]
    dd["AUG_c"] = dd["Access_c"] - dd["Usage"]

    trip = {y: fit(dd, y) for y in ["Access_c", "Usage", "AUG_c"]}
    for y in ["Access_c", "Usage", "AUG_c"]:
        r = trip[y]
        print(f"\n  {y}   N={int(r.nobs)}   within-R2={r.rsquared_within:.4f}")
        print(f"    {'regressor':26s} {'coef':>10s} {'se':>9s} {'p':>8s}")
        for v in X:
            print(line(v, r, v))
            rows.append({"panel": "B", "side": "", "dependent": y, "label": y, "status": "",
                         "regressor": v, "coef": r.params[v], "se": r.std_errors[v],
                         "p": r.pvalues[v],
                         "ci_lo": r.conf_int().loc[v, "lower"],
                         "ci_hi": r.conf_int().loc[v, "upper"],
                         "N": int(r.nobs), "r2_within": r.rsquared_within})

    for v in X[:3]:
        b, de, t = trip["Access_c"].params[v], trip["Usage"].params[v], trip["AUG_c"].params[v]
        assert np.isclose(t, b - de, atol=1e-9), f"identity failed for {v}"
    print("\n  identity theta = beta - delta holds for all three regressors.")

    print("\n  H1 rule (D10) on the credit-only triple:")
    for label, v in [("branches", "branches_per_lakh_adults"), ("ATMs", "atms_per_lakh_adults"),
                     ("UPI users/adult", UPI)]:
        b, de = trip["Access_c"].params[v], trip["Usage"].params[v]
        reading = ("H1 pattern (access>usage>0)" if b > de > 0 else
                   "reversed (usage>access>0)" if de > b > 0 else
                   "no support (not both positive)")
        print(f"    {label:16s} beta_access={b:9.5f}  beta_usage={de:9.5f}   -> {reading}")

    # ---------------- D17 decision rule ------------------------------------
    dep = res["norm_deposit_accts_per_adult"]
    cre = res["norm_credit_accts_per_adult"]
    print(f"\n{'='*92}\n  D17 DECISION RULE\n{'='*92}")
    print(f"    UPI -> deposit accounts : {dep.params[UPI]:9.5f}  p={dep.pvalues[UPI]:.4f}")
    print(f"    UPI -> credit accounts  : {cre.params[UPI]:9.5f}  p={cre.pvalues[UPI]:.4f}")
    sig_c, sig_d = cre.pvalues[UPI] < 0.05, dep.pvalues[UPI] < 0.05
    if sig_c and sig_d:
        verd = ("BOTH large -> F12's Access result is not merely definitional, but only the\n"
                "    CREDIT result gets a substantive reading. Deposit version stays caveated.")
    elif sig_c:
        verd = "credit-only survives -> F12's Access result is NOT merely definitional."
    elif sig_d:
        verd = ("credit NULL, deposit large -> F12's Access coefficient IS the accounting\n"
                "    relationship. Access must be reported CREDIT-ONLY from here; withdraw the\n"
                "    deposit-account version rather than showing it alongside.")
    else:
        verd = "neither significant -> F12's Access result does not survive decomposition at all."
    print(f"    verdict: {verd}")

    pd.DataFrame(rows).to_csv(OUT / "table11_components.csv", index=False)
    print(f"\n  -> {OUT/'table11_components.csv'}")
    d7_robustness()
    return 0


def d7_robustness():
    """
    D7's pre-committed robustness check, re-run on the components.

    This is load-bearing here, not routine: the D17 verdict rests on the deposit-account
    coefficient being null, and deposit accounts is precisely the series with the known
    source defect (D7). Suspect cells inside FY2019-2023 are Delhi 2023 and Chandigarh
    2023 (A6).

    Writes output/table12_components_d7.csv
    """
    p = pd.read_csv(OUT / "panel_digital.csv")
    bad = (((p.state_key == "DELHI") & (p.fy_end == 2023)) |
           ((p.state_key == "CHANDIGARH") & (p.fy_end == 2023)))
    assert bad.sum() == 2, f"expected 2 suspect cells, found {bad.sum()}"

    print(f"\n{'='*92}\n  D7 ROBUSTNESS — drop Delhi 2023 and Chandigarh 2023 (coefficient on UPI)"
          f"\n{'='*92}")
    print(f"    {'dependent':24s} {'all 165':>22s} {'drop D7 cells (163)':>24s}")
    rows = []
    for col, lab in [("norm_deposit_accts_per_adult", "deposit accts / adult"),
                     ("norm_credit_accts_per_adult", "credit accts / adult"),
                     ("Access", "Access (composite)")]:
        cells = {}
        for keep, tag in [(p.index.notna(), "all"), (~bad, "drop")]:
            d = p[keep].set_index(["state_key", "fy_end"])
            r = fit(d, col)
            cells[tag] = (r.params[UPI], r.std_errors[UPI], r.pvalues[UPI], int(r.nobs))
        a, b = cells["all"], cells["drop"]
        print(f"    {lab:24s} {a[0]:9.5f} (p={a[2]:.4f}) {b[0]:14.5f} (p={b[2]:.4f})")
        rows.append({"dependent": col, "label": lab,
                     "coef_all165": a[0], "se_all165": a[1], "p_all165": a[2],
                     "coef_drop_d7": b[0], "se_drop_d7": b[1], "p_drop_d7": b[2],
                     "N_drop_d7": b[3]})
    pd.DataFrame(rows).to_csv(OUT / "table12_components_d7.csv", index=False)
    print(f"\n  -> {OUT/'table12_components_d7.csv'}")


if __name__ == "__main__":
    sys.exit(main())
