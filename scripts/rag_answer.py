"""
Grounded QA pipeline: retrieve chunks, build a prompt, call the LLM, cite sources.

Run from the project root:
    python scripts/rag_answer.py "your question here"

Requires OPENAI_API_KEY (and optionally OPENAI_MODEL) in the environment or a
.env file — copy .env.example to .env and fill it in.

Pipeline:
    question -> retrieve top-k chunks (FAISS) -> prompt with context
    -> OpenAI chat completion -> grounded answer with chunk_id / source citations
"""

from __future__ import annotations

import os
import sys
from typing import Any

import faiss
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer

from semantic_search import load_retrieval_components
from semantic_search import search as retrieve_chunks

DEFAULT_LLM_MODEL = "gpt-4.1-mini"
TOP_K = 4

SYSTEM_PROMPT = """
You are a technical assistant for Mastercard Secure Card on File (Card-on-File
tokenization) developer documentation.
Answer the developer's question using only the provided context below.
Rules:
- Do not use any knowledge outside the provided context.
- Do not invent missing details, endpoints, field names, or status codes.
- If the context does not contain enough information to answer, say exactly:
  "I do not have enough information in the provided documentation to answer this question."
- Always cite the chunk_id(s) and source file(s) you used in your answer.
- Keep the answer concise and technically precise.
""".strip()

USER_MESSAGE_TEMPLATE = """
Context:
{context}

Developer question:
{question}

Answer:
""".strip()


def require_api_key() -> None:
    """Fail early if OPENAI_API_KEY is missing."""
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY is not set. "
            "Create a .env file (see .env.example) or export OPENAI_API_KEY."
        )


def format_context(retrieved: list[dict[str, Any]]) -> str:
    """Render retrieved chunks into the context block passed to the LLM."""
    blocks = []
    for chunk in retrieved:
        metadata = chunk.get("metadata", {})
        blocks.append(
            f"Source chunk ID: {chunk['chunk_id']}\n"
            f"Source file: {metadata.get('source_file')}\n"
            f"Content:\n{chunk['text']}"
        )
    return "\n---\n".join(blocks)


def call_llm(client: OpenAI, model: str, system_prompt: str, user_message: str) -> str:
    """Call the Chat Completions API with a system/user message pair."""
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    )
    return response.choices[0].message.content or ""


def answer_question(
    question: str,
    model: SentenceTransformer,
    index: faiss.Index,
    chunks: list[dict[str, Any]],
    client: OpenAI,
    llm_model: str,
    top_k: int = TOP_K,
) -> dict[str, Any]:
    """Run the full retrieve -> prompt -> answer pipeline for one question."""
    retrieved = retrieve_chunks(question, model, index, chunks, top_k=top_k)
    context = format_context(retrieved)
    user_message = USER_MESSAGE_TEMPLATE.format(context=context, question=question)
    answer = call_llm(client, llm_model, SYSTEM_PROMPT, user_message)
    return {
        "question": question,
        "retrieved": retrieved,
        "answer": answer,
    }


def main() -> None:
    load_dotenv()
    require_api_key()
    llm_model = os.getenv("OPENAI_MODEL", DEFAULT_LLM_MODEL)
    client = OpenAI()

    question = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "How is a serviceId created and what is it used for?"
    )

    embedding_model, index, chunks = load_retrieval_components()
    result = answer_question(
        question, embedding_model, index, chunks, client, llm_model
    )

    print(f"Question: {result['question']}")
    print()
    print("Retrieved chunks:")
    for chunk in result["retrieved"]:
        print(f"  - {chunk['chunk_id']} (score: {chunk['score']:.4f})")
    print()
    print("Answer:")
    print(result["answer"])


if __name__ == "__main__":
    main()
