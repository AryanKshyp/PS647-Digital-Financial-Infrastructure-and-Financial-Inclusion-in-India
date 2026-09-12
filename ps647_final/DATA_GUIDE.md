# Data Guide — plain English

What we're building: one row per **state per year**, for 6 years (FY2018–FY2023), to test whether
banking infrastructure raises *access* to banking more than it raises *usage*.

**33 states × 6 years = 198 rows. No missing data anywhere.**

**The 8 files you need are copied into `data/`** — that's all you have to touch.
Everything in `raw/` is the original download, kept for provenance.

---

## First, four words you'll keep seeing

- **RBI** — Reserve Bank of India, the central bank. Publishes almost all our data.
- **BSR** — "Basic Statistical Return". The annual form every bank branch files with RBI, saying how many
  accounts it has and how much money is in them. This is where *account counts* come from.
- **DBIE** — RBI's online data portal (now at `data.rbi.org.in`). Where we pulled the BSR numbers from.
- **NSDP** — "Net State Domestic Product". Basically a state's income, the state-level version of GDP.
  We use it per person, as our control for how rich a state is.

Two more, used below: **SCB** = scheduled commercial bank (a normal bank). **UT** = Union Territory.

---

## The 8 files you'll actually use

All copied into `data/` under clearer names. Paths below are the originals in `raw/`.

### 1. Bank branches
`raw/handbook_states/t152_bank_offices.csv` → `data/01_branches.csv`
- **What:** how many bank branches each state had, each year.
- **From:** RBI's *Handbook of Statistics on Indian States* — an annual reference book. We scraped it off RBI's website.
- **Issues:** none. Checked and clean.

### 2. ATMs
`raw/atm_deployment/atm_statewise_long.csv` → `data/02_atms.csv`
- **What:** how many ATMs each state had, each year.
- **From:** a separate quarterly RBI release on ATM deployment.
- **Issues:** none. The national totals match RBI's published figures exactly. ATM counts genuinely *fall*
  in some big states in 2024 — that's real (banks removing ATMs), not a mistake.

### 3a. Number of LOAN accounts
`raw/bsr_accounts/derived_state_year_credit_accounts_2010_2023.csv` → `data/03_loan_accounts.csv`
- **What:** how many loan accounts each state had, each year.
- **From:** the BSR forms, via India Data Portal (a university-run mirror of the RBI data).
- **Use the account-count column only** — take loan *amounts* from file 5 instead.
- **Issues:** none. Checked: complete, and the totals match RBI's own published figures.

### 3b. Number of DEPOSIT accounts
`raw/bsr_accounts/PANEL_state_year_accounts_FY2018_FY2024.csv` → `data/04_deposit_accounts.csv`
- **What:** how many deposit (savings/current/fixed) accounts each state had, each year.
- **From:** the BSR forms, pulled from RBI's DBIE portal.
- **Use the deposit-account column only.**
- **Issues:** three states have bad values in later years — see "Problems" below.

Together, 3a and 3b are the *access* half of the hypothesis: everything else measures rupees, these
measure how many people actually have an account.

### 4 & 5. Money deposited, and money lent
`raw/handbook_states/t155_deposits.csv` → `data/05_deposit_amounts.csv`
`raw/handbook_states/t156_credit.csv` → `data/06_loan_amounts.csv`
- **What:** total rupees deposited in, and lent out by, banks in each state, each year (in ₹ crore).
- **From:** the same RBI Handbook as the branches file.
- **Why it matters:** this is the *usage* half — money actually moving, not just accounts existing.
- **Issues:** none.

### 6. State income (the control)
`raw/handbook_states/t19_pc_nsdp_current.csv` → `data/07_income_per_person.csv`
- **What:** income per person in each state, each year.
- **From:** RBI Handbook again.
- **Issues:** not published at all for Lakshadweep or Dadra & Nagar Haveli / Daman & Diu, which is why those
  two get dropped. Gujarat's FY2023-24 is also missing, but that year is outside our panel now, so it
  no longer costs us anything.

### 7. Adult population (the denominator)
`raw/population/adult_pop_18plus_by_state_year_1march.csv` → `data/08_adult_population.csv`
- **What:** how many adults (18+) live in each state, each year.
- **Why it matters:** every headline number is "per person" — branches per adult, accounts per adult. This
  is the bottom of every one of those fractions.
- **From:** a 2020 government population-projection report. It's a PDF, so the numbers were extracted from it.
- **Issues:** the report only publishes age breakdowns every 5 years. So for most years the adult share is
  **estimated between known points**, not published. It's a reasonable estimate, but it must be mentioned
  in your write-up.

### 8. PhonePe transactions and users (the digital measure)
`raw/phonepe_pulse/` → `raw/phonepe_derived/phonepe_state_fy.csv`
- **What:** how many people in each state had signed up to PhonePe, and how many payments they made,
  each year.
- **From:** PhonePe publishes its own data on GitHub, for free. We downloaded the whole thing.
- **Why it matters:** branches and ATMs barely changed over these years. Digital payments exploded.
  This is the infrastructure that actually moved — it's what makes the project "digital" again.
- **Two things to know:**
  - **PhonePe is one company**, roughly half of all UPI. So this measures *PhonePe* take-up and we
    use it as a stand-in for digital payments generally.
  - **Starts one year later.** The data begin in 2018, so the first usable year is FY2019, not
    FY2018. The digital analysis is 5 years, not 6.

---

## Problems worth knowing about

**1. Three states have wrong deposit-account numbers in later years.**
- **Delhi (2023, 2024), Haryana (2024), Chandigarh (2023)** — the savings-account figure roughly doubles
  in one year, which banks don't do.
- This is an error in RBI's own published data, not in how we pulled it.
- Decision taken: keep them for now, then re-run without those 4 cells and compare (see `DECISIONS.md` D7).

**2. Two states are dropped** — Lakshadweep, and Dadra & Nagar Haveli / Daman & Diu — because no income
data is published for them. Both are tiny.

**3. The panel stops at FY2023, not FY2024.** The loan-account data that counts all banks consistently
only runs to 2023. We chose the shorter, cleaner panel over the longer, inconsistent one
(see `DECISIONS.md` D8). Side benefit: this removed the last missing cell, so the panel is now complete.

---

## Two things that will silently break the merge

- **Years are labelled differently in different files.** Banking files say `2018` meaning *31 March 2018*.
  The income file says `2017-18` for that same moment. They line up — but only if you map them deliberately.
- **States changed shape during these years.** Ladakh split off from Jammu & Kashmir in 2020; Daman & Diu
  merged with Dadra & Nagar Haveli. Different files handle this in different years. The rule that works
  everywhere: **add them back together** in every year, so each state means the same thing throughout.

---

## Everything else on disk

Ignore it. It's raw downloads, intermediate working files, duplicate copies in other formats, and a few
things checked and rejected.

Decisions taken along the way, and why, are in `DECISIONS.md`.

Full technical detail, including exact sources and every check run, is in `data_fetching.md`.
