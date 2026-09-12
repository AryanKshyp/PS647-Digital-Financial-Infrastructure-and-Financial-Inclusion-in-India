> **Superseded.** The chapter has since been written directly into the document; see
> `../../Digital_Financial_Infrastructure_Report_with_Chapter5.docx`. This file is kept as
> the record of what was inserted and where.

# Report inserts for Hypothesis 3 (Chapter 5)

Text to paste into `Digital_Financial_Infrastructure_Report.docx`. The report's §2.8 says the data
chapter must remain "the single place the panel is described", so the three new series belong in
Chapter 2, not Chapter 4.

Numbering note: this hypothesis is **H5** in the group's hypothesis list and **Hypothesis 3,
Chapter 5** in the report. Pick one for the final document; the decision and findings logs use the
H5 label and the D/F numbering continues H1's.

---

## 1. Add to Table 2.2 (Source of each series)

| Series | Publication | Table / report | Role |
|---|---|---|---|
| Digital literacy | National Family Health Survey 5 (2019-21), IIPS | State fact sheets, indicators 18 and 19: women and men who have ever used the internet | Moderator (H5a) |
| ICT skills, pre-window | NSS 75th round (July 2017 – June 2018), Schedule 25.2, MoSPI | Tables 13 and 14, persons aged 5+ able to operate a computer / use the internet; 22 major states only | Moderator, robustness |
| Mobile-phone ownership, pre-window | National Family Health Survey 4 (2015-16), IIPS | State fact sheets, indicator 123, women owning a mobile phone they themselves use | Moderator, reverse-causality check |
| Household consumption | Household Consumption Expenditure Survey 2022-23, MoSPI | Fact Sheet, Statement 8, average MPCE by State/UT, rural and urban | Moderator (H5b), robustness |
| General education and inclusion baselines | NFHS-5 and NFHS-4 | Indicators 1, 16, 17 (schooling) and 122 (women's own bank account) | Placebo controls |
| General literacy | Census of India 2011 | State literacy rate | Placebo control |

Also extend §2.8 ("What the hypothesis chapters draw from this panel"):

> Chapter 5 uses the nine series above plus six state-level cross-sections carrying no time
> dimension: digital literacy and general education from NFHS-5, their 2015-16 counterparts from
> NFHS-4, ICT skills from the NSS 75th round, household consumption from HCES 2022-23, and Census
> 2011 literacy. None enters as a time-varying regressor; each is one number per state, interacted
> with the digital-infrastructure measure already in Table 2.2.

---

## 2. Add to §2.7 (Known limitations of the data)

> **Coverage of the pre-window ICT measure.** The published NSS 75th round state tables cover 22
> major states only; every north-eastern state and small union territory is absent. Using it as the
> primary moderator would have dropped 11 of 33 states and removed most of the upper tail of the
> digital-literacy distribution (Sikkim, Mizoram, Goa). It is therefore reported as a robustness
> measure at n = 22, and the primary moderator is taken from NFHS-5, which covers all 33. Where
> both exist they correlate 0.87 (computer ability) and 0.90 (internet ability), so the substitution
> is between two measurements of the same quantity rather than between two quantities.
>
> **The NFHS-5 values were verified, not assumed.** They were taken from a compiled mirror whose
> author flags it as not extensively cross-checked, and were tested against eight independently
> published fact-sheet figures before use; all eight matched exactly. The check runs on every build
> and aborts on any mismatch.
>
> **Urbanisation is derived, not published.** No verifiable machine-readable Census 2011 state
> urbanisation table was obtained, so the urban share used as a placebo control is derived from
> NFHS-5's own urban/rural/total decomposition, u = (total − rural)/(urban − rural). It tracks
> Census 2011 closely where both are known (Delhi 98.2 against 97.5, Kerala 48.6 against 47.7,
> Maharashtra 46.7 against 45.2) but is a survey-sample quantity and is labelled as such. It is
> never used as a headline variable.
>
> **Census 2011 literacy conflates Andhra Pradesh and Telangana.** Telangana did not exist in 2011,
> so both states carry the undivided Andhra Pradesh figure, flagged in the data file. It affects one
> of several placebo controls and none of the treatment measures.
>
> **Two income measures, and they are not interchangeable.** Per-capita NSDP is a production
> measure: output books to the state where a firm is registered, the same attribution issue already
> recorded in §2.7 for deposits held at branch location. MPCE from HCES 2022-23 is household
> consumption collected from households. The two correlate 0.844, and Chapter 4 shows the choice
> between them changes the result, so both are reported.
>
> **Sector combination for MPCE.** MPCE is published separately for rural and urban areas. The two
> are combined at each state's derived urban share; Jammu & Kashmir and Ladakh are combined by
> Census 2011 population weights under the rule in §2.4.

---

## 3. Chapter 5 skeleton, filled

| Report section | Source in this folder |
|---|---|
| 5.1 Hypothesis and pre-commitment | `EXECUTION_PLAN.md` §2 and §7; decision rule logged as the H5 gate table, D18–D28 |
| 5.2 Variables and specification | `final_findings.md` "What was built" + the equation in Result 2 |
| 5.3 Descriptives and diagnostics | `final_findings.md` "Descriptives and diagnostics"; `output/table21`, `table14` |
| 5.4 Results and robustness | `final_findings.md` Results 1–5; `output/table15`–`table23` |
| 5.5 Verdict, implications and limitations | `final_findings.md` "What this means" and "What this cannot claim"; `LIMITATIONS.md` |

**For Appendix A (Decision Log):** D18–D28 in `DECISIONS.md`, continuing H1's numbering. The two
that a reader will look for are **D25** (MPCE is the more credible resources measure, fixed before
the result was seen) and **D27** (the pre-specified headline is not swapped for the larger estimate
found by decomposition).

---

## 4. Two things Chapter 3 may want to borrow

Neither requires re-running H1, and both are optional.

**Wild cluster bootstrap.** §3.2.3 cites Cameron and Miller on 33 clusters sitting at the lower end
of the reliable range, then reports cluster-robust p-values throughout. The marginal results are
exactly where this matters: branches on AUG at p = 0.084, and the UPI access–usage gap at p = 0.020.
`scripts/h5_lib.py::wild_cluster_bootstrap` is vectorised and takes under a second per coefficient.

**The compression problem has a fix.** §3.7 limitation 4 states that Usage is severely right-skewed
after pooled min–max normalisation, so β_access and β_usage "were never on fully equivalent
scales — a direct threat to the comparison itself". Standardising each outcome within itself before
comparing removes that. β₂ in `output/table17_h5_stacked.csv` is H1's access-versus-usage
comparison estimated that way: **−0.906, bootstrap p = 0.081**, sign and conclusion unchanged from
Chapter 3. That is worth a sentence in §3.7 — the limitation is real but does not overturn the
result.
