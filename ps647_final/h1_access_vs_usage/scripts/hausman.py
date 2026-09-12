#!/usr/bin/env python3
"""
STEP 6 — Diagnostic (b): Hausman test, FE versus RE.

H0: the state effects are uncorrelated with the regressors, so RE is consistent and efficient.
Rejecting H0 favours FE.

Standard one-way (entity effects) comparison, as the test is defined.
Writes output/table4_hausman.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from linearmodels.panel import PanelOLS, RandomEffects

ROOT_DIR = Path(__file__).resolve().parent.parent

OUT = ROOT_DIR / "output"
X = ["branches_per_lakh_adults", "atms_per_lakh_adults", "ln_nsdp_pc"]


def hausman(fe, re, names):
    b, B = fe.params[names].values, re.params[names].values
    Vb = fe.cov.loc[names, names].values
    VB = re.cov.loc[names, names].values
    d = b - B
    dV = Vb - VB
    stat = float(d @ np.linalg.pinv(dV) @ d)
    df = np.linalg.matrix_rank(dV)
    return stat, df, float(1 - stats.chi2.cdf(stat, df))


def main() -> int:
    d = pd.read_csv(OUT / "panel_analysis.csv").set_index(["state_key", "fy_end"])
    rows = []
    print("  Hausman test, FE vs RE (entity effects; H0: RE consistent)\n")
    print(f"  {'equation':12s} {'chi2':>10s} {'df':>4s} {'p':>9s}   favours")
    print("  " + "-" * 56)
    for y in ["Access", "Usage", "AUG"]:
        fe = PanelOLS(d[y], d[X], entity_effects=True).fit()
        Xc = d[X].copy(); Xc["const"] = 1.0
        re = RandomEffects(d[y], Xc).fit()
        stat, df, p = hausman(fe, re, X)
        fav = "FE" if p < 0.05 else "RE"
        rows.append({"equation": y, "chi2": stat, "df": df, "p_value": p, "favours": fav})
        print(f"  {y:12s} {stat:10.3f} {df:>4d} {p:9.4f}   {fav}")

    pd.DataFrame(rows).to_csv(OUT / "table4_hausman.csv", index=False)
    print(f"\n  -> {OUT/'table4_hausman.csv'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
