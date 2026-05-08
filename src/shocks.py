"""Stochastic shocks with spatial topology support."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import numpy as np


class ShockType(str, Enum):
    IDIOSYNCRATIC = "idiosyncratic"   # single community
    LOCAL = "local"                    # 1-3 nearest neighbors
    REGIONAL = "regional"              # 30-50% of communities
    GLOBAL = "global"                  # all communities


class ShockTarget(str, Enum):
    MATERIAL = "material"
    TIME = "time"
    FAMILY = "family"
    RELIGION = "religion"
    MEANING_CRISIS = "meaning_crisis"
    COMBINED = "combined"


@dataclass
class ShockEvent:
    shock_type: ShockType
    target: ShockTarget
    severity: float           # fractional loss, ∈ (0, 1]
    affected_indices: list[int] = field(default_factory=list)
    year: float = 0.0


@dataclass
class ShockEnvironment:
    """Calibrated shock environment."""
    annual_shock_probability: float = 0.25
    mean_severity: float = 0.15
    severity_std: float = 0.08

    # Topology mix (must sum ≤ 1; remainder is idiosyncratic)
    p_local: float = 0.35
    p_regional: float = 0.20
    p_global: float = 0.05
    p_idiosyncratic: float = 0.40

    # Shock target mix
    p_material: float = 0.35
    p_time: float = 0.20
    p_family: float = 0.15
    p_religion: float = 0.10
    p_meaning_crisis: float = 0.10
    p_combined: float = 0.10


MILD_ENV = ShockEnvironment(
    annual_shock_probability=0.10,
    mean_severity=0.08,
    severity_std=0.04,
    p_local=0.35, p_regional=0.10, p_global=0.02, p_idiosyncratic=0.53,
)
MODERATE_ENV = ShockEnvironment(
    annual_shock_probability=0.25,
    mean_severity=0.15,
    severity_std=0.08,
    p_local=0.35, p_regional=0.20, p_global=0.05, p_idiosyncratic=0.40,
)
SEVERE_ENV = ShockEnvironment(
    annual_shock_probability=0.45,
    mean_severity=0.25,
    severity_std=0.12,
    p_local=0.30, p_regional=0.30, p_global=0.15, p_idiosyncratic=0.25,
)

SHOCK_ENVIRONMENTS = {
    "mild": MILD_ENV,
    "moderate": MODERATE_ENV,
    "severe": SEVERE_ENV,
}


class ShockGenerator:
    def __init__(self, env: ShockEnvironment, rng: Optional[np.random.Generator] = None) -> None:
        self.env = env
        self.rng = rng if rng is not None else np.random.default_rng()
        self._cooldown: dict[int, float] = {}  # community_idx -> year_available_again

    def sample_severity(self) -> float:
        raw = self.rng.normal(self.env.mean_severity, self.env.severity_std)
        return float(np.clip(raw, 0.01, 0.90))

    def sample_target(self) -> ShockTarget:
        probs = [
            self.env.p_material,
            self.env.p_time,
            self.env.p_family,
            self.env.p_religion,
            self.env.p_meaning_crisis,
            self.env.p_combined,
        ]
        total = sum(probs)
        probs = [p / total for p in probs]
        targets = [
            ShockTarget.MATERIAL,
            ShockTarget.TIME,
            ShockTarget.FAMILY,
            ShockTarget.RELIGION,
            ShockTarget.MEANING_CRISIS,
            ShockTarget.COMBINED,
        ]
        idx = int(self.rng.choice(len(targets), p=probs))
        return targets[idx]

    def sample_topology(self) -> ShockType:
        p_vals = [self.env.p_local, self.env.p_regional, self.env.p_global, self.env.p_idiosyncratic]
        total = sum(p_vals)
        p_vals = [p / total for p in p_vals]
        types = [ShockType.LOCAL, ShockType.REGIONAL, ShockType.GLOBAL, ShockType.IDIOSYNCRATIC]
        idx = int(self.rng.choice(len(types), p=p_vals))
        return types[idx]

    def generate_shocks(
        self,
        n_communities: int,
        current_year: float,
        dt: float = 1.0,
        neighbor_lists: Optional[list[list[int]]] = None,
    ) -> list[ShockEvent]:
        """Generate zero or more shock events for this time step."""
        if n_communities == 0:
            return []

        expected_shocks = self.env.annual_shock_probability * dt
        n_shocks = int(self.rng.poisson(expected_shocks))

        events: list[ShockEvent] = []
        for _ in range(n_shocks):
            topology = self.sample_topology()
            target = self.sample_target()
            severity = self.sample_severity()
            affected = self._select_affected(topology, n_communities, neighbor_lists)

            # Filter out communities in cooldown
            affected = [i for i in affected if self._cooldown.get(i, -1) <= current_year]

            if not affected:
                continue

            event = ShockEvent(
                shock_type=topology,
                target=target,
                severity=severity,
                affected_indices=affected,
                year=current_year,
            )
            events.append(event)

            # Set cooldown (0.5 year) to prevent oscillation cascades
            for i in affected:
                self._cooldown[i] = current_year + 0.5

        return events

    def _select_affected(
        self,
        topology: ShockType,
        n_communities: int,
        neighbor_lists: Optional[list[list[int]]],
    ) -> list[int]:
        if n_communities == 1:
            return [0]

        if topology == ShockType.IDIOSYNCRATIC:
            return [int(self.rng.integers(0, n_communities))]

        if topology == ShockType.LOCAL:
            center = int(self.rng.integers(0, n_communities))
            affected = {center}
            n_local = int(self.rng.integers(1, 4))  # 1-3 neighbors
            if neighbor_lists is not None and center < len(neighbor_lists):
                neighbors = neighbor_lists[center][:n_local]
                affected.update(neighbors)
            else:
                # Fall back to random nearby indices
                candidates = [i for i in range(n_communities) if i != center]
                if candidates:
                    chosen = self.rng.choice(candidates, size=min(n_local, len(candidates)), replace=False)
                    affected.update(int(c) for c in chosen)
            return list(affected)

        if topology == ShockType.REGIONAL:
            fraction = float(self.rng.uniform(0.30, 0.50))
            n_affected = max(1, int(fraction * n_communities))
            indices = self.rng.choice(n_communities, size=n_affected, replace=False)
            return [int(i) for i in indices]

        if topology == ShockType.GLOBAL:
            return list(range(n_communities))

        return [int(self.rng.integers(0, n_communities))]
