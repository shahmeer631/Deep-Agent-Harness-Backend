from __future__ import annotations

from typing import Any, TypedDict

from models import (
    AnalysisResponse,
    CandidateAnalysis,
    CandidateProfile,
    InterviewQuestions,
    MatchResult,
)


class AgentState(TypedDict, total=False):
    resume_bytes: bytes
    resume_filename: str
    job_title: str
    job_description: str
    plan: list[str]
    resume_text: str
    candidate_profile: CandidateProfile
    candidate_analysis: CandidateAnalysis
    match_result: MatchResult
    interview_questions: InterviewQuestions
    analysis_response: AnalysisResponse
    current_step: str
    errors: list[str]
    extras: dict[str, Any]
