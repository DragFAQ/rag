"""
HW8: eval + observability runner for agent_with_tool.answer_question().

Run from the project root:
    python scripts/run_eval.py

Picked agent_with_tool.py as the thing under test, not agent_flow.py or
rag_answer.py, because it's the only script that already exercises every
category the assignment asks for in one place: RAG retrieval, tool calling,
and the "not enough information" fallback from the grounded prompt. Routing
here is model-decided (offer the tool, let it choose), which also makes tool
misuse/non-use an observable outcome instead of something a keyword router
already guarantees.

What this script does NOT do: judge task_success, groundedness, or
answer_quality automatically. Those need a human reading the answer against
the retrieved chunks, which is the actual point of the assignment. The
values hardcoded into EVAL_SET below aren't guesses made before running this
- they were written after a first run, by reading each answer in
outputs/eval_results.md against what it actually retrieved. Re-running after
a prompt or retrieval change means re-reading the answers and updating these
by hand again, not trusting the old ones.

Pipeline per case:
    question -> answer_question() [retrieval + optional tool call + LLM]
             -> wall-clock latency
             -> route/tools_used derived from the returned tool_calls list
             -> merged with the hand-filled judgment
             -> one row in outputs/eval_results.md
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from agent_with_tool import answer_question
from rag_answer import DEFAULT_LLM_MODEL
from semantic_search import load_retrieval_components

NOT_ENOUGH_INFO = "I do not have enough information in the provided documentation to answer this question."


@dataclass
class EvalCase:
    id: int
    question: str
    expected_behavior: str
    # Filled in by hand after reading the answer against retrieved_chunks.
    # yes/partial/no
    task_success: str
    # good/partial/bad/not_applicable
    groundedness: str
    # good/partial/bad
    answer_quality: str
    errors: str = "none"
    notes: str = ""


EVAL_SET: list[EvalCase] = [
    EvalCase(
        id=1,
        question="How is a serviceId created and what is it used for?",
        expected_behavior="Answer from KB: serviceId comes from Mastercard once an entity registers a programName; used to create tokens for that entity",
        task_success="yes",
        groundedness="good",
        answer_quality="good",
        notes="Straightforward single-topic question, this is the corpus's best-covered concept",
    ),
    EvalCase(
        id=2,
        question="What happens to maskedCard and paymentData when a TOKEN_REFRESH event occurs?",
        expected_behavior="Answer from KB (managing_tokens): TOKEN_REFRESH returns both maskedCard and encrypted paymentData with DPAN/DPAN expiry",
        task_success="yes",
        groundedness="good",
        answer_quality="good",
        notes="Targets the table row that's split across two chunks by the sentence-fallback splitter (see README chunking notes) - checks whether the split lost the answer",
    ),
    EvalCase(
        id=3,
        question="What is a serviceId and how is it created?",
        expected_behavior="Answer from KB, same content as case 1 but phrased to hit the tied-score retrieval case flagged in the main README (top-3 chunks all score 0.6250)",
        task_success="yes",
        groundedness="good",
        answer_quality="good",
        errors="none",
        notes="Same 4 chunks retrieved as case 1, in the same order - the tied-score issue documented in the README was measured against semantic_search.py's top_k=3 baseline, not this script's top_k=4, so the extra candidate here evidently pushes the right chunk back to rank 1. Worth flagging as a real gap between the two scripts, not a bug in this one.",
    ),
    EvalCase(
        id=4,
        question="What is the status of token TKN-100234?",
        expected_behavior="Use get_token_status tool, report ACTIVE / masked PAN / expiry / last updated",
        task_success="yes",
        groundedness="not_applicable",
        answer_quality="good",
        notes="Known-good token in MOCK_TOKENS, baseline tool case",
    ),
    EvalCase(
        id=5,
        question="Is TKN-999999 still active?",
        expected_behavior="Call the tool, tool returns not-found, model reports it can't find that token instead of guessing a status",
        task_success="yes",
        groundedness="not_applicable",
        answer_quality="good",
        notes="Checks whether a tool error gets surfaced honestly or the model fills in a plausible-sounding status anyway",
    ),
    EvalCase(
        id=6,
        question="What are the PCI-DSS fines for a card data breach?",
        expected_behavior="Say not enough information - topic is entirely outside this KB (tokenization/registration/payments API docs, not compliance penalties)",
        task_success="yes",
        groundedness="not_applicable",
        answer_quality="good",
        notes="Correctly declined. Side finding: the model appends its citation list after the exact fallback sentence, so route_for() below (which pattern-matches the literal string from rag_answer.SYSTEM_PROMPT) tags this row RAG instead of fallback. The system prompt says 'say exactly' but the citation rule wins - fine for a human reading the answer, but breaks any downstream code that classifies runs by matching that string.",
    ),
    EvalCase(
        id=7,
        question="Where do I find the wallet or DPA identifier for a payment?",
        expected_behavior="Answer from KB (making-payments, dpaData.dpaURI), flagged in README as a case where filtering can't help and the field-naming chunk still misses top-3",
        task_success="yes",
        groundedness="good",
        answer_quality="good",
        errors="none",
        notes="README's version of this failure was measured at final_k=3 through retrieval_improved.py; at top_k=4 here the chunk naming dpaData.dpaURI made it into context and the answer cited it correctly. Same lesson as case 3: this script's larger top_k happens to dodge a gap that's documented elsewhere at a smaller k.",
    ),
    EvalCase(
        id=8,
        question="Tell me about tokens.",
        expected_behavior="Ambiguous - ideally asks for clarification or gives a narrow, hedged answer instead of picking one of the 5 topics and presenting it as the whole picture",
        task_success="partial",
        groundedness="good",
        answer_quality="good",
        notes="Didn't ask for clarification (there's no clarification route in this script, that's agent_flow.py's job) - instead gave a broad, well-organized answer spanning 3 of the 5 topics, and stayed grounded in the 4 retrieved chunks throughout. Marking task_success partial anyway: a real user asking this vague a question probably wanted one specific thing, and picking a broad summary on their behalf is a judgment call the system made silently.",
    ),
    EvalCase(
        id=9,
        question="Can I use a token that was tokenized while adding a card for a cardholder-initiated payment later?",
        expected_behavior="Answer requires connecting token_creation and payments topics - two different source documents",
        task_success="yes",
        groundedness="good",
        answer_quality="good",
        errors="none",
        notes="Retrieved chunks spanned 3 topics (token_creation, payments, token_display) in one top_k=4 call, and the answer correctly synthesized across the first two. Multi-document reasoning worked here - a smaller top_k or a topic filter would likely have broken it.",
    ),
    EvalCase(
        id=10,
        question="What is the reason code for a token that was suspended due to a lost device?",
        expected_behavior="Answer from KB (managing_tokens reason codes) or explicit not-enough-info if the specific device-loss code isn't documented",
        task_success="yes",
        groundedness="not_applicable",
        answer_quality="good",
        errors="none",
        notes="Correctly declined instead of inventing a reason code - the retrieved managing_tokens chunks cover token statuses but not a lost-device-specific reason code, and the model said so instead of guessing. This is the fallback prompt working as designed, not a failure.",
    ),
]


def route_for(tool_calls: list[dict[str, Any]], answer: str) -> str:
    if tool_calls:
        return "tool"
    if answer.strip() == NOT_ENOUGH_INFO:
        return "fallback"
    return "RAG"


def run() -> list[dict[str, Any]]:
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set - copy .env.example to .env and fill it in")

    llm_model = os.getenv("OPENAI_MODEL", DEFAULT_LLM_MODEL)
    client = OpenAI()
    model, index, chunks = load_retrieval_components()

    rows: list[dict[str, Any]] = []
    for case in EVAL_SET:
        start = time.perf_counter()
        result = answer_question(case.question, model, index, chunks, client, llm_model)
        latency_ms = int((time.perf_counter() - start) * 1000)

        retrieved_ids = ", ".join(r["chunk_id"] for r in result["retrieved"])
        tools_used = ", ".join(c["name"] for c in result["tool_calls"]) or "none"

        rows.append(
            {
                "id": case.id,
                "question": case.question,
                "expected_behavior": case.expected_behavior,
                "answer": result["answer"],
                "retrieved_chunks": retrieved_ids,
                "route_or_mode": route_for(result["tool_calls"], result["answer"]),
                "tools_used": tools_used,
                "task_success": case.task_success,
                "groundedness": case.groundedness,
                "answer_quality": case.answer_quality,
                "latency_ms": latency_ms,
                "errors": case.errors,
                "notes": case.notes,
            }
        )
        print(f"[{case.id}/{len(EVAL_SET)}] {case.question[:60]!r} -> {latency_ms} ms, route={rows[-1]['route_or_mode']}")

    return rows


def truncate(text: str, limit: int = 100) -> str:
    flat = text.replace("\n", " ")
    return flat if len(flat) <= limit else flat[: limit - 1] + "…"


def write_results_md(rows: list[dict[str, Any]], path: str) -> None:
    # All 13 fields from the assignment spec live in this table. answer and
    # retrieved_chunks are truncated here for table readability - the full,
    # untruncated text for both is in the "Full answers" section below, keyed
    # by the same case id.
    header = [
        "id", "question", "expected_behavior", "answer", "retrieved_chunks",
        "route_or_mode", "tools_used", "task_success", "groundedness",
        "answer_quality", "latency_ms", "errors", "notes",
    ]
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join(["---"] * len(header)) + "|"]
    for r in rows:
        cells = []
        for h in header:
            value = str(r[h]).replace("\n", " ").replace("|", "/")
            if h in ("answer", "retrieved_chunks", "expected_behavior", "notes"):
                value = truncate(value, 100)
            cells.append(value)
        lines.append("| " + " | ".join(cells) + " |")

    lines.append("")
    lines.append("## Full answers")
    lines.append("")
    for r in rows:
        lines.append(f"### Case {r['id']}: {r['question']}")
        lines.append("")
        lines.append(f"**Retrieved chunks:** {r['retrieved_chunks'] or '(none)'}")
        lines.append("")
        lines.append(f"**Answer:**\n\n{r['answer']}")
        lines.append("")

    with open(path, "w") as f:
        f.write("\n".join(lines))


def write_summary_md(rows: list[dict[str, Any]], path: str) -> None:
    total = len(rows)
    success = sum(1 for r in rows if r["task_success"] == "yes")
    partial = sum(1 for r in rows if r["task_success"] == "partial")
    fail = sum(1 for r in rows if r["task_success"] == "no")

    grounded = [r for r in rows if r["groundedness"] != "not_applicable"]
    g_good = sum(1 for r in grounded if r["groundedness"] == "good")
    g_partial = sum(1 for r in grounded if r["groundedness"] == "partial")
    g_bad = sum(1 for r in grounded if r["groundedness"] == "bad")

    latencies = [r["latency_ms"] for r in rows]
    avg_latency = sum(latencies) / total
    max_latency = max(latencies)

    error_counts: dict[str, int] = {}
    for r in rows:
        error_counts[r["errors"]] = error_counts.get(r["errors"], 0) + 1

    lines = [
        "# Eval Summary — Card-on-File Assistant (agent_with_tool.py)",
        "",
        "```",
        f"Total cases: {total}",
        f"Success rate: {success}/{total} = {success / total:.0%}",
        f"Partial success: {partial}/{total} = {partial / total:.0%}",
        f"Failure rate: {fail}/{total} = {fail / total:.0%}",
        "",
        f"Groundedness good: {g_good}/{len(grounded)} = {g_good / len(grounded):.0%}",
        f"Groundedness partial: {g_partial}/{len(grounded)} = {g_partial / len(grounded):.0%}",
        f"Groundedness bad: {g_bad}/{len(grounded)} = {g_bad / len(grounded):.0%}",
        "",
        f"Average latency: {avg_latency:.0f} ms",
        f"Max latency: {max_latency} ms",
        "",
        "Error types:",
    ]
    for err, count in sorted(error_counts.items(), key=lambda kv: -kv[1]):
        lines.append(f"  {err}: {count}")
    lines.append("```")

    with open(path, "w") as f:
        f.write("\n".join(lines))


def main() -> None:
    rows = run()
    write_results_md(rows, "outputs/eval_results.md")
    write_summary_md(rows, "outputs/eval_summary.md")
    print("\nWrote outputs/eval_results.md and outputs/eval_summary.md")


if __name__ == "__main__":
    main()
