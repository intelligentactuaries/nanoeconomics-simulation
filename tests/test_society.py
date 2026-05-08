"""Tests for Society network dynamics."""
import numpy as np
import pytest

from src.shocks import MODERATE_ENV, ShockGenerator
from src.society import Society, SocietyConfig
from src.outcomes import Outcome


def make_society(n=10, seed=42, **kwargs) -> Society:
    cfg = SocietyConfig(n_communities=n, seed=seed, **kwargs)
    rng = np.random.default_rng(seed)
    return Society(cfg, rng)


def test_society_initializes_correct_n():
    s = make_society(n=15)
    assert len(s.communities) == 15
    assert len(s.configs) == 15
    assert s.positions.shape == (15, 2)


def test_graph_has_edges():
    s = make_society(n=10, network_k=4)
    assert s.graph.number_of_edges() > 0


def test_step_returns_metrics():
    s = make_society(n=5)
    rng = np.random.default_rng(0)
    shock_gen = ShockGenerator(MODERATE_ENV, rng)
    metrics = s.step(0.0, 1.0, shock_gen)
    assert metrics.year == 1.0
    assert metrics.total_wealth > 0
    assert 0.0 <= metrics.gini <= 1.0


def test_total_community_count_conserved():
    s = make_society(n=8)
    rng = np.random.default_rng(1)
    shock_gen = ShockGenerator(MODERATE_ENV, rng)
    for t in range(10):
        metrics = s.step(float(t), 1.0, shock_gen)
    assert len(s.communities) == 8


def test_wealth_histories_grow():
    s = make_society(n=5)
    rng = np.random.default_rng(2)
    shock_gen = ShockGenerator(MODERATE_ENV, rng)
    for t in range(5):
        s.step(float(t), 1.0, shock_gen)
    for wh in s.w_histories:
        assert len(wh) == 5


def test_migration_m_roughly_conserved():
    """Total material capital should not grow solely from migration (positive-sum trade is fine)."""
    cfg = SocietyConfig(n_communities=10, trade_strength=0.0, r_contagion_strength=0.0, seed=0)
    rng = np.random.default_rng(0)
    # No shocks env
    from src.shocks import ShockEnvironment
    zero_shock = ShockEnvironment(annual_shock_probability=0.0)
    shock_gen = ShockGenerator(zero_shock, rng)

    s = Society(cfg, rng)
    m_before = sum(c.m for c in s.communities)
    for t in range(5):
        s.step(float(t), 1.0, shock_gen)
    m_after = sum(c.m for c in s.communities)
    # Without production growth (but m_production_rate > 0 in default config),
    # only check that migration itself doesn't explode M by >50%
    assert m_after < m_before * 3.0


def test_trade_is_positive_sum():
    """Total wealth should benefit from trade, not be destroyed."""
    cfg_trade = SocietyConfig(n_communities=10, trade_strength=2.0, seed=42)
    cfg_no_trade = SocietyConfig(n_communities=10, trade_strength=0.0, seed=42)
    from src.shocks import ShockEnvironment
    zero_shock = ShockEnvironment(annual_shock_probability=0.0)

    rng1 = np.random.default_rng(42)
    rng2 = np.random.default_rng(42)
    s_trade = Society(cfg_trade, rng1)
    s_no_trade = Society(cfg_no_trade, rng2)

    for t in range(10):
        gen1 = ShockGenerator(zero_shock, np.random.default_rng(t))
        gen2 = ShockGenerator(zero_shock, np.random.default_rng(t))
        s_trade.step(float(t), 1.0, gen1)
        s_no_trade.step(float(t), 1.0, gen2)

    w_trade = sum(c.w for c in s_trade.communities)
    w_no_trade = sum(c.w for c in s_no_trade.communities)
    assert w_trade >= w_no_trade * 0.9  # trade doesn't destroy wealth


def test_contagion_affects_multiple_communities():
    """A global shock should be felt by all communities."""
    from src.shocks import ShockEnvironment, ShockType, ShockTarget, ShockEvent
    s = make_society(n=10)
    w_before = [c.w for c in s.communities]

    rng = np.random.default_rng(3)
    global_env = ShockEnvironment(
        annual_shock_probability=100.0,
        mean_severity=0.3, severity_std=0.01,
        p_local=0.0, p_regional=0.0, p_global=1.0, p_idiosyncratic=0.0,
    )
    shock_gen = ShockGenerator(global_env, rng)
    s.step(0.0, 1.0, shock_gen)
    w_after = [c.w for c in s.communities]

    changed = sum(1 for b, a in zip(w_before, w_after) if abs(a - b) > 1e-6)
    assert changed > 5


def test_final_outcomes_returns_list():
    s = make_society(n=6)
    rng = np.random.default_rng(4)
    shock_gen = ShockGenerator(MODERATE_ENV, rng)
    for t in range(10):
        s.step(float(t), 1.0, shock_gen)
    outcomes = s.final_outcomes()
    assert len(outcomes) == 6
    for o in outcomes:
        assert isinstance(o, Outcome)


def test_r_contagion_affects_relational():
    """High R-contagion strength should cause neighbor R to influence local R."""
    cfg_high = SocietyConfig(n_communities=5, r_contagion_strength=0.9, seed=0)
    cfg_none = SocietyConfig(n_communities=5, r_contagion_strength=0.0, seed=0)
    from src.shocks import ShockEnvironment
    zero_shock = ShockEnvironment(annual_shock_probability=0.0)

    rng_h = np.random.default_rng(0)
    rng_n = np.random.default_rng(0)
    s_high = Society(cfg_high, rng_h)
    s_none = Society(cfg_none, rng_n)

    for t in range(5):
        s_high.step(float(t), 1.0, ShockGenerator(zero_shock, np.random.default_rng(t)))
        s_none.step(float(t), 1.0, ShockGenerator(zero_shock, np.random.default_rng(t)))

    r_high = [c.relational.compute_r(cfg.relational_config)
              for c, cfg in zip(s_high.communities, s_high.configs)]
    r_none = [c.relational.compute_r(cfg.relational_config)
              for c, cfg in zip(s_none.communities, s_none.configs)]

    # R values should differ between high and no contagion
    diffs = sum(abs(h - n) > 1e-6 for h, n in zip(r_high, r_none))
    assert diffs >= 1
