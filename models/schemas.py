from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


def _none_to_list(value: Any) -> Any:
    """LLMs often return null for empty arrays — coerce to []."""
    return [] if value is None else value


def _none_to_str(value: Any) -> Any:
    return "" if value is None else value


class CandidateProfile(BaseModel):
    name: str = "Unknown Candidate"
    email: str | None = None
    skills: list[str] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)
    experience: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    summary: str = ""

    @field_validator(
        "skills",
        "education",
        "experience",
        "projects",
        "certifications",
        mode="before",
    )
    @classmethod
    def empty_lists(cls, value: Any) -> Any:
        return _none_to_list(value)

    @field_validator("summary", mode="before")
    @classmethod
    def empty_summary(cls, value: Any) -> Any:
        return _none_to_str(value)

    @field_validator("name", mode="before")
    @classmethod
    def default_name(cls, value: Any) -> Any:
        if value is None or value == "":
            return "Unknown Candidate"
        return value


class MatchResult(BaseModel):
    match_score: int = Field(ge=0, le=100)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    skills_matched: list[str] = Field(default_factory=list)
    skills_missing: list[str] = Field(default_factory=list)
    experience_summary: str = ""
    recommendation: str = ""
    recommendation_label: Literal["hire", "maybe", "pass"] = "maybe"
    reasoning: str = ""

    @field_validator(
        "strengths",
        "weaknesses",
        "skills_matched",
        "skills_missing",
        mode="before",
    )
    @classmethod
    def empty_lists(cls, value: Any) -> Any:
        return _none_to_list(value)

    @field_validator(
        "experience_summary",
        "recommendation",
        "reasoning",
        mode="before",
    )
    @classmethod
    def empty_strings(cls, value: Any) -> Any:
        return _none_to_str(value)

    @field_validator("recommendation_label", mode="before")
    @classmethod
    def normalize_label(cls, value: Any) -> Any:
        if value is None:
            return "maybe"
        text = str(value).strip().lower()
        if text in {"hire", "maybe", "pass"}:
            return text
        return "maybe"


class InterviewQuestions(BaseModel):
    technical: list[str] = Field(default_factory=list)
    behavioral: list[str] = Field(default_factory=list)
    follow_up: list[str] = Field(default_factory=list)

    @field_validator("technical", "behavioral", "follow_up", mode="before")
    @classmethod
    def empty_lists(cls, value: Any) -> Any:
        return _none_to_list(value)


class CandidateAnalysis(BaseModel):
    skills_analysis: str = ""
    experience_analysis: str = ""
    domain_signals: list[str] = Field(default_factory=list)
    seniority_estimate: str = "unknown"
    red_flags: list[str] = Field(default_factory=list)

    @field_validator("domain_signals", "red_flags", mode="before")
    @classmethod
    def empty_lists(cls, value: Any) -> Any:
        return _none_to_list(value)

    @field_validator("skills_analysis", "experience_analysis", mode="before")
    @classmethod
    def empty_strings(cls, value: Any) -> Any:
        return _none_to_str(value)

    @field_validator("seniority_estimate", mode="before")
    @classmethod
    def default_seniority(cls, value: Any) -> Any:
        if value is None or value == "":
            return "unknown"
        return value


class AnalysisResponse(BaseModel):
    id: UUID
    candidate_name: str
    match_score: int
    strengths: list[str]
    weaknesses: list[str]
    skills_matched: list[str]
    skills_missing: list[str]
    experience_summary: str
    recommendation: str
    recommendation_label: Literal["hire", "maybe", "pass"] = "maybe"
    interview_questions: InterviewQuestions
    candidate_profile: CandidateProfile
    job_title: str
    resume_filename: str
    created_at: datetime


class AnalysisSummary(BaseModel):
    id: UUID
    candidate_name: str
    match_score: int
    job_title: str
    recommendation_label: Literal["hire", "maybe", "pass"] | str = "maybe"
    created_at: datetime


class HealthResponse(BaseModel):
    status: str
    llm_configured: bool
    supabase_configured: bool


class ErrorResponse(BaseModel):
    detail: str
    step: str | None = None
    extras: dict[str, Any] = Field(default_factory=dict)
