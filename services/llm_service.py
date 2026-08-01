from __future__ import annotations

from typing import TypeVar

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel

from config import get_settings
from prompts import SENIOR_RECRUITER_SYSTEM_PROMPT

T = TypeVar("T", bound=BaseModel)


class LLMService:
    """Provider-agnostic LLM facade (Google Gemini)."""

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.google_api_key:
            raise RuntimeError("GOOGLE_API_KEY is not configured")
        self._llm = ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.google_api_key,
            temperature=0.2,
        )

    @property
    def llm(self) -> ChatGoogleGenerativeAI:
        return self._llm

    def structured_completion(self, user_prompt: str, response_model: type[T]) -> T:
        structured = self._llm.with_structured_output(response_model)
        result = structured.invoke(
            [
                SystemMessage(content=SENIOR_RECRUITER_SYSTEM_PROMPT),
                HumanMessage(content=user_prompt),
            ]
        )
        if isinstance(result, response_model):
            return result
        return response_model.model_validate(result)


_llm_service: LLMService | None = None


def get_llm_service() -> LLMService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service


# Convenience export for callers that want the raw chat model.
def get_llm() -> ChatGoogleGenerativeAI:
    return get_llm_service().llm
