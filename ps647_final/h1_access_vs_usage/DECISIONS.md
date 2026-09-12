# Decision Log — H1

**D1 — Dropped Lakshadweep and "Dadra & Nagar Haveli and Daman & Diu."**
No income (NSDP) data for either. 35 units → **33 states**. Both tiny, negligible loss.

**D2 — Merged J&K + Ladakh, and DNH + Daman + Diu, in every year.**
Boundaries changed mid-sample; fixed effects need each state to mean the same thing throughout.
Sources record the change in different years, so summing all years is the only rule that works everywhere.

**D3 — Dropped PMJDY.** Infrastructure = branches + ATMs only.
⚠️ Nothing digital left — call it *physical banking infrastructure*, not *digital*. Superseded in part by D10.

**D4 — Keep Gujarat; leave its FY2023-24 income cell missing.**
Panel = **230 rows**, unbalanced. Not sourceable — Gujarat is absent from every RBI Handbook income table
for that year, and its own stats site blocks access. Dropping the state = 224; dropping the year = 198.
Gujarat only drops out of regressions using the income control; descriptives keep all 7 years.

**D5 — Year alignment:** banking `Y` = income `(Y-1)-(Y)` = population `1 March Y`.
All stocks at 31 March. Easy place to introduce a silent one-year offset. Implemented in D9.

**D6 — Disclose that adult population is interpolated.**
Source publishes age breakdowns only every 5 years; 243 of 266 state-years use an estimated 18+ share
applied to published annual totals. Goes in the methodology and limitations.

**D7 — Keep Delhi / Haryana / Chandigarh for now, despite bad deposit-account values.**
RBI's source has a jump in the *savings-account* column: Delhi 39m → 106m (2023, stays high),
Haryana 53m → 102m (2024, stays high), Chandigarh spikes 2023 then reverts. Our extraction is correct —
the break is in the source, likely a bank reclassifying accounts to a head office.
Symptom: deposit accounts per adult hits 9.4 (Delhi 2024) vs 1–3.5 everywhere else.
**Run with them included; re-run dropping the 4 cells (Delhi 2023+2024, Haryana 2024, Chandigarh 2023)
as a robustness check and compare.** These are high-infrastructure states, so if the coefficients move,
this is why.

**D8 — Switched loan accounts to the rural-banks-included file; panel is now FY2018–FY2023 (6 years).**
Fixes the bank-universe mismatch: every variable now counts the same set of banks.
Source: `raw/bsr_accounts/derived_state_year_credit_accounts_2010_2023.csv`.
Could not be merged arithmetically — the two files also differ on *where* a loan is counted, so
"included minus excluded" gave impossible negative values for Maharashtra.
Verified: 33×6 complete, no zeros; amounts reconcile to the Handbook at −0.000%;
0.08–0.87 accounts per adult, rising smoothly in every state.
**Cost:** lose FY2024. **Bonus:** that also removes the Gujarat gap (D4), so the panel is now
**perfectly balanced — 198 rows, zero missing cells across all 8 series.**
⚠️ Use this file's *account counts* only — take credit/deposit *amounts* from the Handbook.

**D9 — Added one canonical year column, `fy_end`, to all 8 files in `data/`.**
`fy_end` = calendar year of the 31 March the row refers to. So `fy_end=2018` means *as at 31 March 2018*,
the close of financial year 2017-18. **Merge and filter on `fy_end`; use it as the year fixed effect.**
- Seven files already used end-March labelling — copied straight across.
- **Only `07_income_per_person.csv` needed converting**: `"2017-18"` → `2018`. It was the one file that
  could have introduced a silent one-year offset.
- Native columns (`year_label`, `march_year`, …) are **left in place** so the original label stays auditable.
- Not named plain `year` on purpose — a bare `2018` is exactly the ambiguity that causes the bug.
- Script: `scripts/add_fy_end.py`, idempotent, safe to re-run.

Verified against known published figures rather than trusting the mapping — at `fy_end=2018`, Maharashtra
returns branches **12,545** and ATMs **25,651** (both match RBI exactly), income **₹172,663** carrying label
`2017-18`, and population dated `1 March 2018`. All eight files return all six panel years.

**D10 — No composite index. Branches and ATMs enter as two separate regressors. FINAL.**
Replaces the single DFI index everywhere. Both measured per lakh adults, entering all three equations
(Access, Usage, AUG) side by side. **No composite index is built, and none is reported — not even as a
robustness check.**

*Safe to separate:* raw correlation between branches/lakh and ATMs/lakh is 0.904, but that is almost
entirely cross-sectional (richer states have more of both). After state + year demeaning — what the model
actually uses — it falls to **0.305, VIF 1.10**. Negligible.

*Decision rule, fixed before seeing any results:* H1 is **fully supported only if β_access > β_usage > 0
holds for branches AND for ATMs**. If it holds for only one, that is reported as **partial support**,
naming which. This is pre-committed; it is not to be revised after the coefficients are seen.

*Why this is better than the index:* a branch is where an account is *opened*; an ATM is where it is
*used*. The split makes a directional prediction the index cannot. The strong result would be ATMs also
failing to raise usage — transaction infrastructure not producing transactions is far better evidence for
"formal rather than functional" than any index coefficient. If ATMs do raise usage, H1 becomes conditional
on infrastructure type, which is still a finding.

*Consequences:* the 0–1 normalisation and the branches-vs-ATMs weighting are both **gone** — two arbitrary
choices removed. Coefficients are now in real units (one more branch per lakh adults → X more accounts per
adult) instead of index points. An "infrastructure overall" claim, if wanted, comes from a **joint F-test**
on the two regressors, not from a composite. The write-up can no longer refer to a "DFI Index".

**D11 — Proceed to estimation despite the Step 4 gate failing.**
Diagnostic (a) returned within-state shares of 7.0% (branches) and 8.7% (ATMs), below the 10% FAIL
threshold fixed in advance. The PDF's instruction on that outcome is to check before concluding
anything, which F4 does. User directed: run the plan end to end and see what comes out.
**Consequence, fixed now so it cannot be revised later:** a null result in Step 5 does **not**
license the conclusion "infrastructure does not raise access". It is indistinguishable from
"the regressors moved too little to detect an effect". Any null must be reported with the 7.0% /
8.7% figures attached. A *significant* result, by contrast, is strong — detected despite thin
variation. No other part of the plan changes; the known Usage skew is **not** fixed, so the
original specification is what gets tested.

**D12 — Extended panel: FY2012–FY2023, branches only. Revises D10.**
The six-year panel could not test H1 (F4, F8): within-state variation in the regressors was 7.0% and
8.7%, and results proved unstable to two observations (F7). Extending the window is the only fix
available in this data.

- **Window FY2012–FY2023, 12 years, N ≈ 396.** Binding constraint is per-capita income, published
  from 2011-12.
- **ATMs are dropped.** RBI's state-wise ATM release begins in 2018 and cannot be extended. This
  **revises D10**: the branches-vs-ATMs comparison is no longer possible, and the infrastructure
  measure is branches per lakh adults alone. No composite index is reintroduced.
- **Expected gain:** branches within-state variation rises 7.0% → **20.1%**, roughly threefold. Still
  below the 25% PASS threshold set in Step 4, so this is an improvement, not a cure — it will be
  reported as WEAK.
- **Deposit accounts are spliced** at 2018: FY2012–FY2018 from the India Data Portal bank-group file,
  FY2019–FY2023 from RBI DBIE. Verified exact at the 2018 overlap (all-India 1,911,503,615 from both,
  0.000% difference) because data/04's own 2018 row is IDP-sourced. The IDP→DBIE source change at
  2018/19 already present under D8 is carried forward unchanged.
- **Everything else is held fixed:** same state harmonisation (D1, D2), same year alignment (D9), same
  normalisation (A2, A3), same pre-committed H1 rule from D10 — now applied to branches only.
- **The six-year results are NOT discarded.** They stand as reported (F5–F8). This is an additional
  specification with more statistical power, not a replacement, and both get reported.

**D13 — Merge Andhra Pradesh + Telangana into one unit, all years. Extends D2, applies to the 12-year panel only.**
Discovered when building the FY2012–FY2023 panel: Telangana shows **zero** branches, deposits and
credit for 2012, 2013 and 2014. It was carved out of Andhra Pradesh in June 2014 (FY2015), so before
that its data sits inside AP. Branches confirm it exactly — AP falls 9,900 (2014) → 6,290 (2015) as
Telangana appears with 4,721; the combined series runs continuously 9,900 → 11,011.

Identical in kind to the J&K/Ladakh and DNH/Daman & Diu merges already in D2, and handled the same
way: **sum the raw counts in every year, before any ratio.** It did not arise earlier because the
split predates the original FY2018–FY2023 window.

**Effect:** the 12-year panel has **32 states × 12 years = 384 rows**, not 33 × 12.
**The 6-year results (F1–F8) are unaffected** — Telangana and AP are correctly separate throughout
FY2018–FY2023, and `scripts/build_panel.py` is left untouched so those results stay reproducible.

Had this been missed, three state-years would have entered the regression with zero infrastructure
and zero deposits — an extreme outlier in exactly the direction that would manufacture a spurious
positive coefficient on branches.

---

**D14 — New direction: add PhonePe Pulse digital-payment data. Reframes the null.**
The physical-infrastructure results (F5–F10) came back null or negative. Working interpretation:
**branches and ATMs are the wrong infrastructure for this period.** India's digital payments boomed
over exactly FY2018–FY2023, so physical footprint is flat-to-declining while the actual channel for
financial access moved to phones. A null on branches is then a substantive result, not only a
variation problem.

- **Next data:** PhonePe Pulse, state-wise, aggregated to the same FY2018–FY2023 window.
- Nothing already estimated is discarded. The physical-infrastructure track stands as reported;
  the digital track is an addition, and the contrast between them is the point.
- ⚠️ PhonePe is **one firm, not the market** — roughly 45–50% of UPI volume. Treat it as a proxy
  for digital-payment penetration, and say so. It also revives the "digital" in the project title,
  which D3 had removed.
- Specification, weighting and H1's pre-committed rule are **not** revised yet. How PhonePe enters
  (regressor? second outcome? interaction?) is an open decision, to be logged separately before
  anything is estimated.

---

**D15 — Merged digital panel: `output/panel_digital.csv`, 33 states × FY2019–FY2023 (165 rows).**
Implements D14's data step. `scripts/merge_phonepe.py`; existing files untouched.

- **FY2018 dropped** — PhonePe's first complete financial year is fy_end=2019. 198 → 165 rows.
- **Denominators follow A4 unchanged:** registered users (stock) **per adult**; transactions and
  value (flows) **per capita**. Also carried: `pp_value_to_nsdp` (rupees transacted per rupee of
  income — dimensionless, so no deflator needed) and `pp_ticket_size_rs` as a diagnostic.
- **Both level and log written** for all three digital series. They grow ~25× in five years, so
  level and log are genuinely different regressors. Choosing between them is a specification
  decision, made below, not a data decision.
- **Access / Usage / AUG are NOT recomputed** on the 165 rows. They keep the min–max scaling pooled
  over the original 198, so the dependent variables are identical to those behind F5–F8 and the two
  tracks stay comparable. Side effect, stated because it looks like a bug otherwise: the normalised
  columns no longer reach exactly 0, since most indicators bottom out in FY2018. Min–max is a
  monotone linear map, so the fixed effects absorb it.
- Asserted on build: 33 states, 5 years, zero nulls, and every banking column **byte-identical** to
  `panel_analysis.csv`.

**Still open, and to be fixed before any estimation:** whether PhonePe enters as a regressor
(does digital payment infrastructure raise access/usage?), as a second outcome (is digital where
inclusion actually happened?), or as an interaction with branches. Recorded here so the choice is
made on reasoning rather than on whichever specification returns stars.

---

**D16 — Resolves D15's open item: UPI enters as a THIRD REGRESSOR, alongside branches and ATMs.
Measure = PhonePe registered users per adult, level (not log).**

User directed: run the same two-way FE as Step 5, adding UPI as an IV, for both Access and Usage.

- **Which PhonePe series, and why not transactions.** Three candidates existed: registered users
  per adult, transactions per capita, value per capita. Transactions/value are themselves *usage*
  of the digital channel — using them to predict the Usage equation would be close to circular
  (a flow explaining a flow of the same kind). **Registered users per adult** is an adoption/stock
  measure — whether the channel is available and taken up at all — the same role branches and ATMs
  play for physical infrastructure. That is the measure used.
- **Level, not log.** Branches and ATMs already enter as levels (per lakh adults); keeping UPI as a
  level (per adult) keeps all three infrastructure regressors in the same kind of unit. Log versions
  exist in the data (D15) and are not used here.
- **Panel is `output/panel_digital.csv`: 33 states × FY2019–FY2023 = 165 rows**, one year shorter
  than the branches/ATMs-only run (F5–F8), because PhonePe data starts at fy_end=2019. This means
  the branches/ATMs coefficients in this spec are **not directly comparable** to F5–F8 — same
  regressors, different sample.
- **AUG is estimated too**, unchanged from Step 5's logic: it is not a fourth finding, only the
  vehicle for the standard error on (Access − Usage), and the θ = β − δ identity is asserted again.
- Model, diagnostics and clustering **otherwise identical to Step 5**: two-way FE (state + year),
  SEs clustered by state, `linearmodels.PanelOLS`. No new diagnostics (Hausman, robustness) run
  unless asked — this is one estimation, not a repeat of the full plan.

---

**D17 — Decompose Access and Usage into their four underlying indicators, and re-run.
Purpose: test whether F12's UPI→Access coefficient is an accounting relationship.**

F12 flagged that PhonePe registration requires a KYC-linked bank account, so `pp_users_per_adult`
and `deposit_accts_per_adult` — half the Access DV — are definitionally entangled (the A7 problem
that dropping PMJDY was meant to remove). **Credit accounts are not entangled in the same way:** a
bank loan account is neither required for nor created by PhonePe registration, and BSR covers
scheduled commercial banks, so PhonePe's own partner-originated lending is not in this series.
The entanglement there is ordinary endogeneity, not accounting.

**Run:** the same spec as D16 (two-way FE, SEs clustered by state, N=165), with each of the four
normalised indicators as its own dependent variable:

| | Access side (per adult) | Usage side (per capita) |
|---|---|---|
| deposits | `norm_deposit_accts_per_adult` ⚠️ entangled | `norm_deposits_per_capita` |
| credit | `norm_credit_accts_per_adult` ✅ clean | `norm_credit_per_capita` |

Plus a **credit-only H1 triple**: Access_c = `norm_credit_accts_per_adult`, Usage unchanged,
AUG_c = Access_c − Usage.

**Decision rule, fixed before the regressions are run:**
- If UPI → credit accounts is **large and significant**, F12's Access result is not merely
  definitional, and it stands as reported with the caveat attached.
- If UPI → credit accounts is **null while UPI → deposit accounts is large**, then F12's Access
  coefficient is **the accounting relationship**, and Access must thereafter be reported
  credit-only, with the deposit-account version withdrawn rather than shown alongside it.
- If **both are large**, the deposit result is still not clean — only the credit result gets a
  substantive reading. No averaging the two conclusions.

**Free check that comes with this:** the four indicators enter Access and Usage as simple means
(A3), so by linearity the Access coefficient must equal the mean of its two component coefficients.
Asserted in the script.

**Bonus:** credit-only Access is also free of the D7 data defect (Delhi 2023, Chandigarh 2023 are
*savings*-account breaks), so that robustness concern does not apply to it.

**Outcome (F13):** rule returned *"credit-only survives"*. The entangled channel (deposit accounts)
is **null**; the clean channel (credit accounts) carries the whole effect, and is unmoved by the D7
check. **Access is reported credit-only from here** — not because the rule forced it, but because the
D7 check showed the composite was averaging a real credit effect with a defect-driven artefact.

---

## Open

**Nothing open. Analysis complete (F14).**

- ~~Eyeball Maharashtra: loan accounts per adult rise 0.29 → 0.78 over six years — check it isn't
  driving the result.~~ **Closed by F14.** Done properly rather than by eye: the headline coefficient
  was refit 33 times, dropping each state in turn. Maharashtra is indeed the most influential
  (0.439 → 0.356) but the result is *more* significant without it. No sign flips, no refit loses 5%
  significance.

### If this is picked up again

Three things would strengthen it, in order of value:

1. **An identification strategy for UPI.** The current digital result is a within-state correlation
   between two co-trending series. Candidate instruments: state-level 4G rollout timing, or the
   staggered geography of Jio's 2016–17 entry.
2. **Total UPI, not one firm.** NPCI publishes state-level UPI aggregates that would replace the
   PhonePe proxy and remove the varying-market-share problem (D14).
3. **Extend the digital panel.** PhonePe data runs to FY2026 in the clone; the banking series stop at
   FY2023 (D8). Updating BSR and the Handbook would take the digital track from 5 years to 8.
