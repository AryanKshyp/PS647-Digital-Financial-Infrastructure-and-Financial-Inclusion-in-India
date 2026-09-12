#!/usr/bin/env python3
"""
Scatter of the four model variables over time, one point per state-year.

Faint lines connect each state across years, so within-state movement is visible --
that is the question Step 4 raised, and it shows up directly here.

Writes output/fig1_variables_over_time.png
"""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent

OUT = ROOT_DIR / "output"
d = pd.read_csv(OUT / "panel_analysis.csv")

PANELS = [
    ("branches_per_lakh_adults", "Branches per lakh adults", "IV"),
    ("atms_per_lakh_adults",     "ATMs per lakh adults",     "IV"),
    ("Access",                   "Access (0-1 composite)",   "DV1"),
    ("Usage",                    "Usage (0-1 composite)",    "DV2"),
]

fig, axes = plt.subplots(2, 2, figsize=(13, 9))
years = sorted(d.fy_end.unique())

for ax, (col, title, role) in zip(axes.ravel(), PANELS):
    # faint per-state trajectories
    for st, g in d.groupby("state_key"):
        g = g.sort_values("fy_end")
        ax.plot(g.fy_end, g[col], color="#9aa5b1", lw=0.8, alpha=0.55, zorder=1)
    # the points themselves
    ax.scatter(d.fy_end, d[col], s=22, color="#2563eb", alpha=0.75,
               edgecolor="white", linewidth=0.4, zorder=2)
    # median trend
    med = d.groupby("fy_end")[col].median()
    ax.plot(med.index, med.values, color="#dc2626", lw=2.4, zorder=3, label="median")

    swing = 100 * ((d.groupby("state_key")[col].max() - d.groupby("state_key")[col].min())
                   / d.groupby("state_key")[col].mean()).median()
    ax.set_title(f"{role} · {title}\nmedian within-state swing {swing:.1f}%",
                 fontsize=11, loc="left")
    ax.set_xticks(years)
    ax.set_xlabel("financial year ending 31 March")
    ax.grid(alpha=0.25, lw=0.6)
    ax.legend(fontsize=8, frameon=False, loc="upper left")

fig.suptitle("State-year observations, FY2018–FY2023 (33 states, 198 points)\n"
             "grey lines trace individual states — flat lines mean little within-state variation",
             fontsize=13, y=0.98)
fig.tight_layout(rect=[0, 0, 1, 0.94])
p = OUT / "fig1_variables_over_time.png"
fig.savefig(p, dpi=150)
print(f"  -> {p}")
