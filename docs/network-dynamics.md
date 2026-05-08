# Network Dynamics — References and Derivations

## Trade: Gravity Model

The trade flow between communities $i$ and $j$ follows a gravity specification:

$$\text{Trade}_{ij}(t) = \kappa \cdot \frac{W_i(t) \cdot W_j(t)}{d_{ij}^2 + \varepsilon}$$

**Origin:** Tinbergen (1962) proposed the gravity model for international trade, observing that trade flows are proportional to the product of national incomes and inversely proportional to distance squared. The specification has since accumulated strong empirical support.

References:
- Tinbergen, J. (1962). *Shaping the World Economy*. New York: Twentieth Century Fund.
- Frankel, J. A., & Romer, D. (1999). Does trade cause growth? *American Economic Review*, 89(3), 379–399.
- Anderson, J. E., & van Wincoop, E. (2003). Gravity with gravitas. *American Economic Review*, 93(1), 170–192.

**In this model:** $\kappa = 0.002$ is calibrated so that trade provides a modest 0.5–1.5% annual M boost for well-connected communities. The denominator's $\varepsilon = 1$ prevents divergence for co-located communities.

Trade is **positive-sum**: both communities gain. This models comparative advantage without requiring explicit specialization.

## Migration: Event-Driven Threshold Model

Migration is triggered when a community's wealth falls below $\tau_m \cdot W_0$ (default: 60% of initial wealth). A fraction $\mu$ of material capital migrates to the nearest higher-wealth neighbor, with friction.

**Theoretical basis:** The threshold model is consistent with empirical migration literature showing that migration is triggered by acute deterioration rather than continuous optimization. Harris & Todaro (1970) model rural-urban migration as triggered by wage differentials; we use wealth differentials.

References:
- Harris, J. R., & Todaro, M. P. (1970). Migration, unemployment and development. *American Economic Review*, 60(1), 126–142.
- Massey, D. S., et al. (1993). Theories of international migration. *Population and Development Review*, 19(3), 431–466.

**Conservation:** Total M across the society does not increase from migration alone. The sender loses more than the receiver gains (friction), modeling transaction costs, skill mismatch, and housing adjustment.

## Contagion: Spatially Extended Shocks

The four shock topologies model empirical observations about how crises spread:

- **Idiosyncratic**: firm-specific or local-government-specific shocks (e.g., factory closure, local drought)
- **Local**: spatially correlated shocks affecting neighbors (e.g., regional flood, supply chain disruption)
- **Regional**: sector-wide or region-wide shocks (e.g., commodity price collapse, regional recession)
- **Global**: systemic shocks affecting all communities (e.g., pandemic, global financial crisis)

References:
- Acemoglu, D., Carvalho, V. M., Ozdaglar, A., & Tahbaz-Salehi, A. (2012). The network origins of aggregate fluctuations. *Econometrica*, 80(5), 1977–2016.
- Gabaix, X. (2011). The granular origins of aggregate fluctuations. *Econometrica*, 79(3), 733–772.

## R-Contagion: Social Capital Diffusion

The relational capital contagion mechanism models social learning and behavioral diffusion:

$$\Delta R_i^{\text{contagion}} = \alpha_c \cdot (\bar{R}_{\text{neighbors},i} - R_i) \cdot \Delta t$$

Communities with high-R neighbors gradually adopt higher-R behaviors (family formation, religious practice, community investment). Communities with low-R neighbors face downward pressure.

**Theoretical basis:**

1. **Behavioral diffusion** — Bandura (1977) and subsequent research shows that behaviors spread through observation and social norms. Dense social networks accelerate diffusion.

2. **Social capital as public good** — Putnam (2000) documents that social capital (trust, civic participation) is correlated across geographic communities. High-trust regions sustain adjacent communities through information sharing and institutional quality.

3. **Cooperation contagion** — Henrich (2020) describes how prosocial norms (including religious institutions) spread through cultural evolution, with adjacent communities adopting norms over multiple generations.

4. **Network effects on norms** — Bramoullé, Galeotti & Rogers (2016) formally model how networks shape the adoption of norms and behaviors, showing that connectivity determines the equilibrium distribution of behaviors.

References:
- Putnam, R. D. (2000). *Bowling Alone: The Collapse and Revival of American Community*. Simon & Schuster.
- Henrich, J. (2020). *The WEIRDest People in the World*. Farrar, Straus & Giroux.
- Bramoullé, Y., Galeotti, A., & Rogers, B. (2016). *The Oxford Handbook of the Economics of Networks*. Oxford University Press.
- Bandura, A. (1977). *Social Learning Theory*. Prentice-Hall.

## Network Structure: k-Nearest Neighbors

Communities are placed at random 2D positions and connected to their $k$ nearest Euclidean neighbors. This creates a geographically embedded network where:
- Trade and contagion decay with distance
- Migration goes to the nearest higher-wealth neighbor
- R-contagion is strongest between close communities

$k = 4$ is the default, matching the empirical observation that most communities have 3–6 strong trading/social partnerships. Higher $k$ creates a more integrated society; $k = 2$ creates a sparse chain.

Reference for geographic network embedding:
- Barthélemy, M. (2011). Spatial networks. *Physics Reports*, 499(1–3), 1–101.
