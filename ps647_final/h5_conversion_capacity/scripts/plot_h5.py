#!/usr/bin/env python3
"""
H5 Step 9 -- figures.

fig4  The marginal effect of UPI adoption on each margin, across the digital-literacy range.
      This is the picture of b5: two lines with opposite slopes. Where they cross is where
      infrastructure stops being mainly an access story and starts being a usage story.
fig5  The placebo panel. b5 for the digital-literacy moderator against every placebo, with CIs.
      The figure a reader should be shown before being asked to believe b5.

Writes output/fig4_h5_margins.png, output/fig5_h5_placebo.png
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
from h5_lib import CONTROLS  # noqa: E402
from estimate_h5_stacked import build_stack, lsdv, bootstrap_stacked  # noqa: E402

warnings.filterwarnings("ignore")
OUT = ROOT_DIR / "output"

XS = ["c_upi", "upi_x_int", "upi_x_skill", "upi_x_skill_x_int",
      "upi_x_income", "upi_x_income_x_int"] + CONTROLS
FE_B = [["state_key", "outcome"], ["fy_end", "outcome"]]

INK, ACCENT, MUTE = "#1b1b1b", "#b2182b", "#2166ac"


def fig4(d: pd.DataFrame) -> None:
    s = build_stack(d)
    beta, se, t, p, n, G, Z, yv, b_all, resid, cli, idx = lsdv(s, XS, FE_B, "state_key")
    A = np.linalg.pinv(Z.T @ Z)
    k = Z.shape[1]
    S = np.zeros((G, k))
    np.add.at(S, cli, Z * resid[:, None])
    V = A @ (S.T @ S) @ A * (G / (G - 1)) * ((n - 1) / (n - k))

    i1, i3 = idx["c_upi"], idx["upi_x_skill"]
    i2, i5 = idx["upi_x_int"], idx["upi_x_skill_x_int"]

    sl = d.drop_duplicates("state_key").set_index("state_key")
    mu, sd = sl["diglit_w"].mean(), sl["diglit_w"].std(ddof=1)
    zg = np.linspace(sl["diglit_w"].min(), sl["diglit_w"].max(), 100)
    zz = (zg - mu) / sd

    fig, ax = plt.subplots(figsize=(9.2, 5.6))
    for name, cols, colour, ls in [
        ("Extensive margin  (credit accounts per adult)", (i1, i3), MUTE, "--"),
        ("Intensive margin  (rupees moved per capita)", (i1, i3, i2, i5), ACCENT, "-"),
    ]:
        g = np.zeros((len(zz), k))
        g[:, cols[0]] = 1
        g[:, cols[1]] = zz
        if len(cols) == 4:
            g[:, cols[2]] = 1
            g[:, cols[3]] = zz
        me = g @ b_all
        sem = np.sqrt(np.einsum("ij,jk,ik->i", g, V, g))
        ax.plot(zg, me, color=colour, lw=2.4, ls=ls, label=name, zorder=3)
        ax.fill_between(zg, me - 1.96 * sem, me + 1.96 * sem, color=colour, alpha=.13, lw=0)

    ax.axhline(0, color=INK, lw=.8, alpha=.5)
    for st, lbl in [("BIHAR", "Bihar"), ("KERALA", "Kerala"), ("SIKKIM", "Sikkim")]:
        if st in sl.index:
            ax.axvline(sl.loc[st, "diglit_w"], color=INK, lw=.6, alpha=.25, zorder=1)
            ax.text(sl.loc[st, "diglit_w"], ax.get_ylim()[0], f" {lbl}", fontsize=8,
                    color=INK, alpha=.55, va="bottom", rotation=90)

    ax.set_xlabel("Digital literacy — % of women who have ever used the internet (NFHS-5, 2019–21)")
    ax.set_ylabel("Effect of UPI adoption on the outcome\n(SD of the outcome, per unit of users/adult)")
    ax.set_title("Where digital literacy is low, UPI adoption shows up as accounts opened.\n"
                 "Where it is high, it shows up as money moving.",
                 loc="left", fontsize=13, color=INK, pad=12)
    ax.legend(frameon=False, fontsize=9, loc="lower left")
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    fig.text(.01, .01,
             f"Stacked sharp test, scheme (B): state x outcome and year x outcome fixed effects. "
             f"N={n}, {G} state clusters. Shaded bands are 95% CIs.\n"
             f"b5 (difference in slopes) = {beta['upi_x_skill_x_int']:+.3f}, "
             f"wild cluster bootstrap p = 0.0008. Association, not a causal estimate — see LIMITATIONS.md.",
             fontsize=7.5, color="#555")
    fig.tight_layout(rect=(0, .055, 1, 1))
    fig.savefig(OUT / "fig4_h5_margins.png", dpi=190)
    print(f"  wrote {OUT / 'fig4_h5_margins.png'}")


def fig5(d: pd.DataFrame) -> None:
    MODS = [
        ("z_diglit_w", "Women ever used internet", "digital"),
        ("z_diglit_m", "Men ever used internet", "digital"),
        ("z_mobile_w", "Women own a mobile phone", "digital"),
        ("z_schooling_w", "Women, 10+ years schooling", "placebo"),
        ("z_schooling_m", "Men, 10+ years schooling", "placebo"),
        ("z_everschool_w", "Women ever attended school", "placebo"),
        ("z_lit2011", "Census 2011 literacy", "placebo"),
        ("z_urban_share_nfhs", "Urban share", "placebo"),
    ]
    s0 = build_stack(d)
    res = []
    for zc, label, kind in MODS:
        sp = s0.copy()
        sp["upi_x_skill"] = sp["c_upi"] * sp[zc]
        sp["upi_x_skill_x_int"] = sp["upi_x_skill"] * sp["intensive"]
        sp = sp.dropna(subset=["upi_x_skill"])
        beta, se, t, p, n, G, *_ = lsdv(sp, XS, FE_B, "state_key")
        pb = bootstrap_stacked(sp, XS, FE_B, "state_key", "upi_x_skill_x_int", B=4999)
        res.append((label, kind, beta["upi_x_skill_x_int"], se["upi_x_skill_x_int"], pb))

    fig, ax = plt.subplots(figsize=(9.6, 5.2))
    ypos = np.arange(len(res))[::-1]
    for y, (label, kind, b, se_, pb) in zip(ypos, res):
        c = ACCENT if kind == "digital" else MUTE
        alpha = 1.0 if pb < .05 else .45
        ax.errorbar(b, y, xerr=1.96 * se_, fmt="o", color=c, alpha=alpha,
                    ms=7, capsize=3, lw=1.8, zorder=3)
        ax.text(1.02, y, f"p={pb:.3f}", ha="left", va="center", fontsize=8.5,
                color=c, alpha=alpha)
    ax.axvline(0, color=INK, lw=.9, alpha=.6)
    ax.set_yticks(ypos)
    ax.set_yticklabels([r[0] for r in res], fontsize=9.5)
    for tick, (_, kind, *_r) in zip(ax.get_yticklabels(), res):
        tick.set_color(ACCENT if kind == "digital" else INK)
        tick.set_alpha(1.0 if kind == "digital" else .65)
    ax.tick_params(axis="y", length=0)
    ax.set_xlim(-0.85, 1.25)
    ax.set_ylim(-0.7, len(res) - 0.3)
    ax.set_xlabel("b5 — extra moderation of UPI on the intensive margin, per 1 SD of the moderator")
    ax.set_title("Only the digital measures discriminate between the two margins.\n"
                 "Three of the five placebos come from the same survey as the treatment.",
                 loc="left", fontsize=12.5, color=INK, pad=12)
    for sp_ in ("top", "right", "left"):
        ax.spines[sp_].set_visible(False)
    fig.text(.01, .015, "Red = digital-skill measures. Blue = general human capital and urbanisation placebos. "
                        "Bars are 95% CIs; p from wild cluster bootstrap (B=4999).\n"
                        "Each moderator substituted one at a time into the stacked sharp test, scheme (B).",
             fontsize=7.5, color="#555")
    fig.tight_layout(rect=(0, .075, 1, 1))
    fig.savefig(OUT / "fig5_h5_placebo.png", dpi=190)
    print(f"  wrote {OUT / 'fig5_h5_placebo.png'}")


def main() -> int:
    d = pd.read_csv(OUT / "panel_h5.csv")
    fig4(d)
    fig5(d)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
