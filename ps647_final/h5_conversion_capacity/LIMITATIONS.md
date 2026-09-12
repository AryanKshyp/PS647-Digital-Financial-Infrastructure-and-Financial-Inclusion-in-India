# Limitations — H5 (Conversion Capacity)

H5 runs on the H1 panel and inherits **every** limitation in
`../h1_access_vs_usage/LIMITATIONS.md` without exception. This file lists only what H5 adds.

digital track without exception. What follows is what H5 adds. Ordered by damage done.

## H5.1 — The interaction inherits a non-causal main effect

H5 moderates the UPI coefficient. §1 above establishes that coefficient as a within-state
correlation between two co-trending series, and §2 that it was added after the pre-registered
hypothesis failed. **Nothing in H5 repairs either.** Every H5 result is a statement about how an
*association* varies, not about how an effect varies.

**One coefficient is partly insulated, and only partly.** β₅ — the triple interaction that carries
the chapter — is a difference between two outcomes measured on the *same state in the same year*.
Any confounder acting equally on both margins differences out: a state income shock, smartphone
diffusion, a fintech entering the market. What survives as a threat is narrower but real: a
confounder that moves the extensive and intensive margins **differently** and is correlated with
digital literacy. The placebo battery (F18) is evidence against that and is not proof of its
absence.

## H5.2 — β₅ depends on how the extensive margin is measured

Reported in the chapter rather than buried, because it is the sharpest internal inconsistency in
the H5 results.

- Extensive margin = credit accounts per adult → β₅ = **+0.452, p = 0.0008**
- Extensive margin = credit accounts *and* deposit accounts → β₅ = **−0.070, p = 0.691**

The two extensive indicators genuinely disagree: the skills interaction is **+0.124** on deposit
accounts and **−0.061** on credit accounts. D17 established before H5 existed that deposit accounts
are definitionally entangled with PhonePe registration, which is why Access is reported credit-only
throughout this project — so the preferred coding was not chosen to produce this result. That is a
reason to prefer credit accounts, not a demonstration that the deposit-account reading is wrong.

## H5.2b — β₅ rests on one outcome pair, not two

Decomposed pairwise (F22), β₅ is **+0.749 (p = .002)** for credit accounts against deposits
₹/capita and **+0.155 (p = .324)** for credit accounts against credit ₹/capita. The pooled headline
of +0.452 is a dilution of the first, not a summary of two comparable estimates.

The decisive pair clears its own placebo battery, so the finding stands — but it is a statement
about **deposit balances**, and the write-up should say so rather than claiming the intensive margin
generally. The pooled figure is nonetheless kept as the headline (D27), because it is what the plan
specified before any data existed and promoting the larger number found afterwards by decomposition
would be retro-fitting.

## H5.3 — The fixed-effect choice, now settled by a test rather than an argument

**Superseded, and recorded rather than deleted.** Earlier drafts of this file conceded that
preferring the conservative fixed-effect scheme (state × outcome and year × outcome) over the
execution plan's literal scheme (state + year + outcome) was a **post hoc** argument, and that a
reader was entitled to read the headline as directionally supported but not significant.

That is no longer the position. The plan's scheme is *nested* in the conservative one, so the
restriction is testable, and F25 tests it: **F(72, 375) = 89.21, p < 10⁻¹⁵**. Outcome-specific
state and year effects are jointly significant; the plan's scheme is misspecified. Variance
explained by the fixed effects alone rises from 0.834 to 0.991.

What remains: the test is the **classical** F-test. With 33 clusters and 72 restrictions no
cluster-robust Wald test exists — the cluster covariance matrix has rank at most G−1 = 32. So the
test licenses the *fixed-effect structure*, not the standard errors, which remain wild-cluster
bootstrapped throughout. Both schemes are still reported side by side in `output/table17`.

## H5.3b — H5b's plain-model support does not survive the change of income measure

The resources interaction is significant on per-capita NSDP (+0.045, p = .013 on deposits ₹;
+0.053, p = .0002 on credit ₹) and is not significant on MPCE (+0.056, p = .423; +0.0004, p = .998).

D25 fixed *before the result was seen* that MPCE would be the more credible of the two for a
moderator standing in for household resources, because NSDP per capita is a production measure
carrying the same booking artefact this project already documents for branch-located deposits. The
rule is applied as written: **H5b's plain-model support is reported as measure-specific, not as a
finding.** The sharp-test null on income (β₆) is unaffected — it holds under both measures and under
every placebo, so that conclusion does not depend on which income measure is preferred.

## H5.4 — The moderator is a proxy, and a coarse one

"Has ever used the internet" is self-reported binary ever-use, not tested skill and not the
six-item NSS 78th ICT battery the original plan specified. The NSS 78th tables sit behind a data
portal; the NSS 75th round's ability items were obtained but **cover only 22 of 33 states** — every
North-Eastern state and small UT is missing from the published table, which is why they are the
robustness measure rather than the primary (D20). Where both exist they correlate r = 0.87–0.90.

Direction of the bias is probably favourable: a coarse proxy attenuates toward zero, so the true
moderation is likely larger than estimated. That is an argument, not a measurement.

## H5.4b — Reverse causality is better addressed than in the first pass, but not closed

The original lag argument (R4) rested on the NSS 75th measure, which covers 22 states. It now also
rests on NFHS-4 women's mobile-phone ownership (2015-16), available for all 33 states, measured
three and a half years before the panel begins and before UPI's April 2016 launch: β₅ = +0.550
(p = .049), with its two same-round placebos null.

Two caveats travel with it. Mobile-phone *ownership* is a weaker construct than internet use —
material access rather than skill — and the contemporaneous version of that same measure is null in
the main tables. And a pre-window moderator rules out the outcome causing the moderator; it does not
rule out a third factor, fixed early, that drives both.

## H5.5 — Moderators are time-invariant, and there are 33 of them

Both moderators are one number per state. The interaction is identified from 33 cross-sectional
values multiplied by within-state variation in UPI. This is the hardest case for cluster-robust
inference, which is why **every p-value in the H5 tables is a wild cluster bootstrap** rather than
a clustered t-test. It also means the design cannot see changes in digital literacy over the
window — and digital literacy was moving fast over exactly these years.

## H5.6 — Two of four outcomes fail the placebo test

R1 clears on credit accounts per adult and on credit ₹/capita. It **fires** on deposits ₹/capita
(urban share produces a larger interaction than digital literacy) and on composite Usage. The
chapter's headline rests on the stacked specification, where the placebo battery clears
decisively — but the plain interaction results on those two outcomes should not be cited as
evidence for a digital-skill effect.

## H5.7 — No district-level test was possible

The obvious answer to H5.5 is more clusters. PhonePe Pulse does carry district-level quarterly data
(783 districts, 2019Q1–2023Q4, present in the existing clone and verified). The blocker is the
moderator: NFHS-5's district fact sheets carry 104 indicators and internet use is not one of them —
it appears only in the 131-indicator state fact sheets. No district-level digital-literacy measure
was found, so there was nothing to interact. Checked, not overlooked (D19).

## H5.8 — Derived urban share is not the Census figure

The urbanisation placebo is derived from NFHS-5's own urban/rural/total decomposition
(`u = (total − rural) / (urban − rural)`), because no verifiable machine-readable Census 2011 state
urbanisation table was obtained. It tracks Census closely where both are known (Delhi 98.2 vs 97.5,
Kerala 48.6 vs 47.7, Maharashtra 46.7 vs 45.2) but is off by ~5pp for Bihar and Goa. It is a
survey-sample quantity used only as a placebo control, and is labelled as such everywhere.

## H5.9 — Census 2011 literacy conflates Andhra Pradesh and Telangana

Telangana did not exist in 2011, so both states carry the undivided Andhra Pradesh literacy figure
in the `lit2011` placebo. Flagged in the data file (`lit2011_undivided_ap`). It affects one of five
placebos and none of the treatment measures.
