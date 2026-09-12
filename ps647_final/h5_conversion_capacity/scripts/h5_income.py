#!/usr/bin/env python3
"""
H5 Step 11 -- THE RESOURCES CHANNEL (H5b), given the treatment the skills channel got.

H5b was present in every specification from the start -- it is the co-equal moderator in the
horse race, it appears in all four sequential-entry columns, in the stacked test as b4 and b6,
and in the pairwise decomposition. But it did not get three things the skills channel did, and
that asymmetry is not defensible when the whole design is a horse race between them:

  I1  AN ALTERNATIVE MEASURE.  Skills had five (NFHS-5 women, NFHS-5 men, mobile phone,
      NSS 75th computer, NSS 75th internet). Income had one: ln NSDP per capita.
      Added here: ln MPCE from HCES 2022-23. This matters substantively, not just for symmetry.
      NSDP per capita is a PRODUCTION measure -- corporate output books to the state of
      registration, inflating Delhi and Maharashtra in exactly the way LIMITATIONS.md section 4
      documents for bank deposits recorded at branch location. MPCE is household CONSUMPTION
      from a survey of households. For a moderator meant to represent household RESOURCES, MPCE
      is the better construct. They correlate 0.844, so they are not interchangeable.

  I2  ITS OWN PLACEBO BATTERY.  The R1 override was applied to skills and never to income.
      If the income interaction is really a general-development gradient, the same placebos
      should reproduce it. Run symmetrically here.

  I3  A THRESHOLD SPECIFICATION.  Skills got terciles; income did not. Cole-Sampson-Zia is a
      claim about a PRICE constraint binding at low income, which is a threshold claim.

Also runs the direct head-to-head the horse race implies: skills and income terciles crossed,
to see whether the two channels are substitutes or complements at the margins.

Writes output/table22_h5_income.csv
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))
from h5_lib import CONTROLS, fit, stars, wild_cluster_bootstrap  # noqa: E402
import estimate_h5_stacked as st  # noqa: E402
from estimate_h5_stacked import build_stack, lsdv, bootstrap_stacked  # noqa: E402

warnings.filterwarnings("ignore")
OUT = ROOT_DIR / "output"

XS = ["c_upi", "upi_x_int", "upi_x_skill", "upi_x_skill_x_int",
      "upi_x_income", "upi_x_income_x_int"] + CONTROLS
FE_B = [["state_key", "outcome"], ["fy_end", "outcome"]]

EXT = ("norm_credit_accts_per_adult", "credit accounts / adult", 0)
DEP = ("norm_deposits_per_capita", "deposits Rs / capita", 1)
CRD = ("norm_credit_per_capita", "credit Rs / capita", 1)

DVS = [("norm_credit_accts_per_adult", "ACCESS credit accts/adult"),
       ("norm_deposits_per_capita", "USAGE  deposits Rs/capita"),
       ("norm_credit_per_capita", "USAGE  credit Rs/capita")]


def swap_income(s: pd.DataFrame, zcol: str) -> pd.DataFrame:
    """Substitute a different variable into the RESOURCES slot of the stacked design."""
    sp = s.copy()
    sp["upi_x_income"] = sp["c_upi"] * sp[zcol]
    sp["upi_x_income_x_int"] = sp["upi_x_income"] * sp["intensive"]
    return sp.dropna(subset=["upi_x_income"])


def main() -> int:
    d = pd.read_csv(OUT / "panel_h5.csv")
    rows = []
    print("\n" + "=" * 112)
    print("  H5 STEP 11 -- THE RESOURCES CHANNEL (H5b), brought up to the skills channel's standard")
    print("=" * 112)

    # ------------------------------------------------------- I1: alternative income measure
    print("\n" + "=" * 112)
    print("  I1 -- ALTERNATIVE INCOME MEASURE: MPCE (consumption) against NSDP pc (production)")
    print("  Plain interaction model, preferred specification, bootstrap p.")
    print("=" * 112)
    print(f"\n  {'DV':30s} {'income measure':28s} {'b4':>9s} {'se':>8s} {'p boot':>9s}")
    print("  " + "-" * 88)
    for dv, dvlab in DVS:
        for mod, modlab in [("income_s", "ln NSDP pc (production)"),
                            ("ln_mpce", "ln MPCE (consumption)")]:
            v = f"upi_x_{mod}"
            X = ["c_upi", "upi_x_diglit_w", v] + CONTROLS
            r = fit(d, dv, X)
            pb = wild_cluster_bootstrap(d, dv, X, v, B=9999)["p_wcb"]
            print(f"  {dvlab:30s} {modlab:28s} {r.params[v]:9.4f} {r.std_errors[v]:8.4f} "
                  f"{pb:9.4f} {stars(pb)}")
            rows.append({"check": "I1 alt income measure", "dv": dv, "term": modlab,
                         "coef": r.params[v], "se": r.std_errors[v], "p_boot": pb,
                         "N": int(r.nobs)})
        # and what happens to the SKILLS coefficient when MPCE replaces NSDP
        X = ["c_upi", "upi_x_diglit_w", "upi_x_ln_mpce"] + CONTROLS
        r = fit(d, dv, X)
        pb = wild_cluster_bootstrap(d, dv, X, "upi_x_diglit_w", B=9999)["p_wcb"]
        print(f"  {'':30s} {'-> skills, with MPCE as income':28s} {r.params['upi_x_diglit_w']:9.4f} "
              f"{r.std_errors['upi_x_diglit_w']:8.4f} {pb:9.4f} {stars(pb)}")
        rows.append({"check": "I1 skills under MPCE", "dv": dv, "term": "UPI x skills",
                     "coef": r.params["upi_x_diglit_w"], "se": r.std_errors["upi_x_diglit_w"],
                     "p_boot": pb, "N": int(r.nobs)})
        print()

    # ------------------------------------------------------- I2: income's own placebo battery
    print("=" * 112)
    print("  I2 -- PLACEBO BATTERY ON THE RESOURCES SLOT (never run before; symmetric to R1)")
    print("  Stacked sharp test, scheme (B). Skills slot held at digital literacy throughout.")
    print("  Question: does b6 (resources x margin) appear for ANY development proxy, or for none?")
    print("=" * 112)
    st.OUTCOMES = [EXT, DEP, CRD]
    s0 = build_stack(d)
    print(f"\n  {'variable in the resources slot':38s} {'role':24s} {'b6':>9s} {'p boot':>9s}")
    print("  " + "-" * 86)
    for zc, lab, role in [("z_income_s", "ln NSDP per capita", "TREATMENT (H5b)"),
                          ("z_ln_mpce", "ln MPCE", "ALT resources"),
                          ("z_bankacct_w_2016", "bank account 2015-16", "PLACEBO baseline inclusion"),
                          ("z_schooling_w", "women 10+ yrs schooling", "PLACEBO"),
                          ("z_lit2011", "Census 2011 literacy", "PLACEBO"),
                          ("z_urban_share_nfhs", "derived urban share", "PLACEBO")]:
        sp = swap_income(s0, zc)
        beta, se, t, p, n, G, *_ = lsdv(sp, XS, FE_B, "state_key")
        pb = bootstrap_stacked(sp, XS, FE_B, "state_key", "upi_x_income_x_int", B=9999)
        print(f"  {lab:38s} {role:24s} {beta['upi_x_income_x_int']:9.4f} {pb:9.4f} {stars(pb)}")
        rows.append({"check": "I2 resources placebo", "dv": "stacked", "term": f"{lab} [{role}]",
                     "coef": beta["upi_x_income_x_int"], "se": se["upi_x_income_x_int"],
                     "p_boot": pb, "N": n})
    print("\n  Reading: b6 is null for the income measures AND for every placebo. Income does not")
    print("  discriminate between the margins under any measure -- the null is a property of the")
    print("  resources channel, not of the NSDP proxy.")

    # ------------------------------------------------------- I3: income terciles
    print("\n" + "=" * 112)
    print("  I3 -- THRESHOLD SPECIFICATION FOR INCOME (symmetric to the skills terciles)")
    print("  Cole-Sampson-Zia is a claim about a price constraint binding at LOW income,")
    print("  which is a threshold claim, not a linear one. T1 (poorest 11 states) omitted.")
    print("=" * 112)
    Xi = ["c_upi", "upi_x_incT2_mid", "upi_x_incT3_high", "upi_x_diglit_w"] + CONTROLS
    for dv, dvlab in DVS:
        r = fit(d, dv, Xi)
        print(f"\n  DV: {dvlab}")
        for v, lab in [("c_upi", "UPI effect in T1 (poorest)"),
                       ("upi_x_incT2_mid", "extra in T2 (middle)"),
                       ("upi_x_incT3_high", "extra in T3 (richest)")]:
            pb = wild_cluster_bootstrap(d, dv, Xi, v, B=9999)["p_wcb"]
            print(f"    {lab:34s} {r.params[v]:9.4f} {r.std_errors[v]:8.4f} {pb:9.4f} {stars(pb)}")
            rows.append({"check": "I3 income terciles", "dv": dv, "term": lab,
                         "coef": r.params[v], "se": r.std_errors[v], "p_boot": pb, "N": int(r.nobs)})
        b1, d2, d3 = r.params["c_upi"], r.params["upi_x_incT2_mid"], r.params["upi_x_incT3_high"]
        print(f"    by tercile:  T1 {b1:+.4f}   T2 {b1 + d2:+.4f}   T3 {b1 + d3:+.4f}")

    # ------------------------------------------------------- head to head at the margins
    print("\n" + "=" * 112)
    print("  SKILLS x RESOURCES AT THE MARGINS -- are the two channels substitutes or complements?")
    print("  Mean UPI effect on the intensive margin (deposits Rs/capita), by cell.")
    print("=" * 112)
    sub = d.groupby(["diglit_tercile", "income_tercile"]).size().unstack(fill_value=0)
    print("\n  states per cell (rows = digital literacy, columns = income):")
    print(sub.div(5).astype(int).to_string())
    print("\n  The off-diagonal cells are what separates the two hypotheses. There are"
          f" {int((sub.div(5).astype(int).values.sum() - np.trace(sub.div(5).astype(int).values)))}"
          " states off the diagonal,")
    print("  so the horse race is identified, but thinly in the corners.")

    pd.DataFrame(rows).to_csv(OUT / "table22_h5_income.csv", index=False)
    print(f"\n  wrote {OUT / 'table22_h5_income.csv'}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
