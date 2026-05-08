"""Nanoeconomics Survival Simulation — Streamlit application entry point.

All adjustment widgets live in the left sidebar, organized by simulation mode.
The main area contains three tabs (Single Community, Society Mode, Compare
Two Societies) which render results once the user clicks the matching Run
button in the sidebar.

Streamlit renders Plotly animations natively via st.plotly_chart, so the
play/slider controls work without any iframe wrapping.
"""
from __future__ import annotations

import time

import numpy as np
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

from src.animation import SocietyAnimationResult, run_society_with_frames
from src.community import CommunityConfig, TimeAllocation
from src.outcomes import OUTCOME_COLORS, Outcome, OutcomeThresholds
from src.relational import RelationalConfig
from src.simulation import SingleCommunityConfig, run_single_community
from src.society import SocietyConfig


# ─────────────────────────────────────────────────────────────
# Page configuration
# ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Nanoeconomics Survival Simulation",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "Community wealth dynamics under the W(M,T,R) Nanoeconomics framework. "
                 "Source: github.com/intelligentactuaries/nanoeconomics-simulation",
    },
)


# ─────────────────────────────────────────────────────────────
# Custom CSS — typography, spacing, sidebar polish
# ─────────────────────────────────────────────────────────────

st.markdown("""
<style>
    /* Tighten main content padding */
    .block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 1400px; }

    /* Hide Streamlit chrome */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stStatusWidget"] {visibility: hidden;}

    /* Typography — colors inherit from the active theme; labels bright enough
       to read on both light and dark backgrounds. */
    h1 { font-weight: 700; letter-spacing: -0.02em; margin-bottom: 0.25rem; }
    h2 { font-weight: 650; letter-spacing: -0.01em; }
    h3 { font-weight: 600; }
    h5 { font-weight: 600; opacity: 0.92; text-transform: uppercase;
         font-size: 0.78rem; letter-spacing: 0.06em; margin-top: 1rem; margin-bottom: 0.4rem; }

    /* Sidebar — theme-aware via CSS variables */
    [data-testid="stSidebar"] { border-right: 1px solid rgba(128,128,128,0.18); }
    [data-testid="stSidebar"] .block-container { padding-top: 1.25rem; padding-bottom: 2rem; }
    [data-testid="stSidebar"] h2 { font-size: 1rem; margin-bottom: 0.5rem; }
    [data-testid="stSidebar"] hr { margin: 0.75rem 0; }

    /* Sliders — slimmer, less padding; labels readable on dark backgrounds */
    [data-testid="stSidebar"] .stSlider { padding-top: 0.1rem; padding-bottom: 0.1rem; }
    [data-testid="stSidebar"] .stSlider label p,
    [data-testid="stSidebar"] .stNumberInput label p,
    [data-testid="stSidebar"] .stRadio label p,
    [data-testid="stSidebar"] .stSegmentedControl label p {
        font-size: 0.86rem; opacity: 0.95; font-weight: 500;
    }

    /* Slider tick / value text — Streamlit renders these in a dim slate
       which is hard to read in dark mode. Bump opacity. */
    [data-testid="stSidebar"] .stSlider [data-baseweb="slider"] div[role="slider"] + div,
    [data-testid="stSidebar"] .stSlider [data-testid="stTickBarMin"],
    [data-testid="stSidebar"] .stSlider [data-testid="stTickBarMax"],
    [data-testid="stSidebar"] [data-baseweb="slider"] [class*="StyledThumbValue"] {
        opacity: 0.95 !important;
    }
    [data-testid="stSidebar"] .stSlider div[data-testid="stThumbValue"] { opacity: 1 !important; }

    /* Primary button — orange→red gradient, works on both themes */
    [data-testid="stSidebar"] button[kind="primary"] {
        background: linear-gradient(135deg, #f59e0b 0%, #dc2626 100%);
        border: none; color: #ffffff; font-weight: 600;
        padding: 0.55rem 1rem; margin-top: 0.5rem;
    }
    [data-testid="stSidebar"] button[kind="primary"]:hover { filter: brightness(1.08); }

    /* Pills (mode selector) span full sidebar width */
    [data-testid="stSidebar"] [data-baseweb="segmented-control"] { width: 100%; }

    /* Metric cards — translucent so they pick up the page theme */
    [data-testid="stMetric"] {
        background: rgba(128, 128, 128, 0.08);
        border: 1px solid rgba(128, 128, 128, 0.18);
        border-radius: 10px;
        padding: 0.75rem 1rem;
    }
    [data-testid="stMetricLabel"] p {
        font-size: 0.74rem; text-transform: uppercase; letter-spacing: 0.06em;
        opacity: 0.92 !important; font-weight: 600;
    }
    [data-testid="stMetricValue"] { font-size: 1.55rem; font-weight: 700; }

    /* Metric delta (small "% of total" line under value) — was a dim slate
       in Society Mode and Compare tabs. Force readable opacity. */
    [data-testid="stMetricDelta"] { opacity: 0.95 !important; }
    [data-testid="stMetricDelta"] svg { opacity: 0.95 !important; }
    [data-testid="stMetricDelta"] div { opacity: 1 !important; font-weight: 500; }

    /* Captions — bright enough on dark backgrounds */
    .stCaption, [data-testid="stCaptionContainer"], small {
        opacity: 0.88 !important;
    }
    [data-testid="stCaptionContainer"] p { opacity: 0.92 !important; }

    /* Section headers (##### Markdown) on every tab */
    .main h5, [data-testid="stMarkdownContainer"] h5 {
        opacity: 0.92 !important;
    }

    /* DataFrame (used in Compare tab) — make cell text readable */
    [data-testid="stDataFrame"] { opacity: 0.95; }
    [data-testid="stDataFrame"] [role="gridcell"],
    [data-testid="stDataFrame"] [role="columnheader"] {
        opacity: 1 !important; font-size: 0.92rem;
    }

    /* Catch-all: any small/secondary text inside the main content area */
    .main p, .main label, .main span { opacity: inherit; }

    /* Header GitHub / Methodology link colors — adapt to theme */
    .main a[href*="github"], .main a[href*="methodology"] {
        color: inherit !important; opacity: 0.88;
    }
    .main a[href*="github"]:hover, .main a[href*="methodology"]:hover {
        opacity: 1; text-decoration: underline !important;
    }

    /* Tighter main subheader */
    .main h2 { margin-top: 0; padding-top: 0; }

    /* Plotly iframe wrapper — transparent so the page bg shows through */
    iframe[srcdoc] { background: transparent !important; }

    /* Static Plotly charts on the main page — force text contrast based on
       the user's actual OS-level theme (Streamlit's theme.base is unreliable).
       No `.main` ancestor scope: that class moved to `[data-testid="stMain"]`
       in newer Streamlit and the rules weren't matching. Targeting `.plotly`
       directly is safe — iframe plots have their own document so they're not
       affected by parent-page CSS. */
    @media (prefers-color-scheme: light) {
        [data-testid="stPlotlyChart"] .plotly svg text,
        .plotly svg text,
        .plotly .xtick text, .plotly .ytick text,
        .plotly .legendtext, .plotly .gtitle,
        .plotly .xtitle, .plotly .ytitle,
        .plotly .annotation-text {
            fill: rgba(38, 39, 48, 0.92) !important;
        }
        .plotly .gridlayer path { stroke: rgba(0, 0, 0, 0.08) !important; }
        .plotly .zerolinelayer path { stroke: rgba(0, 0, 0, 0.20) !important; }
    }
    @media (prefers-color-scheme: dark) {
        [data-testid="stPlotlyChart"] .plotly svg text,
        .plotly svg text,
        .plotly .xtick text, .plotly .ytick text,
        .plotly .legendtext, .plotly .gtitle,
        .plotly .xtitle, .plotly .ytitle,
        .plotly .annotation-text {
            fill: rgba(250, 250, 250, 0.94) !important;
        }
        .plotly .gridlayer path { stroke: rgba(255, 255, 255, 0.14) !important; }
        .plotly .zerolinelayer path { stroke: rgba(255, 255, 255, 0.30) !important; }
    }

    /* Main-area mode tabs (segmented_control) — styled as full-width tabs */
    .main [data-testid="stSegmentedControl"] {
        margin-top: 0.25rem; margin-bottom: 0.25rem;
    }
    .main [data-testid="stSegmentedControl"] > div {
        width: 100%; gap: 0;
    }
    .main [data-testid="stSegmentedControl"] label {
        flex: 1 1 0; text-align: center;
        padding: 0.55rem 1rem; font-size: 0.95rem; font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# Animated figure renderer
#
# st.plotly_chart routes figures through Plotly's React renderer, which can
# fail to register animation frames for figures with many traces or shared
# layout state across multiple charts on a page. Rendering animated figures
# via components.html (which uses a true iframe) gives each figure its own
# document context, so Plotly.newPlot() + addFrames() execute cleanly and
# every play button + slider works.
# ─────────────────────────────────────────────────────────────

def _is_dark_theme() -> bool:
    """Detect whether Streamlit is rendering in dark mode."""
    try:
        base = st.get_option("theme.base") or ""
    except Exception:
        base = ""
    return base.lower() == "dark"


def _plotly_template() -> str:
    return "plotly_dark" if _is_dark_theme() else "plotly_white"


def _apply_theme(fig: go.Figure) -> go.Figure:
    """Make every Plotly figure transparent, pick the right template, and
    force readable text colors. Plotly draws title/tick/legend/node text as
    SVG fills, so page CSS can't lighten them — we have to set the font
    color on the figure itself."""
    is_dark = _is_dark_theme()
    text_color = "rgba(250,250,250,0.94)" if is_dark else "rgba(38,39,48,0.92)"
    grid_color = "rgba(255,255,255,0.12)" if is_dark else "rgba(0,0,0,0.08)"

    fig.update_layout(
        template=_plotly_template(),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=text_color, size=12),
        title_font=dict(color=text_color, size=14),
        legend=dict(font=dict(color=text_color)),
    )
    # Apply to every axis (figures may have yaxis2, yaxis3, etc.)
    fig.update_xaxes(gridcolor=grid_color, linecolor=grid_color,
                     zerolinecolor=grid_color, tickfont=dict(color=text_color),
                     title_font=dict(color=text_color))
    fig.update_yaxes(gridcolor=grid_color, linecolor=grid_color,
                     zerolinecolor=grid_color, tickfont=dict(color=text_color),
                     title_font=dict(color=text_color))
    # Slider/play-button labels live in updatemenus + sliders
    for menu in fig.layout.updatemenus or ():
        menu.font = dict(color=text_color)
    for sl in fig.layout.sliders or ():
        sl.font = dict(color=text_color)
        sl.currentvalue.font = dict(color=text_color)
    return fig


def show_animated(fig: go.Figure, height: int = 520) -> None:
    _apply_theme(fig)
    # Disable all zoom paths on animated network/distribution plots: fixed
    # axes block drag-zoom, scrollZoom blocks the wheel, doubleClick blocks
    # the auto-reset.
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    html = fig.to_html(
        include_plotlyjs='cdn',
        full_html=True,
        config={
            'displayModeBar': False,
            'responsive': True,
            'scrollZoom': False,
            'doubleClick': False,
        },
    )
    # Inside the iframe, use prefers-color-scheme to detect the user's actual
    # theme (st.get_option("theme.base") is unreliable). CSS overrides Plotly's
    # SVG <text fill="..."> attributes via !important, so node labels, axis
    # ticks, titles, legends, year frames, and slider labels stay readable
    # regardless of which mode the user is in.
    inject_css = """
    <style>
        html, body { background: transparent !important; margin: 0; }
        .plotly, .plot-container, .svg-container { background: transparent !important; }

        /* Light mode: dark text on light page */
        @media (prefers-color-scheme: light) {
            body { color: #262730; }
            .plotly svg text,
            .plotly .gtitle,
            .plotly .xtitle, .plotly .ytitle,
            .plotly .xtick text, .plotly .ytick text,
            .plotly .legendtext,
            .plotly .annotation-text,
            .plotly .updatemenu-button text,
            .plotly .slider-label,
            .plotly .slider-currentvalue text {
                fill: rgba(38, 39, 48, 0.92) !important;
            }
            .plotly .gridlayer path { stroke: rgba(0, 0, 0, 0.08) !important; }
            .plotly .zerolinelayer path { stroke: rgba(0, 0, 0, 0.20) !important; }
        }

        /* Dark mode: light text on dark page */
        @media (prefers-color-scheme: dark) {
            body { color: #fafafa; }
            .plotly svg text,
            .plotly .gtitle,
            .plotly .xtitle, .plotly .ytitle,
            .plotly .xtick text, .plotly .ytick text,
            .plotly .legendtext,
            .plotly .annotation-text,
            .plotly .updatemenu-button text,
            .plotly .slider-label,
            .plotly .slider-currentvalue text {
                fill: rgba(250, 250, 250, 0.94) !important;
            }
            .plotly .gridlayer path { stroke: rgba(255, 255, 255, 0.14) !important; }
            .plotly .zerolinelayer path { stroke: rgba(255, 255, 255, 0.30) !important; }
            /* Updatemenu (Play/Pause) button outlines */
            .plotly .updatemenu-button rect {
                stroke: rgba(255, 255, 255, 0.30) !important;
            }
        }
    </style>
    """
    html = html.replace("</head>", inject_css + "</head>", 1)
    components.html(html, height=height + 60, scrolling=False)


# ─────────────────────────────────────────────────────────────
# Figure builders
# ─────────────────────────────────────────────────────────────

def _outcome_badge(outcome: Outcome, fraction: float) -> str:
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
                             line=dict(color='rgba(0,0,0,0)'), name='10–90th pct'))
    fig.add_trace(go.Scatter(x=years + years[::-1], y=p75 + p25[::-1],
                             fill='toself', fillcolor='rgba(59,130,246,0.2)',
                             line=dict(color='rgba(0,0,0,0)'), name='25–75th pct'))
    fig.add_trace(go.Scatter(x=years, y=mean_w, line=dict(color='#2563eb', width=2.5),
                             name='Mean wealth'))
    fig.add_hline(y=w0, line_dash='dash', line_color='#9ca3af', annotation_text='W₀')
    fig.update_layout(
        title='Wealth Trajectory (W/W₀ units)',
        xaxis_title='Year', yaxis_title='W',
        template=_plotly_template(),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=440,
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
    )
    return _apply_theme(fig)


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
        template=_plotly_template(),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=400,
    )
    return _apply_theme(fig)


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
        template=_plotly_template(),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=420,
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
    )
    return _apply_theme(fig)


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
        template=_plotly_template(),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=380,
    )
    return _apply_theme(fig)


def _build_society_animation(result: SocietyAnimationResult) -> go.Figure:
    positions = result.positions
    edges = result.graph_edges
    n = len(positions)
    names = result.community_names

    def make_traces(frame_data):
        traces = []
        for (i, j), ew, ec in zip(edges, frame_data.edge_widths, frame_data.edge_colors):
            traces.append(go.Scatter(
                x=[positions[i, 0], positions[j, 0], None],
                y=[positions[i, 1], positions[j, 1], None],
                mode='lines',
                line=dict(width=ew, color=ec),
                hoverinfo='none', showlegend=False,
            ))
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

    f0 = result.frames[0]
    fig = go.Figure(data=make_traces(f0))

    anim_frames = []
    for frame_data in result.frames:
        m = frame_data.metrics
        anim_frames.append(go.Frame(
            data=make_traces(frame_data),
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
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False,
                   range=[-5, result.config.spatial_spread + 5]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False,
                   range=[-5, result.config.spatial_spread + 5]),
        template=_plotly_template(),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        height=520,
        updatemenus=[dict(
            type='buttons', direction='left', showactive=False,
            x=0.1, y=0, xanchor='right', yanchor='top',
            pad=dict(r=10, t=87),
            buttons=[
                dict(label='▶ Play', method='animate',
                     args=[None, dict(frame=dict(duration=500, redraw=True),
                                      fromcurrent=True,
                                      transition=dict(duration=0))]),
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
            pad=dict(b=10, t=60), len=0.85, x=0.15, y=0,
            currentvalue=dict(prefix='', visible=True, xanchor='center'),
        )],
    )
    return _apply_theme(fig)


def _build_society_metric_fig(result: SocietyAnimationResult) -> go.Figure:
    years = [f.metrics.year for f in result.frames]
    total_w = [f.metrics.total_wealth for f in result.frames]
    gini = [f.metrics.gini for f in result.frames]
    mig = [f.metrics.migration_flux for f in result.frames]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=years, y=total_w, name='Total wealth',
                             line=dict(color='#2563eb'), yaxis='y1'))
    fig.add_trace(go.Scatter(x=years, y=gini, name='Gini',
                             line=dict(color='#dc2626', dash='dash'), yaxis='y2'))
    fig.add_trace(go.Scatter(x=years, y=mig, name='Migration flux',
                             line=dict(color='#d97706', dash='dot'), yaxis='y3'))
    fig.update_layout(
        title='Society Metrics Over Time',
        xaxis=dict(title='Year'),
        yaxis=dict(title='Total wealth', side='left'),
        yaxis2=dict(title='Gini', overlaying='y', side='right', range=[0, 1]),
        yaxis3=dict(title='Migration', overlaying='y', side='right', position=0.95),
        template=_plotly_template(),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=440,
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
    )
    return _apply_theme(fig)


def _build_outcome_dist_anim(result: SocietyAnimationResult) -> go.Figure:
    categories = ['Grew', 'Stabilized', 'Declined', 'Collapsed', 'In progress']
    outcome_keys = ['grew', 'stabilized', 'declined', 'collapsed', 'in_progress']
    colors = [OUTCOME_COLORS[Outcome.GREW], OUTCOME_COLORS[Outcome.STABILIZED],
              OUTCOME_COLORS[Outcome.DECLINED], OUTCOME_COLORS[Outcome.COLLAPSED],
              OUTCOME_COLORS[Outcome.IN_PROGRESS]]
    n = len(result.community_names)

    def counts_for(f):
        return [f.outcome_counts.get(k, 0) / max(n, 1) * 100 for k in outcome_keys]

    f0 = counts_for(result.frames[0])
    fig = go.Figure(go.Bar(x=categories, y=f0, marker_color=colors,
                           text=[f'{v:.0f}%' for v in f0], textposition='auto'))

    anim_frames = []
    for frame_data in result.frames:
        c = counts_for(frame_data)
        anim_frames.append(go.Frame(
            data=[go.Bar(x=categories, y=c, marker_color=colors,
                         text=[f'{v:.0f}%' for v in c], textposition='auto')],
            name=f"Year {frame_data.year:.0f}",
        ))
    fig.frames = anim_frames

    fig.update_layout(
        title='Community Status Distribution',
        yaxis=dict(title='% communities', range=[0, 105]),
        template=_plotly_template(),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=460,
        margin=dict(b=80),
        updatemenus=[dict(
            type='buttons', direction='left', showactive=False,
            x=0.1, y=-0.25, xanchor='right', yanchor='top',
            pad=dict(r=10, t=10),
            buttons=[
                dict(label='▶ Play', method='animate',
                     args=[None, dict(frame=dict(duration=500, redraw=True),
                                      fromcurrent=True,
                                      transition=dict(duration=0))]),
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
            pad=dict(b=10, t=10), len=0.85, x=0.15, y=-0.25,
            currentvalue=dict(prefix='', visible=True, xanchor='center'),
        )],
    )
    return _apply_theme(fig)


# ─────────────────────────────────────────────────────────────
# Runner functions (cached so identical configs aren't recomputed)
# ─────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def _run_single(cfg_dict: dict):
    cfg = SingleCommunityConfig(**cfg_dict)
    return run_single_community(cfg)


@st.cache_data(show_spinner=False)
def _run_society(cfg_dict: dict) -> SocietyAnimationResult:
    return run_society_with_frames(SocietyConfig(**cfg_dict))


# ─────────────────────────────────────────────────────────────
# Main page header
# ─────────────────────────────────────────────────────────────

header_l, header_r = st.columns([5, 2])
with header_l:
    st.title("Nanoeconomics Survival Simulation")
    st.caption(
        "**W(M, T, R) community wealth dynamics** · Denewade (2025) · "
        "Risk-return tradeoff under stochastic shocks"
    )
with header_r:
    st.markdown(
        '<div style="text-align:right; padding-top:0.6rem;">'
        '<a href="https://github.com/intelligentactuaries/nanoeconomics-simulation" '
        'style="text-decoration:none; font-size:0.9rem; margin-right:0.85rem;">↗ GitHub</a>'
        '<a href="https://github.com/intelligentactuaries/nanoeconomics-simulation/blob/main/docs/methodology.md" '
        'style="text-decoration:none; font-size:0.9rem;">↗ Methodology</a>'
        '</div>',
        unsafe_allow_html=True,
    )

SQFT_NOTE = (
    "50–200: Dense urban village · 200–500: Walkable neighborhood · "
    "500–1500: Suburban · 1500–5000: Low-density"
)

MODE_SINGLE = "Single Community"
MODE_SOCIETY = "Society Mode"
MODE_COMPARE = "Compare Societies"
MODES = [MODE_SINGLE, MODE_SOCIETY, MODE_COMPARE]
MODE_ICON = {
    MODE_SINGLE: "🏘️",
    MODE_SOCIETY: "🌐",
    MODE_COMPARE: "⚖️",
}

# ─────────────────────────────────────────────────────────────
# Mode tabs — main-area segmented control acting as tabs.
# Both the sidebar controls and the main view filter on `mode`.
# ─────────────────────────────────────────────────────────────

mode = st.segmented_control(
    "Mode",
    MODES,
    default=MODE_SINGLE,
    format_func=lambda m: f"{MODE_ICON[m]}  {m}",
    label_visibility="collapsed",
    key="active_mode",
    use_container_width=True,
) or MODE_SINGLE

st.divider()

# ─────────────────────────────────────────────────────────────
# Initialize session state
# ─────────────────────────────────────────────────────────────

for k in ('sc_result', 'soc_result', 'cmp_result_a', 'cmp_result_b', 'cmp_elapsed',
         'sc_elapsed', 'soc_elapsed'):
    st.session_state.setdefault(k, None)

# Run-button defaults (only one of these gets set True per rerun, by the
# branch matching the active mode).
sc_run = soc_run = cmp_run = False


# ─────────────────────────────────────────────────────────────
# Sidebar — tab selector at top, then only the active tab's controls
# ─────────────────────────────────────────────────────────────

def _section(label: str) -> None:
    """Small uppercase section heading inside the sidebar."""
    st.markdown(f"##### {label}")


with st.sidebar:
    st.markdown(f"### ⚙️  {MODE_ICON[mode]}  {mode}")
    st.caption("Adjust parameters · click ▶ Run")
    st.divider()

    # ── Single Community controls ──
    if mode == MODE_SINGLE:
        _section("Demographics")
        sc_population = st.slider("Population", 100, 5000, 500, 50, key="sc_pop")
        sc_sqft = st.slider("sqft / resident", 50, 5000, 300, 10, key="sc_sqft",
                            help=SQFT_NOTE)

        _section("Wealth function · α (renormalized)")
        c1, c2, c3 = st.columns(3)
        sc_alpha_m = c1.slider("α_M", 0.1, 0.8, 0.40, 0.05, key="sc_am")
        sc_alpha_t = c2.slider("α_T", 0.1, 0.8, 0.30, 0.05, key="sc_at")
        sc_alpha_r = c3.slider("α_R", 0.1, 0.8, 0.30, 0.05, key="sc_ar")

        _section("Relational weights (renormalized)")
        c1, c2, c3 = st.columns(3)
        sc_wf = c1.slider("w_F", 0.0, 1.0, 0.40, 0.05, key="sc_wf")
        sc_wrel = c2.slider("w_Rel", 0.0, 1.0, 0.30, 0.05, key="sc_wrel")
        sc_ws = c3.slider("w_S", 0.0, 1.0, 0.30, 0.05, key="sc_ws")

        _section("Time allocation (renormalized)")
        sc_p_prod = st.slider("Production", 0.0, 1.0, 0.40, 0.05, key="sc_pp")
        sc_p_fam = st.slider("Family", 0.0, 1.0, 0.25, 0.05, key="sc_pf")
        sc_p_rel = st.slider("Religion / community", 0.0, 1.0, 0.15, 0.05, key="sc_pr")
        sc_p_sp = st.slider("Spatial maintenance", 0.0, 1.0, 0.10, 0.05, key="sc_ps")
        sc_p_leis = st.slider("Leisure", 0.0, 1.0, 0.10, 0.05, key="sc_pl")

        _section("Initial relational state")
        sc_fam0 = st.slider("Initial family strength", 0.0, 1.0, 0.7, 0.05, key="sc_f0")
        sc_rel0 = st.slider("Initial religious participation", 0.0, 1.0, 0.6, 0.05, key="sc_r0")

        _section("Shocks · thresholds")
        sc_shock = st.segmented_control(
            "Shock intensity", ["mild", "moderate", "severe"],
            default="moderate", key="sc_shock",
        ) or "moderate"
        sc_collapse_t = st.slider("Collapse threshold (W/W₀ <)", 0.1, 0.6, 0.3, 0.05, key="sc_ct")
        sc_grow_t = st.slider("Grew threshold (W/W₀ > 1+)", 0.05, 0.5, 0.20, 0.05, key="sc_gt")
        sc_stab_t = st.slider("Stable band ±", 0.01, 0.3, 0.10, 0.01, key="sc_st")
        sc_recov_w = st.slider("Collapse window (periods)", 2, 20, 5, 1, key="sc_rw")

        _section("Simulation")
        sc_horizon = st.slider("Horizon (years)", 5, 100, 30, 5, key="sc_h")
        sc_npaths = st.slider("Monte Carlo paths", 50, 1000, 200, 50, key="sc_np")
        sc_seed = st.number_input("Random seed", value=42, step=1, key="sc_s")

        sc_run = st.button("▶  Run Single Community", type="primary",
                           use_container_width=True, key="sc_run_btn")

    # ── Society Mode controls ──
    elif mode == MODE_SOCIETY:
        _section("Composition")
        soc_n = st.slider("Number of communities", 5, 100, 30, 5, key="soc_n")

        _section("Archetype fractions (renormalized)")
        soc_fs = st.slider("Strong nuclear + religious + dense", 0.0, 1.0, 0.25, 0.05, key="soc_fs")
        soc_fsec = st.slider("Independent + secular + suburban", 0.0, 1.0, 0.25, 0.05, key="soc_fsec")
        soc_fe = st.slider("Extended kin + religious + dense", 0.0, 1.0, 0.25, 0.05, key="soc_fe")
        soc_fm = st.slider("Mixed / diverse", 0.0, 1.0, 0.25, 0.05, key="soc_fm")

        _section("Spatial · network")
        soc_spread = st.slider("Spatial spread", 5, 200, 50, 5, key="soc_spr")
        soc_k = st.slider("Network connectivity k", 2, 10, 4, 1, key="soc_k")

        _section("Inter-community dynamics")
        soc_trade = st.slider("Trade strength", 0.0, 2.0, 1.0, 0.1, key="soc_tr")
        soc_mig = st.slider("Migration friction", 0.0, 1.0, 0.3, 0.05, key="soc_mig")
        soc_rcon = st.slider("R-contagion strength", 0.0, 1.0, 0.3, 0.05, key="soc_rc")

        _section("Shock topology (renormalized)")
        soc_pl = st.slider("Local", 0.0, 1.0, 0.35, 0.05, key="soc_pl")
        soc_pr = st.slider("Regional", 0.0, 1.0, 0.20, 0.05, key="soc_pr")
        soc_pg = st.slider("Global", 0.0, 1.0, 0.05, 0.05, key="soc_pg")
        soc_pi = st.slider("Idiosyncratic", 0.0, 1.0, 0.40, 0.05, key="soc_pi")

        _section("Simulation")
        soc_horizon = st.slider("Horizon (years)", 5, 100, 30, 5, key="soc_h")
        soc_seed = st.number_input("Random seed", value=42, step=1, key="soc_s")

        soc_run = st.button("▶  Run Society Simulation", type="primary",
                            use_container_width=True, key="soc_run_btn")

    # ── Compare Two Societies controls ──
    elif mode == MODE_COMPARE:
        _section("Society A")
        a_n = st.slider("N communities", 5, 100, 30, 5, key="a_n")
        a_fs = st.slider("Strong nuclear + religious", 0.0, 1.0, 0.35, 0.05, key="a_fs")
        a_fsec = st.slider("Independent secular", 0.0, 1.0, 0.15, 0.05, key="a_fsec")
        a_fe = st.slider("Extended kin", 0.0, 1.0, 0.35, 0.05, key="a_fe")
        a_fm = st.slider("Mixed", 0.0, 1.0, 0.15, 0.05, key="a_fm")
        a_spread = st.slider("Spatial spread", 5, 200, 50, 5, key="a_spr")
        a_k = st.slider("Network k", 2, 10, 4, 1, key="a_k")
        a_trade = st.slider("Trade strength", 0.0, 2.0, 1.0, 0.1, key="a_tr")
        a_mig = st.slider("Migration friction", 0.0, 1.0, 0.3, 0.05, key="a_mig")
        a_rc = st.slider("R-contagion", 0.0, 1.0, 0.3, 0.05, key="a_rc")

        st.divider()
        _section("Society B")
        b_n = st.slider("N communities", 5, 100, 30, 5, key="b_n")
        b_fs = st.slider("Strong nuclear + religious", 0.0, 1.0, 0.15, 0.05, key="b_fs")
        b_fsec = st.slider("Independent secular", 0.0, 1.0, 0.35, 0.05, key="b_fsec")
        b_fe = st.slider("Extended kin", 0.0, 1.0, 0.15, 0.05, key="b_fe")
        b_fm = st.slider("Mixed", 0.0, 1.0, 0.35, 0.05, key="b_fm")
        b_spread = st.slider("Spatial spread", 5, 200, 50, 5, key="b_spr")
        b_k = st.slider("Network k", 2, 10, 4, 1, key="b_k")
        b_trade = st.slider("Trade strength", 0.0, 2.0, 1.0, 0.1, key="b_tr")
        b_mig = st.slider("Migration friction", 0.0, 1.0, 0.3, 0.05, key="b_mig")
        b_rc = st.slider("R-contagion", 0.0, 1.0, 0.3, 0.05, key="b_rc")

        st.divider()
        _section("Shared")
        cmp_horizon = st.slider("Horizon (years)", 5, 100, 30, 5, key="cmp_h")
        cmp_seed = st.number_input("Shock seed (same for both)", value=42, step=1, key="cmp_s")

        cmp_run = st.button("▶  Run Comparison", type="primary",
                            use_container_width=True, key="cmp_run_btn")

    st.divider()
    st.caption(
        "**Risk-return tradeoff:** high-R suppresses downside risk; "
        "low-R drives growth. See "
        "[methodology](https://github.com/intelligentactuaries/nanoeconomics-simulation/blob/main/docs/methodology.md)."
    )


# ─────────────────────────────────────────────────────────────
# Handle Run buttons (writes results to session_state)
# ─────────────────────────────────────────────────────────────

if sc_run:
    with st.spinner("Running single-community Monte Carlo..."):
        t0 = time.time()
        community = CommunityConfig(
            population=int(sc_population),
            sqft_per_resident=float(sc_sqft),
            alpha_m=float(sc_alpha_m),
            alpha_t=float(sc_alpha_t),
            alpha_r=float(sc_alpha_r),
            relational_config=RelationalConfig(
                w_family=float(sc_wf), w_religion=float(sc_wrel), w_spatial=float(sc_ws),
            ),
            time_allocation=TimeAllocation(
                production=float(sc_p_prod), family=float(sc_p_fam),
                religion=float(sc_p_rel), spatial_maintenance=float(sc_p_sp),
                leisure=float(sc_p_leis),
            ),
        )
        thresholds = OutcomeThresholds(
            collapse_threshold=float(sc_collapse_t),
            growth_threshold=float(sc_grow_t),
            stability_band=float(sc_stab_t),
            recovery_window=int(sc_recov_w),
        )
        cfg = SingleCommunityConfig(
            community=community, shock_environment=sc_shock,
            horizon=int(sc_horizon), n_paths=int(sc_npaths),
            dt=1.0, seed=int(sc_seed), thresholds=thresholds,
        )
        st.session_state.sc_result = run_single_community(cfg)
        st.session_state.sc_elapsed = time.time() - t0

if soc_run:
    with st.spinner("Running society simulation..."):
        t0 = time.time()
        total = soc_fs + soc_fsec + soc_fe + soc_fm or 1.0
        topo = soc_pl + soc_pr + soc_pg + soc_pi or 1.0
        cfg = SocietyConfig(
            n_communities=int(soc_n),
            archetype_fractions={
                "strong_nuclear_religious_dense": soc_fs / total,
                "independent_secular_suburban": soc_fsec / total,
                "extended_kin_religious_dense": soc_fe / total,
                "mixed_diverse": soc_fm / total,
            },
            spatial_spread=float(soc_spread), network_k=int(soc_k),
            trade_strength=float(soc_trade),
            migration_friction=float(soc_mig),
            r_contagion_strength=float(soc_rcon),
            shock_topology={
                "local": soc_pl / topo, "regional": soc_pr / topo,
                "global": soc_pg / topo, "idiosyncratic": soc_pi / topo,
            },
            horizon=int(soc_horizon), seed=int(soc_seed),
        )
        st.session_state.soc_result = run_society_with_frames(cfg)
        st.session_state.soc_elapsed = time.time() - t0

if cmp_run:
    with st.spinner("Running comparison (two societies)..."):
        t0 = time.time()
        def _mk(n, fs, fsec, fe, fm, spr, k, tr, mig, rc):
            total = fs + fsec + fe + fm or 1.0
            return SocietyConfig(
                n_communities=int(n),
                archetype_fractions={
                    "strong_nuclear_religious_dense": fs / total,
                    "independent_secular_suburban": fsec / total,
                    "extended_kin_religious_dense": fe / total,
                    "mixed_diverse": fm / total,
                },
                spatial_spread=float(spr), network_k=int(k),
                trade_strength=float(tr),
                migration_friction=float(mig),
                r_contagion_strength=float(rc),
                horizon=int(cmp_horizon), seed=int(cmp_seed),
            )
        st.session_state.cmp_result_a = run_society_with_frames(
            _mk(a_n, a_fs, a_fsec, a_fe, a_fm, a_spread, a_k, a_trade, a_mig, a_rc))
        st.session_state.cmp_result_b = run_society_with_frames(
            _mk(b_n, b_fs, b_fsec, b_fe, b_fm, b_spread, b_k, b_trade, b_mig, b_rc))
        st.session_state.cmp_elapsed = time.time() - t0


# ─────────────────────────────────────────────────────────────
# Main area — render only the section matching the active mode.
# Mode is driven by the sidebar tab selector, so the sidebar controls
# and the main view are always in sync.
# ─────────────────────────────────────────────────────────────

# ── Single Community ──
if mode == MODE_SINGLE:
    if st.session_state.sc_result is None:
        st.markdown(f"### {MODE_ICON[MODE_SINGLE]}  Single Community")
        st.info("Configure parameters in the sidebar, then click **▶ Run Single Community**.")
    else:
        result = st.session_state.sc_result
        elapsed = st.session_state.sc_elapsed or 0.0
        fracs = result.outcome_fractions()
        dominant = result.dominant_outcome()
        dom_frac = fracs.get(dominant, 0.0)

        head_l, head_r = st.columns([3, 2])
        with head_l:
            st.markdown(f"### {MODE_ICON[MODE_SINGLE]}  Single Community")
            st.caption(
                f"{result.config.n_paths} Monte Carlo paths · "
                f"{result.config.horizon}-yr horizon · "
                f"shock = `{result.config.shock_environment}` · "
                f"elapsed {elapsed:.1f}s"
            )
        with head_r:
            st.markdown(_outcome_badge(dominant, dom_frac), unsafe_allow_html=True)

        # Outcome distribution as metric cards
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Grew", f"{fracs.get(Outcome.GREW, 0)*100:.0f}%")
        m2.metric("Stabilized", f"{fracs.get(Outcome.STABILIZED, 0)*100:.0f}%")
        m3.metric("Declined", f"{fracs.get(Outcome.DECLINED, 0)*100:.0f}%")
        m4.metric("Collapsed", f"{fracs.get(Outcome.COLLAPSED, 0)*100:.0f}%")

        st.markdown("")
        st.markdown("##### Wealth trajectory")
        st.plotly_chart(_make_trajectory_fig(result), use_container_width=True)

        st.markdown("")
        st.markdown("##### Survival probability S(t)")
        st.plotly_chart(_make_survival_fig(result), use_container_width=True)

        st.markdown("")
        st.markdown("##### M / T / R components")
        st.plotly_chart(_make_components_fig(result), use_container_width=True)

        st.markdown("")
        st.markdown("##### Outcome distribution")
        st.plotly_chart(_make_outcome_bar(fracs), use_container_width=True)


# ── Society Mode ──
elif mode == MODE_SOCIETY:
    if st.session_state.soc_result is None:
        st.markdown(f"### {MODE_ICON[MODE_SOCIETY]}  Society Mode")
        st.info("Configure parameters in the sidebar, then click **▶ Run Society Simulation**.")
    else:
        result = st.session_state.soc_result
        elapsed = st.session_state.soc_elapsed or 0.0

        final = result.final_outcomes
        n = len(final)
        n_grew = sum(1 for o in final if o == Outcome.GREW)
        n_stab = sum(1 for o in final if o == Outcome.STABILIZED)
        n_dec = sum(1 for o in final if o == Outcome.DECLINED)
        n_col = sum(1 for o in final if o == Outcome.COLLAPSED)
        last_m = result.frames[-1].metrics

        st.markdown(f"### {MODE_ICON[MODE_SOCIETY]}  Society Mode")
        st.caption(
            f"{n} communities · {result.config.horizon}-yr horizon · "
            f"elapsed {elapsed:.1f}s"
        )

        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.metric("Grew", n_grew, f"{n_grew/n*100:.0f}%")
        m2.metric("Stabilized", n_stab, f"{n_stab/n*100:.0f}%")
        m3.metric("Declined", n_dec, f"{n_dec/n*100:.0f}%")
        m4.metric("Collapsed", n_col, f"{n_col/n*100:.0f}%")
        m5.metric("Total wealth", f"{last_m.total_wealth:.2f}")
        m6.metric("Gini", f"{last_m.gini:.3f}")

        st.markdown("")
        st.markdown("##### Animated society network")
        show_animated(_build_society_animation(result), height=600)

        st.markdown("")
        st.markdown("##### Status distribution over time")
        show_animated(_build_outcome_dist_anim(result), height=520)

        st.markdown("")
        st.markdown("##### Society metrics")
        st.plotly_chart(_build_society_metric_fig(result), use_container_width=True)

        st.caption(
            "Results reflect the model under the chosen parameters; "
            "not empirical predictions."
        )


# ── Compare Two Societies ──
elif mode == MODE_COMPARE:
    if st.session_state.cmp_result_a is None:
        st.markdown(f"### {MODE_ICON[MODE_COMPARE]}  Compare Two Societies")
        st.info("Configure both societies in the sidebar, then click **▶ Run Comparison**.")
    else:
        r_a = st.session_state.cmp_result_a
        r_b = st.session_state.cmp_result_b
        elapsed = st.session_state.cmp_elapsed or 0.0

        st.markdown(f"### {MODE_ICON[MODE_COMPARE]}  Compare Two Societies")
        st.caption(
            f"Both societies use the same shock seed (`{cmp_seed}`) — differences come "
            f"from composition and network structure, not luck. · elapsed {elapsed:.1f}s"
        )

        def stats(r):
            outcomes = r.final_outcomes
            counts = {o: sum(1 for x in outcomes if x == o)
                      for o in Outcome if o != Outcome.IN_PROGRESS}
            last = r.frames[-1].metrics
            return {
                'n': len(outcomes),
                'grew': counts.get(Outcome.GREW, 0),
                'stabilized': counts.get(Outcome.STABILIZED, 0),
                'declined': counts.get(Outcome.DECLINED, 0),
                'collapsed': counts.get(Outcome.COLLAPSED, 0),
                'total_wealth': last.total_wealth,
                'gini': last.gini,
                'migration': last.migration_flux,
            }
        sa, sb = stats(r_a), stats(r_b)

        # Side-by-side metric strips
        a_col, b_col = st.columns(2)
        with a_col:
            st.markdown("##### 🅐  Society A")
            ma1, ma2, ma3, ma4 = st.columns(4)
            ma1.metric("Grew", sa['grew'])
            ma2.metric("Stabilized", sa['stabilized'])
            ma3.metric("Declined", sa['declined'])
            ma4.metric("Collapsed", sa['collapsed'])
            mb1, mb2 = st.columns(2)
            mb1.metric("Total wealth", f"{sa['total_wealth']:.2f}")
            mb2.metric("Gini", f"{sa['gini']:.3f}")
        with b_col:
            st.markdown("##### 🅑  Society B")
            ma1, ma2, ma3, ma4 = st.columns(4)
            ma1.metric("Grew", sb['grew'])
            ma2.metric("Stabilized", sb['stabilized'])
            ma3.metric("Declined", sb['declined'])
            ma4.metric("Collapsed", sb['collapsed'])
            mb1, mb2 = st.columns(2)
            mb1.metric("Total wealth", f"{sb['total_wealth']:.2f}")
            mb2.metric("Gini", f"{sb['gini']:.3f}")

        st.markdown("")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("##### Society A — network")
            show_animated(_build_society_animation(r_a), height=520)
            st.markdown("##### Society A — status distribution")
            show_animated(_build_outcome_dist_anim(r_a), height=420)
        with c2:
            st.markdown("##### Society B — network")
            show_animated(_build_society_animation(r_b), height=520)
            st.markdown("##### Society B — status distribution")
            show_animated(_build_outcome_dist_anim(r_b), height=420)

        st.markdown("")
        st.markdown("##### Side-by-side comparison")
        import pandas as pd
        df = pd.DataFrame({
            "Metric": [
                "Communities", "Grew", "Stabilized", "Declined", "Collapsed",
                "Final total wealth", "Final Gini", "Final migration flux",
            ],
            "Society A": [
                str(sa['n']), str(sa['grew']), str(sa['stabilized']),
                str(sa['declined']), str(sa['collapsed']),
                f"{sa['total_wealth']:.3f}", f"{sa['gini']:.3f}", f"{sa['migration']:.4f}",
            ],
            "Society B": [
                str(sb['n']), str(sb['grew']), str(sb['stabilized']),
                str(sb['declined']), str(sb['collapsed']),
                f"{sb['total_wealth']:.3f}", f"{sb['gini']:.3f}", f"{sb['migration']:.4f}",
            ],
        })
        st.dataframe(df, hide_index=True, use_container_width=True)
