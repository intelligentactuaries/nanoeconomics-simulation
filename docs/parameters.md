# Parameter Reference

All parameters are user-adjustable via the Gradio UI or programmatically through Pydantic config objects.

## Wealth Function Parameters

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| `alpha_m` | 0.4 | (0, 1) | Elasticity of wealth w.r.t. material capital |
| `alpha_t` | 0.3 | (0, 1) | Elasticity of wealth w.r.t. time (renormalized to sum to 1) |
| `alpha_r` | 0.3 | (0, 1) | Elasticity of wealth w.r.t. relational capital |

Calibration note: equal-weight Cobb-Douglas (1/3, 1/3, 1/3) is a natural prior. The 0.4/0.3/0.3 split slightly privileges material capital, reflecting that material shocks dominate in short-horizon simulations. Users should test sensitivity to these values.

## Relational Capital Weights

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| `w_family` | 0.4 | [0, 1] | Weight on family bond strength |
| `w_religion` | 0.3 | [0, 1] | Weight on religious participation |
| `w_spatial` | 0.3 | [0, 1] | Weight on spatial-density component |

Calibration note: Putnam (2000) finds family and religious networks as primary social capital sources; spatial density effects follow Jacobs (1961). The 0.4/0.3/0.3 split is defensible but not uniquely correct.

## Relational Dynamics

| Parameter | Default | Description |
|-----------|---------|-------------|
| `family_growth_rate` | 0.10 | Annual F increase per unit family time fraction |
| `family_decay_rate` | 0.05 | Annual F decay when family time < 10% |
| `religion_growth_rate` | 0.08 | Annual Rel increase per unit religion time fraction |
| `religion_decay_rate` | 0.03 | Annual Rel decay without participation |

## Spatial Density — S(d)

| Parameter | Value | Description |
|-----------|-------|-------------|
| `SPATIAL_PEAK_SQFT` | 250 | sqft/resident at which S peaks |
| `x_low` | 100 | Lower boundary of logistic bell |
| `x_high` | 400 | Upper boundary of logistic bell |
| `k` | 0.045 | Logistic steepness |

The logistic bell peaks at ~250 sqft/resident. This corresponds to a density of approximately 17 residents per 1000 sqft, or roughly 4-5 story walkable urban housing. The shape is consistent with Jacobs (1961) "eyes on the street" and Alexander's (1977) Pattern 37 "House Cluster."

## Material Capital Dynamics

| Parameter | Default | Description |
|-----------|---------|-------------|
| `m_production_rate` | 0.04 | Annual M growth from production time |
| `m_maintenance_drain` | 0.01 | Annual M drain for spatial/infrastructure maintenance |

Net growth at max production (t_prod = 0.4): 0.04 × 0.4 = 1.6% annual growth, minus 1% drain → ~0.6% net. This models modest material accumulation under normal conditions.

## Hazard Parameters

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| `h0` | 0.02 | [0.001, 0.1] | Baseline annual hazard at W = W0 |
| `beta_w` | 2.0 | [0.5, 5.0] | Wealth-protection coefficient |

At h0 = 0.02 and constant W = W0: 10-year survival ≈ e^(-0.2) ≈ 82%. The beta_w = 2.0 means a 10% wealth decline increases hazard by ~22%, while a 10% wealth gain decreases it by ~18%.

## Shock Environments

| Preset | Annual probability | Mean severity | σ severity |
|--------|-------------------|---------------|------------|
| mild | 0.10 | 0.08 | 0.04 |
| moderate | 0.25 | 0.15 | 0.08 |
| severe | 0.45 | 0.25 | 0.12 |

Shock topology defaults (moderate):
- Idiosyncratic: 40%
- Local: 35%
- Regional: 20%
- Global: 5%

## Outcome Classification Thresholds

| Parameter | Default | Description |
|-----------|---------|-------------|
| `collapse_threshold` | 0.30 | W/W0 below which community is "at risk" |
| `recovery_window` | 5 | Consecutive years at risk → declared collapsed |
| `growth_threshold` | 0.20 | Fractional gain above W0 to classify as grew |
| `stability_band` | 0.10 | ±10% band around W0 for stabilized |

## Society Network Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `spatial_spread` | 50 | Side length of 2D community placement square |
| `network_k` | 4 | k-nearest neighbors connectivity |
| `trade_strength` | 1.0 | Multiplier on gravity trade (0 = autarky) |
| `migration_friction` | 0.3 | Migration loss fraction (0 = lossless, 1 = no migration) |
| `migration_threshold` | 0.6 | W/W0 below which migration is triggered |
| `r_contagion_strength` | 0.3 | Strength of neighbor R influence |

## Sensitivity Analysis Recommendations

1. **Alpha weights**: Test equal-weight (1/3, 1/3, 1/3) vs. material-dominant (0.6, 0.2, 0.2) vs. relational-dominant (0.2, 0.2, 0.6)
2. **Shock severity**: Compare mild vs. severe to bound the effect of the external environment
3. **R-contagion**: Set to 0 (isolated communities) vs. 0.5 (strong network effects)
4. **Trade strength**: Set to 0 (autarky) vs. 2.0 (high integration)
5. **sqft/resident**: 150 (dense) vs. 1000 (suburban) to test the spatial capital hypothesis
