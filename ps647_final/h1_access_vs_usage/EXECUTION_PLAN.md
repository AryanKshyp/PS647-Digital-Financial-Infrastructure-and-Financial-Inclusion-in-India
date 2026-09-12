# Execution Plan — PS 647 State Panel

Follows `project_plan.pdf` exactly, as modified by the ten decisions in `DECISIONS.md`.
Nothing added beyond that.

**Rule: `data/` is read-only.** Every script reads from `data/` and writes to `output/`.

Status: **COMPLETE.** Steps 1–9 on the 6-year panel, plus the D12/D13 extended 12-year panel.
Results in `FINDINGS.md` (F0–F10), tables in `output/`.

---

## Assumptions (logged as F0 in `FINDINGS.md`)

| # | Assumption | Basis |
|---|---|---|
| A1 | The "Access 35%, Usage 45%" weights are **ignored** — they weight RBI's composite index, which we do not build. Applying them would make AUG = 0.35A − 0.45U, breaking the plan's own `AUG = Access − Usage`. | user confirmed |
| A2 | 0–1 normalisation is **min–max pooled over all 198 state-years**. Preserves growth over time, which the FE model estimates from. | user confirmed |
| A3 | Inside Access, and inside Usage, the two indicators get **equal weight**. The PDF gives no within-dimension weights. | follows from A1 |
| A4 | "per adult" = population 18+; "per capita" = **total** population. The PDF uses both terms deliberately. | PDF wording |
| A5 | N = **198** (33 states × 6 years), not the PDF's ≈210 (≈30 × 7). | D8 |
| A6 | Of D7's four suspect cells, only **Delhi 2023 and Chandigarh 2023** are inside FY2018–FY2023. Delhi 2024 and Haryana 2024 fall outside. | D7 + D8 |
| A7 | Construction rule satisfied: infrastructure on the IV side, accounts and balances on the DV side, no overlap. Dropping PMJDY (D3) is what removed it. | PDF construction rule |

---

## DONE — Step 1. Build merged panel
`scripts/build_panel.py` → `output/panel_raw.csv`
Word-boundary state matching; D2 merges; D1 drops; filter 2018–2023; assert 33 × 6 = 198, no nulls.

## DONE — Step 2. Construct variables
`scripts/build_variables.py` → `output/panel_analysis.csv`
IVs in real units (D10, no index). Four DV indicators min–max normalised pooled (A2);
Access and Usage each the mean of their two (A3); `AUG = Access − Usage`; `ln_nsdp_pc`.

## DONE — Step 3. Descriptives
`scripts/descriptives.py` → `output/table1_descriptives.csv`

---

## DONE — Step 4. Diagnostic (a): within-state variation — **RUN FIRST**
→ `output/table2_within_variation.csv`
PDF: *"Run this first; if DFI barely moves within states, fixed effects have nothing to estimate from."*
Per D10 this applies to **branches and ATMs separately**. Decompose variance between vs within state.
**This is a gate** — if within-state variation is negligible, stop and report that rather than
interpret coefficients from variation that does not exist.

## DONE — Step 5. Estimate the three equations
→ `output/table3_main_results.csv`. Two-way FE (state + year), SEs **clustered by state**.

```
(1) Access_it = a_i + L_t + b1*branches + b2*ATMs + g*lnNSDP + e
(2) Usage_it  = a_i + L_t + d1*branches + d2*ATMs + g*lnNSDP + e
(3) AUG_it    = a_i + L_t + t1*branches + t2*ATMs + g*lnNSDP + e
```
Verify the identity **t = b − d**. Equation (3) is not a third finding — it supplies the standard
error on the difference, which is the formal test of H1. Per D10 also report a **joint F-test** on
(branches, ATMs); this replaces what a composite index would have said, and is not an addition.

## DONE — Step 6. Diagnostic (b): Hausman FE vs RE
→ `output/table4_hausman.csv`

## DONE — Step 7. Robustness per D7
→ `output/table5_robustness.csv`. Re-run all three dropping **Delhi 2023 and Chandigarh 2023** (A6).

## DONE — Step 8. Test H1 against the pre-committed rule

| Outcome | Reading |
|---|---|
| b_access > b_usage > 0 | H1 supported — expansion formal, not functional |
| b_access ~ b_usage | H1 rejected — genuine deepening. Still a finding |
| both ~ 0 | check Step 4 before concluding anything |
| t on AUG > 0, significant | the access–usage gap widens as infrastructure expands |

**D10's pre-committed rule, unchanged:** H1 fully supported only if b_access > b_usage > 0 for
**branches AND ATMs**. If only one, report **partial support**, naming which. Not to be revised
after seeing coefficients.

## DONE — Step 9. Assemble limitations
PDF's four (state-level not person-level; deposits recorded by branch location, inflating Maharashtra
and Delhi; no connectivity component — reframed as physical banking infrastructure per D3; reverse
causality only mitigated by FE), plus ours: interpolated adult population (D6), the
Delhi/Haryana/Chandigarh defect (D7), the FY2024 loss (D8).

---

## Logging discipline
- `DECISIONS.md` — new mid-execution choices get the next D-number.
- `FINDINGS.md` — append-only, F-numbered, written **as each result appears, before interpreting it**.
  A failed diagnostic is a finding and gets logged.
- `output/` — fixed filenames, so the report cites files not scrollback.

## Verification
1. Step 1 assertions pass: 33 × 6 = 198, no nulls.
2. D9 spot-check survives the merge: Maharashtra at `fy_end=2018` shows **12,545 branches**,
   **25,651 ATMs**, income **₹172,663**.
3. Step 5 identity holds: t = b − d for both regressors.
4. Scripts re-runnable end to end from `data/` with no manual steps.
