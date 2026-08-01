from __future__ import annotations

import json

from langchain_core.tools import tool

from models import CandidateProfile, InterviewQuestions, MatchResult
from prompts import INTERVIEW_QUESTIONS_PROMPT
from services import get_llm_service


def generate_interview_questions(
    profile: CandidateProfile,
    match: MatchResult,
    job_title: str,
    job_description: str,
) -> InterviewQuestions:
    prompt = INTERVIEW_QUESTIONS_PROMPT.format(
        candidate_json=json.dumps(profile.model_dump(), indent=2),
        match_json=json.dumps(match.model_dump(), indent=2),
        job_title=job_title,
        job_description=job_description,
    )
    return get_llm_service().structured_completion(prompt, InterviewQuestions)


@tool("interview_question_generator")
def interview_question_generator_tool(
    candidate_json: str,
    match_json: str,
    job_title: str,
    job_description: str,
) -> str:
    """Generate technical, behavioral, and follow-up interview questions.

    Questions should probe gaps identified in the match assessment.
    """
    profile = CandidateProfile.model_validate_json(candidate_json)
    match = MatchResult.model_validate_json(match_json)
    questions = generate_interview_questions(
        profile, match, job_title, job_description
    )
    return questions.model_dump_json()
