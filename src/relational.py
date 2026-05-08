"""Relational capital R = w_F * F + w_Rel * Rel + w_S * S(density)."""
from __future__ import annotations

import numpy as np
from pydantic import BaseModel, Field, model_validator


# Spatial logistic peak at ~250 sqft/resident (Jacobs 1961, Alexander 1977)
SPATIAL_PEAK_SQFT = 250.0
SPATIAL_STEEPNESS = 0.015


def spatial_relational_capital(sqft_per_resident: float) -> float:
    """Logistic-bell spatial component peaking at ~250 sqft/resident.

    Uses a product of two logistics to create a single peak:
      S(x) = logistic(k*(x - x_low)) * (1 - logistic(k*(x - x_high)))
    where x_low < peak < x_high.
    """
    if sqft_per_resident < 0:
        raise ValueError("sqft_per_resident must be non-negative")

    x_low = 100.0
    x_high = 400.0
    k = SPATIAL_STEEPNESS * 3

    left = 1.0 / (1.0 + np.exp(-k * (sqft_per_resident - x_low)))
    right = 1.0 - 1.0 / (1.0 + np.exp(-k * (sqft_per_resident - x_high)))
    raw = left * right

    # Normalize so peak ≈ 1.0
    peak_raw = spatial_relational_capital_unnormalized(SPATIAL_PEAK_SQFT, k, x_low, x_high)
    if peak_raw <= 0:
        return 0.0
    return float(np.clip(raw / peak_raw, 0.0, 1.0))


def spatial_relational_capital_unnormalized(x: float, k: float, x_low: float, x_high: float) -> float:
    left = 1.0 / (1.0 + np.exp(-k * (x - x_low)))
    right = 1.0 - 1.0 / (1.0 + np.exp(-k * (x - x_high)))
    return float(left * right)


class RelationalConfig(BaseModel):
    w_family: float = Field(default=0.4, ge=0.0, le=1.0)
    w_religion: float = Field(default=0.3, ge=0.0, le=1.0)
    w_spatial: float = Field(default=0.3, ge=0.0, le=1.0)

    family_decay_rate: float = Field(default=0.05, ge=0.0, description="Per-period decay without family time")
    family_growth_rate: float = Field(default=0.1, ge=0.0, description="Growth rate with family time")
    religion_decay_rate: float = Field(default=0.03, ge=0.0)
    religion_growth_rate: float = Field(default=0.08, ge=0.0)

    @model_validator(mode="after")
    def weights_positive(self) -> "RelationalConfig":
        total = self.w_family + self.w_religion + self.w_spatial
        if total <= 0:
            raise ValueError("Relational weights must sum to a positive value")
        return self


class RelationalState(BaseModel):
    family_strength: float = Field(default=0.7, ge=0.0, le=1.0)
    religion_participation: float = Field(default=0.6, ge=0.0, le=1.0)
    sqft_per_resident: float = Field(default=300.0, ge=10.0)

    def compute_r(self, config: RelationalConfig) -> float:
        total_w = config.w_family + config.w_religion + config.w_spatial
        w_f = config.w_family / total_w
        w_r = config.w_religion / total_w
        w_s = config.w_spatial / total_w

        s = spatial_relational_capital(self.sqft_per_resident)
        return float(
            w_f * self.family_strength
            + w_r * self.religion_participation
            + w_s * s
        )

    def step(
        self,
        config: RelationalConfig,
        family_time_fraction: float,
        religion_time_fraction: float,
        dt: float = 1.0,
        meaning_crisis_shock: float = 0.0,
    ) -> "RelationalState":
        """Update relational state for one time step.

        meaning_crisis_shock ∈ [0, 1]: religion specifically buffers this.
        Returns new RelationalState (immutable update pattern).
        """
        family_min_to_grow = 0.1

        if family_time_fraction >= family_min_to_grow:
            delta_f = config.family_growth_rate * family_time_fraction * dt
        else:
            delta_f = -config.family_decay_rate * dt

        religion_min_to_grow = 0.05
        effective_religion_time = religion_time_fraction * (1.0 + self.religion_participation * 0.2)
        if religion_time_fraction >= religion_min_to_grow:
            delta_rel = config.religion_growth_rate * effective_religion_time * dt
        else:
            delta_rel = -config.religion_decay_rate * dt

        # Religion buffers meaning-crisis shocks — high participation reduces shock impact
        meaning_shock_absorbed = meaning_crisis_shock * self.religion_participation
        delta_rel -= meaning_shock_absorbed * 0.1 * dt

        new_family = float(np.clip(self.family_strength + delta_f, 0.0, 1.0))
        new_religion = float(np.clip(self.religion_participation + delta_rel, 0.0, 1.0))

        return RelationalState(
            family_strength=new_family,
            religion_participation=new_religion,
            sqft_per_resident=self.sqft_per_resident,
        )
