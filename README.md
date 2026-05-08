---
title: Nanoeconomics Community Survival Simulation
emoji: 🌍
colorFrom: yellow
colorTo: red
sdk: streamlit
sdk_version: 1.42.0
app_file: app.py
pinned: false
license: apache-2.0
short_description: Community wealth dynamics under W(M,T,R) framework
---

<img width="1166" height="480" alt="GoogleLogoGIF-LARGE" src="https://github.com/user-attachments/assets/26d42ffe-d734-4f1e-ab96-e2c59a0f73d9" />


# Nanoeconomics: Community Wealth Survival Simulation

An interactive simulation exploring the risk-return tradeoffs in community wealth
dynamics under the W(M, T, R) framework from Denewade (2025) "Nanoeconomics:
Compounding Cooperation for Community Wealth."

## Try It Live

🚀 **[Run the simulation on HuggingFace Spaces](https://huggingface.co/spaces/intelligentactuaries/nanoeconomics-simulation)**

No installation required. Configure community parameters, run simulations,
explore the risk-return tradeoff interactively in your browser.

## What This Simulation Demonstrates

The simulation operationalizes the Nanoeconomics framework as a stochastic
community-level survival model. Wealth W is modeled as a Cobb-Douglas function
of money M, time T, and relational capital R, where R = (family structure,
religious affiliation, spatial density). Communities evolve over time under
stochastic economic, health, and social shocks, with optional network
interactions when multiple communities form a society.

The simulation produces a *risk-return tradeoff*:

- Communities with **high relational capital** (strong nuclear family + religious
  community + dense spatial proximity ~200 sqft/resident) show **lower collapse
  and decline rates** under stress, but **lower mean wealth growth** because
  more time is allocated to relationship maintenance rather than production.

- Communities with **low relational capital** (suburban density ~900 sqft/resident,
  secular, production-focused time allocation) show **higher mean wealth growth**
  but **greater downside variance** when shocks hit.

At society scale (multiple communities forming a network with trade, migration,
and shock contagion), high-R societies show **fewer community-level declines**
but **lower aggregate wealth** than low-R societies. Network effects reduce
inequality (lower Gini) in high-R societies but do not mechanically produce
more total wealth.

This is consistent with decision theory: relational capital functions as
insurance — it dampens downside risk at the cost of upside.

## What This Simulation Does Not Demonstrate

- This is not a claim about real-world societies. The simulation explores the
  implications of the framework's assumptions; whether real communities behave
  this way under specific historical conditions is an empirical question
  requiring real-world data, not simulation alone.

- Parameter values are stylized. The conclusion may shift under different
  shock regimes — preliminary indications suggest high-R may dominate more
  comprehensively under severe-shock environments (a question the simulation
  lets users explore directly).

- The simulation makes no normative claim about which configuration is
  "better" — only what each configuration is *good for*. High-R communities
  optimize for stability and resilience; low-R communities optimize for
  growth. Both are coherent strategies under different objective functions
  and risk tolerances.

## Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open http://localhost:8501 in your browser.

## Installation (Development)

```bash
uv sync
uv run streamlit run app.py
```

## User Interface

The app uses [Streamlit](https://streamlit.io). All adjustment widgets
(sliders, switches, run buttons) live in the **left sidebar**, organized by
mode. The main view shows three tabs as a segmented control at the top:

1. **Single Community** — explore a single community's wealth trajectory,
   survival curve, M/T/R component dynamics, and outcome distribution.
2. **Society Mode** — animate a network of 5–100 communities; watch shocks
   propagate via local/regional/global contagion, R-contagion among
   neighbors, gravity-model trade, and migration.
3. **Compare Two Societies** — run two configurations side-by-side under
   the same shock seed to see how composition and network structure shape
   collective outcomes.

## The Wealth Function

$$W(t) = M(t)^{\alpha_M} \cdot T(t)^{\alpha_T} \cdot R(t)^{\alpha_R}$$

where **M** = material/monetary capital, **T** = time allocation, and
**R** = relational capital parameterized by family structure, religious
participation, and community spatial density.

**Relational capital:**

$$R(t) = w_F \cdot F(t) + w_{Rel} \cdot \text{Rel}(t) + w_S \cdot S(t)$$

- **F(t)** — family bond strength, increases with family time allocation, decays without it
- **Rel(t)** — religious community participation, specifically buffers meaning-crisis shocks
- **S(t)** — spatial-density relational capital; logistic peak at ~250 sqft/resident

## Simulation Modes

1. **Single Community** — configure family structure, religious participation, spatial density,
   time allocation, and observe how a community evolves over 30–100 years under stochastic shocks
2. **Society Network** — simulate 5–100 communities connected by trade, migration, and
   social contagion; observe how composition and network structure shape collective outcomes
3. **Comparative Analysis** — run two societies side-by-side with identical shock seeds
   to test your own hypotheses

## Community Outcome Categories

| Status | Condition |
|--------|-----------|
| **Grew** | W(T) > W(0) × 1.20 |
| **Stabilized** | \|W(T) − W(0)\| / W(0) ≤ 0.10 |
| **Declined** | W fell but did not collapse |
| **Collapsed** | W < 0.30 · W(0) for longer than recovery window |

All thresholds are user-adjustable.

## Walkthrough Notebook

A 12-cell Jupyter walkthrough is provided at
[`notebooks/walkthrough.ipynb`](notebooks/walkthrough.ipynb).
It renders directly on GitHub and on the HuggingFace Space's Files tab.

Contents:
- The $W(M, T, R)$ Cobb-Douglas formulation and hazard / survival math
- A high-relational-capital community Monte Carlo run (300 paths, 30 years)
- High-R vs. low-R comparison under the same shock seed (pandas summary table)
- A 30-community society simulation (per-community outcome table + total
  wealth / Gini / migration trajectories)
- Risk-return tradeoff interpretation

Three matplotlib plots, two pandas tables, math-rich markdown throughout.

## Methodology

See [docs/methodology.md](docs/methodology.md) for the full theoretical setup,
parameter calibrations, and observed simulation results.

See [docs/interpretation.md](docs/interpretation.md) for worked examples demonstrating
the risk-return tradeoff across configurations.

## Research

This work is produced by the **Intelligent Actuaries Research Lab**.
For questions, collaborations, or feedback, contact
[research@intelligentactuaries.com](mailto:research@intelligentactuaries.com).

## Reference

Denewade, A. (2025). *Nanoeconomics: Compounding Cooperation for Community Wealth.*
ResearchGate preprint.

## Citation

```bibtex
@software{denewade2025nanoeconomics,
  author = {Denewade, Ali},
  title = {Nanoeconomics Survival Simulation},
  year = {2025},
  license = {Apache-2.0},
  url = {https://github.com/intelligentactuaries/nanoeconomics-simulation}
}
```

## License

Apache 2.0 — see [LICENSE](LICENSE).
