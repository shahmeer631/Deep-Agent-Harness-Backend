from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from langgraph.graph import END, START, StateGraph

from graph.nodes import (
    analyze_candidate,
    create_plan,
    format_response,
    generate_interview,
    match_job,
    parse_resume,
    persist_results,
    validate_input,
)
from graph.state import AgentState
from models import AnalysisResponse


def build_screening_graph():
    graph = StateGraph(AgentState)

    graph.add_node("validate_input", validate_input)
    graph.add_node("create_plan", create_plan)
    graph.add_node("parse_resume", parse_resume)
    graph.add_node("analyze_candidate", analyze_candidate)
    graph.add_node("match_job", match_job)
    graph.add_node("generate_interview", generate_interview)
    graph.add_node("persist_results", persist_results)
    graph.add_node("format_response", format_response)

    graph.add_edge(START, "validate_input")
    graph.add_edge("validate_input", "create_plan")
    graph.add_edge("create_plan", "parse_resume")
    graph.add_edge("parse_resume", "analyze_candidate")
    graph.add_edge("analyze_candidate", "match_job")
    graph.add_edge("match_job", "generate_interview")
    graph.add_edge("generate_interview", "persist_results")
    graph.add_edge("persist_results", "format_response")
    graph.add_edge("format_response", END)

    return graph.compile()


_compiled_graph = None


def get_screening_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_screening_graph()
    return _compiled_graph


def _initial_state(
    *,
    resume_bytes: bytes,
    resume_filename: str,
    job_description: str,
    job_title: str,
) -> AgentState:
    return {
        "resume_bytes": resume_bytes,
        "resume_filename": resume_filename,
        "job_description": job_description,
        "job_title": job_title,
        "errors": [],
        "extras": {},
        "plan": [],
    }


def run_screening_workflow(
    *,
    resume_bytes: bytes,
    resume_filename: str,
    job_description: str,
    job_title: str = "",
) -> AnalysisResponse:
    graph = get_screening_graph()
    final_state = graph.invoke(
        _initial_state(
            resume_bytes=resume_bytes,
            resume_filename=resume_filename,
            job_description=job_description,
            job_title=job_title,
        )
    )
    response = final_state.get("analysis_response")
    if response is None:
        raise RuntimeError("Workflow completed without an analysis response.")
    return response


def stream_screening_workflow(
    *,
    resume_bytes: bytes,
    resume_filename: str,
    job_description: str,
    job_title: str = "",
) -> Iterator[dict[str, Any]]:
    """Yield real LangGraph node completions, then the final analysis."""
    graph = get_screening_graph()
    final_response: AnalysisResponse | None = None

    for update in graph.stream(
        _initial_state(
            resume_bytes=resume_bytes,
            resume_filename=resume_filename,
            job_description=job_description,
            job_title=job_title,
        ),
        stream_mode="updates",
    ):
        for node_name, node_state in update.items():
            event: dict[str, Any] = {"type": "step", "step": node_name}
            if isinstance(node_state, dict) and node_state.get("plan"):
                event["plan"] = node_state["plan"]
            yield event
            if isinstance(node_state, dict) and node_state.get("analysis_response"):
                final_response = node_state["analysis_response"]

    if final_response is None:
        raise RuntimeError("Workflow completed without an analysis response.")

    yield {
        "type": "result",
        "data": final_response.model_dump(mode="json"),
    }
