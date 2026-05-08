# Nanoeconomics Survival Simulation

An interactive simulation demonstrating the **W(M, T, R) wealth dynamics** from the Nanoeconomics framework (Denewade, 2025). Explores how communities of varying configurations survive, grow, or collapse — individually and as interconnected societies.

## Overview

This simulation operates at two scales:

1. **Single Community** — configure family structure, religious participation, spatial density, time allocation, and observe how a community of 100–5,000 residents evolves over time under stochastic shocks
2. **Society Network** — simulate 5–100 communities connected by trade, migration, and social contagion; observe how network structure and community composition shape collective outcomes
3. **Comparative Analysis** — run two societies side-by-side with identical shock seeds to test your own hypotheses

The wealth function is:

$$W(t) = M(t)^{\alpha_M} \cdot T(t)^{\alpha_T} \cdot R(t)^{\alpha_R}$$

where **M** = material/monetary capital, **T** = time allocation, and **R** = relational capital parameterized by family structure, religious participation, and community spatial density.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the Gradio app
python app.py
```

Then open http://localhost:7860 in your browser.

## Installation (Development)

```bash
uv sync
uv run python app.py
```

## Theoretical Foundation

See [docs/methodology.md](docs/methodology.md) for the full theoretical setup.

**Relational capital:**

$$R(t) = w_F \cdot F(t) + w_{Rel} \cdot \text{Rel}(t) + w_S \cdot S(t)$$

- **F(t)** — family bond strength, increases with family time allocation, decays without it
- **Rel(t)** — religious community participation, specifically buffers meaning-crisis shocks
- **S(t)** — spatial-density relational capital; logistic peak at ~250 sqft/resident (Jacobs 1961, Alexander 1977)

**Hazard function:**

$$h(t) = h_0 \cdot \exp\left(-\beta_W \cdot \frac{\log W(t)}{W_0}\right)$$

## Community Outcome Categories

| Status | Condition |
|--------|-----------|
| **Grew** | W(T) > W(0) × 1.20 |
| **Stabilized** | \|W(T) − W(0)\| / W(0) ≤ 0.10 |
| **Declined** | W fell but did not collapse |
| **Collapsed** | W < 0.30 · W(0) for longer than recovery window |

All thresholds are user-adjustable.

## Honesty Constraints

This simulation is a **theoretical demonstration**, not an empirical claim. All parameters are user-adjustable. The simulation reports what the math produces — if a configuration the user expects to perform well performs poorly at default parameters, that is documented honestly.

> "The agent reports what happened; the user interprets."

## Network Model

Multi-community societies use:
- **Trade** (gravity model, distance-squared decay)
- **Migration** (triggered below threshold, mass conserved)
- **Contagion** (local / regional / global / idiosyncratic shock topologies)
- **R-contagion** (neighbor relational capital influences)

See [docs/network-dynamics.md](docs/network-dynamics.md) for citations and derivations.

## Citation

If you use this simulation in research, please cite:

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

## HuggingFace Space

Deployment: `intelligentactuaries/nanoeconomics-simulation` (link available after deployment session)
