from __future__ import annotations

import io

from langchain_core.tools import tool
from pypdf import PdfReader

from models import CandidateProfile
from prompts import PARSE_RESUME_PROMPT
from services import get_llm_service


def extract_text_from_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    pages: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            pages.append(text)
    return "\n\n".join(pages).strip()


def parse_resume_profile(resume_text: str) -> CandidateProfile:
    if not resume_text.strip():
        raise ValueError("Resume text is empty. The PDF may be scanned or unreadable.")

    prompt = PARSE_RESUME_PROMPT.format(resume_text=resume_text[:20000])
    return get_llm_service().structured_completion(prompt, CandidateProfile)


@tool("resume_parser")
def resume_parser_tool(resume_text: str) -> str:
    """Extract structured candidate profile JSON from resume text.

    Returns name, email, skills, education, experience, projects,
    certifications, and a short summary.
    """
    profile = parse_resume_profile(resume_text)
    return profile.model_dump_json()
