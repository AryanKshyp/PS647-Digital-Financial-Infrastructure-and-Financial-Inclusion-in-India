# Findings Log — H1

Append-only. Each entry records what was run, what came out, and what it means — written **as the
result appears, before interpreting it**. A diagnostic that fails is a finding and gets logged.

Decisions live in `DECISIONS.md`. Steps live in `EXECUTION_PLAN.md`. Tables live in `output/`.

---

## F0 — Assumptions, fixed before any result was produced

Recorded first, deliberately, so no reading of the plan can be adjusted after seeing coefficients.

| # | Assumption | Basis |
|---|---|---|
| A1 | The PDF's "Access 35%, Usage 45%" weights are **ignored**. Those weight RBI's composite FI-Index; this design keeps Access and Usage as two separate dependent variables, so there is nothing for them to weight. Applying them would make AUG = 0.35A − 0.45U, contradicting the PDF's own definition `AUG = Access − Usage`. | user confirmed |
| A2 | 0–1 normalisation is **min–max pooled over all 198 state-years** — one min and max per indicator across the whole panel. Preserves genuine growth over time, which is what the fixed-effects model estimates from. Within-year rescaling was rejected: it would erase the national time trend and gut the year fixed effects. | user confirmed |
| A3 | Inside Access, and inside Usage, the two indicators carry **equal weight** (simple average). The PDF specifies no within-dimension weights. | follows from A1 |
| A4 | **"Per adult" = population 18+; "per capita" = total population.** The PDF uses the two terms deliberately — Access is per adult, Usage is per capita. Both denominators are available in the population file. | PDF wording |
| A5 | N = **198** (33 states × 6 years), against the PDF's anticipated ≈210 (≈30 states × 7 years). Fewer years, more states. | D8 |
| A6 | Of the four suspect deposit-account cells in D7, only **Delhi 2023 and Chandigarh 2023** fall inside FY2018–FY2023. Delhi 2024 and Haryana 2024 are outside the panel and need no action. | D7 + D8 |
| A7 | The PDF's construction rule — infrastructure on one side, accounts and balances on the other, never both — **is satisfied**. Branches and ATMs are the regressors; accounts and balances are the outcomes; nothing appears on both sides. Dropping PMJDY (D3) is what removed the overlap, since PMJDY accounts are an account count and would have sat on both sides, producing the mechanical correlation the PDF warns against. | PDF construction rule |

**Note on A7:** D3 was taken as a scope decision, but it turns out to be load-bearing for
identification, not merely a simplification.

---

## F1 — Merged panel built (Step 1)

`scripts/build_panel.py` → `output/panel_raw.csv`

- **198 rows = 33 states × 6 years (FY2018–FY2023). No nulls, no non-positive values.** All eight
  sources contributed 198 rows and 33 states each, so the inner joins lost nothing.
- D2 merges applied by **summing raw counts before any ratio**: J&K + Ladakh, and DNH + Daman + Diu.
- D1 drops applied: Lakshadweep and the merged DNH/Daman & Diu. Region rows and ALL-INDIA removed.
- **D9 spot-check survives the merge** — Maharashtra at `fy_end=2018` returns branches 12,545,
  ATMs 25,651, income ₹172,663, all matching RBI's published figures exactly.
- State matching uses **word-boundary** regex. A naive substring test folds "AN-DAMAN" into the
  Daman & Diu group; that bug occurred once during data preparation and is now asserted against
  explicitly (`check_andaman_not_folded`).

## F2 — Analysis variables constructed (Step 2)

`scripts/build_variables.py` → `output/panel_analysis.csv`

Per D10 the independent variables are **two separate regressors in real units** — no index, no
normalisation, no weights.

| | range | mean |
|---|---|---|
| Branches per lakh adults | 8.58 – 66.68 | 21.56 |
| ATMs per lakh adults | 11.12 – 100.18 | 32.72 |

The four dependent indicators were min–max normalised pooled (A2) and combined with equal weight
(A3). Both denominators used as the PDF specifies (A4) — Access per adult, Usage per capita:

| | range | mean |
|---|---|---|
| Access (0–1) | 0.010 – 0.959 | 0.250 |
| Usage (0–1) | 0.000 – 0.978 | 0.147 |
| AUG = Access − Usage | −0.459 – 0.422 | 0.104 |

Checks passed: `AUG = Access − Usage` holds exactly; all four normalised indicators span [0,1].

**Not yet a result, but worth recording before estimation:** mean AUG is **positive (+0.104)**,
i.e. across the panel Access sits above Usage on a common 0–1 scale. That is a level fact about the
raw data, not evidence for H1 — H1 is about whether *infrastructure widens* that gap, which only the
regressions can say. Recorded here so it cannot later be mistaken for a finding.

## F3 — Descriptives (Step 3)

`scripts/descriptives.py` → `output/table1_descriptives.csv`

All four sanity gates passed. Credit accounts per adult (0.080–0.866) reproduce the range established
during data validation exactly.

**A6 confirmed empirically.** Deposit accounts per adult above 5 within the window:

- **Chandigarh 2023 (7.69) and Delhi 2023 (7.99)** — the two anomalous cells, and the only two.
- Chandigarh 2018–2022 sits at 5.1–5.4 and Goa at 5.45–5.73 across *all six* years. Both are high
  but flat, so they are genuine levels, not defects, and must **not** be dropped in Step 7.

This confirms the Step 7 robustness check drops exactly two cells, as A6 anticipated.

---

## F4 — Diagnostic (a): within-state variation — **GATE FAILED** (Step 4)

`scripts/within_variation.py` → `output/table2_within_variation.csv`

Thresholds were fixed in the script *before* the numbers were computed: FAIL below 0.10, WEAK below
0.25, PASS above.

| Variable | overall sd | between sd | within sd | within share | median within-state swing | verdict |
|---|---|---|---|---|---|---|
| **Branches per lakh adults** | 11.455 | 11.574 | 0.805 | **7.0%** | 5.6% | **FAIL** |
| **ATMs per lakh adults** | 18.925 | 19.097 | 1.651 | **8.7%** | 11.8% | **FAIL** |
| Access | 0.172 | 0.167 | 0.049 | 28.4% | 47.9% | context |
| Usage | 0.200 | 0.201 | 0.029 | 14.4% | 61.9% | context |
| AUG | 0.128 | 0.127 | 0.029 | 22.9% | 33.6% | context |
| ln(NSDP per capita) | 0.541 | 0.528 | 0.147 | 27.1% | 3.2% | context |

**Roughly 93% of the variation in both regressors is between states, not within them.** Two-way fixed
effects discard exactly that between-state variation. This is precisely the failure the PDF told us to
test for first: *"if DFI barely moves within states, fixed effects have nothing to estimate from."*

**Estimation was not run. Script exits non-zero.**

### Why, diagnosed

1. **Infrastructure stocks are slow-moving.** Raw branch counts swing a median of only 10.7% within a
   state across the six years (Chandigarh 3.6%, Punjab 3.7%); ATMs 17.6%.
2. **The denominator cancels about half of what remains.** Adult population grows a median 10.2% within
   state over the window, in the *same direction* as branches, so the ratio moves less than either part:
   raw branches within share 5.8% and swing 10.7%, but branches *per lakh adults* swing only 5.6%.
   Because adult population is interpolated (D6) it is almost perfectly smooth and contributes no
   independent variation — it only deflates a trend.
3. **The outcomes move far more than the regressors.** Credit accounts have a 30.0% within share and a
   47.8% median swing; Access 28.4%. So Y moves five to ten times more than X within a state. Any
   coefficient estimated here would be identified off a very thin slice of X while Y swings widely —
   wide standard errors are guaranteed regardless of whether an effect exists.

**The problem is the regressors alone.** The dependent variables and the control have ample
within-state variation; the panel is not "too short" in general, it is too short *for infrastructure*.

### Panel length is the binding constraint

Within share for branches per lakh adults, by window:

| Window | Years | N | Within share |
|---|---|---|---|
| 2018–2023 (current) | 6 | 198 | **7.0%** |
| 2014–2023 | 10 | 330 | 13.4% |
| 2012–2023 | 12 | 396 | 20.1% |
| **2011–2023** | **13** | **429** | **23.2%** |

Thirteen years would bring branches to 23.2% — still WEAK by the pre-set threshold, but a different
order of magnitude from 7.0%. **ATMs cannot follow: RBI's state-wise ATM release begins in 2018.**
So the longer panel is available only by dropping ATMs, which contradicts D10.

No decision taken here. Recorded before any interpretation, as the logging discipline requires.

---

## F5 — Main results (Step 5)

`scripts/estimate.py` → `output/table3_main_results.csv`
Two-way FE (state + year), SEs clustered by state, N=198.

| Equation | Regressor | coef | se | p |
|---|---|---|---|---|
| (1) Access | branches/lakh adults | **−0.00897** | 0.00699 | 0.201 |
| (1) Access | ATMs/lakh adults | −0.00164 | 0.00377 | 0.664 |
| (1) Access | ln(NSDP pc) | 0.02340 | 0.04342 | 0.591 |
| (2) Usage | branches/lakh adults | **−0.01264** | 0.00363 | **0.001** |
| (2) Usage | ATMs/lakh adults | −0.00109 | 0.00263 | 0.678 |
| (2) Usage | ln(NSDP pc) | −0.00396 | 0.01502 | 0.793 |
| (3) AUG | branches/lakh adults | +0.00367 | 0.00558 | 0.512 |
| (3) AUG | ATMs/lakh adults | −0.00055 | 0.00159 | 0.731 |

Within-R²: Access 0.069, Usage 0.042, AUG 0.111.

**Identity verified:** θ = β − δ holds exactly for both regressors (branches
−0.00897 − (−0.01264) = +0.00367 = θ). Equation (3) is doing its stated job.

**Joint test (D10, branches = ATMs = 0):** Access χ²=1.97, p=0.374 · Usage χ²=15.07, **p=0.0005** ·
AUG χ²=0.68, p=0.710.

### What the numbers say, before interpretation

1. **Nothing is significant in the Access equation.** Both regressors are near zero, and both carry a
   **negative** sign.
2. **One coefficient is significant: branches → Usage, and it is NEGATIVE** (−0.0126, p=0.001).
   Within a state, years with more branches per lakh adults have *lower* Usage.
3. **AUG is not significant for either regressor** (p=0.512, p=0.731). The formal test of H1 —
   whether the access–usage gap widens with infrastructure — returns nothing.
4. **ATMs are insignificant everywhere**, in all three equations.
5. Explanatory power is very low throughout (within-R² 0.04–0.11), consistent with F4.

### Against H1 as pre-committed in D10

H1 requires **β_access > β_usage > 0** for branches *and* ATMs.

- **Branches:** the *ordering* holds (−0.00897 > −0.01264), but **both coefficients are negative**, so
  `β_usage > 0` fails. And the difference is not significant (AUG p=0.512).
- **ATMs:** the ordering does not even hold (−0.00164 < −0.00109), and nothing is significant.

**H1 is not supported for either regressor.** Not partial support — the positivity condition fails
for branches and the ordering condition fails for ATMs.

**This verdict is constrained by D11.** With within-state variation at 7.0% and 8.7%, a null cannot be
read as "infrastructure does not raise access". The Access nulls are indistinguishable from
insufficient variation. The one significant coefficient — branches → Usage, negative — is the result
that needs explaining, and it is the opposite sign to anything H1 anticipated.

---

## F6 — Diagnostic (b): Hausman, FE vs RE (Step 6)

`scripts/hausman.py` → `output/table4_hausman.csv`

| Equation | χ² | df | p | Favours |
|---|---|---|---|---|
| Access | 108.33 | 3 | <0.0001 | **FE** |
| Usage | 73.18 | 3 | <0.0001 | **FE** |
| AUG | 12.44 | 3 | 0.0060 | **FE** |

H0 (state effects uncorrelated with the regressors) is rejected decisively in all three. **Random
effects is inconsistent here** — state effects *are* correlated with branches and ATMs, exactly the
"wealthier states attract more infrastructure" channel the PDF lists as limitation 4.

**This sharpens the bind rather than resolving it.** Hausman says fixed effects are *required*; F4
says fixed effects have almost nothing to work with (7.0% / 8.7% within-state variation). Dropping
state fixed effects to recover precision is not available — the data itself rejects that
specification. The two diagnostics together say the design cannot be rescued by changing estimator.

## F7 — Robustness per D7 (Step 7)

`scripts/robustness.py` → `output/table5_robustness.csv`
Dropping **Delhi 2023** and **Chandigarh 2023** (2 cells of 198, N: 198 → 196).

| Equation | Regressor | main | p | trimmed | p | |
|---|---|---|---|---|---|---|
| Access | branches | −0.00897 | 0.201 | −0.00570 | 0.078 | |
| Access | **ATMs** | **−0.00164** | 0.664 | **+0.00331** | **0.004** | **sign flip, becomes significant** |
| Usage | branches | −0.01264 | **0.001** | −0.01185 | **0.000** | stable |
| Usage | **ATMs** | −0.00109 | 0.678 | +0.00011 | 0.957 | sign flip |
| AUG | branches | +0.00367 | 0.512 | +0.00615 | 0.098 | |
| AUG | **ATMs** | −0.00055 | 0.731 | +0.00319 | 0.148 | sign flip |

**This is the most important result in the study, and it is a negative one.**

**Two observations out of 198 reverse the sign of every ATM coefficient**, and move ATMs→Access from
null (p=0.664) to significant and positive (p=0.004). A result that depends on two state-years is not
a result. Nothing about ATMs can be concluded in either direction.

This is precisely what F4 predicted. When a regressor has only 7–9% within-state variation, individual
observations carry enormous leverage, and estimates are unstable to trivial perturbations. The Step 4
gate was not a formality; it correctly forecast this fragility.

**One coefficient survives:** branches → Usage stays negative and significant (−0.0126 → −0.0119,
p≤0.001), shifting only 6.2%. It is the only finding in the study robust to the check.

Note the two dropped cells are known defects in RBI's source data (D7), not outliers we disliked. The
fragility is therefore not an artefact of arbitrary trimming — it means the headline ATM result was
being driven by data we had already established was wrong.

---

## F8 — H1 verdict against the pre-committed rule (Step 8)

D10 fixed the rule before any coefficient was seen: **H1 fully supported only if
β_access > β_usage > 0 holds for branches AND for ATMs.**

**Branches** — β_access = −0.00897 (p=0.201), β_usage = −0.01264 (p=0.001).
The *ordering* holds (−0.00897 > −0.01264), but **both are negative**, so `β_usage > 0` fails.
The difference (AUG) is not significant, p=0.512.

**ATMs** — β_access = −0.00164 (p=0.664), β_usage = −0.00109 (p=0.678).
The ordering does **not** hold (−0.00164 < −0.00109), nothing is significant, and F7 shows every
ATM sign reverses when two cells are dropped.

### **H1 is not supported. Not partial support — it fails for both regressors.**

Against the PDF's expected-results table:

| PDF outcome | Applies? |
|---|---|
| β_access > β_usage > 0 → H1 supported | No |
| β_access ≈ β_usage → genuine deepening | No |
| **Both ≈ 0 → check within-state variation before concluding anything** | **Yes — this is the row we land on** |
| β on AUG > 0 and significant → gap widens | No (p=0.512, p=0.731) |

The PDF anticipated this exact outcome and prescribed the response: check within-state variation
before concluding anything. F4 did, in advance, and found 7.0% and 8.7%.

**So the correct conclusion is not "infrastructure does not raise financial inclusion."** It is that
**this design cannot test H1**: over six years, branches and ATMs per lakh adults barely move within
states, the estimator Hausman requires (FE) discards the between-state variation that does exist, and
the resulting estimates are unstable to two observations. The null is uninformative, exactly as D11
fixed in advance that it would be.

### The one robust finding, and it was not predicted

**Branches → Usage is negative and significant** (−0.0126, p=0.001; −0.0119, p<0.001 trimmed;
joint test on Usage χ²=15.07, p=0.0005). Within a state, years with more branches per lakh adults
show *lower* Usage. This is the opposite sign to anything H1 anticipated, and it is the only
coefficient stable across specifications.

It should be treated as a **puzzle, not a result**, for three reasons recorded here rather than
rationalised later:
1. F4's variation problem applies to it as much as to the nulls.
2. Usage is severely compressed — 85% of observations sit below 0.20, skew 2.85, because pooled
   min-max normalisation (A2) is applied to a variable whose top is 14× its median. Delhi and
   Chandigarh set the ceiling and everyone else is squashed. This was identified before estimation
   and deliberately **not** fixed, in order to test the specification as originally written.
3. A negative within-state relationship is at least as consistent with branches being *placed* where
   deposit growth is weak as with branches *causing* weak deposit growth. Nothing here identifies
   direction.

## F9 — Limitations (Step 9)

**From the PDF:**
1. State-level correlation, not person-level. Cannot claim individuals hold unused accounts.
2. Deposits are recorded by branch location, not depositor residence, inflating Maharashtra and Delhi.
3. No connectivity component — reframed as *physical banking infrastructure* (D3).
4. Reverse causality: wealthier states attract infrastructure. **F6 confirms this is live** — Hausman
   rejects RE, i.e. state effects are demonstrably correlated with the regressors.

**Added by this build:**
5. **Within-state variation is 7.0% (branches) and 8.7% (ATMs)** — the binding limitation. The design
   cannot detect an effect of this size regardless of whether one exists (F4, D11).
6. **Estimates are unstable to two observations** (F7). ATM results reverse sign entirely.
7. **Adult population is interpolated**, not published — 243 of 266 state-years use an estimated 18+
   share (D6). Because it is near-linear it also suppresses within-state variation in the regressors.
8. **Usage is severely right-skewed after normalisation** (85% below 0.20), so β_access and β_usage
   are not compared on equivalent scales — a direct threat to the H1 comparison itself.
9. **Panel is FY2018–FY2023, six years, not seven** (D8), and ATMs cannot extend earlier than 2018,
   capping any lengthening of the panel while both regressors are retained.
10. Delhi/Haryana/Chandigarh deposit-account defects in RBI's source (D7); two fall inside the window.

---

## Summary — study complete, Steps 1–9

- Panel built and verified: 33 states × 6 years, 198 rows, zero missing (F1–F3).
- **Step 4 gate failed** and correctly predicted everything downstream (F4).
- **H1 not supported**, but the null is uninformative — the design cannot test it (F5, F8).
- **Hausman requires FE; F4 shows FE has nothing to estimate from.** The bind has no estimator-level
  fix (F6).
- **One robust finding, unpredicted and unexplained:** branches → Usage negative and significant (F7).
- The honest headline is methodological: *a six-year state panel cannot identify the effect of
  banking infrastructure on financial inclusion, because infrastructure does not move enough within
  states over that horizon.*

## F10 — Extended panel, FY2012–FY2023, branches only (D12, D13)

`scripts/build_long.py`, `scripts/estimate_long.py` →
`output/panel_long_analysis.csv`, `table6_long_results.csv`, `table7_long_hausman.csv`,
`table8_long_robustness.csv`

**32 states × 12 years = 384 rows**, balanced, no nulls. ATMs dropped (D12); Andhra Pradesh and
Telangana merged (D13).

**The extension did what it was meant to do.** Within-state variation in branches per lakh adults
rose **7.0% → 15.3%** — more than double, though still WEAK against the 25% threshold.

| Equation | coef (branches) | se | p | within-R² |
|---|---|---|---|---|
| (1) Access | −0.00483 | 0.00645 | 0.455 | −0.172 |
| (2) Usage | **−0.01032** | 0.00570 | **0.071** | −0.478 |
| (3) AUG | **+0.00549** | 0.00385 | 0.155 | 0.215 |

Identity verified: θ = β − δ exactly.

**D7 robustness — no sign flips anywhere**, unlike the six-year panel where every ATM coefficient
reversed:

| Equation | main | p | trimmed | p |
|---|---|---|---|---|
| Access | −0.00483 | 0.455 | −0.00137 | 0.783 |
| Usage | −0.01032 | 0.071 | −0.00843 | 0.087 |
| **AUG** | +0.00549 | 0.155 | **+0.00706** | **0.084** |

**Hausman:** Access now favours **RE** (χ²=3.62, p=0.164); Usage (p<0.0001) and AUG (p=0.032) still
favour FE. Weaker evidence of correlated state effects than in the six-year panel.

### Verdict against the D10 rule, now applied to branches alone

β_access = −0.00483, β_usage = −0.01032. **The ordering holds** (−0.0048 > −0.0103), but **both
coefficients are negative**, so `β_usage > 0` fails.

**H1 is still not supported.** Same conclusion as the six-year panel, reached with twice the
statistical power and without the fragility.

### What did change, and it is the most H1-favourable evidence in the study

**AUG on branches is positive in every specification, and strengthens as the data improves:**
6-year p=0.512 → 12-year p=0.155 → 12-year trimmed **p=0.084**.

The access–usage gap does appear to widen with branch density, in the direction H1 predicts, and the
sign is stable across all four specifications. But it clears only the 10% level at best, and only
after trimming. **This is a suggestive pattern, not a result** — and saying otherwise would be
revising the D10 rule after seeing the coefficients, which D10 explicitly forbids.

### Two caveats that must travel with these numbers

1. **Within-R² is negative for Access (−0.172) and Usage (−0.478).** With two-way fixed effects in
   `linearmodels` this measure can go negative and is not a straightforward goodness-of-fit reading,
   but it does indicate the regressors add nothing over the fixed effects alone. Reported rather than
   suppressed.
2. **branches → Usage stays negative** across both panels (6-year p=0.001; 12-year p=0.071). It is the
   most persistent relationship in the study and remains unexplained. The F8 caution stands: this is
   as consistent with branches being *placed* where deposit growth is weak as with any causal reading.

---

## F11 — Digital panel built: PhonePe merged into the analysis panel (D14, D15)

`scripts/build_phonepe.py` → `raw/phonepe_derived/` · `scripts/merge_phonepe.py` → `output/panel_digital.csv`

- **165 rows = 33 states × FY2019–FY2023.** No nulls, no non-positive values, join lost nothing.
  Every banking column asserted **byte-identical** to `panel_analysis.csv`, so the earlier results
  stay reproducible from an untouched file.
- **FY2018 is lost.** PhonePe's first complete financial year is fy_end=2019.
- Denominators follow **A4 unchanged**: registered users (a stock) per adult; transactions and value
  (flows) per capita.

### The finding that matters: the variation problem does not exist on this side

Same `xtsum` decomposition as Step 4, same 33 states, overlapping years:

| Regressor | Within-state share of total variation |
|---|---|
| branches per lakh adults | **6.5%** |
| ATMs per lakh adults | **8.2%** |
| PhonePe users per adult | **67.1%** |
| PhonePe transactions per capita | **79.9%** |
| PhonePe value per capita | **78.8%** |

Step 4's thresholds were fixed in advance at FAIL < 10%, WEAK < 25%. The digital series clear them by
a factor of three to eight. **The reason the physical-infrastructure track could not test H1 (F4, F8)
does not apply here.**

### Levels, for the record

Unweighted state means. Digital rises ~25× in five years while branches per lakh adults are flat:

| fy_end | users/adult | txns/capita | value/capita (₹) | branches per lakh adults |
|---|---|---|---|---|
| 2019 | 0.135 | 1.2 | 1,857 | 21.39 |
| 2020 | 0.213 | 3.3 | 5,721 | 22.01 |
| 2021 | 0.305 | 6.5 | 12,457 | 21.73 |
| 2022 | 0.388 | 14.5 | 26,493 | 21.37 |
| 2023 | 0.464 | 28.7 | 46,618 | 21.54 |

This is D14's premise stated in numbers: over the study window, financial infrastructure in India
moved while *physical* financial infrastructure did not.

### Not yet done, deliberately

No regression has been run on this panel. How the digital series enters — regressor, second outcome,
or interaction — is an open specification decision (D15), and it will be logged **before** anything is
estimated, for the same reason F0 was written before Step 5.

---

## F12 — UPI added as a third regressor (D16)

`scripts/estimate_digital.py` → `output/table9_digital_results.csv`, `output/table10_digital_samplecheck.csv`

Two-way FE (state + year), SEs clustered by state. **33 states × FY2019–FY2023, N=165.**
UPI = PhonePe registered users per adult, level.

| | Access (1) | Usage (2) | AUG (3) |
|---|---|---|---|
| branches per lakh adults | +0.00545 (p=0.372) | **−0.00619 (p=0.020)** | **+0.01163 (p=0.045)** |
| ATMs per lakh adults | −0.00608 (p=0.067) | −0.00020 (p=0.868) | **−0.00587 (p=0.032)** |
| **UPI users per adult** | **+0.31578 (p<0.001)** | **+0.18330 (p<0.001)** | +0.13248 (p=0.082) |
| ln NSDP per capita | +0.00950 (p=0.701) | −0.00385 (p=0.568) | +0.01335 (p=0.602) |
| within-R² | 0.6091 | 0.8633 | 0.3050 |

θ = β − δ identity holds exactly for all three regressors. Joint test (branches = ATMs = UPI = 0)
rejects in every equation: Access χ²=13.13 p=0.0044, Usage χ²=71.17 p<0.0001, AUG χ²=8.86 p=0.0312.

### What is actually new here

- **UPI is the only regressor in this study that is large, positive and significant.** Moving a state
  from 0 to full adoption raises normalised Access by 0.32 and Usage by 0.18.
- **Within-R² goes from 0.069 → 0.609 (Access) and 0.042 → 0.863 (Usage).** The fixed effects plus
  branches and ATMs explained essentially nothing; adding one digital variable explains most of it.
- **UPI shows the H1 pattern** — β_access (0.316) > β_usage (0.183) > 0 — with the gap significant at
  10% (θ=0.132, p=0.082). **Physical infrastructure still does not**: branches fail (usage negative),
  ATMs fail (access negative).

### Three reasons this is not yet evidence that UPI causes inclusion

1. **The Access result is partly definitional.** Opening a PhonePe account requires a KYC-linked bank
   account. So "PhonePe users per adult" cannot rise unless bank accounts rise — and deposit accounts
   per adult is half the Access DV. **This is the same construction-rule violation (A7) that dropping
   PMJDY (D3) was meant to avoid**, reappearing through the digital side. The coefficient on Access
   should be read as an accounting relationship until that is dealt with.
2. **Reverse causality runs the wrong way and FE does not fix it.** The plausible sequence is
   unbanked → banked → adopts UPI. Both series also grow exponentially within state over the same
   five years, so a large positive coefficient is what two co-trending series produce whether or not
   one causes the other. Year FE removes the *common* national trend, not state-specific trend
   differences.
3. **UPI was not in the pre-committed H1 rule (D10).** That rule named branches and ATMs. The H1
   pattern on UPI is therefore an **exploratory** result, not a confirmation of the registered
   hypothesis. Reporting it as "H1 supported" would be exactly the retro-fitting F0 was written to
   prevent.

### Same-sample check (`table10`) — what moved, and why

The panel lost FY2018, so branches/ATMs coefficients here are not comparable to F5–F8 without this.
Re-running the identical 165 rows *without* UPI separates the two causes:

| | 198, no UPI | same 165, no UPI | 165 + UPI |
|---|---|---|---|
| branches → Usage | −0.01264 (p=0.001) | −0.01145 (p=0.000) | −0.00619 (p=0.020) |
| branches → AUG | +0.00367 (p=0.512) | +0.00783 (p=0.174) | **+0.01163 (p=0.045)** |
| ATMs → AUG | −0.00055 (p=0.731) | −0.00590 (p=0.074) | −0.00587 (p=0.032) |

- **ATMs → AUG is a sample effect**, not a UPI effect: it is already at p=0.074 before UPI is added
  and barely moves after.
- **branches → AUG is a UPI effect**: p=0.174 → 0.045 on the same rows. Controlling for digital
  adoption is what makes it significant.
- **branches → Usage stays negative in all three columns** (p≤0.020 throughout). This is now the most
  robust single relationship in the study, surviving a sample change and a new control. It still has
  no causal reading — branch placement is not random.

---

## F13 — Component decomposition: the entangled channel is the null one (D17)

`scripts/estimate_components.py` → `output/table11_components.csv`, `output/table12_components_d7.csv`

Same spec as F12 (two-way FE, SEs clustered by state, N=165). Coefficient on UPI shown.

### Panel A — each indicator as its own DV

| Dependent variable | UPI coef | se | p | within-R² | |
|---|---|---|---|---|---|
| deposit accounts / adult | +0.1926 | 0.1514 | 0.206 | 0.231 | ⚠️ entangled |
| **credit accounts / adult** | **+0.4390** | 0.1111 | **0.000** | 0.517 | ✅ clean |
| deposits ₹ / capita | +0.2218 | 0.0484 | 0.000 | 0.795 | ✅ clean |
| credit ₹ / capita | +0.1448 | 0.0198 | 0.000 | 0.639 | ✅ clean |

A3 identity asserted and holds: the Access coefficient (0.31578) is exactly the mean of its two
component coefficients, and likewise for Usage.

### The result is the opposite of the concern

D17 predicted two possibilities. Neither of the worrying ones occurred.

- **The definitionally entangled channel — UPI → deposit accounts — is NULL (p=0.206).**
- **The clean channel — UPI → credit accounts — is the large, highly significant one (+0.439, p=0.0001).**
- So F12's +0.316 on composite Access was **not** the accounting relationship. If anything the
  entangled component was *diluting* a real credit effect, not manufacturing one.

**D17's decision rule returns: "credit-only survives → F12's Access result is NOT merely definitional."**

### D7 robustness settles the deposit-account null

The null rests on a series with a known source defect, so D7's pre-committed check was run on it.
Dropping Delhi 2023 and Chandigarh 2023 — 2 cells of 165:

| Dependent | all 165 | drop D7 cells (163) |
|---|---|---|
| deposit accounts / adult | +0.1926 (p=0.206) | **+0.0177 (p=0.509)** |
| credit accounts / adult | +0.4390 (p=0.0001) | **+0.4446 (p=0.0003)** |
| Access (composite) | +0.3158 (p=0.0004) | +0.2312 (p=0.0005) |

- The deposit-account coefficient **collapses to essentially zero** and its standard error falls from
  0.151 to 0.027. What little was there was two defective cells inflating both the estimate and the
  noise. UPI adoption has **no detectable effect on deposit-account counts.**
- The credit-account coefficient **does not move** (0.439 → 0.445). Fully robust.
- The composite Access figure falls 27% (0.316 → 0.231), because it was averaging a real credit
  effect with a defect-driven deposit artefact. **The composite is the wrong number to report.**

### Panel B — credit-only H1 triple

Access_c = credit accounts per adult; Usage unchanged; AUG_c = Access_c − Usage. θ = β − δ asserted.

| | Access_c | Usage | AUG_c |
|---|---|---|---|
| branches per lakh adults | +0.00907 (p=0.085) | −0.00619 (p=0.020) | **+0.01526 (p=0.018)** |
| ATMs per lakh adults | −0.00070 (p=0.773) | −0.00020 (p=0.868) | −0.00049 (p=0.884) |
| **UPI users per adult** | **+0.43898 (p<0.001)** | **+0.18330 (p<0.001)** | **+0.25568 (p=0.020)** |
| within-R² | 0.5168 | 0.8633 | 0.1954 |

- **β_access (0.439) > β_usage (0.183) > 0 for UPI, and the gap is significant at 5%** (p=0.020).
  This is the **first time in the study that the access–usage gap is statistically distinguishable
  from zero.** On the composite Access it was p=0.082; removing the contaminated component roughly
  doubles the gap and halves the p-value.
- **Branches turn positive on access for the first time** (+0.0091, p=0.085) once the DV is credit
  accounts alone and digital adoption is controlled for. branches → AUG_c = +0.0153 (p=0.018).
- **ATMs are null on everything** here — the sample-driven ATM→AUG result from F12 (p=0.032) does not
  survive the switch to credit-only Access (p=0.884). It was a composite-DV artefact.
- Physical infrastructure still **fails** the pre-committed H1 rule: branches have usage negative,
  ATMs have access negative. Unchanged from F8.

### What this still does not establish

1. **Reverse causality is untouched.** FE removes fixed state differences and the common national
   trend; it does not remove state-specific time-varying confounders. Smartphone penetration, fintech
   entry and youth share all rose alongside both UPI adoption and credit accounts.
2. **A mechanism exists, which is not the same as evidence for it.** Digital payment history feeding
   credit underwriting (cash-flow-based lending, account aggregator) is a documented channel in India
   over exactly this window, and it predicts precisely this pattern — UPI moving credit accounts while
   leaving deposit accounts alone. That it matches is suggestive, not confirmatory.
3. **UPI was still not in the pre-committed H1 rule (D10).** This remains an exploratory finding. It
   is now a much cleaner one, but the registered hypothesis was about physical infrastructure and that
   verdict has not changed.
4. **PhonePe is one firm** (~45–50% of UPI), and its market share varies by state (D14).

---

## F14 — Leave-one-state-out: the headline coefficient is robust

`scripts/leave_one_out.py` → `output/table13_leave_one_out.csv`

Closes the open item carried in `DECISIONS.md` since data preparation ("check Maharashtra isn't
driving the result"). Credit accounts per adult is now the headline DV, so it was refit 33 times,
dropping each state in turn.

| | UPI → credit accounts / adult |
|---|---|
| full sample | **+0.4390 (p=0.0001)** |
| range across all 33 refits | +0.3561 to +0.4773 |
| worst p-value across all 33 | **0.0034** |
| sign flips | **0** |
| refits losing 5% significance | **0** |

- **Maharashtra is the most influential state**, as suspected — dropping it moves the coefficient
  from 0.439 to 0.356. But the result gets *more* significant without it (p=0.0000), so Maharashtra
  was inflating the point estimate, not creating the finding.
- Every other state moves it by less than 0.04.
- **Contrast with Track 1**, where dropping 2 of 198 cells flipped every ATM sign (F7). The digital
  result is of a different order of stability, which is what the variation diagnostic (F11) predicted.

The open item is closed: Maharashtra is not driving the result.

---

## Status

**Analysis complete.** Three tracks estimated, all diagnostics run, all pre-committed rules applied
as written. Final report: `final_findings.md`. Limitations: `LIMITATIONS.md`.

| | Track 1 | Track 2 | Track 3 |
|---|---|---|---|
| panel | 33 × FY2018–23 | 32 × FY2012–23 | 33 × FY2019–23 |
| N | 198 | 384 | 165 |
| regressors | branches, ATMs | branches | branches, ATMs, UPI |
| within-variation | 7.0% / 8.7% FAIL | 15.3% WEAK | 6.5% / 8.2% / **67.1%** |
| H1 verdict | not supported | not supported | not supported for physical; **pattern holds for UPI (exploratory)** |
| findings | F1–F8 | F10 | F11–F14 |
