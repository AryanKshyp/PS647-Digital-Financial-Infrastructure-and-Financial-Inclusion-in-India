#!/usr/bin/env python3
"""
Turn the raw DBIE pull (scripts/fetch_bsr_dbie.py) of quarterly BSR-1
Table 1.3 into (a) one end-March XLSX per year and (b) a tidy long panel.

Source table: "Table No 1.3 Outstanding credit of scheduled commercial banks
according to state", Quarterly BSR-1, DBIE reportId 943 / SAP CUID
AXv_x9VyU2RPgSKw_n0gDwc / SI_ID 664696.  Coverage 31-Mar-2014 .. 30-Jun-2026.
Scheduled commercial banks EXCLUDING regional rural banks; place of
utilisation of credit.

Columns in the source flow:
  Reporting Date | Key Description 1 (region) | Key Description 2 (state/UT)
  No of Offices | No of Accounts | Credit Limit (Rs) | Amount Outstanding (Rs)
"""

import json
import os

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "raw", "bsr_accounts")
SRC = os.path.join(OUT, "bsr1_quarterly_state_credit_excl_rrb_long.csv")
YEARS = range(2018, 2025)          # end-March 2018 .. end-March 2024


def main():
    d = pd.read_csv(SRC)
    d["reporting_date"] = d["Reporting Date"].str[:10].str.replace("/", "-", regex=False)
    d = d.rename(columns={"Key Description 1": "region",
                          "Key Description 2": "state",
                          "No of Offices": "n_offices",
                          "No of Accounts": "n_credit_accounts",
                          "Credit Limit": "credit_limit_rs",
                          "Amount Outstanding": "amount_outstanding_rs"})
    keep = ["reporting_date", "region", "state", "n_offices", "n_credit_accounts",
            "credit_limit_rs", "amount_outstanding_rs"]
    d = d[keep].sort_values(["reporting_date", "region", "state"])

    d.to_csv(os.path.join(OUT, "bsr1_state_credit_accounts_all_quarters_2014_2026.csv"),
             index=False)

    panel = []
    for y in YEARS:
        day = f"{y}-03-31"
        sub = d[d.reporting_date == day].copy()
        assert len(sub) > 30, (day, len(sub))
        sub["year_end_march"] = y
        path = os.path.join(OUT, f"bsr1_state_credit_accounts_mar{y}.xlsx")
        with pd.ExcelWriter(path, engine="openpyxl") as w:
            sub.to_excel(w, sheet_name=f"Mar{y}", index=False)
        panel.append(sub)
        print(f"{day}: {len(sub)} states/UTs, "
              f"{sub.n_credit_accounts.sum():,} accounts, "
              f"Rs {sub.amount_outstanding_rs.sum()/1e7:,.0f} crore -> {os.path.basename(path)}")

    p = pd.concat(panel)[["year_end_march", "reporting_date", "region", "state",
                          "n_offices", "n_credit_accounts", "credit_limit_rs",
                          "amount_outstanding_rs"]]
    p.to_csv(os.path.join(OUT, "bsr1_state_credit_accounts_FY2018_FY2024_long.csv"),
             index=False)
    print("panel rows:", len(p), "states:", p.state.nunique())


if __name__ == "__main__":
    main()
