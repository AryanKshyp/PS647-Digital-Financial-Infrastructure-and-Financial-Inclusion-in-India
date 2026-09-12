#!/usr/bin/env python3
"""
H5 Step 5 -- R1 PLACEBO INTERACTIONS. This test OUTRANKS the main results.

Pre-committed override (H5_execution_plan.md section 7), fixed before any coefficient was seen:

    If the placebo interactions return a beta of SIMILAR MAGNITUDE AND SIGNIFICANCE to the
    digital-literacy interaction, then that interaction is NOT identifying a digital-skill
    effect -- it is a generic development gradient. H5a is then reported as NOT SEPARATELY
    IDENTIFIED regardless of its own p-value.

Each placebo is substituted for the digital-literacy moderator in the preferred specification and
run ONE AT A TIME (section 3.4: with 33 clusters, entering them jointly would burn power without
answering the question).

    Y_it = b1*UPI + b3*(UPI x MODERATOR_s) + b4*(UPI x Income_s) + controls + mu_i + lambda_t

THE PLACEBOS, and why these
---------------------------
schooling_w / schooling_m / everschool_w come from NFHS-5 -- THE SAME SURVEY, the same
respondents, the same fieldwork year and the same question format as the digital-literacy
moderator. The only thing that differs is the construct: general education rather than digital
skill. That makes them the sharpest placebo available: no difference in survey design, sampling,
timing or measurement error can explain a difference in results.

lit2011 (Census 2011 general literacy) and urban_share_nfhs (derived urbanisation) are the
conventional development placebos and are weaker, but they are what a reader will ask for.

Writes output/table16_h5_placebo.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))
from h5_lib import CONTROLS, fit, stars, wild_cluster_bootstrap  # noqa: E402

OUT = ROOT_DIR / "output"
UPI, INCOME = "c_upi", "upi_x_income_s"

TRUE_MODERATOR = ("diglit_w", "NFHS-5 women ever used internet", "TREATMENT")

PLACEBOS = [
    ("schooling_w",      "NFHS-5 women 10+ yrs schooling",  "PLACEBO  same instrument"),
    ("schooling_m",      "NFHS-5 men 10+ yrs schooling",    "PLACEBO  same instrument"),
    ("everschool_w",     "NFHS-5 female 6+ ever in school", "PLACEBO  same instrument"),
    ("lit2011",          "Census 2011 general literacy",    "PLACEBO  conventional"),
    ("urban_share_nfhs", "derived urban share",             "PLACEBO  conventional"),
]

ALTERNATIVES = [
    ("diglit_m",       "NFHS-5 men ever used internet",   "ALT digital measure"),
    ("diglit_both",    "NFHS-5 mean of women and men",    "ALT digital measure"),
    ("mobile_w",       "NFHS-5 women own mobile phone",   "ALT digital measure"),
    ("nss75_computer", "NSS 75th can operate computer",   "ALT pre-window (n=22)"),
    ("nss75_internet", "NSS 75th can use internet",       "ALT pre-window (n=22)"),
    ("diglit_gap",     "male minus female internet use",  "ALT gender gap (H4 link)"),
]

DVS = [
    ("norm_credit_accts_per_adult", "ACCESS credit accts/adult"),
    ("norm_deposits_per_capita",    "USAGE  deposits Rs/capita"),
    ("norm_credit_per_capita",      "USAGE  credit Rs/capita"),
    ("Usage",                       "USAGE  composite"),
]

# "similar magnitude" for the override: placebo |beta| reaches this share of the treatment |beta|
SIMILAR_RATIO = 0.60


def run(d, dv, mod):
    v = f"upi_x_{mod}"
    X = [UPI, v, INCOME] + CONTROLS
    r = fit(d, dv, X)
    w = wild_cluster_bootstrap(d, dv, X, v, B=9999)
    return {"coef": r.params[v], "se": r.std_errors[v], "p": r.pvalues[v],
            "p_wcb": w["p_wcb"], "N": int(r.nobs), "r2": r.rsquared_within}


def main() -> int:
    d = pd.read_csv(OUT / "panel_h5.csv")
    print("\n" + "=" * 104)
    print("  H5 STEP 5 -- R1 PLACEBO INTERACTIONS  (this test outranks the main results)")
    print("  Each moderator substituted one at a time into the preferred specification.")
    print("  Income interaction and all controls held fixed throughout.")
    print("=" * 104)

    rows, verdicts = [], {}
    for dv, dvlabel in DVS:
        print(f"\n{'=' * 104}\n  DV: {dvlabel}   ({dv})\n{'=' * 104}")
        print(f"  {'moderator':34s} {'role':26s} {'beta3':>9s} {'se':>8s} "
              f"{'p clust':>8s} {'p boot':>8s} {'N':>5s}")
        print("  " + "-" * 98)

        t = run(d, dv, TRUE_MODERATOR[0])
        print(f"  {TRUE_MODERATOR[1]:34s} {TRUE_MODERATOR[2]:26s} {t['coef']:9.4f} {t['se']:8.4f} "
              f"{t['p']:8.4f} {t['p_wcb']:8.4f} {t['N']:5d} {stars(t['p_wcb'])}")
        rows.append({"dependent": dv, "moderator": TRUE_MODERATOR[0], "role": "TREATMENT", **t})
        print("  " + "-" * 98)

        worst_ratio, worst_name, n_sig = 0.0, None, 0
        for mod, label, role in PLACEBOS:
            p = run(d, dv, mod)
            ratio = abs(p["coef"]) / abs(t["coef"]) if t["coef"] != 0 else np.inf
            same_sign = np.sign(p["coef"]) == np.sign(t["coef"])
            flag = ""
            if p["p_wcb"] < 0.10 and same_sign and ratio >= SIMILAR_RATIO:
                flag = "  <-- FIRES"
                n_sig += 1
            if same_sign and ratio > worst_ratio:
                worst_ratio, worst_name = ratio, label
            print(f"  {label:34s} {role:26s} {p['coef']:9.4f} {p['se']:8.4f} "
                  f"{p['p']:8.4f} {p['p_wcb']:8.4f} {p['N']:5d} {stars(p['p_wcb'])}{flag}")
            rows.append({"dependent": dv, "moderator": mod, "role": role,
                         "ratio_to_treatment": round(ratio, 3), "same_sign": bool(same_sign), **p})

        print("  " + "-" * 98)
        for mod, label, role in ALTERNATIVES:
            a = run(d, dv, mod)
            print(f"  {label:34s} {role:26s} {a['coef']:9.4f} {a['se']:8.4f} "
                  f"{a['p']:8.4f} {a['p_wcb']:8.4f} {a['N']:5d} {stars(a['p_wcb'])}")
            rows.append({"dependent": dv, "moderator": mod, "role": role, **a})

        fired = n_sig > 0
        verdicts[dv] = (fired, worst_name, worst_ratio, t)
        print(f"\n  -> treatment beta3 = {t['coef']:+.4f} (p_boot {t['p_wcb']:.4f}); "
              f"largest same-signed placebo = {worst_ratio:.0%} of it ({worst_name})")
        print(f"  -> R1 VERDICT: {'FIRES -- H5a NOT separately identified on this DV' if fired else 'CLEARS -- the digital-skill interaction is not a generic development gradient'}")

    pd.DataFrame(rows).to_csv(OUT / "table16_h5_placebo.csv", index=False)
    print(f"\n  wrote {OUT / 'table16_h5_placebo.csv'}")

    print("\n" + "=" * 104)
    print("  R1 SUMMARY -- the pre-committed override")
    print("=" * 104)
    for dv, dvlabel in DVS:
        fired, worst_name, ratio, t = verdicts[dv]
        state = "FIRES  " if fired else "CLEARS "
        print(f"  {state} {dvlabel:28s} beta3={t['coef']:+.4f} p_boot={t['p_wcb']:.3f}  "
              f"max same-signed placebo {ratio:.0%}")
    print("=" * 104 + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
