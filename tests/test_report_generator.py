"""Unit tests for Markdown and JSON report generation."""

import json
from core.schemas import (
    MatchAnalysisReport,
    DimensionScore,
    SkillGapAnalysis,
    ImprovementRecommendations,
    VerdictEnum,
)
from core.report_generator import generate_markdown_report, generate_json_report


def test_generate_markdown_report():
    report = MatchAnalysisReport(
        candidate_name="Alex Mercer",
        target_role="AI Engineer",
        overall_score=89.0,
        verdict=VerdictEnum.STRONG_MATCH,
        executive_summary="Alex is an outstanding fit.",
        dimensions=[
            DimensionScore(
                category="Skills Alignment",
                score=90.0,
                weight=0.40,
                weighted_score=36.0,
                justification="Has PyTorch",
            )
        ],
        skills_analysis=SkillGapAnalysis(
            matched_required_skills=["Python", "PyTorch"],
            missing_required_skills=["Kubernetes"],
        ),
        strengths=["Deep ML knowledge"],
        weaknesses=["Needs cloud certification"],
        recommendations=ImprovementRecommendations(
            resume_optimization_tips=["Add quantified latency figures"],
        ),
    )

    md = generate_markdown_report(report)
    assert "# TalentMatch AI - Comprehensive Evaluation Report" in md
    assert "Alex Mercer" in md
    assert "89.0 / 100" in md
    assert "Strong Match" in md
    assert "PyTorch" in md
    assert "Kubernetes" in md
    assert "Deep ML knowledge" in md


def test_generate_json_report():
    report = MatchAnalysisReport(
        candidate_name="Alex Mercer",
        target_role="AI Engineer",
        overall_score=89.0,
        verdict=VerdictEnum.STRONG_MATCH,
        executive_summary="Alex is an outstanding fit.",
        dimensions=[],
        skills_analysis=SkillGapAnalysis(),
        strengths=[],
        weaknesses=[],
        recommendations=ImprovementRecommendations(),
    )

    json_str = generate_json_report(report)
    data = json.loads(json_str)
    assert data["metadata"]["application"] == "TalentMatch AI"
    assert data["report"]["candidate_name"] == "Alex Mercer"
    assert data["report"]["overall_score"] == 89.0

