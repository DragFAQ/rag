"""
Run a fixed set of test questions through the RAG answer pipeline and write
outputs/rag_answers_examples.md and outputs/prompt_improvements.md.

Run from the project root:
    python scripts/run_qa_examples.py

Requires OPENAI_API_KEY (see .env.example).
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from rag_answer import (
    DEFAULT_LLM_MODEL,
    SYSTEM_PROMPT,
    answer_question,
    format_context,
    load_retrieval_components,
    require_api_key,
)

OUTPUTS_DIR = Path("outputs")
ANSWERS_OUTPUT_PATH = OUTPUTS_DIR / "rag_answers_examples.md"
IMPROVEMENTS_OUTPUT_PATH = OUTPUTS_DIR / "prompt_improvements.md"

TEST_QUESTIONS = [
    {
        "question": "What is a serviceId and how is it created?",
        "category": "clear answer in context",
    },
    {
        "question": (
            "How do I get a unique identifier from Mastercard for my program "
            "so I can create tokens?"
        ),
        "category": "rephrased question (same topic as above)",
    },
    {
        "question": "What is Mastercard's current stock price?",
        "category": "insufficient context (out of domain)",
    },
    {
        "question": "How do I reset a cardholder's online banking password?",
        "category": "insufficient context / weak retrieved chunk",
    },
    {
        "question": "What HTTP status code indicates successful token provisioning?",
        "category": "clear answer in context",
    },
    {
        "question": (
            "What is the difference between tokenization while adding a card "
            "and tokenization while transacting?"
        ),
        "category": "clear answer in context (multi-chunk synthesis)",
    },
    {
        "question": (
            "What must an acquirer support to process DSRP card-on-file token "
            "transactions?"
        ),
        "category": "clear answer in context",
    },
    {
        "question": (
            "As an acquirer, what do I need to support to accept these "
            "recurring payment tokens?"
        ),
        "category": "rephrased question (same topic as above)",
    },
]

# Naive baseline prompt (no fallback rule, no citation requirement) used only
# to demonstrate prompt improvements on a few selected questions.
WEAK_USER_MESSAGE_TEMPLATE = """
Answer the question using the context.
Context:
{context}
Question:
{question}
""".strip()

# Indices into TEST_QUESTIONS used for the before/after prompt comparison.
PROMPT_IMPROVEMENT_QUESTION_INDICES = [2, 3, 5]


def run_weak_prompt(client: OpenAI, llm_model: str, question: str, context: str) -> str:
    user_message = WEAK_USER_MESSAGE_TEMPLATE.format(context=context, question=question)
    response = client.chat.completions.create(
        model=llm_model,
        messages=[{"role": "user", "content": user_message}],
    )
    return response.choices[0].message.content or ""


def format_answer_entry(index: int, item: dict, result: dict) -> str:
    chunk_ids = ", ".join(chunk["chunk_id"] for chunk in result["retrieved"])
    sources = ", ".join(
        sorted({chunk["metadata"].get("source_file", "") for chunk in result["retrieved"]})
    )
    return (
        f"## {index}. {item['question']}\n\n"
        f"Category: {item['category']}\n\n"
        f"Retrieved chunks: {chunk_ids}\n\n"
        f"Answer:\n{result['answer']}\n\n"
        f"Source: {sources}\n\n"
        f"Comment: _fill in after reviewing the answer above_\n"
    )


def format_improvement_entry(
    index: int, question: str, weak_answer: str, grounded_answer: str
) -> str:
    return (
        f"## Example {index}: {question}\n\n"
        f"### Before (weak prompt, no fallback/citation rule)\n"
        f"```\n{WEAK_USER_MESSAGE_TEMPLATE}\n```\n\n"
        f"Model answer:\n{weak_answer}\n\n"
        f"### After (grounded prompt with fallback + citation rule)\n"
        f"```\n{SYSTEM_PROMPT}\n```\n\n"
        f"Model answer:\n{grounded_answer}\n\n"
        f"### What changed\n_fill in after comparing the two answers above_\n"
    )


def main() -> None:
    load_dotenv()
    require_api_key()
    llm_model = os.getenv("OPENAI_MODEL", DEFAULT_LLM_MODEL)
    client = OpenAI()

    embedding_model, index, chunks = load_retrieval_components()

    answer_entries = []
    improvement_entries = []

    for position, item in enumerate(TEST_QUESTIONS, start=1):
        result = answer_question(
            item["question"], embedding_model, index, chunks, client, llm_model
        )
        answer_entries.append(format_answer_entry(position, item, result))
        print(f"[{position}/{len(TEST_QUESTIONS)}] {item['question']}")

        if position - 1 in PROMPT_IMPROVEMENT_QUESTION_INDICES:
            context = format_context(result["retrieved"])
            weak_answer = run_weak_prompt(client, llm_model, item["question"], context)
            improvement_entries.append(
                format_improvement_entry(
                    len(improvement_entries) + 1,
                    item["question"],
                    weak_answer,
                    result["answer"],
                )
            )

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    ANSWERS_OUTPUT_PATH.write_text(
        "# RAG Answer Examples\n\n" + "\n---\n\n".join(answer_entries), encoding="utf-8"
    )
    IMPROVEMENTS_OUTPUT_PATH.write_text(
        "# Prompt Improvements\n\n" + "\n---\n\n".join(improvement_entries),
        encoding="utf-8",
    )

    print(f"Wrote {ANSWERS_OUTPUT_PATH}")
    print(f"Wrote {IMPROVEMENTS_OUTPUT_PATH}")


if __name__ == "__main__":
    main()
