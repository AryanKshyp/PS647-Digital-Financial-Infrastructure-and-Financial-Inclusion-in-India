#!/usr/bin/env python3
"""
H5 Step 4 -- baseline and sequential entry (execution plan sections 6.1-6.2).

    Y_it = b1*UPI_it + b3*(UPI_it x DigLit_s) + b4*(UPI_it x Income_s)
           + g1*branches + g2*ATMs + g3*lnNSDP + mu_i + lambda_t + e_it

Two-way FE (state + year), SEs clustered by state, N=165 -- identical estimator to F12.
UPI is mean-centred; moderators are z-scored across the 33 states. So:

    b1 = the UPI effect for a state of AVERAGE conversion capacity
    b3 = how much that effect changes per 1 SD of digital literacy
    b4 = how much that effect changes per 1 SD of state income

Four columns, per execution plan section 6.2:
    (1) UPI only            -- must reproduce F12 exactly; this is a BUILD ASSERTION
    (2) + UPI x DigLit      -- H5a alone
    (3) + UPI x Income      -- H5b alone
    (4) + both              -- PREFERRED. The horse race.

If b3 is large in (2) and collapses in (4), the skills result was income all along. That is a
finding and it gets reported as one.

Writes output/table15_h5_main.csv
       output/table15b_h5_margins.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))
from h5_lib import CONTROLS, fit, stars, wild_cluster_bootstrap, _design, _ols, _cluster_se  # noqa: E402

OUT = ROOT_DIR / "output"

UPI = "c_upi"
SKILL = "upi_x_diglit_w"
INCOME = "upi_x_income_s"

SPECS = {
    "(1) UPI only":        [UPI] + CONTROLS,
    "(2) + skills":        [UPI, SKILL] + CONTROLS,
    "(3) + resources":     [UPI, INCOME] + CONTROLS,
    "(4) + both":          [UPI, SKILL, INCOME] + CONTROLS,
}

DVS = [
    ("norm_credit_accts_per_adult", "ACCESS  credit accounts / adult", "HEADLINE"),
    ("norm_deposits_per_capita",    "USAGE   deposits Rs / capita",    ""),
    ("norm_credit_per_capita",      "USAGE   credit Rs / capita",      ""),
    ("norm_deposit_accts_per_adult", "ACCESS  deposit accounts / adult (entangled, D17)", ""),
    ("Access",                      "composite Access",                ""),
    ("Usage",                       "composite Usage",                 ""),
    ("AUG",                         "composite AUG = Access - Usage",  ""),
]

F12_UPI_ACCESS = 0.31578   # FINDINGS.md F12, composite Access
F12_UPI_USAGE = 0.18330


def verify_lsdv_matches_panelols(d: pd.DataFrame) -> None:
    """The bootstrap uses an LSDV refit. Prove it is the same model as PanelOLS before trusting it.

    Coefficients must be identical. Clustered SEs differ by a CONSTANT factor, because
    linearmodels and this code count the absorbed fixed effects differently in the CR1
    small-sample correction. That constant is verified to be the same for every regressor, and
    it cancels exactly in the bootstrap: t_obs and every t* are formed with the same formula,
    so any common scale on the SE divides out of the comparison |t*| >= |t_obs|.
    """
    ratios = []
    for y in ["norm_credit_accts_per_adult", "Usage"]:
        X = SPECS["(4) + both"]
        r = fit(d, y, X)
        yv, Z, cl, _ = _design(d, y, X)
        beta, resid = _ols(yv, Z)
        se = _cluster_se(Z, resid, cl)
        for i, v in enumerate(X):
            if not np.isclose(r.params[v], beta[i + 1], atol=1e-10):
                sys.exit(f"FATAL: LSDV != PanelOLS on {v}: {beta[i+1]} vs {r.params[v]}")
            ratios.append(se[i + 1] / r.std_errors[v])
    ratios = np.array(ratios)
    if ratios.std() > 1e-9:
        sys.exit(f"FATAL: SE scale is not constant across regressors (sd={ratios.std():.2e}); "
                 "it would not cancel in the bootstrap")
    print(f"  LSDV verified identical to PanelOLS: coefficients match to <1e-10; clustered SEs")
    print(f"  differ by a constant df factor {ratios.mean():.6f} (sd {ratios.std():.1e}) which")
    print(f"  cancels in the bootstrap t-ratio.\n")


def main() -> int:
    d = pd.read_csv(OUT / "panel_h5.csv")
    print("\n" + "=" * 104)
    print("  H5 STEP 4 -- BASELINE AND SEQUENTIAL ENTRY")
    print("  Two-way FE (state + year), SEs clustered by state, N=165")
    print("  UPI mean-centred | moderators z-scored across 33 states")
    print("=" * 104 + "\n")

    verify_lsdv_matches_panelols(d)

    # ---------------------------------------------------------------- build assertion
    r1 = fit(d, "Access", SPECS["(1) UPI only"])
    r1u = fit(d, "Usage", SPECS["(1) UPI only"])
    print("  BUILD ASSERTION -- column (1) must reproduce F12 on the composite DVs")
    print(f"    Access : got {r1.params[UPI]:.5f}  F12 reported {F12_UPI_ACCESS:.5f}  "
          f"{'OK' if np.isclose(r1.params[UPI], F12_UPI_ACCESS, atol=1e-5) else 'MISMATCH'}")
    print(f"    Usage  : got {r1u.params[UPI]:.5f}  F12 reported {F12_UPI_USAGE:.5f}  "
          f"{'OK' if np.isclose(r1u.params[UPI], F12_UPI_USAGE, atol=1e-5) else 'MISMATCH'}")
    if not np.isclose(r1.params[UPI], F12_UPI_ACCESS, atol=1e-5):
        sys.exit("FATAL: H5 panel does not reproduce F12. The merge broke something.")
    print()

    rows, margin_rows = [], []
    for dv, label, tag in DVS:
        print("=" * 104)
        print(f"  DV: {label}   {tag}")
        print("=" * 104)
        header = f"  {'regressor':22s}" + "".join(f"{c:>21s}" for c in SPECS)
        print(header)
        print("  " + "-" * (22 + 21 * len(SPECS)))

        fits = {c: fit(d, dv, X) for c, X in SPECS.items()}
        for v, vlabel in [(UPI, "UPI (at mean cap.)"), (SKILL, "UPI x skills"),
                          (INCOME, "UPI x resources")]:
            line = f"  {vlabel:22s}"
            for c in SPECS:
                r = fits[c]
                if v in r.params.index:
                    line += f"{r.params[v]:>13.4f}{stars(r.pvalues[v]):<8s}"
                else:
                    line += f"{'--':>21s}"
            print(line)
            line = f"  {'':22s}"
            for c in SPECS:
                r = fits[c]
                line += (f"{'(' + format(r.std_errors[v], '.4f') + ')':>21s}"
                         if v in r.params.index else f"{'':>21s}")
            print(line)

        line = f"  {'within-R2':22s}"
        for c in SPECS:
            line += f"{fits[c].rsquared_within:>21.4f}"
        print(line + "\n")

        for c, X in SPECS.items():
            r = fits[c]
            for v in X:
                rows.append({"dependent": dv, "dv_label": label, "column": c, "regressor": v,
                             "coef": r.params[v], "se": r.std_errors[v], "t": r.tstats[v],
                             "p": r.pvalues[v], "ci_lo": r.conf_int().loc[v, "lower"],
                             "ci_hi": r.conf_int().loc[v, "upper"],
                             "N": int(r.nobs), "r2_within": r.rsquared_within})

        # ------------------------------------------------ marginal effects from column (4)
        r4 = fits["(4) + both"]
        b1, b3, b4 = r4.params[UPI], r4.params[SKILL], r4.params[INCOME]
        V = r4.cov
        print(f"  MARGINAL EFFECT of UPI at different levels of digital literacy "
              f"(income held at its mean):")
        for z, zl in [(-1.5, "very low  (-1.5 SD, ~Bihar)"), (-1.0, "low       (-1.0 SD)"),
                      (0.0, "average   ( 0.0 SD)"), (1.0, "high      (+1.0 SD)"),
                      (1.5, "very high (+1.5 SD, ~Kerala)")]:
            me = b1 + b3 * z
            var = V.loc[UPI, UPI] + z ** 2 * V.loc[SKILL, SKILL] + 2 * z * V.loc[UPI, SKILL]
            se = np.sqrt(max(var, 0))
            lo, hi = me - 1.96 * se, me + 1.96 * se
            sig = "" if lo < 0 < hi else "  *"
            print(f"    {zl:30s} {me:8.4f}  se {se:.4f}   95% CI [{lo:7.4f}, {hi:7.4f}]{sig}")
            margin_rows.append({"dependent": dv, "z_diglit": z, "label": zl.split("(")[0].strip(),
                                "marginal_effect": me, "se": se, "ci_lo": lo, "ci_hi": hi})
        print()

    pd.DataFrame(rows).to_csv(OUT / "table15_h5_main.csv", index=False)
    pd.DataFrame(margin_rows).to_csv(OUT / "table15b_h5_margins.csv", index=False)
    print(f"  wrote {OUT / 'table15_h5_main.csv'}")
    print(f"  wrote {OUT / 'table15b_h5_margins.csv'}\n")

    # ---------------------------------------------------------------- wild cluster bootstrap
    print("=" * 104)
    print("  WILD CLUSTER BOOTSTRAP (R6, mandatory) -- Rademacher, null imposed, B=9999")
    print("  33 clusters, and the key coefficients are identified off one number per state.")
    print("  This is the case where the cluster-robust t-approximation is least trustworthy.")
    print("=" * 104)
    print(f"\n  {'DV':34s} {'coefficient':16s} {'estimate':>10s} {'p clustered':>12s} {'p bootstrap':>12s}")
    print("  " + "-" * 88)
    boot = []
    for dv, label, _ in DVS[:4]:
        r4 = fit(d, dv, SPECS["(4) + both"])
        for v, vl in [(SKILL, "UPI x skills"), (INCOME, "UPI x resources"), (UPI, "UPI")]:
            w = wild_cluster_bootstrap(d, dv, SPECS["(4) + both"], v, B=9999)
            print(f"  {dv[:34]:34s} {vl:16s} {w['coef']:10.4f} {r4.pvalues[v]:12.4f} "
                  f"{w['p_wcb']:12.4f} {stars(w['p_wcb'])}")
            boot.append({"dependent": dv, "regressor": v, "coef": w["coef"],
                         "se_cluster": w["se_cluster"], "t": w["t"],
                         "p_clustered": r4.pvalues[v], "p_wild_bootstrap": w["p_wcb"],
                         "wcb_ci_lo": w["ci_lo"], "wcb_ci_hi": w["ci_hi"], "B": w["B"]})
        print()
    pd.DataFrame(boot).to_csv(OUT / "table15c_h5_bootstrap.csv", index=False)
    print(f"  wrote {OUT / 'table15c_h5_bootstrap.csv'}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
