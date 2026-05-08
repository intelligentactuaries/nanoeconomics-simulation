"""Tests for outcome classification."""
import pytest

from src.outcomes import (
    CommunityResult,
    Outcome,
    OutcomeClassifier,
    OutcomeThresholds,
    compute_gini,
)


def make_result(w_history: list[float], w0: float = 1.0) -> CommunityResult:
    return CommunityResult(
        w_history=w_history,
        w0=w0,
        years=list(range(len(w_history))),
        alive_history=[True] * len(w_history),
    )


def test_classify_grew():
    clf = OutcomeClassifier()
    result = make_result([1.0] * 5 + [1.5])  # ends 50% above W0
    assert clf.classify(result) == Outcome.GREW


def test_classify_stabilized():
    clf = OutcomeClassifier()
    result = make_result([1.0, 1.02, 0.99, 1.01, 1.03])
    assert clf.classify(result) == Outcome.STABILIZED


def test_classify_declined():
    clf = OutcomeClassifier()
    result = make_result([1.0, 0.9, 0.85, 0.80, 0.78])  # fell but not collapsed
    assert clf.classify(result) == Outcome.DECLINED


def test_classify_collapsed():
    clf = OutcomeClassifier()
    # W stays below 0.3 * W0 for > 5 periods
    result = make_result([1.0, 0.5, 0.2, 0.1, 0.1, 0.1, 0.1, 0.1])
    assert clf.classify(result) == Outcome.COLLAPSED


def test_collapse_requires_sustained_duration():
    clf = OutcomeClassifier(OutcomeThresholds(recovery_window=5))
    # Below threshold only 3 periods < 5
    result = make_result([1.0, 0.2, 0.2, 0.2, 1.0, 1.0])
    assert clf.classify(result) != Outcome.COLLAPSED


def test_collapse_recovery_window_exact():
    t = OutcomeThresholds(recovery_window=3, collapse_threshold=0.3)
    clf = OutcomeClassifier(t)
    # Exactly 3 periods below → collapsed
    result = make_result([1.0, 0.2, 0.2, 0.2])
    assert clf.classify(result) == Outcome.COLLAPSED
    # Only 2 periods → not collapsed
    result2 = make_result([1.0, 0.2, 0.2, 1.0])
    assert clf.classify(result2) != Outcome.COLLAPSED


def test_custom_thresholds():
    t = OutcomeThresholds(growth_threshold=0.05, stability_band=0.02)
    clf = OutcomeClassifier(t)
    result = make_result([1.0, 1.06])  # 6% above W0, threshold=5%
    assert clf.classify(result) == Outcome.GREW


def test_empty_history():
    clf = OutcomeClassifier()
    result = make_result([])
    outcome = clf.classify(result)
    assert outcome in list(Outcome)


def test_single_step():
    clf = OutcomeClassifier()
    result = make_result([2.0])
    assert clf.classify(result) == Outcome.GREW


def test_classify_interim_in_progress_early():
    clf = OutcomeClassifier()
    outcome = clf.classify_interim([1.0, 1.01], w0=1.0)
    assert outcome == Outcome.IN_PROGRESS


def test_classify_interim_collapsed():
    clf = OutcomeClassifier()
    w_hist = [1.0] + [0.1] * 10
    outcome = clf.classify_interim(w_hist, w0=1.0)
    assert outcome == Outcome.COLLAPSED


def test_gini_all_equal():
    assert abs(compute_gini([1.0, 1.0, 1.0, 1.0])) < 1e-9


def test_gini_maximum_inequality():
    # One community has everything
    g = compute_gini([0, 0, 0, 4.0])
    assert g > 0.7


def test_gini_bounded():
    import numpy as np
    rng = np.random.default_rng(42)
    for _ in range(20):
        vals = list(rng.exponential(1.0, 10))
        g = compute_gini(vals)
        assert 0.0 <= g <= 1.0


def test_gini_empty():
    assert compute_gini([]) == 0.0


def test_outcome_colors_defined():
    from src.outcomes import OUTCOME_COLORS
    for o in [Outcome.COLLAPSED, Outcome.GREW, Outcome.STABILIZED, Outcome.DECLINED]:
        assert o in OUTCOME_COLORS
        assert OUTCOME_COLORS[o].startswith("#")
