"""Nanoeconomics Survival Simulation — Gradio application entry point."""
from __future__ import annotations

import time
from typing import Optional

import gradio as gr
import numpy as np
import plotly.graph_objects as go

from src.animation import SocietyAnimationResult, run_society_with_frames
from src.community import CommunityConfig, TimeAllocation
from src.outcomes import OUTCOME_COLORS, Outcome, OutcomeThresholds
from src.relational import RelationalConfig
from src.simulation import SingleCommunityConfig, run_single_community
from src.society import SocietyConfig


# ─────────────────────────────────────────────────────────────
# Helper builders
# ─────────────────────────────────────────────────────────────

def build_community_config(
    population: int,
    sqft_per_resident: float,
    alpha_m: float,
    alpha_t: float,
    alpha_r: float,
    w_family: float,
    w_religion: float,
    w_spatial: float,
    p_production: float,
    p_family: float,
    p_religion: float,
    p_spatial_maint: float,
    p_leisure: float,
    family_strength_init: float,
    religion_init: float,
) -> CommunityConfig:
    return CommunityConfig(
        population=int(np.clip(population, 100, 5000)),
        sqft_per_resident=float(sqft_per_resident),
        alpha_m=float(alpha_m),
        alpha_t=float(alpha_t),
        alpha_r=float(alpha_r),
        relational_config=RelationalConfig(
            w_family=float(w_family),
            w_religion=float(w_religion),
            w_spatial=float(w_spatial),
        ),
        time_allocation=TimeAllocation(
            production=float(p_production),
            family=float(p_family),
            religion=float(p_religion),
            spatial_maintenance=float(p_spatial_maint),
            leisure=float(p_leisure),
        ),
    )


def _animated_fig_to_html(fig: go.Figure, height: int = 480) -> str:
    """Render an animated Plotly figure as standalone HTML.

    gr.Plot serializes figures via Plotly.react(), which does not preserve
    animation frames — clicking play in such figures fails silently. Rendering
    via to_html() uses Plotly.newPlot() and registers frames properly, so the
    play button and slider work as expected.
    """
    return fig.to_html(
        include_plotlyjs='cdn',
        full_html=False,
        default_height=f'{height}px',
        config={'displayModeBar': False, 'responsive': True},
    )


def _outcome_badge_html(outcome: Outcome, fraction: float) -> str:
    color = OUTCOME_COLORS.get(outcome, "#9ca3af")
    label = outcome.value.upper()
    return f"""
    <div style="text-align:center; margin: 12px 0;">
      <span style="
        background-color: {color};
        color: white;
        font-size: 2em;
        font-weight: 800;
        padding: 14px 36px;
        border-radius: 8px;
        display: inline-block;
        letter-spacing: 2px;
      ">{label}</span>
      <p style="margin-top:8px; color:#6b7280; font-size:0.95em;">
        {fraction*100:.0f}% of paths ended with this outcome
      </p>
    </div>
    """


def _make_trajectory_fig(result) -> go.Figure:
    years = result.paths[0].years
    mean_w = result.mean_trajectory()
    p10 = result.percentile_trajectory(10)
    p25 = result.percentile_trajectory(25)
    p75 = result.percentile_trajectory(75)
    p90 = result.percentile_trajectory(90)
    w0 = result.w0

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=years + years[::-1], y=p90 + p10[::-1],
                             fill='toself', fillcolor='rgba(59,130,246,0.1)',
                             line=dict(color='rgba(0,0,0,0)'), name='10–90th pct', showlegend=True))
    fig.add_trace(go.Scatter(x=years + years[::-1], y=p75 + p25[::-1],
                             fill='toself', fillcolor='rgba(59,130,246,0.2)',
                             line=dict(color='rgba(0,0,0,0)'), name='25–75th pct', showlegend=True))
    fig.add_trace(go.Scatter(x=years, y=mean_w, line=dict(color='#2563eb', width=2.5),
                             name='Mean wealth'))
    fig.add_hline(y=w0, line_dash='dash', line_color='#9ca3af', annotation_text='W₀')
    fig.update_layout(
        title='Wealth Trajectory (W/W₀ units)',
        xaxis_title='Year', yaxis_title='W',
        template='plotly_white', height=320,
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
    )
    return fig


def _make_survival_fig(result) -> go.Figure:
    years = result.paths[0].years
    mean_surv = result.mean_survival_curve()
    p10_s = [np.percentile([p.survival_curve[i] for p in result.paths], 10) for i in range(len(years))]
    p90_s = [np.percentile([p.survival_curve[i] for p in result.paths], 90) for i in range(len(years))]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=years + years[::-1], y=p90_s + p10_s[::-1],
                             fill='toself', fillcolor='rgba(22,163,74,0.12)',
                             line=dict(color='rgba(0,0,0,0)'), name='10–90th pct'))
    fig.add_trace(go.Scatter(x=years, y=mean_surv, line=dict(color='#16a34a', width=2.5),
                             name='Mean survival'))
    fig.update_layout(
        title='Survival Probability S(t)',
        xaxis_title='Year', yaxis_title='S(t)',
        yaxis=dict(range=[0, 1.05]),
        template='plotly_white', height=280,
    )
    return fig


def _make_components_fig(result) -> go.Figure:
    years = result.paths[0].years
    mean_m = [np.mean([p.m_history[i] for p in result.paths]) for i in range(len(years))]
    mean_t = [np.mean([p.t_history[i] for p in result.paths]) for i in range(len(years))]
    mean_r = [np.mean([p.r_history[i] for p in result.paths]) for i in range(len(years))]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=years, y=mean_m, name='M (material)', line=dict(color='#f59e0b')))
    fig.add_trace(go.Scatter(x=years, y=mean_t, name='T (time)', line=dict(color='#6366f1')))
    fig.add_trace(go.Scatter(x=years, y=mean_r, name='R (relational)', line=dict(color='#ec4899')))
    fig.update_layout(
        title='M / T / R Component Trajectories (mean across paths)',
        xaxis_title='Year', yaxis_title='Value',
        template='plotly_white', height=280,
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
    )
    return fig


def _make_outcome_bar(fractions: dict) -> go.Figure:
    labels = ['Grew', 'Stabilized', 'Declined', 'Collapsed']
    outcomes = [Outcome.GREW, Outcome.STABILIZED, Outcome.DECLINED, Outcome.COLLAPSED]
    colors = [OUTCOME_COLORS[o] for o in outcomes]
    values = [fractions.get(o, 0) * 100 for o in outcomes]

    fig = go.Figure(go.Bar(
        x=labels, y=values, marker_color=colors,
        text=[f'{v:.0f}%' for v in values], textposition='auto',
    ))
    fig.update_layout(
        title='Outcome Distribution (% of paths)',
        yaxis=dict(title='% of paths', range=[0, 105]),
        template='plotly_white', height=260,
    )
    return fig


# ─────────────────────────────────────────────────────────────
# Tab 1: Single Community
# ─────────────────────────────────────────────────────────────

def run_single_community_tab(
    population, sqft_per_resident, alpha_m, alpha_t, alpha_r,
    w_family, w_religion, w_spatial,
    p_production, p_family_t, p_religion_t, p_spatial_maint, p_leisure,
    family_init, religion_init,
    shock_env_name, horizon, n_paths, seed,
    collapse_threshold, growth_threshold, stability_band, recovery_window,
):
    t0 = time.time()
    try:
        community = build_community_config(
            population, sqft_per_resident,
            alpha_m, alpha_t, alpha_r,
            w_family, w_religion, w_spatial,
            p_production, p_family_t, p_religion_t, p_spatial_maint, p_leisure,
            family_init, religion_init,
        )
        thresholds = OutcomeThresholds(
            collapse_threshold=float(collapse_threshold),
            growth_threshold=float(growth_threshold),
            stability_band=float(stability_band),
            recovery_window=int(recovery_window),
        )
        cfg = SingleCommunityConfig(
            community=community,
            shock_environment=shock_env_name,
            horizon=int(horizon),
            n_paths=int(n_paths),
            dt=1.0,
            seed=int(seed),
            thresholds=thresholds,
        )
        result = run_single_community(cfg)

        fracs = result.outcome_fractions()
        dominant = result.dominant_outcome()
        dom_frac = fracs.get(dominant, 0.0)

        elapsed = time.time() - t0
        summary = (
            f"**{int(n_paths)} Monte Carlo paths | {int(horizon)}-year horizon | "
            f"Shock: {shock_env_name} | Elapsed: {elapsed:.1f}s**\n\n"
            f"| Outcome | Fraction |\n|---------|----------|\n"
            + "\n".join(f"| {o.value.capitalize()} | {v*100:.1f}% |" for o, v in sorted(fracs.items(), key=lambda x: x[0].value))
        )

        return (
            _make_trajectory_fig(result),
            _make_survival_fig(result),
            _make_components_fig(result),
            _make_outcome_bar(fracs),
            _outcome_badge_html(dominant, dom_frac),
            summary,
        )
    except Exception as e:
        empty = go.Figure()
        return empty, empty, empty, empty, f"<p style='color:red'>Error: {e}</p>", str(e)


# ─────────────────────────────────────────────────────────────
# Tab 2: Society Mode
# ─────────────────────────────────────────────────────────────

def _build_society_animation(result: SocietyAnimationResult) -> go.Figure:
    """Build Plotly figure with frames for animated society network."""
    positions = result.positions
    edges = result.graph_edges
    n = len(positions)
    names = result.community_names

    def make_network_traces(frame_data):
        traces = []
        # Edge traces
        for (i, j), ew, ec in zip(edges, frame_data.edge_widths, frame_data.edge_colors):
            traces.append(go.Scatter(
                x=[positions[i, 0], positions[j, 0], None],
                y=[positions[i, 1], positions[j, 1], None],
                mode='lines',
                line=dict(width=ew, color=ec),
                hoverinfo='none', showlegend=False,
            ))
        # Node trace
        traces.append(go.Scatter(
            x=positions[:, 0], y=positions[:, 1],
            mode='markers+text',
            marker=dict(
                size=frame_data.node_sizes,
                color=frame_data.node_colors,
                line=dict(width=1, color='white'),
            ),
            text=[f'C{i}' for i in range(n)],
            textposition='top center',
            hovertext=names,
            hoverinfo='text',
            showlegend=False,
        ))
        return traces

    # Initial frame
    f0 = result.frames[0]
    initial_traces = make_network_traces(f0)

    fig = go.Figure(data=initial_traces)

    # Build animation frames
    anim_frames = []
    for frame_data in result.frames:
        frame_traces = make_network_traces(frame_data)
        m = frame_data.metrics
        anim_frames.append(go.Frame(
            data=frame_traces,
            name=f"Year {frame_data.year:.0f}",
            layout=go.Layout(
                title_text=(
                    f"Year {frame_data.year:.0f}  |  "
                    f"Total wealth: {m.total_wealth:.2f}  |  "
                    f"Gini: {m.gini:.3f}  |  "
                    f"Collapsed: {m.n_collapsed}"
                )
            ),
        ))

    fig.frames = anim_frames

    fig.update_layout(
        title=f"Year {f0.metrics.year:.0f}  |  Communities: {n}",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-5, result.config.spatial_spread + 5]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-5, result.config.spatial_spread + 5]),
        template='plotly_white',
        height=480,
        updatemenus=[dict(
            type='buttons',
            direction='left',
            showactive=False,
            x=0.1, y=0,
            xanchor='right', yanchor='top',
            pad=dict(r=10, t=87),
            buttons=[
                dict(label='▶ Play', method='animate',
                     args=[None, dict(frame=dict(duration=500, redraw=True),
                                      fromcurrent=True,
                                      transition=dict(duration=0, easing='linear'))]),
                dict(label='⏸ Pause', method='animate',
                     args=[[None], dict(frame=dict(duration=0, redraw=False),
                                        mode='immediate',
                                        transition=dict(duration=0))]),
            ],
        )],
        sliders=[dict(
            active=0,
            steps=[dict(
                args=[[f.name], dict(frame=dict(duration=0, redraw=True),
                                     mode='immediate',
                                     transition=dict(duration=0))],
                label=f.name, method='animate',
            ) for f in anim_frames],
            currentvalue=dict(prefix='', visible=True, xanchor='center'),
            pad=dict(b=10, t=60), len=0.85, x=0.15, y=0,
        )],
    )
    return fig


def _build_society_metric_fig(result: SocietyAnimationResult) -> go.Figure:
    years = [f.metrics.year for f in result.frames]
    total_w = [f.metrics.total_wealth for f in result.frames]
    gini = [f.metrics.gini for f in result.frames]
    mig = [f.metrics.migration_flux for f in result.frames]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=years, y=total_w, name='Total wealth', line=dict(color='#2563eb'), yaxis='y1'))
    fig.add_trace(go.Scatter(x=years, y=gini, name='Gini', line=dict(color='#dc2626', dash='dash'), yaxis='y2'))
    fig.add_trace(go.Scatter(x=years, y=mig, name='Migration flux', line=dict(color='#d97706', dash='dot'), yaxis='y3'))
    fig.update_layout(
        title='Society Metrics Over Time',
        xaxis=dict(title='Year'),
        yaxis=dict(title='Total wealth', side='left'),
        yaxis2=dict(title='Gini', overlaying='y', side='right', range=[0, 1]),
        yaxis3=dict(title='Migration', overlaying='y', side='right', position=0.95),
        template='plotly_white', height=300,
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
    )
    return fig


def _build_outcome_dist_anim(result: SocietyAnimationResult) -> go.Figure:
    """Status distribution chart with frames matching network animation."""
    categories = ['Grew', 'Stabilized', 'Declined', 'Collapsed', 'In progress']
    outcome_keys = ['grew', 'stabilized', 'declined', 'collapsed', 'in_progress']
    colors = [OUTCOME_COLORS[Outcome.GREW], OUTCOME_COLORS[Outcome.STABILIZED],
              OUTCOME_COLORS[Outcome.DECLINED], OUTCOME_COLORS[Outcome.COLLAPSED],
              OUTCOME_COLORS[Outcome.IN_PROGRESS]]
    n = len(result.community_names)

    def counts_for_frame(f):
        return [f.outcome_counts.get(k, 0) / max(n, 1) * 100 for k in outcome_keys]

    f0_counts = counts_for_frame(result.frames[0])
    fig = go.Figure(go.Bar(
        x=categories, y=f0_counts,
        marker_color=colors,
        text=[f'{v:.0f}%' for v in f0_counts], textposition='auto',
    ))

    anim_frames = []
    for frame_data in result.frames:
        counts = counts_for_frame(frame_data)
        anim_frames.append(go.Frame(
            data=[go.Bar(x=categories, y=counts, marker_color=colors,
                         text=[f'{v:.0f}%' for v in counts], textposition='auto')],
            name=f"Year {frame_data.year:.0f}",
        ))
    fig.frames = anim_frames

    fig.update_layout(
        title='Community Status Distribution',
        yaxis=dict(title='% communities', range=[0, 105]),
        template='plotly_white', height=280,
        updatemenus=[dict(
            type='buttons',
            direction='left',
            showactive=False,
            x=0.1, y=-0.2,
            xanchor='right', yanchor='top',
            pad=dict(r=10, t=10),
            buttons=[
                dict(label='▶ Play', method='animate',
                     args=[None, dict(frame=dict(duration=500, redraw=True),
                                      fromcurrent=True,
                                      transition=dict(duration=0, easing='linear'))]),
                dict(label='⏸ Pause', method='animate',
                     args=[[None], dict(frame=dict(duration=0, redraw=False),
                                        mode='immediate',
                                        transition=dict(duration=0))]),
            ],
        )],
        sliders=[dict(
            active=0,
            steps=[dict(
                args=[[f.name], dict(frame=dict(duration=0, redraw=True),
                                     mode='immediate',
                                     transition=dict(duration=0))],
                label=f.name, method='animate',
            ) for f in anim_frames],
            currentvalue=dict(prefix='', visible=True, xanchor='center'),
            pad=dict(b=10, t=10), len=0.85, x=0.15, y=-0.2,
        )],
        margin=dict(b=80),
    )
    return fig


def _society_summary_text(result: SocietyAnimationResult) -> str:
    final = result.final_outcomes
    n = len(final)
    if n == 0:
        return "No communities."

    n_grew = sum(1 for o in final if o == Outcome.GREW)
    n_stab = sum(1 for o in final if o == Outcome.STABILIZED)
    n_dec = sum(1 for o in final if o == Outcome.DECLINED)
    n_col = sum(1 for o in final if o == Outcome.COLLAPSED)
    last_m = result.frames[-1].metrics

    high_r_types = {"strong_nuclear_religious_dense", "extended_kin_religious_dense"}
    high_r_idx = [i for i, cfg in enumerate(result.society.configs) if cfg.name in {
        "Strong nuclear + religious + dense", "Extended kin + religious + dense"
    }]
    low_r_idx = [i for i, cfg in enumerate(result.society.configs) if cfg.name not in {
        "Strong nuclear + religious + dense", "Extended kin + religious + dense"
    }]

    def outcome_rate(indices, target):
        if not indices:
            return float('nan')
        return sum(1 for i in indices if final[i] == target) / len(indices)

    high_r_collapse = outcome_rate(high_r_idx, Outcome.COLLAPSED)
    low_r_grow = outcome_rate(low_r_idx, Outcome.GREW)

    lines = [
        f"**End-of-simulation summary ({n} communities, {result.config.horizon}-year horizon)**\n",
        f"- Grew: **{n_grew}** ({n_grew/n*100:.0f}%) | Stabilized: **{n_stab}** ({n_stab/n*100:.0f}%) | "
        f"Declined: **{n_dec}** ({n_dec/n*100:.0f}%) | Collapsed: **{n_col}** ({n_col/n*100:.0f}%)",
        f"- Final Gini: **{last_m.gini:.3f}** | Final total wealth: **{last_m.total_wealth:.3f}**",
        "",
        "**Cross-configuration findings (honest report):**",
    ]
    if high_r_idx:
        lines.append(f"- High-R community types (strong nuclear + extended kin): "
                     f"{len(high_r_idx)} communities, collapse rate: {high_r_collapse*100:.0f}%")
    if low_r_idx:
        lines.append(f"- Other community types: "
                     f"{len(low_r_idx)} communities, growth rate: {low_r_grow*100:.0f}%")

    society_status = "fragmented" if n_col > n * 0.4 else ("growing" if n_grew > n * 0.4 else "mixed")
    lines.append(f"\n*Overall society status: **{society_status}***")
    lines.append("\n*Note: These results reflect the mathematical model under specified parameters. "
                 "They are not empirical predictions.*")
    return "\n".join(lines)


def run_society_tab(
    n_communities,
    frac_strong, frac_secular, frac_extended, frac_mixed,
    spatial_spread, network_k,
    trade_strength, migration_friction, r_contagion,
    p_local, p_regional, p_global, p_idiosyncratic,
    horizon, seed,
):
    t0 = time.time()
    try:
        total = frac_strong + frac_secular + frac_extended + frac_mixed
        if total <= 0:
            total = 1.0
        archetype_fractions = {
            "strong_nuclear_religious_dense": frac_strong / total,
            "independent_secular_suburban": frac_secular / total,
            "extended_kin_religious_dense": frac_extended / total,
            "mixed_diverse": frac_mixed / total,
        }
        shock_topology_total = p_local + p_regional + p_global + p_idiosyncratic
        if shock_topology_total <= 0:
            shock_topology_total = 1.0

        cfg = SocietyConfig(
            n_communities=int(n_communities),
            archetype_fractions=archetype_fractions,
            spatial_spread=float(spatial_spread),
            network_k=int(network_k),
            trade_strength=float(trade_strength),
            migration_friction=float(migration_friction),
            r_contagion_strength=float(r_contagion),
            shock_topology={
                "local": p_local / shock_topology_total,
                "regional": p_regional / shock_topology_total,
                "global": p_global / shock_topology_total,
                "idiosyncratic": p_idiosyncratic / shock_topology_total,
            },
            horizon=int(horizon),
            seed=int(seed),
        )
        result = run_society_with_frames(cfg)
        elapsed = time.time() - t0

        network_html = _animated_fig_to_html(_build_society_animation(result), height=560)
        dist_html = _animated_fig_to_html(_build_outcome_dist_anim(result), height=360)
        metrics_fig = _build_society_metric_fig(result)
        summary = _society_summary_text(result) + f"\n\n*Simulation time: {elapsed:.1f}s*"

        return network_html, dist_html, metrics_fig, summary
    except Exception as e:
        import traceback
        return "", "", go.Figure(), f"**Error:** {e}\n\n```\n{traceback.format_exc()}\n```"


# ─────────────────────────────────────────────────────────────
# Tab 3: Compare Two Societies
# ─────────────────────────────────────────────────────────────

def _comparison_table(r_a: SocietyAnimationResult, r_b: SocietyAnimationResult) -> str:
    def stats(r):
        n = len(r.final_outcomes)
        outcomes = r.final_outcomes
        counts = {o: sum(1 for x in outcomes if x == o) for o in Outcome if o != Outcome.IN_PROGRESS}
        last = r.frames[-1].metrics
        return {
            'n': n,
            'grew': counts.get(Outcome.GREW, 0),
            'stabilized': counts.get(Outcome.STABILIZED, 0),
            'declined': counts.get(Outcome.DECLINED, 0),
            'collapsed': counts.get(Outcome.COLLAPSED, 0),
            'total_wealth': last.total_wealth,
            'gini': last.gini,
            'migration': last.migration_flux,
        }

    sa, sb = stats(r_a), stats(r_b)
    n_a, n_b = sa['n'], sb['n']

    def pct(d, k, n):
        return f"{d[k]}/{n} ({d[k]/max(n,1)*100:.0f}%)"

    lines = [
        "| Metric | Society A | Society B |",
        "|--------|-----------|-----------|",
        f"| Communities | {n_a} | {n_b} |",
        f"| Grew | {pct(sa,'grew',n_a)} | {pct(sb,'grew',n_b)} |",
        f"| Stabilized | {pct(sa,'stabilized',n_a)} | {pct(sb,'stabilized',n_b)} |",
        f"| Declined | {pct(sa,'declined',n_a)} | {pct(sb,'declined',n_b)} |",
        f"| Collapsed | {pct(sa,'collapsed',n_a)} | {pct(sb,'collapsed',n_b)} |",
        f"| Final total wealth | {sa['total_wealth']:.3f} | {sb['total_wealth']:.3f} |",
        f"| Final Gini | {sa['gini']:.3f} | {sb['gini']:.3f} |",
        f"| Final migration flux | {sa['migration']:.4f} | {sb['migration']:.4f} |",
    ]
    return "\n".join(lines)


def run_comparison_tab(
    # Society A
    n_a, frac_strong_a, frac_secular_a, frac_extended_a, frac_mixed_a,
    spread_a, k_a, trade_a, migration_a, r_contagion_a,
    # Society B
    n_b, frac_strong_b, frac_secular_b, frac_extended_b, frac_mixed_b,
    spread_b, k_b, trade_b, migration_b, r_contagion_b,
    # Shared settings
    horizon, seed,
):
    t0 = time.time()
    try:
        def make_cfg(n, fs, fse, fe, fm, spread, k, trade, mig, r_con):
            total = fs + fse + fe + fm or 1.0
            return SocietyConfig(
                n_communities=int(n),
                archetype_fractions={
                    "strong_nuclear_religious_dense": fs / total,
                    "independent_secular_suburban": fse / total,
                    "extended_kin_religious_dense": fe / total,
                    "mixed_diverse": fm / total,
                },
                spatial_spread=float(spread),
                network_k=int(k),
                trade_strength=float(trade),
                migration_friction=float(mig),
                r_contagion_strength=float(r_con),
                horizon=int(horizon),
                seed=int(seed),
            )

        cfg_a = make_cfg(n_a, frac_strong_a, frac_secular_a, frac_extended_a, frac_mixed_a,
                         spread_a, k_a, trade_a, migration_a, r_contagion_a)
        cfg_b = make_cfg(n_b, frac_strong_b, frac_secular_b, frac_extended_b, frac_mixed_b,
                         spread_b, k_b, trade_b, migration_b, r_contagion_b)

        r_a = run_society_with_frames(cfg_a)
        r_b = run_society_with_frames(cfg_b)

        net_a = _animated_fig_to_html(_build_society_animation(r_a), height=480)
        net_b = _animated_fig_to_html(_build_society_animation(r_b), height=480)
        dist_a = _animated_fig_to_html(_build_outcome_dist_anim(r_a), height=360)
        dist_b = _animated_fig_to_html(_build_outcome_dist_anim(r_b), height=360)

        elapsed = time.time() - t0
        comparison = _comparison_table(r_a, r_b)
        note = (
            "\n\n*Both societies used the same shock seed — differences are due to composition and "
            "network structure, not luck.*"
            f"\n\n*Elapsed: {elapsed:.1f}s*"
        )

        return net_a, net_b, dist_a, dist_b, comparison + note
    except Exception as e:
        import traceback
        return "", "", "", "", f"**Error:** {e}\n\n```\n{traceback.format_exc()}\n```"


# ─────────────────────────────────────────────────────────────
# Gradio UI
# ─────────────────────────────────────────────────────────────

SQFT_ANNOTATION = (
    "50–200: Dense urban village | "
    "200–500: Walkable neighborhood | "
    "500–1500: Suburban | "
    "1500–5000: Low-density"
)


def build_ui():
    with gr.Blocks(title="Nanoeconomics Survival Simulation", theme=gr.themes.Soft()) as demo:
        gr.Markdown("""
# Nanoeconomics Survival Simulation
**W(M, T, R) Community Wealth Dynamics** — Denewade (2025)

Explore how communities survive, grow, or collapse depending on material capital, time allocation, and relational structure. See [docs/methodology.md](docs/methodology.md) for the theoretical foundation.
""")

        with gr.Tabs():
            # ── TAB 1: SINGLE COMMUNITY ──
            with gr.TabItem("Single Community"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### Community Configuration")
                        with gr.Accordion("Demographics", open=True):
                            population = gr.Slider(100, 5000, value=500, step=50, label="Population")
                            sqft_per_resident = gr.Slider(
                                50, 5000, value=300, step=10,
                                label=f"sqft/resident  ({SQFT_ANNOTATION})",
                            )

                        with gr.Accordion("Wealth Function (α weights)", open=False):
                            gr.Markdown("*Exponents renormalized to sum to 1*")
                            alpha_m = gr.Slider(0.1, 0.8, value=0.4, step=0.05, label="α_M (material)")
                            alpha_t = gr.Slider(0.1, 0.8, value=0.3, step=0.05, label="α_T (time)")
                            alpha_r = gr.Slider(0.1, 0.8, value=0.3, step=0.05, label="α_R (relational)")

                        with gr.Accordion("Relational Capital Weights", open=False):
                            gr.Markdown("*Renormalized to sum to 1*")
                            w_family = gr.Slider(0.0, 1.0, value=0.4, step=0.05, label="w_F (family)")
                            w_religion = gr.Slider(0.0, 1.0, value=0.3, step=0.05, label="w_Rel (religion)")
                            w_spatial = gr.Slider(0.0, 1.0, value=0.3, step=0.05, label="w_S (spatial)")

                        with gr.Accordion("Time Allocation", open=False):
                            gr.Markdown("*Renormalized to sum to 1*")
                            p_production = gr.Slider(0.0, 1.0, value=0.40, step=0.05, label="Production")
                            p_family_t = gr.Slider(0.0, 1.0, value=0.25, step=0.05, label="Family")
                            p_religion_t = gr.Slider(0.0, 1.0, value=0.15, step=0.05, label="Religion/community")
                            p_spatial_maint = gr.Slider(0.0, 1.0, value=0.10, step=0.05, label="Spatial maintenance")
                            p_leisure = gr.Slider(0.0, 1.0, value=0.10, step=0.05, label="Leisure")

                        with gr.Accordion("Initial Relational State", open=False):
                            family_init = gr.Slider(0.0, 1.0, value=0.7, step=0.05, label="Initial family strength")
                            religion_init = gr.Slider(0.0, 1.0, value=0.6, step=0.05, label="Initial religious participation")

                        with gr.Accordion("Shock Environment", open=True):
                            shock_env_name = gr.Radio(
                                ["mild", "moderate", "severe"], value="moderate", label="Shock intensity"
                            )

                        with gr.Accordion("Outcome Thresholds", open=False):
                            collapse_threshold = gr.Slider(0.1, 0.6, value=0.3, step=0.05, label="Collapse: W/W₀ below this")
                            growth_threshold = gr.Slider(0.05, 0.5, value=0.20, step=0.05, label="Grew: W/W₀ above 1 + this")
                            stability_band = gr.Slider(0.01, 0.3, value=0.10, step=0.01, label="Stable band ± (fraction of W₀)")
                            recovery_window = gr.Slider(2, 20, value=5, step=1, label="Collapse window (periods)")

                        with gr.Accordion("Simulation Settings", open=True):
                            horizon = gr.Slider(5, 100, value=30, step=5, label="Horizon (years)")
                            n_paths = gr.Slider(50, 1000, value=200, step=50, label="Monte Carlo paths")
                            seed = gr.Number(value=42, label="Random seed", precision=0)

                        run_btn_1 = gr.Button("Run Simulation", variant="primary")

                    with gr.Column(scale=2):
                        outcome_badge = gr.HTML(label="Dominant Outcome")
                        traj_fig = gr.Plot(label="Wealth Trajectory")
                        surv_fig = gr.Plot(label="Survival Curve")
                        comp_fig = gr.Plot(label="M/T/R Components")
                        outcome_bar = gr.Plot(label="Outcome Distribution")
                        summary_md = gr.Markdown()

                run_btn_1.click(
                    run_single_community_tab,
                    inputs=[
                        population, sqft_per_resident, alpha_m, alpha_t, alpha_r,
                        w_family, w_religion, w_spatial,
                        p_production, p_family_t, p_religion_t, p_spatial_maint, p_leisure,
                        family_init, religion_init,
                        shock_env_name, horizon, n_paths, seed,
                        collapse_threshold, growth_threshold, stability_band, recovery_window,
                    ],
                    outputs=[traj_fig, surv_fig, comp_fig, outcome_bar, outcome_badge, summary_md],
                )

            # ── TAB 2: SOCIETY MODE ──
            with gr.TabItem("Society Mode"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### Society Composition")
                        n_communities = gr.Slider(5, 100, value=30, step=5, label="Number of communities")
                        with gr.Accordion("Archetype fractions (renormalized)", open=True):
                            frac_strong = gr.Slider(0.0, 1.0, value=0.25, step=0.05, label="Strong nuclear + religious + dense")
                            frac_secular = gr.Slider(0.0, 1.0, value=0.25, step=0.05, label="Independent + secular + suburban")
                            frac_extended = gr.Slider(0.0, 1.0, value=0.25, step=0.05, label="Extended kin + religious + dense")
                            frac_mixed = gr.Slider(0.0, 1.0, value=0.25, step=0.05, label="Mixed/diverse")
                        spatial_spread = gr.Slider(5, 200, value=50, step=5, label="Spatial spread (units)")
                        network_k = gr.Slider(2, 10, value=4, step=1, label="Network connectivity k")

                        gr.Markdown("### Inter-Community Dynamics")
                        trade_strength = gr.Slider(0.0, 2.0, value=1.0, step=0.1, label="Trade strength multiplier")
                        migration_friction = gr.Slider(0.0, 1.0, value=0.3, step=0.05, label="Migration friction")
                        r_contagion = gr.Slider(0.0, 1.0, value=0.3, step=0.05, label="R-contagion strength")

                        gr.Markdown("### Shock Topology (probabilities, renormalized)")
                        p_local = gr.Slider(0.0, 1.0, value=0.35, step=0.05, label="Local")
                        p_regional = gr.Slider(0.0, 1.0, value=0.20, step=0.05, label="Regional")
                        p_global = gr.Slider(0.0, 1.0, value=0.05, step=0.05, label="Global")
                        p_idiosyncratic = gr.Slider(0.0, 1.0, value=0.40, step=0.05, label="Idiosyncratic")

                        gr.Markdown("### Simulation Settings")
                        horizon_s = gr.Slider(5, 100, value=30, step=5, label="Horizon (years)")
                        seed_s = gr.Number(value=42, label="Random seed", precision=0)

                        run_btn_2 = gr.Button("Run Society Simulation", variant="primary")

                    with gr.Column(scale=2):
                        gr.Markdown("**Animated Society Network**")
                        society_network_fig = gr.HTML()
                        gr.Markdown("**Status Distribution**")
                        society_dist_fig = gr.HTML()
                        society_metrics_fig = gr.Plot(label="Society Metrics")
                        society_summary = gr.Markdown()

                run_btn_2.click(
                    run_society_tab,
                    inputs=[
                        n_communities,
                        frac_strong, frac_secular, frac_extended, frac_mixed,
                        spatial_spread, network_k,
                        trade_strength, migration_friction, r_contagion,
                        p_local, p_regional, p_global, p_idiosyncratic,
                        horizon_s, seed_s,
                    ],
                    outputs=[society_network_fig, society_dist_fig, society_metrics_fig, society_summary],
                )

            # ── TAB 3: COMPARE TWO SOCIETIES ──
            with gr.TabItem("Compare Two Societies"):
                gr.Markdown("### Configure both societies, then run them with the same shock seed to test your hypothesis.")

                with gr.Row():
                    with gr.Column():
                        gr.Markdown("#### Society A")
                        n_a = gr.Slider(5, 100, value=30, step=5, label="N communities")
                        frac_strong_a = gr.Slider(0.0, 1.0, value=0.35, step=0.05, label="Strong nuclear + religious (dense)")
                        frac_secular_a = gr.Slider(0.0, 1.0, value=0.15, step=0.05, label="Independent + secular (suburban)")
                        frac_extended_a = gr.Slider(0.0, 1.0, value=0.35, step=0.05, label="Extended kin + religious (dense)")
                        frac_mixed_a = gr.Slider(0.0, 1.0, value=0.15, step=0.05, label="Mixed/diverse")
                        spread_a = gr.Slider(5, 200, value=50, step=5, label="Spatial spread")
                        k_a = gr.Slider(2, 10, value=4, step=1, label="Network k")
                        trade_a = gr.Slider(0.0, 2.0, value=1.0, step=0.1, label="Trade strength")
                        migration_a = gr.Slider(0.0, 1.0, value=0.3, step=0.05, label="Migration friction")
                        r_con_a = gr.Slider(0.0, 1.0, value=0.3, step=0.05, label="R-contagion")

                    with gr.Column():
                        gr.Markdown("#### Society B")
                        n_b = gr.Slider(5, 100, value=30, step=5, label="N communities")
                        frac_strong_b = gr.Slider(0.0, 1.0, value=0.15, step=0.05, label="Strong nuclear + religious (dense)")
                        frac_secular_b = gr.Slider(0.0, 1.0, value=0.35, step=0.05, label="Independent + secular (suburban)")
                        frac_extended_b = gr.Slider(0.0, 1.0, value=0.15, step=0.05, label="Extended kin + religious (dense)")
                        frac_mixed_b = gr.Slider(0.0, 1.0, value=0.35, step=0.05, label="Mixed/diverse")
                        spread_b = gr.Slider(5, 200, value=50, step=5, label="Spatial spread")
                        k_b = gr.Slider(2, 10, value=4, step=1, label="Network k")
                        trade_b = gr.Slider(0.0, 2.0, value=1.0, step=0.1, label="Trade strength")
                        migration_b = gr.Slider(0.0, 1.0, value=0.3, step=0.05, label="Migration friction")
                        r_con_b = gr.Slider(0.0, 1.0, value=0.3, step=0.05, label="R-contagion")

                with gr.Row():
                    horizon_c = gr.Slider(5, 100, value=30, step=5, label="Horizon (shared)")
                    seed_c = gr.Number(value=42, label="Shock seed (same for both)", precision=0)
                    run_btn_3 = gr.Button("Run Comparison", variant="primary")

                with gr.Row():
                    with gr.Column():
                        gr.Markdown("**Society A Network**")
                        net_a_fig = gr.HTML()
                        gr.Markdown("**Society A Status**")
                        dist_a_fig = gr.HTML()
                    with gr.Column():
                        gr.Markdown("**Society B Network**")
                        net_b_fig = gr.HTML()
                        gr.Markdown("**Society B Status**")
                        dist_b_fig = gr.HTML()

                comparison_table = gr.Markdown()

                run_btn_3.click(
                    run_comparison_tab,
                    inputs=[
                        n_a, frac_strong_a, frac_secular_a, frac_extended_a, frac_mixed_a,
                        spread_a, k_a, trade_a, migration_a, r_con_a,
                        n_b, frac_strong_b, frac_secular_b, frac_extended_b, frac_mixed_b,
                        spread_b, k_b, trade_b, migration_b, r_con_b,
                        horizon_c, seed_c,
                    ],
                    outputs=[net_a_fig, net_b_fig, dist_a_fig, dist_b_fig, comparison_table],
                )

        gr.Markdown("""
---
**Nanoeconomics Survival Simulation** | [Methodology](docs/methodology.md) | Apache 2.0 | Denewade (2025)

*This simulation is a theoretical demonstration. It makes no empirical claims. All parameters are user-adjustable.*
""")

    return demo


demo = build_ui()

if __name__ == "__main__":
    demo.launch(share=False)
