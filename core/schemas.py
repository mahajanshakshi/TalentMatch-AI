"""Pydantic v2 schemas for structured resume parsing, JD extraction, and match analysis."""

from enum import Enum
from typing import List, Optional, Any, Union
from pydantic import BaseModel, Field, AliasChoices, field_validator


# -------------------------------------------------------------------------
# Candidate / Resume Schemas
# -------------------------------------------------------------------------

class ContactInfo(BaseModel):
    """Candidate contact and portfolio coordinates."""
    name: Optional[str] = Field(default="Candidate", description="Full name of candidate")
    email: Optional[str] = Field(default=None, description="Primary email address")
    phone: Optional[str] = Field(default=None, description="Phone number")
    linkedin: Optional[str] = Field(default=None, description="LinkedIn profile URL or username")
    github: Optional[str] = Field(default=None, description="GitHub profile URL or username")
    portfolio: Optional[str] = Field(default=None, description="Personal website or portfolio URL")
    location: Optional[str] = Field(default=None, description="City, State, Country or Remote status")

    @field_validator("name", mode="before")
    @classmethod
    def clean_name(cls, v):
        return v if v else "Candidate"


class WorkExperienceItem(BaseModel):
    """Individual career position."""
    job_title: Optional[str] = Field(default="Professional", validation_alias=AliasChoices("job_title", "title", "role"), description="Job or role title")
    company: Optional[str] = Field(default="Company", validation_alias=AliasChoices("company", "organization", "employer"), description="Company or organization name")
    location: Optional[str] = Field(default=None, description="Location of the position")
    start_date: Optional[str] = Field(default=None, description="Start date (e.g. Jan 2021)")
    end_date: Optional[str] = Field(default=None, description="End date or 'Present'")
    highlights: List[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("highlights", "responsibilities", "achievements"),
        description="Key accomplishments, measurable impacts, and responsibilities"
    )

    @field_validator("job_title", "company", mode="before")
    @classmethod
    def clean_work_fields(cls, v):
        return v if v else "Not specified"

    @field_validator("highlights", mode="before")
    @classmethod
    def normalize_highlights(cls, v):
        if isinstance(v, str):
            return [v]
        return v or []


class EducationItem(BaseModel):
    """Academic qualification."""
    degree: Optional[str] = Field(default="Degree", description="Degree type (e.g. B.S., M.S., Ph.D.)")
    field_of_study: Optional[str] = Field(default=None, validation_alias=AliasChoices("field_of_study", "major", "specialization"), description="Major or specialization")
    institution: Optional[str] = Field(default="Institution", validation_alias=AliasChoices("institution", "university", "school", "college"), description="University, college, or school")
    graduation_year: Optional[str] = Field(default=None, validation_alias=AliasChoices("graduation_year", "year"), description="Year or expected year of graduation")
    gpa_or_honors: Optional[str] = Field(default=None, validation_alias=AliasChoices("gpa_or_honors", "honors", "gpa"), description="GPA or honors if mentioned")

    @field_validator("degree", "institution", mode="before")
    @classmethod
    def clean_edu_fields(cls, v):
        return v if v else "Not specified"


class ProjectItem(BaseModel):
    """Notable project."""
    name: str = Field(default="Project", validation_alias=AliasChoices("name", "title", "project_name"), description="Project title or name")
    description: str = Field(default="", description="Overview and key deliverables of the project")
    technologies: List[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("technologies", "tech_stack", "tools"),
        description="List of tools, languages, or libraries utilized"
    )

    @field_validator("technologies", mode="before")
    @classmethod
    def normalize_technologies(cls, v):
        if isinstance(v, str):
            return [v]
        return v or []


class SkillsCategorized(BaseModel):
    """Categorized skill set."""
    technical_skills: List[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("technical_skills", "hard_skills", "technical"),
        description="Languages, frameworks, core technical skills (e.g. Python, PyTorch)"
    )
    tools_and_platforms: List[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("tools_and_platforms", "tools", "platforms"),
        description="Developer tools, cloud, infrastructure (e.g. Docker, AWS, Git)"
    )
    soft_skills: List[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("soft_skills", "interpersonal_skills"),
        description="Communication, leadership, collaboration, problem solving"
    )
    domain_knowledge: List[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("domain_knowledge", "domains", "industry_knowledge"),
        description="Industry or subject-matter expertise (e.g. NLP, FinTech, Healthcare)"
    )


class ParsedResume(BaseModel):
    """Complete structured resume representation."""
    candidate_name: Optional[str] = Field(default="Candidate", validation_alias=AliasChoices("candidate_name", "name", "full_name"), description="Full candidate name")
    contact_info: ContactInfo = Field(default_factory=ContactInfo)
    professional_summary: Optional[str] = Field(
        default="",
        validation_alias=AliasChoices("professional_summary", "summary", "profile", "objective"),
        description="Executive summary or professional objective"
    )

    @field_validator("candidate_name", mode="before")
    @classmethod
    def clean_candidate_name(cls, v):
        return v if v else "Candidate"

    @field_validator("professional_summary", mode="before")
    @classmethod
    def clean_summary(cls, v):
        return v if v else ""
    skills: SkillsCategorized = Field(default_factory=SkillsCategorized)
    experience: List[WorkExperienceItem] = Field(default_factory=list, validation_alias=AliasChoices("experience", "work_experience", "employment_history"))
    education: List[EducationItem] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    projects: List[ProjectItem] = Field(default_factory=list)
    total_experience_years: Optional[float] = Field(
        default=None,
        validation_alias=AliasChoices("total_experience_years", "years_of_experience", "total_years"),
        description="Estimated total professional experience in years"
    )

    @field_validator("certifications", mode="before")
    @classmethod
    def normalize_certifications(cls, v):
        if not v:
            return []
        normalized = []
        for item in v:
            if isinstance(item, str):
                normalized.append(item)
            elif isinstance(item, dict):
                parts = [str(val) for val in item.values() if val]
                normalized.append(" - ".join(parts) if parts else str(item))
            else:
                normalized.append(str(item))
        return normalized


# -------------------------------------------------------------------------
# Job Description Schemas
# -------------------------------------------------------------------------

class ParsedJobDescription(BaseModel):
    """Complete structured job requirement representation."""
    job_title: str = Field(default="Target Role", description="Job or position title")
    company: Optional[str] = Field(default=None, description="Hiring company name if provided")
    experience_level: str = Field(
        default="Not specified",
        description="Seniority level (Entry, Mid, Senior, Lead, Executive)"
    )
    min_years_experience: Optional[float] = Field(
        default=None,
        description="Minimum years of required professional experience"
    )
    required_technical_skills: List[str] = Field(
        default_factory=list,
        description="Mandatory technical competencies and tools"
    )
    preferred_technical_skills: List[str] = Field(
        default_factory=list,
        description="Preferred or nice-to-have technical skills"
    )
    soft_skills: List[str] = Field(
        default_factory=list,
        description="Interpersonal, collaboration, and work style requirements"
    )
    tools_and_platforms: List[str] = Field(
        default_factory=list,
        description="Required tools, cloud platforms, and environments"
    )
    education_requirements: List[str] = Field(
        default_factory=list,
        description="Required academic degrees or fields"
    )
    core_responsibilities: List[str] = Field(
        default_factory=list,
        description="Primary day-to-day duties and deliverables"
    )
    role_summary: str = Field(
        default="",
        description="Brief synopsis of the role purpose and team mission"
    )

    @field_validator("job_title", mode="before")
    @classmethod
    def clean_jd_title(cls, v):
        return v if v else "Target Role"

    @field_validator("role_summary", mode="before")
    @classmethod
    def clean_jd_summary(cls, v):
        return v if v else ""


# -------------------------------------------------------------------------
# Match Analysis & Reporting Schemas
# -------------------------------------------------------------------------

class VerdictEnum(str, Enum):
    STRONG_MATCH = "Strong Match"
    GOOD_MATCH = "Good Match"
    POTENTIAL_MATCH = "Potential Match"
    MODERATE_MATCH = "Moderate Match"
    LOW_MATCH = "Low Match"


class DimensionScore(BaseModel):
    """Individual evaluation dimension score."""
    category: str = Field(default="Evaluation Dimension", validation_alias=AliasChoices("category", "dimension", "name"), description="Name of the scoring dimension")
    score: float = Field(default=70.0, ge=0.0, le=100.0, description="Raw score between 0 and 100")
    weight: float = Field(default=0.25, ge=0.0, le=1.0, description="Dimension weighting factor")
    weighted_score: float = Field(default=17.5, ge=0.0, le=100.0, description="Weighted contribution")
    justification: str = Field(default="", validation_alias=AliasChoices("justification", "reason", "rationale"), description="Explainable rationale for this score")
    key_findings: List[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("key_findings", "observations", "findings"),
        description="Bullet observations supporting the dimension score"
    )

    @field_validator("score", "weight", "weighted_score", mode="before")
    @classmethod
    def clean_numerical(cls, v):
        if isinstance(v, str):
            v = v.replace("%", "").strip()
        try:
            return float(v)
        except Exception:
            return 0.0

    @field_validator("key_findings", mode="before")
    @classmethod
    def clean_findings(cls, v):
        if isinstance(v, str):
            return [v]
        return v or []


class SkillGapAnalysis(BaseModel):
    """Granular comparison of skills."""
    matched_required_skills: List[str] = Field(
        default_factory=list,
        description="Required JD skills found in resume"
    )
    matched_preferred_skills: List[str] = Field(
        default_factory=list,
        description="Nice-to-have JD skills found in resume"
    )
    missing_required_skills: List[str] = Field(
        default_factory=list,
        description="Mandatory JD skills not evidenced in resume"
    )
    missing_preferred_skills: List[str] = Field(
        default_factory=list,
        description="Preferred JD skills absent from resume"
    )
    additional_candidate_skills: List[str] = Field(
        default_factory=list,
        description="Valuable candidate skills not explicitly requested"
    )

    @field_validator(
        "matched_required_skills",
        "matched_preferred_skills",
        "missing_required_skills",
        "missing_preferred_skills",
        "additional_candidate_skills",
        mode="before",
    )
    @classmethod
    def clean_skill_lists(cls, v):
        if isinstance(v, str):
            return [s.strip("- *").strip() for s in v.split(",") if s.strip()]
        elif isinstance(v, list):
            res = []
            for item in v:
                if isinstance(item, str):
                    res.append(item)
                elif isinstance(item, dict):
                    res.extend([str(val) for val in item.values() if val])
            return res
        return v or []


class ImprovementRecommendations(BaseModel):
    """Actionable recommendations for candidate optimization."""
    resume_optimization_tips: List[str] = Field(
        default_factory=list,
        description="Concrete formatting and wording tweaks to boost ATS alignment"
    )
    content_and_impact_metrics: List[str] = Field(
        default_factory=list,
        description="Suggestions for highlighting business impact and quantifiable metrics"
    )
    skills_gap_bridging: List[str] = Field(
        default_factory=list,
        description="Recommendations on key technologies or certifications to acquire"
    )
    interview_preparation_focus: List[str] = Field(
        default_factory=list,
        description="Specific topics the candidate should be prepared to defend"
    )

    @field_validator(
        "resume_optimization_tips",
        "content_and_impact_metrics",
        "skills_gap_bridging",
        "interview_preparation_focus",
        mode="before",
    )
    @classmethod
    def clean_rec_lists(cls, v):
        if isinstance(v, str):
            return [line.strip("- *").strip() for line in v.split("\n") if line.strip()]
        elif isinstance(v, list):
            res = []
            for item in v:
                if isinstance(item, str):
                    res.append(item)
                elif isinstance(item, dict):
                    res.extend([str(val) for val in item.values() if val])
            return res
        return v or []


class MatchAnalysisReport(BaseModel):
    """Complete explainable resume-JD evaluation report."""
    candidate_name: str = Field(default="Candidate", description="Name of the candidate evaluated")
    target_role: str = Field(default="Target Role", description="Job title evaluated against")
    overall_score: float = Field(default=70.0, ge=0.0, le=100.0, description="Composite score (0-100)")
    verdict: VerdictEnum = Field(default=VerdictEnum.GOOD_MATCH, description="Categorical match verdict")
    executive_summary: str = Field(
        default="",
        description="High-level narrative explaining the match decision and hiring viability"
    )
    dimensions: List[DimensionScore] = Field(
        default_factory=list,
        description="Detailed dimensional breakdown with explainability"
    )
    skills_analysis: SkillGapAnalysis = Field(default_factory=SkillGapAnalysis, description="Granular skill gap analysis")
    strengths: List[str] = Field(default_factory=list, description="Top candidate strengths aligned to the role")
    weaknesses: List[str] = Field(default_factory=list, description="Identified gaps, risks, or weak alignments")
    recommendations: ImprovementRecommendations = Field(
        default_factory=ImprovementRecommendations,
        description="Actionable improvement recommendations"
    )

    @field_validator("candidate_name", "target_role", "executive_summary", mode="before")
    @classmethod
    def clean_report_strings(cls, v):
        return v if v else "Not specified"

    @field_validator("overall_score", mode="before")
    @classmethod
    def clean_overall_score(cls, v):
        if isinstance(v, str):
            v = v.replace("%", "").strip()
        try:
            return max(0.0, min(100.0, float(v)))
        except Exception:
            return 70.0

    @field_validator("strengths", "weaknesses", mode="before")
    @classmethod
    def clean_list_fields(cls, v):
        if isinstance(v, str):
            return [line.strip("- *").strip() for line in v.split("\n") if line.strip()]
        return v or []

    @field_validator("verdict", mode="before")
    @classmethod
    def clean_verdict(cls, v):
        if isinstance(v, str):
            v_lower = v.lower()
            if any(term in v_lower for term in ["strong", "high", "excellent", "great", "top"]):
                return VerdictEnum.STRONG_MATCH
            elif any(term in v_lower for term in ["good", "solid"]):
                return VerdictEnum.GOOD_MATCH
            elif any(term in v_lower for term in ["potential", "partial", "fair", "average", "promising"]):
                return VerdictEnum.POTENTIAL_MATCH
            elif any(term in v_lower for term in ["moderate", "medium"]):
                return VerdictEnum.MODERATE_MATCH
            elif any(term in v_lower for term in ["low", "poor", "weak", "not", "bad", "unlikely", "no match"]):
                return VerdictEnum.LOW_MATCH
            return VerdictEnum.POTENTIAL_MATCH
        return v or VerdictEnum.POTENTIAL_MATCH

