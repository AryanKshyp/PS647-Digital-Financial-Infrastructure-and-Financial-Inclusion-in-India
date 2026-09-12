#!/usr/bin/env python3
"""
Digital-track figure. Writes output/fig3_digital.png

Left  : the UPI coefficient on each of the four component indicators, with the
        D7-trimmed deposit-account estimate overlaid — the entangled channel
        collapses to zero when two defective cells are removed, the clean one does not.
Right : the credit-only H1 triple — access, usage, and the gap between them.

Colour encodes significance only, matching fig2's convention; every mark also carries
its p-value as text, so nothing is conveyed by colour alone.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent

OUT = ROOT_DIR / "output"
t11 = pd.read_csv(OUT / "table11_components.csv")
t12 = pd.read_csv(OUT / "table12_components_d7.csv")

SIG, MARG, NS = "#dc2626", "#f59e0b", "#94a3b8"
INK, MUTED = "#1e293b", "#64748b"


def colour(p):
    return SIG if p < .05 else MARG if p < .10 else NS


fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.5, 5.0))

# ---------------- left: UPI coefficient on each component -------------------
comp = [
    ("credit accounts / adult", "norm_credit_accts_per_adult", "clean"),
    ("deposits ₹ / capita", "norm_deposits_per_capita", "clean"),
    ("credit ₹ / capita", "norm_credit_per_capita", "clean"),
    ("deposit accounts / adult", "norm_deposit_accts_per_adult", "entangled"),
]
for i, (lab, col, status) in enumerate(comp):
    r = t11[(t11.panel == "A") & (t11.dependent == col) &
            (t11.regressor == "pp_users_per_adult")].iloc[0]
    c = colour(r.p)
    ax1.plot([r.ci_lo, r.ci_hi], [i, i], color=c, lw=2.6, solid_capstyle="round", zorder=2)
    ax1.plot(r.coef, i, "o", color=c, ms=9, zorder=3, mec="white", mew=2)
    ax1.annotate(f"{r.coef:+.3f}  p={r.p:.3f}", (r.ci_hi, i), textcoords="offset points",
                 xytext=(9, 0), va="center", fontsize=9, color=INK)

# the D7-trimmed deposit-account estimate, overlaid on the same row
d = t12[t12.dependent == "norm_deposit_accts_per_adult"].iloc[0]
y = len(comp) - 1
ax1.plot(d.coef_drop_d7, y, "D", color=INK, ms=7, zorder=4, mec="white", mew=1.5)
ax1.annotate(f"drop 2 defective cells → {d.coef_drop_d7:+.3f}  p={d.p_drop_d7:.3f}",
             (d.coef_drop_d7, y), textcoords="offset points", xytext=(0, -20),
             ha="center", fontsize=8.5, color=INK,
             bbox=dict(boxstyle="round,pad=0.3", fc="#f1f5f9", ec="#cbd5e1", lw=.8))

ax1.axvline(0, color="black", lw=1, ls="--", alpha=.7, zorder=1)
ax1.set_yticks(range(len(comp)))
ax1.set_yticklabels([f"{l}\n({s})" for l, _, s in comp], fontsize=9)
ax1.set_ylim(-0.7, len(comp) - 0.4)
ax1.set_xlim(-0.15, 0.85)
ax1.set_xlabel("coefficient on UPI users per adult (95% CI)")
ax1.set_title("The entangled channel is the null one\n"
              "red p<0.05 · grey n.s. · N=165",
              fontsize=11, loc="left", color=INK)
ax1.grid(axis="x", alpha=.25)
for s in ("top", "right"):
    ax1.spines[s].set_visible(False)

# ---------------- right: credit-only H1 triple ------------------------------
trip = [("Access\n(credit accounts)", "Access_c"), ("Usage", "Usage"),
        ("gap\n(Access − Usage)", "AUG_c")]
for i, (lab, dep) in enumerate(trip):
    r = t11[(t11.panel == "B") & (t11.dependent == dep) &
            (t11.regressor == "pp_users_per_adult")].iloc[0]
    c = colour(r.p)
    ax2.plot([i, i], [r.ci_lo, r.ci_hi], color=c, lw=2.8, solid_capstyle="round", zorder=2)
    ax2.plot(i, r.coef, "o", color=c, ms=10, zorder=3, mec="white", mew=2)
    ax2.annotate(f"{r.coef:+.3f}\np={r.p:.3f}", (i, r.ci_hi), textcoords="offset points",
                 xytext=(0, 9), ha="center", fontsize=9.5, color=INK)

ax2.axhline(0, color="black", lw=1, ls="--", alpha=.7, zorder=1)
ax2.set_xticks(range(len(trip)))
ax2.set_xticklabels([t[0] for t in trip], fontsize=9.5)
ax2.set_xlim(-0.6, 2.6)
ax2.set_ylim(-0.05, 0.72)
ax2.set_ylabel("coefficient on UPI users per adult (95% CI)")
ax2.set_title("H1's pattern, on UPI: access > usage > 0\n"
              "the gap is significant for the first time in the study",
              fontsize=11, loc="left", color=INK)
ax2.grid(axis="y", alpha=.25)
for s in ("top", "right"):
    ax2.spines[s].set_visible(False)

fig.tight_layout()
fig.savefig(OUT / "fig3_digital.png", dpi=150)
print(f"-> {OUT/'fig3_digital.png'}")
