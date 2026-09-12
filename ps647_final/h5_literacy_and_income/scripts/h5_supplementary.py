#!/usr/bin/env python3
"""
H5 Step 10 -- two checks owed and not previously run.

S1  PAIRWISE DECOMPOSITION OF b5.
    The stacked test pools two intensive outcomes against one extensive outcome, so b5 is an
    average. R9 showed the extensive side is not homogeneous (the skills interaction is +0.124 on
    deposit accounts and -0.061 on credit accounts). The same question has to be asked of the
    INTENSIVE side: is b5 carried by deposits, by credit, or by both? Run the sharp test once per
    outcome pair, 330 rows each.

    This is the diagnostic R9 should have prompted and did not.

S2  THE SUPPLEMENTARY THE EXECUTION PLAN PROMISED (section 6.5) AND THIS PROJECT DID NOT RUN.
    Digital-channel intensity: does digital literacy steepen the slope of PhonePe transactions on
    PhonePe registrations?

        ln(1 + pp_txns_per_capita)_it = b1*UPI + b3*(UPI x DigLit) + ... + mu_i + lambda_t

    ENTANGLEMENT, STATED UP FRONT: a PhonePe transaction requires a PhonePe registration, so the
    dependent variable cannot rise without the regressor rising. b1 is uninterpretable and is not
    reported as a finding. Only b3 is read -- whether the conversion of registrations into
    transactions is steeper where digital literacy is higher. The mechanical link does not
    obviously generate a DIFFERENTIAL by literacy, which is why b3 survives where b1 does not.
    This remains a supplementary, not a headline.

Writes output/table20_h5_supplementary.csv
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
SHARED = ROOT_DIR.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))
from h5_lib import CONTROLS, fit, stars, wild_cluster_bootstrap  # noqa: E402
import estimate_h5_stacked as st  # noqa: E402
from estimate_h5_stacked import build_stack, lsdv, bootstrap_stacked  # noqa: E402

warnings.filterwarnings("ignore")
OUT = ROOT_DIR / "output"

XS = ["c_upi", "upi_x_int", "upi_x_skill", "upi_x_skill_x_int",
      "upi_x_income", "upi_x_income_x_int"] + CONTROLS
FE_B = [["state_key", "outcome"], ["fy_end", "outcome"]]

EXTENSIVE = ("norm_credit_accts_per_adult", "credit accounts / adult", 0)
INTENSIVE = [("norm_deposits_per_capita", "deposits Rs / capita", 1),
             ("norm_credit_per_capita", "credit Rs / capita", 1)]
ENTANGLED = ("norm_deposit_accts_per_adult", "deposit accounts / adult", 0)


def sharp(d, outcomes, label, rows, note=""):
    saved = st.OUTCOMES
    st.OUTCOMES = outcomes
    try:
        s = build_stack(d)
        beta, se, t, p, n, G, *_ = lsdv(s, XS, FE_B, "state_key")
        pb = bootstrap_stacked(s, XS, FE_B, "state_key", "upi_x_skill_x_int", B=9999)
        pb6 = bootstrap_stacked(s, XS, FE_B, "state_key", "upi_x_income_x_int", B=9999)
    finally:
        st.OUTCOMES = saved
    print(f"  {label:46s} {beta['upi_x_skill_x_int']:9.4f} {se['upi_x_skill_x_int']:8.4f} "
          f"{pb:9.4f} {beta['upi_x_income_x_int']:9.4f} {pb6:9.4f} {n:6d} {stars(pb)} {note}")
    rows.append({"check": "S1 pairwise", "pair": label, "b5": beta["upi_x_skill_x_int"],
                 "se_b5": se["upi_x_skill_x_int"], "p_b5": pb,
                 "b6": beta["upi_x_income_x_int"], "p_b6": pb6, "N": n, "note": note})


def main() -> int:
    d = pd.read_csv(OUT / "panel_h5.csv")
    rows = []

    print("\n" + "=" * 112)
    print("  S1 -- PAIRWISE DECOMPOSITION OF b5")
    print("  Which intensive outcome carries the headline? Each row is one extensive/intensive pair.")
    print("=" * 112)
    print(f"\n  {'outcome pair':46s} {'b5':>9s} {'se':>8s} {'p boot':>9s} "
          f"{'b6':>9s} {'p boot':>9s} {'N':>6s}")
    print("  " + "-" * 104)

    sharp(d, [EXTENSIVE] + INTENSIVE, "POOLED (table17 baseline)", rows, "<- headline")
    for col, lab, _ in INTENSIVE:
        sharp(d, [EXTENSIVE, (col, lab, 1)], f"credit accts  vs  {lab}", rows)
    # and the same pairs against the entangled extensive indicator, to locate the R9 reversal
    for col, lab, _ in INTENSIVE:
        sharp(d, [ENTANGLED, (col, lab, 1)], f"deposit accts vs  {lab}", rows, "(entangled, D17)")

    print("\n  Reading: if b5 is similar across both credit-accounts pairs, the headline is not")
    print("  an artefact of one outcome. The deposit-accounts rows locate where R9 reverses.")

    # ------------------------------------------------------------------ S2
    print("\n" + "=" * 112)
    print("  S2 -- DIGITAL-CHANNEL INTENSITY (execution plan section 6.5, not previously run)")
    print("  DV = ln(1 + PhonePe transactions per capita). ENTANGLED with the regressor by")
    print("  construction: b1 is NOT a finding. Only b3 is read.")
    print("=" * 112)

    d = d.copy()
    d["ln1p_txns_pc"] = np.log1p(d["pp_txns_per_capita"])
    d["ln1p_value_pc"] = np.log1p(d["pp_value_per_capita"])

    print(f"\n  {'DV':30s} {'moderator':30s} {'b3':>9s} {'se':>8s} {'p boot':>9s}")
    print("  " + "-" * 92)
    for dv, dvlab in [("ln1p_txns_pc", "ln(1+ txns per capita)"),
                      ("ln1p_value_pc", "ln(1+ value per capita)")]:
        for mod, modlab, role in [("diglit_w", "NFHS-5 women internet", "TREATMENT"),
                                  ("schooling_w", "NFHS-5 women 10+ yrs school", "PLACEBO"),
                                  ("everschool_w", "NFHS-5 ever attended school", "PLACEBO"),
                                  ("lit2011", "Census 2011 literacy", "PLACEBO"),
                                  ("urban_share_nfhs", "derived urban share", "PLACEBO")]:
            v = f"upi_x_{mod}"
            X = ["c_upi", v, "upi_x_income_s"] + CONTROLS
            r = fit(d, dv, X)
            pb = wild_cluster_bootstrap(d, dv, X, v, B=9999)["p_wcb"]
            mark = "  <-- FIRES" if (pb < 0.05 and role == "PLACEBO") else ""
            print(f"  {dvlab:30s} {modlab + ' [' + role + ']':30s} {r.params[v]:9.4f} "
                  f"{r.std_errors[v]:8.4f} {pb:9.4f} {stars(pb)}{mark}")
            rows.append({"check": "S2 channel intensity", "pair": dv, "b5": r.params[v],
                         "se_b5": r.std_errors[v], "p_b5": pb, "b6": np.nan, "p_b6": np.nan,
                         "N": int(r.nobs), "note": f"{modlab} [{role}]"})

    pd.DataFrame(rows).to_csv(OUT / "table20_h5_supplementary.csv", index=False)
    print(f"\n  wrote {OUT / 'table20_h5_supplementary.csv'}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
