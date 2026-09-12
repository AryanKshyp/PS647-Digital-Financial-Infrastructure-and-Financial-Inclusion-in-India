#!/usr/bin/env python3
"""
H5 Step 7 -- threshold specification (execution plan section 6.4).

The linear interaction assumes returns to skill are constant. The ICRIER "necessary but not
sufficient" reading implies something different: a FLOOR, where literacy matters up to a
threshold and then stops. Terciles distinguish the two.

    Y_it = b1*UPI + sum_{k=2,3} d_k*(UPI x 1[DigLit in tercile k]) + controls + mu_i + lambda_t

    d3 > d2 > 0   increasing returns to skill -- true complementarity
    d2 ~ d3 > 0   floor effect -- literacy matters up to a threshold, then stops
    d2 ~ d3 ~ 0   no threshold structure

T1 (lowest third) is the omitted category, so d2 and d3 read as the extra UPI effect relative to
the least digitally literate states. 11 states per tercile.

Also runs the tercile version of the sharp test, where the question is whether the
extensive/intensive gap widens monotonically across terciles.

Writes output/table18_h5_threshold.csv
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))
from h5_lib import CONTROLS, fit, stars, wild_cluster_bootstrap  # noqa: E402
from estimate_h5_stacked import build_stack, lsdv, bootstrap_stacked  # noqa: E402

warnings.filterwarnings("ignore")
OUT = ROOT_DIR / "output"

DVS = [
    ("norm_credit_accts_per_adult", "ACCESS credit accts/adult (extensive)"),
    ("norm_deposits_per_capita",    "USAGE  deposits Rs/capita (intensive)"),
    ("norm_credit_per_capita",      "USAGE  credit Rs/capita   (intensive)"),
]


def main() -> int:
    d = pd.read_csv(OUT / "panel_h5.csv")
    print("\n" + "=" * 100)
    print("  H5 STEP 7 -- THRESHOLD SPECIFICATION (digital-literacy terciles)")
    print("  T1 (least digitally literate 11 states) is the omitted category.")
    print("=" * 100)

    terc = d.drop_duplicates("state_key").set_index("state_key")["diglit_tercile"]
    dl = d.drop_duplicates("state_key").set_index("state_key")["diglit_w"]
    for t in ["T1_low", "T2_mid", "T3_high"]:
        mem = sorted(terc[terc == t].index)
        print(f"    {t:8s} diglit {dl[mem].min():4.1f}-{dl[mem].max():4.1f}  n={len(mem)}")

    X = ["c_upi", "upi_x_T2_mid", "upi_x_T3_high",
         "upi_x_income_s"] + CONTROLS
    rows = []
    for dv, label in DVS:
        r = fit(d, dv, X)
        print(f"\n{'=' * 100}\n  DV: {label}\n{'=' * 100}")
        print(f"  {'term':44s} {'coef':>10s} {'se':>9s} {'p clust':>9s} {'p boot':>9s}")
        print("  " + "-" * 86)
        for v, lab in [("c_upi", "b1  UPI effect in T1 (lowest literacy)"),
                       ("upi_x_T2_mid", "d2  extra UPI effect, T2 (middle)"),
                       ("upi_x_T3_high", "d3  extra UPI effect, T3 (highest)"),
                       ("upi_x_income_s", "b4  UPI x resources (held in)")]:
            pb = wild_cluster_bootstrap(d, dv, X, v, B=9999)["p_wcb"]
            print(f"  {lab:44s} {r.params[v]:10.4f} {r.std_errors[v]:9.4f} "
                  f"{r.pvalues[v]:9.4f} {pb:9.4f} {stars(pb)}")
            rows.append({"spec": "unstacked", "dependent": dv, "term": v, "label": lab,
                         "coef": r.params[v], "se": r.std_errors[v],
                         "p_clustered": r.pvalues[v], "p_wild_bootstrap": pb, "N": int(r.nobs)})

        d2, d3 = r.params["upi_x_T2_mid"], r.params["upi_x_T3_high"]
        print(f"\n    UPI effect by tercile:  T1 {r.params['c_upi']:+.4f}   "
              f"T2 {r.params['c_upi'] + d2:+.4f}   T3 {r.params['c_upi'] + d3:+.4f}")
        if d3 > d2 > 0:
            shape = "increasing returns to skill (d3 > d2 > 0) -- true complementarity"
        elif d2 > 0 and d3 > 0 and abs(d3 - d2) < 0.5 * max(abs(d2), abs(d3)):
            shape = "floor effect (d2 ~ d3 > 0) -- matters up to a threshold, then stops"
        elif d3 < d2 < 0:
            shape = "decreasing (d3 < d2 < 0) -- catch-up, low-literacy states gain most"
        else:
            shape = "no clean monotone structure"
        print(f"    shape: {shape}")

    # --------------------------------------------------- tercile version of the sharp test
    print(f"\n{'=' * 100}")
    print("  TERCILE SHARP TEST -- does the extensive/intensive gap widen across terciles?")
    print("  Scheme (B) fixed effects. T1 omitted.")
    print("=" * 100)
    s = build_stack(d)
    s = s.merge(d[["state_key", "fy_end", "diglit_tercile"]].drop_duplicates(),
                on=["state_key", "fy_end"], how="left")
    for t in ["T2_mid", "T3_high"]:
        s[f"upi_x_{t}"] = s["c_upi"] * (s["diglit_tercile"] == t).astype(float)
        s[f"upi_x_{t}_x_int"] = s[f"upi_x_{t}"] * s["intensive"]

    Xs = ["c_upi", "upi_x_int", "upi_x_T2_mid", "upi_x_T2_mid_x_int",
          "upi_x_T3_high", "upi_x_T3_high_x_int",
          "upi_x_income", "upi_x_income_x_int"] + CONTROLS
    fe = [["state_key", "outcome"], ["fy_end", "outcome"]]
    beta, se, t, p, n, G, *_ = lsdv(s, Xs, fe, "state_key")
    print(f"\n  {'term':46s} {'coef':>10s} {'se':>9s} {'p boot':>9s}")
    print("  " + "-" * 78)
    for v, lab in [("upi_x_int", "gap (intensive - extensive) in T1"),
                   ("upi_x_T2_mid_x_int", "extra gap in T2"),
                   ("upi_x_T3_high_x_int", "extra gap in T3")]:
        pb = bootstrap_stacked(s, Xs, fe, "state_key", v, B=9999)
        print(f"  {lab:46s} {beta[v]:10.4f} {se[v]:9.4f} {pb:9.4f} {stars(pb)}")
        rows.append({"spec": "stacked_tercile", "dependent": "stacked", "term": v, "label": lab,
                     "coef": beta[v], "se": se[v], "p_clustered": p[v],
                     "p_wild_bootstrap": pb, "N": n})
    g1 = beta["upi_x_int"]
    print(f"\n    intensive-minus-extensive gap by tercile:  "
          f"T1 {g1:+.4f}   T2 {g1 + beta['upi_x_T2_mid_x_int']:+.4f}   "
          f"T3 {g1 + beta['upi_x_T3_high_x_int']:+.4f}")

    pd.DataFrame(rows).to_csv(OUT / "table18_h5_threshold.csv", index=False)
    print(f"\n  wrote {OUT / 'table18_h5_threshold.csv'}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
