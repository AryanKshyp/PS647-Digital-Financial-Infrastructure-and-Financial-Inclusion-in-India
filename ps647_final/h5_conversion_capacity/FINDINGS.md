# Findings Log — H5 (Conversion Capacity)

Append-only, F-numbered. Continues the numbering of `../h1_access_vs_usage/FINDINGS.md` (F0–F14).
Decisions: `DECISIONS.md`. Plan: `EXECUTION_PLAN.md`. Tables: `output/`.

Written as each result appeared, before interpreting it, same discipline as F0–F14.

## F15 — Moderators built and verified; all gates PASS

`scripts/build_moderators.py` → `../data/09_diglit.csv` · `scripts/build_h5_panel.py` →
`output/panel_h5.csv` · `scripts/h5_gates.py` → `output/table14_h5_gates.csv`

**Source verification, before anything was estimated.** The NFHS-5 compiled mirror used
(github.com/jvargh7/nfhs5_factsheets) carries its author's warning that it is not extensively
cross-checked. It was tested against 8 independently published NFHS-5 figures — Bihar women 20.6,
Goa men 82.9, Meghalaya men 42.1, Sikkim women 76.7, Mizoram women 67.6, Andhra women 21.0,
Tripura women 22.9, Delhi men 85.2. **All 8 matched exactly.**

**Cross-source validation.** The two digital-literacy measures come from different surveys, years
and respondents, and agree:

| | r | n |
|---|---|---|
| NFHS-5 women internet vs NSS 75th computer ability | **0.867** | 22 |
| NFHS-5 women internet vs NSS 75th internet ability | **0.903** | 22 |
| NFHS-5 women internet vs NFHS-5 women's own mobile phone | 0.789 | 33 |

**Gates, against thresholds fixed in the plan before the data existed:**

| | Gate 1 corr with UPI | Gate 2 IQR/SD | Gate 3 within-state % |
|---|---|---|---|
| digital literacy | **0.243 PASS** | 1.48 PASS | 65.9% |
| income | **0.687 PASS** | 1.28 PASS | 70.8% |
| *reference: UPI itself* | — | — | *67.1% (= F11 exactly)* |

- Digital literacy is **almost orthogonal to UPI adoption** (r=0.243). The collinearity problem the
  plan worried about does not exist on the skills side. Income is closer (0.687) but inside PASS.
- corr(digital literacy, income) = **0.682** — separable, so the horse race is meaningful.
- VIFs on the two interaction terms: **2.17 and 2.59**. Negligible.
- Spread is wide: Bihar 20.6% to Sikkim 76.7%, SD 16.7.

## F16 — Baseline reproduces F12 exactly; the horse race splits by outcome

`scripts/estimate_h5.py` → `table15_h5_main.csv`, `table15b_h5_margins.csv`,
`table15c_h5_bootstrap.csv`

**Build assertion passed.** Column (1) returns Access **0.31578** and Usage **0.18330** — F12's
figures to five decimals. The merge preserved the H1 panel.

Column (4), the preferred specification. p-values are **wild cluster bootstrap** (B=9999,
Rademacher, null imposed), which is the mandatory R6 check:

| DV | UPI | UPI × skills | UPI × resources |
|---|---|---|---|
| **credit accounts / adult** (extensive, clean) | +0.374 (.017) | −0.061 (.104) | +0.035 (.391) |
| deposits ₹/capita (intensive) | +0.132 (.003) | **+0.056 (.061)** | **+0.045 (.013)** |
| credit ₹/capita (intensive) | +0.044 (.186) | **−0.029 (.044)** | **+0.053 (.0002)** |
| deposit accounts / adult (entangled, D17) | +0.286 (.054) | **+0.124 (.039)** | −0.052 (.315) |

**The sequential-entry finding the plan asked for, and it fires.** On composite Usage the skills
interaction is **+0.0411 (p<0.01) in column (2) and collapses to +0.0135 (n.s.) in column (4)**
once income enters. On that DV the skills result was income all along. It does **not** collapse on
deposits ₹/capita (0.081 → 0.056, still significant).

**Nothing moderates the clean extensive margin.** Neither interaction reaches significance on
credit accounts per adult, and the marginal effect of UPI is flat-to-declining across the literacy
range (0.466 at −1.5 SD, 0.282 at +1.5 SD).

## F17 — R1 placebos: the result is DV-specific, and two of four DVs fail

`scripts/h5_placebo.py` → `table16_h5_placebo.csv`. Each moderator substituted one at a time.

| DV | treatment β₃ | largest same-signed placebo | R1 verdict |
|---|---|---|---|
| credit accounts / adult | −0.061 (.104) | 0% of it | **CLEARS** |
| deposits ₹/capita | +0.056 (.061) | **116%** (urban share, +0.065, p=.079) | **FIRES** |
| credit ₹/capita | −0.029 (.044) | 49%, n.s. | **CLEARS** |
| composite Usage | +0.014 (n.s.) | 187% (urban share) | **FIRES** |

**The deposits result does not survive its own placebo.** Derived urban share produces a *larger*
interaction than digital literacy does. Under the override fixed in the plan, H5a is **not
separately identified** on that DV, whatever its own p-value says.

**The credit ₹/capita result clears, and clears in an unusually strong way.** The digital-literacy
interaction is negative (−0.029, p=.044) while the two same-instrument schooling placebos are
**positive and significant** (+0.018 p=.096, +0.022 p=.032). Opposite signs from the same survey,
same respondents, same year — these are not the same construct.

Two other readings worth logging: the NSS 75th pre-window measures give **+0.045 (p=.006)** and
**+0.040 (p=.008)** on deposits at n=22, stronger than NFHS-5; and **women's mobile-phone ownership
is null on every DV** — owning a handset is not the same endowment as being able to use it.

## F18 — The sharp test: β₅ > 0, and only the digital measures produce it

`scripts/estimate_h5_stacked.py` → `table17_h5_stacked.csv`. 165 × 3 outcomes = **495 rows**,
33 state clusters, each outcome standardised within itself. p = wild cluster bootstrap.

| | (A) state + year + outcome FE | (B) state×outcome + year×outcome FE |
|---|---|---|
| β₁ UPI | +1.256 (.021) | +1.420 (.019) |
| **β₂ UPI × Intensive** ← *H1's test* | −0.660 (.261) | **−0.906 (.081)** |
| β₃ UPI × skills | −0.747 (.103) | **−0.345 (.0077)** |
| **β₅ UPI × skills × Intensive** ← **H5 KEY** | +1.055 (.183) | **+0.452 (.0008)** |
| β₄ UPI × resources | −0.494 (.329) | +0.196 (.223) |
| β₆ UPI × resources × Intensive | +1.048 (.153) | **+0.013 (.936)** |

Under (A), β₅ and β₆ are nearly identical (+1.055, +1.048) and neither is significant — the
signature of a FE structure that cannot separate the two moderators (D22). Under (B):

- **β₅ = +0.452, p = 0.0008.** Digital literacy's moderation is specific to the intensive margin.
- **β₆ = +0.013, p = 0.936.** Income's is not. Income raises both margins alike — a level effect,
  not a second-level-divide effect.
- β₃ = −0.345: more digital literacy means UPI adoption translates *less* into account counts.
- β₂ = −0.906 reproduces H1's pattern (access effect exceeds usage effect) on the stacked data.

**The placebo battery on the headline specification — this is the result the chapter rests on:**

| moderator substituted for skills | role | β₅ | p |
|---|---|---|---|
| **NFHS-5 women ever used internet** | TREATMENT | **+0.452** | **.0008** |
| **NFHS-5 men ever used internet** | alt digital | **+0.398** | **.0047** |
| NFHS-5 women own a mobile phone | alt digital | +0.309 | .195 |
| NFHS-5 women 10+ yrs schooling | placebo, same survey | +0.223 | .352 |
| NFHS-5 men 10+ yrs schooling | placebo, same survey | +0.051 | .818 |
| NFHS-5 female ever attended school | placebo, same survey | +0.152 | .578 |
| Census 2011 literacy | placebo | +0.031 | .932 |
| derived urban share | placebo | +0.113 | .456 |
| NSS 75th computer ability (n=22) | alt pre-window | +0.518 | .244 |

**Only the two internet-use measures produce β₅**, and they agree with each other despite being
measured on different respondents. **All five placebos are null — including three drawn from the
same survey, the same households and the same fieldwork year as the treatment.** No difference in
sampling, timing or instrument can explain the gap.

## F19 — Threshold: increasing returns on deposits, and the margin gap closes in the top tercile

`scripts/estimate_h5_threshold.py` → `table18_h5_threshold.csv`. T1 (11 least literate states)
omitted.

| DV | T1 | T2 | T3 | shape |
|---|---|---|---|---|
| deposits ₹/capita | +0.055 | +0.079 | **+0.146** (d₃ p=.017) | **increasing returns to skill** |
| credit accounts / adult | +0.355 | +0.489 | +0.255 | no monotone structure |
| credit ₹/capita | +0.072 | +0.086 | +0.037 | no monotone structure |

Tercile version of the sharp test — the intensive-minus-extensive gap:

| | T1 | T2 | T3 |
|---|---|---|---|
| gap | **−1.060** (p=.012) | −1.469 | **−0.260** (extra gap in T3 +0.800, p=.021) |

In the least digitally literate third of states UPI adoption raises the extensive margin far more
than the intensive one. **In the most literate third the two nearly converge.** Same finding as
β₅, expressed without assuming linearity.

## F20 — Robustness: β₅ survives five of six perturbations and all 33 leave-one-out refits

`scripts/h5_robustness.py` → `table19_h5_robustness.csv`, `table19b_h5_leave_one_out.csv`

| check | β₅ | p | change |
|---|---|---|---|
| baseline | +0.452 | .0008 | — |
| R3 residualise DigLit on state-mean UPI | +0.358 | .0043 | −20.8% |
| R7 drop Delhi 2023 + Chandigarh 2023 (D7) | +0.427 | .0029 | −5.6% |
| R8 drop 4 small UTs | +0.462 | .0445 | +2.1% |
| R10 drop 3 lowest + 3 highest DigLit states | +0.602 | .0125 | +33.1% |
| **R9 add deposit accounts to the extensive side** | **−0.070** | **.691** | **−116%** |

R3 is worth noting: the R² of digital literacy on state-mean UPI adoption is only **0.059**, so
there was little mechanical collinearity to remove, and removing it costs a fifth of the estimate.

**R5 leave-one-state-out, 33 refits:** range **+0.382 to +0.560**, worst p **0.029**,
**0 sign flips, 0 refits losing 5% significance.** Most influential: Telangana (+0.108),
Maharashtra (−0.070). Stability of the same order as F14 found for the H1 main effect.

**R9 is a genuine failure and is not explained away** (D23). β₅ holds when the extensive margin is
credit accounts and does not hold when deposit accounts are averaged in. F16 shows why the two
cannot be averaged — the skills interaction on deposit accounts is +0.124 and on credit accounts
−0.061 — but that is an explanation, not a rescue.

## F21 — H5 verdict against the pre-committed rules

**H5a (skills).** Not supported in the plain form. β₃ is not significant on the clean extensive
margin, and where it is significant on an intensive margin it either fails its own placebo
(deposits ₹) or is **negative** (credit ₹). The plan's "β₃ < 0 → catch-up" row is the closest
match, and it applies to credit ₹/capita only.

**H5b (resources).** Supported on the intensive margin: +0.045 (p=.013) on deposits ₹, +0.053
(p=.0002) on credit ₹, and it is the interaction that survives when both enter together on
composite Usage. Null on the clean extensive margin. **In the plain interaction model, resources
beat skills** — the Cole–Sampson–Zia outcome the plan flagged as a live possibility.

*(Refined by F22, logged after this verdict was written: β₅ is carried entirely by the
credit-accounts-vs-deposits-₹ pair, +0.749; the credit-₹ pair is null. The verdict below stands,
but the sharper statement is in F22.)*

**The corollary — the sharp test — is where H5 actually holds, and it holds for skills, not for
resources.** β₅ = +0.452 (p=.0008), β₆ = +0.013 (p=.936). Conversion capacity conditions *which
margin* infrastructure moves, and it is the **digital-skill** endowment that does the conditioning,
not the income endowment. Income shifts both margins together; digital literacy trades one against
the other.

This is not the result the plain interaction model suggested, and the two must be reported
together. The plain model asks "does the effect get bigger?" — for which income wins. The sharp
test asks "does the effect change *kind*?" — for which only digital literacy does anything.

## F22 — Pairwise decomposition: β₅ is carried by one outcome pair, and the channel-intensity supplementary is null

`scripts/h5_supplementary.py` → `output/table20_h5_supplementary.csv`

Two checks that were owed and had not been run: the pairwise decomposition R9 should have prompted,
and the digital-channel-intensity specification promised in `EXECUTION_PLAN.md` §6.5.

### S1 — which outcome pair carries the headline

The stacked test pools two intensive outcomes against one extensive outcome, so β₅ is an average.
Run one pair at a time, 330 rows each:

| extensive vs intensive | β₅ | p | β₆ (income) | p |
|---|---|---|---|---|
| pooled — the table17 headline | +0.452 | .0008 | +0.013 | .936 |
| **credit accounts vs deposits ₹/capita** | **+0.749** | **.0019** | −0.065 | .766 |
| credit accounts vs credit ₹/capita | +0.155 | **.324** | +0.091 | .530 |
| deposit accounts vs deposits ₹/capita *(entangled)* | −0.296 | .446 | +0.420 | .014 |
| deposit accounts vs credit ₹/capita *(entangled)* | −0.890 | .089 | +0.576 | .040 |

**β₅ is not an average of two similar effects. It is carried entirely by the deposits-₹ pair.**
The credit-₹ pair is null. The headline figure of +0.452 is therefore a dilution of +0.749, not a
summary of two comparable estimates, and the sharper statement is available:

> Digital literacy shifts UPI's effect away from credit-account creation and toward **deposit
> balances specifically** — not toward credit volume.

**The decisive pair clears its own placebo battery**, which is what licenses the sharper claim:

| moderator | role | β₅ | p |
|---|---|---|---|
| NFHS-5 women ever used internet | TREATMENT | +0.749 | **.0019** |
| NFHS-5 men ever used internet | alt digital | +0.690 | **.0054** |
| NFHS-5 women own a mobile phone | alt digital | +0.291 | .311 |
| NFHS-5 women 10+ yrs schooling | placebo, same survey | +0.343 | .175 |
| NFHS-5 men 10+ yrs schooling | placebo, same survey | +0.127 | .620 |
| NFHS-5 female ever attended school | placebo, same survey | +0.348 | .271 |
| Census 2011 literacy | placebo | +0.188 | .633 |
| derived urban share | placebo | +0.353 | .300 |

**The last two rows locate R9.** With the entangled deposit-accounts indicator on the extensive
side, β₅ turns negative (−0.296, −0.890) and β₆ becomes significant (+0.420, +0.576). So R9's
reversal is not noise: substituting the entangled indicator does not weaken the skills result, it
**replaces it with an income result**. That is what an accounting relationship looks like —
PhonePe registration requires a bank account, richer states register more, and the deposit-account
count follows mechanically. D17's credit-only rule is doing real work here, and F22 is the clearest
evidence for it in either chapter.

### S2 — digital-channel intensity (the §6.5 supplementary, finally run)

DV = ln(1 + PhonePe transactions or value per capita). β₁ is uninterpretable by construction —
a transaction requires a registration — so only β₃ is read.

| DV | β₃ on digital literacy | p |
|---|---|---|
| ln(1 + transactions per capita) | −0.020 | .890 |
| ln(1 + value per capita) | −0.409 | .089 |

All five placebos are null on both. **Digital literacy does not steepen the conversion of PhonePe
registrations into PhonePe transactions.** Together with F18 this narrows what H5 is about: the
skills endowment does not make people use the payment app more intensively per registration; it
changes how payment adoption maps onto the **banking** system. Reported as a null, and it is a
useful one — it rules out "digitally literate people just transact more" as the mechanism behind
β₅.

## F23 — Descriptives: the compression H1 documented is inherited, and the two moderators are not the same variable

`scripts/h5_descriptives.py` → `output/table21_h5_descriptives.csv`

Run before the estimates, per the report's Chapter 4 template §4.3. Missing from the first pass.

**Compression.** H1's limitation 4 records that Usage is severely right-skewed after pooled
min–max normalisation and that this threatens the access–usage comparison itself. It is inherited
here, and it is not uniform across outcomes:

| outcome | share below 0.20 | skew |
|---|---|---|
| credit accounts / adult *(extensive)* | 46.7% | 1.10 |
| deposits ₹/capita *(intensive)* | 83.0% | 2.50 |
| credit ₹/capita *(intensive)* | 86.1% | 3.13 |

The intensive-margin outcomes are roughly twice as compressed as the extensive one. **An
unstacked comparison of coefficients across them was never like-for-like.** This is the specific
justification for standardising within outcome before stacking (§6.3) — it is a repair of a
limitation H1 had to leave open, not a convenience.

**Moderator separability.** corr(digital literacy, ln NSDP pc) = 0.682; corr(digital literacy,
ln MPCE) = 0.766; **corr(ln NSDP pc, ln MPCE) = 0.844 — the two income measures are not
interchangeable**, which is what makes F24 possible. The two primary moderators disagree by up to
23 rank positions out of 33 (Telangana 28th on literacy, 5th on income; Manipur 15th and 30th).
Without that disagreement the horse race would be undefined.

**Cross-tabulating the terciles** shows where the design is thin: 7 states in low-literacy /
low-income, 5 in high/high, and 17 of 33 off the diagonal. The horse race is identified, but the
corners are sparse and any claim about them should be correspondingly weak.

## F24 — The resources channel, brought to the skills channel's standard: H5b is measure-dependent

`scripts/h5_income.py` → `output/table22_h5_income.csv`

H5b was in every specification from the start, but it had one measure where skills had five, no
placebo battery, and no threshold specification. All three are now run.

### I1 — the income result does not survive the change of measure

| DV | ln NSDP pc *(production)* | ln MPCE *(consumption)* |
|---|---|---|
| credit accounts / adult | +0.035 (.391) | +0.019 (.625) |
| deposits ₹/capita | **+0.045 (.013)** | +0.056 (**.423**) |
| credit ₹/capita | **+0.053 (.0002)** | **+0.000 (.998)** |

**The headline H5b result is specific to NSDP per capita and vanishes under MPCE.** On credit
₹/capita — where NSDP gave the single strongest income coefficient in the whole H5 chapter,
p = 0.0002 — MPCE returns +0.0004, p = 0.998.

This is not a tie-break to be split. NSDP per capita is a **production** measure: corporate output
books to the state of registration, which inflates Delhi and Maharashtra in precisely the way
`../h1_access_vs_usage/LIMITATIONS.md` §4 already documents for bank deposits recorded at branch
location. MPCE is household **consumption**, measured on households. For a moderator that is
supposed to represent household *resources*, MPCE is the better construct and NSDP is the
convenient one. The honest reading is that **H5b's apparent support was riding on the measure with
the known attribution artefact.**

Note also what happens to the skills coefficient when MPCE occupies the resources slot: on credit
accounts it moves from −0.061 (p=.104) to −0.054 (p=.076).

### I2 — the resources slot, placebo-tested (never done before)

Stacked sharp test, scheme (B); skills held at digital literacy; each candidate substituted into
the resources slot:

| variable in the resources slot | role | β₆ | p |
|---|---|---|---|
| ln NSDP per capita | TREATMENT (H5b) | +0.013 | .936 |
| ln MPCE | alt resources | +0.039 | .805 |
| women's own bank account, 2015-16 | placebo: **baseline inclusion** | +0.247 | .543 |
| women 10+ yrs schooling | placebo | −0.002 | .996 |
| Census 2011 literacy | placebo | −0.114 | .827 |
| derived urban share | placebo | +0.007 | .964 |

β₆ is null for **both** income measures and for every placebo. The failure of income to
discriminate between margins is therefore a property of the resources channel itself, not an
artefact of the NSDP proxy. F18's conclusion survives F24's demolition of the plain-model result.

### I3 — income terciles

| DV | T1 (poorest 11) | T2 | T3 (richest 11) |
|---|---|---|---|
| credit accounts / adult | +0.326 | +0.469 | +0.406 |
| deposits ₹/capita | +0.160 (p=.046) | +0.183 | +0.203 |
| credit ₹/capita | +0.032 (n.s.) | **+0.101 (p=.005)** | **+0.115 (p=.001)** |

The credit-₹ income effect is a **threshold**: absent in the poorest third, present and similar in
the upper two. That is the shape Cole–Sampson–Zia predicts for a price constraint. It is reported
with I1 attached — the same coefficient disappears under MPCE.

## F25 — Specification tests: the fixed-effect scheme is required by the data, and β₅ survives a pre-UPI moderator

`scripts/h5_spec_tests.py` → `output/table23_h5_spec_tests.csv`

### S1 — the weakest link in H5's pre-commitment, now testable

`LIMITATIONS.md` H5.3 conceded that preferring scheme (B) over the plan's literal scheme (A) was a
**post hoc** argument. Scheme (A) is nested in (B), so the restriction is testable.

| | RSS | parameters |
|---|---|---|
| (A) state + year + outcome FE | 81.578 | 48 |
| (B) state × outcome + year × outcome FE | 4.500 | 120 |

**F(72, 375) = 89.21, p < 10⁻¹⁵.** H0 — that outcome-specific state and year effects are jointly
zero — is rejected overwhelmingly. Variance explained by the fixed effects alone rises from 0.834
to 0.991. **Scheme (A) is misspecified; scheme (B) is required by the data, not chosen by the
analyst.** This is the same logical move H1 makes in §3.4.1, where the Hausman test rather than the
analyst rules out random effects.

Stated limitation: with 33 clusters and 72 restrictions a cluster-robust Wald test is unavailable
(the cluster covariance matrix has rank at most G−1 = 32), so this is the classical F-test. It
licenses the **fixed-effect structure**, not the standard errors; those remain bootstrapped
throughout.

### S2 — a moderator measured before UPI existed at scale

Every digital-literacy measure used so far is either contemporaneous with the outcomes (NFHS-5,
2019-21) or covers 22 states (NSS 75th). NFHS-4 (2015-16) carries women's own mobile-phone
ownership for all 33 panel states — three and a half years before the panel begins, and before
UPI's April 2016 launch.

| moderator in the skills slot | vintage | β₅ | p |
|---|---|---|---|
| internet use *(headline)* | 2019-21 | +0.452 | **.0008** |
| mobile phone | 2019-21 | +0.309 | .195 |
| **mobile phone** | **2015-16** | **+0.550** | **.049** |
| change in mobile phone | 2016→2021 | −0.124 | .273 |
| 10+ yrs schooling *(placebo)* | 2015-16 | +0.248 | .321 |
| own bank account *(placebo)* | 2015-16 | +0.326 | .440 |

**β₅ survives on a moderator that cannot have been caused by UPI-era outcomes**, and the two
placebos from the *same survey round* do not reproduce it. This is a considerably stronger answer
to reverse causality than anything in the first pass, where the lag argument rested on the 22-state
NSS measure.

Two honest observations. The 2015-16 mobile measure is *larger* than the contemporaneous 2019-21
one (+0.550 vs +0.309), which is not what a mechanical story predicts but is only a single
comparison. And the *change* in mobile ownership returns nothing — it is the level of the
endowment that matters here, not its growth.

### S3 — Hausman, for symmetry with H1 §3.4.1

Fixed effects are required on credit accounts (χ²=22.0, p=.001) and deposits ₹ (χ²=75.3,
p<10⁻¹³). On credit ₹ the statistic is negative (−2.08), meaning the estimated variance difference
is not positive definite — **an uninformative test, not support for random effects**. Fixed effects
are retained throughout.
