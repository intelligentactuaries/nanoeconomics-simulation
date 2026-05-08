"""Outcome classification for community simulation results."""
from __future__ import annotations

from enum import Enum
from typing import Optional

import numpy as np
from pydantic import BaseModel, Field


class Outcome(str, Enum):
    COLLAPSED = "collapsed"
    GREW = "grew"
    STABILIZED = "stabilized"
    DECLINED = "declined"
    IN_PROGRESS = "in_progress"


OUTCOME_COLORS = {
    Outcome.COLLAPSED: "#dc2626",   # red
    Outcome.GREW: "#16a34a",        # green
    Outcome.STABILIZED: "#2563eb",  # blue
    Outcome.DECLINED: "#d97706",    # amber
    Outcome.IN_PROGRESS: "#9ca3af", # grey
}


class OutcomeThresholds(BaseModel):
    collapse_threshold: float = Field(
        default=0.3,
        gt=0.0, lt=1.0,
        description="W/W0 ratio below which community is considered collapsed",
    )
    recovery_window: int = Field(
        default=5,
        gt=0,
        description="Consecutive periods below collapse threshold to declare collapse",
    )
    growth_threshold: float = Field(
        default=0.20,
        gt=0.0,
        description="Minimum fractional W gain (above W0) to classify as grew",
    )
    stability_band: float = Field(
        default=0.10,
        gt=0.0,
        description="Max fractional deviation from W0 for stabilized",
    )


class CommunityResult(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    w_history: list[float]
    w0: float
    years: list[float]
    alive_history: list[bool]
    outcome: Optional[Outcome] = None


class OutcomeClassifier:
    def __init__(self, thresholds: Optional[OutcomeThresholds] = None) -> None:
        self.thresholds = thresholds or OutcomeThresholds()

    def classify(self, result: CommunityResult) -> Outcome:
        """Classify a community's outcome from its wealth history."""
        w_hist = result.w_history
        w0 = result.w0

        if not w_hist or w0 <= 0:
            return Outcome.DECLINED

        t = self.thresholds
        w_final = w_hist[-1]

        # Check collapse: W < tau_c * W0 for duration > recovery_window
        if self._is_collapsed(w_hist, w0, t):
            return Outcome.COLLAPSED

        # Check growth
        if w_final > w0 * (1 + t.growth_threshold):
            return Outcome.GREW

        # Check stability
        if abs(w_final - w0) / w0 <= t.stability_band:
            return Outcome.STABILIZED

        # Otherwise declined (fell but not collapsed)
        return Outcome.DECLINED

    def _is_collapsed(
        self,
        w_hist: list[float],
        w0: float,
        t: OutcomeThresholds,
    ) -> bool:
        """Check if community collapsed (sustained W below threshold)."""
        collapse_floor = w0 * t.collapse_threshold
        consecutive = 0
        max_consecutive = 0
        for w in w_hist:
            if w < collapse_floor:
                consecutive += 1
                max_consecutive = max(max_consecutive, consecutive)
            else:
                consecutive = 0
        return max_consecutive >= t.recovery_window

    def classify_interim(self, w_hist_so_far: list[float], w0: float) -> Outcome:
        """Quick classification for animation frames (in-progress if ambiguous)."""
        if not w_hist_so_far:
            return Outcome.IN_PROGRESS

        t = self.thresholds
        w_current = w_hist_so_far[-1]
        collapse_floor = w0 * t.collapse_threshold

        if self._is_collapsed(w_hist_so_far, w0, t):
            return Outcome.COLLAPSED

        if len(w_hist_so_far) < t.recovery_window * 2:
            return Outcome.IN_PROGRESS

        if w_current > w0 * (1 + t.growth_threshold):
            return Outcome.GREW

        if abs(w_current - w0) / w0 <= t.stability_band:
            return Outcome.STABILIZED

        if w_current < w0:
            return Outcome.DECLINED

        return Outcome.IN_PROGRESS


def compute_gini(values: list[float]) -> float:
    """Gini coefficient for a list of wealth values."""
    if not values or all(v == 0 for v in values):
        return 0.0
    arr = np.sort(np.array(values, dtype=float))
    n = len(arr)
    if n == 0 or arr.sum() == 0:
        return 0.0
    index = np.arange(1, n + 1)
    return float((2 * np.sum(index * arr) - (n + 1) * arr.sum()) / (n * arr.sum()))
