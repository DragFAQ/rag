"""
Run a fixed set of test queries through semantic search and write
outputs/retrieval_examples.md (per-query top-3 results + relevance comment).

Run from the project root:
    python scripts/generate_retrieval_examples.py
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

OUTPUTS_DIR = Path("outputs")
OUTPUT_PATH = OUTPUTS_DIR / "retrieval_examples.md"
TOP_K = 3

TEST_QUERIES = [
    {
        "query": "What is a serviceId and how is it created?",
        "comment": "relevant",
    },
    {
        "query": "How do I get a unique identifier from Mastercard for my program?",
        "comment": "relevant",
    },
    {
        "query": "What HTTP status code indicates successful token provisioning?",
        "comment": "relevant",
    },
    {
        "query": "What must an acquirer support to process DSRP token transactions?",
        "comment": "relevant",
    },
    {
        "query": "Tell me about card art and visual representation of stored cards",
        "comment": "partially relevant",
    },
    {
        "query": "What does the DE104 field contain?",
        "comment": (
            "relevant, but low confidence — Top-1 does contain the answer, but "
            "it's a small part of a chunk mostly about SLI values, so its score "
            "is lower than several clearly irrelevant results (see Conclusion)."
        ),
    },
    {
        "query": "What is Mastercard's current stock price?",
        "comment": "not relevant",
    },
    {
        "query": "How do I reset a cardholder's online banking password?",
        "comment": "not relevant",
    },
]

CONCLUSION = """
## Conclusion

**Where retrieval works well:**
- Direct-topic and rephrased queries about a concept the docs name explicitly
  (`serviceId`, DSRP/SLI acquirer requirements, token provisioning status
  codes) reliably surface the correct chunk as Top-1, scoring 0.48-0.68.
  Rephrasing "serviceId" as "unique identifier for my program" (Query 2, 0.60)
  actually scored *higher* than the literal term (Query 1, 0.48) — the model
  is matching meaning, not just shared vocabulary.

**Where retrieval is weak, and the biggest finding — score is not a reliable
relevance signal in this corpus:**
- The two out-of-domain queries (stock price, password reset) still return
  top-3 chunks, since `IndexFlatIP` always returns its k nearest neighbors with
  no similarity threshold. Query 7 (stock price) scored 0.39-0.42 as expected
  for something unrelated — but Query 8 (password reset) scored 0.48-0.49,
  landing squarely inside the same range as clearly *relevant* Query 1
  (0.46-0.48). A fixed score cutoff would either accept the irrelevant
  password-reset chunks or reject the relevant serviceId chunks — it can't do
  both correctly at once.
- Worse, the DE104 query (Query 6) scored only 0.26-0.31 even though its Top-1
  chunk genuinely contains the answer — the answering sentence is a small part
  of a chunk mostly about SLI values, so the chunk's embedding isn't pulled
  strongly toward the specific field code. This chunk scored *lower* than the
  irrelevant password-reset chunks. Exact codes/field names get diluted by
  whatever else is in the same chunk; a keyword/BM25 pass (Lesson 5's hybrid
  retrieval) would catch this reliably where semantic similarity doesn't.
- Descriptive phrasing ("card art and visual representation") retrieved the
  right document but ranked the introductory chunk above the chunk that
  actually names the `artUri` field — right document, imperfect chunk-level
  ranking.
- **Practical implication:** since similarity score alone can't separate
  relevant from irrelevant here, the answer-generation layer (HW4) needs an
  explicit LLM-side fallback rule ("say you don't have enough information")
  rather than a retrieval-side score threshold — which is exactly what
  `scripts/rag_answer.py` implements and what Examples 3/4 in
  `outputs/rag_answers_examples.md` demonstrate.
""".strip()


def format_query_entry(index: int, item: dict[str, Any], results: list[dict[str, Any]]) -> str:
    lines = [f"## Query {index}: {item['query']}", ""]
    for rank, result in enumerate(results, start=1):
        metadata = result["metadata"]
        preview = result["text"][:160].replace("\n", " ")
        lines.append(
            f"Top-{rank}: {result['chunk_id']} | score: {result['score']:.4f}"
        )
        lines.append(f"  Text: {preview}...")
        lines.append(f"  Source: {metadata.get('source_file')}")
    lines.append("")
    lines.append(f"Comment: {item['comment']}")
    return "\n".join(lines)


def main() -> None:
    from semantic_search import load_retrieval_components, search

    model, index, chunks = load_retrieval_components()

    entries = []
    for position, item in enumerate(TEST_QUERIES, start=1):
        results = search(item["query"], model, index, chunks, top_k=TOP_K)
        entries.append(format_query_entry(position, item, results))
        print(f"[{position}/{len(TEST_QUERIES)}] {item['query']}")

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        "# Retrieval Examples\n\n" + "\n\n---\n\n".join(entries) + "\n\n---\n\n" + CONCLUSION,
        encoding="utf-8",
    )
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
