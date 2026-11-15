"""Unit tests for analyzer logic, consistency enforcement, and scoring math."""

import pytest
from unittest.mock import MagicMock
from core.schemas import (
    MatchAnalysisReport,
    DimensionScore,
    SkillGapAnalysis,
    ImprovementRecommendations,
    VerdictEnum,
    ParsedResume,
    ParsedJobDescription,
)
from core.analyzer import (
    compute_verdict_from_score,
    enforce_score_consistency,
    ResumeJDAnalyzer,
)


def test_verdict_calculation():
    assert compute_verdict_from_score(92.0) == VerdictEnum.STRONG_MATCH
    assert compute_verdict_from_score(85.0) == VerdictEnum.STRONG_MATCH
    assert compute_verdict_from_score(78.5) == VerdictEnum.GOOD_MATCH
    assert compute_verdict_from_score(62.0) == VerdictEnum.POTENTIAL_MATCH
    assert compute_verdict_from_score(45.0) == VerdictEnum.MODERATE_MATCH
    assert compute_verdict_from_score(30.0) == VerdictEnum.LOW_MATCH


def test_enforce_score_consistency():
    # Construct a report where the LLM might have had a slight arithmetic or verdict mismatch
    raw_report = MatchAnalysisReport(
        candidate_name="Bob Test",
        target_role="Data Scientist",
        overall_score=50.0,  # deliberately wrong
        verdict=VerdictEnum.LOW_MATCH,  # deliberately wrong
        executive_summary="Testing math consistency",
        dimensions=[
            DimensionScore(
                category="Skills Alignment",
                score=80.0,  # 80 * 0.40 = 32.0
                weight=0.40,
                weighted_score=0.0,
                justification="Has core skills",
            ),
            DimensionScore(
                category="Experience Relevance",
                score=70.0,  # 70 * 0.25 = 17.5
                weight=0.25,
                weighted_score=0.0,
                justification="Relevant experience",
            ),
            DimensionScore(
                category="Responsibilities Fit",
                score=75.0,  # 75 * 0.20 = 15.0
                weight=0.20,
                weighted_score=0.0,
                justification="Good fit",
            ),
            DimensionScore(
                category="Education & Credentials",
                score=80.0,  # 80 * 0.15 = 12.0
                weight=0.15,
                weighted_score=0.0,
                justification="B.S. in CS",
            ),
        ],
        skills_analysis=SkillGapAnalysis(
            matched_required_skills=["Python"],
            missing_required_skills=[],
        ),
        strengths=["Good fundamentals"],
        weaknesses=[],
        recommendations=ImprovementRecommendations(),
    )

    # 32.0 + 17.5 + 15.0 + 12.0 = 76.5 -> Verdict must be GOOD_MATCH
    corrected = enforce_score_consistency(raw_report)
    assert corrected.overall_score == 76.5
    assert corrected.verdict == VerdictEnum.GOOD_MATCH
    assert corrected.dimensions[0].weighted_score == 32.0


def test_analyzer_mock_pipeline():
    mock_groq = MagicMock()
    mock_groq.is_ready.return_value = True

    dummy_resume = ParsedResume(
        candidate_name="Alice Candidate",
        professional_summary="Senior developer",
    )
    dummy_jd = ParsedJobDescription(
        job_title="Senior Python Dev",
        role_summary="Backend engineering",
    )
    dummy_report = MatchAnalysisReport(
        candidate_name="Alice Candidate",
        target_role="Senior Python Dev",
        overall_score=85.0,
        verdict=VerdictEnum.STRONG_MATCH,
        executive_summary="Excellent fit.",
        dimensions=[
            DimensionScore(
                category="Skills Alignment",
                score=85.0,
                weight=0.40,
                weighted_score=34.0,
                justification="Strong skills",
            ),
            DimensionScore(
                category="Experience Relevance",
                score=85.0,
                weight=0.25,
                weighted_score=21.25,
                justification="Experienced",
            ),
            DimensionScore(
                category="Responsibilities Fit",
                score=85.0,
                weight=0.20,
                weighted_score=17.0,
                justification="Fit",
            ),
            DimensionScore(
                category="Education & Credentials",
                score=85.0,
                weight=0.15,
                weighted_score=12.75,
                justification="Credentials",
            ),
        ],
        skills_analysis=SkillGapAnalysis(),
        strengths=["Speed"],
        weaknesses=["None"],
        recommendations=ImprovementRecommendations(),
    )

    mock_groq.call_structured_json.side_effect = [dummy_resume, dummy_jd, dummy_report]

    analyzer = ResumeJDAnalyzer(groq_service=mock_groq)
    res, jd, rep = analyzer.run_full_pipeline("sample resume", "sample jd")

    assert res.candidate_name == "Alice Candidate"
    assert jd.job_title == "Senior Python Dev"
    assert rep.overall_score == 85.0
    assert rep.verdict == VerdictEnum.STRONG_MATCH

