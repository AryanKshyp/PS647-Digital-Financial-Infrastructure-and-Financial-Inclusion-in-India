# H5 — Execution Plan

**Digital Literacy and Income: Digital Literacy and Income as Complements to Digital Financial Infrastructure**

PS 647 · This is the *buildable* version of `H5_analysis_plan.md`, rewritten against what the H1
track actually produced (`ps647_final/`). It follows H1's logging discipline: decisions get D-numbers,
findings get F-numbers, gates are pre-committed before estimation.

---

## 0. The one-paragraph version

H1 built a 33-state × FY2019–FY2023 panel and found one thing that worked: **UPI adoption
(PhonePe registered users per adult) raises credit accounts per adult by +0.439 (p=0.0001)**, robust
to leave-one-state-out, while branches and ATMs do nothing. H5 asks the obvious next question:
**+0.439 for whom?** Same panel, same estimator, same dependent variables, same clustering — the
only new objects are two moderators and their interactions with UPI. H1's main effect becomes H5's
baseline; H5 splits it. Nothing in H1 has to be re-run, re-built, or revised.

---

## 1. What changed from `H5_analysis_plan.md`, and why

The original H5 plan was written before the H1 data existed. Five of its assumptions are now known
to be wrong for this project. Recording them here so the change is visible rather than silent.

| # | Original plan said | Reality in `ps647_final/` | What H5 does instead |
|---|---|---|---|
| 1 | Panel spine = **district × quarter, 2019–2025**, ~640 × 24 | H1 is **state × financial year, FY2019–FY2023**, N=165. Banking outcomes (BSR credit/deposit accounts) exist only at state level in what was fetched | **Track A = state × FY, N=165.** Identical spine to H1. Track B (district) is optional, §9 |
| 2 | DFI = PCA index over internet subs, teledensity, BharatNet, branches, ATMs | D10 **forbids composite indices** — "no composite index is built, and none is reported, not even as a robustness check." TRAI/BharatNet were never fetched | **DFI = PhonePe registered users per adult, level.** The single regressor D16 already validated. No index |
| 3 | Primary DV = **UPI transactions per capita** | UPI is the **regressor** here (D16). Using PhonePe transactions as DV against PhonePe users as IV is the circularity D16 explicitly rejected | **DV = the H1 outcome set** (credit accounts/adult, deposits ₹/capita, credit ₹/capita). PhonePe-intensity DV appears only as a labelled supplementary, §6.5 |
| 4 | Seven controls entered as main effects | **State fixed effects absorb every time-invariant control** — urban %, literacy 2011, FLIS, SC/ST %. They cannot enter as main effects | They enter as **interaction placebos** (R1) instead. This is strictly better: it is exactly the test that matters |
| 5 | Access DV = account ownership from CAMS/Findex | Ceiling effect confirmed — the plan's own §7 flags 89–94.6% ownership with near-zero variance. Also CAMS is one wave, so no panel | **Access = credit accounts per adult** (D17: the clean, non-entangled channel; deposit accounts are definitionally tied to PhonePe registration) |

**The one thing that got better.** The original plan's §5.3 "sharp test" needs an access DV and a
usage DV measured on the same units, same panel, same normalisation. **H1 already built exactly
that** — `Access` and `Usage`, min–max normalised over a common pool (A2), with the difference
`AUG = Access − Usage` and its standard error already estimated. H5's key term drops straight into
H1's equation. The plan's claim "one model, two hypotheses, no overlap" is literally true here.

---

## 2. Hypothesis, restated for this panel

**H5.** The effect of digital financial infrastructure on financial inclusion is conditional on the
population's **complementary endowments**.

- **H5a (skills).** The UPI → inclusion effect is stronger where digital literacy is higher.
- **H5b (resources).** The UPI → inclusion effect is stronger where household resources are higher.
- **Corollary (the sharp test).** Complementary endowments should condition **usage**, not **access**.

### The reframing that has to be stated out loud

The digital-divide literature's *first level* is physical access to ICTs; its *second level* is
skilled use. This panel does not contain those variables. What it contains is:

| Divide level | Original plan's proxy | **This panel's proxy** |
|---|---|---|
| First — access | % adults with an account | **Credit accounts per adult** — the extensive margin: does a formal relationship exist at all |
| Second — usage | UPI transactions per capita | **Deposits ₹/capita, credit ₹/capita** — the intensive margin: how much moves through it |

This is a *mapping*, not an identity, and the write-up must say so in one sentence rather than
burying it. The defensible claim is the **extensive-vs-intensive margin** version of H5: conversion
capacity should matter more for how much money flows than for whether an account exists. That is a
real, falsifiable restatement and it is the one this data can carry.

### What H5 inherits from H1, and cannot fix

`../h1_access_vs_usage/LIMITATIONS.md` §1–2 apply in full and must be repeated, not quietly dropped:

- The UPI result is a **within-state correlation between two co-trending series**. Year FE removes
  the common national trend, not state-specific trends. **No causal claim is available.**
- UPI was added **after** the physical null, so it is **exploratory by construction** (D10 named
  branches and ATMs).

**Therefore H5's β₃ is a heterogeneity result, not a causal one.** The honest sentence is: *"the
UPI–inclusion association is steeper in states with more digital literacy."* That is still worth
having — heterogeneity in an association is informative about mechanism, and the sharp test (§6.3)
is a *within-observation* comparison that differences out any confounder acting equally on access
and usage. Overclaiming here is the single most likely way this section gets marked down.

---

## 3. Variables

### 3.1 Dependent variables — all already in `../h1_access_vs_usage/output/panel_digital.csv`, zero fetch cost

| Role | Column | Margin | Status |
|---|---|---|---|
| **Primary access** | `norm_credit_accts_per_adult` | extensive | ✅ clean (D17, F13) |
| Secondary access | `norm_deposit_accts_per_adult` | extensive | ⚠️ entangled with PhonePe KYC; report, never headline |
| **Primary usage** | `norm_deposits_per_capita` | intensive | ✅ clean |
| **Primary usage** | `norm_credit_per_capita` | intensive | ✅ clean |
| Composites | `Access`, `Usage`, `AUG` | — | keep for continuity with F12; `Access` is deposit-contaminated, so credit-only is the headline |

All are min–max normalised pooled over the original 198 state-years (A2). **Do not re-normalise.**
If H5 re-scales them, every coefficient stops being comparable to F12/F13 and the report loses its
spine.

### 3.2 Independent variable

`pp_users_per_adult` — PhonePe registered users per adult, **level**, exactly as D16 fixed it.
Within-state variation 67.1% (F11), so the variation gate that killed the physical track does not
apply. Branches and ATMs stay in as controls, unchanged, so the H5 columns sit directly beside F12's.

### 3.3 Moderators — the only genuinely new data

**H5a — Digital literacy, `diglit_s`. Time-invariant, state level.**

*Primary source: NSS 75th round (2017-18), Report 585, "Household Social Consumption: Education".*
State × sector tables of the percentage of persons able to **operate a computer** and able to **use
the internet**. Take the all-persons state figure; if only rural/urban are published, weight by the
state's Census urban share.

Chosen over the NSS 78th MIS for three reasons, all pre-committed:

1. **It strictly pre-dates every outcome year.** Outcomes run FY2019–FY2023; the moderator is
   2017-18. Robustness check R4 in the original plan ("break reverse causality by lagging the
   moderator") is satisfied *by construction* rather than by assertion. MIS 78th (2020-21) sits
   inside the outcome window.
2. It is an **ability** item, not a usage item — "able to operate a computer" measures skill
   endowment, which is what H5a is about. It is not conditional on the respondent having a
   connection, which is the confound the original plan's item-screen (§3.3) was built to avoid.
3. The state tables are in a public MoSPI PDF. The MIS 78th state tables sit behind dataful.in.

*Robustness moderators (R2), in priority order:*

| Measure | Source | Why it is a different construct |
|---|---|---|
| MIS 78th round 6-item skill index (PCA + simple mean) | NSS 78th, dataful.in / MoSPI report | The original plan's preferred measure; richer skill content |
| % women who have ever used the internet | **NFHS-5 (2019-21)**, state factsheets | Different survey, different respondents, and the only one also available at **district** level (783-district Track B, §9) |
| PMGDISHA certified per 1,000 rural adults | data.gov.in | Policy-delivered skilling, not self-reported ability. Excludes urban agglomerations — see R8 |
| Census 2011 household computer ownership | Census 2011 HH-14 | Pre-treatment by a decade; pure material-access measure |

**Report the primary and all obtainable robustness versions side by side.** Reporting only whichever
one produces stars is index-shopping, and the original plan flags that risk correctly.

**H5b — Resources, `income_s`. Time-invariant, state level.**

*Primary:* `ln_nsdp_pc` **averaged over FY2019–FY2023** per state. Already in the panel — zero fetch.
Made time-invariant deliberately, so H5a and H5b moderators have identical structure and the horse
race in §6.2 is fair rather than an artefact of one moderator having five times the variation.

The time-varying `ln_nsdp_pc` **stays in as a main-effect control**, exactly as in F12. Do not drop it.

*Robustness:* **MPCE from HCES 2022-23** (state, rural + urban, population-weighted). Worth the fetch
because NSDP per capita carries the same production-booking artefact the project already documents
for banking data — corporate output books to Delhi and Maharashtra, inflating their per-capita income
the way branch-location booking inflates their deposits (`LIMITATIONS.md` §4). MPCE is a household
consumption measure and does not have that problem. If NSDP and MPCE give different answers, MPCE is
the more credible one for a *resources* moderator, and that should be stated now, not after seeing it.

### 3.4 Controls

| Control | How it enters | Why |
|---|---|---|
| `branches_per_lakh_adults`, `atms_per_lakh_adults` | main effect | continuity with F12 |
| `ln_nsdp_pc` (time-varying) | main effect | continuity with F12 |
| state FE `μ_i`, year FE `λ_t` | absorbed | continuity with F12 |
| % urban (Census 2011), literacy rate (Census 2011), NCFE-FLIS 2019 score, SC/ST % | **interacted with UPI, in R1 placebos only** | State FE absorb their main effects. As interactions they are the test that decides whether β₃ is a digital-skill effect or a generic-development effect |

**Do not build an "interact everything simultaneously" specification.** With 33 clusters, each extra
interaction costs real power. R1 runs them **one at a time**, as separate placebo columns.

---

## 4. Data to fetch — the complete list

Everything else comes from `../h1_access_vs_usage/output/panel_digital.csv` untouched.

| # | Item | Source | Level | Rows | Effort |
|---|---|---|---|---|---|
| 1 | **% able to operate a computer / use internet, 2017-18** | NSS 75th Report 585 (MoSPI PDF) | state × sector | 33 | ~2h, PDF table extraction |
| 2 | % urban, literacy rate, SC/ST %, HH computer ownership | Census 2011 (censusindia.gov.in) | state | 33 | ~1h, published tables |
| 3 | NCFE-FLIS 2019 financial literacy score | NCFE 2019 report PDF | state/UT | 33 | ~30min |
| 4 | MIS 78th 6-item ICT skills | dataful.in / MoSPI MIS report | state | 33 | ~2h, access uncertain |
| 5 | NFHS-5 internet use (women, men) | IIPS state + district factsheets | state, **district** | 33 / 707 | ~1h state, ~1 day district |
| 6 | MPCE 2022-23 | HCES 2022-23 factsheet | state × sector | 33 | ~1h |
| 7 | PMGDISHA certified | data.gov.in CSV | state/UT | 36 | ~15min |

**Items 1 and 2 are the minimum viable set.** With those two alone the full primary specification and
the decisive R1 placebo both run. Items 3–7 strengthen the robustness appendix. Item 5 (district) is
only needed if Track B goes ahead.

**State-name harmonisation is not optional.** Every fetched file must be mapped onto the 33 keys in
`panel_digital.csv`, applying D1 (drop Lakshadweep, DNH&DD) and D2 (J&K + Ladakh summed). Telangana
and Andhra Pradesh stay **separate** here — D13's merge applies only to the 12-year panel.

---

## 5. Gates — run before any interaction is estimated

Both thresholds are fixed now, in writing, before the data exists. This is the F0 discipline.

### Gate 1 — Is the moderator distinguishable from the regressor?

Compute, across the 33 states, the correlation between `diglit_s` and state-mean
`pp_users_per_adult`; likewise for `income_s`.

| corr | Verdict |
|---|---|
| < 0.70 | **PASS** — estimate as specified |
| 0.70 – 0.85 | **WEAK** — estimate, report the correlation and VIFs on the interaction terms alongside every coefficient |
| > 0.85 | **FAIL** — the raw interaction is not interpretable. Switch to the residualised moderator (R3) before going further |

**Already known, and it is encouraging:** corr(state-mean UPI adoption, state-mean ln NSDP pc) =
**0.687** across the 33 states — inside PASS, just. So H5b is testable as specified without
residualisation. H5a's correlation is unknown until item 1 is fetched, and digital literacy is the
more likely of the two to breach the line.

### Gate 2 — Does the moderator have usable spread?

Report min, max, IQR and the coefficient of variation of `diglit_s` across 33 states. If the
interquartile range is under half a standard deviation, the interaction is being identified off a
handful of extreme states and a leave-one-out (R5) is mandatory rather than optional. Kerala and
Bihar are the obvious poles; the finding must not be *only* Kerala.

### Gate 3 — Is the interaction identified at all?

Report within-state variation of `UPI × diglit_s` using the same `xtsum` decomposition as F4/F11. It
should be close to UPI's own 67.1%, since `diglit_s` is a constant multiplier within state. If it is
not, something is wrong with the merge. **This is a build check, not a substantive gate** — record
it and move on.

---

## 6. Specifications

All two-way FE (state + year), `linearmodels.PanelOLS`, SEs clustered by state, N = 165 — identical
to `../h1_access_vs_usage/scripts/estimate_digital.py`. **All continuous variables mean-centred before interacting**, so
β₁ reads as the UPI effect at average complementary endowments, not at an out-of-support zero.

`diglit_s` and `income_s` are time-invariant and absorbed by state FE. Their interactions with UPI
are still identified, from within-state variation in UPI. Say this in a footnote — someone will ask.

### 6.1 Baseline

```
Y_it = β₁·UPI_it
     + β₃·(UPI_it × DigLit_s)        ← H5a
     + β₄·(UPI_it × Income_s)        ← H5b
     + γ₁·branches_it + γ₂·ATMs_it + γ₃·lnNSDP_it
     + μ_i + λ_t + ε_it
```

Run for each DV in §3.1. **Headline DV = `norm_credit_accts_per_adult`**, because that is the DV
F13/F14 established as clean and stable.

### 6.2 Sequential entry — four columns, the horse race

| Col | Specification | What it shows |
|---|---|---|
| (1) | UPI only | replicates F12 exactly — **must match to the 5th decimal, or the merge broke something** |
| (2) | + UPI × DigLit | H5a alone |
| (3) | + UPI × Income | H5b alone |
| (4) | + both | **preferred** |

Column (1) is a build assertion, not a result. If β₃ is large in (2) and collapses in (4), the skills
result was income all along. **That is a finding and gets reported as one.**

### 6.3 The sharp test — stacked DV

Stack the three clean DVs in long form, one row per state × year × outcome, N = 165 × 3 = **495**:

```
Y_itk = β₁·UPI_it
      + β₂·(UPI_it × Intensive_k)                  ← this is H1's test
      + β₃·(UPI_it × DigLit_s)
      + β₅·(UPI_it × DigLit_s × Intensive_k)       ← H5's key term
      + β₄·(UPI_it × Income_s)
      + β₆·(UPI_it × Income_s × Intensive_k)
      + γ'X_it + μ_i + λ_t + θ_k + ε_itk
```

`Intensive_k = 0` for credit accounts/adult; `= 1` for deposits ₹/capita and credit ₹/capita.
Cluster by state (33 clusters, 495 rows).

**β₅ > 0 is the strongest evidence H5 can produce in this data.** A state that is simply richer or
more developed would show up in β₃ and β₄ — but it would not predict that the moderation is
*specific to the intensive margin*. β₅ isolates that. And because it is a within-state-year
comparison across outcomes, any confounder that moves access and usage together differences out.

`Y` must be standardised **within outcome** (mean 0, SD 1 per k) before stacking, or β₅ just picks up
that the three DVs have different scales. Note this diverges from A2's pooled min–max: it applies
*only* inside the stacked specification, and the un-stacked §6.1 results keep the original scaling so
they stay comparable to F12/F13.

### 6.4 Threshold specification

The original plan's §5.4, unchanged — literacy may work as a floor, not a gradient:

```
Y_it = β₁·UPI_it + Σ_{k=2,3} δ_k·(UPI_it × 1[DigLit_s ∈ tercile k]) + γ'X_it + μ_i + λ_t + ε_it
```

- `δ₃ > δ₂ > 0` → increasing returns to skill, true complementarity
- `δ₂ ≈ δ₃ > 0` → floor effect: literacy matters up to a threshold, then stops (the ICRIER
  "necessary but not sufficient" reading)
- 11 states per tercile. Report the tercile membership so the reader can see which states are where.

### 6.5 Supplementary — digital-channel intensity

Reported separately and clearly labelled, because it is not clean:

```
ln(pp_txns_per_capita)_it = β₁·UPI_it + β₃·(UPI_it × DigLit_s) + ... + μ_i + λ_t + ε_it
```

**The entanglement, stated up front:** a PhonePe transaction requires a PhonePe registration, so the
DV cannot rise without the IV rising. β₁ is uninterpretable. **β₃ is the only coefficient read from
this specification** — whether the *slope* of transactions on registrations is steeper in
high-literacy states. That is a conversion-rate question, and the mechanical link does not obviously
generate a differential. It goes in an appendix, not the main table.

---

## 7. Pre-committed decision rules

Fixed now. Not to be revised after coefficients are seen. This is D10's discipline and it is what
made the H1 write-up credible.

### H5a / H5b verdict — from §6.1 column (4), headline DV

| Result | Verdict |
|---|---|
| β₃ > 0, p < 0.05 | **H5a supported** — skills channel operates |
| β₄ > 0, p < 0.05 | **H5b supported** — resources channel operates |
| β₃ > 0, β₄ ≈ 0 | Conversion is **capability**-constrained → policy: skilling |
| β₃ ≈ 0, β₄ > 0 | Conversion is **affordability**-constrained → policy: subsidy (Cole–Sampson–Zia) |
| both > 0 | Independent channels; both bind |
| both ≈ 0 | **H5 not supported** — infrastructure converts uniformly. A genuine convergence finding |
| β₃ < 0 | **Catch-up** — low-literacy states gain most. Report it; it is the more interesting result |

### The R1 override — this one outranks the table above

If the placebo interactions (UPI × 2011 general literacy, UPI × urban %) return a β of **similar
magnitude and significance** to β₃, then β₃ is **not** identifying a digital-skill effect. It is a
generic development gradient. In that case H5a is reported as **not separately identified**,
regardless of its own p-value. Fixed in advance because it is the first thing any examiner asks.

### The sharp-test verdict

| Result | Reading |
|---|---|
| β₅ > 0, p < 0.05 | **H5's corollary holds.** Complementary endowments conditions the intensive margin specifically — the strongest available claim |
| β₅ ≈ 0 while β₃ > 0 | Complementary endowments is a **generic** moderator, not a second-level one. The theoretical framing is not supported even though H5a is |
| β₅ < 0 | Capacity matters more for *getting* an account than for *using* it. Contradicts the framework; report it |

### Power, acknowledged in advance

33 clusters, one time-invariant moderator each. A β₃ that is economically large but p ≈ 0.15 is the
most likely outcome, and it is **not** the same as a null. Report the point estimate, the CI, and the
wild-cluster-bootstrap p, and say which of the two situations the data is in. Pre-committing this
prevents the temptation to hunt specifications until something clears 0.05.

---

## 8. Robustness — mapped from the original plan onto this panel

| # | Check | Status |
|---|---|---|
| **R1** | **Placebo interactions:** swap DigLit for 2011 general literacy, % urban, and log NSDP, one at a time | **Run first. Decisive — see the override above** |
| R2 | Alternative moderators: MIS 78th index, NFHS-5 internet use, PMGDISHA, Census computer ownership; MPCE for income | Needs fetch items 4–7 |
| R3 | Residualise: `DigLit = π₀ + π₁·(state-mean UPI) + ν`, interact `ν̂`; bootstrap SEs | Mandatory only if Gate 1 returns FAIL |
| R4 | Lag structure | **Satisfied by construction** — moderator 2017-18, outcomes FY2019–23 |
| R5 | **Leave-one-state-out**, 33 refits | Reuse `../h1_access_vs_usage/scripts/leave_one_out.py`. F14 already did this for the main effect; do it for β₃. Mandatory if Gate 2 is marginal |
| R6 | Wild cluster bootstrap on β₃, β₄, β₅ | **Mandatory.** 33 clusters. Report alongside every clustered p |
| R7 | D7 defect cells: drop Delhi 2023 and Chandigarh 2023 | Reuse `../h1_access_vs_usage/scripts/robustness.py`. Applies to deposit-based DVs only — credit accounts are unaffected (D17) |
| R8 | Drop Delhi, Chandigarh, Puducherry, A&N | Small UTs are outliers on both moderators; PMGDISHA excludes urban agglomerations |
| R9 | Deposit-accounts DV, reported but not headlined | The D17 entanglement check, extended to the interaction |
| R10 | Composite `Access`/`Usage`/`AUG` DVs | Continuity with F12. Not headline, per D17 |

---

## 9. Track B — the district extension (optional, high value, ~2 days)

**This is genuinely available and nobody on the project has used it yet.** The PhonePe clone in
`raw/phonepe_pulse/` contains **district-level** quarterly data that was never touched:

- `map/transaction/hover/country/india/state/<state>/<year>/<q>.json` → transaction count and value
- `map/user/hover/country/india/state/<state>/<year>/<q>.json` → registered users

Verified on disk: **783 district-rows per quarter, all 36 states/UTs, complete from 2019Q1 through
2023Q4** (and running to 2026). At FY2019–FY2023 that is **783 × 20 ≈ 15,660 rows** against Track A's
165, and **~700 clusters** against 33. The power problem in §7 disappears.

| | Track A | Track B |
|---|---|---|
| Spine | state × FY | **district × quarter** |
| N | 165 | ~15,660 |
| Clusters | 33 | ~700 (cluster at district, or two-way district + state) |
| DV | credit accounts/adult, ₹/capita | `ln(1 + UPI txns per capita)` |
| IV | PhonePe users per adult | PhonePe users per adult |
| Moderator | NSS 75th (state) | **NFHS-5 district internet use** (707 districts) |

**A useful property, worth stating in the methods section.** In a log specification,
`ln(txns/pop) = ln(txns) − ln(pop)`. If district population is held time-invariant, `ln(pop)` is a
district constant and is **absorbed entirely by the district fixed effect**. So Track B's estimates
do not depend on having good district population projections — Census 2011 populations suffice. This
sidesteps the interpolated-population limitation (D6) that Track A carries.

**What it costs:** district name harmonisation between PhonePe and NFHS-5. This is the whole job and
it is not trivial — PhonePe uses live district names ("kasargod district"), NFHS-5 uses 2011-vintage
Census districts, and roughly 100 districts were split or renamed between 2011 and 2023. Budget most
of the two days for the crosswalk, and report the match rate and which districts were dropped.

**Recommendation: do Track A first and completely.** Track B is the upgrade, not the deliverable. If
Track A's β₃ is directionally clear but underpowered — the most likely outcome — Track B is the right
answer to that and worth the two days. If Track A returns a flat null with tight CIs, Track B will
mostly confirm it and the time is better spent on the write-up.

---

## 10. Threats to validity

| Threat | Severity | Mitigation |
|---|---|---|
| **β₃ is a generic development gradient, not a skills effect** | **High** | R1 placebos + the pre-committed override in §7. This is the load-bearing check |
| **The main effect it moderates is not causal** (`LIMITATIONS.md` §1) | **High** | Cannot be fixed. State it plainly; frame every H5 result as heterogeneity in an association. The sharp test (β₅) partially escapes it by differencing across outcomes |
| Low power — 33 clusters, one time-invariant moderator | High | Wild cluster bootstrap (R6); report CIs not just stars; §7's pre-commitment that "large but p=0.15" ≠ null; Track B if needed |
| Collinearity DigLit–UPI | Medium | Gate 1; R3 residualisation if it fails. Income already known clear at 0.687 |
| **PhonePe market share varies by state** and may correlate with digital literacy | **Medium** | Not previously flagged as an H5-specific problem, and it is one: if PhonePe's share is higher in high-literacy states, β₃ is partly measurement. Check against NPCI's state-wise UPI totals (published June 2025) — this is the single most valuable half-day of extra data work |
| Moderator measured at state level, mechanism is individual | Medium | Standard ecological-inference caveat. Track B narrows the unit but does not remove it |
| Boundary merges (D2) mean J&K+Ladakh is one unit | Low | Inherited from H1, already documented |
| Self-reported ICT ability | Low–Med | Biases *against* finding complementarity where it matters most — conservative, note it |

---

## 11. Work plan

Scripts follow the H1 convention: read from `data/` and `output/`, write to `output/`, fixed
filenames so the report cites files not scrollback.

| Step | Task | Script | Output |
|---|---|---|---|
| 0 | **Fix the hardcoded paths.** Every script in `scripts/` has `OUT = Path("/home/yuvraj/ps647_final/output")` — a Linux path from another machine. Make it repo-relative. Install `pandas`, `numpy`, `linearmodels`, `scipy` (none are present locally) | — | runnable repo |
| 1 | Fetch + harmonise moderators onto the 33 state keys | `build_moderators.py` | `../data/09_diglit.csv`, `data/10_state_controls.csv` |
| 2 | Merge into `panel_digital.csv`, mean-centre, build interactions | `build_h5_panel.py` | `output/panel_h5.csv` (165 × ~45) |
| 3 | **Gates 1–3.** Correlations, spread, within-variation | `h5_gates.py` | `output/table14_h5_gates.csv` → **go / no-go** |
| 4 | Baseline + sequential entry (§6.1–6.2) | `estimate_h5.py` | `output/table15_h5_main.csv` |
| 5 | **R1 placebos** (§7 override) | `h5_placebo.py` | `output/table16_h5_placebo.csv` |
| 6 | Stacked sharp test (§6.3) | `estimate_h5_stacked.py` | `output/table17_h5_stacked.csv` — **the headline** |
| 7 | Threshold terciles (§6.4) | `estimate_h5_threshold.py` | `output/table18_h5_threshold.csv` |
| 8 | R5 leave-one-out, R6 bootstrap, R7–R10 | `h5_robustness.py` | `output/table19_h5_robustness.csv` |
| 9 | Figures: marginal effect of UPI across the DigLit range, with CI band | `plot_h5.py` | `output/fig4_h5_margins.png` |
| 10 | Write up; append F15+ to `FINDINGS.md`, D18+ to `DECISIONS.md` | — | H5 chapter |

**Step 3 is the gate.** Step 5 outranks step 4. Steps 4 and 6 are the deliverable.

**Ordering note.** Write the F-number entry for each result *before* interpreting it, as `FINDINGS.md`
does. The H1 track's credibility comes almost entirely from having done this.

---

## 12. What we can claim, by outcome

**If β₃ > 0 and β₅ > 0 and R1 clears:** uniform national digital-payment rollout *widens*
state-level gaps in financial deepening, because identical adoption converts into use at different
rates depending on pre-existing skill. Digital skilling must be sequenced alongside connectivity
spending, not after it. Combined with H1 — infrastructure raised access more than usage — the joint
story is that **digitalisation expanded formal access broadly but reproduced exclusion at the usage
margin, and the states least able to convert are the ones that were already behind.** That answers
the main PS's second half directly.

**If β₄ dominates β₃:** the binding constraint is affordability, not capability, consistent with
Cole–Sampson–Zia. Policy shifts to transaction-cost and device subsidy rather than training.

**If both ≈ 0:** UPI converts uniformly across states regardless of skill or income — a genuine
convergence finding, and given H1's result a striking one: the channel that worked, worked
everywhere. Report it as a null with the CIs attached, not as a failure.

**If R1 fires:** report that complementary endowments cannot be separated from general development at
state level with 33 observations, and that Track B (783 districts) is the design that could. That is
a methodological finding of the same kind as H1's F4, and this project has already shown it knows how
to report one honestly.

---

## Appendix — relationship to H1, for the joint report

| | Interacts DFI with… | Key coefficient | Table |
|---|---|---|---|
| **H1** | *type of outcome* — access vs usage | β₂ in §6.3 | already estimated: `table9`, `table11` |
| **H5** | *complementary endowments* — skills + resources | β₅ in §6.3 | `table17` |

Both come out of **the same stacked equation**. Present them as adjacent columns of one table, with
H1 as column (1) and H5 as column (2). The report then has a single empirical model rather than two
studies stapled together, which is the strongest structural claim the group can make.

If a triple interaction with gender or rural status is wanted later, run **only one**, and
`UPI × DigLit × Female` is the natural choice given the main PS. Triple interactions exhaust power
fast, and at 33 clusters there is none to spare.
