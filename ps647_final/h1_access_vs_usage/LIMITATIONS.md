# Limitations — H1

Ordered by how much damage each does to the conclusions. Sources in `FINDINGS.md` and `DECISIONS.md`.

---

## 1. Identification — the binding limitation

**Physical tracks: the regressors barely move.** Within-state variation is **7.0%** (branches) and
**8.7%** (ATMs) over six years — below the 10% FAIL threshold fixed before we looked (F4). Fixed
effects use only within-state movement, so the null on branches and ATMs **cannot be distinguished
from "not enough variation to detect anything"**. Extending to 12 years raises it to 15.3% — better,
still below the 25% PASS line. *Any null on physical infrastructure must be reported with these
numbers attached.*

**Digital track: variation is ample, causality is not.** UPI within-state variation is 67.1%, so the
above does not apply. But fixed effects remove fixed state differences and the common national trend
— **not state-specific time-varying confounders.** Smartphone penetration, fintech entry and youth
share all rose alongside both UPI adoption and credit accounts over FY2019–23. The digital result is
a within-state correlation between two co-trending series. **No causal claim is available.**

**Reverse causality is live, not hypothetical.** Hausman rejects random effects (p<0.0001), which is
direct evidence that state effects are correlated with the regressors (F6).

## 2. The digital result is exploratory by construction

UPI was added **after** seeing the physical null. The pre-committed hypothesis (D10) named branches
and ATMs, and it failed. The UPI finding therefore cannot be reported as a hypothesis that was
tested and passed — it is a hypothesis **generated** by this data, for a future design to test.
Stating it any other way is the retro-fitting that pre-committing was meant to prevent.

## 3. Data defects we know about

- **Deposit-account breaks in RBI's source** (D7): Delhi 2023, Chandigarh 2023 inside the window.
  Not our extraction — the savings-account column roughly doubles in one year. Two cells of 165, and
  they were enough to move the deposit-account coefficient from +0.193 to +0.018 (F13).
- **Adult population is interpolated**, not published — 243 of 266 state-years use an estimated 18+
  share (D6). Being near-linear, it also *suppresses* within-state variation in the per-adult
  regressors, making limitation 1 worse than it looks.
- **Two states dropped** for having no income data: Lakshadweep, and Dadra & Nagar Haveli / Daman &
  Diu (D1). Both tiny.
- **Boundary changes forced merges:** J&K + Ladakh, and (12-year panel only) Andhra Pradesh +
  Telangana (D2, D13). Each merged unit is one state throughout, so nothing state-specific can be
  said about either half.

## 4. Measurement

- **Attribution differs across sources, three ways.** Bank deposits and credit are recorded at
  **branch location**, not customer residence — this inflates Maharashtra and Delhi, where lending is
  booked. Loan accounts use **place of sanction**. PhonePe uses the **user's registered state**.
  These are three different definitions of "where", merged into one panel.
- **PhonePe is one firm**, ~45–50% of UPI, with market share that varies by state. Cross-state levels
  are noisier than within-state growth. NPCI's total UPI series would fix this.
- **Usage is severely right-skewed after 0–1 normalisation** — 85% of observations below 0.20 — so
  β_access and β_usage were never on fully equivalent scales. This is a direct threat to the H1
  comparison itself, and it was left unfixed deliberately, to test the specification as written.
- **State-level, not person-level.** Nothing here can show that *individuals* hold unused accounts;
  that is the mechanism H1 describes, and this design cannot see it.

## 5. Scope

- **Physical panel stops at FY2023** (D8) — the loan-account series that counts banks consistently
  ends there. FY2024 was traded away for a clean bank universe.
- **Digital panel is 5 years**, one shorter than the others: PhonePe data begin in 2018, so FY2019 is
  the first complete financial year.
- **ATMs cannot go back past 2018**, which caps any lengthening of the panel while both physical
  regressors are retained.
- **No connectivity or account-usage-frequency component.** Dropping PMJDY (D3) was necessary — those
  accounts would have sat on both sides of the regression — but it left the physical measure with
  nothing digital in it, until PhonePe was added.

---

## What survives all of this

- **The physical null**, reported *as uninformative* rather than as evidence of no effect.
- **branches → Usage negative** (p≤0.020 across three specifications and two samples) — robust, and
  with no causal reading available: equally consistent with branches being *placed* where deposit
  growth is weak.
- **UPI → credit accounts positive** (+0.439), robust to dropping any single state (F14) and to the
  known data defects (F13) — but correlational.
- **UPI → deposit accounts ≈ 0**, which is the asymmetry the whole digital finding rests on.
