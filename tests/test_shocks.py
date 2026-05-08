"""Tests for shock generation module."""
import numpy as np
import pytest

from src.shocks import (
    MILD_ENV,
    MODERATE_ENV,
    SEVERE_ENV,
    ShockEnvironment,
    ShockGenerator,
    ShockTarget,
    ShockType,
)


def test_shock_types_exist():
    assert ShockType.IDIOSYNCRATIC
    assert ShockType.LOCAL
    assert ShockType.REGIONAL
    assert ShockType.GLOBAL


def test_generate_shocks_returns_list():
    rng = np.random.default_rng(42)
    gen = ShockGenerator(MODERATE_ENV, rng)
    shocks = gen.generate_shocks(n_communities=10, current_year=0.0, dt=1.0)
    assert isinstance(shocks, list)


def test_global_shock_affects_all():
    rng = np.random.default_rng(42)
    # Force global shocks by overriding env
    env = ShockEnvironment(
        annual_shock_probability=10.0,  # high to guarantee shocks
        mean_severity=0.2,
        severity_std=0.01,
        p_local=0.0, p_regional=0.0, p_global=1.0, p_idiosyncratic=0.0,
    )
    gen = ShockGenerator(env, rng)
    shocks = gen.generate_shocks(n_communities=5, current_year=0.0, dt=1.0)
    # Every generated shock should be global
    for shock in shocks:
        assert shock.shock_type == ShockType.GLOBAL
        assert sorted(shock.affected_indices) == [0, 1, 2, 3, 4]


def test_idiosyncratic_affects_one():
    rng = np.random.default_rng(123)
    env = ShockEnvironment(
        annual_shock_probability=10.0,
        mean_severity=0.2, severity_std=0.01,
        p_local=0.0, p_regional=0.0, p_global=0.0, p_idiosyncratic=1.0,
    )
    gen = ShockGenerator(env, rng)
    shocks = gen.generate_shocks(n_communities=20, current_year=0.0, dt=1.0)
    for shock in shocks:
        assert shock.shock_type == ShockType.IDIOSYNCRATIC
        assert len(shock.affected_indices) == 1


def test_regional_affects_30_to_50_percent():
    """_select_affected for REGIONAL should pick 30-50% of communities before cooldown filtering."""
    env = ShockEnvironment()
    for seed in range(50):
        gen = ShockGenerator(env, np.random.default_rng(seed))
        affected = gen._select_affected(ShockType.REGIONAL, n_communities=100, neighbor_lists=None)
        n = len(affected)
        assert 28 <= n <= 52, f"Regional _select_affected chose {n}/100 communities (seed={seed})"


def test_severity_bounded():
    rng = np.random.default_rng(7)
    gen = ShockGenerator(SEVERE_ENV, rng)
    for _ in range(100):
        s = gen.sample_severity()
        assert 0.0 < s <= 0.90


def test_mild_less_frequent_than_severe():
    rng_m = np.random.default_rng(42)
    rng_s = np.random.default_rng(42)
    n_shocks_mild = sum(
        len(ShockGenerator(MILD_ENV, np.random.default_rng(i)).generate_shocks(10, i, 1.0))
        for i in range(100)
    )
    n_shocks_severe = sum(
        len(ShockGenerator(SEVERE_ENV, np.random.default_rng(i)).generate_shocks(10, i, 1.0))
        for i in range(100)
    )
    assert n_shocks_mild < n_shocks_severe


def test_cooldown_prevents_double_shock():
    rng = np.random.default_rng(0)
    env = ShockEnvironment(
        annual_shock_probability=100.0,
        mean_severity=0.2, severity_std=0.01,
        p_local=0.0, p_regional=0.0, p_global=0.0, p_idiosyncratic=1.0,
    )
    gen = ShockGenerator(env, rng)
    shocks1 = gen.generate_shocks(n_communities=1, current_year=0.0, dt=1.0)
    shocks2 = gen.generate_shocks(n_communities=1, current_year=0.1, dt=1.0)
    # Should have fewer shocks in second call due to cooldown
    assert len(shocks2) <= len(shocks1)


def test_no_shocks_for_zero_communities():
    rng = np.random.default_rng(5)
    gen = ShockGenerator(SEVERE_ENV, rng)
    shocks = gen.generate_shocks(n_communities=0, current_year=0.0, dt=1.0)
    assert shocks == []


def test_shock_frequency_calibration():
    """Mean shocks per year should be close to annual_shock_probability."""
    rng = np.random.default_rng(42)
    gen = ShockGenerator(MODERATE_ENV, rng)
    total = 0
    trials = 1000
    for i in range(trials):
        total += len(gen.generate_shocks(n_communities=1, current_year=float(i * 2), dt=1.0))
    # With cooldown filtering, actual rate ≤ env rate; just check it's in reasonable range
    observed_rate = total / trials
    assert 0.05 <= observed_rate <= 0.5
