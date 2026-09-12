#!/usr/bin/env python3
"""
Stamp a single canonical year column, `fy_end`, onto every file in data/.

`fy_end` = the calendar year of the 31 March the row refers to.
So fy_end=2018 means "as at 31 March 2018", i.e. the close of financial year 2017-18.

The sources disagree on how they label that same instant:

  file                     native column   native label   fy_end
  01/05/06 (RBI Handbook)  year_label      2018           2018    (already end-March)
  02 (ATMs)                year            2018           2018    (already end-March)
  03 (loan accounts)       year            2018           2018    (already end-March)
  04 (deposit accounts)    march_year      2018           2018    (already end-March)
  07 (income / NSDP)       year_label      2017-18        2018    <-- the only conversion
  08 (adult population)    year            2018           2018    (1 March 2018)

Only the income file uses financial-year notation, and it is the one that would
silently introduce a one-year offset. The native column is left untouched so the
original label stays auditable; `fy_end` is added alongside it.

Idempotent: re-running overwrites `fy_end` with the same values.
"""

import re
import sys
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent   # this hypothesis folder
SHARED = ROOT_DIR.parent                            # ps647_final/: data/ and raw/ are shared

DATA = SHARED / "data"

# file -> (native year column, how to read it)
SPEC = {
    "01_branches.csv":         ("year_label", "end_march"),
    "02_atms.csv":             ("year",       "end_march"),
    "03_loan_accounts.csv":    ("year",       "end_march"),
    "04_deposit_accounts.csv": ("march_year", "end_march"),
    "05_deposit_amounts.csv":  ("year_label", "end_march"),
    "06_loan_amounts.csv":     ("year_label", "end_march"),
    "07_income_per_person.csv": ("year_label", "fy_span"),
    "08_adult_population.csv": ("year",       "end_march"),
}

FY_SPAN = re.compile(r"^(\d{4})-(\d{2})$")


def to_fy_end(val, kind):
    s = str(val).strip()
    if kind == "end_march":
        return int(s) if s.isdigit() else None
    m = FY_SPAN.match(s)          # "2017-18" -> 2018
    if not m:
        return None
    start = int(m.group(1))
    end2 = int(m.group(2))
    # sanity: the second half must be the next year's last two digits
    if (start + 1) % 100 != end2:
        raise ValueError(f"unexpected financial-year label: {s!r}")
    return start + 1


def main():
    for fname, (col, kind) in SPEC.items():
        path = DATA / fname
        df = pd.read_csv(path)
        if col not in df.columns:
            print(f"  !! {fname}: no column {col!r}, skipped")
            continue

        df["fy_end"] = df[col].map(lambda v: to_fy_end(v, kind)).astype("Int64")

        # put fy_end immediately after the native column, so it reads naturally
        cols = [c for c in df.columns if c != "fy_end"]
        i = cols.index(col) + 1
        df = df[cols[:i] + ["fy_end"] + cols[i:]]

        df.to_csv(path, index=False)

        got = sorted(df["fy_end"].dropna().unique())
        in_window = [y for y in got if 2018 <= y <= 2023]
        nulls = int(df["fy_end"].isna().sum())
        flag = "" if len(in_window) == 6 else "   <-- CHECK"
        print(f"  {fname:26s} {col:11s} -> fy_end {got[0]}..{got[-1]}  "
              f"(panel yrs present: {len(in_window)}/6, unparsed: {nulls}){flag}")


if __name__ == "__main__":
    sys.exit(main())
