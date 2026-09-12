# PS 647 Report — LaTeX source

## Uploading to Overleaf

1. Zip **this whole folder** (`report/`), keeping the subdirectories.
2. Overleaf → New Project → **Upload Project** → select the zip.
3. Menu → **Main document**: `main.tex` · **Compiler**: **pdfLaTeX**.

Nothing else needs configuring. The project uses `natbib` + BibTeX (not biblatex/biber),
so Overleaf's default bibliography handling works unchanged.

Locally: `latexmk -pdf main.tex` (and `latexmk -c` to clean).

## Layout

| Path | Contents |
|---|---|
| `main.tex` | Preamble, title page, `\input{}` list. **Edit the title-page block for author names.** |
| `chapters/00_abstract.tex` | Abstract |
| `chapters/01_introduction.tex` | Ch 1 — Introduction, background, literature, the three hypotheses |
| `chapters/02_data.tex` | Ch 2 — Shared data: nine sources, three panels |
| `chapters/03_hypothesis1.tex` | Ch 3 — Hypothesis 1 across all three tracks, complete |
| `chapters/04_hypothesis2.tex` | Ch 4 — **stub** |
| `chapters/05_hypothesis3.tex` | Ch 5 — **stub** |
| `chapters/06_conclusion.tex` | Ch 6 — Discussion and conclusion |
| `chapters/99_ai_acknowledgement.tex` | Acknowledgement of AI assistance |
| `appendices/a_decision_log.tex` | Appendix A — decision log D1–D17 |
| `appendices/b_full_tables.tex` | **Not included.** Full-precision regression output; uncomment its `\input` in `main.tex` to restore |
| `images/` | Six figures |
| `references.bib` | Bibliography (29 entries) |

## Figures

| File | Shows |
|---|---|
| `fig1_variables_over_time.png` | Why the physical tracks failed — flat regressors, climbing outcomes |
| `fig2_coefficients.png` | All physical coefficients with CIs, both tracks |
| `fig3_digital.png` | The digital result — entangled channel null, clean channel significant |
| `fig4_digital_vs_physical.png` | The premise: digital rose ~25×, physical flat *(generated)* |
| `fig5_within_variation.png` | Within-state variation against the pre-set thresholds *(generated)* |
| `fig6_leave_one_out.png` | Leave-one-state-out robustness, 33 refits *(generated)* |

Figures 1–3 come from `../output/`. Figures 4–6 are built by `make_figures.py` — re-run it
(`python3 make_figures.py`) after any re-estimation rather than editing the images.

## Filling in the stubs

Chapters 4 and 5 are skeletons with every heading and `\label{}` in place, so cross-references
resolve while they are empty. Yellow notes say what belongs in each section. The same applies to
the Hypothesis 2 and 3 statement boxes in §1.4 and the per-hypothesis summaries in §6.1.

## Before submitting

Hide every "to be completed" marker by changing one line in `main.tex`:
`\usepackage[...]{todonotes}` → `\usepackage[disable]{todonotes}`.

## Two things that will break the build

1. **Never paste the ₹ symbol.** U+20B9 is absent from the T1 font encoding and pdfLaTeX fails on
   it. Use the `\rs` macro.
2. **Do not add `siunitx`.** Tables use plain `booktabs` columns.
