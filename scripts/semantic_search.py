"""
Query the FAISS index built by scripts/build_faiss_index.py.

Run from the project root:
    python scripts/semantic_search.py "your question here"

This script reads:
    data/processed/chunks.jsonl
    data/index/faiss.index

The `search()` function is also imported by later retrieval pipelines
(e.g. the RAG answer-generation script).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from build_faiss_index import load_jsonl_records

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
CHUNKS_PATH = Path("data/processed/chunks.jsonl")
INDEX_PATH = Path("data/index/faiss.index")
DEFAULT_QUERY = "How does a device generate a token for a card during checkout?"
TOP_K = 3


def search(
    query: str,
    model: SentenceTransformer,
    index: faiss.Index,
    chunks: list[dict[str, Any]],
    top_k: int = TOP_K,
) -> list[dict[str, Any]]:
    """
    Embed a query and return the top-k matching chunks with their scores.
    """
    query_embedding = model.encode([query], convert_to_numpy=True).astype("float32")
    faiss.normalize_L2(query_embedding)
    scores, indices = index.search(query_embedding, top_k)

    results: list[dict[str, Any]] = []
    for score, chunk_index in zip(scores[0], indices[0]):
        if chunk_index == -1:
            continue
        chunk = chunks[int(chunk_index)]
        results.append(
            {
                "score": float(score),
                "chunk_id": chunk["chunk_id"],
                "text": chunk["text"],
                "metadata": chunk.get("metadata", {}),
            }
        )
    return results


def main() -> None:
    if not CHUNKS_PATH.exists() or not INDEX_PATH.exists():
        raise FileNotFoundError(
            "Chunks file or FAISS index not found. "
            "Run scripts/build_faiss_index.py first."
        )

    query = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_QUERY

    chunks = load_jsonl_records(CHUNKS_PATH)
    index = faiss.read_index(str(INDEX_PATH))
    model = SentenceTransformer(MODEL_NAME)

    print(f"Query: {query}")
    print(f"Top-k: {TOP_K}")
    print()

    results = search(query=query, model=model, index=index, chunks=chunks, top_k=TOP_K)

    for rank, result in enumerate(results, start=1):
        metadata = result["metadata"]
        print("-" * 80)
        print(f"Rank: {rank}")
        print(f"Score: {result['score']:.4f}")
        print(f"Chunk ID: {result['chunk_id']}")
        print(f"Source file: {metadata.get('source_file')}")
        print(f"Section: {metadata.get('section')}")
        print("Text preview:")
        print(result["text"][:400])
    print("-" * 80)


if __name__ == "__main__":
    main()
