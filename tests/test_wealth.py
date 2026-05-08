"""Tests for the W(M, T, R) wealth function."""
import numpy as np
import pytest

from src.wealth import compute_wealth, compute_wealth_array


def test_basic_computation():
    w = compute_wealth(1.0, 1.0, 1.0)
    assert abs(w - 1.0) < 1e-9


def test_zero_m_returns_zero():
    assert compute_wealth(0.0, 1.0, 1.0) == 0.0


def test_zero_t_returns_zero():
    assert compute_wealth(1.0, 0.0, 1.0) == 0.0


def test_zero_r_returns_zero():
    assert compute_wealth(1.0, 1.0, 0.0) == 0.0


def test_negative_inputs_raise():
    with pytest.raises(ValueError):
        compute_wealth(-1.0, 1.0, 1.0)
    with pytest.raises(ValueError):
        compute_wealth(1.0, -1.0, 1.0)
    with pytest.raises(ValueError):
        compute_wealth(1.0, 1.0, -1.0)


def test_alpha_sum_constraint_renormalized():
    # Unnormalized alphas should still produce correct Cobb-Douglas
    w1 = compute_wealth(2.0, 3.0, 4.0, alpha_m=0.4, alpha_t=0.3, alpha_r=0.3)
    w2 = compute_wealth(2.0, 3.0, 4.0, alpha_m=4.0, alpha_t=3.0, alpha_r=3.0)
    assert abs(w1 - w2) < 1e-9


def test_alpha_zero_weights_raise():
    with pytest.raises(ValueError):
        compute_wealth(1.0, 1.0, 1.0, alpha_m=0.0, alpha_t=0.0, alpha_r=0.0)


def test_increasing_in_each_dimension():
    w_base = compute_wealth(1.0, 1.0, 1.0)
    assert compute_wealth(2.0, 1.0, 1.0) > w_base
    assert compute_wealth(1.0, 2.0, 1.0) > w_base
    assert compute_wealth(1.0, 1.0, 2.0) > w_base


def test_cobb_douglas_homogeneity():
    # W(lambda*M, lambda*T, lambda*R) = lambda * W(M,T,R) when alphas sum to 1
    lam = 3.0
    w = compute_wealth(1.0, 1.0, 1.0)
    w_scaled = compute_wealth(lam, lam, lam)
    assert abs(w_scaled - lam * w) < 1e-9


def test_array_version_matches_scalar():
    m = np.array([1.0, 2.0, 0.5])
    t = np.array([1.0, 1.5, 0.8])
    r = np.array([1.0, 0.7, 1.2])
    result = compute_wealth_array(m, t, r)
    for i in range(3):
        assert abs(result[i] - compute_wealth(m[i], t[i], r[i])) < 1e-9


def test_array_handles_zeros():
    m = np.array([0.0, 1.0, 1.0])
    t = np.array([1.0, 0.0, 1.0])
    r = np.array([1.0, 1.0, 0.0])
    result = compute_wealth_array(m, t, r)
    assert all(result == 0.0)


def test_alpha_elasticity():
    # Doubling M should increase W by factor 2^alpha_m
    alpha_m = 0.4
    w1 = compute_wealth(1.0, 1.0, 1.0, alpha_m=alpha_m)
    w2 = compute_wealth(2.0, 1.0, 1.0, alpha_m=alpha_m)
    assert abs(w2 / w1 - 2**alpha_m) < 1e-6
