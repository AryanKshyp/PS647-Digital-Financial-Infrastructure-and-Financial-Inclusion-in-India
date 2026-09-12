#!/usr/bin/env python3
"""
Merge the PhonePe Pulse series into the existing analysis panel (D14/D15).

  output/panel_analysis.csv            33 states x FY2018-FY2023  (198 rows)
+ raw/phonepe_derived/phonepe_state_fy.csv
= output/panel_digital.csv             33 states x FY2019-FY2023  (165 rows)

FY2018 is lost: PhonePe's first complete financial year is fy_end=2019, because the
repo starts at calendar 2018Q1 and fy_end=2018 would need Apr-Dec 2017.

Denominator convention follows A4 unchanged -- per ADULT for stocks (a person either
has the thing or not), per CAPITA for money and transaction flows:

    registered users (stock, access-like) -> per adult
    transactions     (flow,  usage-like)  -> per capita
    value            (flow,  money)       -> per capita

The banking columns are copied across untouched, INCLUDING the min-max normalised
indicators and Access / Usage / AUG. Those were pooled over all 198 rows of the
six-year panel and are deliberately NOT recomputed on the 165: recomputing would
silently change the dependent variables and break comparability with the results
already reported (F5-F8). Consequence, harmless but worth stating: because the
minimum of most indicators falls in FY2018, the normalised columns no longer reach
exactly 0 in this file. Min-max is a monotone linear map, so the state and year
fixed effects absorb the difference.

Nothing in data/, raw/, or any existing output/ file is modified.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent   # this hypothesis folder
SHARED = ROOT_DIR.parent                            # ps647_final/: data/ and raw/ are shared

ROOT = ROOT_DIR
BANK = ROOT / "output/panel_analysis.csv"
PHONEPE = SHARED / "raw/phonepe_derived/phonepe_state_fy.csv"
OUT = ROOT / "output/panel_digital.csv"

YEARS = range(2019, 2024)


def main():
    bank = pd.read_csv(BANK)
    pp = pd.read_csv(PHONEPE)

    keep = ["state_key", "fy_end", "txn_count", "txn_amount_inr",
            "txn_count_p2p", "txn_count_retail", "txn_count_utility",
            "registered_users_31mar"]
    pp = pp[keep]

    # inner join. Both sides are already on state_key + fy_end, harmonised by the
    # same build_panel.state_key, so nothing should be dropped except by the window.
    n_bank_in_window = (bank.fy_end.isin(YEARS)).sum()
    df = bank.merge(pp, on=["state_key", "fy_end"], how="inner")
    df = df[df.fy_end.isin(YEARS)].sort_values(["state_key", "fy_end"]).reset_index(drop=True)

    assert len(df) == n_bank_in_window, (
        f"join lost rows: {len(df)} kept of {n_bank_in_window} banking rows in FY2019-23")

    adults = df.pop_18plus_000 * 1_000
    people = df.pop_total_000 * 1_000

    # --- digital variables ------------------------------------------------
    df["pp_users_per_adult"] = df.registered_users_31mar / adults
    df["pp_txns_per_capita"] = df.txn_count / people
    df["pp_value_per_capita"] = df.txn_amount_inr / people

    # payment intensity: rupees transacted per rupee of income. Dimensionless, so
    # it is comparable across states and years without deflating.
    df["pp_value_to_nsdp"] = df.pp_value_per_capita / df.nsdp_pc_rs

    # mean ticket size, a diagnostic rather than a regressor
    df["pp_ticket_size_rs"] = df.txn_amount_inr / df.txn_count

    # logs: all three grow roughly exponentially (26x over five years), so the
    # level and the log are very different regressors. Both are written; which one
    # is used is a specification decision, not a data decision.
    for c in ("pp_users_per_adult", "pp_txns_per_capita", "pp_value_per_capita"):
        df["ln_" + c] = np.log(df[c])

    # --- assertions -------------------------------------------------------
    assert df.state_key.nunique() == 33, f"{df.state_key.nunique()} states, expected 33"
    assert sorted(df.fy_end.unique()) == list(YEARS), "wrong years"
    assert len(df) == 33 * 5 == 165, f"{len(df)} rows, expected 165"
    assert not df.isna().any().any(), f"nulls: {df.columns[df.isna().any()].tolist()}"

    raw_pp = ["txn_count", "txn_amount_inr", "registered_users_31mar"]
    assert (df[raw_pp] > 0).all().all(), "non-positive PhonePe values"

    # banking columns must be byte-identical to what the earlier track used
    chk = bank[bank.fy_end.isin(YEARS)].sort_values(["state_key", "fy_end"]).reset_index(drop=True)
    for c in bank.columns:
        assert df[c].equals(chk[c]), f"banking column {c} changed during the merge"

    # the merge must not have crossed states: PhonePe's own Maharashtra FY2023 total
    m = df[(df.state_key == "MAHARASHTRA") & (df.fy_end == 2023)].iloc[0]
    src = pd.read_csv(PHONEPE)
    s = src[(src.state_key == "MAHARASHTRA") & (src.fy_end == 2023)].iloc[0]
    assert m.txn_count == s.txn_count and m.txn_amount_inr == s.txn_amount_inr, \
        "Maharashtra row does not match the source file"

    # ticket size sanity: a real payment, not paise and not crore
    assert 200 < df.pp_ticket_size_rs.min() and df.pp_ticket_size_rs.max() < 20_000, \
        f"implausible ticket size range {df.pp_ticket_size_rs.min():.0f}-{df.pp_ticket_size_rs.max():.0f}"

    df.to_csv(OUT, index=False)

    print(f"{OUT.relative_to(ROOT)}  ->  {len(df)} rows x {df.shape[1]} cols  "
          f"(33 states x FY2019-FY2023)\n")
    cols = ["pp_users_per_adult", "pp_txns_per_capita", "pp_value_per_capita",
            "pp_value_to_nsdp", "pp_ticket_size_rs"]
    print(df[cols].describe().loc[["mean", "std", "min", "max"]].T.to_string(
        float_format=lambda v: f"{v:,.3f}"))

    print("\nall-India-ish means by year (unweighted across states):")
    g = df.groupby("fy_end")[["pp_users_per_adult", "pp_txns_per_capita",
                              "pp_value_per_capita", "branches_per_lakh_adults"]].mean()
    print(g.to_string(float_format=lambda v: f"{v:,.3f}"))

    print("\nwithin-state share of total variation (xtsum convention):")
    for c in cols[:4] + ["ln_pp_txns_per_capita", "ln_pp_value_per_capita",
                         "ln_pp_users_per_adult", "branches_per_lakh_adults",
                         "atms_per_lakh_adults"]:
        v = df[c]
        w = v - v.groupby(df.state_key).transform("mean")
        print(f"   {c:28s} {w.std() / v.std():6.1%}")


if __name__ == "__main__":
    sys.exit(main())
