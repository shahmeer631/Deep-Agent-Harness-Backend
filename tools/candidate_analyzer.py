from __future__ import annotations

import json

from langchain_core.tools import tool

from models import CandidateAnalysis, CandidateProfile
from prompts import ANALYZE_CANDIDATE_PROMPT
from services import get_llm_service


def analyze_candidate_profile(
    profile: CandidateProfile,
    resume_text: str,
) -> CandidateAnalysis:
    prompt = ANALYZE_CANDIDATE_PROMPT.format(
        candidate_json=json.dumps(profile.model_dump(), indent=2),
        resume_excerpt=resume_text[:8000],
    )
    return get_llm_service().structured_completion(prompt, CandidateAnalysis)


@tool("candidate_analyzer")
def candidate_analyzer_tool(candidate_json: str, resume_excerpt: str) -> str:
    """Analyze candidate skills depth, experience trajectory, and seniority.

    Used after resume parsing and before job matching.
    """
    profile = CandidateProfile.model_validate_json(candidate_json)
    analysis = analyze_candidate_profile(profile, resume_excerpt)
    return analysis.model_dump_json()
