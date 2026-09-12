#!/usr/bin/env python3
"""
D12 — Estimate the three equations on the extended FY2012-FY2023 panel.

Identical specification to scripts/estimate.py except the regressor set: branches only,
since ATMs cannot extend before 2018. Two-way FE (state + year), SEs clustered by state.
Also runs the Hausman diagnostic and the D7 robustness trim on this panel.

Writes output/table6_long_results.csv, output/table7_long_hausman.csv,
       output/table8_long_robustness.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from linearmodels.panel import PanelOLS, RandomEffects

ROOT_DIR = Path(__file__).resolve().parent.parent

OUT = ROOT_DIR / "output"
X = ["branches_per_lakh_adults", "ln_nsdp_pc"]
EQS = [("(1) Access", "Access"), ("(2) Usage", "Usage"), ("(3) AUG", "AUG")]


def fit(d, y):
    return PanelOLS(d[y], d[X], entity_effects=True, time_effects=True,
                    drop_absorbed=True).fit(cov_type="clustered", cluster_entity=True)


def run(panel, tag):
    d = panel.set_index(["state_key", "fy_end"])
    res = {y: fit(d, y) for _, y in EQS}
    rows = [{"spec": tag, "equation": eq, "dependent": y, "regressor": v,
             "coef": res[y].params[v], "se": res[y].std_errors[v],
             "t": res[y].tstats[v], "p": res[y].pvalues[v],
             "ci_lo": res[y].conf_int().loc[v, "lower"],
             "ci_hi": res[y].conf_int().loc[v, "upper"],
             "N": int(res[y].nobs), "r2_within": res[y].rsquared_within}
            for eq, y in EQS for v in X]
    return res, pd.DataFrame(rows)


def show(res, label):
    print(f"\n{'='*88}\n  {label}\n{'='*88}")
    for eq, y in EQS:
        r = res[y]
        print(f"\n  {eq}   N={int(r.nobs)}   within-R2={r.rsquared_within:.4f}")
        print(f"    {'regressor':28s} {'coef':>12s} {'se':>10s} {'t':>8s} {'p':>8s}   95% CI")
        for v in X:
            ci = r.conf_int().loc[v]
            st = "***" if r.pvalues[v] < .01 else "**" if r.pvalues[v] < .05 else "*" if r.pvalues[v] < .10 else ""
            print(f"    {v:28s} {r.params[v]:12.5f} {r.std_errors[v]:10.5f} "
                  f"{r.tstats[v]:8.2f} {r.pvalues[v]:8.3f}   "
                  f"[{ci['lower']:9.5f},{ci['upper']:9.5f}] {st}")
    print("\n  identity check, (3) = (1) - (2):")
    v = X[0]
    b, dd, t = res["Access"].params[v], res["Usage"].params[v], res["AUG"].params[v]
    assert np.isclose(t, b - dd, atol=1e-9)
    print(f"    {v:28s} {b:.5f} - ({dd:.5f}) = {b-dd:.5f}   theta {t:.5f}   OK")


def hausman(fe, re, names):
    d = fe.params[names].values - re.params[names].values
    dV = fe.cov.loc[names, names].values - re.cov.loc[names, names].values
    stat = float(d @ np.linalg.pinv(dV) @ d)
    df = np.linalg.matrix_rank(dV)
    return stat, df, float(1 - stats.chi2.cdf(stat, df))


def main() -> int:
    panel = pd.read_csv(OUT / "panel_long_analysis.csv")
    res, tbl = run(panel, "long_12yr")
    show(res, "EXTENDED PANEL FY2012-FY2023 — two-way FE, SEs clustered by state")
    tbl.to_csv(OUT / "table6_long_results.csv", index=False)

    # ---- Hausman ----
    d = panel.set_index(["state_key", "fy_end"])
    print("\n  Hausman FE vs RE:")
    hrows = []
    for _, y in EQS:
        fe = PanelOLS(d[y], d[X], entity_effects=True).fit()
        Xc = d[X].copy(); Xc["const"] = 1.0
        re_ = RandomEffects(d[y], Xc).fit()
        s_, df_, p_ = hausman(fe, re_, X)
        fav = "FE" if p_ < .05 else "RE"
        hrows.append({"equation": y, "chi2": s_, "df": df_, "p_value": p_, "favours": fav})
        print(f"    {y:10s} chi2={s_:9.3f} df={df_} p={p_:.4f}  favours {fav}")
    pd.DataFrame(hrows).to_csv(OUT / "table7_long_hausman.csv", index=False)

    # ---- D7 robustness ----
    cells = [("DELHI", 2023), ("CHANDIGARH", 2023)]
    m = panel.apply(lambda r: (r.state_key, r.fy_end) in cells, axis=1)
    res_t, tbl_t = run(panel[~m], "long_12yr_d7trim")
    print(f"\n  D7 robustness — dropping {int(m.sum())} cells (N {len(panel)} -> {len(panel)-int(m.sum())}):")
    print(f"    {'equation':12s} {'main':>11s} {'p':>7s} {'trimmed':>11s} {'p':>7s}")
    v = X[0]
    for eq, y in EQS:
        cm, pm = res[y].params[v], res[y].pvalues[v]
        ct, pt = res_t[y].params[v], res_t[y].pvalues[v]
        flag = "  SIGN FLIP" if cm * ct < 0 else ""
        print(f"    {eq:12s} {cm:11.5f} {pm:7.3f} {ct:11.5f} {pt:7.3f}{flag}")
    pd.concat([tbl, tbl_t], ignore_index=True).to_csv(OUT / "table8_long_robustness.csv", index=False)

    print(f"\n  -> table6_long_results.csv, table7_long_hausman.csv, table8_long_robustness.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
