#!/usr/bin/env python3
"""
Build the three report-specific figures from the analysis panels.
Outputs go to report/images/. Re-run after any re-estimation.
"""
import pathlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output"
IMG = pathlib.Path(__file__).resolve().parent / "images"

RED, BLUE, GREY, AMBER = "#c0392b", "#1f4e79", "#8a8a8a", "#e8912a"
plt.rcParams.update({"font.size": 9, "axes.spines.top": False,
                     "axes.spines.right": False, "figure.dpi": 200})

# ─────────────────────────────────────────────────────────────────────
# FIG 4 — the premise: digital moved, physical did not
# ─────────────────────────────────────────────────────────────────────
d = pd.read_csv(OUT / "panel_digital.csv")
m = d.groupby("fy_end")[["pp_users_per_adult", "pp_txns_per_capita",
                         "pp_value_per_capita", "branches_per_lakh_adults",
                         "atms_per_lakh_adults"]].mean()
idx = m / m.iloc[0] * 100

fig, ax = plt.subplots(1, 2, figsize=(9.6, 3.6))

series = [("pp_value_per_capita", "UPI value per capita", RED, "-"),
          ("pp_txns_per_capita", "UPI transactions per capita", AMBER, "-"),
          ("pp_users_per_adult", "UPI users per adult", BLUE, "-"),
          ("branches_per_lakh_adults", "Branches per lakh adults", GREY, "--"),
          ("atms_per_lakh_adults", "ATMs per lakh adults", GREY, ":")]
for c, lab, col, ls in series:
    ax[0].plot(idx.index, idx[c], marker="o", ms=3.5, color=col, ls=ls, lw=1.6, label=lab)
ax[0].set_yscale("log")
ax[0].set_yticks([100, 300, 1000, 3000])
ax[0].set_yticklabels(["100", "300", "1,000", "3,000"])
ax[0].axhline(100, color="k", lw=0.6, alpha=.4)
ax[0].set_ylabel("index, FY2019 = 100  (log scale)")
ax[0].set_xlabel("financial year ending 31 March")
ax[0].set_xticks(idx.index)
ax[0].set_title("Digital infrastructure moved; physical did not", loc="left", fontsize=10)
ax[0].legend(frameon=False, fontsize=7.4, loc="upper left")
ax[0].grid(axis="y", alpha=.25)

w = 0.36
x = np.arange(len(m))
ax2 = ax[1]
ax2.bar(x - w/2, m["pp_users_per_adult"], w, color=BLUE, label="UPI users per adult (left)")
ax2.set_ylabel("UPI users per adult", color=BLUE)
ax2.tick_params(axis="y", colors=BLUE)
ax2b = ax2.twinx()
ax2b.bar(x + w/2, m["branches_per_lakh_adults"], w, color=GREY,
         label="Branches per lakh adults (right)")
ax2b.set_ylabel("Branches per lakh adults", color="#5a5a5a")
ax2b.set_ylim(0, 30)
ax2b.spines["top"].set_visible(False)
ax2.set_xticks(x); ax2.set_xticklabels(m.index)
ax2.set_xlabel("financial year ending 31 March")
ax2.set_title("Levels: a 3.4$\\times$ rise against a flat line", loc="left", fontsize=10)
h1, l1 = ax2.get_legend_handles_labels(); h2, l2 = ax2b.get_legend_handles_labels()
ax2.legend(h1 + h2, l1 + l2, frameon=False, fontsize=7.4, loc="upper left")
fig.tight_layout()
fig.savefig(IMG / "fig4_digital_vs_physical.png", bbox_inches="tight")
plt.close(fig)

# ─────────────────────────────────────────────────────────────────────
# FIG 5 — within-state variation: why Track 3 can answer what 1 and 2 could not
# ─────────────────────────────────────────────────────────────────────
labels = ["Branches\nper lakh adults", "ATMs\nper lakh adults",
          "UPI users\nper adult", "UPI transactions\nper capita", "UPI value\nper capita"]
vals = [6.5, 8.2, 67.1, 79.9, 78.8]
cols = [GREY, GREY, BLUE, BLUE, BLUE]

fig, ax = plt.subplots(figsize=(8.2, 3.5))
bars = ax.bar(labels, vals, color=cols, width=.62)
ax.axhspan(0, 10, color=RED, alpha=.10)
ax.axhspan(10, 25, color=AMBER, alpha=.12)
ax.axhline(10, color=RED, lw=1.1, ls="--")
ax.axhline(25, color=AMBER, lw=1.1, ls="--")
ax.text(4.52, 10, " FAIL\n threshold", va="center", fontsize=7.4, color=RED)
ax.text(4.52, 25, " PASS\n threshold", va="center", fontsize=7.4, color="#a8690f")
for b, v in zip(bars, vals):
    # lift the labels on the two short bars clear of the FAIL/PASS threshold lines
    off = 28.0 if v < 15 else 1.6
    ax.text(b.get_x() + b.get_width()/2, v + off, f"{v:.1f}%", ha="center", fontsize=9,
            fontweight="bold", color=b.get_facecolor())
ax.set_ylim(0, 92); ax.set_xlim(-0.6, 5.4)
ax.set_ylabel("within-state share of total variation")
ax.set_title("Thresholds were fixed before the numbers were computed.\n"
             "The physical regressors fail; the digital regressors clear the PASS line "
             "by a factor of three.", loc="left", fontsize=9.6)
ax.grid(axis="y", alpha=.25)
fig.tight_layout()
fig.savefig(IMG / "fig5_within_variation.png", bbox_inches="tight")
plt.close(fig)

# ─────────────────────────────────────────────────────────────────────
# FIG 6 — leave-one-out: refit 33 times, dropping each state
# ─────────────────────────────────────────────────────────────────────
lo = pd.read_csv(OUT / "table13_leave_one_out.csv")
base = float(lo.loc[lo["dropped"] == "(none)", "coef"].iloc[0])
s = lo[lo["dropped"] != "(none)"].sort_values("coef").reset_index(drop=True)

fig, ax = plt.subplots(figsize=(8.6, 4.6))
y = np.arange(len(s))
ax.hlines(y, base, s["coef"], color="#c9c9c9", lw=1.0)
ax.scatter(s["coef"], y, s=22, color=RED, zorder=3)
ax.axvline(base, color=BLUE, lw=1.4,
           label=f"full sample: {base:+.3f}")
ax.axvline(0, color="k", lw=0.8, ls="--")
ax.set_yticks(y)
ax.set_yticklabels([t.title().replace("And ", "and ") for t in s["dropped"]], fontsize=6.6)
ax.set_xlim(-0.02, 0.55)
ax.set_xlabel("coefficient on UPI users per adult, credit accounts equation")
ax.set_title("Leave-one-state-out: the result does not rest on any single state\n"
             f"range {s['coef'].min():+.3f} to {s['coef'].max():+.3f}; "
             "every refit significant at 5\\%", loc="left", fontsize=10)
ax.legend(frameon=False, fontsize=8, loc="lower right")
ax.grid(axis="x", alpha=.25)
fig.tight_layout()
fig.savefig(IMG / "fig6_leave_one_out.png", bbox_inches="tight")
plt.close(fig)

print("wrote fig4_digital_vs_physical.png, fig5_within_variation.png, fig6_leave_one_out.png")
print(f"leave-one-out range: {s['coef'].min():.4f} to {s['coef'].max():.4f}, base {base:.4f}")
