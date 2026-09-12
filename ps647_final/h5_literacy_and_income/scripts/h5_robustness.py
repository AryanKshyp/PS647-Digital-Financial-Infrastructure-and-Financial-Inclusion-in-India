#!/usr/bin/env python3
"""
H5 Step 8 -- robustness (execution plan section 8).

Everything here targets the HEADLINE coefficient b5 -- the triple interaction
UPI x DigLit x Intensive from the stacked sharp test, scheme (B) -- plus the unstacked b3 where
relevant. R6 (wild cluster bootstrap) is not repeated here: it is already applied to every
coefficient in every table.

  R3  Residualised moderator. Regress DigLit on state-mean UPI adoption, interact the residual.
      Removes any mechanical collinearity; b5 then reads as "returns to infrastructure differ
      more between margins in states with more digital skill than their adoption level predicts".
  R5  Leave-one-state-out. 33 refits. The check F14 ran for the H1 main effect, applied to b5.
  R7  D7 defect cells. Drop Delhi 2023 and Chandigarh 2023 (RBI source errors in the savings-
      account column). Affects deposit-based outcomes only; credit accounts are unaffected (D17).
  R8  Drop small UTs (Delhi, Chandigarh, Puducherry, Andaman & Nicobar). They are outliers on
      both moderators and on every per-capita banking ratio.
  R9  Alternative Intensive coding. Move the entangled deposit-accounts indicator in as a second
      EXTENSIVE outcome, so the extensive margin is not carried by credit accounts alone.
  R10 Drop the top and bottom moderator states (Sikkim, Chandigarh, Goa / Bihar, Andhra, Tripura)
      -- is the result only the poles of the distribution?

Writes output/table19_h5_robustness.csv
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))
from h5_lib import CONTROLS, fit, stars, wild_cluster_bootstrap  # noqa: E402
from estimate_h5_stacked import build_stack, lsdv, bootstrap_stacked, OUTCOMES  # noqa: E402

warnings.filterwarnings("ignore")
OUT = ROOT_DIR / "output"

XS = ["c_upi", "upi_x_int", "upi_x_skill", "upi_x_skill_x_int",
      "upi_x_income", "upi_x_income_x_int"] + CONTROLS
FE_B = [["state_key", "outcome"], ["fy_end", "outcome"]]
KEY = "upi_x_skill_x_int"


def b5_of(d: pd.DataFrame, boot: bool = True, seed: int = 647) -> dict:
    s = build_stack(d)
    beta, se, t, p, n, G, *_ = lsdv(s, XS, FE_B, "state_key")
    out = {"coef": beta[KEY], "se": se[KEY], "p_clustered": p[KEY], "N": n, "clusters": G,
           "b3": beta["upi_x_skill"], "b2": beta["upi_x_int"], "b6": beta["upi_x_income_x_int"]}
    out["p_wcb"] = bootstrap_stacked(s, XS, FE_B, "state_key", KEY, B=9999, seed=seed) if boot else np.nan
    return out


def show(tag: str, r: dict, base: dict, rows: list, note: str = "") -> None:
    delta = (r["coef"] - base["coef"]) / abs(base["coef"]) * 100 if base["coef"] else np.nan
    print(f"  {tag:44s} {r['coef']:9.4f} {r['se']:8.4f} {r['p_wcb']:9.4f} "
          f"{r['N']:6d} {r['clusters']:5d} {delta:+8.1f}% {stars(r['p_wcb'])} {note}")
    rows.append({"check": tag, "coef_b5": r["coef"], "se": r["se"], "p_wild_bootstrap": r["p_wcb"],
                 "pct_change_vs_baseline": round(delta, 2), "N": r["N"], "clusters": r["clusters"],
                 "b3": r["b3"], "b2": r["b2"], "b6": r["b6"], "note": note})


def main() -> int:
    d = pd.read_csv(OUT / "panel_h5.csv")
    rows = []
    print("\n" + "=" * 112)
    print("  H5 STEP 8 -- ROBUSTNESS OF THE HEADLINE COEFFICIENT")
    print("  b5 = UPI x digital literacy x Intensive, stacked sharp test, scheme (B)")
    print("=" * 112)
    print(f"\n  {'specification':44s} {'b5':>9s} {'se':>8s} {'p boot':>9s} "
          f"{'N':>6s} {'clus':>5s} {'change':>9s}")
    print("  " + "-" * 104)

    base = b5_of(d)
    show("BASELINE (table17 scheme B)", base, base, rows)

    # ---------------------------------------------------------------- R3 residualised moderator
    sl = d.drop_duplicates("state_key").set_index("state_key")
    upi_mean = d.groupby("state_key")["pp_users_per_adult"].mean()
    x = np.column_stack([np.ones(len(sl)), upi_mean.loc[sl.index].to_numpy()])
    yv = sl["diglit_w"].to_numpy()
    bb, *_ = np.linalg.lstsq(x, yv, rcond=None)
    resid = yv - x @ bb
    res_z = pd.Series((resid - resid.mean()) / resid.std(ddof=1), index=sl.index)
    d3 = d.copy()
    d3["z_diglit_w"] = d3["state_key"].map(res_z)
    show("R3 residualised on state-mean UPI", b5_of(d3), base, rows,
         f"(R2 of DigLit on UPI = {1 - (resid**2).sum() / ((yv - yv.mean())**2).sum():.3f})")

    # ---------------------------------------------------------------- R7 D7 defect cells
    d7 = d[~(((d.state_key == "DELHI") & (d.fy_end == 2023))
             | ((d.state_key == "CHANDIGARH") & (d.fy_end == 2023)))]
    show("R7 drop Delhi 2023 + Chandigarh 2023", b5_of(d7), base, rows, "(D7 source defects)")

    # ---------------------------------------------------------------- R8 drop small UTs
    uts = ["DELHI", "CHANDIGARH", "PUDUCHERRY", "ANDAMAN AND NICOBAR ISLANDS"]
    show("R8 drop 4 small UTs", b5_of(d[~d.state_key.isin(uts)]), base, rows, f"({', '.join(u.title() for u in uts[:3])}...)")

    # ---------------------------------------------------------------- R10 drop moderator poles
    sl_sorted = sl["diglit_w"].sort_values()
    poles = list(sl_sorted.head(3).index) + list(sl_sorted.tail(3).index)
    show("R10 drop 3 lowest + 3 highest DigLit states", b5_of(d[~d.state_key.isin(poles)]), base,
         rows, f"({', '.join(p.title()[:12] for p in poles)})")

    # ---------------------------------------------------------------- R9 alternative coding
    import estimate_h5_stacked as st
    saved = st.OUTCOMES
    st.OUTCOMES = [("norm_credit_accts_per_adult", "credit accounts / adult", 0),
                   ("norm_deposit_accts_per_adult", "deposit accounts / adult", 0),
                   ("norm_deposits_per_capita", "deposits Rs / capita", 1),
                   ("norm_credit_per_capita", "credit Rs / capita", 1)]
    show("R9 add deposit accounts to extensive side", b5_of(d), base, rows,
         "(4 outcomes, 2 per margin)")
    st.OUTCOMES = saved

    # ---------------------------------------------------------------- R5 leave-one-state-out
    print("\n" + "=" * 112)
    print("  R5 LEAVE-ONE-STATE-OUT -- 33 refits, the check F14 ran for the H1 main effect")
    print("=" * 112)
    loo = []
    for st_name in sorted(d.state_key.unique()):
        r = b5_of(d[d.state_key != st_name], boot=False)
        loo.append({"dropped": st_name, "b5": r["coef"], "se": r["se"], "p": r["p_clustered"]})
    loo = pd.DataFrame(loo).sort_values("b5")
    flips = int((np.sign(loo.b5) != np.sign(base["coef"])).sum())
    lost = int((loo.p >= 0.05).sum())
    print(f"\n    full sample b5      : {base['coef']:+.4f}  (p_boot {base['p_wcb']:.4f})")
    print(f"    range across refits : {loo.b5.min():+.4f} to {loo.b5.max():+.4f}")
    print(f"    worst clustered p   : {loo.p.max():.4f}")
    print(f"    sign flips          : {flips}")
    print(f"    refits losing 5%    : {lost}")
    print(f"\n    most influential states (largest move in b5):")
    infl = loo.assign(move=(loo.b5 - base["coef"]).abs()).sort_values("move", ascending=False)
    for _, r in infl.head(5).iterrows():
        print(f"      drop {r['dropped'].title():30s} b5 -> {r['b5']:+.4f}  "
              f"({r['b5'] - base['coef']:+.4f})  p={r['p']:.4f}")
    loo.to_csv(OUT / "table19b_h5_leave_one_out.csv", index=False)
    rows.append({"check": "R5 leave-one-out: min", "coef_b5": loo.b5.min(), "se": np.nan,
                 "p_wild_bootstrap": np.nan, "pct_change_vs_baseline": np.nan,
                 "N": np.nan, "clusters": 32, "b3": np.nan, "b2": np.nan, "b6": np.nan,
                 "note": f"{flips} sign flips, {lost} refits above p=0.05"})
    rows.append({"check": "R5 leave-one-out: max", "coef_b5": loo.b5.max(), "se": np.nan,
                 "p_wild_bootstrap": np.nan, "pct_change_vs_baseline": np.nan,
                 "N": np.nan, "clusters": 32, "b3": np.nan, "b2": np.nan, "b6": np.nan,
                 "note": f"worst p {loo.p.max():.4f}"})

    pd.DataFrame(rows).to_csv(OUT / "table19_h5_robustness.csv", index=False)
    print(f"\n  wrote {OUT / 'table19_h5_robustness.csv'}")
    print(f"  wrote {OUT / 'table19b_h5_leave_one_out.csv'}\n")

    # ---------------------------------------------------------------- verdict
    surv = [r for r in rows if r["check"] != "BASELINE (table17 scheme B)"
            and not np.isnan(r.get("p_wild_bootstrap", np.nan))]
    n_sig = sum(1 for r in surv if r["p_wild_bootstrap"] < 0.05)
    same_sign = sum(1 for r in surv if np.sign(r["coef_b5"]) == np.sign(base["coef"]))
    print("=" * 112)
    print(f"  ROBUSTNESS VERDICT: {n_sig}/{len(surv)} perturbations keep b5 significant at 5%; "
          f"{same_sign}/{len(surv)} keep the sign.")
    print(f"  Leave-one-out: {flips} sign flips, {lost}/33 refits lose 5% significance.")
    print("=" * 112 + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
