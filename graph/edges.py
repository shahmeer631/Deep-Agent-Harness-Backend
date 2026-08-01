"""Deterministic screening graph edges.

Primary path is linear for predictable cost and interview clarity.
`create_plan` sits after validation so the agent plans before tool execution.
"""

from typing import Literal

from graph.state import AgentState

WORKFLOW_STEPS = [
    "validate_input",
    "create_plan",
    "parse_resume",
    "analyze_candidate",
    "match_job",
    "generate_interview",
    "persist_results",
    "format_response",
]


def next_after_validation(state: AgentState) -> Literal["create_plan"]:
    _ = state
    return "create_plan"


def next_after_plan(state: AgentState) -> Literal["parse_resume"]:
    _ = state
    return "parse_resume"
