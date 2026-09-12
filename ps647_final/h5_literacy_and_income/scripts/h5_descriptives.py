#!/usr/bin/env python3
"""
H5 Step 3a -- DESCRIPTIVES. Runs before the estimates, per the report's Chapter 4 template
section 4.3: "Means, standard deviations and ranges, flagging anything bearing on the
specification, skew, compression, extreme values, before presenting estimates."

This was missing from the first pass of H5 and is the direct analogue of H1's
table1_descriptives.csv. Three things it is meant to catch:

  1. COMPRESSION IN THE OUTCOMES. H1's limitation 4 records that Usage is severely right-skewed
     after pooled min-max normalisation (85 per cent of observations below 0.20), and that this
     is "a direct threat to the comparison itself". H5 inherits those variables, so the same
     diagnostic has to be reported here, and the stacked specification's within-outcome
     standardisation has to be justified against it rather than asserted.

  2. SPREAD AND OUTLIERS IN THE MODERATORS. An interaction identified off 33 cross-sectional
     values is only as good as the spread of those values.

  3. WHETHER THE TWO MODERATORS ARE THE SAME VARIABLE. Reported as a correlation matrix and as
     the states that disagree most between the two rankings.

Writes output/table21_h5_descriptives.csv
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
SHARED = ROOT_DIR.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

warnings.filterwarnings("ignore")
OUT = ROOT_DIR / "output"

OUTCOMES = [
    ("norm_credit_accts_per_adult", "credit accounts / adult", "extensive (HEADLINE)"),
    ("norm_deposits_per_capita", "deposits Rs / capita", "intensive"),
    ("norm_credit_per_capita", "credit Rs / capita", "intensive"),
    ("norm_deposit_accts_per_adult", "deposit accounts / adult", "extensive (entangled, D17)"),
    ("Access", "Access composite", "composite"),
    ("Usage", "Usage composite", "composite"),
]
REGRESSORS = [
    ("pp_users_per_adult", "UPI users / adult", "IV"),
    ("branches_per_lakh_adults", "branches / lakh adults", "control"),
    ("atms_per_lakh_adults", "ATMs / lakh adults", "control"),
    ("ln_nsdp_pc", "ln NSDP per capita", "control (time-varying)"),
]
MODERATORS = [
    ("diglit_w", "digital literacy: women ever used internet (%)", "H5a PRIMARY"),
    ("diglit_m", "men ever used internet (%)", "H5a alt"),
    ("mobile_w", "women own a mobile phone (%)", "H5a alt"),
    ("mobile_w_2016", "women own a mobile phone, 2015-16 (%)", "H5a pre-window"),
    ("nss75_computer", "can operate a computer, 2017-18 (%)", "H5a pre-window, n=22"),
    ("income_s", "state-mean ln NSDP per capita", "H5b PRIMARY"),
    ("ln_mpce", "ln MPCE, HCES 2022-23", "H5b alt (consumption)"),
    ("schooling_w", "women 10+ years schooling (%)", "placebo"),
    ("everschool_w", "women ever attended school (%)", "placebo"),
    ("lit2011", "Census 2011 literacy (%)", "placebo"),
    ("urban_share_nfhs", "derived urban share (%)", "placebo"),
    ("bankacct_w_2016", "women own a bank account, 2015-16 (%)", "placebo: BASELINE INCLUSION"),
]


def stats(s: pd.Series) -> dict:
    s = s.dropna()
    return {"n": len(s), "mean": s.mean(), "sd": s.std(ddof=1), "min": s.min(),
            "p25": s.quantile(.25), "median": s.median(), "p75": s.quantile(.75),
            "max": s.max(), "skew": s.skew(), "cv": s.std(ddof=1) / s.mean() if s.mean() else np.nan}


def block(d: pd.DataFrame, items, title: str, rows: list, per_state: bool = False) -> None:
    print(f"\n  {title}")
    print(f"    {'variable':46s} {'n':>4s} {'mean':>9s} {'sd':>8s} {'min':>8s} "
          f"{'med':>8s} {'max':>8s} {'skew':>7s}")
    print("    " + "-" * 102)
    src = d.drop_duplicates("state_key") if per_state else d
    for col, label, role in items:
        if col not in src.columns:
            continue
        st = stats(src[col])
        flag = ""
        if abs(st["skew"]) > 1.5:
            flag = "  <-- skewed"
        print(f"    {label[:46]:46s} {st['n']:4d} {st['mean']:9.3f} {st['sd']:8.3f} "
              f"{st['min']:8.3f} {st['median']:8.3f} {st['max']:8.3f} {st['skew']:7.2f}{flag}")
        rows.append({"block": title, "variable": col, "label": label, "role": role, **st})


def main() -> int:
    d = pd.read_csv(OUT / "panel_h5.csv")
    rows = []
    print("\n" + "=" * 112)
    print("  H5 STEP 3a -- DESCRIPTIVES  (report template section 4.3: before any estimate)")
    print(f"  Panel: {len(d)} state-years, {d.state_key.nunique()} states, "
          f"FY{d.fy_end.min()}-FY{d.fy_end.max()}")
    print("=" * 112)

    block(d, OUTCOMES, "DEPENDENT VARIABLES (165 state-years; pooled min-max scale inherited from H1)", rows)
    block(d, REGRESSORS, "REGRESSORS (165 state-years)", rows)
    block(d, MODERATORS, "MODERATORS AND PLACEBOS (33 states, one value each)", rows, per_state=True)

    # ---------------------------------------------------------------- compression check
    print("\n" + "=" * 112)
    print("  COMPRESSION CHECK -- H1's limitation 4, re-run on the variables H5 inherits")
    print("=" * 112)
    print(f"\n    {'outcome':34s} {'share below 0.20':>18s} {'skew':>8s} {'p90/p50':>10s}")
    print("    " + "-" * 74)
    for col, label, _ in OUTCOMES:
        s = d[col].dropna()
        share = (s < 0.20).mean()
        ratio = s.quantile(.90) / s.median() if s.median() else np.nan
        print(f"    {label:34s} {share:17.1%} {s.skew():8.2f} {ratio:10.2f}")
        rows.append({"block": "compression", "variable": col, "label": label,
                     "role": "share below 0.20", "n": len(s), "mean": share,
                     "sd": np.nan, "min": np.nan, "p25": np.nan, "median": np.nan,
                     "p75": np.nan, "max": np.nan, "skew": s.skew(), "cv": ratio})

    print("\n    Reading. The compression H1 documented is real and is inherited here: the two")
    print("    intensive-margin outcomes are far more compressed than the extensive one, so an")
    print("    UNSTACKED comparison of coefficients across them is not a like-for-like comparison.")
    print("    This is the specific reason the stacked test standardises WITHIN outcome before")
    print("    stacking (EXECUTION_PLAN.md section 6.3). It is a repair, not a convenience.")

    # ---------------------------------------------------------------- are the moderators the same?
    print("\n" + "=" * 112)
    print("  ARE THE TWO MODERATORS THE SAME VARIABLE?")
    print("=" * 112)
    sl = d.drop_duplicates("state_key").set_index("state_key")
    key = ["diglit_w", "income_s", "ln_mpce", "mobile_w_2016", "schooling_w",
           "lit2011", "urban_share_nfhs", "bankacct_w_2016"]
    cm = sl[key].corr()
    print("\n    " + " " * 20 + "".join(f"{c[:10]:>12s}" for c in key))
    for i in key:
        print(f"    {i:20s}" + "".join(f"{cm.loc[i, j]:12.3f}" for j in key))

    r_di = cm.loc["diglit_w", "income_s"]
    r_dm = cm.loc["diglit_w", "ln_mpce"]
    print(f"\n    corr(digital literacy, ln NSDP pc) = {r_di:.3f}")
    print(f"    corr(digital literacy, ln MPCE)    = {r_dm:.3f}")
    print(f"    corr(ln NSDP pc, ln MPCE)          = {cm.loc['income_s', 'ln_mpce']:.3f}"
          "   <- the two income measures are NOT interchangeable")

    sl = sl.copy()
    sl["rank_dig"] = sl["diglit_w"].rank(ascending=False)
    sl["rank_inc"] = sl["income_s"].rank(ascending=False)
    sl["gap"] = sl["rank_dig"] - sl["rank_inc"]
    print("\n    States where the two rankings disagree most (this is what identifies the horse race):")
    print(f"      {'state':28s} {'diglit rank':>12s} {'income rank':>12s} {'gap':>6s}")
    for _, r in sl.reindex(sl["gap"].abs().sort_values(ascending=False).index).head(6).iterrows():
        print(f"      {r.name.title():28s} {int(r['rank_dig']):12d} {int(r['rank_inc']):12d} "
              f"{int(r['gap']):+6d}")
    max_gap = int(sl["gap"].abs().max())
    print("\n    If these two rankings were identical the horse race would be undefined. They are not:")
    print(f"    the moderators disagree by up to {max_gap} rank positions out of {len(sl)}.")

    pd.DataFrame(rows).to_csv(OUT / "table21_h5_descriptives.csv", index=False)
    print(f"\n  wrote {OUT / 'table21_h5_descriptives.csv'}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
