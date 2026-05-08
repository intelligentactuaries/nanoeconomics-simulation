"""Hazard function and survival probability mathematics."""
from __future__ import annotations

import numpy as np


DEFAULT_H0 = 0.02       # baseline annual hazard
DEFAULT_BETA_W = 2.0    # wealth-protection coefficient


def hazard(
    w: float,
    w0: float,
    h0: float = DEFAULT_H0,
    beta_w: float = DEFAULT_BETA_W,
) -> float:
    """Instantaneous hazard rate: h(t) = h0 * exp(-beta_W * log(W/W0)).

    Higher wealth → lower hazard. At W = W0, h = h0.
    W must be positive; w0 must be positive.
    """
    if w0 <= 0:
        raise ValueError(f"w0 must be positive, got {w0}")
    if w <= 0:
        w = 1e-10  # near-zero → very high hazard

    log_ratio = np.log(w / w0)
    return float(h0 * np.exp(-beta_w * log_ratio))


def survival_probability(
    w_trajectory: list[float],
    w0: float,
    dt: float = 1.0,
    h0: float = DEFAULT_H0,
    beta_w: float = DEFAULT_BETA_W,
) -> float:
    """Compute cumulative survival probability from a wealth trajectory.

    S(T) = exp(-∫₀ᵀ h(t) dt) ≈ exp(-Σ h(t_i) * dt)
    """
    if not w_trajectory:
        return 1.0
    cumulative_hazard = sum(hazard(w, w0, h0, beta_w) * dt for w in w_trajectory)
    return float(np.exp(-cumulative_hazard))


def survival_curve(
    w_trajectory: list[float],
    w0: float,
    dt: float = 1.0,
    h0: float = DEFAULT_H0,
    beta_w: float = DEFAULT_BETA_W,
) -> list[float]:
    """Cumulative survival S(t) at each time step."""
    if not w_trajectory:
        return []
    result = []
    cumulative_hazard = 0.0
    for w in w_trajectory:
        cumulative_hazard += hazard(w, w0, h0, beta_w) * dt
        result.append(float(np.exp(-cumulative_hazard)))
    return result


def hazard_array(
    w: np.ndarray,
    w0: float,
    h0: float = DEFAULT_H0,
    beta_w: float = DEFAULT_BETA_W,
) -> np.ndarray:
    """Vectorized hazard for an array of wealth values."""
    w = np.asarray(w, dtype=float)
    safe_w = np.where(w > 0, w, 1e-10)
    log_ratio = np.log(safe_w / w0)
    h = h0 * np.exp(-beta_w * log_ratio)
    return h
