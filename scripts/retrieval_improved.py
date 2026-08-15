"""
Improved retrieval: metadata post-filtering plus simple hybrid scoring.

Run from the project root:
    python scripts/retrieval_improved.py "your question here"
    python scripts/retrieval_improved.py "your question here" --topic payments
    python scripts/retrieval_improved.py "your question here" --topic payments --hybrid

Pipeline:
    query -> FAISS top candidate_k -> metadata post-filter -> hybrid rescoring
    -> final_k chunks

Both steps are optional, so the same function covers all four configurations in
outputs/retrieval_comparison.md. With neither one on, retrieve() returns the
same results as the baseline search.
"""

from __future__ import annotations

import argparse
import re
from typing import Any

import faiss
from sentence_transformers import SentenceTransformer

from semantic_search import load_retrieval_components
from semantic_search import search as semantic_search

CANDIDATE_K = 10
FINAL_K = 3
SEMANTIC_WEIGHT = 0.7
KEYWORD_WEIGHT = 0.3


def tokenize(text: str) -> set[str]:
    """Split text into a set of lowercase word tokens for overlap scoring."""
    return set(re.findall(r"\b\w+\b", text.lower()))


def keyword_overlap_score(query: str, text: str) -> float:
    """Fraction of query terms that appear in the chunk. No IDF weighting."""
    query_terms = tokenize(query)
    if not query_terms:
        return 0.0
    return len(query_terms & tokenize(text)) / len(query_terms)


def metadata_matches(result: dict[str, Any], metadata_filter: dict[str, str]) -> bool:
    """Check that a chunk's metadata matches every key in the filter."""
    metadata = result.get("metadata", {})
    return all(metadata.get(key) == value for key, value in metadata_filter.items())


def apply_metadata_filter(
    results: list[dict[str, Any]], metadata_filter: dict[str, str]
) -> list[dict[str, Any]]:
    """
    Drop candidates whose metadata does not match the filter.

    FAISS stores vectors only, so this runs after the search. It can return
    fewer than final_k results, and a matching chunk below candidate_k is
    never seen.
    """
    return [result for result in results if metadata_matches(result, metadata_filter)]


def add_hybrid_scores(query: str, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Blend semantic and keyword scores, then re-sort by the combined score."""
    scored_results: list[dict[str, Any]] = []
    for result in results:
        semantic_score = result["score"]
        keyword_score = keyword_overlap_score(query, result["text"])
        scored_results.append(
            {
                **result,
                "semantic_score": semantic_score,
                "keyword_score": keyword_score,
                "hybrid_score": (
                    SEMANTIC_WEIGHT * semantic_score + KEYWORD_WEIGHT * keyword_score
                ),
            }
        )
    scored_results.sort(key=lambda result: result["hybrid_score"], reverse=True)
    return scored_results


def retrieve(
    query: str,
    model: SentenceTransformer,
    index: faiss.Index,
    chunks: list[dict[str, Any]],
    metadata_filter: dict[str, str] | None = None,
    use_hybrid: bool = False,
    candidate_k: int = CANDIDATE_K,
    final_k: int = FINAL_K,
) -> list[dict[str, Any]]:
    """Retrieve chunks, optionally metadata-filtered and hybrid-reranked."""
    results = semantic_search(
        query=query, model=model, index=index, chunks=chunks, top_k=candidate_k
    )
    if metadata_filter:
        results = apply_metadata_filter(results, metadata_filter)
    if use_hybrid:
        results = add_hybrid_scores(query, results)
    return results[:final_k]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Retrieve chunks with optional metadata filtering and hybrid scoring."
    )
    parser.add_argument("query", help="the question to search for")
    parser.add_argument(
        "--topic",
        help="restrict results to one topic (entity_registration, token_creation, "
        "token_management, token_display, payments)",
    )
    parser.add_argument(
        "--hybrid",
        action="store_true",
        help="rerank candidates by hybrid score instead of semantic score alone",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    metadata_filter = {"topic": args.topic} if args.topic else None

    model, index, chunks = load_retrieval_components()
    results = retrieve(
        query=args.query,
        model=model,
        index=index,
        chunks=chunks,
        metadata_filter=metadata_filter,
        use_hybrid=args.hybrid,
    )

    print(f"Query: {args.query}")
    print(f"Metadata filter: {metadata_filter or 'none'}")
    print(f"Hybrid scoring: {'on' if args.hybrid else 'off'}")
    print(f"Candidates: {CANDIDATE_K} -> final: {FINAL_K}")
    print()

    if not results:
        print("No results: the metadata filter excluded every candidate.")
        return

    for rank, result in enumerate(results, start=1):
        metadata = result["metadata"]
        print("-" * 80)
        print(f"Rank: {rank}")
        if args.hybrid:
            print(f"Hybrid score: {result['hybrid_score']:.4f}")
            print(f"  Semantic: {result['semantic_score']:.4f}")
            print(f"  Keyword: {result['keyword_score']:.4f}")
        else:
            print(f"Score: {result['score']:.4f}")
        print(f"Chunk ID: {result['chunk_id']}")
        print(f"Topic: {metadata.get('topic')}")
        print(f"Source file: {metadata.get('source_file')}")
        print(f"Section: {metadata.get('section')}")
        print("Text preview:")
        print(result["text"][:400])
    print("-" * 80)


if __name__ == "__main__":
    main()
