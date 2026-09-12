# BSR account-count data — sources, coverage, validation

Target: state-wise **number of deposit accounts** (BSR-2) and **number of credit/loan
accounts** (BSR-1) of Scheduled Commercial Banks, end-March 2018 … end-March 2024.

## 1. Status — COMPLETE for FY2018–FY2024

| Variable | Years | Source |
|---|---|---|
| Number of **credit** accounts, state-wise | Mar-2018 … Mar-2024 (series runs Mar-2014 → Jun-2026) | RBI DBIE, **quarterly BSR-1 Table 1.3**, *excluding* RRBs |
| Number of **deposit** accounts, state-wise | Mar-2019 … Mar-2024 (series runs to Mar-2026) | RBI DBIE, **annual BSR-2 Table 2.3**, *including* RRBs |
| Number of **deposit** accounts, Mar-2018 only | Mar-2018 | India Data Portal redistribution of RBI BSR-2 (DBIE's own Table 2.3 starts at Mar-2019) |

`PANEL_state_year_accounts_FY2018_FY2024.csv` is the ready-to-use output: **35 states/UTs
× 7 years = 245 rows, no missing cells** in either account-count column.

## 2. Files

### A. Pulled directly from RBI's DBIE/CIMS portal (`https://data.rbi.org.in`)

Fetched with `../../scripts/fetch_bsr_dbie.py`; see `DBIE_ACCESS_NOTES.md` for the protocol.

| File | Report | Content |
|---|---|---|
| `bsr1_quarterly_state_credit_excl_rrb_long.csv` (+ `_raw.json`) | DBIE report **943**, Quarterly BSR-1 Table 1.3 "Outstanding credit of SCBs according to state" | `Time Date, Sorting Order, No of Offices, Key Description 1 (region), Key Description 2 (state), No of Accounts, Credit Limit, Amount Outstanding`. 1,728 rows, 48 quarters Mar-2014 → Jun-2026, 38 state/UT labels. Amounts in **rupees**. |
| `bsr2_annual_state_deposits_incl_rrb_long.csv` (+ `_raw.json`) | DBIE report **853**, Annual BSR-2 Table 2.3 "Deposits of SCBs according to State/UT" | Warehouse-style layout: `Quarter Date`, `Dimension 1` = state/region/ALL-INDIA, `Measure 1…15`. 348 rows, Mar-2019 → Mar-2026. |
| `bsr1_annual_state_credit_incl_rrb_long.csv` (+ `_raw.json`) | Annual BSR-1, state-wise, **including** RRBs | Only 42 rows, reporting date **Mar-2026 only** — DBIE keeps a single vintage of the annual BSR-1 state table, so it cannot supply FY2018–FY2024. Kept for reference. |
| `bsr2_quarterly_state_deposits_excl_rrb_long.csv` (+ `_raw.json`) | Quarterly BSR-2 Table 2.3, *excluding* RRBs | Mar-2023 → Mar-2026 only. Alternative to the annual file if an excl-RRB deposit universe is wanted, but too short for this panel. |
| `bsr1_state_credit_accounts_mar2018.xlsx` … `mar2024.xlsx`, `bsr1_state_credit_accounts_FY2018_FY2024_long.csv`, `bsr1_state_credit_accounts_all_quarters_2014_2026.csv` | same report 943, tidied | One workbook per March year (36 states/UTs: `n_offices`, `n_credit_accounts`, `credit_limit_rs`, `amount_outstanding_rs`), plus long-format 252-row and 1,728-row versions. These keep Ladakh separate from J&K, unlike `PANEL_…csv`. |
| `econsurvey2024-25_tab33_state_deposit_credit_AMOUNTS.xlsx` | Economic Survey Table 3.3 | Checked as a possible account-count source — it is **amounts only**. Retained as an independent cross-check of the amount columns. |
| `bsr1_credit_accounts_SOURCE.json`, `SOURCE_MANIFEST.json` | — | Provenance records for the DBIE pulls. |

**Measure layout of the BSR-2 file (decoded and verified):**

| Year | Columns present | Meaning |
|---|---|---|
| 2019, 2020, 2024, 2025, 2026 | M1…M9 | M1 offices; M2/M3 current a/c count & amount; M4/M5 savings; M6/M7 term; **M8/M9 total count & amount** |
| 2021, 2022, 2023 | M1…M7 only | no total columns — **total = M2+M4+M6** (accounts) and **M3+M5+M7** (amount) |

Additivity checked exactly (max |M2+M4+M6 − M8| = 0 for 2019). Amounts are in **rupees**.
`Dimension 1` mixes states with the six region aggregates and `ALL-INDIA` — filter those out
before summing.

### B. India Data Portal redistribution of RBI BSR (fills Mar-2018 deposits; independent cross-check elsewhere)

Publisher: India Data Portal, Bharti Institute of Public Policy, ISB. Underlying source is
RBI BSR-1 / BSR-2. Cite RBI as the source and IDP as the access route.

| File | Source URL | Content |
|---|---|---|
| `idp_bsr2_deposits_bankgroup_district_2009_2017.csv` | https://ckan.indiadataportal.com/dataset/eb565ca6-aa06-47fd-9c81-05c7ed6c538b/resource/3d6dc991-9a60-47d6-b107-2e2536688e5e/download/bankgroup-wise-deposits.csv | BSR-2 district × bank group × population group. 51,579 rows. **The `year` column is one behind the reference date — `year=2017` is as-at 31-Mar-2018** (proved in §3). `number_of_deposits` is in **thousands of accounts**; `deposits` in ₹ crore. |
| `idp_bsr2_deposits_populationgroup_district_2019_2022.csv` | https://ckan.indiadataportal.com/dataset/eb565ca6-aa06-47fd-9c81-05c7ed6c538b/resource/991a33ab-67c0-4748-9ded-012f449497be/download/populationgroup-wise-deposits.csv | BSR-2 district × population group, Mar-2019 … Mar-2022 (year labels correct here). `no_of_offices, no_of_accounts` (thousands), `deposit_amount` (₹ crore). |
| `idp_bsr1_credit_district_2010_2023.csv` (227 MB) | https://ckan.indiadataportal.com/dataset/eb565ca6-aa06-47fd-9c81-05c7ed6c538b/resource/fe227e6c-cd04-43a8-8559-334c4f766ade/download/credit-by-scheduled-commercial-banks.csv | BSR-1 district × population group × bank group × occupation, Mar-2010 … Mar-2023. 1,715,987 rows. `no_of_accounts` is an **actual count**; `credit_limit`/`amount_outstanding` in ₹ crore. Bank groups include **RRBs and Small Finance Banks**, so this is the *including-RRB* universe — useful as a cross-check on, not a substitute for, the DBIE quarterly (excl-RRB) credit series. No total/subtotal rows, so summing is safe. |

### C. Derived panels

| File | Content |
|---|---|
| **`PANEL_state_year_accounts_FY2018_FY2024.csv`** | `march_year, state_key, no_of_credit_accounts, credit_outstanding_rs_crore, credit_offices, credit_src, no_of_deposit_accounts, deposit_amount_rs_crore, no_of_offices, deposit_src`. 35 states × 2018–2024. Region/ALL-INDIA rows removed, state names normalised, **Jammu & Kashmir + Ladakh merged**, amounts converted to ₹ crore, deposit accounts converted to actual counts. |
| `derived_state_year_credit_accounts_2010_2023.csv` | state × year from the IDP credit file (incl RRBs), 2010–2023. |
| `derived_state_year_DEPOSIT_accounts_mar2018_mar2022.csv` | state × year from the two IDP deposit files, Mar-2018 … Mar-2022 (accounts in **thousands**). |
| `derived_state_year_deposit_accounts_2010_2018.csv` | full IDP bank-group deposit series, year label corrected to the end-March reference year. |

## 3. Validation

All-India totals against RBI's *Handbook of Statistics on Indian States* Tables 155/156
(files in `../bsr_3a/`), ₹ crore:

| End-March | Handbook deposits | Panel deposits | Handbook credit (incl RRB) | Panel credit (excl RRB) |
|---|---|---|---|---|
| 2018 | 11,434,451 | 11,434,450 | 8,766,973 | 8,511,720 |
| 2019 | 12,639,009 | 12,639,010 | 9,897,595 | 9,613,101 |
| 2020 | 13,748,655 | 13,748,660 | 10,518,812 | 10,217,760 |
| 2021 | 15,443,510 | 15,443,510 | 11,078,050 | 10,738,440 |
| 2022 | 17,008,795 | 17,008,800 | 12,258,748 | 11,886,682 |
| 2023 | 18,742,311 | 18,742,310 | 14,198,006 | 13,778,419 |
| 2024 | 21,253,358 | 21,253,360 | 16,913,694 | 16,434,164 |

Deposits reconcile to the rupee. Credit sits ~3 % below the Handbook in every year — exactly
as expected, because the quarterly BSR-1 excludes Regional Rural Banks while the Handbook
includes them. The IDP credit file (incl RRBs) matches the Handbook to <0.01 % for
2018–2023, which independently confirms both the DBIE extract and the RRB explanation.

The Mar-2018 deposit row's exact match (11,434,450 vs 11,434,451) is what proves the
one-year offset in the IDP bank-group file's `year` column.

Account-count magnitudes: credit 17.2 crore (2018) → 37.3 crore (2024); deposits 191 crore
(2018) → 265 crore (2024). Implied average balances (₹3.9 lakh per loan account, ₹80k per
deposit account in 2024) are sensible.

## 4. Definitions and caveats

* **Universe differs between the two variables.** Deposit accounts include RRBs; credit
  accounts exclude them. If a like-for-like universe matters, either use the IDP credit
  series (incl RRBs, but only to FY2023) or state the difference.
* **Reference date** is 31 March in every case — the March quarter was selected from the
  quarterly credit file.
* **Jammu & Kashmir + Ladakh are merged in the panel.** They must be: the IDP deposit data
  reports Ladakh as exactly zero for Mar-2019 (its figures still inside J&K) while being
  non-zero for Mar-2018 and Mar-2020 onward. DBIE reports them separately from Mar-2019.
* **Dadra & Nagar Haveli and Daman & Diu** are separate rows in the Mar-2018 IDP source and
  merged from Mar-2020; the panel merges them in all years.
* `NCT OF DELHI` (DBIE) is normalised to `delhi`; other spelling fixes: `Andman and
  Nocobar Islands` → Andaman & Nicobar, `Uttrakhand` → Uttarakhand.
* The DBIE credit table is BSR-1 Table 1.3, which RBI compiles by **place of utilisation**.
  The IDP credit extract does not label its basis — check before mixing the two.

## 5. If the series need extending or re-pulling

`../../scripts/fetch_bsr_dbie.py` re-runs the DBIE extraction; `DBIE_ACCESS_NOTES.md`
documents the gateway protocol, the AES parameters, the required call ordering and the
report-id / OpenDocument-CUID inventory. `MANUAL_STEPS.md` covers the browser fallback.
