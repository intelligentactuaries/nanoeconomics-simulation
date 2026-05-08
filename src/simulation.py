"""Top-level simulation orchestration for single communities and societies."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from pydantic import BaseModel, Field

from .community import CommunityConfig, CommunityState, initialize_community, step_community
from .outcomes import (
    CommunityResult,
    Outcome,
    OutcomeClassifier,
    OutcomeThresholds,
    compute_gini,
)
from .shocks import SHOCK_ENVIRONMENTS, ShockEnvironment, ShockGenerator
from .survival import survival_curve


class SingleCommunityConfig(BaseModel):
    community: CommunityConfig = Field(default_factory=CommunityConfig)
    shock_environment: str = Field(default="moderate", description="mild/moderate/severe")
    horizon: int = Field(default=30, ge=5, le=100)
    n_paths: int = Field(default=200, ge=1, le=1000)
    dt: float = Field(default=1.0)
    seed: Optional[int] = None
    thresholds: OutcomeThresholds = Field(default_factory=OutcomeThresholds)


@dataclass
class SinglePathResult:
    w_history: list[float]
    m_history: list[float]
    t_history: list[float]
    r_history: list[float]
    alive_history: list[bool]
    years: list[float]
    outcome: Outcome
    survival_curve: list[float]


@dataclass
class SingleCommunityRunResult:
    config: SingleCommunityConfig
    paths: list[SinglePathResult]
    w0: float

    @property
    def n_paths(self) -> int:
        return len(self.paths)

    def mean_trajectory(self) -> list[float]:
        if not self.paths:
            return []
        n = len(self.paths[0].w_history)
        return [
            float(np.mean([p.w_history[i] for p in self.paths if i < len(p.w_history)]))
            for i in range(n)
        ]

    def percentile_trajectory(self, q: float) -> list[float]:
        if not self.paths:
            return []
        n = len(self.paths[0].w_history)
        return [
            float(np.percentile([p.w_history[i] for p in self.paths if i < len(p.w_history)], q))
            for i in range(n)
        ]

    def outcome_counts(self) -> dict[Outcome, int]:
        counts: dict[Outcome, int] = {o: 0 for o in Outcome if o != Outcome.IN_PROGRESS}
        for p in self.paths:
            counts[p.outcome] = counts.get(p.outcome, 0) + 1
        return counts

    def outcome_fractions(self) -> dict[Outcome, float]:
        counts = self.outcome_counts()
        total = self.n_paths
        return {o: c / total for o, c in counts.items()}

    def dominant_outcome(self) -> Outcome:
        counts = self.outcome_counts()
        return max(counts, key=lambda o: counts[o])

    def mean_survival_curve(self) -> list[float]:
        if not self.paths:
            return []
        n = len(self.paths[0].survival_curve)
        return [
            float(np.mean([p.survival_curve[i] for p in self.paths if i < len(p.survival_curve)]))
            for i in range(n)
        ]


def run_single_path(
    config: CommunityConfig,
    horizon: int,
    dt: float,
    rng: np.random.Generator,
    shock_env: ShockEnvironment,
    thresholds: OutcomeThresholds,
) -> SinglePathResult:
    state = initialize_community(config, rng)
    w0 = state.w
    shock_gen = ShockGenerator(shock_env, rng)
    classifier = OutcomeClassifier(thresholds)

    w_hist, m_hist, t_hist, r_hist, alive_hist, years = [], [], [], [], [], []
    n_steps = int(horizon / dt)

    for step_i in range(n_steps):
        year = step_i * dt
        shocks = shock_gen.generate_shocks(n_communities=1, current_year=year, dt=dt)
        # All shocks affect community 0 (single community mode)
        applicable = [s for s in shocks if 0 in s.affected_indices]

        state = step_community(state, dt=dt, shocks=applicable)

        w_hist.append(state.w)
        m_hist.append(state.m)
        r_hist.append(state.relational.compute_r(config.relational_config))
        t_hist.append(state.time_alloc.effective_t())
        alive_hist.append(state.alive)
        years.append(state.year)

    surv = survival_curve(w_hist, w0=max(w0, 1e-10), dt=dt)
    comm_result = CommunityResult(
        w_history=w_hist, w0=max(w0, 1e-10), years=years, alive_history=alive_hist,
    )
    outcome = classifier.classify(comm_result)

    return SinglePathResult(
        w_history=w_hist,
        m_history=m_hist,
        t_history=t_hist,
        r_history=r_hist,
        alive_history=alive_hist,
        years=years,
        outcome=outcome,
        survival_curve=surv,
    )


def run_single_community(config: SingleCommunityConfig) -> SingleCommunityRunResult:
    """Run n_paths Monte Carlo paths for a single community. Reproducible via seed."""
    seed = config.seed if config.seed is not None else 0
    rng = np.random.default_rng(seed)
    shock_env = SHOCK_ENVIRONMENTS.get(config.shock_environment, SHOCK_ENVIRONMENTS["moderate"])

    init_state = initialize_community(config.community)
    w0 = init_state.w

    paths = []
    for path_seed in range(config.n_paths):
        path_rng = np.random.default_rng(seed * 10000 + path_seed)
        path = run_single_path(
            config.community,
            horizon=config.horizon,
            dt=config.dt,
            rng=path_rng,
            shock_env=shock_env,
            thresholds=config.thresholds,
        )
        paths.append(path)

    return SingleCommunityRunResult(config=config, paths=paths, w0=w0)
