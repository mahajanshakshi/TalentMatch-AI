"""Custom CSS styles for the TalentMatch AI Streamlit interface."""

MAIN_CSS = """
<style>
/* Main Container Styling */
.main {
    background-color: transparent;
}

/* Header Banner */
.hero-header {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
    border-radius: 16px;
    padding: 2.2rem 2.5rem;
    color: white;
    margin-bottom: 2rem;
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.15), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.hero-title {
    font-size: 2.4rem;
    font-weight: 800;
    letter-spacing: -0.025em;
    margin: 0;
    background: linear-gradient(90deg, #38bdf8, #818cf8, #c084fc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero-subtitle {
    font-size: 1.05rem;
    color: #94a3b8;
    margin-top: 0.5rem;
    font-weight: 400;
}

/* Cards */
.analysis-card {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1.25rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
}

/* Verdict Badges */
.verdict-badge {
    display: inline-block;
    padding: 0.5rem 1.2rem;
    border-radius: 9999px;
    font-weight: 700;
    font-size: 1.1rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 1rem;
}

.verdict-strong {
    background: linear-gradient(135deg, #059669 0%, #10b981 100%);
    color: #ffffff;
    box-shadow: 0 4px 14px 0 rgba(16, 185, 129, 0.39);
}

.verdict-good {
    background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
    color: #ffffff;
    box-shadow: 0 4px 14px 0 rgba(59, 130, 246, 0.39);
}

.verdict-potential {
    background: linear-gradient(135deg, #d97706 0%, #f59e0b 100%);
    color: #ffffff;
    box-shadow: 0 4px 14px 0 rgba(245, 158, 11, 0.39);
}

.verdict-moderate {
    background: linear-gradient(135deg, #ea580c 0%, #f97316 100%);
    color: #ffffff;
    box-shadow: 0 4px 14px 0 rgba(249, 115, 22, 0.39);
}

.verdict-low {
    background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%);
    color: #ffffff;
    box-shadow: 0 4px 14px 0 rgba(239, 68, 68, 0.39);
}

/* Skill Pills */
.skill-pill {
    display: inline-block;
    padding: 0.3rem 0.75rem;
    margin: 0.25rem 0.25rem;
    border-radius: 6px;
    font-size: 0.85rem;
    font-weight: 600;
    transition: all 0.2s ease;
}

.skill-pill-matched {
    background: rgba(16, 185, 129, 0.15);
    color: #10b981;
    border: 1px solid rgba(16, 185, 129, 0.35);
}

.skill-pill-preferred {
    background: rgba(59, 130, 246, 0.15);
    color: #3b82f6;
    border: 1px solid rgba(59, 130, 246, 0.35);
}

.skill-pill-missing {
    background: rgba(239, 68, 68, 0.15);
    color: #ef4444;
    border: 1px solid rgba(239, 68, 68, 0.35);
}

.skill-pill-bonus {
    background: rgba(168, 85, 247, 0.15);
    color: #a855f7;
    border: 1px solid rgba(168, 85, 247, 0.35);
}

/* Dimension Score Bar */
.dim-row {
    padding: 0.85rem 1rem;
    border-radius: 8px;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    margin-bottom: 0.75rem;
}

.dim-title {
    font-weight: 700;
    font-size: 0.95rem;
}

.dim-score-badge {
    float: right;
    font-weight: 800;
    padding: 0.15rem 0.6rem;
    border-radius: 4px;
    font-size: 0.9rem;
}

/* Strengths / Weaknesses bullet cards */
.bullet-card-pos {
    border-left: 4px solid #10b981;
    background: rgba(16, 185, 129, 0.05);
    padding: 0.75rem 1rem;
    margin-bottom: 0.6rem;
    border-radius: 0 8px 8px 0;
}

.bullet-card-neg {
    border-left: 4px solid #ef4444;
    background: rgba(239, 68, 68, 0.05);
    padding: 0.75rem 1rem;
    margin-bottom: 0.6rem;
    border-radius: 0 8px 8px 0;
}

.bullet-card-tip {
    border-left: 4px solid #3b82f6;
    background: rgba(59, 130, 246, 0.05);
    padding: 0.75rem 1rem;
    margin-bottom: 0.6rem;
    border-radius: 0 8px 8px 0;
}

/* Sidebar styling */
[data-testid="stSidebar"] {
    border-right: 1px solid rgba(255, 255, 255, 0.1);
}
</style>
"""


def get_css() -> str:
    """Return the application CSS stylesheet."""
    return MAIN_CSS

