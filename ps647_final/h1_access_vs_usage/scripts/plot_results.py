#!/usr/bin/env python3
"""Coefficient plot across both tracks. Writes output/fig2_coefficients.png"""
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent

OUT = ROOT_DIR / "output"
t3 = pd.read_csv(OUT / "table3_main_results.csv")
t6 = pd.read_csv(OUT / "table6_long_results.csv")
t8 = pd.read_csv(OUT / "table8_long_robustness.csv")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.5, 5.4))

# ---- left: all coefficients, both tracks ----
rows = []
for lab, df, reg in [("6-yr · branches", t3, "branches_per_lakh_adults"),
                     ("6-yr · ATMs", t3, "atms_per_lakh_adults"),
                     ("12-yr · branches", t6, "branches_per_lakh_adults")]:
    for eq in ["Access", "Usage", "AUG"]:
        r = df[(df.dependent == eq) & (df.regressor == reg)].iloc[0]
        rows.append((f"{eq}\n{lab}", r.coef, r.ci_lo, r.ci_hi, r.p))
rows = rows[::-1]
y = range(len(rows))
cols = ["#dc2626" if p < .05 else "#f59e0b" if p < .10 else "#94a3b8" for *_, p in rows]
for i, (lab, c, lo, hi, p) in zip(y, rows):
    ax1.plot([lo, hi], [i, i], color=cols[i], lw=2.4, solid_capstyle="round")
    ax1.plot(c, i, "o", color=cols[i], ms=7, zorder=3)
ax1.axvline(0, color="black", lw=1, ls="--", alpha=.7)
ax1.set_yticks(list(y)); ax1.set_yticklabels([r[0] for r in rows], fontsize=8)
ax1.set_xlabel("coefficient (95% CI)")
ax1.set_title("Coefficients, both tracks\nred p<0.05 · amber p<0.10 · grey n.s.",
              fontsize=11, loc="left")
ax1.grid(axis="x", alpha=.25)

# ---- right: AUG on branches across the four specifications ----
aug = [
    ("6-yr", t3[(t3.dependent == "AUG") & (t3.regressor == "branches_per_lakh_adults")].iloc[0]),
    ("6-yr\ntrimmed", pd.read_csv(OUT/"table5_robustness.csv").query(
        "spec=='d7_trimmed' and dependent=='AUG' and regressor=='branches_per_lakh_adults'").iloc[0]),
    ("12-yr", t6[(t6.dependent == "AUG") & (t6.regressor == "branches_per_lakh_adults")].iloc[0]),
    ("12-yr\ntrimmed", t8.query(
        "spec=='long_12yr_d7trim' and dependent=='AUG' and regressor=='branches_per_lakh_adults'").iloc[0]),
]
xs = range(len(aug))
for i, (lab, r) in zip(xs, aug):
    c = "#f59e0b" if r.p < .10 else "#94a3b8"
    ax2.plot([i, i], [r.ci_lo, r.ci_hi], color=c, lw=2.6, solid_capstyle="round")
    ax2.plot(i, r.coef, "o", color=c, ms=8, zorder=3)
    ax2.annotate(f"p={r.p:.3f}", (i, r.ci_hi), textcoords="offset points",
                 xytext=(0, 7), ha="center", fontsize=9)
ax2.axhline(0, color="black", lw=1, ls="--", alpha=.7)
ax2.set_xticks(list(xs)); ax2.set_xticklabels([a[0] for a in aug], fontsize=9)
ax2.set_ylabel("coefficient on branches (95% CI)")
ax2.set_title("AUG equation: the access–usage gap\npositive in all four, never below p=0.084",
              fontsize=11, loc="left")
ax2.grid(axis="y", alpha=.25)

fig.tight_layout()
fig.savefig(OUT / "fig2_coefficients.png", dpi=150)
print(f"  -> {OUT/'fig2_coefficients.png'}")
