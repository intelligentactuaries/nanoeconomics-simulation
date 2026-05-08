# Interpretation Guide

## Reading Single-Community Results

### The Outcome Badge

The large colored label (GREW / STABILIZED / DECLINED / COLLAPSED) shows the **dominant outcome**
across all Monte Carlo paths. It is determined by majority vote. A community showing "STABILIZED"
in 55% of paths with "GREW" in 30% and "DECLINED" in 15% is qualitatively different from one
showing "STABILIZED" in 55% with "COLLAPSED" in 25%.

**Always read the full outcome distribution, not just the badge.**

### Survival Curve

S(t) falls from 1.0 toward 0 as cumulative hazard accumulates. Key values:
- S(30) > 0.9: low-risk community
- S(30) ∈ [0.5, 0.9]: moderate risk
- S(30) < 0.5: high risk — half of simulated paths have collapsed by year 30

The mean survival curve (green line) ± 10th–90th percentile bands shows the distribution
across paths. Wide bands indicate high sensitivity to shock draws.

### Trajectory Bands

The 25th–75th percentile band (darker shading) shows the "typical" path. The 10th–90th
band (lighter shading) shows the range of plausible outcomes. A community with a rising
mean but wide spread is doing well on average but volatile — individual realizations vary a lot.

### M/T/R Components

Watching M, T, and R separately helps diagnose what is driving wealth dynamics:
- **R flat but M declining**: material shocks are the dominant factor
- **M stable but R declining**: family/religious time allocation is insufficient, R is eroding
- **T stable but W declining**: relational capital must be falling

---

## Walkthrough 1: High-R Community Under Moderate Shocks — Stabilization Profile

**Configuration:** 300 residents, 180 sqft/resident, family time 30%, religion time 20%, production time 35%

This configuration produces high relational capital (R ≈ 0.78): dense spatial layout peaks the S
component, and substantial family and religion time allocation sustains F and Rel. The time budget
shift — 35% production rather than 40% — means T-effective is slightly lower.

**Expected result under moderate shocks, 30 years:**
- Dominant outcome: STABILIZED (~50–55% of paths)
- Secondary outcome: DECLINED (~30–35%), GREW (~12–18%), COLLAPSED (<5%)
- Survival S(30): typically > 0.85
- Trajectory: mean W stays near W₀, with narrow bands — low variance across paths

**What to notice:** High R buffers the community against the downside. Collapse rates are very low.
But mean wealth does not substantially exceed W₀ because productive time is reduced. This community
is *resilient*, not *growing*.

**Diagnostic check:** Watch the R component — it should stay elevated. Watch M — it may drift
slightly downward under production-focused shocks but recover via the community's resilience buffer.

---

## Walkthrough 2: Low-R Community Under Moderate Shocks — Growth with Variance

**Configuration:** 500 residents, 900 sqft/resident, family time 15%, religion time 5%, production time 50%

This configuration produces low relational capital (R ≈ 0.38): suburban density puts S on the
low-density tail of the logistic curve, and minimal family/religion time means F and Rel drift
downward over time. But productive time allocation is high, which drives M growth.

**Expected result under moderate shocks, 30 years:**
- Dominant outcome: GREW (~55–65% of paths)
- Secondary outcome: STABILIZED (~15–20%), DECLINED (~15–25%), COLLAPSED (<5% at moderate shocks)
- Survival S(30): typically 0.80–0.90
- Trajectory: mean W rises above W₀, but wide 10–90th percentile bands — high variance across paths

**What to notice:** High production time drives strong mean wealth growth. But the path distribution
is wide — some shock sequences produce significant decline. This community is *growing*, but more
exposed to downside when shocks cluster.

**Diagnostic check:** Watch R — it will gradually erode as family and religion allocation is low.
This erosion is slow but accumulates; over 50+ year horizons the gap with high-R communities narrows
as low-R communities eventually see R approach its lower bound.

---

## Walkthrough 3: Society Comparison — Network-Level Expression of the Tradeoff

**Setup (Compare Two Societies mode):**
- Society A: 70% high-R archetypes (strong nuclear + extended kin), 30% mixed
- Society B: 70% low-R archetypes (independent secular + mixed), 30% extended kin
- Same horizon, same shock seed, same network parameters

**Expected result under moderate shocks, 30 years:**
- Society A: lower collapse rate, lower total wealth, lower Gini
- Society B: higher total wealth, higher Gini, higher collapse rate among low-R communities

**What to notice:** The network structure adds layers. Trade allows wealthy low-R communities to
partially subsidize declining high-R neighbors, and R-contagion pulls both types toward the
societal mean. The result is that the wealth difference may be smaller than single-community
comparisons suggest — network integration partially offsets compositional differences.

**Key metric to watch:** Final Gini. High-R-dominated societies typically show lower Gini because
R-contagion homogenizes relational capital and trade redistributes material capital. This is
a testable implication: denser relational networks should exhibit lower wealth inequality, not
necessarily higher mean wealth.

---

## Walkthrough 4: Severe Shocks — User-Explored Regime

**Setup:** Run the same High-R vs. Low-R single-community comparison from Walkthroughs 1 and 2,
but set shock intensity to "severe."

This walkthrough is intentionally left for users to run and observe. The deployment document
notes that preliminary results suggest the risk-return tradeoff may narrow or invert under
severe shocks — high-R may show lower collapse *and* competitive mean wealth when shocks are
frequent and severe.

**What to look for:**
- Does the High-R collapse rate remain near zero, or does it rise under severe shocks?
- Does the Low-R collapse rate rise faster than High-R?
- At what shock intensity does the Grew/Collapsed distribution suggest High-R dominates
  on both dimensions simultaneously?

**Why this matters:** If the tradeoff inverts at severe shocks, the normative conclusion shifts:
relational capital functions as insurance that pays out precisely when needed most. The simulation
lets users probe this directly. The answer is parameter-dependent and the user should report what
they observe, not what any particular theory predicts.

---

## Comparison Mode: Exploring the Hypothesis

The comparison mode directly tests whether high-R communities outperform low-R communities at
the societal level under specific parameter assumptions.

**Setup for a clean test:**
- Society A: 70% high-R archetypes (strong nuclear + extended kin)
- Society B: 70% low-R archetypes (secular suburban + mixed)
- Same horizon, same shock seed
- All other parameters identical

**What to look for:**
- If Society A has lower collapse rate but similar or lower mean wealth: the risk-return tradeoff
  is operating as expected
- If Society A has lower collapse rate AND higher mean wealth: high-R dominates in this regime —
  note the shock severity and parameters
- If results are similar: network effects (trade, migration) may dominate composition effects —
  the network is smoothing out compositional differences
- If Society B outperforms on all metrics: this is information, not a modeling error. Document
  the parameter regime and investigate why

**The simulation does not guarantee a result.** The user's hypothesis may be supported, weakly
supported, not supported, or refuted depending on parameter choices. That is the point.

---

## Honesty Notes

- N Monte Carlo paths = N independent shock histories. The outcome distribution reflects genuine
  uncertainty under the model, not repeated measurements of the same thing.
- "Grew" in 30% of paths does not mean the community will grow — it means 30% of plausible
  shock sequences lead to growth under this model.
- The model has no feedback mechanism between community composition and shock frequency. Real
  societies may face fewer or more shocks depending on their structure — this simulation does not
  model that.
- Default parameters are calibrated to produce *illustrative* behavior, not to prove a point.
  The risk-return tradeoff emerges from the model structure itself, not from hand-tuned parameters.
