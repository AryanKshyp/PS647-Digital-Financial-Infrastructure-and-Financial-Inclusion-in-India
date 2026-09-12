# Decision Log — H5 (Conversion Capacity)

Continues the numbering of `../h1_access_vs_usage/DECISIONS.md` (D1–D17), which is NOT revised by
anything here. Plan: `EXECUTION_PLAN.md`. Findings: `FINDINGS.md`.

Findings: F15 onward. Nothing in D1–D17 is revised; H5 adds to the study, it does not re-open it.

**D18 — H5 runs on `../h1_access_vs_usage/output/panel_digital.csv` unchanged. State × FY2019–FY2023, N=165.**
The original `H5_analysis_plan.md` specified a district × quarter spine, a PCA-based DFI index and
UPI transactions as the dependent variable. All three are incompatible with what this project
built: D10 forbids composite indices, D16 makes UPI the *regressor*, and the banking outcomes exist
only at state level. H5 therefore reuses the H1 panel exactly — same DVs, same A2 normalisation,
same estimator, same clustering — and adds only moderators and interactions.
**Consequence:** H5's baseline column must reproduce F12 to five decimals. It does (F15). That is
a build assertion, not a result.

**D19 — District track (Track B) dropped. Reason recorded so it is not re-attempted blindly.**
PhonePe Pulse does carry district-level data in the existing clone (`raw/phonepe_pulse/map/`:
783 districts × quarter, 2019Q1–2023Q4, verified). The blocker is the *moderator*: NFHS-5 district
fact sheets carry 104 indicators and internet use is **not among them** — it appears only in the
131-indicator state fact sheets. There is no district-level digital-literacy measure available, so
a district design would have nothing to interact. Checked and rejected, not overlooked.

**D20 — Primary digital-literacy moderator: NFHS-5 (2019-21) "women who have ever used the
internet", state level. NSS 75th round (2017-18) kept as the pre-window robustness measure.**
The execution plan named NSS 75th as primary because it strictly pre-dates the outcome window.
It is demoted for one reason: **the published NSS 75th state table covers 22 states only** — every
North-Eastern state and small UT is absent. Using it as primary would drop 11 of 33 states and take
N from 165 to 110, losing exactly the units that sit at the top of the digital-literacy
distribution (Sikkim, Mizoram, Goa). NFHS-5 covers all 33.
- The two measures correlate **r = 0.867** (computer ability) and **r = 0.903** (internet ability)
  across the 22 states where both exist — different surveys, different years, different
  respondents. They are measuring the same thing.
- The NSS 75th version is reported alongside every headline result, at n=22, and the lag argument
  is reported with it.
- Source mirror for NFHS-5 was **verified against 8 independently published figures before use**
  (`scripts/build_moderators.py::assert_nfhs_spotchecks`); all matched exactly.

**D21 — Both moderators z-scored; the income moderator is made TIME-INVARIANT.**
Income enters twice and the two roles must not be confused:
- as a **main-effect control**, time-varying `ln_nsdp_pc`, exactly as in F12 — unchanged;
- as a **moderator**, the FY2019–FY2023 state mean, deliberately time-invariant.
The skills moderator is a single survey wave and cannot vary over time. Letting income vary while
skills could not would hand H5b five times the identifying variation, and the skills-vs-resources
horse race would be decided by that asymmetry rather than by the data. Both are therefore one
number per state, z-scored, so β₃ and β₄ are both read as "per 1 SD of the moderator".

**D22 — The stacked sharp test is reported under TWO fixed-effect schemes; (B) is the headline.**
Both were written into `scripts/estimate_h5_stacked.py` before it was run, with (B) labelled
a priori as "strictly more demanding".
- (A) state + year + outcome FE — the execution plan's literal specification.
- (B) state × outcome + year × outcome FE — every outcome carries its own state level and its own
  national time path.
(B) is taken as the headline. The argument is **post hoc but checkable**: under (A), β₅ (+1.055)
and β₆ (+1.048) come back nearly identical and neither is significant, which is the signature of a
fixed-effect structure that cannot separate the two moderators — (A) forces one state intercept
across three outcomes whose state structures differ. Scheme (A) is reported in full next to (B) so
the reader can judge rather than take this on trust.

**D23 — R9 fails, and is reported as a failure rather than explained away.**
Adding deposit accounts per adult to the extensive side of the stacked test drives β₅ from +0.452
(p=0.0008) to −0.070 (p=0.691). The D17 entanglement is the likely reason — deposit accounts move
mechanically with PhonePe registration, and F13 already found the skills interaction on that
indicator runs the *opposite* way (+0.124, p=0.039) to the one on credit accounts (−0.061) — but
D17's credit-only rule was fixed before H5 existed and this does not retro-justify it.
**The honest statement: β₅ holds when the extensive margin is measured by credit accounts and
does not hold when deposit accounts are averaged in.** That sentence travels with the result.

**D24 — Every H5 claim is a heterogeneity claim, not a causal one.**
H5 interacts a main effect that `../h1_access_vs_usage/LIMITATIONS.md` §1–2 already establishes as a non-causal
within-state correlation between co-trending series, added post hoc. The interaction inherits that.
β₅ is partially protected — it is a difference *between outcomes measured on the same state in the
same year*, so any confounder acting equally on both margins differences out — but it is not
immune to a confounder that moves the two margins differently and correlates with digital literacy.
Fixed now: no H5 result is written up as "digital literacy causes infrastructure to convert
better". The permitted form is "the UPI–inclusion association differs by margin, and that
difference varies with digital literacy".

**D25 — MPCE (HCES 2022-23) added as the second resources measure, and it is the better construct.**
H5b had one measure where H5a had five. That asymmetry is indefensible in a design whose whole
point is a horse race between the two channels.

*Why MPCE and not simply "another income proxy".* Per-capita NSDP is a **production** measure:
output books to the state where the firm is registered. That is the same attribution artefact
`../h1_access_vs_usage/LIMITATIONS.md` §4 already documents for bank deposits, which are recorded
at branch location and inflate Maharashtra and Delhi. MPCE is household **consumption**, collected
from households. For a moderator meant to stand for household *resources*, MPCE is the right
construct and NSDP is the available one. They correlate 0.844 — close, not interchangeable.

*Fixed before the result was seen:* if the two disagree, **MPCE is the more credible** for H5b, and
NSDP's result is to be reported as measure-specific rather than as the finding. F24 is the case
where that rule bites, and it is applied as written: H5b's plain-model support is reported as
**not robust to the measure**.

*Sector combination.* MPCE is published rural and urban separately; the two are combined at each
state's derived urban share (the same quantity used for the urbanisation placebo). J&K and Ladakh
are population-weighted per D2.

**D26 — Scheme (B) is retained for the stacked test, now on a test rather than an argument.**
D22 recorded that preferring (B) over the plan's literal scheme (A) was post hoc. (A) is nested in
(B), so the restriction is testable, and F25 tests it: **F(72, 375) = 89.21, p < 10⁻¹⁵**. Scheme
(A) is misspecified. This converts the choice from a judgement call into a data requirement, in the
same way H1's Hausman test rules out random effects rather than the analyst ruling them out.
The classical-F caveat (no cluster-robust Wald available at 33 clusters and 72 restrictions) travels
with it: the test licenses the fixed-effect structure, not the standard errors.

**D27 — The pre-specified headline is NOT swapped for the larger pairwise estimate.**
F22 shows β₅ is carried by the credit-accounts-vs-deposits-₹ pair (+0.749) and that the pooled
three-outcome figure (+0.452) is a dilution. The temptation is to promote +0.749 to the headline.

**It is not promoted.** The pooled specification is what `EXECUTION_PLAN.md` §6.3 specified before
any data existed; it is significant as specified; and replacing it with a larger number found by
decomposition afterwards is exactly the retro-fitting that H1's §3.6.2 exists to prevent. The
pooled figure stays the headline. The decomposition is reported immediately beneath it as what the
headline *means*, and the interpretive claim is narrowed accordingly — to deposit balances, not to
the intensive margin in general.

**D28 — NFHS-4 (2015-16) mobile-phone ownership added as the strictly pre-window moderator.**
The plan's R4 ("break reverse causality by lagging the moderator") was satisfied only by the NSS
75th measure, which covers 22 states. NFHS-4 carries women's own mobile-phone ownership for all 33
panel states, measured 3.5 years before the window and before UPI's April 2016 launch.

It is a **weaker construct** than internet use — owning a handset is material access, not skill,
and the contemporaneous mobile measure is itself null in the main tables (F17). It is used only for
the reverse-causality check, never as a primary moderator, and its two same-round placebos
(schooling 2015-16, own bank account 2015-16) are reported beside it so "any 2015-16 development
measure would do" can be ruled out. F25 reports the outcome.

*Also added, and not in the original plan:* **women's own bank account, NFHS-4 2015-16**, as a
placebo. It is the sharpest available confound because it is about the *outcome* rather than about
development — if states that were already more financially included convert UPI differently, that
is not a skill effect. It is null in both the skills slot (β₅ = +0.326, p = .440) and the resources
slot (β₆ = +0.247, p = .543).
