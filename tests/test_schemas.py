"""Unit tests for Pydantic v2 schemas and validation."""

import pytest
from pydantic import ValidationError
from core.schemas import (
    ContactInfo,
    ParsedResume,
    ParsedJobDescription,
    MatchAnalysisReport,
    DimensionScore,
    SkillGapAnalysis,
    ImprovementRecommendations,
    VerdictEnum,
)


def test_contact_info_valid():
    contact = ContactInfo(
        name="Alice Cooper",
        email="alice@example.com",
        github="github.com/alice",
    )
    assert contact.name == "Alice Cooper"
    assert contact.email == "alice@example.com"
    assert contact.phone is None


def test_dimension_score_boundaries():
    # Valid score
    dim = DimensionScore(
        category="Skills Alignment",
        score=85.5,
        weight=0.40,
        weighted_score=34.2,
        justification="Strong match with mandatory skills.",
    )
    assert dim.score == 85.5

    # Out-of-bounds score should raise ValidationError
    with pytest.raises(ValidationError):
        DimensionScore(
            category="Skills Alignment",
            score=150.0,
            weight=0.40,
            weighted_score=60.0,
            justification="Invalid score",
        )


def test_verdict_fuzzy_matching():
    r1 = MatchAnalysisReport(
        candidate_name="Jane Doe",
        target_role="Software Engineer",
        overall_score=68.0,
        verdict="Partial Match",
    )
    assert r1.verdict == VerdictEnum.POTENTIAL_MATCH

    r2 = MatchAnalysisReport(
        candidate_name="Jane Doe",
        target_role="Software Engineer",
        overall_score=92.0,
        verdict="High Match",
    )
    assert r2.verdict == VerdictEnum.STRONG_MATCH


def test_match_analysis_report_serialization():
    report = MatchAnalysisReport(
        candidate_name="John Doe",
        target_role="AI Engineer",
        overall_score=88.5,
        verdict=VerdictEnum.STRONG_MATCH,
        executive_summary="Candidate demonstrates excellent fit.",
        dimensions=[
            DimensionScore(
                category="Skills Alignment",
                score=90.0,
                weight=0.40,
                weighted_score=36.0,
                justification="Has PyTorch and Python",
            ),
            DimensionScore(
                category="Experience Relevance",
                score=85.0,
                weight=0.25,
                weighted_score=21.25,
                justification="5 years in AI",
            ),
            DimensionScore(
                category="Responsibilities Fit",
                score=88.0,
                weight=0.20,
                weighted_score=17.6,
                justification="Prior RAG experience",
            ),
            DimensionScore(
                category="Education & Credentials",
                score=90.0,
                weight=0.15,
                weighted_score=13.5,
                justification="M.S. in Computer Science",
            ),
        ],
        skills_analysis=SkillGapAnalysis(
            matched_required_skills=["Python", "PyTorch"],
            missing_required_skills=[],
            matched_preferred_skills=["Docker"],
        ),
        strengths=["Solid ML background", "Strong communication"],
        weaknesses=["No Kubernetes production experience"],
        recommendations=ImprovementRecommendations(
            resume_optimization_tips=["Highlight model latency gains"],
            skills_gap_bridging=["Learn Kubernetes basics"],
        ),
    )

    dumped = report.model_dump()
    assert dumped["candidate_name"] == "John Doe"
    assert dumped["verdict"] == "Strong Match"
    assert len(dumped["dimensions"]) == 4

    # Test roundtrip
    restored = MatchAnalysisReport.model_validate(dumped)
    assert restored.overall_score == 88.5
    assert restored.verdict == VerdictEnum.STRONG_MATCH

