"""Multi-community society network with trade, migration, contagion, R-contagion."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import networkx as nx
import numpy as np

from .community import CommunityConfig, CommunityState, initialize_community, step_community
from .outcomes import OutcomeClassifier, OutcomeThresholds, compute_gini
from .relational import RelationalState
from .shocks import SHOCK_ENVIRONMENTS, ShockEnvironment, ShockGenerator


COMMUNITY_ARCHETYPES = {
    "strong_nuclear_religious_dense": CommunityConfig(
        name="Strong nuclear + religious + dense",
        population=400,
        sqft_per_resident=200.0,
    ),
    "independent_secular_suburban": CommunityConfig(
        name="Independent + secular + suburban",
        population=600,
        sqft_per_resident=800.0,
    ),
    "extended_kin_religious_dense": CommunityConfig(
        name="Extended kin + religious + dense",
        population=350,
        sqft_per_resident=180.0,
    ),
    "mixed_diverse": CommunityConfig(
        name="Mixed/diverse",
        population=500,
        sqft_per_resident=400.0,
    ),
}


def _build_archetype_config(archetype: str, rng: np.random.Generator) -> CommunityConfig:
    from .community import TimeAllocation
    from .relational import RelationalConfig

    if archetype == "strong_nuclear_religious_dense":
        return CommunityConfig(
            name="Strong nuclear + religious + dense",
            population=int(rng.integers(300, 500)),
            sqft_per_resident=float(rng.uniform(150, 280)),
            relational_config=RelationalConfig(w_family=0.5, w_religion=0.3, w_spatial=0.2),
            time_allocation=TimeAllocation(production=0.35, family=0.30, religion=0.20, spatial_maintenance=0.08, leisure=0.07),
        )
    elif archetype == "independent_secular_suburban":
        return CommunityConfig(
            name="Independent + secular + suburban",
            population=int(rng.integers(400, 700)),
            sqft_per_resident=float(rng.uniform(600, 1200)),
            relational_config=RelationalConfig(w_family=0.3, w_religion=0.1, w_spatial=0.6),
            time_allocation=TimeAllocation(production=0.50, family=0.15, religion=0.05, spatial_maintenance=0.15, leisure=0.15),
        )
    elif archetype == "extended_kin_religious_dense":
        return CommunityConfig(
            name="Extended kin + religious + dense",
            population=int(rng.integers(300, 450)),
            sqft_per_resident=float(rng.uniform(130, 250)),
            relational_config=RelationalConfig(w_family=0.45, w_religion=0.35, w_spatial=0.20),
            time_allocation=TimeAllocation(production=0.30, family=0.35, religion=0.20, spatial_maintenance=0.08, leisure=0.07),
        )
    else:  # mixed_diverse
        return CommunityConfig(
            name="Mixed/diverse",
            population=int(rng.integers(300, 600)),
            sqft_per_resident=float(rng.uniform(250, 600)),
            relational_config=RelationalConfig(w_family=0.35, w_religion=0.25, w_spatial=0.40),
            time_allocation=TimeAllocation(production=0.40, family=0.22, religion=0.13, spatial_maintenance=0.12, leisure=0.13),
        )


@dataclass
class SocietyMetrics:
    year: float
    total_wealth: float
    mean_wealth: float
    gini: float
    migration_flux: float
    n_collapsed: int
    n_grew: int
    n_stabilized: int
    n_declined: int
    n_in_progress: int


@dataclass
class SocietyConfig:
    n_communities: int = 30
    archetype_fractions: dict[str, float] = field(default_factory=lambda: {
        "strong_nuclear_religious_dense": 0.25,
        "independent_secular_suburban": 0.25,
        "extended_kin_religious_dense": 0.25,
        "mixed_diverse": 0.25,
    })
    spatial_spread: float = 50.0
    network_k: int = 4

    trade_strength: float = 1.0
    migration_friction: float = 0.3
    migration_threshold: float = 0.6     # W/W0 below which migration triggers
    r_contagion_strength: float = 0.3

    shock_environment: str = "moderate"
    shock_topology: Optional[dict[str, float]] = None

    horizon: int = 30
    dt: float = 1.0
    seed: Optional[int] = 0
    thresholds: OutcomeThresholds = field(default_factory=OutcomeThresholds)


class Society:
    def __init__(self, config: SocietyConfig, rng: np.random.Generator) -> None:
        self.config = config
        self.rng = rng
        self.communities: list[CommunityState] = []
        self.configs: list[CommunityConfig] = []
        self.w0s: list[float] = []
        self.positions: np.ndarray = np.empty((0, 2))
        self.graph: nx.Graph = nx.Graph()
        self.metrics_history: list[SocietyMetrics] = []
        self.w_histories: list[list[float]] = []
        self.classifier = OutcomeClassifier(config.thresholds)
        self._setup()

    def _setup(self) -> None:
        n = self.config.n_communities
        archetypes = list(self.config.archetype_fractions.keys())
        fracs = list(self.config.archetype_fractions.values())
        total = sum(fracs)
        probs = [f / total for f in fracs]

        chosen = self.rng.choice(archetypes, size=n, p=probs)
        for archetype in chosen:
            cfg = _build_archetype_config(archetype, self.rng)
            self.configs.append(cfg)
            state = initialize_community(cfg, self.rng)
            self.communities.append(state)
            self.w0s.append(state.w)
            self.w_histories.append([])

        # 2D positions on continuous plane
        spread = self.config.spatial_spread
        self.positions = self.rng.uniform(0, spread, size=(n, 2))

        # Build k-nearest-neighbor graph
        self.graph = self._build_knn_graph(n, self.config.network_k)

    def _build_knn_graph(self, n: int, k: int) -> nx.Graph:
        g = nx.Graph()
        g.add_nodes_from(range(n))
        if n < 2:
            return g
        for i in range(n):
            dists = [
                (j, float(np.linalg.norm(self.positions[i] - self.positions[j])))
                for j in range(n) if j != i
            ]
            dists.sort(key=lambda x: x[1])
            for j, _ in dists[:k]:
                g.add_edge(i, j)
        return g

    def _neighbor_lists(self) -> list[list[int]]:
        return [list(self.graph.neighbors(i)) for i in range(len(self.communities))]

    def _distances(self) -> np.ndarray:
        n = len(self.communities)
        d = np.zeros((n, n))
        for i in range(n):
            for j in range(i + 1, n):
                dist = float(np.linalg.norm(self.positions[i] - self.positions[j]))
                d[i, j] = d[j, i] = dist
        return d

    def step(
        self,
        current_year: float,
        dt: float,
        shock_gen: ShockGenerator,
    ) -> SocietyMetrics:
        n = len(self.communities)
        if n == 0:
            return SocietyMetrics(current_year, 0, 0, 0, 0, 0, 0, 0, 0, 0)

        distances = self._distances()
        neighbor_lists = self._neighbor_lists()

        # 1. Generate shocks
        shocks = shock_gen.generate_shocks(
            n_communities=n,
            current_year=current_year,
            dt=dt,
            neighbor_lists=neighbor_lists,
        )

        # 2. Trade: gravity model redistributes M
        wealth_arr = np.array([c.w for c in self.communities])
        m_boost = np.zeros(n)
        kappa = 0.002 * self.config.trade_strength
        eps = 1.0
        for i in range(n):
            for j in self.graph.neighbors(i):
                d2 = distances[i, j] ** 2 + eps
                trade = kappa * wealth_arr[i] * wealth_arr[j] / d2
                m_boost[i] += trade * dt

        # 3. R-contagion: weighted average of neighbor R
        r_vals = np.array([c.relational.compute_r(cfg.relational_config)
                           for c, cfg in zip(self.communities, self.configs)])
        r_neighbor_avgs = np.zeros(n)
        for i in range(n):
            neighbors = list(self.graph.neighbors(i))
            if neighbors:
                r_neighbor_avgs[i] = float(np.mean(r_vals[neighbors]))

        # 4. Step each community
        new_states = []
        for i, (state, cfg) in enumerate(zip(self.communities, self.configs)):
            applicable_shocks = [s for s in shocks if i in s.affected_indices]
            new_state = step_community(
                state,
                dt=dt,
                shocks=applicable_shocks,
                m_boost=float(m_boost[i]),
                r_neighbor_avg=float(r_neighbor_avgs[i]),
                r_contagion_strength=self.config.r_contagion_strength,
            )
            new_states.append(new_state)

        # 5. Migration: communities below threshold migrate to nearest higher-wealth neighbor
        migration_flux = 0.0
        w_new = np.array([s.w for s in new_states])
        tau_m = self.config.migration_threshold
        mu = 0.02 * (1 - self.config.migration_friction)
        m_adjustments = np.zeros(n)

        for i, state in enumerate(new_states):
            w0_i = self.w0s[i]
            if state.w < w0_i * tau_m:
                neighbors = list(self.graph.neighbors(i))
                if not neighbors:
                    continue
                higher = [j for j in neighbors if w_new[j] > state.w]
                if not higher:
                    continue
                target = higher[int(np.argmax([w_new[j] for j in higher]))]
                migrate_m = state.m * mu
                m_adjustments[i] -= migrate_m
                m_adjustments[target] += migrate_m * 0.8  # some friction loss
                migration_flux += migrate_m

        # Apply migration adjustments
        for i in range(n):
            if m_adjustments[i] != 0:
                new_m = max(new_states[i].m + m_adjustments[i], 1e-6)
                s = new_states[i]
                from .community import CommunityState
                new_states[i] = CommunityState(
                    m=new_m,
                    relational=s.relational,
                    time_alloc=s.time_alloc,
                    population=s.population,
                    year=s.year,
                    alive=s.alive,
                    config=s.config,
                )

        self.communities = new_states

        # Record wealth histories
        for i, s in enumerate(self.communities):
            self.w_histories[i].append(s.w)

        # Compute metrics
        w_arr = np.array([s.w for s in self.communities])
        pop_arr = np.array([s.population for s in self.communities])
        total_wealth = float(np.sum(w_arr * pop_arr))
        mean_w = float(np.mean(w_arr))
        gini = compute_gini(list(w_arr))

        outcomes = [
            self.classifier.classify_interim(self.w_histories[i], self.w0s[i])
            for i in range(n)
        ]
        from .outcomes import Outcome
        metrics = SocietyMetrics(
            year=current_year + dt,
            total_wealth=total_wealth,
            mean_wealth=mean_w,
            gini=gini,
            migration_flux=migration_flux,
            n_collapsed=sum(1 for o in outcomes if o == Outcome.COLLAPSED),
            n_grew=sum(1 for o in outcomes if o == Outcome.GREW),
            n_stabilized=sum(1 for o in outcomes if o == Outcome.STABILIZED),
            n_declined=sum(1 for o in outcomes if o == Outcome.DECLINED),
            n_in_progress=sum(1 for o in outcomes if o == Outcome.IN_PROGRESS),
        )
        self.metrics_history.append(metrics)
        return metrics

    def final_outcomes(self) -> list:
        from .outcomes import Outcome
        results = []
        for i in range(len(self.communities)):
            from .outcomes import CommunityResult
            result = CommunityResult(
                w_history=self.w_histories[i],
                w0=self.w0s[i],
                years=[j * self.config.dt for j in range(len(self.w_histories[i]))],
                alive_history=[True] * len(self.w_histories[i]),
            )
            results.append(self.classifier.classify(result))
        return results
