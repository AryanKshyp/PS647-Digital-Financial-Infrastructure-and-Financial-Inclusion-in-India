# Quarterly BSR-7 / "Statement No. 3A" — what is here and why

## What Statement 3A is

"Quarterly Statistics on Deposits and Credit of Scheduled Commercial Banks",
**Statement No. 3A: State-wise Number of Reporting Offices, Aggregate Deposit and Bank
Credit of SCBs**. It carries three variables per state: reporting offices, aggregate
deposits (₹ crore), bank credit (₹ crore). **It does not carry account counts** — those
live in BSR-1 / BSR-2 (see `../bsr_accounts/`).

## Why there are no raw Statement 3A files here

RBI's landing page
<https://rbi.org.in/Scripts/QuarterlyPublications.aspx?head=Quarterly+Statistics+on+Deposits+and+Credit+of+Scheduled+Commercial+Banks>
still lists every quarter from 1998 to 2023, but every statement link points at the old
`https://dbie.rbi.org.in/DBIE/dbie.rbi?site=publicOpenDocument&sIDType=CUID&iDocID=...`
viewer. `dbie.rbi.org.in` now 302-redirects to the Angular SPA at `data.rbi.org.in`, so
none of those links resolve to a file any more. Quarters from March 2023 onward are only in
the new portal. Direct portal URLs for Statement 3A are listed in
`../bsr_accounts/MANUAL_STEPS.md`.

## What is here instead — the same three variables, annual, 2004–2025

RBI's *Handbook of Statistics on Indian States* republishes exactly these series as static
XLSX, sourced from the Basic Statistical Returns. Downloaded
2026-09-08 from <https://rbi.org.in/Scripts/AnnualPublications.aspx?head=Handbook+of+Statistics+on+Indian+States>:

| File | RBI table | Content | Coverage |
|---|---|---|---|
| `hbstates_T152_statewise_offices_of_SCBs.xlsx` | Table 152 | State-wise distribution of offices of SCBs (number of offices) | 2004–2025, two sheets (2004–14, 2015–25) |
| `hbstates_T155_statewise_deposits_of_SCBs.xlsx` | Table 155 | State-wise deposits by SCBs, ₹ crore, as at end-March | 2004–2025 |
| `hbstates_T156_statewise_credit_of_SCBs.xlsx` | Table 156 | State-wise credit by SCBs, ₹ crore, as at end-March | 2004–2025 |
| `hbstates_T153_statewise_CD_ratio_place_of_sanction.xlsx` | Table 153 | Credit–deposit ratio, place of sanction | 2004–2025 |
| `hbstates_T154_statewise_CD_ratio_place_of_utilisation.xlsx` | Table 154 | Credit–deposit ratio, place of utilisation | 2004–2025 |

Direct file URLs (they carry a build hash and change with each Handbook edition):

```
https://rbidocs.rbi.org.in/rdocs/Publications/DOCs/152T_1112202512B2BF0FBDB74FF48CF835E2A6B7C592.XLSX
https://rbidocs.rbi.org.in/rdocs/Publications/DOCs/153T_111220255DEA2A2D23744132BFEDD5768D038648.XLSX
https://rbidocs.rbi.org.in/rdocs/Publications/DOCs/154T_111220253A00C718ED584E7C850BBCAC3B2FA18B.XLSX
https://rbidocs.rbi.org.in/rdocs/Publications/DOCs/155T_11122025BC88547570414295AB088FBCF5C90806.XLSX
https://rbidocs.rbi.org.in/rdocs/Publications/DOCs/156T_1112202520771561966C49F1B9C00F56ACF97557.XLSX
```

Sheet layout: row with `Region/State/Union Territory` is the header; year columns follow;
last data row is `ALL INDIA`; footnotes state `Source: Basic Statistical Returns of
Scheduled Commercial Banks in India` and that figures from 2020 onward follow a revised
state classification.

All-India values, end-March (₹ crore / count):

| | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|---|
| Offices | 141,909 | 145,374 | 153,102 | 154,485 | 154,758 | 158,642 | 163,216 |
| Deposits | 11,434,451 | 12,639,009 | 13,748,655 | 15,443,510 | 17,008,795 | 18,742,311 | 21,253,358 |
| Credit | 8,766,973 | 9,897,595 | 10,518,812 | 11,078,050 | 12,258,748 | 14,198,006 | 16,913,694 |

**Note:** `../handbook_states/` already holds the same five Handbook tables scraped to CSV
in an earlier pass. These XLSX copies are the originals as published; use whichever is
more convenient, but do not treat them as two independent sources.

**Difference from true Statement 3A:** the Handbook is annual (end-March only) and
excludes the intra-year quarters. If the panel only needs end-March values — which is the
case for an FY2018–FY2024 state panel — it is a complete substitute.
