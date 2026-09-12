# H5 — Conversion Capacity: Digital Literacy and Income as Complements to Digital Financial Infrastructure

**PS 647 Group Project**
Main PS: *To what extent has the expansion of India's digital financial infrastructure improved financial inclusion, and has it reduced persistent gaps across rural–urban, gender and income groups?*

---

## 1. The hypothesis

**H5 (unified).** The effect of digital financial infrastructure on financial inclusion is conditional on the *conversion capacity* of the population — the endowments required to turn access into use.

- **H5a — Skills channel.** The positive effect of digital financial infrastructure on financial inclusion is stronger where digital literacy is higher.
- **H5b — Resources channel.** The positive effect of digital financial infrastructure on financial inclusion is stronger among higher-income groups.

**Corollary (the sharp test).** Because both skills and resources are *second-level divide* phenomena, neither should moderate first-level access outcomes. Conversion capacity should condition **usage**, not **access**.

### Why this is one hypothesis, not two

Digital literacy and income are each other's primary confounder. Digital literacy correlates tightly with income, education and urbanisation. Estimated separately:

- A positive skills interaction may simply be capturing "richer states benefit more" → that is H5b wearing a costume.
- A positive income interaction may simply be capturing "more skilled people benefit more" → that is H5a wearing a costume.

Neither result is interpretable in isolation. Entering both interactions in one model is not a convenience — it is the identification strategy. The horse race between skills and resources *is* the contribution.

---

## 2. Theoretical framing

The organising framework is the **three-level digital divide**.

| Level | Content | Where our variables sit |
|---|---|---|
| **First — Access** | Physical availability of ICTs, infrastructure, affordability | Our **independent variable** (DFI) |
| **Second — Usage & skills** | Ability to use digital tools effectively; passive consumption vs capital-enhancing use | Our **moderators** (digital literacy, income) and our primary **outcomes** |
| **Third — Outcomes** | Tangible financial, economic and social benefits | Secondary outcomes (formal saving, borrowing) |

Hargittai (2002) classified inequalities in the *type* of use as the second-level divide; van Dijk's usage-gap thesis holds that better-resourced users deploy advanced, capital-enhancing applications while others default to passive use. van Deursen & van Dijk (2019) formalise the progression from access → skills → outcomes.

This framework generates a prediction that a bare interaction model cannot: **conversion capacity should be irrelevant at the first level and decisive at the second.** If our moderators also condition account ownership, the framework is wrong or our moderators are contaminated. That falsifiability is the strength of the design.

### Prior expectations from the literature

The mechanism is theoretically settled but empirically contested, and the design should absorb three qualifications:

1. **Necessary but not sufficient.** ICRIER's district-level UPI work finds socio-economic indicators including digital literacy are necessary but not sufficient for adoption; the coefficient on high digital literacy remains below 1. → Expect a modest β, not a large one.
2. **Prices may dominate knowledge.** Cole, Sampson & Zia (2011, *Journal of Finance*) find financial education raised demand for bank accounts only among the least educated and least literate, while small subsidies moved demand substantially more. → H5b may dominate H5a. Be prepared for this.
3. **Infrastructure saturates.** The district-level supply-side study finds a structural break in the staggered 5G rollout: past a connectivity threshold, further infrastructure yields near-zero marginal returns for onboarding, while merchant-network density outperforms infrastructure by roughly six times. → Specify thresholds, not just linear interactions, and control for merchant density.

---

## 3. Variables

### 3.1 Dependent variables

Run the **full menu**, not one DV. The comparison across the menu is the sharp test in §5.3.

| Level | DV | Construction | Source |
|---|---|---|---|
| **First (access)** | Account ownership | % adults 18+ with an account | CAMS 2022-23; Findex 2025 |
| **First (access)** | Debit/RuPay card ownership | % adults holding a card | CAMS 2022-23; Findex 2025 |
| **Second (usage)** | **UPI transactions per capita** ★ | ln(1 + UPI txn count ÷ adult population) | PhonePe Pulse (district × quarter) |
| **Second (usage)** | UPI value per capita | ln(1 + UPI value ÷ adult population) | PhonePe Pulse |
| **Second (usage)** | Account activity | 1 − (zero-balance PMJDY ÷ total PMJDY) | PMJDY portal (monthly) |
| **Third (depth)** | Credit deepening | Credit accounts per 1,000 adults; C-D ratio | RBI BSR / DBIE |
| **Third (depth)** | Formal saving / borrowing | Binary indicators | Findex 2025; CAMS |

★ **Primary DV: UPI transactions per capita.** Continuous, high variance, district-level, long time series. Use logs — raw UPI volumes are heavily right-skewed and Maharashtra/Karnataka will otherwise dominate the fit.

**Critical:** UPI transactions appear here as a DV. They must therefore be **excluded** from the DFI index. Regressing digital payments on digital payments is the most likely fatal error in this design.

### 3.2 Independent variable — DFI (enabling layer only)

| Component | Source | Level |
|---|---|---|
| Internet subscribers per 100 | TRAI (quarterly) | Telecom circle ≈ state |
| Rural teledensity | TRAI | Circle |
| BharatNet gram panchayats connected | DoT / data.gov.in | State, District |
| Bank branches + BC outlets per 100k adults | RBI DBIE | District |
| ATMs per 100k adults | RBI DBIE | District |

**Construction:** standardise each, extract the first principal component, standardise the result. Report the loadings and the variance explained in an appendix.

**Explicitly excluded and why:**

| Excluded | Reason |
|---|---|
| UPI transactions | It is the DV |
| RuPay / AEPS volumes | Downstream of UPI adoption |
| PoS terminals | Arguably an outcome of merchant digitisation |
| Aadhaar saturation | Near-saturated post-2018; negligible cross-state variance |

### 3.3 Moderators

**H5a — Digital literacy (skills).** Built from the NSS 78th round MIS ICT module, using only items executable **without an internet connection**, so the moderator measures skill endowment rather than connectivity endowment.

| # | Item | Include |
|---|---|---|
| 1 | Use copy and paste tools to duplicate or move information within a document | ✅ |
| 2 | Use basic arithmetic formulae in a spreadsheet | ✅ |
| 3 | Create electronic presentations with presentation software | ✅ |
| 4 | Connect and install a new device | ✅ |
| 5 | Configure software | ✅ |
| 6 | Transfer files between a computer and other devices | ✅ |
| 7 | Write a computer program in a specialised language | ✗ near-zero variance |
| 8 | Send e-mails with attached files | ✗ connectivity-dependent |
| 9 | Find/download/install software; online search | ✗ connectivity-dependent |

```
DigLit_s = first principal component (or simple mean) of z-scores on items 1–6
```

Report Cronbach's alpha and both the PCA and simple-average versions, so no one can accuse the group of index-shopping.

**H5b — Income (resources).**

| Measure | Source | Level |
|---|---|---|
| Log NSDP per capita | MoSPI / state statistical handbooks | State × year |
| MPCE | HCES 2022-23, 2023-24 | State × sector |
| Household asset-wealth index (PCA) | CAMS asset possession module | Individual → district/state |
| Within-economy income quintile | Findex 2025 | Individual |

### 3.4 Controls

| Control | Source | Why it is in |
|---|---|---|
| % urban | Census projections | Urbanisation drives both DFI and inclusion |
| General literacy rate (2011) | Census 2011 | Separates digital from general human capital |
| **Financial literacy score** | NCFE-FLIS 2019 (state/UT) | Without it, β₃ cannot be claimed as a *digital* skill effect |
| **UDYAM registrations per capita** | UDYAM portal | Merchant density outperformed infrastructure ~6× in prior work |
| % SC/ST population | Census | Structural exclusion |
| Female LFPR | PLFS | Links to H4 |
| Household electrification | Census / NFHS-5 | Precondition for device use |

---

## 4. Data sources

| Source | Provides | Level | Access |
|---|---|---|---|
| **MIS, NSS 78th round (2020-21)** | Nine ICT skill items; only 38% of households digitally literate; Kerala first on all nine parameters | State | Tables: https://dataful.in/datasets/18169/ · Microdata: https://microdata.gov.in/NADA/index.php/catalog/218 |
| **CAMS 2022-23 (NSS 79th round)** | ICT skills **and** financial inclusion in one instrument; 302,086 households, ~1.3m persons; 94.6% account ownership; 82.1% rural vs 91.8% urban youth internet use | State × gender × sector | Microdata: https://microdata.gov.in/NADA/index.php/catalog/220 · CSV mirror: https://data.opencity.in/dataset/comprehensive-annual-modular-survey-cams-nss-79th-round-2022-23 · Report: https://www.mospi.gov.in/sites/default/files/publication_reports/CAMS%20Report_October_N.pdf |
| **CMS:T 2025 (Jan–Mar 2025)** | Second wave. Rural men able to bank online 39%→54%, rural women 17%→30%, urban women 38%→51% | National; state estimates carry RSE warnings | MoSPI |
| **PhonePe Pulse** | UPI registered users and transactions | District × quarter | Open data (GitHub / pulse.phonepe.com) |
| **NPCI** | State-wise UPI usage (added June 2025) | State | npci.org.in |
| **PMJDY portal** | Accounts, zero-balance accounts | State, monthly | pmjdy.gov.in |
| **RBI DBIE / BSR** | Branches, ATMs, deposits, credit accounts | District | dbie.rbi.org.in |
| **TRAI** | Internet and mobile subscribers | Telecom circle | trai.gov.in |
| **NCFE-FLIS 2019** | Financial literacy by state; 27% nationally, Goa highest, Chhattisgarh lowest | State/UT | https://ncfe.org.in/wp-content/uploads/2023/12/NCFE-2019_Final_Report.pdf |
| **PMGDISHA** | 7.35 cr enrolled, 6.39 cr trained, 4.78 cr certified | State/UT | https://www.data.gov.in/resource/statesut-wise-achievements-pradhan-mantri-gramin-digital-saksharta-abhiyan-pmgdisha-scheme |
| **NFHS-5 (2019-21)** | Women's mobile ownership, internet use, account use | **District** | IIPS / DHS STATcompiler |
| **Global Findex 2025** | Account ownership 89% (2024) vs 77.5% (2021); Digital Connectivity Tracker | Country / individual | https://microdata.worldbank.org/index.php/catalog/7916 |

**Master panel spine:** district × quarter, 2019–2025 (~640 districts × ~24 quarters). Survey-based access outcomes run at state level as a separately labelled specification, since CAMS is state-representative only.

---

## 5. Empirical strategy

### 5.1 Baseline

```
ln(1 + UPI_dt) = α
               + β₁ · DFI_dt
               + β₃ · (DFI_dt × DigLit_s)      ← H5a
               + β₄ · (DFI_dt × Income_dt)     ← H5b
               + γ'X_dt
               + μ_d + λ_t + ε_dt
```

- All continuous variables **mean-centred** before interacting, so β₁ reads as the DFI effect at average conversion capacity rather than at an out-of-support zero.
- `μ_d` district fixed effects; `λ_t` quarter fixed effects.
- Standard errors clustered at state level; **wild cluster bootstrap** given ~30 clusters.
- The standalone `DigLit_s` term is absorbed by district fixed effects (time-invariant, one survey wave). State this in a footnote — the interaction remains identified from within-district variation in DFI.

**Decision rule**

| Result | Reading |
|---|---|
| β₃ > 0 | Skills channel operates — H5a supported |
| β₄ > 0 | Resources channel operates — H5b supported |
| β₃ > 0, β₄ ≈ 0 | Conversion is about **capability**; policy → skilling |
| β₃ ≈ 0, β₄ > 0 | Conversion is about **affordability**; policy → subsidy (consistent with Cole–Sampson–Zia) |
| Both > 0 | Independent channels; sequencing matters for both |
| Both ≈ 0 | Infrastructure works uniformly — genuine convergence, contradicts H5 |
| β₃ < 0 | Catch-up: low-literacy areas gain most. Interesting and publishable |

### 5.2 Sequential entry

Report four columns to show how each coefficient behaves as the other enters:

| Col | Specification |
|---|---|
| (1) | DFI only |
| (2) | DFI + DFI×DigLit |
| (3) | DFI + DFI×Income |
| (4) | DFI + both interactions ← **preferred** |

If β₃ is large in (2) and collapses in (4), the skills result was income all along. That is a finding, not a failure — report it.

### 5.3 The sharp test: stacked DV specification

Stack all DVs in long format, one row per district × quarter × outcome, each DV standardised to mean 0 SD 1:

```
Y_dtk = β₁·DFI_dt
      + β₂·(DFI_dt × Usage_k)
      + β₃·(DFI_dt × DigLit_s)
      + β₅·(DFI_dt × DigLit_s × Usage_k)     ← the key term
      + γ'X_dt + μ_d + λ_t + θ_k + ε_dtk
```

where `Usage_k = 1` for second/third-level outcomes and `0` for first-level access outcomes.

**β₅ > 0 is the strongest available evidence for H5**, because it shows digital literacy conditions *usage* specifically rather than being a generic development proxy. A generic income or development story would predict β₅ ≈ 0.

This also cleanly separates H5 from H1: H1 tests β₂ (does infrastructure move access more than usage), H5 tests β₅ (does capability condition that difference).

### 5.4 Threshold specification

Given the documented saturation break, do not assume linearity:

```
ln(1+UPI_dt) = β₁·DFI_dt
             + Σ_{k=2,3} δ_k·(DFI_dt × 1[DigLit_s ∈ tercile k])
             + γ'X_dt + μ_d + λ_t + ε_dt
```

- `δ₃ > δ₂ > 0` → true complementarity, increasing returns to skill
- `δ₂ ≈ δ₃ > 0` → floor effect; literacy matters up to a threshold then stops (consistent with "necessary but not sufficient")

---

## 6. Robustness

| # | Check | Purpose |
|---|---|---|
| R1 | **Placebo interaction**: replace DigLit with log NSDP and with 2011 general literacy | If these produce similar β₃, the skills result is a development proxy. **Run this first — it is the first thing anyone will ask for.** |
| R2 | **Alternative moderators**: PMGDISHA certified per 1,000 rural adults; Census 2011 computer ownership; residualised ICT index | Stability across conceptually distinct measures |
| R3 | **Residualisation**: regress DigLit on DFI, interact the residual | Removes mechanical collinearity; bootstrap the SEs |
| R4 | **Lag structure**: moderator from MIS 2020-21, outcomes from 2022-25 | Breaks reverse causality |
| R5 | **State-level replication** | Robustness to unit of analysis |
| R6 | **UPI value vs count** as DV | Breadth vs depth of adoption |
| R7 | Winsorise UPI at 1st/99th percentile | Outlier sensitivity |
| R8 | Drop Delhi, Chandigarh, small UTs | PMGDISHA excludes urban agglomerations |

### Residualisation (R3)

```
DigLit_s = π₀ + π₁·DFI_s + ν_s     →     DigLit⊥_s = ν̂_s
```

β₃ then reads: *returns to infrastructure are higher in places with more skill than their connectivity would predict* — arguably a sharper statement of H5 than the raw version.

---

## 7. Threats to validity

| Threat | Severity | Mitigation |
|---|---|---|
| **Digital literacy is endogenous to development** — education is the largest contributor to inequality in ICT skill acquisition (Shapley decomposition, MIS 78th) | High | R1 placebo; income controls; §5.2 sequential entry |
| **Reverse causality** — a Jharkhand study finds trust is a *result* of UPI adoption, not a prerequisite; confidence developed through use | High | R4 lag (2020-21 moderator → 2022-25 outcomes) |
| **Collinearity** DFI–DigLit | Medium | Report correlation matrix and VIFs; if r > 0.85, use R3 |
| **Correlated measurement error** if moderator and DV come from the same survey instrument | Medium | Moderator from MIS 2020-21, DVs from CAMS/administrative sources — different survey, year and respondents |
| **Ceiling effect on access** — account ownership is 89–94.6% with almost no cross-state variance | Medium | Never headline access as DV; it appears only in the §5.3 stacked test |
| **PhonePe is one PSP, not all of UPI** | Medium | State explicitly as a proxy limitation; cross-check against NPCI state-wise data (June 2025) |
| **Self-reported ICT skills** | Low–Med | Likely biases *against* finding complementarity where it matters most — note as conservative |
| **Small cluster count (~30 states)** | Low–Med | Wild cluster bootstrap |
| **CMS:T state estimates** not designed for state-level use | Low | Report RSEs or drop small states |

---

## 8. What we can claim

**If β₃ > 0 and β₅ > 0:** uniform national infrastructure rollout mechanically *widens* state-level gaps, because identical investment converts at different rates depending on pre-existing skill. Digital skilling must be sequenced before or alongside connectivity spending, not after it. This answers the second half of the main PS directly — digitalisation expanded formal access but reproduced exclusion at the usage margin.

**If β₄ dominates β₃:** the binding constraint is affordability, not capability. Consistent with Cole–Sampson–Zia. Policy implication shifts to transaction-cost subsidy and device affordability rather than training.

**If both ≈ 0:** infrastructure is genuinely inclusive and the persistent gaps documented in the motivation come from elsewhere — a null worth reporting honestly.

---

## 9. Work plan

| Step | Task | Output |
|---|---|---|
| 1 | Download MIS state tables from dataful.in, build 6-item DigLit index | 30-row spreadsheet |
| 2 | Correlate DigLit with DFI components | **Go / no-go decision on testability** |
| 3 | Build DFI index (PCA) — assign to **one** person, everyone else imports | `dfi_index` column |
| 4 | Assemble PhonePe Pulse district × quarter panel | UPI DVs |
| 5 | Merge administrative DVs (PMJDY, RBI BSR) | Master panel |
| 6 | Baseline + sequential entry (§5.1–5.2) | Table 1 |
| 7 | Stacked DV specification (§5.3) | Table 2 — the headline |
| 8 | Threshold specification (§5.4) | Table 3 |
| 9 | Robustness R1–R8 | Appendix |

**Step 2 is the gate.** If DigLit and DFI correlate above 0.85, the hypothesis is not testable as specified and the group must switch to the residualised or PMGDISHA moderator before investing further effort.

### Master panel structure

```
district_id | state | quarter
── DV ──
upi_txn_pc | upi_value_pc | account_activity | credit_accts_1000
── IV ──
dfi_index
── Moderators ──
diglit_mis        (state, 2020-21)   ← H5a
nsdp_pc_log       (state × year)     ← H5b
── Controls ──
urban_pct | literacy_2011 | flis_score | udyam_pc | sc_st_pct | female_lfpr
```

---

## 10. References

**Theory**
- Hargittai, E. (2002). Second-Level Digital Divide: Differences in People's Online Skills. *First Monday* 7(4).
- van Deursen, A. & van Dijk, J. (2019). The first-level digital divide shifts from inequalities in physical access to inequalities in material access. *New Media & Society* 21(2).
- van Dijk, J. (2020). *The Digital Divide*. Polity.

**Core empirical**
- Cole, S., Sampson, T. & Zia, B. (2011). Prices or Knowledge? What Drives Demand for Financial Services in Emerging Markets? *Journal of Finance* 66(6), 1844–1867. https://www.hbs.edu/ris/Publication%20Files/09-117.pdf
- ICRIER / IPCIDE (2024). *Diffusion of Digital Payments in India: Insights from PhonePe Pulse*. WP1. https://icrier.org/pdf/IPCIDE-wp1.pdf
- NBER Working Paper 33259. *Breaking Barriers to Financial Access*. https://www.nber.org/system/files/working_papers/w33259/w33259.pdf
- Balasundaram et al. (2025). The Impact of Digital Financial Inclusion on Income Inequality in Rural India. *Indian Economic Journal*. https://journals.sagepub.com/doi/10.1177/00194662251332866
- Gupta, Anand & Gupta (2025). Are digital payments driven by wealth inequality? Evidence from UPI adoption in India. https://www.sciencedirect.com/science/article/abs/pii/S0313592625002899
- Agarwal, Alok, Ghosh, Ghosh, Piskorski & Seru. Banking the Unbanked: What Do 255 Million New Bank Accounts Reveal About Financial Access? SSRN 2906523.
- IMF. *India's Financial System*, Ch. 7: Digital Financial Services and Inclusion. https://www.elibrary.imf.org/display/book/9798400223525/CH007.xml

**Sceptical counter-case (engage with these)**
- Fernandes, D., Lynch, J. & Netemeyer, R. (2014). Financial Literacy, Financial Education, and Downstream Financial Behaviors. *Management Science* 60(8).
- Kaiser, T. & Menkhoff, L. (2017). Does Financial Education Impact Financial Literacy and Financial Behavior, and If So, When? *World Bank Economic Review* 31(3).

**Reference / descriptive**
- Global Findex 2025. https://microdata.worldbank.org/index.php/catalog/7916
- GSMA Mobile Gender Gap Report. https://www.gsma.com/gender-gap/
- NCFE (2019). Financial Literacy and Inclusion Survey. https://ncfe.org.in/wp-content/uploads/2023/12/NCFE-2019_Final_Report.pdf

---

## Appendix — Relationship to other hypotheses

| | Interacts DFI with… | Distinct because |
|---|---|---|
| **H1** | *type of outcome* (access vs usage) | No population moderator — holds population fixed, varies outcome |
| **H2** | rural/urban | Geographic |
| **H4** | gender | Demographic |
| **H5** | *conversion capacity* (skills + resources) | Holds outcome fixed, varies capability |

H1 tests β₂ in §5.3; H5 tests β₅ in the same equation. **One model, two hypotheses, no overlap.** Present them as adjacent columns of the same table rather than as separate analyses.

If the group later wants a triple interaction with gender or rural status, run **only one** — `DFI × DigLit × Female` is the natural choice given the main PS emphasises the gender gap. Triple interactions exhaust statistical power quickly.
