#!/usr/bin/env python3
"""
Report-ready figures for the digital-literacy-and-income chapter.

Six figures, numbered for the report's Chapter 5, in the same visual idiom as Chapter 3:
wide, multi-panel where a comparison is being made, thresholds and zero lines drawn explicitly,
and every panel carrying the number a reader would otherwise have to look up in a table.

  5.1  The two endowments, and where they disagree        (motivates the horse race)
  5.2  Marginal effect of UPI by margin, across literacy  (the headline picture)
  5.3  The placebo panel                                  (why to believe the headline)
  5.4  The resources channel under two income measures    (why H5b does not survive)
  5.5  Decomposition and leave-one-out                    (what the headline rests on)
  5.6  Thresholds: terciles and the closing gap           (no functional form assumed)

Writes output/report_fig5_1.png ... report_fig5_6.png
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))
from h5_lib import CONTROLS, fit, wild_cluster_bootstrap  # noqa: E402
import estimate_h5_stacked as st  # noqa: E402
from estimate_h5_stacked import build_stack, lsdv, bootstrap_stacked  # noqa: E402

warnings.filterwarnings("ignore")
OUT = ROOT_DIR / "output"

XS = ["c_upi", "upi_x_int", "upi_x_skill", "upi_x_skill_x_int",
      "upi_x_income", "upi_x_income_x_int"] + CONTROLS
FE_B = [["state_key", "outcome"], ["fy_end", "outcome"]]

INK, RED, BLUE, GREY = "#1b1b1b", "#b2182b", "#2166ac", "#8c8c8c"
plt.rcParams.update({
    "font.size": 9, "axes.titlesize": 10.5, "axes.labelsize": 9,
    "axes.edgecolor": "#444444", "axes.linewidth": 0.8,
    "xtick.color": "#333333", "ytick.color": "#333333",
    "figure.facecolor": "white", "savefig.facecolor": "white",
})
DPI = 200


def pfmt(pv: float) -> str:
    """Never print 'p = 0.000'."""
    return "p < 0.001" if pv < 0.001 else f"p = {pv:.3f}"


def despine(ax, keep=("left", "bottom")):
    for s in ("top", "right", "left", "bottom"):
        if s not in keep:
            ax.spines[s].set_visible(False)


def stacked_fit(s, xs=XS, fe=FE_B):
    return lsdv(s, xs, fe, "state_key")


# --------------------------------------------------------------------------- 5.1
def fig_5_1(d):
    sl = d.drop_duplicates("state_key").set_index("state_key")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.6, 4.5),
                                   gridspec_kw={"width_ratios": [1.35, 1]})

    x, y = sl["income_s"], sl["diglit_w"]
    b, a = np.polyfit(x, y, 1)
    xs_ = np.linspace(x.min(), x.max(), 50)
    ax1.plot(xs_, a + b * xs_, color=GREY, lw=1.2, ls="--", zorder=1)
    resid = y - (a + b * x)
    ax1.scatter(x, y, s=34, color=BLUE, alpha=.75, zorder=3, edgecolor="white", lw=.6)
    for k in resid.abs().sort_values(ascending=False).head(7).index:
        ax1.annotate(k.title(), (x[k], y[k]), fontsize=7.5, color=INK,
                     xytext=(4, 4), textcoords="offset points")
    ax1.set_xlabel("Resources — state-mean ln NSDP per capita, FY2019–23")
    ax1.set_ylabel("Digital literacy — women who have\never used the internet (%)")
    ax1.set_title(f"The two endowments are correlated (r = {x.corr(y):.2f})\n"
                  "but far from identical", loc="left", color=INK)
    despine(ax1)

    ct = (d.drop_duplicates("state_key")
            .pivot_table(index="diglit_tercile", columns="income_tercile",
                         values="state_key", aggfunc="count").fillna(0))
    ct = ct.reindex(index=["T3_high", "T2_mid", "T1_low"],
                    columns=["T1_low", "T2_mid", "T3_high"]).fillna(0)
    im = ax2.imshow(ct.values, cmap="Blues", vmin=0, vmax=ct.values.max())
    for i in range(3):
        for j in range(3):
            v = int(ct.values[i, j])
            ax2.text(j, i, v, ha="center", va="center", fontsize=13,
                     color="white" if v > ct.values.max() * .6 else INK)
    ax2.set_xticks(range(3), ["low", "middle", "high"])
    ax2.set_yticks(range(3), ["high", "middle", "low"])
    ax2.set_xlabel("Income tercile")
    ax2.set_ylabel("Digital-literacy tercile")
    n_off = int(ct.values.sum() - np.trace(np.flipud(ct.values)))
    ax2.set_title(f"{n_off} of 33 states sit off the diagonal.\n"
                  "Those states identify the horse race.", loc="left", color=INK)
    for s_ in ("top", "right", "left", "bottom"):
        ax2.spines[s_].set_visible(False)
    ax2.tick_params(length=0)

    fig.tight_layout()
    fig.savefig(OUT / "report_fig5_1.png", dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print("  wrote report_fig5_1.png")


# --------------------------------------------------------------------------- 5.2
def fig_5_2(d):
    s = build_stack(d)
    beta, se, t, p, n, G, Z, yv, b_all, resid, cli, idx = stacked_fit(s)
    A = np.linalg.pinv(Z.T @ Z)
    k = Z.shape[1]
    S = np.zeros((G, k))
    np.add.at(S, cli, Z * resid[:, None])
    V = A @ (S.T @ S) @ A * (G / (G - 1)) * ((n - 1) / (n - k))
    i1, i3 = idx["c_upi"], idx["upi_x_skill"]
    i2, i5 = idx["upi_x_int"], idx["upi_x_skill_x_int"]

    sl = d.drop_duplicates("state_key").set_index("state_key")
    mu, sd = sl["diglit_w"].mean(), sl["diglit_w"].std(ddof=1)
    zg = np.linspace(sl["diglit_w"].min(), sl["diglit_w"].max(), 120)
    zz = (zg - mu) / sd

    fig, ax = plt.subplots(figsize=(9.4, 5.2))
    for name, cols, colour, ls in [
        ("Extensive margin — credit accounts per adult", (i1, i3), BLUE, "--"),
        ("Intensive margin — rupees moved per capita", (i1, i3, i2, i5), RED, "-"),
    ]:
        g = np.zeros((len(zz), k))
        g[:, cols[0]] = 1
        g[:, cols[1]] = zz
        if len(cols) == 4:
            g[:, cols[2]] = 1
            g[:, cols[3]] = zz
        me = g @ b_all
        sem = np.sqrt(np.einsum("ij,jk,ik->i", g, V, g))
        ax.plot(zg, me, color=colour, lw=2.5, ls=ls, label=name, zorder=3)
        ax.fill_between(zg, me - 1.96 * sem, me + 1.96 * sem, color=colour, alpha=.12, lw=0)
    ax.axhline(0, color=INK, lw=.9, alpha=.55)

    ymin = ax.get_ylim()[0]
    for stt, lbl in [("BIHAR", "Bihar"), ("UTTAR PRADESH", "Uttar Pradesh"),
                     ("KERALA", "Kerala"), ("SIKKIM", "Sikkim")]:
        if stt in sl.index:
            xv = sl.loc[stt, "diglit_w"]
            ax.axvline(xv, color=GREY, lw=.6, alpha=.45, zorder=1)
            ax.text(xv, ymin, f" {lbl}", fontsize=7.5, color=GREY, va="bottom", rotation=90)

    ax.set_xlabel("Digital literacy — % of women who have ever used the internet (NFHS-5, 2019–21)")
    ax.set_ylabel("Effect of UPI adoption on the outcome\n(standard deviations, per unit of users per adult)")
    ax.set_title("Where digital literacy is low, UPI adoption shows up as accounts opened.\n"
                 "Where it is high, it shows up as money held in them.", loc="left", color=INK)
    ax.legend(frameon=False, fontsize=8.5, loc="lower left")
    despine(ax)
    fig.tight_layout()
    fig.savefig(OUT / "report_fig5_2.png", dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print("  wrote report_fig5_2.png")


# --------------------------------------------------------------------------- 5.3
def fig_5_3(d):
    MODS = [
        ("z_diglit_w", "Women ever used the internet", "2019–21", "digital"),
        ("z_diglit_m", "Men ever used the internet", "2019–21", "digital"),
        ("z_mobile_w_2016", "Women own a mobile phone", "2015–16", "digital"),
        ("z_mobile_w", "Women own a mobile phone", "2019–21", "digital"),
        ("z_schooling_w", "Women, 10+ years of schooling", "2019–21", "placebo"),
        ("z_everschool_w", "Women ever attended school", "2019–21", "placebo"),
        ("z_schooling_w_2016", "Women, 10+ years of schooling", "2015–16", "placebo"),
        ("z_bankacct_w_2016", "Women own a bank account", "2015–16", "placebo"),
        ("z_lit2011", "General literacy rate", "2011", "placebo"),
        ("z_urban_share_nfhs", "Urban share", "derived", "placebo"),
    ]
    s0 = build_stack(d)
    res = []
    for zc, lab, vint, kind in MODS:
        sp = s0.copy()
        sp["upi_x_skill"] = sp["c_upi"] * sp[zc]
        sp["upi_x_skill_x_int"] = sp["upi_x_skill"] * sp["intensive"]
        sp = sp.dropna(subset=["upi_x_skill"])
        beta, se, *_ = stacked_fit(sp)
        pb = bootstrap_stacked(sp, XS, FE_B, "state_key", "upi_x_skill_x_int", B=4999)
        res.append((lab, vint, kind, beta["upi_x_skill_x_int"], se["upi_x_skill_x_int"], pb))

    fig, ax = plt.subplots(figsize=(10.2, 5.4))
    ypos = np.arange(len(res))[::-1]
    for y, (lab, vint, kind, b, se_, pb) in zip(ypos, res):
        c = RED if kind == "digital" else BLUE
        alpha = 1.0 if pb < .05 else .40
        ax.errorbar(b, y, xerr=1.96 * se_, fmt="o", color=c, alpha=alpha,
                    ms=6.5, capsize=3, lw=1.7, zorder=3)
        ax.text(1.30, y, pfmt(pb), ha="right", va="center", fontsize=8, color=c, alpha=alpha)
    ax.axvline(0, color=INK, lw=.9, alpha=.6)
    ax.set_yticks(ypos)
    ax.set_yticklabels([f"{l}   ({v})" for l, v, *_ in res], fontsize=8.8)
    for tick, (_, _, kind, *_r) in zip(ax.get_yticklabels(), res):
        tick.set_color(RED if kind == "digital" else INK)
        tick.set_alpha(1.0 if kind == "digital" else .7)
    ax.tick_params(axis="y", length=0)
    ax.set_xlim(-0.75, 1.33)
    ax.set_ylim(-0.7, len(res) - 0.3)
    ax.set_xlabel("Extra moderation of UPI on the intensive margin, per 1 SD of the moderator")
    ax.set_title("Only the digital measures distinguish the two margins.\n"
                 "Four placebos come from the same surveys, households and years as the treatment.",
                 loc="left", color=INK)
    despine(ax, keep=("bottom",))
    fig.tight_layout()
    fig.savefig(OUT / "report_fig5_3.png", dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print("  wrote report_fig5_3.png")


# --------------------------------------------------------------------------- 5.4
def fig_5_4(d):
    DVS = [("norm_credit_accts_per_adult", "Credit accounts\nper adult"),
           ("norm_deposits_per_capita", "Deposits ₹\nper capita"),
           ("norm_credit_per_capita", "Credit ₹\nper capita")]
    rows = []
    for dv, lab in DVS:
        for mod, mlab, c in [("income_s", "ln NSDP per capita (production)", BLUE),
                             ("ln_mpce", "ln MPCE (household consumption)", RED)]:
            v = f"upi_x_{mod}"
            X = ["c_upi", "upi_x_diglit_w", v] + CONTROLS
            r = fit(d, dv, X)
            pb = wild_cluster_bootstrap(d, dv, X, v, B=9999)["p_wcb"]
            rows.append((lab, mlab, c, r.params[v], r.std_errors[v], pb))

    fig, ax = plt.subplots(figsize=(9.8, 4.2))
    groups = [r[0] for r in rows[::2]]
    XMAX = 0.205
    for gi, g in enumerate(groups):
        sub = [r for r in rows if r[0] == g]
        for oi, (lab, mlab, c, b_, se_, pb) in enumerate(sub):
            y = gi + (-0.17 if oi == 0 else 0.17)     # NSDP on top, MPCE beneath
            alpha = 1.0 if pb < .05 else .42
            ax.errorbar(b_, y, xerr=1.96 * se_, fmt="o", color=c, ms=6.5, capsize=3,
                        lw=1.9, alpha=alpha, zorder=3,
                        label=mlab if gi == 0 else None)
            ax.text(XMAX, y, pfmt(pb), ha="right", va="center", fontsize=7.8,
                    color=c, alpha=alpha)
        if gi < len(groups) - 1:
            ax.axhline(gi + 0.5, color="#dddddd", lw=.8, zorder=0)
    ax.axvline(0, color=INK, lw=.9, alpha=.6)
    ax.set_yticks(range(len(groups)))
    ax.set_yticklabels(groups, fontsize=9)
    ax.tick_params(axis="y", length=0)
    ax.set_ylim(len(groups) - 0.5, -0.5)
    ax.set_xlim(-0.075, XMAX)
    ax.set_xticks([-0.05, 0.0, 0.05, 0.10])
    ax.set_xlabel("Interaction of UPI adoption with the resources moderator, per 1 SD")
    ax.set_title("The resources result depends on which income measure is used.\n"
                 "Its strongest coefficient (p = 0.0002) becomes p = 0.998 under household consumption.",
                 loc="left", color=INK)
    ax.legend(frameon=False, fontsize=8.3, loc="upper center",
              bbox_to_anchor=(0.42, -0.17), ncol=2)
    despine(ax, keep=("bottom",))
    fig.tight_layout()
    fig.savefig(OUT / "report_fig5_4.png", dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print("  wrote report_fig5_4.png")


# --------------------------------------------------------------------------- 5.5
def fig_5_5(d):
    EXT = ("norm_credit_accts_per_adult", "credit accounts / adult", 0)
    ENT = ("norm_deposit_accts_per_adult", "deposit accounts / adult", 0)
    DEP = ("norm_deposits_per_capita", "deposits ₹ / capita", 1)
    CRD = ("norm_credit_per_capita", "credit ₹ / capita", 1)
    pairs = [([EXT, DEP, CRD], "Pooled — all three outcomes\n(the reported headline)", True),
             ([EXT, DEP], "Credit accounts  vs  deposits ₹", True),
             ([EXT, CRD], "Credit accounts  vs  credit ₹", True),
             ([ENT, DEP], "Deposit accounts  vs  deposits ₹", False),
             ([ENT, CRD], "Deposit accounts  vs  credit ₹", False)]
    saved = st.OUTCOMES
    res = []
    for outs, lab, clean in pairs:
        st.OUTCOMES = outs
        s = build_stack(d)
        beta, se, *_ = stacked_fit(s)
        pb = bootstrap_stacked(s, XS, FE_B, "state_key", "upi_x_skill_x_int", B=9999)
        res.append((lab, clean, beta["upi_x_skill_x_int"], se["upi_x_skill_x_int"], pb))
    st.OUTCOMES = saved

    loo = pd.read_csv(OUT / "table19b_h5_leave_one_out.csv")
    base = res[0][2]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.0, 4.4),
                                   gridspec_kw={"width_ratios": [1.25, 1]})
    ypos = np.arange(len(res))[::-1]
    for y, (lab, clean, b, se_, pb) in zip(ypos, res):
        c = RED if clean else GREY
        alpha = 1.0 if pb < .05 else .45
        ax1.errorbar(b, y, xerr=1.96 * se_, fmt="o", color=c, ms=7, capsize=3,
                     lw=1.9, alpha=alpha, zorder=3)
        ax1.text(1.86, y, pfmt(pb), ha="right", va="center", fontsize=7.8,
                 color=c, alpha=alpha)
    ax1.axvline(0, color=INK, lw=.9, alpha=.6)
    ax1.set_yticks(ypos)
    ax1.set_yticklabels([r[0] for r in res], fontsize=8.5)
    for tick, r in zip(ax1.get_yticklabels(), res):
        tick.set_color(INK if r[1] else GREY)
    ax1.tick_params(axis="y", length=0)
    ax1.set_xlim(-1.8, 1.9)
    ax1.set_xlabel("Differential moderation, per 1 SD of digital literacy")
    ax1.set_title("The effect is carried by deposits, and reverses\n"
                  "on the entangled account measure (grey)", loc="left", color=INK)
    despine(ax1, keep=("bottom",))

    ax2.hist(loo["b5"], bins=12, color=BLUE, alpha=.72, edgecolor="white")
    ax2.axvline(base, color=RED, lw=2, label=f"full sample  {base:+.3f}")
    ax2.axvline(0, color=INK, lw=.9, alpha=.6)
    ax2.set_xlabel("Estimate when one state is dropped")
    ax2.set_ylabel("Number of refits")
    ax2.set_title(f"33 refits: range {loo['b5'].min():+.3f} to {loo['b5'].max():+.3f},\n"
                  "no sign flips, none loses significance", loc="left", color=INK)
    ax2.legend(frameon=False, fontsize=8)
    despine(ax2)
    fig.tight_layout()
    fig.savefig(OUT / "report_fig5_5.png", dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print("  wrote report_fig5_5.png")


# --------------------------------------------------------------------------- 5.6
def fig_5_6(d):
    X = ["c_upi", "upi_x_T2_mid", "upi_x_T3_high", "upi_x_income_s"] + CONTROLS
    DVS = [("norm_credit_accts_per_adult", "Credit accounts per adult\n(extensive margin)", BLUE),
           ("norm_deposits_per_capita", "Deposits ₹ per capita\n(intensive margin)", RED),
           ("norm_credit_per_capita", "Credit ₹ per capita\n(intensive margin)", "#762a83")]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.8, 4.4),
                                   gridspec_kw={"width_ratios": [1.15, 1]})
    xs_ = np.arange(3)
    # label offsets chosen per series so the three lines' annotations do not collide at x=0
    offs = {0: (0, 10), 1: (0, 9), 2: (0, -15)}
    for si, (dv, lab, c) in enumerate(DVS):
        r = fit(d, dv, X)
        b1 = r.params["c_upi"]
        vals = [b1, b1 + r.params["upi_x_T2_mid"], b1 + r.params["upi_x_T3_high"]]
        ax1.plot(xs_, vals, "-o", color=c, lw=2.1, ms=7, label=lab)
        for xx, vv in zip(xs_, vals):
            ax1.annotate(f"{vv:.3f}", (xx, vv), fontsize=7.4, color=c,
                         xytext=offs[si], textcoords="offset points", ha="center")
    ax1.axhline(0, color=INK, lw=.9, alpha=.5)
    ax1.set_xticks(xs_, ["lowest third", "middle third", "highest third"])
    ax1.set_xlim(-0.35, 2.45)
    ax1.set_ylim(-0.06, 0.62)
    ax1.set_xlabel("States grouped by digital literacy")
    ax1.set_ylabel("Effect of UPI adoption")
    # Accurate to what the lines do: only deposits rises monotonically. Credit accounts peaks
    # in the middle tercile and falls; credit rupees falls in the top tercile.
    ax1.set_title("No functional form assumed. Only the deposits margin\n"
                  "rises across terciles — neither credit series does", loc="left", color=INK)
    ax1.legend(frameon=False, fontsize=7.6, loc="upper center",
               bbox_to_anchor=(0.5, -0.20), ncol=3, columnspacing=1.1)
    despine(ax1)

    s = build_stack(d)
    s = s.merge(d[["state_key", "fy_end", "diglit_tercile"]].drop_duplicates(),
                on=["state_key", "fy_end"], how="left")
    for t in ["T2_mid", "T3_high"]:
        s[f"upi_x_{t}"] = s["c_upi"] * (s["diglit_tercile"] == t).astype(float)
        s[f"upi_x_{t}_x_int"] = s[f"upi_x_{t}"] * s["intensive"]
    Xs = ["c_upi", "upi_x_int", "upi_x_T2_mid", "upi_x_T2_mid_x_int",
          "upi_x_T3_high", "upi_x_T3_high_x_int", "upi_x_income", "upi_x_income_x_int"] + CONTROLS
    beta, se, *_ = lsdv(s, Xs, FE_B, "state_key")
    g1 = beta["upi_x_int"]
    gaps = [g1, g1 + beta["upi_x_T2_mid_x_int"], g1 + beta["upi_x_T3_high_x_int"]]
    ax2.bar(xs_, gaps, color=[BLUE, BLUE, RED], alpha=.82, width=.6)
    for xx, vv in zip(xs_, gaps):
        ax2.annotate(f"{vv:.2f}", (xx, vv), fontsize=8.5, color=INK, ha="center",
                     xytext=(0, -14 if vv < 0 else 5), textcoords="offset points")
    ax2.axhline(0, color=INK, lw=.9)
    ax2.set_xticks(xs_, ["lowest third", "middle third", "highest third"])
    ax2.set_xlabel("States grouped by digital literacy")
    ax2.set_ylabel("Intensive minus extensive effect")
    ax2.set_title("The gap between the two margins nearly closes\nin the most literate third",
                  loc="left", color=INK)
    despine(ax2)
    fig.tight_layout()
    fig.savefig(OUT / "report_fig5_6.png", dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print("  wrote report_fig5_6.png")


def main() -> int:
    d = pd.read_csv(OUT / "panel_h5.csv")
    print("\n  Building report figures 5.1-5.6\n")
    fig_5_1(d)
    fig_5_2(d)
    fig_5_3(d)
    fig_5_4(d)
    fig_5_5(d)
    fig_5_6(d)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
