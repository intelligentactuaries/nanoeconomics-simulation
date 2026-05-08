# Methodology

## Single-Community Wealth Dynamics

### Wealth Function

The core quantity is the **Cobb-Douglas wealth function**:

$$W(t) = M(t)^{\alpha_M} \cdot T(t)^{\alpha_T} \cdot R(t)^{\alpha_R}$$

with $\alpha_M + \alpha_T + \alpha_R = 1$. Default values: $\alpha_M = 0.4$, $\alpha_T = 0.3$, $\alpha_R = 0.3$.

The choice of Cobb-Douglas (vs. additive) is deliberate: **zero in any dimension collapses wealth to zero**, modeling the empirical observation that purely material communities without relational structure, or communities with no productive time, cannot sustain themselves.

### Material Capital M(t)

M grows through productive time allocation and decays through maintenance:

$$\frac{dM}{dt} = r_M \cdot t_{\text{prod}} \cdot M - d_M \cdot M + \text{trade boost}$$

- $r_M = 0.04$ (4% annual growth from productive time)
- $d_M = 0.01$ (1% annual maintenance drain)
- Trade boost from neighboring communities (see Network Model)

Shocks can reduce M instantaneously.

### Time Allocation T(t)

Time is allocated across five activities:

| Activity | Default fraction |
|----------|----------------|
| Production | 0.40 |
| Family | 0.25 |
| Religion/community | 0.15 |
| Spatial maintenance | 0.10 |
| Leisure | 0.10 |

Allocations sum to 1 (enforced by normalization). The T component used in W is:

$$T_{\text{eff}} = t_{\text{prod}} + 0.3 \cdot t_{\text{leisure}}$$

capturing that leisure partially restores productive capacity.

### Relational Capital R(t)

$$R(t) = \frac{w_F \cdot F(t) + w_{Rel} \cdot \text{Rel}(t) + w_S \cdot S(d)}{w_F + w_{Rel} + w_S}$$

**Family strength F(t)** — in [0, 1]:
- Increases when family time fraction ≥ 10%: $\Delta F = r_F \cdot t_{\text{fam}}$
- Decays otherwise: $\Delta F = -d_F$
- Default $r_F = 0.10$, $d_F = 0.05$

**Religious participation Rel(t)** — in [0, 1]:
- Increases with religious time allocation
- Specifically absorbs meaning-crisis shocks: high Rel reduces the impact of meaning-crisis events
- Default $r_{Rel} = 0.08$, $d_{Rel} = 0.03$

**Spatial density component S(d)** — in [0, 1]:
A logistic-bell function of square footage per resident:

$$S(d) = \text{logistic}(k(d - d_{\text{low}})) \cdot (1 - \text{logistic}(k(d - d_{\text{high}})))$$

with $d_{\text{low}} = 100$, $d_{\text{high}} = 400$, $k = 0.045$, normalized so peak = 1.0 at $d \approx 250$ sqft/resident.

This curve encodes the hypothesis of Jacobs (1961) and Alexander (1977) that walkable, moderately dense communities have the richest informal interaction. It peaks at approximately 250 sqft/resident and falls off both for very dense (overcrowded) and very sparse (suburban) configurations.

### Hazard and Survival

The community faces a continuous hazard of collapse:

$$h(t) = h_0 \cdot \exp\left(-\beta_W \cdot \log\frac{W(t)}{W_0}\right)$$

- $h_0 = 0.02$: baseline annual hazard (2% annual risk at $W = W_0$)
- $\beta_W = 2.0$: wealth-protection coefficient
- $W_0$: initial wealth (community-specific)

When $W > W_0$, hazard falls below $h_0$. When $W < W_0$, hazard exceeds $h_0$. The exponential form ensures hazard remains positive.

Cumulative survival:

$$S(T) = \exp\left(-\int_0^T h(t)\, dt\right) \approx \exp\left(-\sum_t h(t) \cdot \Delta t\right)$$

### Outcome Classification

At simulation end, each community (or path) is classified:

| Outcome | Condition |
|---------|-----------|
| **Collapsed** | $W < \tau_c \cdot W_0$ for ≥ $N_{\text{rec}}$ consecutive periods |
| **Grew** | $W(T) > W_0 \cdot (1 + \tau_g)$ |
| **Stabilized** | $|W(T) - W_0| / W_0 \leq \tau_s$ |
| **Declined** | None of the above |

Default thresholds: $\tau_c = 0.30$, $N_{\text{rec}} = 5$, $\tau_g = 0.20$, $\tau_s = 0.10$.

### Stochastic Shocks

Each year, shocks arrive as a Poisson process with mean rate $\lambda_{\text{annual}}$. Each shock has:

- **Topology**: idiosyncratic (40%), local (35%), regional (20%), global (5%)
- **Target**: material (35%), time (20%), family (15%), religion (10%), meaning-crisis (10%), combined (10%)
- **Severity**: Normal($\mu_s$, $\sigma_s$), clipped to (0.01, 0.90)

A **cooldown** prevents the same community from being shocked again within 0.5 years (prevents unphysical oscillation cascades).

---

## Multi-Community Network Model

### Society Structure

A society is a set of $N$ communities at 2D positions on a continuous plane, connected by a k-nearest-neighbor graph (default $k = 4$).

### 1. Trade — Gravity Model

$$\text{Trade}_{ij}(t) = \kappa \cdot \frac{W_i(t) \cdot W_j(t)}{d_{ij}^2 + \varepsilon}$$

This redistributes material capital: both communities $i$ and $j$ gain $\text{Trade}_{ij}(t) \cdot \Delta t$ added to their M. Trade is **positive-sum** — both benefit from exchange.

Default: $\kappa = 0.002$, $\varepsilon = 1.0$ (prevents divergence at zero distance). A trade strength multiplier lets users scale this from 0 (autarky) to 2.0 (high integration).

Reference: Tinbergen (1962), "Shaping the World Economy"; Frankel & Romer (1999).

### 2. Migration — Event-Driven

When community $i$'s wealth falls below $\tau_m \cdot W_0^{(i)}$ (default $\tau_m = 0.60$, higher than the collapse threshold to model early exit before collapse):

1. Identify neighbors with higher current wealth
2. Select the highest-wealth neighbor $j$
3. Transfer $\mu \cdot M_i$ from $i$ to $j$ (with friction: $j$ receives $0.8 \times$ what $i$ loses)
4. Population conservation is maintained

$\mu = 0.02 \cdot (1 - f_{\text{friction}})$, where friction models integration costs. Migration may temporarily lower $j$'s R if integration friction is modeled (currently via M adjustment only; R friction is a planned extension).

### 3. Contagion — Spatially Extended Shocks

Society-level shocks use the same four topology types as single-community mode, but now `ShockGenerator` receives the full neighbor list and applies shocks to the correct subset of communities. Network-distance weighting is used for regional shocks.

### 4. R-Contagion

Each community's relational capital is slightly influenced by its neighbors:

$$\Delta R_i^{\text{contagion}} = \alpha_c \cdot \left(\bar{R}_{\text{neighbors},i} - R_i\right) \cdot \Delta t \cdot 0.1$$

High-R neighbors lift low-R communities; low-R neighbors pull down high-R communities. Strength $\alpha_c \in [0, 1]$ (default 0.3). The 0.1 dampening factor keeps the effect modest — it supplements, not overrides, the community's own internal dynamics.

Reference: Putnam (2000), *Bowling Alone*; Henrich (2020), *The WEIRDest People in the World*.

### Society Metrics

At each time step:
- **Total societal wealth**: $\sum_i W_i \cdot \text{pop}_i$
- **Gini coefficient**: standard formula over $\{W_i\}$
- **Migration flux**: total M transferred in the period
- **Outcome distribution**: fraction of communities in each category

---

## Simulation Architecture

```
app.py
  └── run_single_community()  →  SingleCommunityRunResult
        └── run_single_path() per path
              ├── initialize_community()
              ├── step_community() × horizon
              └── survival_curve()
  └── run_society_with_frames()  →  SocietyAnimationResult
        └── Society.step() × horizon
              ├── ShockGenerator.generate_shocks()
              ├── Trade gravity model
              ├── R-contagion
              ├── step_community() × n_communities
              └── Migration
```

---

## Observed Behavior at Default Parameters

The following results were produced by running the simulation at default parameter values
(moderate shock environment, 30-year horizon, 200 Monte Carlo paths per single-community
run, 30-community society, 25% each archetype).

**Single-community results (representative runs):**

| Configuration | Grew | Stabilized | Declined | Collapsed |
|---------------|------|------------|----------|-----------|
| High-R (strong nuclear + religious + dense, ~200 sqft/resident) | 11.6% | 52.0% | 36.4% | 0% |
| Low-R (independent secular + suburban, ~900 sqft/resident) | 60.8% | 17.6% | 21.6% | 0% |

High-R communities stabilize at high rates; low-R communities grow at high rates.
Collapse rates are near zero for both under moderate shocks.

**Society-level results (30-community mixed society):**

- High-R community types: lower collapse and decline rates, lower mean wealth
- Low-R community types: higher mean wealth, higher growth rates
- Final Gini: typically lower in high-R-dominated societies
- Network trade buffers both types against severe localized shocks

## Interpretation

The observed pattern is a **risk-return tradeoff**, not evidence that one configuration
dominates the other.

Relational capital functions as *insurance*: it dampens downside risk (stabilization
instead of decline; decline instead of collapse) at the cost of upside (lower mean
wealth growth, because time allocated to family, religion, and community maintenance
is time not allocated to production).

This is mathematically consistent with the Cobb-Douglas structure: high R increases the
R exponent's contribution but reduces the T-to-production allocation, creating a direct
tradeoff under the model's assumptions. It is also consistent with empirically observed
community resilience patterns: close-knit communities often survive crises better but
accumulate material wealth more slowly than production-focused peers.

The appropriate question is not "which is better" but "better for what objective under
what shock regime." High-R communities optimize for resilience under stress; low-R
communities optimize for wealth accumulation under stability.

## Open Empirical Questions

The simulation raises several questions that real-world data could address:

1. **Shock-severity crossover:** At what shock severity does high-R begin to dominate
   on *all* dimensions (both lower collapse and higher mean wealth)? The simulation
   shows this may occur at severe shock levels — empirical investigation of historical
   communities under extreme stress could test this.

2. **Parameter calibration:** The spatial density, time allocation, and relational
   growth parameters are stylized. How do the qualitative findings change under
   empirically calibrated values from specific communities (e.g., Amish, kibbutzim,
   urban neighborhoods, suburban developments)?

3. **Historical community data:** What longitudinal data exists on community-level
   wealth and survival rates disaggregated by family structure, religious participation,
   and density? The simulation's framework suggests specific variables to measure.

4. **Network composition effects:** Does the tradeoff persist in high-R-majority
   networks, or do network spillovers eventually allow high-R communities to achieve
   both resilience and growth? The simulation allows this to be explored directly.

---

## Limitations and Scope

1. **Theoretical model** — parameters are illustrative, not calibrated from empirical data
2. **Continuous time approximation** — discrete annual steps approximate continuous dynamics
3. **No spatial heterogeneity within communities** — each community is a representative agent
4. **Migration is simplified** — real migration involves demographic shifts, skill mismatch, housing constraints not captured here
5. **Trade is symmetric** — the gravity model here doesn't capture terms-of-trade effects or asymmetric specialization
6. **R-contagion is linear** — non-linear threshold effects (e.g., social tipping points) are not modeled
