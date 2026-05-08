"""Tests for single-community and society simulation orchestration."""
import numpy as np
import pytest

from src.community import CommunityConfig
from src.outcomes import Outcome
from src.simulation import SingleCommunityConfig, run_single_community
from src.society import SocietyConfig
from src.animation import run_society_with_frames


# ─────────────────────────────────────────────────────────────
# Single community tests
# ─────────────────────────────────────────────────────────────

def make_config(**kwargs) -> SingleCommunityConfig:
    return SingleCommunityConfig(**kwargs)


def test_run_produces_correct_path_count():
    cfg = make_config(n_paths=50, horizon=10, seed=42)
    result = run_single_community(cfg)
    assert result.n_paths == 50


def test_trajectories_have_correct_length():
    cfg = make_config(n_paths=10, horizon=20, seed=1)
    result = run_single_community(cfg)
    for path in result.paths:
        assert len(path.w_history) == 20
        assert len(path.years) == 20
        assert len(path.survival_curve) == 20


def test_reproducibility():
    cfg = make_config(n_paths=30, horizon=15, seed=7)
    r1 = run_single_community(cfg)
    r2 = run_single_community(cfg)
    for i in range(30):
        for j in range(15):
            assert abs(r1.paths[i].w_history[j] - r2.paths[i].w_history[j]) < 1e-12


def test_different_seeds_differ():
    cfg1 = make_config(n_paths=20, horizon=10, seed=0)
    cfg2 = make_config(n_paths=20, horizon=10, seed=99)
    r1 = run_single_community(cfg1)
    r2 = run_single_community(cfg2)
    diffs = sum(
        abs(r1.paths[0].w_history[i] - r2.paths[0].w_history[i]) > 1e-6
        for i in range(10)
    )
    assert diffs > 0


def test_all_outcomes_are_valid():
    cfg = make_config(n_paths=50, horizon=30, seed=42)
    result = run_single_community(cfg)
    valid = set(Outcome) - {Outcome.IN_PROGRESS}
    for path in result.paths:
        assert path.outcome in valid


def test_outcome_fractions_sum_to_one():
    cfg = make_config(n_paths=100, horizon=30, seed=10)
    result = run_single_community(cfg)
    fracs = result.outcome_fractions()
    assert abs(sum(fracs.values()) - 1.0) < 1e-9


def test_mean_trajectory_same_length():
    cfg = make_config(n_paths=30, horizon=25, seed=5)
    result = run_single_community(cfg)
    mean = result.mean_trajectory()
    assert len(mean) == 25


def test_survival_curve_decreasing_on_average():
    cfg = make_config(n_paths=50, horizon=20, seed=3, shock_environment="severe")
    result = run_single_community(cfg)
    mean_surv = result.mean_survival_curve()
    for i in range(1, len(mean_surv)):
        assert mean_surv[i] <= mean_surv[i - 1] + 1e-9


def test_mild_survives_better_than_severe():
    base_community = CommunityConfig()
    cfg_mild = make_config(community=base_community, n_paths=100, horizon=30, seed=42, shock_environment="mild")
    cfg_severe = make_config(community=base_community, n_paths=100, horizon=30, seed=42, shock_environment="severe")
    r_mild = run_single_community(cfg_mild)
    r_severe = run_single_community(cfg_severe)
    mild_mean_surv = r_mild.mean_survival_curve()[-1]
    severe_mean_surv = r_severe.mean_survival_curve()[-1]
    assert mild_mean_surv > severe_mean_surv


def test_w0_recorded():
    cfg = make_config(n_paths=10, horizon=5, seed=0)
    result = run_single_community(cfg)
    assert result.w0 > 0


def test_dominant_outcome_is_valid():
    cfg = make_config(n_paths=50, horizon=30, seed=42)
    result = run_single_community(cfg)
    dom = result.dominant_outcome()
    assert dom in list(Outcome)


# ─────────────────────────────────────────────────────────────
# Society animation tests
# ─────────────────────────────────────────────────────────────

def make_society_cfg(**kwargs) -> SocietyConfig:
    return SocietyConfig(**kwargs)


def test_society_animation_frames_count():
    cfg = make_society_cfg(n_communities=10, horizon=15, seed=1)
    result = run_society_with_frames(cfg)
    assert len(result.frames) == 15


def test_society_animation_reproducible():
    cfg = make_society_cfg(n_communities=8, horizon=10, seed=5)
    r1 = run_society_with_frames(cfg)
    r2 = run_society_with_frames(cfg)
    for i in range(len(r1.frames)):
        assert abs(r1.frames[i].metrics.total_wealth - r2.frames[i].metrics.total_wealth) < 1e-9


def test_society_animation_node_colors_count():
    cfg = make_society_cfg(n_communities=12, horizon=5, seed=0)
    result = run_society_with_frames(cfg)
    for frame in result.frames:
        assert len(frame.node_colors) == 12


def test_society_animation_final_outcomes_count():
    cfg = make_society_cfg(n_communities=7, horizon=5, seed=3)
    result = run_society_with_frames(cfg)
    assert len(result.final_outcomes) == 7
    for o in result.final_outcomes:
        assert isinstance(o, Outcome)


def test_society_animation_metrics_year_sequence():
    cfg = make_society_cfg(n_communities=5, horizon=10, seed=2)
    result = run_society_with_frames(cfg)
    years = [f.metrics.year for f in result.frames]
    for i in range(1, len(years)):
        assert years[i] > years[i - 1]


def test_society_animation_outcome_counts_sum_to_n():
    cfg = make_society_cfg(n_communities=20, horizon=10, seed=9)
    result = run_society_with_frames(cfg)
    for frame in result.frames:
        total = sum(frame.outcome_counts.values())
        assert total == 20
