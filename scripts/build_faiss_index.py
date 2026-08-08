"""
Build embeddings and a FAISS index for the chunked knowledge base.

Run from the project root:
    python scripts/build_faiss_index.py

This script reads:
    data/processed/chunks.jsonl

And produces:
    data/processed/embeddings.npy
    data/index/faiss.index
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
CHUNKS_PATH = Path("data/processed/chunks.jsonl")
EMBEDDINGS_PATH = Path("data/processed/embeddings.npy")
INDEX_PATH = Path("data/index/faiss.index")


def load_jsonl_records(input_path: Path) -> list[dict[str, Any]]:
    """
    Load JSON records from a file that holds one or more JSON objects back
    to back (either one per line, or pretty-printed across several lines).
    """
    decoder = json.JSONDecoder()
    text = input_path.read_text(encoding="utf-8")
    records: list[dict[str, Any]] = []
    position = 0
    length = len(text)
    while position < length:
        while position < length and text[position] in " \t\r\n":
            position += 1
        if position >= length:
            break
        record, position = decoder.raw_decode(text, position)
        records.append(record)
    return records


def normalize_embeddings(embeddings: np.ndarray) -> np.ndarray:
    """
    Normalize vectors so IndexFlatIP behaves like cosine similarity search.
    """
    embeddings = embeddings.astype("float32")
    faiss.normalize_L2(embeddings)
    return embeddings


def main() -> None:
    if not CHUNKS_PATH.exists():
        raise FileNotFoundError(
            f"Chunks file not found: {CHUNKS_PATH}. "
            "Run scripts/prepare_knowledge_base.py first."
        )

    print(f"Embedding model: {MODEL_NAME}")
    print(f"Input chunks: {CHUNKS_PATH}")

    chunks = load_jsonl_records(CHUNKS_PATH)
    if not chunks:
        raise ValueError("No chunks found. Please check the input chunks file.")
    print(f"Chunks loaded: {len(chunks)}")

    texts = [chunk["text"] for chunk in chunks]

    print("Loading embedding model...")
    model = SentenceTransformer(MODEL_NAME)

    print("Creating embeddings...")
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
    embeddings = normalize_embeddings(embeddings)
    embedding_dimension = embeddings.shape[1]
    print(f"Embeddings shape: {embeddings.shape}")

    print("Building FAISS index with IndexFlatIP...")
    index = faiss.IndexFlatIP(embedding_dimension)
    index.add(embeddings)

    EMBEDDINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    np.save(EMBEDDINGS_PATH, embeddings)
    faiss.write_index(index, str(INDEX_PATH))

    print(f"Saved embeddings: {EMBEDDINGS_PATH}")
    print(f"Saved FAISS index: {INDEX_PATH}")
    print(f"Vectors in index: {index.ntotal}")


if __name__ == "__main__":
    main()
