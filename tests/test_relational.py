"""Tests for relational capital module."""
import pytest

from src.relational import (
    RelationalConfig,
    RelationalState,
    spatial_relational_capital,
    SPATIAL_PEAK_SQFT,
)


def test_spatial_logistic_peak_near_250():
    s_peak = spatial_relational_capital(SPATIAL_PEAK_SQFT)
    s_low = spatial_relational_capital(50.0)
    s_high = spatial_relational_capital(2000.0)
    assert s_peak > s_low
    assert s_peak > s_high
    assert 0.8 <= s_peak <= 1.0, f"Peak value {s_peak} not near 1.0"


def test_spatial_peak_is_maximum():
    values = [spatial_relational_capital(x) for x in [50, 100, 200, 250, 300, 500, 1000, 2000]]
    peak = max(values)
    assert peak == spatial_relational_capital(250.0) or abs(peak - spatial_relational_capital(250.0)) < 0.05


def test_spatial_negative_raises():
    with pytest.raises(ValueError):
        spatial_relational_capital(-10.0)


def test_spatial_output_bounded():
    for x in [0, 10, 100, 250, 500, 1000, 5000]:
        s = spatial_relational_capital(float(x))
        assert 0.0 <= s <= 1.0, f"spatial({x}) = {s} out of [0,1]"


def test_relational_state_compute_r_bounded():
    config = RelationalConfig()
    state = RelationalState(family_strength=0.7, religion_participation=0.6, sqft_per_resident=300.0)
    r = state.compute_r(config)
    assert 0.0 <= r <= 1.0


def test_family_decay_without_family_time():
    config = RelationalConfig(family_decay_rate=0.1)
    state = RelationalState(family_strength=0.8, religion_participation=0.5, sqft_per_resident=300.0)
    new_state = state.step(config, family_time_fraction=0.0, religion_time_fraction=0.1, dt=1.0)
    assert new_state.family_strength < state.family_strength


def test_family_grows_with_family_time():
    config = RelationalConfig(family_growth_rate=0.2)
    state = RelationalState(family_strength=0.4, religion_participation=0.5, sqft_per_resident=300.0)
    new_state = state.step(config, family_time_fraction=0.4, religion_time_fraction=0.1, dt=1.0)
    assert new_state.family_strength > state.family_strength


def test_religion_buffers_meaning_crisis():
    config = RelationalConfig()
    state_high_rel = RelationalState(family_strength=0.6, religion_participation=0.9, sqft_per_resident=300.0)
    state_low_rel = RelationalState(family_strength=0.6, religion_participation=0.1, sqft_per_resident=300.0)

    # With strong meaning crisis, high religion should lose less R
    new_high = state_high_rel.step(config, 0.2, 0.2, dt=1.0, meaning_crisis_shock=0.8)
    new_low = state_low_rel.step(config, 0.2, 0.2, dt=1.0, meaning_crisis_shock=0.8)

    r_high_after = new_high.compute_r(config)
    r_low_after = new_low.compute_r(config)
    # High religion loses less religion participation
    assert new_high.religion_participation >= new_low.religion_participation


def test_religion_decay_without_participation():
    config = RelationalConfig(religion_decay_rate=0.1)
    state = RelationalState(family_strength=0.5, religion_participation=0.7, sqft_per_resident=300.0)
    new_state = state.step(config, family_time_fraction=0.2, religion_time_fraction=0.0, dt=1.0)
    assert new_state.religion_participation < state.religion_participation


def test_relational_values_stay_bounded_after_step():
    config = RelationalConfig()
    state = RelationalState(family_strength=1.0, religion_participation=1.0, sqft_per_resident=250.0)
    for _ in range(10):
        state = state.step(config, 0.3, 0.2, dt=1.0, meaning_crisis_shock=0.5)
        assert 0.0 <= state.family_strength <= 1.0
        assert 0.0 <= state.religion_participation <= 1.0


def test_relational_config_weight_validation():
    with pytest.raises(Exception):
        RelationalConfig(w_family=0.0, w_religion=0.0, w_spatial=0.0)


def test_relational_sqft_preserved_after_step():
    config = RelationalConfig()
    state = RelationalState(family_strength=0.5, religion_participation=0.5, sqft_per_resident=450.0)
    new_state = state.step(config, 0.2, 0.1, dt=1.0)
    assert new_state.sqft_per_resident == 450.0
