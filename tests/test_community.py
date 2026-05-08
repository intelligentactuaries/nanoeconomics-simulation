"""Tests for single-community state machine."""
import numpy as np
import pytest

from src.community import CommunityConfig, TimeAllocation, initialize_community, step_community
from src.relational import RelationalConfig
from src.shocks import ShockEvent, ShockTarget, ShockType


def make_config(**kwargs) -> CommunityConfig:
    return CommunityConfig(**kwargs)


def test_time_allocation_normalizes():
    ta = TimeAllocation(production=2.0, family=1.0, religion=1.0, spatial_maintenance=1.0, leisure=0.0)
    total = ta.production + ta.family + ta.religion + ta.spatial_maintenance + ta.leisure
    assert abs(total - 1.0) < 1e-9


def test_time_allocation_zero_raises():
    with pytest.raises(Exception):
        TimeAllocation(production=0.0, family=0.0, religion=0.0, spatial_maintenance=0.0, leisure=0.0)


def test_initialize_community_creates_valid_state():
    config = make_config()
    state = initialize_community(config)
    assert state.alive
    assert state.m > 0
    assert state.w > 0
    assert state.year == 0.0


def test_m_grows_with_production():
    config = make_config(m_production_rate=0.10, m_maintenance_drain=0.0)
    state = initialize_community(config)
    m_before = state.m
    new_state = step_community(state, dt=1.0)
    assert new_state.m > m_before


def test_step_advances_year():
    config = make_config()
    state = initialize_community(config)
    new_state = step_community(state, dt=1.0)
    assert abs(new_state.year - 1.0) < 1e-9


def test_shock_reduces_material():
    config = make_config()
    state = initialize_community(config)
    m_before = state.m
    shock = ShockEvent(
        shock_type=ShockType.IDIOSYNCRATIC,
        target=ShockTarget.MATERIAL,
        severity=0.3,
        affected_indices=[0],
    )
    new_state = step_community(state, dt=1.0, shocks=[shock])
    assert new_state.m < m_before


def test_shock_reduces_family():
    config = make_config()
    state = initialize_community(config)
    f_before = state.relational.family_strength
    shock = ShockEvent(
        shock_type=ShockType.IDIOSYNCRATIC,
        target=ShockTarget.FAMILY,
        severity=0.5,
        affected_indices=[0],
    )
    new_state = step_community(state, dt=1.0, shocks=[shock])
    # Family should be lower (reduced by shock)
    assert new_state.relational.family_strength <= f_before


def test_dead_community_unchanged():
    config = make_config()
    state = initialize_community(config)
    state.alive = False
    state.m = 0.01
    new_state = step_community(state, dt=1.0)
    assert new_state.m == state.m


def test_r_contagion_pulls_toward_neighbor():
    config = make_config()
    state = initialize_community(config)
    r_before = state.relational.compute_r(config.relational_config)
    # Neighbor has high R
    new_state_high = step_community(state, dt=1.0, r_neighbor_avg=1.0, r_contagion_strength=0.5)
    r_high = new_state_high.relational.compute_r(config.relational_config)
    # Neighbor has low R
    new_state_low = step_community(state, dt=1.0, r_neighbor_avg=0.0, r_contagion_strength=0.5)
    r_low = new_state_low.relational.compute_r(config.relational_config)
    assert r_high >= r_low


def test_wealth_computed_from_state():
    config = make_config()
    state = initialize_community(config)
    assert state.w > 0
    assert isinstance(state.w, float)


def test_multiple_steps_deterministic():
    config = make_config()
    state1 = initialize_community(config)
    state2 = initialize_community(config)
    for _ in range(5):
        state1 = step_community(state1, dt=1.0)
        state2 = step_community(state2, dt=1.0)
    assert abs(state1.w - state2.w) < 1e-9
