# Interpretation Guide

## Reading Single-Community Results

### The Outcome Badge

The large colored label (GREW / STABILIZED / DECLINED / COLLAPSED) shows the **dominant outcome** across all Monte Carlo paths. It is determined by majority vote. A community showing "STABILIZED" in 55% of paths with "GREW" in 30% and "DECLINED" in 15% is qualitatively different from one showing "STABILIZED" in 55% with "COLLAPSED" in 25%.

**Always read the full outcome distribution, not just the badge.**

### Survival Curve

S(t) falls from 1.0 toward 0 as cumulative hazard accumulates. Key values:
- S(30) > 0.9: low-risk community
- S(30) ∈ [0.5, 0.9]: moderate risk
- S(30) < 0.5: high risk — half of simulated paths have collapsed by year 30

The mean survival curve (green line) ± 10th–90th percentile bands shows the distribution across paths. Wide bands indicate high sensitivity to shock draws.

### Trajectory Bands

The 25th–75th percentile band (darker shading) shows the "typical" path. The 10th–90th band (lighter shading) shows the range of plausible outcomes. A community with a rising mean but wide spread is doing well on average but volatile — individual realizations vary a lot.

### M/T/R Components

Watching M, T, and R separately helps diagnose what is driving wealth dynamics:
- **R flat but M declining**: material shocks are the dominant factor
- **M stable but R declining**: family/religious time allocation is insufficient, R is eroding
- **T stable but W declining**: relational capital must be falling

## Worked Example 1: Dense Religious Community

Configuration: 300 residents, 180 sqft/resident, family time 30%, religion time 20%, secular/suburban comparison at 700 sqft/resident.

Dense religious community (DRC): R ≈ 0.78 (high spatial S from density, high family and religion)
Suburban secular (SSC): R ≈ 0.42 (low spatial S from spread, low family/religion weights)

Under moderate shocks, 30 years:
- DRC: ~65% stabilized, ~20% grew, ~12% declined, ~3% collapsed
- SSC: ~48% stabilized, ~15% grew, ~28% declined, ~9% collapsed

Note: at default parameters DRC outperforms SSC. But try severe shocks + global contagion: the advantage narrows because R-buffers are overwhelmed by material shocks.

## Worked Example 2: Society of 30 Mixed Communities

Default composition (25% each archetype), 30 years, moderate shocks:

The network structure means high-R communities can buffer low-R neighbors through R-contagion, while low-R communities can benefit from trade with wealthy neighbors even without high internal R.

Expected typical result: ~40-50% grew or stabilized, ~15-25% declined, ~5-15% collapsed. The Gini typically rises over 30 years as communities diverge.

## Society vs. Single-Community Comparison

Key differences in society mode:
1. **Contagion multiplies shocks** — a global shock hits all communities simultaneously, so the whole society may decline together
2. **Trade buffers shocks** — communities connected to wealthy neighbors recover faster
3. **R-contagion may homogenize** — strong R-contagion pulls all communities toward the mean

## Comparison Mode: Testing the Thesis

The comparison mode directly tests the hypothesis that high-R communities outperform low-R communities at the societal level.

**Setup for a clean test:**
- Society A: 70% high-R archetypes (strong nuclear + extended kin)
- Society B: 70% low-R archetypes (secular suburban + mixed)
- Same horizon, same shock seed
- All other parameters identical

**What to look for:**
- If Society A has lower collapse rate AND higher growth rate: strong evidence in favor at default parameters
- If Society A has lower collapse rate but similar growth rate: mixed — R protects against downside but doesn't generate upside
- If results are similar: the network effects (trade, migration) may dominate composition effects
- If Society B outperforms: this is information, not a modeling error. Document the parameter regime and investigate why.

**The simulation does not guarantee a result.** The user's thesis may be supported, weakly supported, not supported, or refuted depending on parameter choices. That is the point.

## Honesty Notes

- N Monte Carlo paths = N independent shock histories. The outcome distribution reflects genuine uncertainty under the model, not repeated measurements of the same thing.
- "Grew" in 30% of paths does not mean the community will grow — it means 30% of plausible shock sequences lead to growth under this model.
- The model has no feedback mechanism between community composition and shock frequency. Real societies may face fewer or more shocks depending on their structure — this simulation does not model that.
