# Population denominators — state-wise adult (18+) population, 2011–2036

## Source

**Report of the Technical Group on Population Projections — "Population Projections for
India and States 2011–2036"**
National Commission on Population, Ministry of Health & Family Welfare, Government of India,
**July 2020** (Census of India 2011 series; Technical Group chaired by the Registrar General of India).

| | |
|---|---|
| Download URL used | `https://nhm.gov.in/New_Updates_2018/Report_Population_Projection_2019.pdf` |
| Downloaded | 2026-09-08 (HTTP 200, browser User-Agent) |
| Local file | `Population_Projections_India_States_2011-2036_TechnicalGroup_July2020.pdf` |
| Size / pages | 11,543,351 bytes, 268 PDF pages, PDF 1.5 |
| MD5 | `c1ab36564180d7908d4777060afa108e` |

Mirrors of the same document (not downloaded, for reference):
* `https://main.mohfw.gov.in/sites/default/files/Population Projection Report 2011-2036 - upload_compressed_0.pdf`
  (MoHFW; DNS did not resolve from this machine on 2026-09-08)
* `https://www.india.gov.in/my-government/documents/details/population-projections-for-india-and-states-2011-2036`
* `https://educationforallinindia.com/wp-content/uploads/2023/04/Population-Projection-Report-2011-2036-upload_compressed_0-4.pdf`

**No official machine-readable (XLSX/CSV) release exists.** data.gov.in / censusindia.gov.in /
MoSPI publish only the PDF or derived summary charts. Commercial re-publishers
(`dataful.in` datasets 1301, 1302, 18521) have tabulated versions behind a login.
The CSVs in this directory were therefore extracted from the PDF directly
(`../../scripts/parse_population_projections.py`, `pypdf` text extraction).

Note the PDF page numbering is offset by **+4** from the printed report page numbers
(printed page 82 = PDF page 86). All page references below are **PDF pages**.

---

## What the report actually contains (important)

The report publishes **total** population for **every** year 2011–2036, but publishes
**age detail only for the quinquennial years 2011, 2016, 2021, 2026, 2031, 2036**.
There is **no published per-year adult population**. See "Derived panel" below.

### Summary tables — annual totals, all 38 units (India + states + UTs)

| Table | Reference date | PDF pages | File |
|---|---|---|---|
| Table 8 | as on **1 March**, 2011–2036 | 47–59 | `pop_total_annual_1march_2011_2036.csv` |
| Table 11 | as on **1 July**, 2011–2036 | 86–98 | `pop_total_annual_1july_2011_2036.csv` |
| Table 14 | as on **1 October**, 2011–2036 | 125–137 | `pop_total_annual_1october_2011_2036.csv` |

Each page carries 3 units × 3 columns (Persons / Male / Female), rows = years 2011…2036.
Units are in **thousands ('000)**. Column order (verified from the printed headers):
INDIA, JAMMU & KASHMIR (UT), HIMACHAL PRADESH, PUNJAB, HARYANA, NCT OF DELHI, RAJASTHAN,
UTTAR PRADESH, BIHAR, ASSAM, WEST BENGAL, JHARKHAND, ODISHA, CHHATTISGARH, MADHYA PRADESH,
GUJARAT, MAHARASHTRA, ANDHRA PRADESH, KARNATAKA, KERALA, TAMIL NADU, CHANDIGARH, UTTARAKHAND,
SIKKIM, ARUNACHAL PRADESH, NAGALAND, MANIPUR, MIZORAM, TRIPURA, MEGHALAYA, DAMAN & DIU,
DADRA & NAGAR HAVELI, GOA, LAKSHADWEEP, PUDUCHERRY, ANDAMAN & NICOBAR ISLANDS, TELANGANA, LADAKH.

(Tables 9, 12, 15 = urban population; tables 10, 13, 16 = urban share. Not extracted.)

**Which reference date to use.** For an Indian financial year FY *t* (1 Apr *t*−1 → 31 Mar *t*),
the exact mid-point is **1 October of year *t*−1** — so `pop_total_annual_1october_*.csv`
with `year = t-1` is the natural denominator for FY *t*. For a calendar year, use the 1 July file.

### Detailed tables — age structure, quinquennial years only

Per-unit blocks of 4–5 pages, in this order (PDF page of the T-17 page):

| Unit | T-17 page | Unit | T-17 page |
|---|---|---|---|
| INDIA | 164 | MADHYA PRADESH | 225 |
| JAMMU & KASHMIR (UT) | 169 | GUJARAT | 229 |
| HIMACHAL PRADESH | 173 | MAHARASHTRA | 233 |
| PUNJAB | 177 | ANDHRA PRADESH | 237 |
| UTTARAKHAND | 181 | KARNATAKA | 241 |
| HARYANA | 185 | KERALA | 245 |
| NCT OF DELHI | 189 | TAMIL NADU | 249 |
| RAJASTHAN | 193 | TELANGANA | 253 |
| UTTAR PRADESH | 197 | NORTH-EAST STATES (Excluding Assam) | 257 |
| BIHAR | 201 | | |
| ASSAM | 205 | | |
| WEST BENGAL | 209 | | |
| JHARKHAND | 213 | | |
| ODISHA | 217 | | |
| CHHATTISGARH | 221 | | |

Within each block (T-17 page = *p*):

* **T-17** (*p*) — "Projected Population Characteristics as on 1st March: 2011–2036".
  Columns = 2011, 2016, 2021, 2026, 2031, 2036. Rows include Total / Male / Female,
  sex ratio, density, and **"Population by broad age-group ('000)": `18 years and above`,
  `0-14`, `15-59`, `60+`**, then percentage shares, median age, dependency ratios.
  → `pop_broad_agegroups_quinquennial.csv`
* **TABLE-17A** (*p*) — demographic indicators (TFR, CBR, CDR, IMR, e0) by 5-year period. Not extracted.
* **TABLE-18** (*p*+1) — "Projected Population By Age and Sex as on 1st March: 2011–2036 ('000)".
  Age bands: **0-1, 0-4, 5-9, 10-14, 15-19, 20-24, 25-29, 30-34, 35-39, 40-44, 45-49,
  50-54, 55-59, 60-64, 65-69, 70-74, 75-79, 80+, Total**, each × Person/Male/Female.
  (`0-1` is a *subset* of `0-4` — do not add it when summing.)
  → `pop_by_5yr_ageband_quinquennial.csv`
* **TABLE-19** (*p*+2) — the same as percentage distribution. Not extracted (derivable).
* **TABLE-20** (*p*+3) — "Projected Population By Sex For Ages 5 To 23 Years", **single years of age**.
  → `pop_by_single_age_5to23_quinquennial.csv`

**Coverage gap in the source:** age detail exists for only **24 units** — India, 22 states,
and one *combined* "North-East states (excluding Assam)". **Goa is excluded from the
projection exercise entirely** (its base-year data were unusable), and the smaller UTs
(Chandigarh, Daman & Diu, Dadra & Nagar Haveli, Lakshadweep, Puducherry, Andaman & Nicobar,
Ladakh) have annual totals but **no** age breakdown.

---

## Files in this directory

| File | Contents | Units |
|---|---|---|
| `Population_Projections_..._July2020.pdf` | the source report | — |
| `pop_total_annual_1march_2011_2036.csv` | Table 8: total/male/female by unit × year | '000 |
| `pop_total_annual_1july_2011_2036.csv` | Table 11: same, 1 July | '000 |
| `pop_total_annual_1october_2011_2036.csv` | Table 14: same, 1 October | '000 |
| `pop_broad_agegroups_quinquennial.csv` | T-17: total, male, female, **18+**, 0-14, 15-59, 60+ | '000 |
| `pop_by_5yr_ageband_quinquennial.csv` | Table 18: 19 age bands × person/male/female | '000 |
| `pop_by_single_age_5to23_quinquennial.csv` | Table 20: single ages 5–23 × person/male/female | '000 |
| `adult_pop_18plus_by_state_year_{1march,1july,1october}.csv` | **derived** annual 18+ panel | '000 |

Row counts: 988 = 38 units × 26 years (annual tables); 144 = 24 units × 6 years (T-17);
2736 = 24 × 6 × 19 (Tables 18 and 20).

### Validation performed
* T-17 `pop_total` matches Table 8 for every unit/year — 0 mismatches.
* Table 18 `Total` row = sum of the 17 non-overlapping bands — 0 mismatches.
* T-17 `15-59` = sum of Table 18 bands 15-19…55-59 — 0 mismatches.
* Identity `18+ = Total − (0-4) − Σ(single ages 5…17)` (Table 18 + Table 20) reproduces the
  **published** 18+ figure exactly for all 23 units that print it.
* 1 March < 1 July < 1 October < next 1 March for every unit-year.

### One repaired source defect
For **NCT OF DELHI** the `18 years and above` row is **printed blank** in the PDF
(PDF p. 189). It was reconstructed with the identity above, which is exact for every other
state. Those six rows are flagged `pop_18plus_source = "derived_T18_T20 (row blank in PDF)"`.
A `Population (000')` layout quirk on the Rajasthan page (PDF p. 193, where the Total values
sit on the header line) is handled in the parser.

---

## Derived panel: adult population by state and year

`adult_pop_18plus_by_state_year_*.csv` — built by
`../../scripts/build_adult_population_panel.py`.

Columns: `state, year, ref_date, pop_total_000, share_18plus, pop_18plus_000,
share_source_unit, share_source, share_method`.

**Method (this is an interpolation, not a published series):**
1. 18+ share = `pop_18plus / pop_total` at the anchors 2011, 2016, 2021, 2026, 2031, 2036 (T-17).
2. The share is **linearly interpolated** between anchors for the intervening years.
3. It is multiplied by the **published annual total** for the chosen reference date.

`share_method` is `"published"` only where the year is an anchor year and the state has its own
T-17 block; otherwise it says the share was interpolated. The *total* is always published.

**Proxy shares** (`share_source` column) for units the report gives no age structure for:
* `NE_combined_proxy` — Sikkim, Arunachal Pradesh, Nagaland, Manipur, Mizoram, Tripura,
  Meghalaya use the report's own combined North-East (excl. Assam) share.
* `jammu_kashmir_proxy` — Ladakh uses the J&K (UT) share (Ladakh was part of J&K until 2019).
* `india_proxy` — Goa, Chandigarh, Daman & Diu, Dadra & Nagar Haveli, Lakshadweep, Puducherry,
  Andaman & Nicobar Islands use the all-India share. **These are the weakest rows**;
  Chandigarh and D&NH are migrant-heavy with markedly adult-skewed age structures, so their
  18+ counts are understated. Consider dropping these units, or using the 2011 Census
  age distribution for them instead.

For reference, the interpolated all-India 18+ share runs 0.673 (2018) → 0.705 (2024); the
published anchors are 0.630 (2011), 0.661 (2016), 0.691 (2021), 0.715 (2026).

### If you prefer 15+ or 20+ instead of 18+
Both are available **exactly** at the quinquennial anchors from
`pop_by_5yr_ageband_quinquennial.csv`:
* `15+` = sum of bands 15-19 … 80+ (equivalently `pop_15_59 + pop_60plus` from T-17),
* `20+` = sum of bands 20-24 … 80+.
Interpolate those shares the same way. 18+ is preferred here because the report prints it
directly and it matches the electoral/banking-eligibility definition.

---

## Gaps and caveats

1. **Projections, not observations.** These are 2020-vintage projections anchored on Census 2011,
   with no Census after 2011 to correct them. Post-2011 error compounds; by 2024 the all-India
   projection (1.403 bn at 1 July 2024) is the standard official denominator but is not measured.
2. **No annual age detail is published.** Any per-year adult figure — including the derived files
   here — involves interpolation. Do not present interpolated values as report figures.
3. **Goa has no age structure at all** in the report; its total is projected but it was excluded
   from the Technical Group's age-structure exercise.
4. **Seven north-eastern states are only available combined** for age structure.
5. **J&K / Ladakh:** the report already reflects the 2019 reorganisation and reports them
   separately from 2011 onwards (back-cast). Andhra Pradesh and Telangana are likewise separate
   throughout. Check this against however your other panel sources treat these splits.
6. **Dadra & Nagar Haveli and Daman & Diu** are separate units here, though they merged into a
   single UT in Jan 2020. Sum them if your panel uses the merged UT.
7. Units are **thousands** everywhere in this directory.

## Fallbacks (not used, recorded in case they are needed)
* Census 2011 C-13 / C-14 single-year age tables on `censusindia.gov.in` give measured (not
  projected) 2011 age structure for every state **including Goa and all UTs** — the right
  source if the small-UT proxies above are unacceptable.
* RBI *Handbook of Statistics on Indian States* has state population but **no age breakdown**.
