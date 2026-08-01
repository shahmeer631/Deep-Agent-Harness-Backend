from __future__ import annotations

from datetime import datetime, timezone

from graph.state import AgentState
from models import (
    AnalysisResponse,
    CandidateAnalysis,
    CandidateProfile,
    InterviewQuestions,
    MatchResult,
)
from tools import (
    candidate_analyzer_tool,
    candidate_matcher_tool,
    extract_text_from_pdf,
    interview_question_generator_tool,
    resume_parser_tool,
    supabase_persistence_tool,
)


MIN_JOB_DESCRIPTION_CHARS = 40
MAX_UPLOAD_BYTES = 8 * 1024 * 1024

REGISTERED_TOOLS = [
    resume_parser_tool,
    candidate_analyzer_tool,
    candidate_matcher_tool,
    interview_question_generator_tool,
    supabase_persistence_tool,
]


def validate_input(state: AgentState) -> AgentState:
    errors: list[str] = []
    resume_bytes = state.get("resume_bytes") or b""
    filename = (state.get("resume_filename") or "").strip()
    job_description = (state.get("job_description") or "").strip()
    job_title = (state.get("job_title") or "").strip() or "Untitled Role"

    if not resume_bytes:
        errors.append("Resume file is required.")
    elif len(resume_bytes) > MAX_UPLOAD_BYTES:
        errors.append("Resume exceeds the 8MB upload limit.")

    if not filename.lower().endswith(".pdf"):
        errors.append("Only PDF resumes are supported.")

    if len(job_description) < MIN_JOB_DESCRIPTION_CHARS:
        errors.append(
            f"Job description must be at least {MIN_JOB_DESCRIPTION_CHARS} characters."
        )

    if errors:
        raise ValueError(" | ".join(errors))

    return {
        **state,
        "job_title": job_title,
        "job_description": job_description,
        "resume_filename": filename,
        "current_step": "validate_input",
        "errors": [],
    }


def create_plan(state: AgentState) -> AgentState:
    """Explicit planning step — demonstrates agent planning before tool execution."""
    job_title = state["job_title"]
    plan = [
        f"Parse resume PDF ({state['resume_filename']}) into a CandidateProfile",
        "Analyze skills depth, experience trajectory, and seniority signals",
        f"Match candidate against role: {job_title}",
        "Calculate calibrated match score, strengths, and missing skills",
        "Generate technical, behavioral, and follow-up interview questions",
        "Persist resume, job description, and analysis to Supabase",
        "Return a structured hiring evaluation to the UI",
    ]
    return {
        **state,
        "plan": plan,
        "current_step": "create_plan",
        "extras": {
            **(state.get("extras") or {}),
            "plan_steps": len(plan),
        },
    }


def parse_resume(state: AgentState) -> AgentState:
    resume_text = extract_text_from_pdf(state["resume_bytes"])
    if len(resume_text) < 50:
        raise ValueError(
            "Could not extract enough text from the PDF. "
            "Try a text-based (non-scanned) resume."
        )
    tool_json = resume_parser_tool.invoke({"resume_text": resume_text})
    profile = CandidateProfile.model_validate_json(tool_json)
    return {
        **state,
        "resume_text": resume_text,
        "candidate_profile": profile,
        "current_step": "parse_resume",
    }


def analyze_candidate(state: AgentState) -> AgentState:
    profile = state["candidate_profile"]
    if not profile.skills and not profile.experience:
        raise ValueError(
            "Candidate analysis failed: no skills or experience found in the resume."
        )

    tool_json = candidate_analyzer_tool.invoke(
        {
            "candidate_json": profile.model_dump_json(),
            "resume_excerpt": state["resume_text"][:8000],
        }
    )
    analysis = CandidateAnalysis.model_validate_json(tool_json)

    enriched_summary = profile.summary
    if analysis.skills_analysis:
        enriched_summary = (
            f"{profile.summary}\n\nSkills: {analysis.skills_analysis}".strip()
            if profile.summary
            else analysis.skills_analysis
        )

    enriched_profile = profile.model_copy(
        update={"summary": enriched_summary[:1200]}
    )

    return {
        **state,
        "candidate_profile": enriched_profile,
        "candidate_analysis": analysis,
        "current_step": "analyze_candidate",
        "extras": {
            **(state.get("extras") or {}),
            "skill_count": len(profile.skills),
            "experience_count": len(profile.experience),
            "seniority_estimate": analysis.seniority_estimate,
            "domain_signals": analysis.domain_signals,
            "red_flags": analysis.red_flags,
        },
    }


def match_job(state: AgentState) -> AgentState:
    tool_json = candidate_matcher_tool.invoke(
        {
            "candidate_json": state["candidate_profile"].model_dump_json(),
            "job_title": state["job_title"],
            "job_description": state["job_description"],
        }
    )
    match = MatchResult.model_validate_json(tool_json)
    return {
        **state,
        "match_result": match,
        "current_step": "match_job",
    }


def generate_interview(state: AgentState) -> AgentState:
    tool_json = interview_question_generator_tool.invoke(
        {
            "candidate_json": state["candidate_profile"].model_dump_json(),
            "match_json": state["match_result"].model_dump_json(),
            "job_title": state["job_title"],
            "job_description": state["job_description"],
        }
    )
    questions = InterviewQuestions.model_validate_json(tool_json)
    return {
        **state,
        "interview_questions": questions,
        "current_step": "generate_interview",
    }


def persist_results(state: AgentState) -> AgentState:
    tool_json = supabase_persistence_tool.invoke(
        {
            "filename": state["resume_filename"],
            "extracted_text": state["resume_text"],
            "candidate_json": state["candidate_profile"].model_dump_json(),
            "job_title": state["job_title"],
            "job_description": state["job_description"],
            "match_json": state["match_result"].model_dump_json(),
            "interview_json": state["interview_questions"].model_dump_json(),
        }
    )
    analysis = AnalysisResponse.model_validate_json(tool_json)
    return {
        **state,
        "analysis_response": analysis,
        "current_step": "persist_results",
    }


def format_response(state: AgentState) -> AgentState:
    """Normalize the API payload so the frontend always gets a complete DTO."""
    existing = state.get("analysis_response")
    profile = state["candidate_profile"]
    match = state["match_result"]
    questions = state["interview_questions"]
    candidate_analysis = state.get("candidate_analysis")

    if existing is None:
        raise ValueError("Missing analysis response after persistence.")

    experience_summary = match.experience_summary
    if not experience_summary and candidate_analysis:
        experience_summary = candidate_analysis.experience_analysis

    analysis = AnalysisResponse(
        id=existing.id,
        candidate_name=profile.name or existing.candidate_name,
        match_score=match.match_score,
        strengths=match.strengths,
        weaknesses=match.weaknesses,
        skills_matched=match.skills_matched,
        skills_missing=match.skills_missing,
        experience_summary=experience_summary,
        recommendation=match.recommendation,
        recommendation_label=match.recommendation_label,
        interview_questions=questions,
        candidate_profile=profile,
        job_title=state["job_title"],
        resume_filename=state["resume_filename"],
        created_at=existing.created_at or datetime.now(timezone.utc),
    )
    return {
        **state,
        "analysis_response": analysis,
        "current_step": "format_response",
    }
