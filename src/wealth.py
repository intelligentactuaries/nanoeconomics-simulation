"""W(M, T, R) Cobb-Douglas wealth function."""
from __future__ import annotations

import numpy as np


DEFAULT_ALPHA_M = 0.4
DEFAULT_ALPHA_T = 0.3
DEFAULT_ALPHA_R = 0.3


def compute_wealth(
    m: float,
    t: float,
    r: float,
    alpha_m: float = DEFAULT_ALPHA_M,
    alpha_t: float = DEFAULT_ALPHA_T,
    alpha_r: float = DEFAULT_ALPHA_R,
) -> float:
    """Cobb-Douglas wealth: W = M^alpha_M * T^alpha_T * R^alpha_R.

    All inputs must be non-negative. Returns 0 when any dimension is 0.
    Alphas are renormalized if they don't sum to 1.
    """
    total = alpha_m + alpha_t + alpha_r
    if total <= 0:
        raise ValueError("Alpha weights must sum to a positive number")
    alpha_m, alpha_t, alpha_r = alpha_m / total, alpha_t / total, alpha_r / total

    if m < 0 or t < 0 or r < 0:
        raise ValueError(f"W components must be non-negative, got M={m}, T={t}, R={r}")

    if m == 0.0 or t == 0.0 or r == 0.0:
        return 0.0

    return float(m**alpha_m * t**alpha_t * r**alpha_r)


def compute_wealth_array(
    m: np.ndarray,
    t: np.ndarray,
    r: np.ndarray,
    alpha_m: float = DEFAULT_ALPHA_M,
    alpha_t: float = DEFAULT_ALPHA_T,
    alpha_r: float = DEFAULT_ALPHA_R,
) -> np.ndarray:
    """Vectorized Cobb-Douglas wealth for arrays of communities."""
    total = alpha_m + alpha_t + alpha_r
    if total <= 0:
        raise ValueError("Alpha weights must sum to a positive number")
    alpha_m, alpha_t, alpha_r = alpha_m / total, alpha_t / total, alpha_r / total

    m = np.asarray(m, dtype=float)
    t = np.asarray(t, dtype=float)
    r = np.asarray(r, dtype=float)

    result = np.zeros_like(m)
    mask = (m > 0) & (t > 0) & (r > 0)
    result[mask] = m[mask] ** alpha_m * t[mask] ** alpha_t * r[mask] ** alpha_r
    return result
