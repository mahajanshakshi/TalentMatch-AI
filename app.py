"""TalentMatch AI - Enterprise AI Resume Parser & Intelligent Job Matcher.

Main Streamlit Application.
"""

import os
import importlib
import streamlit as st
import config

# Ensure submodules are refreshed cleanly to avoid cached stale imports
import core.schemas
importlib.reload(core.schemas)
import core.groq_service
importlib.reload(core.groq_service)
import core.analyzer
importlib.reload(core.analyzer)
from core.groq_service import GroqService, GroqServiceError, get_accessible_chat_models
from core.document_parser import extract_resume_text, DocumentParsingError
from core.text_cleaner import clean_text
from core.token_counter import count_tokens
from core.analyzer import ResumeJDAnalyzer
from core.report_generator import generate_markdown_report, generate_json_report
from core.samples import SAMPLE_RESUMES, SAMPLE_JOB_DESCRIPTIONS
from ui.styles import get_css
from ui.components import (
    render_hero_header,
    render_verdict_badge,
    render_skill_pills,
    create_match_gauge_chart,
    create_dimension_breakdown_chart,
)

# -----------------------------------------------------------------------------
# Streamlit Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title=f"{config.APP_NAME} - Enterprise Resume & JD Matcher",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject custom CSS
st.markdown(get_css(), unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Session State Initialization
# -----------------------------------------------------------------------------
if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""
if "resume_file_name" not in st.session_state:
    st.session_state.resume_file_name = ""
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None
if "parsed_resume" not in st.session_state:
    st.session_state.parsed_resume = None
if "parsed_jd" not in st.session_state:
    st.session_state.parsed_jd = None


# -----------------------------------------------------------------------------
# Sidebar Configuration
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image(
        "https://img.icons8.com/fluency/96/artificial-intelligence.png",
        width=56,
    )
    st.title("Settings & Engine")

    # Always reload .env on each render to dynamically reflect changes
    config.load_environment()
    env_api_key = config.get_effective_groq_api_key()

    # Sync session state with .env if not explicitly overridden by user typing
    if "sidebar_groq_key" not in st.session_state or not st.session_state.sidebar_groq_key:
        if env_api_key:
            st.session_state.sidebar_groq_key = env_api_key

    # API Key Configuration Input
    initial_widget_val = st.session_state.get("sidebar_groq_key", env_api_key)
    api_key_input = st.text_input(
        "Groq API Key",
        value=initial_widget_val,
        key="groq_key_input_box",
        type="password",
        placeholder="gsk_...",
        help="Paste your Groq Cloud API key. Automatically loaded from .env if present.",
    )

    # Determine active key
    effective_key = api_key_input.strip() if api_key_input and api_key_input.strip() else env_api_key

    # API Status Check & Reload Control
    col_status, col_reload = st.columns([2, 1])
    with col_reload:
        if st.button("🔄 Reload", help="Reload environment variables from .env file", use_container_width=True):
            config.load_environment()
            fresh_key = config.get_effective_groq_api_key()
            st.session_state.sidebar_groq_key = fresh_key
            st.session_state["groq_key_input_box"] = fresh_key
            st.rerun()

    if effective_key and not effective_key.startswith("your_") and len(effective_key) > 10:
        masked_preview = f"{effective_key[:7]}...{effective_key[-4:]}"
        st.success(f"✅ Groq API Configured (`{masked_preview}`)")
    else:
        st.warning("⚠️ Groq API Key Missing")
        st.info("Paste your key above or add it to `.env` as `GROQ_API_KEY=`.")

    # Model Selection (dynamically resolved to models accessible with this API key)
    accessible_models = get_accessible_chat_models(effective_key)
    current_default_model = config.get_configured_groq_model()
    model_idx = 0
    if current_default_model in accessible_models:
        model_idx = accessible_models.index(current_default_model)

    selected_model = st.selectbox(
        "Groq LLM Model",
        options=accessible_models,
        index=model_idx,
        help="Model used for resume extraction and scoring.",
    )

    st.markdown("---")
    st.subheader("Quick Presets")
    preset_choice = st.selectbox(
        "Load Sample Data",
        options=["Select a sample...", "AI Engineer vs AI Role", "Junior Dev vs AI Role"],
    )

    if preset_choice == "AI Engineer vs AI Role":
        sample_res = list(SAMPLE_RESUMES.values())[0]
        sample_jd = list(SAMPLE_JOB_DESCRIPTIONS.values())[0]
        if st.button("Apply Sample Preset", use_container_width=True):
            st.session_state.resume_text = sample_res.strip()
            st.session_state.resume_file_name = "Alex_Mercer_Resume.pdf (Sample)"
            st.session_state["jd_input_area"] = sample_jd.strip()
            st.rerun()

    elif preset_choice == "Junior Dev vs AI Role":
        sample_res = list(SAMPLE_RESUMES.values())[1]
        sample_jd = list(SAMPLE_JOB_DESCRIPTIONS.values())[0]
        if st.button("Apply Sample Preset", use_container_width=True):
            st.session_state.resume_text = sample_res.strip()
            st.session_state.resume_file_name = "Jordan_Taylor_Resume.docx (Sample)"
            st.session_state["jd_input_area"] = sample_jd.strip()
            st.rerun()

    st.markdown("---")
    st.markdown(
        """
        <div style="font-size: 0.82rem; color: #64748b; line-height: 1.5;">
            <b>Architecture:</b><br>
            • PyMuPDF & python-docx<br>
            • Pydantic v2 JSON Validation<br>
            • Groq LLM (Deterministic, Temp=0)<br>
            • Plotly Interactive Analytics
        </div>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------------------------------------------------------
# Header
# -----------------------------------------------------------------------------
render_hero_header()


# -----------------------------------------------------------------------------
# Input Section: Two Columns (Resume Upload vs Job Description)
# -----------------------------------------------------------------------------
col_resume, col_jd = st.columns([1, 1], gap="large")

with col_resume:
    st.subheader("1. Resume Document")
    uploaded_file = st.file_uploader(
        "Upload Candidate Resume (PDF or DOCX)",
        type=["pdf", "docx"],
        help="Upload PDF or Microsoft Word DOCX resume.",
    )

    # Process uploaded file if new
    if uploaded_file is not None:
        try:
            with st.spinner("Extracting text from document..."):
                extraction_result = extract_resume_text(
                    file_source=uploaded_file,
                    file_name=uploaded_file.name,
                    clean=True,
                )
                st.session_state.resume_text = extraction_result["cleaned_text"]
                st.session_state.resume_file_name = uploaded_file.name
                st.success(
                    f"Parsed **{uploaded_file.name}** "
                    f"({extraction_result['char_count']:,} chars, ~{count_tokens(st.session_state.resume_text):,} tokens)"
                )
        except DocumentParsingError as dpe:
            st.error(f"Extraction Error: {str(dpe)}")
        except Exception as e:
            st.error(f"Unexpected file error: {str(e)}")

    # Editable / Viewable Resume Text Area
    resume_text_val = st.text_area(
        "Extracted Resume Content (Review or Paste Directly):",
        value=st.session_state.resume_text,
        height=320,
        placeholder="Extracted resume text appears here, or you can paste raw resume text manually...",
    )
    if resume_text_val != st.session_state.resume_text:
        st.session_state.resume_text = resume_text_val

    if st.session_state.resume_text:
        st.caption(
            f"📄 **Resume Length:** {len(st.session_state.resume_text):,} characters | "
            f"**Token Estimate:** ~{count_tokens(st.session_state.resume_text):,} tokens"
        )

with col_jd:
    st.subheader("2. Job Description")
    default_jd = st.session_state.get("jd_input_area", "")
    jd_input = st.text_area(
        "Paste Target Job Requirements:",
        value=default_jd,
        key="jd_input_area",
        height=390,
        placeholder="Paste full job description, role overview, required skills, and responsibilities here...",
    )

    if jd_input:
        st.caption(
            f"🎯 **JD Length:** {len(jd_input):,} characters | "
            f"**Token Estimate:** ~{count_tokens(jd_input):,} tokens"
        )


# -----------------------------------------------------------------------------
# Action Trigger Button
# -----------------------------------------------------------------------------
st.markdown("<br>", unsafe_allow_html=True)
run_col1, run_col2, run_col3 = st.columns([1, 2, 1])

with run_col2:
    start_analysis = st.button(
        "🚀 Run AI Resume & JD Match Analysis",
        type="primary",
        use_container_width=True,
        disabled=not bool(st.session_state.resume_text.strip() and jd_input.strip()),
    )


# -----------------------------------------------------------------------------
# Execution Workflow
# -----------------------------------------------------------------------------
if start_analysis:
    if not effective_key or effective_key.startswith("your_"):
        st.error(
            "⚠️ **Groq API Key is required.** Please enter your API key in the left sidebar "
            "or populate `GROQ_API_KEY` inside `.env`."
        )
    elif not st.session_state.resume_text.strip():
        st.error("Please upload a resume or paste resume text before analyzing.")
    elif not jd_input.strip():
        st.error("Please enter or paste a job description before analyzing.")
    else:
        # Initialize Groq & Analyzer
        try:
            groq_svc = GroqService(api_key=effective_key, model=selected_model)
            analyzer = ResumeJDAnalyzer(groq_service=groq_svc)

            progress_bar = st.progress(0.0)
            status_text = st.empty()

            def on_progress(message: str, frac: float):
                status_text.markdown(f"**Status:** {message}")
                progress_bar.progress(frac)

            # Execute pipeline
            parsed_resume, parsed_jd, report = analyzer.run_full_pipeline(
                resume_text=st.session_state.resume_text,
                jd_text=jd_input,
                progress_callback=on_progress,
            )

            # Store in session state
            st.session_state.analysis_results = report
            st.session_state.parsed_resume = parsed_resume
            st.session_state.parsed_jd = parsed_jd

            status_text.empty()
            progress_bar.empty()
            st.balloons()

        except GroqServiceError as gse:
            st.error(f"❌ **AI Service Error:** {str(gse)}")
        except Exception as ex:
            st.error(f"❌ **Analysis Failed:** {str(ex)}")


# -----------------------------------------------------------------------------
# Display Analysis Results
# -----------------------------------------------------------------------------
report = st.session_state.analysis_results
parsed_res = st.session_state.parsed_resume
parsed_job = st.session_state.parsed_jd

if report is not None:
    st.markdown("---")
    st.markdown("## 📊 Evaluation & Match Results")

    # Top Overview Row
    top_c1, top_c2 = st.columns([1.1, 1], gap="medium")

    with top_c1:
        st.markdown(render_verdict_badge(report.verdict), unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="analysis-card">
                <h3 style="margin-top:0; color:#f8fafc;">Executive Summary</h3>
                <p style="color:#cbd5e1; font-size:1.02rem; line-height:1.6;">
                    {report.executive_summary}
                </p>
                <div style="margin-top:1rem; font-size:0.9rem; color:#94a3b8;">
                    <b>Candidate:</b> {report.candidate_name} &nbsp;|&nbsp;
                    <b>Target Role:</b> {report.target_role}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with top_c2:
        gauge_fig = create_match_gauge_chart(report.overall_score, report.verdict.value)
        st.plotly_chart(gauge_fig, use_container_width=True)

    # Detailed Tabs
    tab_scoring, tab_skills, tab_sw, tab_recs, tab_profiles, tab_export = st.tabs([
        "📈 Scoring Dimensions",
        "🎯 Skill Gap Analysis",
        "⚖️ Strengths & Risks",
        "💡 Recommendations",
        "🔍 Structured Profiles",
        "📥 Export & Download",
    ])

    # Tab 1: Scoring Dimensions
    with tab_scoring:
        st.subheader("Dimensional Scoring Breakdown")
        dim_fig = create_dimension_breakdown_chart(report.dimensions)
        st.plotly_chart(dim_fig, use_container_width=True)

        for dim in report.dimensions:
            with st.expander(
                f"**{dim.category}** — {dim.score:.1f}% (Weight: {int(dim.weight * 100)}% | Points: {dim.weighted_score:.1f})",
                expanded=True,
            ):
                st.markdown(f"**Rationale:** {dim.justification}")
                if dim.key_findings:
                    st.markdown("**Key Observations:**")
                    for kf in dim.key_findings:
                        st.markdown(f"- {kf}")

    # Tab 2: Skill Gap Analysis
    with tab_skills:
        st.subheader("Granular Skill Comparison")
        skills = report.skills_analysis

        sk_col1, sk_col2 = st.columns(2, gap="medium")

        with sk_col1:
            st.markdown("#### ✅ Matched Mandatory Skills")
            st.markdown(
                render_skill_pills(skills.matched_required_skills, "matched"),
                unsafe_allow_html=True,
            )

            st.markdown("<br>#### 🌟 Matched Preferred / Bonus Skills", unsafe_allow_html=True)
            st.markdown(
                render_skill_pills(skills.matched_preferred_skills, "preferred"),
                unsafe_allow_html=True,
            )

            st.markdown("<br>#### 🚀 Additional Candidate Proficiencies", unsafe_allow_html=True)
            st.markdown(
                render_skill_pills(skills.additional_candidate_skills, "bonus"),
                unsafe_allow_html=True,
            )

        with sk_col2:
            st.markdown("#### ❌ Missing Mandatory Skills (Critical)")
            if skills.missing_required_skills:
                st.markdown(
                    render_skill_pills(skills.missing_required_skills, "missing"),
                    unsafe_allow_html=True,
                )
            else:
                st.success("No missing mandatory skills detected! Excellent match.")

            st.markdown("<br>#### ⚠️ Missing Preferred Skills", unsafe_allow_html=True)
            st.markdown(
                render_skill_pills(skills.missing_preferred_skills, "missing"),
                unsafe_allow_html=True,
            )

    # Tab 3: Strengths & Weaknesses
    with tab_sw:
        sw_col1, sw_col2 = st.columns(2, gap="medium")

        with sw_col1:
            st.subheader("Top Strengths")
            for strength in report.strengths:
                st.markdown(
                    f'<div class="bullet-card-pos"><b>✓</b> {strength}</div>',
                    unsafe_allow_html=True,
                )

        with sw_col2:
            st.subheader("Identified Gaps & Risks")
            for weakness in report.weaknesses:
                st.markdown(
                    f'<div class="bullet-card-neg"><b>✕</b> {weakness}</div>',
                    unsafe_allow_html=True,
                )

    # Tab 4: Recommendations
    with tab_recs:
        st.subheader("Strategic Improvement Recommendations")
        recs = report.recommendations

        rec1, rec2 = st.columns(2, gap="medium")
        with rec1:
            st.markdown("#### 📝 Resume Optimization & ATS Alignment")
            for tip in recs.resume_optimization_tips:
                st.markdown(
                    f'<div class="bullet-card-tip"><b>Tip:</b> {tip}</div>',
                    unsafe_allow_html=True,
                )

            st.markdown("<br>#### 📊 Framing Quantifiable Business Impact", unsafe_allow_html=True)
            for imp in recs.content_and_impact_metrics:
                st.markdown(
                    f'<div class="bullet-card-tip"><b>Metric:</b> {imp}</div>',
                    unsafe_allow_html=True,
                )

        with rec2:
            st.markdown("#### 🎯 Skills Gap Bridging")
            for b in recs.skills_gap_bridging:
                st.markdown(
                    f'<div class="bullet-card-tip"><b>Bridge:</b> {b}</div>',
                    unsafe_allow_html=True,
                )

            st.markdown("<br>#### 🎙️ High-Priority Interview Focus Topics", unsafe_allow_html=True)
            for p in recs.interview_preparation_focus:
                st.markdown(
                    f'<div class="bullet-card-tip"><b>Focus:</b> {p}</div>',
                    unsafe_allow_html=True,
                )

    # Tab 5: Structured Profiles
    with tab_profiles:
        st.subheader("Extracted Entity Breakdown (Pydantic v2)")
        p_col1, p_col2 = st.columns(2, gap="medium")

        with p_col1:
            st.markdown("#### Parsed Candidate Profile")
            if parsed_res:
                st.json(parsed_res.model_dump())
            else:
                st.info("No parsed resume in memory.")

        with p_col2:
            st.markdown("#### Parsed Job Requirements")
            if parsed_job:
                st.json(parsed_job.model_dump())
            else:
                st.info("No parsed job description in memory.")

    # Tab 6: Export & Download
    with tab_export:
        st.subheader("Export Analysis Report")
        st.write("Download your full report in Markdown or JSON format for your records or ATS.")

        markdown_report_str = generate_markdown_report(report, parsed_res, parsed_job)
        json_report_str = generate_json_report(report, parsed_res, parsed_job)

        down_col1, down_col2 = st.columns(2)

        with down_col1:
            st.download_button(
                label="📄 Download Markdown Report (.md)",
                data=markdown_report_str,
                file_name=f"TalentMatch_Report_{report.candidate_name.replace(' ', '_')}.md",
                mime="text/markdown",
                use_container_width=True,
            )

        with down_col2:
            st.download_button(
                label="📦 Download JSON Data (.json)",
                data=json_report_str,
                file_name=f"TalentMatch_Report_{report.candidate_name.replace(' ', '_')}.json",
                mime="application/json",
                use_container_width=True,
            )

        with st.expander("Report Preview (Markdown)", expanded=False):
            st.markdown(markdown_report_str)

