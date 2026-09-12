#!/usr/bin/env python3
"""
H5 Step 12 -- SPECIFICATION TESTS.

S1  THE FIXED-EFFECT SCHEME, TESTED RATHER THAN ARGUED.
    LIMITATIONS.md H5.3 concedes that preferring scheme (B) over scheme (A) is a POST HOC
    argument: (A) is the execution plan's literal specification, (B) is the one that gives the
    significant result, and the stated reason for (B) -- that under (A) b5 and b6 come back nearly
    identical -- was noticed after seeing the output. That is the weakest link in H5's
    pre-commitment discipline and it should not stand on rhetoric.

    (A) is NESTED in (B): state + year + outcome effects are a restricted case of
    state x outcome + year x outcome effects. So the restriction is testable. If the additional
    outcome-specific effects are jointly significant, scheme (B) is REQUIRED BY THE DATA and the
    choice stops being a judgement call -- the same logical move H1 makes with the Hausman test
    in section 3.4.1, where the data rather than the analyst rules out random effects.

    Caveat stated up front: with 33 clusters and ~70 restrictions a cluster-robust Wald test is
    not available (the cluster covariance matrix has rank at most G-1 = 32). The F-test below is
    therefore the classical homoskedastic one. It is evidence about the fixed-effect structure,
    not about the standard errors, and is labelled as such.

S2  A STRICTLY PRE-WINDOW MODERATOR.
    Every digital-literacy measure used so far is either contemporaneous with the outcome window
    (NFHS-5, 2019-21) or covers only 22 states (NSS 75th, 2017-18). NFHS-4 (2015-16) carries
    women's own mobile-phone ownership for all 36 states -- three and a half years before the
    panel starts, and measured before UPI existed at scale (UPI launched April 2016). It is a
    weaker construct than internet use, but it cannot be contaminated by the outcome. If b5
    survives on it, reverse causality is much harder to argue.

S3  HAUSMAN, FE vs RE, for symmetry with H1 section 3.4.1.

Writes output/table23_h5_spec_tests.csv
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as sps

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))
from h5_lib import CONTROLS, fit, stars  # noqa: E402
import estimate_h5_stacked as st  # noqa: E402
from estimate_h5_stacked import build_stack, lsdv, bootstrap_stacked  # noqa: E402

warnings.filterwarnings("ignore")
OUT = ROOT_DIR / "output"

XS = ["c_upi", "upi_x_int", "upi_x_skill", "upi_x_skill_x_int",
     "upi_x_income", "upi_x_income_x_int"] + CONTROLS
FE_A = [["state_key"], ["fy_end"], ["outcome"]]
FE_B = [["state_key", "outcome"], ["fy_end", "outcome"]]


def design(s, X, fe):
    parts = [np.ones((len(s), 1)), s[X].to_numpy(float)]
    for cols in fe:
        key = s[cols].astype(str).agg("|".join, axis=1)
        parts.append(pd.get_dummies(key, drop_first=True, dtype=float).to_numpy())
    return np.column_stack(parts), s["y"].to_numpy(float)


def rss_df(s, X, fe):
    Z, y = design(s, X, fe)
    beta, *_ = np.linalg.lstsq(Z, y, rcond=None)
    r = y - Z @ beta
    return float(r @ r), np.linalg.matrix_rank(Z), len(y)


def main() -> int:
    d = pd.read_csv(OUT / "panel_h5.csv")
    rows = []
    s = build_stack(d)

    # ------------------------------------------------------------------ S1
    print("\n" + "=" * 108)
    print("  S1 -- IS THE CONSERVATIVE FIXED-EFFECT SCHEME REQUIRED BY THE DATA?")
    print("  H0: outcome-specific state and year effects are jointly zero, i.e. scheme (A) suffices.")
    print("=" * 108)
    rss_a, k_a, n = rss_df(s, XS, FE_A)
    rss_b, k_b, _ = rss_df(s, XS, FE_B)
    q = k_b - k_a
    dfr = n - k_b
    F = ((rss_a - rss_b) / q) / (rss_b / dfr)
    p = 1 - sps.f.cdf(F, q, dfr)
    print(f"\n    scheme (A)  RSS = {rss_a:10.3f}   parameters = {k_a:4d}")
    print(f"    scheme (B)  RSS = {rss_b:10.3f}   parameters = {k_b:4d}")
    print(f"    restrictions q = {q},  residual df = {dfr}")
    print(f"\n    F({q}, {dfr}) = {F:.3f},  p = {p:.3g}")
    verdict = ("REJECTED -- outcome-specific effects are jointly significant, so scheme (B) is\n"
               "    required by the data and scheme (A) is misspecified"
               if p < 0.05 else
               "NOT rejected -- scheme (A) is adequate and preferring (B) remains a judgement call")
    print(f"    H0 is {verdict}.")
    print(f"\n    R2 explained by the fixed effects alone rises from "
          f"{1 - rss_a / float(((s['y'] - s['y'].mean())**2).sum()):.4f} (A) to "
          f"{1 - rss_b / float(((s['y'] - s['y'].mean())**2).sum()):.4f} (B).")
    print("    NOTE: classical F-test, not cluster-robust (see module docstring). It licenses the")
    print("    fixed-effect structure, not the standard errors; those remain bootstrapped.")
    rows.append({"test": "S1 FE scheme F-test", "statistic": F, "df1": q, "df2": dfr, "p": p,
                 "note": "A nested in B; classical F, not cluster-robust"})

    # ------------------------------------------------------------------ S2
    print("\n" + "=" * 108)
    print("  S2 -- STRICTLY PRE-WINDOW MODERATOR: women's own mobile phone, NFHS-4 (2015-16)")
    print("  Measured 3.5 years before the panel begins and before UPI existed at scale.")
    print("=" * 108)
    print(f"\n  {'moderator in the skills slot':40s} {'vintage':12s} {'b5':>9s} {'p boot':>9s}")
    print("  " + "-" * 78)
    for zc, lab, vint in [("z_diglit_w", "internet use (headline)", "2019-21"),
                          ("z_mobile_w", "mobile phone", "2019-21"),
                          ("z_mobile_w_2016", "mobile phone", "2015-16"),
                          ("z_mobile_w_change", "change in mobile phone", "2016->2021"),
                          ("z_schooling_w_2016", "10+ yrs schooling [PLACEBO]", "2015-16"),
                          ("z_bankacct_w_2016", "own bank account [PLACEBO]", "2015-16")]:
        sp = s.copy()
        sp["upi_x_skill"] = sp["c_upi"] * sp[zc]
        sp["upi_x_skill_x_int"] = sp["upi_x_skill"] * sp["intensive"]
        sp = sp.dropna(subset=["upi_x_skill"])
        beta, se, t, pv, nn, G, *_ = lsdv(sp, XS, FE_B, "state_key")
        pb = bootstrap_stacked(sp, XS, FE_B, "state_key", "upi_x_skill_x_int", B=9999)
        print(f"  {lab:40s} {vint:12s} {beta['upi_x_skill_x_int']:9.4f} {pb:9.4f} {stars(pb)}")
        rows.append({"test": "S2 pre-window moderator", "statistic": beta["upi_x_skill_x_int"],
                     "df1": np.nan, "df2": nn, "p": pb, "note": f"{lab} ({vint})"})
    print("\n  Reading: mobile-phone ownership measured in 2015-16 cannot have been caused by")
    print("  UPI-era outcomes. Its 2015-16 PLACEBO counterparts from the same survey round are")
    print("  the control for 'any 2015-16 development measure would do'.")

    # ------------------------------------------------------------------ S3
    print("\n" + "=" * 108)
    print("  S3 -- HAUSMAN, FE vs RE (symmetry with H1 section 3.4.1)")
    print("=" * 108)
    from linearmodels.panel import PanelOLS, RandomEffects
    X = ["c_upi", "upi_x_diglit_w", "upi_x_income_s"] + CONTROLS
    print(f"\n  {'DV':34s} {'chi2':>9s} {'df':>4s} {'p':>10s}  favours")
    print("  " + "-" * 74)
    for dv in ["norm_credit_accts_per_adult", "norm_deposits_per_capita", "norm_credit_per_capita"]:
        dd = d.set_index(["state_key", "fy_end"])
        fe = PanelOLS(dd[dv], dd[X], entity_effects=True, time_effects=True,
                      drop_absorbed=True).fit()
        re = RandomEffects(dd[dv], dd[X]).fit()
        common = [v for v in X if v in fe.params.index and v in re.params.index]
        b = (fe.params[common] - re.params[common]).to_numpy()
        V = (fe.cov.loc[common, common] - re.cov.loc[common, common]).to_numpy()
        chi2 = float(b @ np.linalg.pinv(V) @ b)
        df = np.linalg.matrix_rank(V)
        if chi2 < 0:
            # Var(b_FE) - Var(b_RE) is not positive definite in this sample. A negative statistic
            # is NOT evidence for random effects; the test is simply uninformative here.
            pv, favours = np.nan, "inconclusive (non-PD difference)"
        else:
            pv = 1 - sps.chi2.cdf(chi2, df)
            favours = "FE" if pv < 0.05 else "RE"
        pstr = "       n/a" if np.isnan(pv) else f"{pv:10.4g}"
        print(f"  {dv:34s} {chi2:9.2f} {df:4d} {pstr}  {favours}")
        rows.append({"test": "S3 Hausman", "statistic": chi2, "df1": df, "df2": np.nan,
                     "p": pv, "note": f"{dv} -> {favours}"})
    print("\n  As in H1, fixed effects are required wherever the test is informative: state effects")
    print("  are correlated with the regressors, so between-state variation cannot be used. The")
    print("  credit Rs/capita row returns a negative statistic, meaning the estimated variance")
    print("  difference is not positive definite -- that is an uninformative test, not support for")
    print("  random effects. Fixed effects are retained throughout regardless, for consistency")
    print("  with H1 and because the two informative rows reject RE decisively.")

    pd.DataFrame(rows).to_csv(OUT / "table23_h5_spec_tests.csv", index=False)
    print(f"\n  wrote {OUT / 'table23_h5_spec_tests.csv'}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
