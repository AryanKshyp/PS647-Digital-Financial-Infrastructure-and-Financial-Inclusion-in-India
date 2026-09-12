# data/ — the 8 files the analysis uses

Copies of the source files, renamed for clarity. Originals stay in `../raw/` untouched.

Panel: **33 states × FY2018–FY2023 = 198 rows**, no missing data.

| File | What it gives | Column to use |
|---|---|---|
| `01_branches.csv` | bank branches per state | `value` |
| `02_atms.csv` | ATMs per state | `atms` |
| `03_loan_accounts.csv` | number of loan accounts | `no_of_credit_accounts` |
| `04_deposit_accounts.csv` | number of deposit accounts | `no_of_deposit_accounts` |
| `05_deposit_amounts.csv` | money deposited (₹ crore) | `value` |
| `06_loan_amounts.csv` | money lent (₹ crore) | `value` |
| `07_income_per_person.csv` | income per person (₹) | `value` |
| `08_adult_population.csv` | adults 18+ (thousands) | `pop_18plus_000` |

**Every file has a `fy_end` column** — the calendar year of the 31 March it refers to.
`fy_end=2018` means *as at 31 March 2018*. Merge and filter on this, and use it as the year fixed effect.

**These are unfiltered.** They still hold all years and all states as published — filter to
`fy_end` 2018–2023 and the 33 states when you merge.

## Four things to get right when merging

1. **Take only the named column.** Files 03 and 04 also carry rupee amounts — ignore those, use 05/06
   instead. Mixing them breaks comparability.
2. **Year labels differ — already solved.** File 07 labels 31 March 2018 as `2017-18`; the others call it
   `2018`. The `fy_end` column reconciles all of them, so **join on `fy_end`, never on the native
   `year_label` / `year` / `march_year` columns** (those are kept only for provenance).
3. **Merge states before dividing.** Add Jammu & Kashmir + Ladakh together, and Dadra & Nagar Haveli +
   Daman + Diu together, in *every* year. Sum the raw counts first, then compute per-adult ratios.
4. **Drop two units:** Lakshadweep, and the merged Dadra & Nagar Haveli / Daman & Diu (no income data).
   Also drop the region rows (`NORTHERN REGION` etc.) and `ALL-INDIA` where they appear.

## Known issue

`04_deposit_accounts.csv` has bad values for **Delhi 2023, Haryana 2024, Chandigarh 2023** — RBI's own
data, not our extraction. Haryana/Delhi 2024 fall outside the panel anyway; Delhi 2023 and Chandigarh 2023
are inside it. Plan is to run with them, then re-run without and compare (`../h1_access_vs_usage/DECISIONS.md` D7).

## Digital data lives elsewhere

PhonePe Pulse (added later, D14) is **not** in this folder — it is built by script from a cloned
repo into `../raw/phonepe_derived/`. Merge it with `../h1_access_vs_usage/scripts/merge_phonepe.py`, which produces
`../h1_access_vs_usage/output/panel_digital.csv` (33 states × FY2019–FY2023). Details: `../data_fetching.md` §10.

## Digital-literacy moderators (H5)

`09_diglit.csv` — 33 states × 16 columns, built by `../h5_conversion_capacity/scripts/build_moderators.py`. Holds the H5
conversion-capacity moderators and the placebo controls:

| Column | What it is | Source |
|---|---|---|
| `diglit_w`, `diglit_m` | % who have ever used the internet | NFHS-5 (2019-21) state fact sheets |
| `nss75_computer`, `nss75_internet` | % age 5+ able to operate a computer / use the internet | NSS 75th round (2017-18) — **22 states only** |
| `schooling_w`, `schooling_m`, `everschool_w` | general education | NFHS-5 — used as **placebos**, not controls |
| `mobile_w`, `bankacct_w` | women's own mobile phone / bank account | NFHS-5 |
| `lit2011` | general literacy rate | Census 2011 (AP and Telangana share the undivided value) |
| `urban_share_nfhs` | urban share **derived** from the NFHS-5 urban/rural split, not the Census figure | derived |

Raw sources in `../raw/diglit/`. The NFHS-5 mirror is verified against 8 published figures on
every build — the script aborts if any fails. Merge with `../h5_conversion_capacity/scripts/build_h5_panel.py`, which
produces `../output/panel_h5.csv`. Details: `../h5_conversion_capacity/DECISIONS.md`.

Plain-English explanation of each file: `../DATA_GUIDE.md`
Decisions and why: `../h1_access_vs_usage/DECISIONS.md` · Full technical detail: `../data_fetching.md`
