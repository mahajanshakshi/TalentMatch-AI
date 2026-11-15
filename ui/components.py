"""Reusable UI widgets, Plotly charts, and visual components."""

import html
from typing import List
import plotly.graph_objects as go
import streamlit as st

import config
from core.schemas import DimensionScore, VerdictEnum


def render_hero_header():
    """Render the top hero banner."""
    st.markdown(
        f"""
        <div class="hero-header">
            <h1 class="hero-title">⚡ {config.APP_NAME}</h1>
            <p class="hero-subtitle">
                {config.APP_SUBTITLE} • Powered by Groq <code>{config.GROQ_MODEL}</code>
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_verdict_css_class(verdict: VerdictEnum | str) -> str:
    """Map verdict enum or string to appropriate CSS class."""
    v_str = verdict.value if isinstance(verdict, VerdictEnum) else str(verdict)
    v_lower = v_str.lower()

    if "strong" in v_lower:
        return "verdict-strong"
    elif "good" in v_lower:
        return "verdict-good"
    elif "potential" in v_lower:
        return "verdict-potential"
    elif "moderate" in v_lower:
        return "verdict-moderate"
    else:
        return "verdict-low"


def render_verdict_badge(verdict: VerdictEnum | str) -> str:
    """Generate HTML for a styled verdict pill."""
    v_str = verdict.value if isinstance(verdict, VerdictEnum) else str(verdict)
    css_cls = get_verdict_css_class(verdict)
    return f'<div class="verdict-badge {css_cls}">Verdict: {html.escape(v_str)}</div>'


def render_skill_pills(skills: List[str], pill_type: str = "matched") -> str:
    """
    Render a group of colored skill pills as HTML.
    
    pill_type: 'matched' | 'preferred' | 'missing' | 'bonus'
    """
    if not skills:
        return '<span style="color: #64748b; font-style: italic;">None identified</span>'

    cls_name = f"skill-pill-{pill_type}"
    pills_html = []
    for skill in skills:
        safe_skill = html.escape(skill)
        pills_html.append(f'<span class="skill-pill {cls_name}">{safe_skill}</span>')

    return "".join(pills_html)


def create_match_gauge_chart(score: float, verdict: str) -> go.Figure:
    """Create a Plotly radial gauge for overall match score."""
    # Determine bar color based on score thresholds
    if score >= 85:
        bar_color = "#10b981"  # Emerald
    elif score >= 70:
        bar_color = "#3b82f6"  # Blue
    elif score >= 55:
        bar_color = "#f59e0b"  # Amber
    elif score >= 40:
        bar_color = "#f97316"  # Orange
    else:
        bar_color = "#ef4444"  # Red

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": f"<b>Match Score</b><br><span style='font-size:0.8em;color:#94a3b8'>{verdict}</span>", "font": {"size": 20, "color": "#f8fafc"}},
            number={"suffix": "%", "font": {"size": 48, "color": bar_color, "family": "Inter, sans-serif"}},
            gauge={
                "axis": {
                    "range": [0, 100],
                    "tickwidth": 1,
                    "tickcolor": "#475569",
                    "tickfont": {"color": "#94a3b8"},
                },
                "bar": {"color": bar_color, "thickness": 0.28},
                "bgcolor": "rgba(0,0,0,0)",
                "borderwidth": 1,
                "bordercolor": "rgba(255,255,255,0.1)",
                "steps": [
                    {"range": [0, 40], "color": "rgba(239, 68, 68, 0.12)"},
                    {"range": [40, 55], "color": "rgba(249, 115, 22, 0.12)"},
                    {"range": [55, 70], "color": "rgba(245, 158, 11, 0.12)"},
                    {"range": [70, 85], "color": "rgba(59, 130, 246, 0.12)"},
                    {"range": [85, 100], "color": "rgba(16, 185, 129, 0.15)"},
                ],
                "threshold": {
                    "line": {"color": "#ffffff", "width": 3},
                    "thickness": 0.75,
                    "value": score,
                },
            },
        )
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#f8fafc", "family": "Inter, sans-serif"},
        height=280,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return fig


def create_dimension_breakdown_chart(dimensions: List[DimensionScore]) -> go.Figure:
    """Create a Plotly horizontal bar chart illustrating scoring across dimensions."""
    categories = [d.category for d in dimensions]
    scores = [d.score for d in dimensions]
    weights = [f"Weight: {int(d.weight * 100)}%" for d in dimensions]

    # Assign bar colors per category score
    colors = []
    for s in scores:
        if s >= 85:
            colors.append("#10b981")
        elif s >= 70:
            colors.append("#3b82f6")
        elif s >= 55:
            colors.append("#f59e0b")
        elif s >= 40:
            colors.append("#f97316")
        else:
            colors.append("#ef4444")

    fig = go.Figure(
        go.Bar(
            x=scores,
            y=categories,
            orientation="h",
            text=[f"{s:.1f}% ({w})" for s, w in zip(scores, weights)],
            textposition="auto",
            marker=dict(
                color=colors,
                line=dict(color="rgba(255,255,255,0.2)", width=1),
                cornerradius=6,
            ),
            hoverinfo="x+y",
        )
    )

    fig.update_layout(
        title={
            "text": "<b>Evaluation Dimensions</b>",
            "font": {"size": 18, "color": "#f8fafc"},
            "x": 0.05,
        },
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#94a3b8", "family": "Inter, sans-serif"},
        xaxis=dict(
            range=[0, 105],
            gridcolor="rgba(255,255,255,0.06)",
            zerolinecolor="rgba(255,255,255,0.1)",
            title="Score (%)",
        ),
        yaxis=dict(
            autorange="reversed",
            tickfont={"size": 13, "color": "#f8fafc"},
        ),
        height=280,
        margin=dict(l=10, r=20, t=50, b=20),
    )
    return fig

