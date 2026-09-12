#!/usr/bin/env python3
"""
H5 Step 2 -- merge moderators into the H1 digital panel and build interaction terms.

Reads  ../h1_access_vs_usage/output/panel_digital.csv   (33 states x FY2019-FY2023 = 165 rows, D15, untouched)
       data/09_diglit.csv         (33 states, moderators + placebos)
Writes output/panel_h5.csv   (this folder)

CONSTRUCTION RULES, fixed here before any estimation
----------------------------------------------------
1. NOTHING IN THE H1 PANEL IS RECOMPUTED. Every column carried over from panel_digital.csv is
   asserted byte-identical. The dependent variables keep the pooled min-max scaling from A2, so
   every H5 coefficient stays on the same scale as F12/F13 and the two chapters are comparable.

2. UPI is MEAN-CENTRED, not rescaled. In a two-way FE model centring a regressor leaves its
   coefficient unchanged, so the H5 baseline column must reproduce F12's +0.31578 exactly. That
   is the build assertion, not a result.

3. MODERATORS ARE Z-SCORED across the 33 states (mean 0, SD 1). Two reasons:
   - centring is required for beta_1 to read as "the UPI effect at average conversion capacity"
     rather than at an out-of-support zero;
   - scaling makes beta_3 read as "change in the UPI effect per 1 SD of digital literacy",
     which is comparable across moderators measured in different units (percent internet use vs
     log rupees). Without it the skills-vs-resources horse race would be decided by units.

4. THE INCOME MODERATOR IS TIME-INVARIANT: the FY2019-FY2023 state mean of ln NSDP per capita.
   Deliberate. The skills moderator is a single-wave survey and cannot be time-varying, so making
   income time-varying would hand H5b five times the identifying variation and the horse race
   would not be a fair test. Time-varying ln_nsdp_pc STAYS in as a main-effect control, exactly
   as in F12.

5. Moderators are z-scored BEFORE interacting; the interaction is then the product of two
   centred variables. Interactions are not themselves re-centred (that would break the
   marginal-effect interpretation).
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent   # this hypothesis folder
SHARED = ROOT_DIR.parent                            # ps647_final/: data/ and raw/ are shared
OUT = ROOT_DIR / "output"
H1_OUT = SHARED / "h1_access_vs_usage" / "output"   # H5 reads H1's panel, never writes to it
DATA = SHARED / "data"

# moderators and placebos that get z-scored and interacted with UPI
MODERATORS = [
    "diglit_w",        # PRIMARY H5a  -- NFHS-5 women ever used internet
    "diglit_m",        # alt H5a      -- NFHS-5 men ever used internet
    "diglit_both",     # alt H5a      -- mean of the two
    "diglit_gap",      # H4 link      -- male minus female internet use
    "nss75_computer",  # R2 H5a       -- NSS 75th ability to operate a computer (pre-window, n=22)
    "nss75_internet",  # R2 H5a       -- NSS 75th ability to use internet (pre-window, n=22)
    "mobile_w",        # R2 H5a       -- NFHS-5 women's own mobile phone
    "income_s",        # PRIMARY H5b  -- state-mean ln NSDP per capita
    "ln_mpce",         # R2 H5b       -- HCES 2022-23 MPCE, a household CONSUMPTION measure
    "mobile_w_2016",   # R4 H5a       -- NFHS-4 women's own mobile phone, STRICTLY PRE-WINDOW
    "mobile_w_change", # R4 H5a       -- change in mobile ownership 2015-16 -> 2019-21
    # ---- placebos (R1): general human capital and urbanisation, NOT digital skill
    "schooling_w",     # PLACEBO -- NFHS-5 women with 10+ years schooling  [SAME INSTRUMENT]
    "schooling_m",     # PLACEBO -- NFHS-5 men with 10+ years schooling    [SAME INSTRUMENT]
    "everschool_w",    # PLACEBO -- NFHS-5 female 6+ ever attended school  [SAME INSTRUMENT]
    "lit2011",         # PLACEBO -- Census 2011 general literacy
    "urban_share_nfhs",  # PLACEBO -- derived urban share
    "schooling_w_2016",  # PLACEBO -- NFHS-4 schooling, the pre-window counterpart of schooling_w
    "bankacct_w_2016",   # PLACEBO -- NFHS-4 women's own bank account, i.e. BASELINE INCLUSION.
                         # The sharpest confound available: if states that were already more
                         # financially included convert UPI differently, that is not a skill
                         # effect. Not in the original plan; added because it is the one placebo
                         # that is about the outcome rather than about development.
]

UPI = "pp_users_per_adult"

DVS = ["norm_credit_accts_per_adult", "norm_deposits_per_capita", "norm_credit_per_capita",
       "norm_deposit_accts_per_adult", "Access", "Usage", "AUG"]


def main() -> int:
    print("\n" + "=" * 96)
    print("  H5 STEP 2 -- building output/panel_h5.csv")
    print("=" * 96 + "\n")

    panel = pd.read_csv(H1_OUT / "panel_digital.csv")
    mods = pd.read_csv(DATA / "09_diglit.csv")
    print(f"  H1 digital panel : {panel.shape[0]} rows x {panel.shape[1]} cols, "
          f"{panel.state_key.nunique()} states, fy_end {panel.fy_end.min()}-{panel.fy_end.max()}")
    print(f"  moderators       : {mods.shape[0]} states x {mods.shape[1] - 1} columns")

    # ---- income moderator: state mean of the time-varying control (rule 4)
    income_s = panel.groupby("state_key")["ln_nsdp_pc"].mean().rename("income_s")
    mods = mods.merge(income_s, left_on="state_key", right_index=True, how="left")

    # ---- merge, asserting nothing is lost
    before = panel.shape
    d = panel.merge(mods, on="state_key", how="left", validate="many_to_one")
    assert d.shape[0] == before[0], f"merge changed row count {before[0]} -> {d.shape[0]}"
    for c in panel.columns:
        assert d[c].equals(panel[c]), f"FATAL: merge altered carried-over column {c}"
    print(f"  merged           : {d.shape[0]} rows, all {len(panel.columns)} H1 columns byte-identical")

    unmatched = d.loc[d["diglit_w"].isna(), "state_key"].unique()
    if len(unmatched):
        sys.exit(f"FATAL: states with no moderator: {list(unmatched)}")

    # ---- z-score the moderators across states (rule 3), using one value per state not per row
    state_level = d.drop_duplicates("state_key").set_index("state_key")
    zstats = {}
    for m in MODERATORS:
        s = state_level[m]
        mu, sd = s.mean(), s.std(ddof=1)
        if not np.isfinite(sd) or sd == 0:
            sys.exit(f"FATAL: moderator {m} has zero/undefined spread")
        d[f"z_{m}"] = (d[m] - mu) / sd
        zstats[m] = (mu, sd, int(s.notna().sum()))

    # ---- centre UPI (rule 2)
    upi_mean = d[UPI].mean()
    d["c_upi"] = d[UPI] - upi_mean
    print(f"  centred {UPI} at its panel mean {upi_mean:.5f}")

    # ---- interactions
    for m in MODERATORS:
        d[f"upi_x_{m}"] = d["c_upi"] * d[f"z_{m}"]
    print(f"  built {len(MODERATORS)} UPI x moderator interaction terms")

    # ---- terciles, for the threshold specification. Built for BOTH moderators so the
    # skills and resources channels get symmetric treatment (they did not, in the first pass).
    for base, prefix in [("diglit_w", ""), ("income_s", "inc")]:
        terc = pd.qcut(state_level[base], 3, labels=["T1_low", "T2_mid", "T3_high"])
        col = "diglit_tercile" if prefix == "" else "income_tercile"
        d[col] = d["state_key"].map(terc).astype(str)
        for t in ["T2_mid", "T3_high"]:
            d[f"upi_x_{prefix}{t}"] = d["c_upi"] * (d[col] == t).astype(float)

    d.to_csv(OUT / "panel_h5.csv", index=False)
    print(f"\n  wrote {OUT / 'panel_h5.csv'}  ({d.shape[0]} rows x {d.shape[1]} cols)\n")

    # ---- report what was built
    print("  MODERATOR Z-SCORING (one value per state; mean and SD across states)")
    print(f"    {'moderator':20s} {'n':>3s} {'mean':>9s} {'sd':>9s}")
    for m in MODERATORS:
        mu, sd, n = zstats[m]
        print(f"    {m:20s} {n:3d} {mu:9.3f} {sd:9.3f}")

    # Read the tercile columns back off the panel rather than reusing the loop variable:
    # the loop leaves `terc` holding whichever moderator was cut last, which silently
    # mislabelled this table on the first run.
    assigned = d.drop_duplicates("state_key").set_index("state_key")
    for base, col, lab in [("diglit_w", "diglit_tercile", "DIGITAL-LITERACY TERCILES (diglit_w, %)"),
                           ("income_s", "income_tercile", "INCOME TERCILES (state-mean ln NSDP pc)")]:
        print(f"\n  {lab}")
        for t in ["T1_low", "T2_mid", "T3_high"]:
            members = sorted(assigned.index[assigned[col] == t])
            rng = state_level.loc[members, base]
            print(f"    {t:8s} [{rng.min():6.2f}-{rng.max():6.2f}]  n={len(members):2d}  "
                  f"{', '.join(m.title() for m in members)}")

    missing_dv = [c for c in DVS if c not in d.columns]
    if missing_dv:
        sys.exit(f"FATAL: dependent variables missing from panel: {missing_dv}")
    print(f"\n  all {len(DVS)} dependent variables present and unmodified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
