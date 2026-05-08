"""Tests for hazard and survival functions."""
import numpy as np
import pytest

from src.survival import hazard, hazard_array, survival_curve, survival_probability


def test_hazard_at_w0_equals_h0():
    h = hazard(1.0, w0=1.0, h0=0.02)
    assert abs(h - 0.02) < 1e-9


def test_hazard_decreasing_in_wealth():
    h_low = hazard(0.5, w0=1.0)
    h_base = hazard(1.0, w0=1.0)
    h_high = hazard(2.0, w0=1.0)
    assert h_low > h_base > h_high


def test_hazard_positive():
    for w in [0.01, 0.5, 1.0, 5.0, 100.0]:
        assert hazard(w, w0=1.0) > 0


def test_hazard_zero_wealth():
    h = hazard(0.0, w0=1.0)
    assert h > 1.0  # very high hazard


def test_hazard_invalid_w0():
    with pytest.raises(ValueError):
        hazard(1.0, w0=0.0)
    with pytest.raises(ValueError):
        hazard(1.0, w0=-1.0)


def test_survival_starts_at_one():
    curve = survival_curve([1.0, 1.0, 1.0], w0=1.0)
    assert curve[0] <= 1.0


def test_survival_monotonically_decreasing():
    # If W stays below W0, hazard is high and survival should decrease
    trajectory = [0.5] * 20
    curve = survival_curve(trajectory, w0=1.0)
    for i in range(1, len(curve)):
        assert curve[i] <= curve[i - 1] + 1e-12


def test_survival_nondecreasing_if_wealth_growing():
    # Not guaranteed to decrease if W grows above W0 (hazard goes to near-zero)
    trajectory = [2.0] * 20
    curve = survival_curve(trajectory, w0=1.0)
    # Each increment should be tiny
    diffs = [curve[i + 1] - curve[i] for i in range(len(curve) - 1)]
    assert all(d <= 0 for d in diffs)


def test_survival_probability_empty():
    assert survival_probability([], w0=1.0) == 1.0


def test_survival_probability_decreases_with_horizon():
    traj_short = [0.8] * 10
    traj_long = [0.8] * 30
    s_short = survival_probability(traj_short, w0=1.0)
    s_long = survival_probability(traj_long, w0=1.0)
    assert s_long < s_short


def test_survival_probability_in_unit_interval():
    for n in [1, 5, 50, 200]:
        traj = [0.5] * n
        s = survival_probability(traj, w0=1.0)
        assert 0.0 <= s <= 1.0


def test_hazard_array_matches_scalar():
    w = np.array([0.5, 1.0, 2.0])
    h_arr = hazard_array(w, w0=1.0)
    for i in range(3):
        assert abs(h_arr[i] - hazard(w[i], w0=1.0)) < 1e-9
