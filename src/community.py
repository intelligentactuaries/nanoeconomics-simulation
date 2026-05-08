"""Single-community state machine with time-stepping dynamics."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from pydantic import BaseModel, Field, model_validator

from .relational import RelationalConfig, RelationalState
from .shocks import ShockEvent, ShockTarget
from .wealth import compute_wealth


class TimeAllocation(BaseModel):
    """Time shares across activities; auto-normalizes to sum to 1."""
    production: float = Field(default=0.40, ge=0.0)
    family: float = Field(default=0.25, ge=0.0)
    religion: float = Field(default=0.15, ge=0.0)
    spatial_maintenance: float = Field(default=0.10, ge=0.0)
    leisure: float = Field(default=0.10, ge=0.0)

    @model_validator(mode="after")
    def normalize(self) -> "TimeAllocation":
        total = (
            self.production + self.family + self.religion
            + self.spatial_maintenance + self.leisure
        )
        if total <= 0:
            raise ValueError("At least one time allocation must be positive")
        self.production /= total
        self.family /= total
        self.religion /= total
        self.spatial_maintenance /= total
        self.leisure /= total
        return self

    def effective_t(self) -> float:
        """Productive time component used in W(M,T,R) — focuses on production + some leisure."""
        return self.production + 0.3 * self.leisure


class CommunityConfig(BaseModel):
    name: str = "Community"
    population: int = Field(default=500, ge=100, le=5000)
    sqft_per_resident: float = Field(default=300.0, ge=10.0)

    # Wealth function exponents
    alpha_m: float = Field(default=0.4, gt=0.0)
    alpha_t: float = Field(default=0.3, gt=0.0)
    alpha_r: float = Field(default=0.3, gt=0.0)

    # Initial values
    m0: float = Field(default=1.0, gt=0.0, description="Initial material capital (normalized)")

    time_allocation: TimeAllocation = Field(default_factory=TimeAllocation)
    relational_config: RelationalConfig = Field(default_factory=RelationalConfig)

    # Material capital dynamics
    m_production_rate: float = Field(default=0.04, description="Annual M growth from production")
    m_maintenance_drain: float = Field(default=0.01, description="Annual M drain for maintenance")

    # Hazard
    h0: float = Field(default=0.02)
    beta_w: float = Field(default=2.0)


@dataclass
class CommunityState:
    """Mutable simulation state for one community at one time step."""
    m: float
    relational: RelationalState
    time_alloc: TimeAllocation
    population: float
    year: float = 0.0
    alive: bool = True
    w: float = field(init=False)
    config: CommunityConfig = field(repr=False, default=None)  # type: ignore[assignment]

    def __post_init__(self) -> None:
        self.w = self._compute_w()

    def _compute_w(self) -> float:
        r = self.relational.compute_r(self.config.relational_config)
        t = self.time_alloc.effective_t()
        return compute_wealth(
            self.m, t, r,
            self.config.alpha_m, self.config.alpha_t, self.config.alpha_r,
        )

    def apply_shock(self, event: ShockEvent) -> None:
        """Apply a shock event to this community in-place."""
        s = event.severity
        if event.target in (ShockTarget.MATERIAL, ShockTarget.COMBINED):
            self.m = max(self.m * (1 - s), 1e-6)
        if event.target in (ShockTarget.TIME, ShockTarget.COMBINED):
            # Reduce production time, shift to recovery
            prod_reduction = self.time_alloc.production * s * 0.5
            new_prod = max(self.time_alloc.production - prod_reduction, 0.01)
            self.time_alloc = TimeAllocation(
                production=new_prod,
                family=self.time_alloc.family,
                religion=self.time_alloc.religion,
                spatial_maintenance=self.time_alloc.spatial_maintenance + prod_reduction * 0.5,
                leisure=self.time_alloc.leisure,
            )
        if event.target == ShockTarget.FAMILY:
            self.relational = RelationalState(
                family_strength=max(self.relational.family_strength * (1 - s), 0.0),
                religion_participation=self.relational.religion_participation,
                sqft_per_resident=self.relational.sqft_per_resident,
            )
        if event.target == ShockTarget.RELIGION:
            self.relational = RelationalState(
                family_strength=self.relational.family_strength,
                religion_participation=max(self.relational.religion_participation * (1 - s), 0.0),
                sqft_per_resident=self.relational.sqft_per_resident,
            )
        # meaning_crisis handled in relational step
        self.w = self._compute_w()


def step_community(
    state: CommunityState,
    dt: float = 1.0,
    shocks: Optional[list[ShockEvent]] = None,
    meaning_crisis_intensity: float = 0.0,
    m_boost: float = 0.0,
    r_neighbor_avg: float = 0.0,
    r_contagion_strength: float = 0.0,
) -> CommunityState:
    """Advance community state by dt years. Returns new state."""
    if not state.alive:
        return state

    config = state.config
    ta = state.time_alloc

    # Material capital: grows with production, drains with maintenance
    m_growth = config.m_production_rate * ta.production * state.m * dt
    m_drain = config.m_maintenance_drain * state.m * dt
    m_new = state.m + m_growth - m_drain + m_boost

    # Apply shocks to material before relational update
    temp_state = CommunityState(
        m=max(m_new, 1e-6),
        relational=state.relational,
        time_alloc=ta,
        population=state.population,
        year=state.year + dt,
        alive=state.alive,
        config=config,
    )

    if shocks:
        for shock in shocks:
            temp_state.apply_shock(shock)

    # Collect meaning_crisis severity from shocks
    mc_severity = meaning_crisis_intensity
    if shocks:
        for shock in shocks:
            if shock.target.value == "meaning_crisis":
                mc_severity = max(mc_severity, shock.severity)

    # Relational dynamics
    new_relational = temp_state.relational.step(
        config=config.relational_config,
        family_time_fraction=ta.family,
        religion_time_fraction=ta.religion,
        dt=dt,
        meaning_crisis_shock=mc_severity,
    )

    # R-contagion: neighbor R slightly pulls local R
    if r_contagion_strength > 0 and r_neighbor_avg > 0:
        local_r = new_relational.compute_r(config.relational_config)
        pull = r_contagion_strength * (r_neighbor_avg - local_r) * dt * 0.1
        # Distribute pull proportionally across family and religion
        new_f = float(np.clip(new_relational.family_strength + pull * 0.5, 0.0, 1.0))
        new_rel = float(np.clip(new_relational.religion_participation + pull * 0.5, 0.0, 1.0))
        new_relational = RelationalState(
            family_strength=new_f,
            religion_participation=new_rel,
            sqft_per_resident=new_relational.sqft_per_resident,
        )

    new_state = CommunityState(
        m=temp_state.m,
        relational=new_relational,
        time_alloc=ta,
        population=state.population,
        year=state.year + dt,
        alive=state.alive,
        config=config,
    )

    return new_state


def initialize_community(config: CommunityConfig, rng: Optional[np.random.Generator] = None) -> CommunityState:
    """Create initial community state from config."""
    rel_state = RelationalState(
        family_strength=config.relational_config.w_family * 0.9,  # near max
        religion_participation=config.relational_config.w_religion * 0.9,
        sqft_per_resident=config.sqft_per_resident,
    )
    # Ensure initial relational values are in [0,1]
    rel_state = RelationalState(
        family_strength=min(rel_state.family_strength, 1.0),
        religion_participation=min(rel_state.religion_participation, 1.0),
        sqft_per_resident=rel_state.sqft_per_resident,
    )

    return CommunityState(
        m=config.m0,
        relational=rel_state,
        time_alloc=config.time_allocation,
        population=float(config.population),
        year=0.0,
        alive=True,
        config=config,
    )
