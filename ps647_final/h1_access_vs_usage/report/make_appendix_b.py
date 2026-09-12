#!/usr/bin/env python3
"""
Generate appendices/b_full_tables.tex from the analysis output CSVs.

Appendix B reports the regression results at the precision written by the
estimation scripts, so that the rounded figures in Chapter 3 are auditable.
It is generated rather than transcribed so the two cannot drift apart.

Run from the report/ directory after any re-estimation:
    python3 make_appendix_b.py
"""
import pathlib
import pandas as pd

OUT = pathlib.Path(__file__).resolve().parent.parent / "output"
DEST = pathlib.Path(__file__).resolve().parent / "appendices" / "b_full_tables.tex"

NICE = {
    "branches_per_lakh_adults": "Branches / lakh adults",
    "atms_per_lakh_adults": "ATMs / lakh adults",
    "ln_nsdp_pc": r"$\ln$(NSDP p.c.)",
}
SPEC = {
    "main": "Six-year panel, main",
    "d7_trimmed": "Six-year panel, D7-trimmed",
    "long_12yr": "Twelve-year panel, main",
    "long_12yr_d7trim": "Twelve-year panel, D7-trimmed",
}


def esc(s):
    return str(s).replace("_", r"\_").replace("%", r"\%").replace("&", r"\&")


def reg_block(df, caption, label):
    head = (r"Equation & Regressor & Coefficient & Std. error & $t$ & $p$ & "
            r"Within-$R^2$ \\")
    lines = [r"{\footnotesize",
             r"\begin{longtable}{@{}llrrrrr@{}}",
             rf"\caption{{{caption}}}", rf"\label{{{label}}}\\",
             r"\toprule", head, r"\midrule", r"\endfirsthead",
             r"\toprule", head, r"\midrule", r"\endhead",
             r"\bottomrule", r"\endlastfoot"]
    for spec, g in df.groupby("spec", sort=False):
        lines.append(rf"\multicolumn{{7}}{{@{{}}l}}{{\textbf{{{SPEC.get(spec, esc(spec))}}}}} \\[2pt]")
        for _, r in g.iterrows():
            lines.append(
                f"{esc(r['equation'])} & {NICE.get(r['regressor'], esc(r['regressor']))} & "
                f"{r['coef']:.6f} & {r['se']:.6f} & {r['t']:.3f} & {r['p']:.4f} & "
                f"{r['r2_within']:.4f} \\\\")
        lines.append(r"\addlinespace")
    lines += [r"\end{longtable}", r"}"]
    return "\n".join(lines)


parts = [
    r"\chapter{Full Regression Output}", r"\label{app:tables}", "",
    "The tables in Chapter~\\ref{ch:h1} round coefficients to five decimal places for readability.",
    "This appendix reproduces the same estimates at the precision written by the estimation",
    "scripts, so that the rounded figures in the text are auditable. Every table here is generated",
    "directly from the corresponding file in \\texttt{output/}; the mapping is given in",
    "Appendix~\\ref{app:repro}. All specifications include state and year fixed effects, with",
    "standard errors clustered by state.", "",
    r"\section{Six-year panel, \panelA{}}", r"\label{sec:app-6yr}", "",
    "Thirty-three states, $N = 198$ in the main specification and $N = 196$ after excluding",
    "Delhi 2023 and Chandigarh 2023. Both branches and ATMs are included as regressors.", "",
    reg_block(pd.read_csv(OUT / "table5_robustness.csv"),
              "Six-year panel: main and D7-trimmed estimates, full precision", "tab:app-6yr"),
    "",
    r"\section{Twelve-year panel, \panelB{}}", r"\label{sec:app-12yr}", "",
    "Thirty-two states, $N = 384$ in the main specification and $N = 382$ after trimming. Branches",
    "only; ATMs cannot be extended before 2018. Andhra Pradesh and Telangana are merged in all",
    "years (D13). Note the negative within-$R^2$ values discussed in Section~\\ref{sec:h1-long}.",
    "",
    reg_block(pd.read_csv(OUT / "table8_long_robustness.csv"),
              "Twelve-year panel: main and D7-trimmed estimates, full precision", "tab:app-12yr"),
    "",
    r"\section{Hausman tests}", r"\label{sec:app-hausman}", "",
    r"\begin{table}[H]", r"\centering",
    r"\caption{Hausman test statistics, both panels}", r"\label{tab:app-hausman}",
    r"\small", r"\begin{tabular}{@{}llrrrl@{}}", r"\toprule",
    r"Panel & Equation & $\chi^2$ & df & $p$ & Favours \\", r"\midrule",
]
for lbl, fn in (("Six-year", "table4_hausman.csv"), ("Twelve-year", "table7_long_hausman.csv")):
    h = pd.read_csv(OUT / fn)
    for i, r in h.iterrows():
        pv = f"{r['p_value']:.6f}" if r["p_value"] > 1e-6 else r"$<10^{-6}$"
        parts.append(f"{lbl if i == 0 else ''} & {esc(r['equation'])} & {r['chi2']:.3f} & "
                     f"{int(r['df'])} & {pv} & {esc(r['favours'])} \\\\")
    parts.append(r"\addlinespace")
parts += [r"\bottomrule", r"\end{tabular}", r"\end{table}", "",
          r"\section{Variance decomposition, full precision}", r"\label{sec:app-within}", "",
          r"\begin{table}[H]", r"\centering",
          r"\caption{Between- and within-state variance decomposition, six-year panel}",
          r"\label{tab:app-within}", r"\footnotesize",
          r"\begin{tabular}{@{}lrrrrrl@{}}", r"\toprule",
          r"Variable & Overall & Between & Within & Within & Median & Verdict \\",
          r" & SD & SD & SD & share & swing (\%) & \\", r"\midrule"]
w = pd.read_csv(OUT / "table2_within_variation.csv")
for _, r in w.iterrows():
    v = str(r["verdict"]) if pd.notna(r["verdict"]) else "---"
    parts.append(f"{esc(r['variable'].strip())} & {r['overall_sd']:.4f} & {r['between_sd']:.4f} & "
                 f"{r['within_sd']:.4f} & {r['within_share']*100:.2f}\\% & "
                 f"{r['median_within_state_swing_pct']:.2f} & {v} \\\\")
parts += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]

DEST.write_text("\n".join(parts) + "\n")
print(f"wrote {DEST}")
