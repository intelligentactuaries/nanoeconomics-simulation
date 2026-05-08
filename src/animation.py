"""Animation frame data structures for Plotly-based society visualization."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from .outcomes import Outcome, OUTCOME_COLORS
from .society import Society, SocietyConfig, SocietyMetrics
from .shocks import SHOCK_ENVIRONMENTS, ShockGenerator


@dataclass
class AnimationFrame:
    year: float
    node_colors: list[str]
    node_sizes: list[float]
    edge_widths: list[float]
    edge_colors: list[str]
    metrics: SocietyMetrics
    interim_outcomes: list[Outcome]

    # For status distribution chart (frame-by-frame)
    outcome_counts: dict[str, int] = field(default_factory=dict)


@dataclass
class SocietyAnimationResult:
    frames: list[AnimationFrame]
    positions: np.ndarray
    graph_edges: list[tuple[int, int]]
    community_names: list[str]
    final_outcomes: list[Outcome]
    config: SocietyConfig
    society: Society


def _outcome_to_color(outcome: Outcome) -> str:
    return OUTCOME_COLORS.get(outcome, OUTCOME_COLORS[Outcome.IN_PROGRESS])


def _pop_to_size(population: float) -> float:
    return float(10 + 20 * np.log(max(population, 100)) / np.log(5000))


def run_society_with_frames(config: SocietyConfig) -> SocietyAnimationResult:
    """Run society simulation, collecting one animation frame per time step."""
    seed = config.seed if config.seed is not None else 0
    rng = np.random.default_rng(seed)

    society = Society(config, rng)
    shock_env = SHOCK_ENVIRONMENTS.get(config.shock_environment, SHOCK_ENVIRONMENTS["moderate"])

    # Apply custom shock topology if specified
    if config.shock_topology:
        from .shocks import ShockEnvironment
        shock_env = ShockEnvironment(
            annual_shock_probability=shock_env.annual_shock_probability,
            mean_severity=shock_env.mean_severity,
            severity_std=shock_env.severity_std,
            p_local=config.shock_topology.get("local", shock_env.p_local),
            p_regional=config.shock_topology.get("regional", shock_env.p_regional),
            p_global=config.shock_topology.get("global", shock_env.p_global),
            p_idiosyncratic=config.shock_topology.get("idiosyncratic", shock_env.p_idiosyncratic),
        )

    shock_gen = ShockGenerator(shock_env, rng)
    n_steps = int(config.horizon / config.dt)
    frames: list[AnimationFrame] = []
    n = len(society.communities)
    edges = list(society.graph.edges())

    for step_i in range(n_steps):
        year = step_i * config.dt
        metrics = society.step(year, config.dt, shock_gen)

        interim_outcomes = [
            society.classifier.classify_interim(society.w_histories[i], society.w0s[i])
            for i in range(n)
        ]
        node_colors = [_outcome_to_color(o) for o in interim_outcomes]
        node_sizes = [_pop_to_size(c.population) for c in society.communities]

        # Edge width from recent trade (proportional to product of wealth)
        w_arr = np.array([c.w for c in society.communities])
        edge_widths = []
        edge_colors_list = []
        for (i, j) in edges:
            w_prod = w_arr[i] * w_arr[j]
            edge_widths.append(float(np.clip(w_prod * 2.0, 0.3, 5.0)))
            edge_colors_list.append("#94a3b8")  # neutral slate

        outcome_counts = {
            "collapsed": metrics.n_collapsed,
            "grew": metrics.n_grew,
            "stabilized": metrics.n_stabilized,
            "declined": metrics.n_declined,
            "in_progress": metrics.n_in_progress,
        }

        frame = AnimationFrame(
            year=metrics.year,
            node_colors=node_colors,
            node_sizes=node_sizes,
            edge_widths=edge_widths,
            edge_colors=edge_colors_list,
            metrics=metrics,
            interim_outcomes=interim_outcomes,
            outcome_counts=outcome_counts,
        )
        frames.append(frame)

    final_outcomes = society.final_outcomes()
    community_names = [cfg.name for cfg in society.configs]

    return SocietyAnimationResult(
        frames=frames,
        positions=society.positions,
        graph_edges=edges,
        community_names=community_names,
        final_outcomes=final_outcomes,
        config=config,
        society=society,
    )
