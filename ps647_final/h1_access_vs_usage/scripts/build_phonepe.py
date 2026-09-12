#!/usr/bin/env python3
"""
Build state-level PhonePe Pulse panels from the cloned repo (D14).

Source: raw/phonepe_pulse  (github.com/PhonePe/pulse, shallow clone)

Two things to know about the repo's own layout, both checked before writing this:

  * `aggregated/transaction/.../state/<state>/<y>/<q>.json` carries transaction
    COUNTS ONLY — the amount field has been stripped in the current release.
  * `map/transaction/hover/country/india/<y>/<q>.json` carries count AND amount
    for every state in one file. That is the source used for the value series.

So counts+amounts come from map/, the P2P / Retail / Utility split comes from
aggregated/, and registered users come from map/user/.

Financial-year convention matches the rest of the project (D9): fy_end = Y means
"year ending 31 March Y", i.e. calendar 2018Q2+Q3+Q4 and 2019Q1 give fy_end=2019.
  - transactions are FLOWS  -> summed over the four quarters
  - registered users is a STOCK (verified monotone) -> taken at Q1 of year Y,
    i.e. the value as at 31 March Y

Data begin 2018Q1, so the first complete financial year is fy_end=2019.

Nothing in data/ or raw/phonepe_pulse is modified. Outputs go to raw/phonepe_derived/.
"""

import json
import os
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_panel import state_key          # same harmoniser as the banking panel

ROOT_DIR = Path(__file__).resolve().parent.parent   # this hypothesis folder
SHARED = ROOT_DIR.parent                            # ps647_final/: data/ and raw/ are shared

ROOT = ROOT_DIR
PULSE = SHARED / "raw/phonepe_pulse/data"
OUT = SHARED / "raw/phonepe_derived"

QUARTERS = [(y, q) for y in range(2018, 2027) for q in (1, 2, 3, 4)]


def load_quarterly() -> pd.DataFrame:
    """One row per raw PhonePe state per calendar quarter."""
    rec = defaultdict(dict)

    for y, q in QUARTERS:
        f = PULSE / f"map/transaction/hover/country/india/{y}/{q}.json"
        if not f.exists():
            continue
        for x in json.loads(f.read_text())["data"]["hoverDataList"]:
            m = x["metric"][0]
            rec[(x["name"], y, q)].update(
                txn_count=m["count"], txn_amount_inr=m.get("amount")
            )

        f = PULSE / f"map/user/hover/country/india/{y}/{q}.json"
        if f.exists():
            for s, v in json.loads(f.read_text())["data"]["hoverData"].items():
                rec[(s, y, q)]["registered_users"] = v["registeredCount"]

    # category split: P2P / Retail / Utility, counts only
    for d in (PULSE / "aggregated/transaction/country/india/state").iterdir():
        for yd in d.iterdir():
            for f in yd.iterdir():
                y, q = int(yd.name), int(f.stem)
                # aggregated/ uses hyphenated dir names, map/ uses spaced names
                name = d.name.replace("-", " ").replace(" & ", " & ")
                for x in json.loads(f.read_text())["data"]["transactionData"]:
                    col = "txn_count_" + x["name"].lower().replace(" ", "_")
                    rec[(name, y, q)][col] = x["paymentInstruments"][0]["count"]

    rows = [dict(raw_state=s, year=y, quarter=q, **v) for (s, y, q), v in rec.items()]
    df = pd.DataFrame(rows).sort_values(["raw_state", "year", "quarter"])
    for c in ("txn_count_p2p", "txn_count_retail", "txn_count_utility"):
        if c in df:
            df[c] = df[c].fillna(0)     # a state-quarter with no such transactions
    return df.reset_index(drop=True)


def to_financial_year(q: pd.DataFrame) -> pd.DataFrame:
    """Calendar quarters -> fy_end, with the project's D1/D2 state harmonisation."""
    q = q.copy()
    # Apr-Dec of year Y-1 and Jan-Mar of year Y both belong to fy_end = Y
    q["fy_end"] = q["year"] + (q["quarter"] >= 2).astype(int)
    q["state_key"] = q["raw_state"].map(state_key)

    flows = ["txn_count", "txn_amount_inr",
             "txn_count_p2p", "txn_count_retail", "txn_count_utility"]
    flows = [c for c in flows if c in q]

    fy = q.groupby(["state_key", "fy_end"], as_index=False).agg(
        **{c: (c, "sum") for c in flows},
        quarters_used=("quarter", "nunique"),   # nunique, not size:
        # J&K and Ladakh are two raw rows that fold into one state_key (D2),
        # so "size" would report 8 quarters for that unit and drop it entirely.
    )

    # stock: registered users as at 31 March fy_end == calendar Q1 of that year
    stock = (q[q["quarter"] == 1]
             .groupby(["state_key", "year"], as_index=False)["registered_users"].sum()
             .rename(columns={"year": "fy_end",
                              "registered_users": "registered_users_31mar"}))

    fy = fy.merge(stock, on=["state_key", "fy_end"], how="left")
    # drop the two part-years at the ends (fy_end=2018 has only Jan-Mar 2018,
    # the last fy_end has only the quarters published so far)
    fy = fy[fy["quarters_used"] == 4].reset_index(drop=True)
    return fy


def main():
    OUT.mkdir(exist_ok=True)

    qtr = load_quarterly()
    qtr.to_csv(OUT / "phonepe_state_quarterly.csv", index=False)

    fy = to_financial_year(qtr)
    fy.to_csv(OUT / "phonepe_state_fy.csv", index=False)

    panel = fy[fy["fy_end"].between(2019, 2023)].reset_index(drop=True)
    panel.to_csv(OUT / "phonepe_state_fy2019_fy2023.csv", index=False)

    # ---- assertions ----------------------------------------------------
    assert qtr[["txn_count", "txn_amount_inr", "registered_users"]].notna().all().all(), \
        "missing count/amount/users in the quarterly build"
    assert (qtr.groupby(["year", "quarter"]).size() == 36).all(), "not 36 states every quarter"
    # J&K + Ladakh must have been summed, not duplicated (D2)
    assert "LADAKH" not in set(fy["state_key"]), "Ladakh not folded into J&K"
    n_states = fy["state_key"].nunique()
    assert n_states == 35, f"expected 35 harmonised units, got {n_states}"
    for name, d in (("full FY", fy), ("panel window", panel)):
        yrs = sorted(d["fy_end"].unique())
        assert len(d) == n_states * len(yrs), f"{name} not rectangular"

    print(f"quarterly : {len(qtr):5d} rows  "
          f"{qtr['year'].min()}Q{qtr[qtr.year==qtr.year.min()].quarter.min()}"
          f"–{qtr['year'].max()}Q{qtr[qtr.year==qtr.year.max()].quarter.max()}"
          f"  ({qtr['raw_state'].nunique()} raw states)")
    print(f"financial : {len(fy):5d} rows  fy_end {fy.fy_end.min()}–{fy.fy_end.max()}"
          f"  ({n_states} harmonised units)")
    print(f"panel     : {len(panel):5d} rows  fy_end 2019–2023")
    print()
    mh = panel[panel.state_key == "MAHARASHTRA"]
    print("Maharashtra:")
    for _, r in mh.iterrows():
        print(f"   fy{int(r.fy_end)}  txns {r.txn_count/1e6:9.1f}m   "
              f"value ₹{r.txn_amount_inr/1e12:7.2f} lakh cr   "
              f"users {r.registered_users_31mar/1e6:6.2f}m")


if __name__ == "__main__":
    sys.exit(main())
