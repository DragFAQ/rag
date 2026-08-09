"""
Orchestration layer combining retrieval (RAG) with an external tool call.

Run from the project root:
    python scripts/agent_with_tool.py "your question here"

Requires OPENAI_API_KEY (see .env.example), same as scripts/rag_answer.py.

Pipeline:
    question -> retrieve top-k chunks (FAISS) for static context
             -> model call with tool available (get_token_status)
             -> if model requests the tool: validate args -> execute -> feed
                result back -> final model call
             -> if no tool call: answer from retrieved context directly
             -> grounded answer with chunk_id / tool citations

This is the integration-layer pattern from lesson 8: the model only proposes
which tool to call and with what arguments; this script validates and
executes it. The model never touches the mock token vault directly.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from external_tool import TOOL_SCHEMA, get_token_status
from rag_answer import DEFAULT_LLM_MODEL, format_context, require_api_key
from semantic_search import load_retrieval_components
from semantic_search import search as retrieve_chunks

TOP_K = 4

SYSTEM_PROMPT = """
You are a technical assistant for Mastercard Secure Card on File (Card-on-File
tokenization) developer documentation.
You have two sources of information:
1. Retrieved documentation context, provided below in the user message.
2. A tool, get_token_status, which returns the LIVE status of one specific
   token by its token_reference (format TKN-XXXXXX).

Rules:
- Use the tool only when the user asks about the current status of a
  specific token reference. Never use it for general conceptual questions.
- Answer conceptual questions only from the provided documentation context,
  never from general knowledge.
- Do not invent missing details, endpoints, field names, status codes, or
  token data.
- If neither the context nor the tool gives enough information, say exactly:
  "I do not have enough information in the provided documentation to answer this question."
- Always cite the chunk_id(s)/source file(s) used, and/or the token_reference
  looked up via the tool.
- Keep the answer concise and technically precise.
""".strip()

USER_MESSAGE_TEMPLATE = """
Documentation context:
{context}

Developer question:
{question}
""".strip()


def build_messages(question: str, context: str) -> list[dict[str, Any]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": USER_MESSAGE_TEMPLATE.format(context=context, question=question),
        },
    ]


def execute_tool_call(name: str, arguments_json: str) -> dict[str, Any]:
    """Validate and dispatch a model-requested tool call. Never raises."""
    if name != "get_token_status":
        return {"error": f"Unknown tool: {name}"}

    try:
        arguments = json.loads(arguments_json)
    except json.JSONDecodeError:
        return {"error": "Tool arguments were not valid JSON"}

    token_reference = arguments.get("token_reference")
    if not token_reference or not isinstance(token_reference, str):
        return {"error": "token_reference is required and must be a string"}

    return get_token_status(token_reference)


def answer_question(
    question: str,
    model,
    index,
    chunks: list[dict[str, Any]],
    client: OpenAI,
    llm_model: str,
    top_k: int = TOP_K,
) -> dict[str, Any]:
    """Run the retrieve -> model (+ optional tool call) -> answer pipeline."""
    retrieved = retrieve_chunks(question, model, index, chunks, top_k=top_k)
    context = format_context(retrieved)
    messages = build_messages(question, context)

    response = client.chat.completions.create(
        model=llm_model,
        messages=messages,
        tools=[TOOL_SCHEMA],
    )
    reply = response.choices[0].message
    tool_calls_made: list[dict[str, Any]] = []

    if reply.tool_calls:
        messages.append(reply.model_dump(exclude_unset=True))
        for tool_call in reply.tool_calls:
            result = execute_tool_call(
                tool_call.function.name, tool_call.function.arguments
            )
            tool_calls_made.append(
                {
                    "name": tool_call.function.name,
                    "arguments": tool_call.function.arguments,
                    "result": result,
                }
            )
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result),
                }
            )

        response = client.chat.completions.create(model=llm_model, messages=messages)
        reply = response.choices[0].message

    return {
        "question": question,
        "retrieved": retrieved,
        "tool_calls": tool_calls_made,
        "answer": reply.content or "",
    }


def main() -> None:
    load_dotenv()
    require_api_key()
    llm_model = os.getenv("OPENAI_MODEL", DEFAULT_LLM_MODEL)
    client = OpenAI()

    question = (
        sys.argv[1] if len(sys.argv) > 1 else "What is the status of token TKN-100234?"
    )

    embedding_model, index, chunks = load_retrieval_components()
    result = answer_question(question, embedding_model, index, chunks, client, llm_model)

    print(f"Question: {result['question']}")
    print()
    print("Retrieved chunks:")
    for chunk in result["retrieved"]:
        print(f"  - {chunk['chunk_id']} (score: {chunk['score']:.4f})")
    print()
    print("Tool calls:")
    if result["tool_calls"]:
        for call in result["tool_calls"]:
            print(f"  - {call['name']}({call['arguments']}) -> {call['result']}")
    else:
        print("  (none)")
    print()
    print("Answer:")
    print(result["answer"])


if __name__ == "__main__":
    main()
