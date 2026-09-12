#!/usr/bin/env python3
"""
H5 Step 3 -- the pre-committed gates. RUN BEFORE ANY INTERACTION IS ESTIMATED.

Thresholds were fixed in writing in H5_execution_plan.md section 5 before the moderator data
existed. They are reproduced as constants below and are not to be edited after seeing output.

Gate 1  Is the moderator distinguishable from the regressor?
        corr(moderator, state-mean UPI adoption) across the 33 states.
        PASS < 0.70 | WEAK 0.70-0.85 | FAIL > 0.85 (-> residualise, R3)

Gate 2  Does the moderator have usable spread?
        IQR >= 0.5 SD, else leave-one-out (R5) becomes mandatory rather than optional.

Gate 3  Is the interaction identified? (build check, not a substantive gate)
        Within-state share of variation in UPI x moderator, same xtsum decomposition as F4/F11.
        Should sit near UPI's own 67.1%.

Also reports the moderator correlation matrix and interaction-term VIFs, because the
skills-vs-resources horse race in section 6.2 is only interpretable if the two moderators are
separable from each other, not merely from UPI.

Writes output/table14_h5_gates.csv
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
OUT = ROOT_DIR / "output"

GATE1_PASS, GATE1_FAIL = 0.70, 0.85
GATE2_IQR_SD_RATIO = 0.50
UPI = "pp_users_per_adult"

PRIMARY = ["diglit_w", "income_s"]
SECONDARY = ["diglit_m", "diglit_both", "diglit_gap", "nss75_computer", "nss75_internet", "mobile_w"]
PLACEBO = ["schooling_w", "schooling_m", "everschool_w", "lit2011", "urban_share_nfhs"]


def gate1(state_level: pd.DataFrame, m: str) -> tuple[float, str]:
    sub = state_level[[m, "upi_mean"]].dropna()
    r = sub[m].corr(sub["upi_mean"])
    v = "PASS" if abs(r) < GATE1_PASS else ("WEAK" if abs(r) <= GATE1_FAIL else "FAIL")
    return r, v


def gate2(state_level: pd.DataFrame, m: str) -> tuple[float, float, str]:
    s = state_level[m].dropna()
    iqr = s.quantile(.75) - s.quantile(.25)
    sd = s.std(ddof=1)
    ratio = iqr / sd
    return ratio, sd, ("PASS" if ratio >= GATE2_IQR_SD_RATIO else "THIN")


def within_share(d: pd.DataFrame, col: str) -> float:
    """within_sd / overall_sd, the Stata xtsum convention used by scripts/within_variation.py.
    Reproduced exactly so these numbers are comparable to F4 and F11."""
    sub = d[["state_key", col]].dropna()
    x = sub[col]
    grand = x.mean()
    mi = sub.groupby("state_key")[col].transform("mean")
    within = (x - mi + grand).std(ddof=1)
    return within / x.std(ddof=1) * 100


def vif(X: pd.DataFrame) -> pd.Series:
    """VIF via R^2 of each column on the others (with intercept)."""
    out = {}
    Xm = X.dropna()
    for c in Xm.columns:
        y = Xm[c].values
        Z = np.column_stack([np.ones(len(Xm)), Xm.drop(columns=c).values])
        beta, *_ = np.linalg.lstsq(Z, y, rcond=None)
        resid = y - Z @ beta
        ss_tot = ((y - y.mean()) ** 2).sum()
        r2 = 1 - (resid ** 2).sum() / ss_tot if ss_tot > 0 else 0.0
        out[c] = np.inf if r2 >= 1 else 1 / (1 - r2)
    return pd.Series(out)


def main() -> int:
    d = pd.read_csv(OUT / "panel_h5.csv")
    state_level = d.drop_duplicates("state_key").set_index("state_key").copy()
    state_level["upi_mean"] = d.groupby("state_key")[UPI].mean()

    print("\n" + "=" * 100)
    print("  H5 STEP 3 -- PRE-COMMITTED GATES   (thresholds fixed before the data existed)")
    print(f"  Gate 1: PASS |r| < {GATE1_PASS} | WEAK <= {GATE1_FAIL} | FAIL above")
    print(f"  Gate 2: PASS IQR/SD >= {GATE2_IQR_SD_RATIO}")
    print("=" * 100 + "\n")

    rows = []
    print(f"  {'moderator':20s} {'role':10s} {'n':>3s} {'G1 corr':>9s} {'G1':>5s} "
          f"{'G2 IQR/SD':>10s} {'G2':>5s} {'G3 within%':>11s}")
    print("  " + "-" * 80)
    for m, role in ([(x, "PRIMARY") for x in PRIMARY]
                    + [(x, "secondary") for x in SECONDARY]
                    + [(x, "placebo") for x in PLACEBO]):
        r, v1 = gate1(state_level, m)
        ratio, sd, v2 = gate2(state_level, m)
        w = within_share(d, f"upi_x_{m}")
        n = int(state_level[m].notna().sum())
        print(f"  {m:20s} {role:10s} {n:3d} {r:9.3f} {v1:>5s} {ratio:10.2f} {v2:>5s} {w:10.1f}%")
        rows.append({"moderator": m, "role": role, "n_states": n,
                     "gate1_corr_with_upi": round(r, 4), "gate1_verdict": v1,
                     "gate2_iqr_over_sd": round(ratio, 3), "gate2_sd": round(sd, 3),
                     "gate2_verdict": v2, "gate3_within_share_pct": round(w, 2)})

    print(f"\n  reference -- within-state share for UPI itself: {within_share(d, UPI):.1f}% "
          f"(F11 reported 67.1%)")

    # ---------------- moderator correlation matrix: is the horse race separable?
    print("\n  MODERATOR CORRELATION MATRIX (across states) -- the horse race is only")
    print("  interpretable if skills and resources are separable from EACH OTHER, not just from UPI")
    key = ["diglit_w", "income_s", "schooling_w", "lit2011", "urban_share_nfhs", "mobile_w"]
    cm = state_level[key].corr()
    print("\n    " + " " * 18 + "".join(f"{c[:9]:>11s}" for c in key))
    for i in key:
        print(f"    {i:18s}" + "".join(f"{cm.loc[i, j]:11.3f}" for j in key))

    r_skill_income = cm.loc["diglit_w", "income_s"]
    print(f"\n    corr(digital literacy, income) = {r_skill_income:.3f}", end="  ")
    print("-- separable, horse race is meaningful" if abs(r_skill_income) < GATE1_FAIL
          else "-- NOT separable, the horse race cannot be read")

    # ---------------- VIFs on the estimated interaction terms
    print("\n  VIF ON THE PREFERRED SPECIFICATION'S REGRESSORS (section 6.1, column 4)")
    spec = ["c_upi", "upi_x_diglit_w", "upi_x_income_s",
            "branches_per_lakh_adults", "atms_per_lakh_adults", "ln_nsdp_pc"]
    v = vif(d[spec])
    for k, val in v.items():
        flag = "" if val < 5 else ("  <-- elevated" if val < 10 else "  <-- SEVERE")
        print(f"    {k:28s} {val:7.2f}{flag}")
        rows.append({"moderator": f"VIF:{k}", "role": "vif", "n_states": len(d),
                     "gate1_corr_with_upi": round(val, 3), "gate1_verdict": "",
                     "gate2_iqr_over_sd": np.nan, "gate2_sd": np.nan,
                     "gate2_verdict": "", "gate3_within_share_pct": np.nan})

    pd.DataFrame(rows).to_csv(OUT / "table14_h5_gates.csv", index=False)
    print(f"\n  wrote {OUT / 'table14_h5_gates.csv'}")

    # ---------------- overall verdict
    v_dig, _ = gate1(state_level, "diglit_w")[1], None
    v_inc = gate1(state_level, "income_s")[1]
    print("\n" + "=" * 100)
    print(f"  GATE VERDICT -- H5a (diglit_w): {v_dig}   |   H5b (income_s): {v_inc}")
    if v_dig == "FAIL" or v_inc == "FAIL":
        print("  -> At least one primary moderator FAILS. R3 residualisation is now MANDATORY")
        print("     before the raw interaction can be interpreted.")
    else:
        print("  -> Both primary moderators are separable from UPI. Proceed to estimation as")
        print("     specified, carrying the correlations alongside every coefficient.")
    print("=" * 100 + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
