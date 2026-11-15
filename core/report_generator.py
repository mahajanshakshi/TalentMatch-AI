"""Report generation utilities for downloading analysis results in Markdown, JSON, and Text."""

import json
from datetime import datetime, timezone
from core.schemas import MatchAnalysisReport, ParsedResume, ParsedJobDescription


def generate_markdown_report(
    report: MatchAnalysisReport,
    resume: ParsedResume | None = None,
    jd: ParsedJobDescription | None = None,
) -> str:
    """Generate a comprehensive, beautiful Markdown report for download."""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    md = []
    md.append(f"# TalentMatch AI - Comprehensive Evaluation Report")
    md.append(f"**Generated:** {now_str}  \n**Candidate:** {report.candidate_name}  \n**Target Role:** {report.target_role}")
    md.append("\n---\n")

    # Executive Overview
    md.append("## 1. Executive Summary")
    md.append(f"- **Overall Match Score:** `{report.overall_score:.1f} / 100`")
    md.append(f"- **Verdict:** **{report.verdict.value}**")
    md.append(f"\n> {report.executive_summary}\n")

    # Dimension Breakdown
    md.append("## 2. Dimensional Score Breakdown")
    md.append("| Dimension | Score | Weight | Contribution | Justification |")
    md.append("| :--- | :---: | :---: | :---: | :--- |")
    for dim in report.dimensions:
        md.append(
            f"| **{dim.category}** | {dim.score:.1f}% | {int(dim.weight * 100)}% | "
            f"{dim.weighted_score:.1f} pts | {dim.justification} |"
        )
    md.append("")

    # Skills Gap Analysis
    md.append("## 3. Skill Gap Analysis")
    skills = report.skills_analysis

    md.append("### Matched Required Skills")
    if skills.matched_required_skills:
        for s in skills.matched_required_skills:
            md.append(f"- [x] {s}")
    else:
        md.append("_None detected._")
    md.append("")

    md.append("### Matched Preferred / Bonus Skills")
    if skills.matched_preferred_skills:
        for s in skills.matched_preferred_skills:
            md.append(f"- [x] {s}")
    else:
        md.append("_None detected._")
    md.append("")

    md.append("### Missing Required Skills (Critical Gaps)")
    if skills.missing_required_skills:
        for s in skills.missing_required_skills:
            md.append(f"- [ ] **{s}**")
    else:
        md.append("_All required skills satisfied!_")
    md.append("")

    md.append("### Missing Preferred Skills")
    if skills.missing_preferred_skills:
        for s in skills.missing_preferred_skills:
            md.append(f"- [ ] {s}")
    else:
        md.append("_No preferred skills missing._")
    md.append("")

    if skills.additional_candidate_skills:
        md.append("### Additional Candidate Proficiencies")
        for s in skills.additional_candidate_skills:
            md.append(f"- + {s}")
        md.append("")

    # Strengths and Weaknesses
    md.append("## 4. Key Strengths & Potential Risks")
    md.append("### Top Candidate Strengths")
    for st in report.strengths:
        md.append(f"- **+** {st}")
    md.append("")

    md.append("### Identified Weaknesses / Areas for Attention")
    for w in report.weaknesses:
        md.append(f"- **-** {w}")
    md.append("")

    # Actionable Recommendations
    md.append("## 5. Actionable Improvement Recommendations")
    recs = report.recommendations

    if recs.resume_optimization_tips:
        md.append("### Resume Optimization & ATS Alignment")
        for tip in recs.resume_optimization_tips:
            md.append(f"1. {tip}")
        md.append("")

    if recs.content_and_impact_metrics:
        md.append("### Framing Quantifiable Impact")
        for imp in recs.content_and_impact_metrics:
            md.append(f"1. {imp}")
        md.append("")

    if recs.skills_gap_bridging:
        md.append("### Skills Gap Bridging")
        for b in recs.skills_gap_bridging:
            md.append(f"1. {b}")
        md.append("")

    if recs.interview_preparation_focus:
        md.append("### Interview Preparation Topics")
        for p in recs.interview_preparation_focus:
            md.append(f"1. {p}")
        md.append("")

    md.append("---\n*Generated autonomously by TalentMatch AI.*")
    return "\n".join(md)


def generate_json_report(
    report: MatchAnalysisReport,
    resume: ParsedResume | None = None,
    jd: ParsedJobDescription | None = None,
) -> str:
    """Generate structured JSON report for API or system export."""
    payload = {
        "metadata": {
            "application": "TalentMatch AI",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "1.0.0",
        },
        "report": report.model_dump(),
    }
    if resume:
        payload["parsed_resume"] = resume.model_dump()
    if jd:
        payload["parsed_job_description"] = jd.model_dump()

    return json.dumps(payload, indent=2, ensure_ascii=False)
