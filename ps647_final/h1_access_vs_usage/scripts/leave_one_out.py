#!/usr/bin/env python3
"""
Closes the long-standing open item in DECISIONS.md:

    "Before writing up, eyeball Maharashtra: loan accounts per adult rise 0.29 -> 0.78
     over six years. Monotone and plausible (lending booked in Mumbai), but check it
     isn't driving the result."

Credit accounts per adult is now the headline dependent variable (D17/F13), so this
matters more than when it was written. Rather than eyeball one state, refit the headline
coefficient 33 times, dropping each state in turn.

Writes output/table13_leave_one_out.csv
"""
import sys
from pathlib import Path

import pandas as pd
from linearmodels.panel import PanelOLS

ROOT_DIR = Path(__file__).resolve().parent.parent

OUT = ROOT_DIR / "output"
X = ["branches_per_lakh_adults", "atms_per_lakh_adults", "pp_users_per_adult", "ln_nsdp_pc"]
Y = "norm_credit_accts_per_adult"
UPI = "pp_users_per_adult"


def coef(d):
    r = PanelOLS(d[Y], d[X], entity_effects=True, time_effects=True).fit(
        cov_type="clustered", cluster_entity=True)
    return r.params[UPI], r.pvalues[UPI], int(r.nobs)


def main() -> int:
    p = pd.read_csv(OUT / "panel_digital.csv")
    base, base_p, _ = coef(p.set_index(["state_key", "fy_end"]))
    print(f"  full sample: {base:.4f}  p={base_p:.4f}\n")

    rows = [{"dropped": "(none)", "coef": base, "p": base_p, "change": 0.0}]
    for s in sorted(p.state_key.unique()):
        c, pv, _ = coef(p[p.state_key != s].set_index(["state_key", "fy_end"]))
        rows.append({"dropped": s, "coef": c, "p": pv, "change": c - base})

    df = pd.DataFrame(rows)
    loo = df[df.dropped != "(none)"]

    print("  five most influential states:")
    for _, r in loo.reindex(loo.change.abs().sort_values(ascending=False).index).head(5).iterrows():
        print(f"    drop {r.dropped:26s} {r.coef:8.4f}  p={r.p:.4f}   ({r.change:+.4f})")

    print(f"\n  range over all 33 refits : {loo.coef.min():.4f} to {loo.coef.max():.4f}")
    print(f"  worst p-value            : {loo.p.max():.4f}")
    print(f"  sign flips               : {(loo.coef <= 0).sum()}")
    print(f"  drops below 5%           : {(loo.p >= 0.05).sum()}")

    assert (loo.coef > 0).all() and (loo.p < 0.05).all(), \
        "headline coefficient is not robust to dropping a single state"

    df.to_csv(OUT / "table13_leave_one_out.csv", index=False)
    print(f"\n  -> {OUT/'table13_leave_one_out.csv'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
