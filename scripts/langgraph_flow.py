"""
HW7 - same workflow as agent_flow.py (HW6), rewritten on LangGraph.

    python scripts/langgraph_flow.py "your question here"
    python scripts/langgraph_flow.py    # 3 demo questions, writes outputs/langgraph_examples.md

Graph: classify_request -> [policy_rag | token_status | clarification] -> build_answer -> END
Routing and tools are unchanged from agent_flow.py (route_question,
get_token_status, search, list_supported_topics). build_answer is split out
as its own node here instead of being templated inline per route.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from agent_flow import TOKEN_REFERENCE_PATTERN, list_supported_topics, route_question
from external_tool import get_token_status
from semantic_search import load_retrieval_components, search


class AgentState(TypedDict):
    user_question: str
    selected_route: str
    tool_calls: list[dict[str, Any]]
    observations: list[Any]
    tool_result: dict[str, Any]
    final_answer: str
    executed_nodes: list[str]


def classify_request(state: AgentState) -> dict[str, Any]:
    return {
        "selected_route": route_question(state["user_question"]),
        "executed_nodes": state["executed_nodes"] + ["classify_request"],
    }


def run_policy_rag(model, index, chunks: list[dict[str, Any]]):
    def node(state: AgentState) -> dict[str, Any]:
        retrieved = search(state["user_question"], model, index, chunks, top_k=3)
        tool_calls = state["tool_calls"] + [
            {
                "tool": "search",
                "args": {"query": state["user_question"], "top_k": 3},
                "result": [r["chunk_id"] for r in retrieved],
            }
        ]
        return {
            "tool_calls": tool_calls,
            "observations": state["observations"] + [[r["chunk_id"] for r in retrieved]],
            "tool_result": retrieved[0] if retrieved else {},
            "executed_nodes": state["executed_nodes"] + ["run_policy_rag"],
        }

    return node


def run_token_status(state: AgentState) -> dict[str, Any]:
    match = TOKEN_REFERENCE_PATTERN.search(state["user_question"])
    if not match:
        return {
            "observations": state["observations"] + ["no token reference found in the question"],
            "tool_result": {"error": "no token reference found in the question"},
            "executed_nodes": state["executed_nodes"] + ["run_token_status"],
        }

    token_reference = match.group(0).upper()
    result = get_token_status(token_reference)
    tool_calls = state["tool_calls"] + [
        {"tool": "get_token_status", "args": {"token_reference": token_reference}, "result": result}
    ]
    return {
        "tool_calls": tool_calls,
        "observations": state["observations"] + [result],
        "tool_result": result,
        "executed_nodes": state["executed_nodes"] + ["run_token_status"],
    }


def ask_clarification(state: AgentState) -> dict[str, Any]:
    topics = list_supported_topics()
    tool_calls = state["tool_calls"] + [{"tool": "list_supported_topics", "args": {}, "result": topics}]
    return {
        "tool_calls": tool_calls,
        "observations": state["observations"] + [topics],
        "tool_result": topics,
        "executed_nodes": state["executed_nodes"] + ["ask_clarification"],
    }


def build_answer(state: AgentState) -> dict[str, Any]:
    route = state["selected_route"]
    result = state["tool_result"]

    if route == "token_status":
        if "error" in result:
            answer = f"Couldn't look that up - {result['error']}"
        else:
            answer = (
                f"Token {result['token_reference']} is {result['status']} "
                f"(masked PAN {result['masked_pan']}, expires {result['expiry']}, "
                f"last updated {result['last_updated']})."
            )
    elif route == "policy_rag":
        if not result:
            answer = "Nothing in the docs matches that, sorry."
        else:
            answer = (
                f"{result['text'].strip()[:400]}\n\n(source: {result['chunk_id']}, "
                f"{result['metadata'].get('source_file', 'unknown source')})"
            )
    else:  # clarification
        topic_list = ", ".join(result["topics"])
        answer = (
            f"Not sure what you're asking - I can help with: {topic_list}. If you meant "
            "a specific token, give me its reference (TKN-XXXXXX) and I'll check its status."
        )

    return {
        "final_answer": answer,
        "executed_nodes": state["executed_nodes"] + ["build_answer"],
    }


def route_decision(state: AgentState) -> str:
    return state["selected_route"]


def build_graph(model, index, chunks: list[dict[str, Any]]):
    workflow = StateGraph(AgentState)

    workflow.add_node("classify_request", classify_request)
    workflow.add_node("policy_rag", run_policy_rag(model, index, chunks))
    workflow.add_node("token_status", run_token_status)
    workflow.add_node("clarification", ask_clarification)
    workflow.add_node("build_answer", build_answer)

    workflow.set_entry_point("classify_request")
    workflow.add_conditional_edges(
        "classify_request",
        route_decision,
        {
            "policy_rag": "policy_rag",
            "token_status": "token_status",
            "clarification": "clarification",
        },
    )
    workflow.add_edge("policy_rag", "build_answer")
    workflow.add_edge("token_status", "build_answer")
    workflow.add_edge("clarification", "build_answer")
    workflow.add_edge("build_answer", END)

    return workflow.compile()


def initial_state(question: str) -> AgentState:
    return {
        "user_question": question,
        "selected_route": "",
        "tool_calls": [],
        "observations": [],
        "tool_result": {},
        "final_answer": "",
        "executed_nodes": [],
    }


TEST_QUESTIONS = [
    "How is a serviceId created and what is it used for?",
    "What is the status of token TKN-100234?",
    "Tell me something interesting.",
]


def print_trace(state: AgentState) -> None:
    print(f"Question: {state['user_question']}")
    print(f"Route: {state['selected_route']}")
    print(f"Executed nodes: {' -> '.join(state['executed_nodes'])}")
    if state["tool_calls"]:
        for call in state["tool_calls"]:
            print(f"Tool called: {call['tool']}({call['args']})")
    else:
        print("Tool called: (none)")
    print(f"Observations: {state['observations']}")
    print(f"Final state: {state}")
    print(f"Final answer: {state['final_answer']}")
    print("-" * 80)


def write_report(states: list[AgentState], path: Path) -> None:
    lines = [
        "# LangGraph Workflow Examples (HW7)",
        "",
        f"{len(states)} questions, one per route, run through `scripts/langgraph_flow.py`.",
        "",
        "---",
        "",
    ]
    for state in states:
        lines.append(f"Question: {state['user_question']}")
        lines.append(f"Route: {state['selected_route']}")
        lines.append(f"Nodes: {' -> '.join(state['executed_nodes'])}")
        if state["tool_calls"]:
            for call in state["tool_calls"]:
                lines.append(f"Tool called: {call['tool']}({call['args']})")
        else:
            lines.append("Tool called: (none)")
        lines.append(f"Final answer: {state['final_answer']}")
        lines.append("")
        lines.append("---")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    model, index, chunks = load_retrieval_components()
    app = build_graph(model, index, chunks)

    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
        state = app.invoke(initial_state(question))
        print_trace(state)
        return

    states = [app.invoke(initial_state(q)) for q in TEST_QUESTIONS]
    for state in states:
        print_trace(state)

    report_path = Path("outputs/langgraph_examples.md")
    write_report(states, report_path)
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    main()
