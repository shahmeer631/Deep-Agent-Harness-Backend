from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from supabase import Client, create_client

from config import get_settings
from models import (
    AnalysisResponse,
    AnalysisSummary,
    CandidateProfile,
    InterviewQuestions,
    MatchResult,
)


class SupabaseService:
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.supabase_url or not settings.supabase_service_role_key:
            raise RuntimeError("Supabase credentials are not configured")
        self._client: Client = create_client(
            settings.supabase_url,
            settings.supabase_service_role_key,
        )

    @property
    def client(self) -> Client:
        return self._client

    def save_analysis(
        self,
        *,
        filename: str,
        extracted_text: str,
        profile: CandidateProfile,
        job_title: str,
        job_description: str,
        match: MatchResult,
        interview: InterviewQuestions,
    ) -> AnalysisResponse:
        resume_row = (
            self._client.table("resumes")
            .insert(
                {
                    "filename": filename,
                    "extracted_text": extracted_text,
                    "parsed_json": profile.model_dump(),
                }
            )
            .execute()
        )
        resume = resume_row.data[0]

        job_row = (
            self._client.table("job_descriptions")
            .insert(
                {
                    "title": job_title,
                    "description": job_description,
                }
            )
            .execute()
        )
        job = job_row.data[0]

        raw_analysis = {
            "candidate_profile": profile.model_dump(),
            "match": match.model_dump(),
            "interview_questions": interview.model_dump(),
        }

        analysis_row = (
            self._client.table("analyses")
            .insert(
                {
                    "resume_id": resume["id"],
                    "job_description_id": job["id"],
                    "candidate_name": profile.name,
                    "match_score": match.match_score,
                    "strengths": match.strengths,
                    "weaknesses": match.weaknesses,
                    "skills_matched": match.skills_matched,
                    "skills_missing": match.skills_missing,
                    "experience_summary": match.experience_summary,
                    "recommendation": match.recommendation,
                    "recommendation_label": match.recommendation_label,
                    "interview_questions": interview.model_dump(),
                    "raw_analysis": raw_analysis,
                }
            )
            .execute()
        )
        analysis = analysis_row.data[0]

        return self._to_analysis_response(analysis, profile, job_title, filename, match)

    def list_analyses(self, limit: int = 50) -> list[AnalysisSummary]:
        rows = (
            self._client.table("analyses")
            .select(
                "id, candidate_name, match_score, recommendation, recommendation_label, created_at, job_descriptions(title), raw_analysis"
            )
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )

        summaries: list[AnalysisSummary] = []
        for row in rows.data or []:
            job = row.get("job_descriptions") or {}
            raw = row.get("raw_analysis") or {}
            match = raw.get("match") or {}
            label = (
                row.get("recommendation_label")
                or match.get("recommendation_label")
                or self._infer_label(row.get("recommendation", ""))
            )
            summaries.append(
                AnalysisSummary(
                    id=UUID(row["id"]),
                    candidate_name=row["candidate_name"],
                    match_score=row["match_score"],
                    job_title=job.get("title") or "Untitled role",
                    recommendation_label=label,
                    created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")),
                )
            )
        return summaries

    def get_analysis(self, analysis_id: UUID) -> AnalysisResponse | None:
        rows = (
            self._client.table("analyses")
            .select(
                "*, job_descriptions(title), resumes(filename, parsed_json)"
            )
            .eq("id", str(analysis_id))
            .limit(1)
            .execute()
        )
        if not rows.data:
            return None

        row = rows.data[0]
        job = row.get("job_descriptions") or {}
        resume = row.get("resumes") or {}
        raw = row.get("raw_analysis") or {}
        profile_data = resume.get("parsed_json") or raw.get("candidate_profile") or {}
        match_data = raw.get("match") or {}
        profile = CandidateProfile.model_validate(profile_data)
        match = MatchResult(
            match_score=row["match_score"],
            strengths=row.get("strengths") or [],
            weaknesses=row.get("weaknesses") or [],
            skills_matched=row.get("skills_matched") or [],
            skills_missing=row.get("skills_missing") or [],
            experience_summary=row.get("experience_summary") or "",
            recommendation=row.get("recommendation") or "",
            recommendation_label=row.get("recommendation_label")
            or match_data.get("recommendation_label")
            or "maybe",
            reasoning=match_data.get("reasoning") or "",
        )
        return self._to_analysis_response(
            row,
            profile,
            job.get("title") or "Untitled role",
            resume.get("filename") or "resume.pdf",
            match,
        )

    def _to_analysis_response(
        self,
        row: dict[str, Any],
        profile: CandidateProfile,
        job_title: str,
        filename: str,
        match: MatchResult,
    ) -> AnalysisResponse:
        questions = InterviewQuestions.model_validate(row.get("interview_questions") or {})
        created = row["created_at"]
        if isinstance(created, str):
            created_at = datetime.fromisoformat(created.replace("Z", "+00:00"))
        else:
            created_at = created

        return AnalysisResponse(
            id=UUID(row["id"]),
            candidate_name=row["candidate_name"],
            match_score=row["match_score"],
            strengths=row.get("strengths") or [],
            weaknesses=row.get("weaknesses") or [],
            skills_matched=row.get("skills_matched") or [],
            skills_missing=row.get("skills_missing") or [],
            experience_summary=row.get("experience_summary") or "",
            recommendation=row.get("recommendation") or "",
            recommendation_label=match.recommendation_label,
            interview_questions=questions,
            candidate_profile=profile,
            job_title=job_title,
            resume_filename=filename,
            created_at=created_at,
        )

    @staticmethod
    def _infer_label(recommendation: str) -> str:
        text = recommendation.lower()
        if "pass" in text or "reject" in text or "not advance" in text:
            return "pass"
        if "hire" in text or "advance" in text or "recommend" in text:
            return "hire"
        return "maybe"


_supabase_service: SupabaseService | None = None


def get_supabase_service() -> SupabaseService:
    global _supabase_service
    if _supabase_service is None:
        _supabase_service = SupabaseService()
    return _supabase_service
