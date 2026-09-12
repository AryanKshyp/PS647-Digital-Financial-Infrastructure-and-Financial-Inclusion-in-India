#!/usr/bin/env python3
"""
STEP 7 — Robustness per D7.

Re-run all three equations dropping the two suspect deposit-account cells that fall inside
the FY2018-FY2023 window (A6, confirmed empirically in F3):
    DELHI 2023, CHANDIGARH 2023
Delhi 2024 and Haryana 2024 lie outside the panel and need no action.
Goa, and Chandigarh 2018-2022, are high but flat -- genuine levels, NOT dropped.

Writes output/table5_robustness.csv
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from estimate import run, X

ROOT_DIR = Path(__file__).resolve().parent.parent

OUT = ROOT_DIR / "output"
DROP_CELLS = [("DELHI", 2023), ("CHANDIGARH", 2023)]


def main() -> int:
    panel = pd.read_csv(OUT / "panel_analysis.csv")
    mask = panel.apply(lambda r: (r.state_key, r.fy_end) in DROP_CELLS, axis=1)
    print(f"  dropping {int(mask.sum())} cells: " + ", ".join(f"{s} {y}" for s, y in DROP_CELLS))
    trimmed = panel[~mask]

    res_m, tbl_m = run(panel, "main")
    res_r, tbl_r = run(trimmed, "d7_trimmed")

    print(f"\n  N: main {len(panel)}  ->  trimmed {len(trimmed)}\n")
    print(f"  {'equation':12s} {'regressor':28s} {'main coef':>11s} {'p':>7s} "
          f"{'trimmed coef':>13s} {'p':>7s}  {'shift':>9s}")
    print("  " + "-" * 92)
    for eq, y in [("(1) Access", "Access"), ("(2) Usage", "Usage"), ("(3) AUG", "AUG")]:
        for v in X[:2]:
            cm, pm = res_m[y].params[v], res_m[y].pvalues[v]
            cr, pr = res_r[y].params[v], res_r[y].pvalues[v]
            flip = "  SIGN FLIP" if cm * cr < 0 else ""
            sigch = "  SIG CHANGE" if (pm < .05) != (pr < .05) else ""
            print(f"  {eq:12s} {v:28s} {cm:11.5f} {pm:7.3f} {cr:13.5f} {pr:7.3f} "
                  f"{100*(cr-cm)/abs(cm):8.1f}%{flip}{sigch}")

    out = pd.concat([tbl_m, tbl_r], ignore_index=True)
    out.to_csv(OUT / "table5_robustness.csv", index=False)
    print(f"\n  -> {OUT/'table5_robustness.csv'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
