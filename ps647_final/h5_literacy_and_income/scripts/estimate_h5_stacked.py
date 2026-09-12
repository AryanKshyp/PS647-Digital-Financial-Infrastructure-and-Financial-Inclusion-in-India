#!/usr/bin/env python3
"""
H5 Step 6 -- THE SHARP TEST (execution plan section 6.3). This is the headline specification.

H5's corollary: complementary endowments is a SECOND-LEVEL divide phenomenon, so it should condition
USAGE, not ACCESS. A moderator that is really just a development proxy would condition both
equally. The test stacks the outcomes and asks whether the moderation DIFFERS between them.

    Y_itk = b1*UPI + b2*(UPI x Intensive_k)
          + b3*(UPI x DigLit_s) + b5*(UPI x DigLit_s x Intensive_k)     <- b5 is the key term
          + b4*(UPI x Income_s) + b6*(UPI x Income_s x Intensive_k)
          + controls + fixed effects + e_itk

    Intensive_k = 0  credit accounts per adult        (extensive margin: does an account exist)
    Intensive_k = 1  deposits Rs/capita, credit Rs/capita  (intensive margin: how much moves)

165 state-years x 3 outcomes = 495 rows. Each outcome is standardised WITHIN OUTCOME to mean 0
SD 1 before stacking, otherwise b5 would only be picking up that the three DVs have different
scales. This is the one place the A2 pooled min-max scaling is set aside; the unstacked results
in table15 keep it, so they stay comparable to F12/F13.

b2 IS H1'S TEST -- whether infrastructure moves access more than usage. b5 is H5's. One equation,
two hypotheses, reported as adjacent rows.

WHY THIS SPECIFICATION ESCAPES PART OF THE ENDOGENEITY PROBLEM
--------------------------------------------------------------
The H1 main effect it builds on is a within-state correlation between two co-trending series and
is not causal (LIMITATIONS.md section 1). b5 does not inherit that in full: it is a difference
between outcomes measured on the SAME state in the SAME year, so any confounder that moves access
and usage together -- a state-specific income shock, smartphone diffusion, a fintech entering --
differences out. What b5 cannot survive is a confounder that moves usage and access DIFFERENTLY
and is correlated with digital literacy. That is a much narrower threat, and it is the honest
claim to make for this coefficient.

TWO FIXED-EFFECT SCHEMES, both reported:
  (A) plan spec   : state + year + outcome fixed effects
  (B) conservative: state x outcome + year x outcome fixed effects -- lets every outcome carry its
                    own state level and its own national time path. Strictly more demanding.

Writes output/table17_h5_stacked.csv
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))
from h5_lib import CONTROLS  # noqa: E402

warnings.filterwarnings("ignore")
OUT = ROOT_DIR / "output"

OUTCOMES = [
    ("norm_credit_accts_per_adult", "credit accounts / adult", 0),   # ACCESS, extensive
    ("norm_deposits_per_capita",    "deposits Rs / capita",    1),   # USAGE, intensive
    ("norm_credit_per_capita",      "credit Rs / capita",      1),   # USAGE, intensive
]

SKILL, INCOME = "z_diglit_w", "z_income_s"


def build_stack(d: pd.DataFrame) -> pd.DataFrame:
    zcols = [c for c in d.columns if c.startswith("z_")]   # carry every moderator for R1
    frames = []
    for col, label, intensive in OUTCOMES:
        f = d[["state_key", "fy_end", "c_upi"] + zcols + CONTROLS].copy()
        y = d[col]
        f["y"] = (y - y.mean()) / y.std(ddof=1)          # standardise WITHIN outcome
        f["outcome"] = col
        f["outcome_label"] = label
        f["intensive"] = float(intensive)
        frames.append(f)
    s = pd.concat(frames, ignore_index=True)

    s["upi_x_int"] = s["c_upi"] * s["intensive"]
    s["upi_x_skill"] = s["c_upi"] * s[SKILL]
    s["upi_x_income"] = s["c_upi"] * s[INCOME]
    s["upi_x_skill_x_int"] = s["upi_x_skill"] * s["intensive"]      # b5, the key term
    s["upi_x_income_x_int"] = s["upi_x_income"] * s["intensive"]    # b6
    return s


def lsdv(s: pd.DataFrame, X: list[str], fe: list[list[str]], cluster: str):
    """Multi-way LSDV with CR1 cluster-robust SEs. Same estimator family as the rest of the study;
    written out here because the stacked design has three fixed-effect dimensions."""
    parts = [np.ones((len(s), 1)), s[X].to_numpy(float)]
    for cols in fe:
        key = s[cols].astype(str).agg("|".join, axis=1)
        parts.append(pd.get_dummies(key, drop_first=True, dtype=float).to_numpy())
    Z = np.column_stack(parts)
    yv = s["y"].to_numpy(float)
    beta, *_ = np.linalg.lstsq(Z, yv, rcond=None)
    resid = yv - Z @ beta

    cl = s[cluster].to_numpy()
    uniq, cli = np.unique(cl, return_inverse=True)
    n, k = Z.shape
    G = len(uniq)
    A = np.linalg.pinv(Z.T @ Z)
    S = np.zeros((G, k))
    np.add.at(S, cli, Z * resid[:, None])
    meat = S.T @ S
    V = A @ meat @ A * (G / (G - 1)) * ((n - 1) / (n - k))
    se = np.sqrt(np.diag(V))

    from scipy import stats
    idx = {v: i + 1 for i, v in enumerate(X)}
    t = {v: beta[idx[v]] / se[idx[v]] for v in X}
    p = {v: 2 * (1 - stats.t.cdf(abs(t[v]), G - 1)) for v in X}
    return ({v: beta[idx[v]] for v in X}, {v: se[idx[v]] for v in X}, t, p,
            n, G, Z, yv, beta, resid, cli, idx)


def bootstrap_stacked(s, X, fe, cluster, target, B=9999, seed=647):
    """Same null-imposed wild cluster bootstrap as h5_lib, adapted to the stacked design.
    Clusters are states: the three outcome rows for a state-year are resampled together, which is
    what makes the within-state-year difference across outcomes a valid comparison."""
    _, _, _, _, n, G, Z, yv, beta, resid, cli, idx = lsdv(s, X, fe, cluster)
    j = idx[target]
    k = Z.shape[1]
    scale = (G / (G - 1)) * ((n - 1) / (n - k))
    A = np.linalg.pinv(Z.T @ Z)
    h = Z @ A[:, j]
    P = np.linalg.pinv(Z)
    M = np.eye(n) - Z @ P

    Sg = np.zeros((G, k))
    np.add.at(Sg, cli, Z * resid[:, None])
    se_j = np.sqrt((A @ (Sg.T @ Sg) @ A * scale)[j, j])
    t_obs = beta[j] / se_j

    Zr = np.delete(Z, j, axis=1)
    br, *_ = np.linalg.lstsq(Zr, yv, rcond=None)
    fit_r = Zr @ br
    resid_r = yv - fit_r

    rng = np.random.default_rng(seed)
    W = rng.choice([-1.0, 1.0], size=(G, B))
    Y = fit_r[:, None] + resid_r[:, None] * W[cli, :]
    Bt = P @ Y
    U = M @ Y
    Sb = np.zeros((G, B))
    np.add.at(Sb, cli, h[:, None] * U)
    Vjj = scale * (Sb ** 2).sum(axis=0)
    t_star = np.where(Vjj > 0, Bt[j] / np.sqrt(Vjj), np.nan)
    ok = np.isfinite(t_star)
    return float((np.abs(t_star[ok]) >= abs(t_obs)).sum() + 1) / (ok.sum() + 1)


def main() -> int:
    d = pd.read_csv(OUT / "panel_h5.csv")
    s = build_stack(d)
    print("\n" + "=" * 104)
    print("  H5 STEP 6 -- THE SHARP TEST (stacked outcomes)")
    print(f"  {len(d)} state-years x {len(OUTCOMES)} outcomes = {len(s)} rows, "
          f"{s.state_key.nunique()} clusters (states)")
    print("  Each outcome standardised within itself (mean 0, SD 1) before stacking.")
    print("=" * 104 + "\n")
    print("  Intensive_k = 0 : credit accounts / adult          (extensive margin)")
    print("  Intensive_k = 1 : deposits Rs/capita, credit Rs/capita (intensive margin)\n")

    X = ["c_upi", "upi_x_int", "upi_x_skill", "upi_x_skill_x_int",
         "upi_x_income", "upi_x_income_x_int"] + CONTROLS

    SCHEMES = {
        "(A) state + year + outcome FE": [["state_key"], ["fy_end"], ["outcome"]],
        "(B) state x outcome + year x outcome FE": [["state_key", "outcome"], ["fy_end", "outcome"]],
    }

    LABELS = {
        "c_upi": "b1  UPI",
        "upi_x_int": "b2  UPI x Intensive        <- H1's test",
        "upi_x_skill": "b3  UPI x skills",
        "upi_x_skill_x_int": "b5  UPI x skills x Intensive   <- H5 KEY",
        "upi_x_income": "b4  UPI x resources",
        "upi_x_income_x_int": "b6  UPI x resources x Intensive",
    }

    rows = []
    for scheme, fe in SCHEMES.items():
        beta, se, t, p, n, G, *_ = lsdv(s, X, fe, "state_key")
        print("=" * 104)
        print(f"  {scheme}    N={n}  clusters={G}")
        print("=" * 104)
        print(f"  {'coefficient':36s} {'estimate':>10s} {'se':>9s} {'t':>7s} "
              f"{'p clust':>9s} {'p boot':>9s}")
        print("  " + "-" * 88)
        for v in X:
            if v not in LABELS:
                continue
            pb = bootstrap_stacked(s, X, fe, "state_key", v, B=9999)
            star = "***" if pb < .01 else "**" if pb < .05 else "*" if pb < .10 else ""
            print(f"  {LABELS[v]:36s} {beta[v]:10.4f} {se[v]:9.4f} {t[v]:7.2f} "
                  f"{p[v]:9.4f} {pb:9.4f} {star}")
            rows.append({"scheme": scheme, "regressor": v, "label": LABELS[v].split("  ")[1],
                         "coef": beta[v], "se": se[v], "t": t[v], "p_clustered": p[v],
                         "p_wild_bootstrap": pb, "N": n, "clusters": G})
        print(f"\n  {'controls (branches, ATMs, lnNSDP)':36s}"
              + "  ".join(f"{c.split('_')[0]} {beta[c]:+.4f}" for c in CONTROLS))

        # ---- implied marginal moderation on each margin
        print(f"\n  IMPLIED: how the UPI effect shifts per 1 SD of the moderator")
        print(f"    {'':22s} {'extensive (access)':>20s} {'intensive (usage)':>20s} {'difference':>14s}")
        for nm, b_, b5_ in [("digital literacy", "upi_x_skill", "upi_x_skill_x_int"),
                            ("resources/income", "upi_x_income", "upi_x_income_x_int")]:
            ext, dif = beta[b_], beta[b5_]
            print(f"    {nm:22s} {ext:20.4f} {ext + dif:20.4f} {dif:14.4f}")
        print()

    # ------------------------------------------------------------------ R1 ON THE HEADLINE
    # The placebo override applies to the sharp test too, and this is the version that matters.
    # Substitute each placebo for the skills moderator and ask whether IT also produces b5 > 0.
    # A generic development gradient should not discriminate between the two margins; if it does,
    # b5 is not measuring a second-level divide.
    print("=" * 104)
    print("  R1 PLACEBO ON THE SHARP TEST -- scheme (B), each moderator substituted for skills")
    print("  The question is not whether b5 is significant. It is whether ONLY digital literacy")
    print("  produces it. A development proxy should move both margins alike, i.e. b5 ~ 0.")
    print("=" * 104)
    fe_b = SCHEMES["(B) state x outcome + year x outcome FE"]
    print(f"\n  {'moderator substituted for skills':38s} {'role':22s} {'b3':>9s} {'b5':>9s} "
          f"{'p boot b5':>10s}")
    print("  " + "-" * 92)
    PLACEBO_MODS = [
        ("z_diglit_w", "NFHS-5 women internet", "TREATMENT"),
        ("z_schooling_w", "NFHS-5 women 10+ yrs school", "PLACEBO same instrument"),
        ("z_schooling_m", "NFHS-5 men 10+ yrs school", "PLACEBO same instrument"),
        ("z_everschool_w", "NFHS-5 female ever in school", "PLACEBO same instrument"),
        ("z_lit2011", "Census 2011 literacy", "PLACEBO conventional"),
        ("z_urban_share_nfhs", "derived urban share", "PLACEBO conventional"),
        ("z_diglit_m", "NFHS-5 men internet", "ALT digital"),
        ("z_mobile_w", "NFHS-5 women mobile phone", "ALT digital"),
        ("z_nss75_computer", "NSS 75th computer ability", "ALT pre-window n=22"),
    ]
    for zcol, label, role in PLACEBO_MODS:
        sp = s.copy()
        sp["upi_x_skill"] = sp["c_upi"] * sp[zcol]
        sp["upi_x_skill_x_int"] = sp["upi_x_skill"] * sp["intensive"]
        sp = sp.dropna(subset=["upi_x_skill"])
        beta, se, t, p, n, G, *_ = lsdv(sp, X, fe_b, "state_key")
        pb = bootstrap_stacked(sp, X, fe_b, "state_key", "upi_x_skill_x_int", B=9999)
        star = "***" if pb < .01 else "**" if pb < .05 else "*" if pb < .10 else ""
        mark = "  <-- FIRES" if (pb < 0.05 and role.startswith("PLACEBO")) else ""
        print(f"  {label:38s} {role:22s} {beta['upi_x_skill']:9.4f} "
              f"{beta['upi_x_skill_x_int']:9.4f} {pb:10.4f} {star}{mark}")
        rows.append({"scheme": "(B) R1 placebo", "regressor": zcol, "label": f"{label} [{role}]",
                     "coef": beta["upi_x_skill_x_int"], "se": se["upi_x_skill_x_int"],
                     "t": t["upi_x_skill_x_int"], "p_clustered": p["upi_x_skill_x_int"],
                     "p_wild_bootstrap": pb, "N": n, "clusters": G})
    print()

    pd.DataFrame(rows).to_csv(OUT / "table17_h5_stacked.csv", index=False)
    print(f"  wrote {OUT / 'table17_h5_stacked.csv'}\n")

    # ---------------------------------------------------------------- verdict
    print("=" * 104)
    print("  SHARP-TEST VERDICT against the rule fixed in execution plan section 7")
    print("=" * 104)
    df = pd.DataFrame(rows)
    for scheme in SCHEMES:
        sub = df[df.scheme == scheme].set_index("regressor")
        b5, p5 = sub.loc["upi_x_skill_x_int", "coef"], sub.loc["upi_x_skill_x_int", "p_wild_bootstrap"]
        b6, p6 = sub.loc["upi_x_income_x_int", "coef"], sub.loc["upi_x_income_x_int", "p_wild_bootstrap"]
        b3 = sub.loc["upi_x_skill", "coef"]
        print(f"\n  {scheme}")
        if p5 < 0.05 and b5 > 0:
            v = "b5 > 0 and significant -> H5's corollary HOLDS for skills"
        elif p5 < 0.05 and b5 < 0:
            v = "b5 < 0 and significant -> capacity matters MORE for access than usage; CONTRADICTS the framework"
        elif abs(b3) > 1e-9 and p5 >= 0.05:
            v = "b5 ~ 0 -> skills moderation does not differ between margins; NOT a second-level effect"
        else:
            v = "b5 ~ 0"
        print(f"    skills    b5 = {b5:+.4f} (p_boot {p5:.4f})  {v}")
        vi = ("b6 > 0 and significant -> resources condition the intensive margin specifically"
              if p6 < 0.05 and b6 > 0 else
              "b6 < 0 and significant -> resources matter more for access" if p6 < 0.05 else
              "b6 ~ 0 -> resources moderation does not differ between margins")
        print(f"    resources b6 = {b6:+.4f} (p_boot {p6:.4f})  {vi}")
    print("=" * 104 + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
