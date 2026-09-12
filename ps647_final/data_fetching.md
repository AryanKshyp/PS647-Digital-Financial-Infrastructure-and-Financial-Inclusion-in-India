# Data Fetching Notes

Panel: ~30 states/UTs × FY2018–FY2024. PMJDY **dropped** — DFI index = branches + ATMs only.
Raw files land in `raw/<source>/`. Nothing is merged yet.

---

## 1. RBI Handbook of Statistics on Indian States

- **Edition used:** 2024-25, released 11 Dec 2025 — covers through FY2024-25, so our window is fully inside it.
- **Landing page:** https://www.rbi.org.in/Scripts/AnnualPublications.aspx?head=Handbook+of+Statistics+on+Indian+States
- **Script:** `scripts/fetch_handbook.py` → `raw/handbook_states/`

| Table | id | Gives | File |
|---|---|---|---|
| 152 | 23601 | Bank offices (branches), end-March | `t152_bank_offices.csv` |
| 155 | 23604 | Deposits, ₹ crore | `t155_deposits.csv` |
| 156 | 23605 | Credit, ₹ crore | `t156_credit.csv` |
| 19 | 23468 | Per-capita NSDP, current prices | `t19_pc_nsdp_current.csv` |
| 20 | 23469 | Per-capita NSDP, constant prices | `t19_pc_nsdp_constant.csv` |
| 153 | 23602 | C-D ratio, place of sanction | `t153_cd_ratio_sanction.csv` |
| 154 | 23603 | C-D ratio, place of utilisation | `t154_cd_ratio_utilisation.csv` |
| 160 | 23609 | RRB deposits, ₹ crore | `t160_rrb_deposits.csv` |
| 161 | 23610 | RRB credit, ₹ crore | `t161_rrb_credit.csv` |
| 163 | 23612 | RRB branches | `t163_rrb_branches.csv` |

(160/161/163 were pulled to diagnose the BSR universe question in §7 — not needed as analysis variables.)

Each table lives at `https://www.rbi.org.in/Scripts/PublicationsView.aspx?id=<id>`.

**Nuances:**
- No XLSX download exists — tables are HTML only, parsed with `pandas.read_html`.
- Each table is split across **two** HTML `<table>` blocks (early years, then a "Concld." block with later years). Script stitches both.
- Header row is found by detecting the row where most cells look like years, since the number of title/unit rows above it varies by table.
- Dropped rows: regional aggregates (`NORTHERN REGION` etc.), `ALL-INDIA`, notes, footnotes.
- Cleaning: stripped thousands commas and trailing footnote markers (`@ # * $`); RBI nulls (`-`, `..`, `n.a.`, `Neg.`) → NaN.
- Output is **long** format: `state_raw, year_label, value, table, source_title, source_url`. Raw HTML kept alongside for audit.
- Banking tables are **calendar-labelled by end-March** (`2018` = 31 Mar 2018 = FY2017-18 close). NSDP tables use FY labels (`2017-18`). **These need aligning at merge time.**
- Coverage pulled: banking 2004–2025 (37 states), NSDP 2011-12–2024-25 (34 states).

---

## 2. RBI State-wise & Region-wise Deployment of ATMs

- **Not** in the Handbook (table 4.1.34 was dropped from the current edition) and **not** the bank-wise `ATMView.aspx` series. It is a standalone quarterly data release.
- **Landing page:** https://www.rbi.org.in/Scripts/StateRegionATMView.aspx
- **Per-release permalink:** `.../StateRegionATMView.aspx?sratmid=N` — end-March: **31**=2018, **35**=2019, **39**=2020, **43**=2021, **47**=2022 *(Revised)*, **51**=2023, **55**=2024
- **Files:** `raw/atm_deployment/rbi_statewise_atm_march{2018..2024}.{xlsx,pdf}` + `SOURCE_URLS_all_quarters_2017_2025.json` (every quarter 2017–2025, if we ever want quarterly frequency)
- **Script:** `scripts/parse_atm.py` → `raw/atm_deployment/atm_statewise_long.csv`

**Nuances:**
- The year/quarter archive is an ASP.NET `__doPostBack` widget, not plain-GET navigable — links were harvested by scripting the postbacks with `__VIEWSTATE`/`__EVENTVALIDATION`.
- Sheet is **bank × state** (rows = banks incl. White Label ATM Operators, cols = states). We take the **grand-total row**.
- Grand-total row label varies: `Grand Total`, `GRAND TOTAL`, and `Total (Banks+WLAOs)` in the Revised March-2022 file. Parser matches all three and takes the **last** match.
- Sheet name varies too (`Statewise March-2018`, `Statewise March 2022`, `State-Wise March-24`) — matched by regex.
- Header row located by detecting known state names, since leading blank/title rows vary.
- Spelling drift normalised: `ORISSA`→`ODISHA`, `PONDICHERRY`→`PUDUCHERRY`, `CHHATISGARH`→`CHHATTISGARH`, `NCT OF DELHI`→`DELHI`, `LAKSHWADEEP`→`LAKSHADWEEP`, `JAMMU AND KASHMIR`→`JAMMU & KASHMIR`, `ANDAMAN & NICOBAR`→`... ISLANDS`.
- **All-India totals reproduced independently** and match the source: 222,066 (2018) · 221,703 · 234,357 · 238,588 · 251,740 · 258,534 · 257,654 (2024).
- 2022–2024 files also carry a **district-wise** sheet, unused for now.
- The 2024 dip in AP, Telangana, Maharashtra, UP, Bihar is **real** (ATM decommissioning), not a parse error.

---

## 3. State harmonisation (constant panel)

Boundary changes inside the window. Merging is not just tidiness — it is arithmetically exact:

- **Jammu & Kashmir + Ladakh → "Jammu & Kashmir (incl. Ladakh)"**
  Ladakh appears only from 2020 in *both* sources (68 branches, 136 ATMs); blank 2018–19 because it was still inside J&K. Summing gives an unbroken 2018–2024 series.
- **Dadra & Nagar Haveli + Daman + Diu → "DNH & Daman & Diu"**
  ⚠️ **The merge lands in a different year in each source.** Handbook: D&D goes blank from **2020** exactly as DNH jumps 59 → 110. ATM files: DNH/Daman/Diu stay three separate columns until **2021** and merge from **2022**. Summing *all three* across *all* years is correct for both and is the only rule that works.
- Rule: **sum levels** (branches, ATMs, deposits, credit, accounts, population) before computing any ratio. Never average ratios.
- Note the Handbook uses `Daman & Diu` as one unit; the ATM files split `DAMAN` and `DIU` into two columns pre-2022.

**Name crosswalk is small.** After upper-casing and standardising `AND`→`&`, **34 of 37 units match exactly** across Handbook / ATM / population. The complete list of mismatches:

| Handbook | ATM | Population |
|---|---|---|
| `DELHI` | `DELHI` | `NCT OF DELHI` |
| `JAMMU & KASHMIR` | `JAMMU & KASHMIR` | `JAMMU & KASHMIR (UT)` |
| `DAMAN & DIU` | `DAMAN` + `DIU` (pre-2022), merged col (2022+) | `DAMAN & DIU` |

---

## 4. Known gaps

- **Gujarat per-capita NSDP FY2023-24** — missing in the Handbook at both current and constant prices (Gujarat releases NSDP late). MoSPI's site is a JS-rendered SPA and not scriptable; `data.gov.in` has a GSDP-based alternative. Options: source manually, or let FY2024 Gujarat drop on the control variable.
- **NSDP has no rows at all** for Dadra & Nagar Haveli, Daman & Diu, Lakshadweep → these UTs cannot carry the `lnNSDP` control.
- Ladakh NSDP exists only from 2022-23; handled by the J&K merge above.

---

## 5. Population Projections 2011–2036 (adult denominators)

- **Report:** *Population Projections for India and States 2011–2036*, Technical Group on Population Projections, NCP/MoHFW, July 2020.
- **Working URL:** https://nhm.gov.in/New_Updates_2018/Report_Population_Projection_2019.pdf (268 pp, 11.5 MB). The MoHFW mirror's DNS did not resolve. **No official XLSX/CSV exists anywhere** — PDF only.
- **Scripts:** `scripts/parse_population_projections.py`, `scripts/build_adult_population_panel.py` → `raw/population/`
- **Use:** `adult_pop_18plus_by_state_year_1march.csv` (see alignment rule below). All figures in **thousands**.

**The central nuance:** the report publishes **annual totals** for 2011–2036, but **age detail only for 2011, 2016, 2021, 2026, 2031, 2036**. There is no published annual adult figure. So the 18+ series is *derived*: the 18+ **share** is linearly interpolated between quinquennial anchors and applied to the published annual total. Totals are published; adult counts are ours.

**Other nuances:**
- Validated four ways, all exact: T-17 totals = Table 8; Table 18 total = sum of bands; T-17 `15-59` = sum of bands; and `18+ = Total − (0-4) − Σ(ages 5…17)` reproduces the published 18+ exactly for all 23 states that print it.
- **NCT of Delhi's `18+` row is blank in the PDF** — reconstructed via that identity, flagged `derived_T18_T20`.
- **Goa is excluded from the report's age-structure exercise entirely.** The 7 NE states (excl. Assam) are only available **combined**. Chandigarh, D&NH, Daman & Diu, Lakshadweep, Puducherry, A&N, Ladakh have totals but no age data.
- Proxy shares assigned where age data is absent (`share_source` column): `NE_combined_proxy`, `jammu_kashmir_proxy` (Ladakh), `india_proxy`. **The `india_proxy` rows are the weakest** — Chandigarh and D&NH are migrant-heavy and adult-skewed, so their adult share is understated. Census 2011 C-13/C-14 is the fallback.
- 2020-vintage projections off Census 2011, with no later census to correct them — error compounds toward 2024.
- D&NH and Daman & Diu are separate units here; J&K/Ladakh and AP/Telangana are split back to 2011. Reconcile via §3.

---

## 6. ⚠️ Year-alignment rule (easiest place to introduce a silent error)

Three different year conventions are in play. They line up like this:

| Source | Label for the same instant | Convention |
|---|---|---|
| Handbook banking (152/155/156), ATM files | `2018` | stock as at **31 Mar 2018** |
| Handbook NSDP (19/20) | `2017-18` | FY **ending** 31 Mar 2018 |
| Population panel | `1march 2018` | stock as at **1 Mar 2018** |

**Rule: banking year `Y` ↔ NSDP FY `(Y-1)-(Y)` ↔ population `1 March Y`.**

- Every variable we use — branches, ATMs, deposits, credit, deposit/credit accounts — is a **stock at 31 March**, not a flow. So the denominator must be a **stock at the same instant**.
- Use the **1 March** population series, *not* 1 October. 1 March is one month off; the 1-October-of-FY−1 series (which suits mid-year flow averaging) would be **six months** off and would bias every per-capita ratio.
- With "FY2018" meaning the year ending 31 Mar 2018, the panel is banking years 2018…2024 = 7 years.

---

---

## 7. BSR account counts (the Access DV)

RBI **no longer publishes BSR as static files** — every `AnnualPublications.aspx` link now 302s to the retired `dbie.rbi.org.in`, which redirects to the Angular SPA at `data.rbi.org.in`. Data was pulled **programmatically from DBIE/CIMS with no credentials**; protocol in `raw/bsr_accounts/DBIE_ACCESS_NOTES.md`.

| Variable | Source | Coverage | Universe / basis |
|---|---|---|---|
| Credit accounts | DBIE report **943**, Quarterly BSR-1 Table 1.3 | Mar-2014 → Jun-2026 | **excl. RRBs**, place of **sanction** |
| Deposit accounts | DBIE report **853**, Annual BSR-2 Table 2.3 | Mar-2019 → Mar-2026 | **incl. RRBs** |
| Deposit accounts, **Mar-2018 only** | India Data Portal redistribution of RBI BSR-2 | — | report 853 starts Mar-2019 |

- **Output:** `raw/bsr_accounts/PANEL_state_year_accounts_FY2018_FY2024.csv` — 35 states × 7 years, **no missing cells**.
- **Scripts:** `scripts/fetch_bsr_dbie.py`, `scripts/dbie_client.py`, `scripts/build_bsr_credit_accounts_panel.py`
- IDP's bank-group file labels years **one behind** the reference date (`year=2017` = 31-Mar-2018). Its credit file does **not** — labels there are correct as-is.
- DBIE gotcha: `dbie_getReportLink` needs **both** `reportId` and `lang` AES-encrypted; plaintext returns a generic "Internal Server Error" that reads like an outage.
- `raw/bsr_3a/` — Statement 3A is portal-only, but its three variables (offices, deposits, credit) are just Handbook T152/155/156, already pulled. No separate fetch needed.

### Validation run here, not taken on trust

- **Deposit amounts vs Handbook T155, state × year, all 7 years:** median difference **0.0001%**, max 0.038% (Lakshadweep whole-crore rounding). **2018 matches as well as every other year** — independently confirming the IDP year-offset, which a wrong offset would have blown apart.
- **IDP credit year labels correct as-is:** median difference vs Handbook T156 = **0.001%**.

### The credit series sits on a different footing from the Handbook — decomposed exactly

Two effects compound, not one:

1. **Basis.** DBIE credit = place of **sanction**; Handbook T156 = place of **utilisation**. Checked against T153/T154: Delhi 1,680,085 vs 1,679,326 (0.05%), Maharashtra 4,679,668 vs 4,695,854 (0.3%).
2. **RRB exclusion.** The residual after fixing basis **equals the RRB credit share almost exactly**: Mizoram 41.2% vs 41.1%, Tripura 21.7 vs 21.8, Bihar 10.0 vs 10.0, UP 8.7 vs 8.7; Delhi/Goa/Sikkim ~0 vs 0.

### ⚠️ Universe asymmetry inside the Access DV

Access = deposit accounts per adult **+** credit accounts per adult — but the two halves are not on the same universe:

| | RRBs | Basis |
|---|---|---|
| Deposit accounts | **included** | branch location |
| Credit accounts | **excluded** | place of sanction |

- Excluding RRBs drops a median **~18%** of credit accounts nationally — **65% Mizoram, 39% Tripura, 37% Telangana, 33% UP**.
- The exclusion **drifts within state over time** (median 0.8 pp; 6.2 pp Mizoram, 5.8 pp Bihar, 5.2 pp Tripura), so state fixed effects do **not** fully absorb it.
- It bites hardest in exactly the rural/low-income states H1 is about.

### Option on the table

`derived_state_year_credit_accounts_2010_2023.csv` (IDP, **incl. RRBs**, place of **utilisation**) covers **2018–2023 but not 2024**. Better on both counts — universe matches the deposit side, and utilisation is the basis the plan's own Limitations section prefers — at the cost of one panel year (N 245 → 210).

**Checked and refuted:** an earlier note claimed this file switches basis at 2018/2019. It does not. Median difference vs the utilisation basis is 0.035–0.051% in *every* year 2017–2023, and Maharashtra matches utilisation exactly throughout. The file is consistently place-of-utilisation.

---

## 8. Status

| Source | Status |
|---|---|
| Handbook (branches, deposits, credit, NSDP, RRB) | done, verified |
| ATM deployment 2018–2024 | done, all-India totals reproduced |
| Population / adult denominators | done, validated 4 ways |
| BSR account counts 2018–2024 | done, validated against Handbook |

Nothing is merged yet. Open decisions: RRB-inclusive credit accounts vs FY2024 coverage (§7); Gujarat FY2024 NSDP (§4).

---

## 8. Plan audit (vs `project_plan.pdf`)

**Every required variable is present.** Merged panel = **33 states × 7 years = 231**, minus Gujarat FY2024 → **230** (plan anticipated N≈210).

| Plan variable | Source | Status |
|---|---|---|
| Branches per lakh adults | T152 + population | ✓ |
| ATMs per lakh adults | ATM release | ✓ |
| PMJDY accounts | — | dropped by decision |
| Deposit accounts per adult | `PANEL_state_year_accounts_FY2018_FY2024.csv` | ✓ |
| Credit accounts per adult | same | ✓ (see flag 1) |
| Deposits per capita | T155 | ✓ |
| Credit outstanding per capita | T156 | ✓ |
| log NSDP per capita | T19 current | ✓ except Gujarat FY2023-24 |

### Flags

1. **RRB universe mismatch — the one that can bias H1.** Credit accounts come from the quarterly BSR-1, which **excludes RRBs**. Deposit accounts, deposit/credit amounts and branches all **include** them. RRB credit share is 3.0% nationally but **41.9% Mizoram, 20.7% Tripura, 10.8% Bihar, 9.4% UP, 0.4% Maharashtra** — systematically largest in the poorest states, i.e. exactly where the access story lives. Fix: use the IDP credit file (incl RRBs, matches Handbook <0.01%) for the accounts numerator, or subtract RRBs from every other series.
2. **Deposit accounts change source mid-panel** — FY2018 from India Data Portal, FY2019–24 from DBIE. All-India series is smooth, but it is not one series.
3. **Gujarat has no FY2023-24 NSDP** → costs 1 state-year on the control.
4. **DNH & Daman & Diu and Lakshadweep have no NSDP at all** → 2 units drop out (35 → 33) once the control is included.
5. **Adult population 18+ is derived, not published** — 243 of 266 state-years use an interpolated age share (§5).

### Extra data on disk (not required by the plan)

Keep if useful, but none of it feeds the model: T153/T154 C-D ratios; T160/161/163 RRB tables (diagnostic for flag 1 — worth keeping); T19 constant prices; population 1-July/1-October variants and 3 intermediate age files; 14 ATM PDFs (duplicate the XLSX); `raw/bsr_3a/*.xlsx` (duplicate the Handbook CSVs); `derived_*.csv` ×3 and `bsr1_state_credit_accounts_mar20xx.xlsx` ×7 (superseded by the PANEL); `bsr1_annual_state_credit_incl_rrb` (Mar-2026 only); `bsr2_quarterly_state_deposits_excl_rrb` (2023-26, too short); Economic Survey table (amounts only); the 4 loose `.xlsx` in the project root (manual downloads, superseded by the automated pull).

**`idp_bsr1_credit_district_2010_2023.csv` is 227 MB — 92% of the repo.** Do not delete it yet: it is the incl-RRB credit source that fixes flag 1.

---

## 9. Completeness check (FY2018–FY2024, 33 states)

All eight required series are **complete** — 231 cells each, zero missing, zero zeros — except:

- **Gujarat per-capita NSDP FY2023-24** (1 cell). Panel = **230 usable rows**.

### ⚠️ Data-quality defect found in deposit accounts

Not a missing-data problem — a *wrong-value* problem, in RBI's source rather than our extraction
(`Measure2+Measure4+Measure6` reproduces `Measure8` exactly wherever both are published).

The **savings-account** column breaks for three states:

| State | Savings accounts (millions) | Break |
|---|---|---|
| Delhi | 35.5 → 38.7 → **106.1** → 130.9 → 159.4 | from 2023, persists |
| Haryana | 47.7 → 52.6 → **102.1** | from 2024, persists |
| Chandigarh | 2.98 → **5.03** → 3.25 | 2023 only, reverts |

Detected via deposit accounts per adult, which is stable at 1–3.5 for every other state but reaches
**8.0 (Delhi 2023), 9.4 (Delhi 2024), 5.4 (Haryana 2024), 7.7 (Chandigarh 2023)**.
Goa sits at 5.5–5.8 across *all* years — high but not a break, so treat it as genuine.

Likely cause: a bank reclassifying savings accounts to a head-office location. Delhi and Haryana are
high-infrastructure states, so this inflates the Access variable precisely where the hypothesis is
tested. Affected cells: **Delhi 2023 & 2024, Haryana 2024, Chandigarh 2023**.

---

## 10. PhonePe Pulse (digital payments) — added under D14

**Source:** `https://github.com/PhonePe/pulse` — PhonePe's own open data release.
Shallow-cloned to `raw/phonepe_pulse/` (62 MB, untouched). Builder: `scripts/build_phonepe.py`.

**Two layouts in the repo, and only one of them has money in it:**
- `aggregated/transaction/.../state/<state>/<y>/<q>.json` — transaction **counts only**; the amount
  field is stripped in the current release. Used only for the P2P / Retail / Utility split.
- `map/transaction/hover/country/india/<y>/<q>.json` — **count *and* amount**, every state in one
  file. This is the source for the value series.
- `map/user/hover/country/india/<y>/<q>.json` — registered users per state (a cumulative **stock**,
  verified monotone across all 1,188 quarter-transitions).

**Coverage:** 36 raw states × 34 quarters (2018Q1–2026Q2), **zero gaps, zero missing amounts**.

**Financial-year conversion** (same `fy_end` rule as everything else, D9):
- fy_end = Y covers calendar **Q2+Q3+Q4 of Y−1 and Q1 of Y**.
- Transactions are **flows** → summed over the four quarters.
- Registered users is a **stock** → taken at calendar Q1 of Y, i.e. as at 31 March Y.
- Data start 2018Q1, so the first complete year is **fy_end = 2019**. Part-years at both ends are
  dropped automatically (`quarters_used == 4`).

**States:** harmonised with `build_panel.state_key`, so Ladakh folds into J&K (D2) and names match the
banking panel exactly. 35 units; the only two not in the 33-state panel are Lakshadweep and DNH_DD,
which D1 already drops. **Every one of the 33 panel states is present in every year.**

**Outputs** (`raw/phonepe_derived/`, nothing in `data/` touched):
| File | Rows |
|---|---|
| `phonepe_state_quarterly.csv` | 1,224 — raw state × calendar quarter |
| `phonepe_state_fy.csv` | 280 — 35 units × fy_end 2019–2026 |
| `phonepe_state_fy2019_fy2023.csv` | 175 — 35 units × the 5 years overlapping the banking panel |

Columns: `txn_count`, `txn_amount_inr` (rupees), `txn_count_p2p/retail/utility`,
`registered_users_31mar`.

**Validation:**
- P2P + Retail + Utility reproduces the map/ total to **0.000000%** on all 1,224 state-quarters —
  the two independent trees in the repo agree exactly.
- **45.5 crore** registered users at 31 March 2023, against PhonePe's own publicly stated 45+ crore.
- **44.3 bn** transactions in FY2023, against ~84 bn total UPI transactions that year — consistent
  with PhonePe's ~50% share.
- Mean ticket size FY2023 = **₹1,593**, a sane per-transaction value (confirms amounts are rupees,
  not paise or crore).

**⚠️ Caveats to carry into the write-up:**
- **One firm, not the market.** PhonePe is ~45–50% of UPI. This measures PhonePe penetration and is
  used as a *proxy* for digital-payment penetration. Its market share also varies by state, so
  cross-state levels are noisier than within-state growth.
- **Panel is FY2019–FY2023 = 5 years**, one shorter than the banking panel; fy_end 2018 cannot be
  built (needs Apr–Dec 2017).
- **Registered users are accounts, not people** — one person with two numbers counts twice, and the
  series can exceed plausible adult counts in small states. Check before using it as a denominator.
- Transactions are attributed to the **user's registered state**, not where the money was spent —
  a different attribution rule from BSR's place-of-sanction (§7).
