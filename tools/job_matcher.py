from __future__ import annotations

import json

from langchain_core.tools import tool

from models import CandidateProfile, MatchResult
from prompts import MATCH_CANDIDATE_PROMPT
from services import get_llm_service


def match_candidate_to_job(
    profile: CandidateProfile,
    job_title: str,
    job_description: str,
) -> MatchResult:
    prompt = MATCH_CANDIDATE_PROMPT.format(
        candidate_json=json.dumps(profile.model_dump(), indent=2),
        job_title=job_title,
        job_description=job_description,
    )
    result = get_llm_service().structured_completion(prompt, MatchResult)
    result.match_score = max(0, min(100, result.match_score))
    return result


@tool("candidate_matcher")
def candidate_matcher_tool(
    candidate_json: str,
    job_title: str,
    job_description: str,
) -> str:
    """Compare a candidate profile JSON against a job description.

    Returns calibrated match_score, strengths, weaknesses, skills_matched,
    skills_missing, recommendation, and recommendation_label.
    """
    profile = CandidateProfile.model_validate_json(candidate_json)
    result = match_candidate_to_job(profile, job_title, job_description)
    return result.model_dump_json()
