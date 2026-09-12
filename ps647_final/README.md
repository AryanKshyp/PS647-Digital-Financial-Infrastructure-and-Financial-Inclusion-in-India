# PS 647 — Digital Financial Infrastructure and Financial Inclusion in India

**Main question:** to what extent has the expansion of India's digital financial infrastructure
improved financial inclusion, and has it reduced persistent gaps across rural–urban, gender and
income groups?

Two hypotheses were tested. **They share the data and nothing else** — separate scripts, separate
outputs, separate logs.

```
ps647_final/
├── data/                      ← SHARED. The 8 banking/population files + 09_diglit.csv
├── raw/                       ← SHARED. Original downloads, kept for provenance
├── DATA_GUIDE.md              ← SHARED. Plain-English guide to every data file
├── data_fetching.md           ← SHARED. Full technical provenance
│
├── h1_access_vs_usage/        ← H1
│   ├── scripts/  output/  report/
│   ├── EXECUTION_PLAN.md   FINDINGS.md (F0–F14)   DECISIONS.md (D1–D17)
│   ├── LIMITATIONS.md      final_findings.md  ← START HERE for H1
│
└── h5_literacy_and_income/    ← H5
    ├── scripts/  output/
    ├── EXECUTION_PLAN.md   FINDINGS.md (F15–F25)  DECISIONS.md (D18–D28)
    ├── LIMITATIONS.md      final_findings.md  ← START HERE for H5
```

---

## H1 — Access versus Usage · `h1_access_vs_usage/`

**Does infrastructure raise *access* to banking more than it raises *usage*?**

Three panels: 33 states × FY2018–23 (N=198, branches + ATMs); 32 states × FY2012–23 (N=384,
branches only); 33 states × FY2019–23 (N=165, + UPI).

- **Not supported for physical infrastructure.** Branches and ATMs do nothing — and with only
  7.0% / 8.7% within-state variation, the panel could not have detected it if they did.
- **The pattern holds for digital.** UPI adoption raises Access (+0.439) more than Usage (+0.183).
- **The effect runs through credit, not deposits.** UPI moves loan accounts; it does nothing to
  deposit-account counts.

→ `h1_access_vs_usage/final_findings.md`

## H5 — Digital Literacy and Income as Complements · `h5_literacy_and_income/`

**Does that infrastructure convert into inclusion at the same rate everywhere?** Moderators:
digital literacy (skills) and income (resources).

Runs on H1's `h1_access_vs_usage/output/panel_digital.csv` unchanged — same 165 rows, same estimator, same clustering.
Its baseline column reproduces H1's headline coefficients to five decimals as a build assertion.

- **No, and the difference is qualitative.** Where digital literacy is low, UPI adoption shows up
  as accounts opened; where it is high, as money moving (β₅ = +0.452, bootstrap p = 0.0008).
- **Income does not do this.** It raises both margins alike (β₆ = +0.013, p = 0.936) — and its
  apparent edge in the simple model vanishes when household consumption replaces state production
  as the income measure (p = 0.0002 → p = 0.998).
- Five placebo moderators — three from the *same survey, same households, same year* as the
  treatment — all return nothing.

→ `h5_literacy_and_income/final_findings.md`

---

## How the two fit together

They are **one equation**, not two studies. In
`h5_literacy_and_income/output/table17_h5_stacked.csv`:

| | coefficient | asks |
|---|---|---|
| **H1** | β₂ — UPI × Intensive | does infrastructure move access more than usage? |
| **H5** | β₅ — UPI × DigLit × Intensive | does capability condition that difference? |

Joint reading: digitalisation expanded formal access broadly, but whether that access became
functional depended on a skill endowment that was already unequally distributed.

---

## Reproducing

Shared data is read-only. Each hypothesis writes only into its own `output/`.

```bash
pip install pandas numpy scipy linearmodels statsmodels matplotlib

# H1 — from data/ to results
cd h1_access_vs_usage
python scripts/build_panel.py && python scripts/build_variables.py
python scripts/within_variation.py      # the Step 4 gate (exits non-zero by design when it fails)
python scripts/estimate.py && python scripts/hausman.py && python scripts/robustness.py
python scripts/merge_phonepe.py         # -> output/panel_digital.csv
python scripts/estimate_digital.py && python scripts/estimate_components.py
python scripts/leave_one_out.py

# H5 — needs H1's output/panel_digital.csv to exist first
cd ../h5_literacy_and_income
python scripts/build_moderators.py && python scripts/build_h5_panel.py
python scripts/h5_descriptives.py       # descriptives, before any estimate
python scripts/h5_gates.py              # the go/no-go
python scripts/estimate_h5.py
python scripts/h5_placebo.py            # outranks the main table — see EXECUTION_PLAN.md §7
python scripts/estimate_h5_stacked.py   # the headline
python scripts/estimate_h5_threshold.py && python scripts/h5_robustness.py
python scripts/h5_supplementary.py      # -> table20, the pairwise decomposition of b5
python scripts/h5_income.py             # -> table22, the resources channel
python scripts/h5_spec_tests.py         # -> table23, FE test + pre-UPI moderator + Hausman
python scripts/plot_h5.py
python scripts/plot_report_figures.py   # -> report_fig5_1..6, the chapter figures
python scripts/write_report_chapter.py  # -> ../Digital_..._with_Chapter5.docx
```

**Path convention.** Every script sets `ROOT_DIR` to its own hypothesis folder and `SHARED` to this
directory. `data/` and `raw/` are read from `SHARED`; results are written to `ROOT_DIR/output`.
H5 reads H1's panel via an explicit `H1_OUT` and never writes to it.

---

## Reading the logs

Both hypotheses follow the same discipline, and it is the main reason to trust either:

- **`DECISIONS.md`** — every mid-execution choice, D-numbered, with the reasoning recorded *before*
  the consequence was known. H5 continues H1's numbering and revises none of it.
- **`FINDINGS.md`** — append-only, F-numbered, each result written down *before* it was
  interpreted. Failed diagnostics are findings and are logged as such.
- **`LIMITATIONS.md`** — ordered by how much damage each does to the conclusions, not by how easy
  they are to defend.

Decision rules were pre-committed before coefficients were seen (H1: D10; H5: `EXECUTION_PLAN.md`
§7) and were not revised afterwards. Where a pre-committed rule went against the result — H1's D10
rule, H5's R9 robustness check — the rule is reported as binding.
