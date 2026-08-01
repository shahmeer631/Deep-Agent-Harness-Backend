from __future__ import annotations

import json
from uuid import UUID

from fastapi import APIRouter, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from config import get_settings
from graph import run_screening_workflow
from graph.graph import stream_screening_workflow
from models import AnalysisResponse, AnalysisSummary, HealthResponse
from services import get_supabase_service

router = APIRouter()


def _assert_api_key(x_api_key: str | None) -> None:
    expected = get_settings().agent_api_key
    if expected and x_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")


def _validate_resume_upload(resume: UploadFile) -> None:
    if resume.content_type not in {
        "application/pdf",
        "application/octet-stream",
    }:
        raise HTTPException(status_code=400, detail="Resume must be a PDF file.")


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        llm_configured=bool(settings.google_api_key),
        supabase_configured=bool(
            settings.supabase_url and settings.supabase_service_role_key
        ),
    )


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_candidate(
    resume: UploadFile = File(...),
    job_description: str = Form(...),
    job_title: str = Form(""),
    x_api_key: str | None = Header(default=None),
) -> AnalysisResponse:
    _assert_api_key(x_api_key)
    _validate_resume_upload(resume)

    resume_bytes = await resume.read()
    filename = resume.filename or "resume.pdf"

    try:
        return run_screening_workflow(
            resume_bytes=resume_bytes,
            resume_filename=filename,
            job_description=job_description,
            job_title=job_title,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {exc}",
        ) from exc


@router.post("/analyze/stream")
async def analyze_candidate_stream(
    resume: UploadFile = File(...),
    job_description: str = Form(...),
    job_title: str = Form(""),
    x_api_key: str | None = Header(default=None),
) -> StreamingResponse:
    """SSE stream of real LangGraph node completions, then final result."""
    _assert_api_key(x_api_key)
    _validate_resume_upload(resume)

    resume_bytes = await resume.read()
    filename = resume.filename or "resume.pdf"

    def event_generator():
        try:
            for event in stream_screening_workflow(
                resume_bytes=resume_bytes,
                resume_filename=filename,
                job_description=job_description,
                job_title=job_title,
            ):
                yield f"data: {json.dumps(event)}\n\n"
        except ValueError as exc:
            yield f"data: {json.dumps({'type': 'error', 'detail': str(exc)})}\n\n"
        except Exception as exc:  # noqa: BLE001
            yield f"data: {json.dumps({'type': 'error', 'detail': str(exc)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/analyses", response_model=list[AnalysisSummary])
async def list_analyses(
    x_api_key: str | None = Header(default=None),
) -> list[AnalysisSummary]:
    _assert_api_key(x_api_key)
    try:
        return get_supabase_service().list_analyses()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/analyses/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(
    analysis_id: UUID,
    x_api_key: str | None = Header(default=None),
) -> AnalysisResponse:
    _assert_api_key(x_api_key)
    try:
        result = get_supabase_service().get_analysis(analysis_id)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if result is None:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    return result
