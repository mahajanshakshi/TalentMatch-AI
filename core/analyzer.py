"""Resume Parser and Match Analyzer orchestrator."""

import json
import logging
from typing import Callable, Optional

import config
from core.schemas import (
    ParsedResume,
    ParsedJobDescription,
    MatchAnalysisReport,
    VerdictEnum,
    DimensionScore,
)
from core.groq_service import GroqService, GroqServiceError
from core.prompts import (
    RESUME_EXTRACTION_SYSTEM_PROMPT,
    JOB_DESCRIPTION_EXTRACTION_SYSTEM_PROMPT,
    RESUME_MATCH_SYSTEM_PROMPT,
)

logger = logging.getLogger(__name__)


def compute_verdict_from_score(score: float) -> VerdictEnum:
    """Determine the verdict category strictly based on score."""
    if score >= 85.0:
        return VerdictEnum.STRONG_MATCH
    elif score >= 70.0:
        return VerdictEnum.GOOD_MATCH
    elif score >= 55.0:
        return VerdictEnum.POTENTIAL_MATCH
    elif score >= 40.0:
        return VerdictEnum.MODERATE_MATCH
    else:
        return VerdictEnum.LOW_MATCH


def enforce_score_consistency(report: MatchAnalysisReport) -> MatchAnalysisReport:
    """
    Ensure mathematical precision and consistency across dimension weights,
    weighted scores, composite overall score, and matching verdict.
    """
    total_weighted = 0.0
    updated_dimensions = []

    for dim in report.dimensions:
        cat_lower = dim.category.lower()
        if "skill" in cat_lower:
            weight = config.SCORING_WEIGHTS["skills_alignment"]
        elif "experience" in cat_lower:
            weight = config.SCORING_WEIGHTS["experience_relevance"]
        elif "responsibilit" in cat_lower or "role" in cat_lower:
            weight = config.SCORING_WEIGHTS["responsibilities_fit"]
        elif "education" in cat_lower or "credential" in cat_lower:
            weight = config.SCORING_WEIGHTS["education_credentials"]
        else:
            weight = dim.weight if dim.weight > 0 else 0.25

        score = max(0.0, min(100.0, round(float(dim.score), 1)))
        weighted = round(score * weight, 2)
        total_weighted += weighted

        updated_dimensions.append(
            DimensionScore(
                category=dim.category,
                score=score,
                weight=round(weight, 2),
                weighted_score=weighted,
                justification=dim.justification,
                key_findings=dim.key_findings,
            )
        )

    calculated_overall = round(min(100.0, max(0.0, total_weighted)), 1)
    consistent_verdict = compute_verdict_from_score(calculated_overall)

    report.dimensions = updated_dimensions
    report.overall_score = calculated_overall
    report.verdict = consistent_verdict
    return report


class ResumeJDAnalyzer:
    """High-level analyzer coordinating parsing and matching workflows."""

    def __init__(self, groq_service: Optional[GroqService] = None, api_key: Optional[str] = None):
        self.groq_service = groq_service or GroqService(api_key=api_key)

    def parse_resume(self, resume_text: str) -> ParsedResume:
        """Extract structured resume information from raw text."""
        if not resume_text.strip():
            raise ValueError("Resume text is empty.")

        user_prompt = f"Extract structured resume information from the following text:\n\n{resume_text}"
        return self.groq_service.call_structured_json(
            system_prompt=RESUME_EXTRACTION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=ParsedResume,
        )

    def parse_job_description(self, jd_text: str) -> ParsedJobDescription:
        """Extract structured requirements from job description text."""
        if not jd_text.strip():
            raise ValueError("Job description text is empty.")

        user_prompt = f"Extract structured job requirements from the following job description:\n\n{jd_text}"
        return self.groq_service.call_structured_json(
            system_prompt=JOB_DESCRIPTION_EXTRACTION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=ParsedJobDescription,
        )

    def analyze_match(
        self,
        resume_obj: ParsedResume,
        jd_obj: ParsedJobDescription,
        raw_resume_text: str = "",
        raw_jd_text: str = "",
    ) -> MatchAnalysisReport:
        """
        Perform in-depth matching analysis between parsed resume and parsed job description.
        """
        payload = {
            "parsed_resume": resume_obj.model_dump(),
            "parsed_job_description": jd_obj.model_dump(),
        }

        user_prompt = (
            "Perform an objective, explainable evaluation comparing this candidate's resume "
            "against the target job description.\n\n"
            f"EVALUATION DATA (JSON):\n{json.dumps(payload, indent=2)}\n\n"
        )

        if raw_resume_text and len(raw_resume_text) < 15000:
            user_prompt += f"FULL RESUME TEXT FOR CONTEXT:\n{raw_resume_text[:12000]}\n\n"
        if raw_jd_text and len(raw_jd_text) < 10000:
            user_prompt += f"FULL JOB DESCRIPTION TEXT FOR CONTEXT:\n{raw_jd_text[:8000]}\n\n"

        report = self.groq_service.call_structured_json(
            system_prompt=RESUME_MATCH_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=MatchAnalysisReport,
        )

        # Enforce exact mathematical score consistency and verdict alignment
        return enforce_score_consistency(report)

    def run_full_pipeline(
        self,
        resume_text: str,
        jd_text: str,
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ) -> tuple[ParsedResume, ParsedJobDescription, MatchAnalysisReport]:
        """
        Execute full end-to-end pipeline:
        1. Parse Resume
        2. Parse Job Description
        3. Match Analysis
        
        Args:
            resume_text: Cleaned resume string.
            jd_text: Cleaned job description string.
            progress_callback: Optional callback(step_message, fraction_complete).
            
        Returns:
            tuple of (ParsedResume, ParsedJobDescription, MatchAnalysisReport)
        """
        def update_progress(msg: str, frac: float):
            if progress_callback:
                progress_callback(msg, frac)
            logger.info("Pipeline step: %s (%.0f%%)", msg, frac * 100)

        update_progress("Extracting structured candidate profile from resume...", 0.20)
        parsed_resume = self.parse_resume(resume_text)

        update_progress("Extracting structured criteria from job description...", 0.50)
        parsed_jd = self.parse_job_description(jd_text)

        update_progress("Executing AI matching algorithm and scoring dimensions...", 0.80)
        report = self.analyze_match(
            resume_obj=parsed_resume,
            jd_obj=parsed_jd,
            raw_resume_text=resume_text,
            raw_jd_text=jd_text,
        )

        update_progress("Analysis completed successfully!", 1.0)
        return parsed_resume, parsed_jd, report

