from __future__ import annotations

import json

from langchain_core.tools import tool

from models import (
    AnalysisResponse,
    CandidateProfile,
    InterviewQuestions,
    MatchResult,
)
from services import get_supabase_service


def persist_analysis(
    *,
    filename: str,
    extracted_text: str,
    profile: CandidateProfile,
    job_title: str,
    job_description: str,
    match: MatchResult,
    interview: InterviewQuestions,
) -> AnalysisResponse:
    return get_supabase_service().save_analysis(
        filename=filename,
        extracted_text=extracted_text,
        profile=profile,
        job_title=job_title,
        job_description=job_description,
        match=match,
        interview=interview,
    )


@tool("supabase_persistence")
def supabase_persistence_tool(
    filename: str,
    extracted_text: str,
    candidate_json: str,
    job_title: str,
    job_description: str,
    match_json: str,
    interview_json: str,
) -> str:
    """Persist resume, job description, and analysis rows to Supabase.

    Returns the saved AnalysisResponse as JSON.
    """
    profile = CandidateProfile.model_validate_json(candidate_json)
    match = MatchResult.model_validate_json(match_json)
    interview = InterviewQuestions.model_validate_json(interview_json)
    saved = persist_analysis(
        filename=filename,
        extracted_text=extracted_text,
        profile=profile,
        job_title=job_title,
        job_description=job_description,
        match=match,
        interview=interview,
    )
    return saved.model_dump_json()
