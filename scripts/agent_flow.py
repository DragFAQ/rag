"""
Custom agent workflow (HW6): a deterministic router in front of the retrieval
pipeline and the token-status tool from earlier homeworks.

Run from the project root:
    python scripts/agent_flow.py "your question here"
    python scripts/agent_flow.py               # runs the built-in demo questions

No LLM call anywhere in this script, on purpose. Routing is a plain keyword
check and the final answer is templated straight off the observation - that's
what the assignment means by "custom flow": the code decides the order of
steps, not the model. Compare with agent_with_tool.py, where the model itself
decides whether to call the tool.

Workflow:
    user question -> router -> [route] -> tool call / retrieval -> observation
                  -> state update -> final answer

Routes:
    token_status   -> external_tool.get_token_status()
                       (question names a specific TKN-XXXXXX reference)
    policy_rag     -> semantic_search.search() over the Mastercard docs
                       (conceptual question about tokenization/payments/etc.)
    clarification  -> list_supported_topics() below, question doesn't match
                       either route clearly enough to act on
"""

from __future__ import annotations

import re
import sys
from typing import Any

from external_tool import get_token_status
from semantic_search import load_retrieval_components, search

TOKEN_REFERENCE_PATTERN = re.compile(r"TKN-\d{6,}", re.IGNORECASE)

STATUS_WORDS = ["status", "active", "suspended", "deleted", "valid", "expired"]

POLICY_KEYWORDS = [
    "serviceid", "service id", "tokeniz", "register", "entity", "entities",
    "payment", "checkout", "wallet", "dpa", "pan", "card on file", "program",
    "reason code", "cardholder",
]

# Second mock tool for this homework - fixed result, no API call. Used by the
# clarification route so a vague question gets pointed somewhere useful
# instead of a flat "please rephrase".
SUPPORTED_TOPICS = {
    "token_creation": "how tokens get created (adding a card, during checkout, or for an existing card)",
    "token_management": "updating, suspending, or deleting an existing token",
    "payments": "making a payment with a Card-on-File token",
    "entity_registration": "registering an entity/program to get a serviceId",
    "token_display": "showing a cardholder a masked/tokenized PAN in the UI",
}


def list_supported_topics() -> dict[str, Any]:
    """
    Tool: list_supported_topics
    Type: read tool, fixed result (mock)
    Purpose: what topics the knowledge base actually covers, so a vague or
    off-topic question can be steered back to something answerable instead
    of just failing.
    """
    return {"topics": SUPPORTED_TOPICS}


def route_question(question: str) -> str:
    q = question.lower()

    has_token_ref = bool(TOKEN_REFERENCE_PATTERN.search(question))
    asks_status = "token" in q and any(w in q for w in STATUS_WORDS)
    if has_token_ref or asks_status:
        return "token_status"

    if any(k in q for k in POLICY_KEYWORDS):
        return "policy_rag"

    return "clarification"


def run_agent(question: str, model, index, chunks: list[dict[str, Any]]) -> dict[str, Any]:
    """Route the question, run the matching step, and return the full state."""
    state: dict[str, Any] = {
        "user_question": question,
        "selected_route": route_question(question),
        "tool_calls": [],
        "observations": [],
        "final_answer": None,
    }

    if state["selected_route"] == "token_status":
        match = TOKEN_REFERENCE_PATTERN.search(question)
        if not match:
            state["observations"].append("no token reference found in the question")
            state["final_answer"] = (
                "Which token do you mean? Send me the reference in TKN-XXXXXX "
                "format and I'll check its live status."
            )
            return state

        token_reference = match.group(0).upper()
        result = get_token_status(token_reference)
        state["tool_calls"].append(
            {"tool": "get_token_status", "args": {"token_reference": token_reference}, "result": result}
        )
        state["observations"].append(result)

        if "error" in result:
            state["final_answer"] = f"Couldn't look that up - {result['error']}"
        else:
            state["final_answer"] = (
                f"Token {result['token_reference']} is {result['status']} "
                f"(masked PAN {result['masked_pan']}, expires {result['expiry']}, "
                f"last updated {result['last_updated']})."
            )
        return state

    if state["selected_route"] == "policy_rag":
        retrieved = search(question, model, index, chunks, top_k=3)
        state["observations"].append([r["chunk_id"] for r in retrieved])

        if not retrieved:
            state["final_answer"] = "Nothing in the docs matches that, sorry."
            return state

        top = retrieved[0]
        state["tool_calls"].append(
            {"tool": "search", "args": {"query": question, "top_k": 3}, "result": [r["chunk_id"] for r in retrieved]}
        )
        state["final_answer"] = (
            f"{top['text'].strip()[:400]}\n\n(source: {top['chunk_id']}, "
            f"{top['metadata'].get('source_file', 'unknown source')})"
        )
        return state

    # clarification
    topics = list_supported_topics()
    state["tool_calls"].append({"tool": "list_supported_topics", "args": {}, "result": topics})
    state["observations"].append(topics)
    topic_list = ", ".join(topics["topics"])
    state["final_answer"] = (
        f"Not sure what you're asking - I can help with: {topic_list}. If you meant "
        "a specific token, give me its reference (TKN-XXXXXX) and I'll check its status."
    )
    return state


DEMO_QUESTIONS = [
    "How is a serviceId created and what is it used for?",
    "What is the status of token TKN-100234?",
    "Is TKN-999999 still active?",
    "Tell me something interesting.",
    "How do I get a masked PAN displayed to the cardholder?",
]


def main() -> None:
    model, index, chunks = load_retrieval_components()

    questions = [" ".join(sys.argv[1:])] if len(sys.argv) > 1 else DEMO_QUESTIONS

    for question in questions:
        state = run_agent(question, model, index, chunks)
        print(f"Question: {question}")
        print(f"Route: {state['selected_route']}")
        if state["tool_calls"]:
            for call in state["tool_calls"]:
                print(f"Tool called: {call['tool']}({call['args']})")
        else:
            print("Tool called: (none)")
        print(f"Observation: {state['observations']}")
        print(f"State: {state}")
        print(f"Final answer: {state['final_answer']}")
        print("-" * 80)


if __name__ == "__main__":
    main()
