"""
Normalize raw knowledge base documents and split them into chunks.

Run from the project root:
    python scripts/prepare_knowledge_base.py

Purpose:
    Convert raw source documents (Markdown files with YAML frontmatter) into
    a single normalized JSONL format, then split each document into
    metadata-rich chunks ready for embeddings.

This script reads:
    - Markdown files with an optional YAML frontmatter header
      (source, title, topic, retrieved)

And produces:
    data/processed/normalized_documents.jsonl
    data/processed/chunks.jsonl
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

HEADING_RE = re.compile(r"^#{1,6}\s+(.+)$")
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
NORMALIZED_OUTPUT_PATH = PROCESSED_DIR / "normalized_documents.jsonl"
CHUNKS_OUTPUT_PATH = PROCESSED_DIR / "chunks.jsonl"
CHUNK_SIZE = 700
CHUNK_OVERLAP = 150


def split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """
    Split a Markdown file into its YAML frontmatter and body text.

    Supports simple `key: value` frontmatter (no nested structures), which
    is what the raw documents in this project use.
    """
    if not text.startswith("---"):
        return {}, text

    lines = text.splitlines()
    closing_index = next(
        (i for i in range(1, len(lines)) if lines[i].strip() == "---"), None
    )
    if closing_index is None:
        return {}, text

    frontmatter: dict[str, str] = {}
    for line in lines[1:closing_index]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        frontmatter[key.strip()] = value.strip()

    body = "\n".join(lines[closing_index + 1 :]).strip()
    return frontmatter, body


def extract_markdown_title(text: str) -> str | None:
    """
    Extract the first H1 heading from a Markdown document.
    """
    for line in text.splitlines():
        stripped_line = line.strip()
        if stripped_line.startswith("# "):
            return stripped_line.replace("# ", "", 1).strip()
    return None


def read_markdown_file(file_path: Path) -> dict[str, Any]:
    """
    Read a Markdown file and convert it into a normalized document object.
    """
    raw_text = file_path.read_text(encoding="utf-8")
    frontmatter, body = split_frontmatter(raw_text)

    title = (
        frontmatter.get("title")
        or extract_markdown_title(body)
        or file_path.stem.replace("_", " ").replace("-", " ").title()
    )

    return {
        "document_id": file_path.stem,
        "source_file": str(file_path),
        "source_type": "markdown",
        "title": title,
        "text": body,
        "metadata": {
            "language": "en",
            "domain": "payments",
            "document_type": "api_documentation",
            "topic": frontmatter.get("topic"),
            "source_url": frontmatter.get("source"),
            "retrieved": frontmatter.get("retrieved"),
        },
    }


def load_raw_sources(raw_dir: Path) -> list[dict[str, Any]]:
    """
    Load supported source files from the raw directory.
    Supported formats:
        - .md
    """
    documents: list[dict[str, Any]] = []
    for file_path in sorted(raw_dir.iterdir()):
        if file_path.suffix.lower() == ".md":
            documents.append(read_markdown_file(file_path))
        else:
            print(f"Warning: unsupported file type skipped: {file_path}")
    return documents


def save_jsonl(records: list[dict[str, Any]], output_path: Path) -> None:
    """
    Save records in JSONL format (one JSON object per line).
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as output_file:
        for record in records:
            output_file.write(json.dumps(record, ensure_ascii=False) + "\n")


def extract_units(text: str) -> list[str]:
    """
    Split text into semantic units (headings, paragraphs, list items, table
    rows) — one per non-empty line. Markdown source in this project already
    puts one such unit per line, separated by blank lines.
    """
    return [line.strip() for line in text.splitlines() if line.strip()]


def extract_heading(unit: str) -> str | None:
    """Return the heading text if this unit is a Markdown heading line."""
    match = HEADING_RE.match(unit)
    return match.group(1).strip() if match else None


def joined_length(units: list[str]) -> int:
    """Length of `units` if joined with newlines."""
    return sum(len(unit) for unit in units) + max(len(units) - 1, 0)


def split_oversized_unit(
    unit: str, chunk_size: int, overlap: int
) -> list[str]:
    """
    Split a single unit that is larger than chunk_size on its own.

    Prefers sentence boundaries so pieces stay readable; only falls back to
    a hard character split if a single sentence still exceeds chunk_size.
    """
    sentences = [s for s in SENTENCE_SPLIT_RE.split(unit) if s]
    if len(sentences) <= 1:
        return split_text_by_chars(unit, chunk_size, overlap)

    pieces: list[str] = []
    current = ""
    for sentence in sentences:
        candidate = f"{current} {sentence}".strip() if current else sentence
        if len(candidate) <= chunk_size:
            current = candidate
            continue
        if current:
            pieces.append(current)
        if len(sentence) > chunk_size:
            pieces.extend(split_text_by_chars(sentence, chunk_size, overlap))
            current = ""
        else:
            current = sentence
    if current:
        pieces.append(current)
    return pieces


def split_text_by_chars(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Last-resort hard character split for text with no sentence breaks."""
    pieces: list[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        piece = text[start:end].strip()
        if piece:
            pieces.append(piece)
        start = end - overlap
    return pieces


def chunk_units_with_overlap(
    units: list[str],
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[tuple[str, str | None]]:
    """
    Pack units into chunks up to chunk_size characters, carrying a trailing
    overlap of whole units into the next chunk so chunk boundaries land on
    paragraph/heading/list-item/table-row edges instead of mid-word.

    Returns (chunk_text, section) pairs, where `section` is the nearest
    Markdown heading seen at or before the start of that chunk.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    def overlap_tail(current: list[str]) -> list[str]:
        tail: list[str] = []
        for unit in reversed(current):
            candidate = [unit] + tail
            if tail and joined_length(candidate) > overlap:
                break
            tail = candidate
        return tail

    results: list[tuple[str, str | None]] = []
    current: list[str] = []
    section_for_current: str | None = None
    running_section: str | None = None

    for unit in units:
        heading = extract_heading(unit)
        if heading:
            running_section = heading

        if len(unit) > chunk_size:
            if current:
                results.append(("\n".join(current), section_for_current))
                current = []
            for piece in split_oversized_unit(unit, chunk_size, overlap):
                results.append((piece, running_section))
            section_for_current = running_section
            continue

        if not current:
            current = [unit]
            section_for_current = running_section
            continue

        if joined_length(current) + 1 + len(unit) > chunk_size:
            results.append(("\n".join(current), section_for_current))
            current = overlap_tail(current) + [unit]
            section_for_current = running_section
        else:
            current.append(unit)

    if current:
        results.append(("\n".join(current), section_for_current))

    return results


def build_chunk_id(document_id: str, chunk_index: int) -> str:
    """Create a stable, predictable chunk ID."""
    return f"{document_id}_chunk_{chunk_index:03d}"


def chunk_document(document: dict[str, Any]) -> list[dict[str, Any]]:
    """Split one normalized document into metadata-rich chunks."""
    units = extract_units(document["text"])
    chunk_results = chunk_units_with_overlap(units)
    chunks: list[dict[str, Any]] = []

    for index, (chunk_text, section) in enumerate(chunk_results, start=1):
        chunks.append(
            {
                "chunk_id": build_chunk_id(document["document_id"], index),
                "text": chunk_text,
                "metadata": {
                    "document_id": document["document_id"],
                    "source_file": document["source_file"],
                    "source_type": document["source_type"],
                    "title": document["title"],
                    "section": section,
                    "chunk_index": index,
                    "language": document["metadata"].get("language"),
                    "domain": document["metadata"].get("domain"),
                    "document_type": document["metadata"].get("document_type"),
                    "topic": document["metadata"].get("topic"),
                    "source_url": document["metadata"].get("source_url"),
                },
            }
        )

    return chunks


def main() -> None:
    if not RAW_DIR.exists():
        raise FileNotFoundError(
            f"Raw data directory not found: {RAW_DIR}. "
            "Please run this script from the project root."
        )

    documents = load_raw_sources(RAW_DIR)
    save_jsonl(documents, NORMALIZED_OUTPUT_PATH)

    all_chunks: list[dict[str, Any]] = []
    for document in documents:
        all_chunks.extend(chunk_document(document))
    save_jsonl(all_chunks, CHUNKS_OUTPUT_PATH)

    print("=" * 80)
    print("PREPARE KNOWLEDGE BASE: NORMALIZE SOURCES")
    print("=" * 80)
    print(f"Raw directory: {RAW_DIR}")
    print(f"Normalized documents: {len(documents)}")
    print(f"Output file: {NORMALIZED_OUTPUT_PATH}")
    print()

    for doc in documents:
        print("-" * 80)
        print(f"Document ID: {doc['document_id']}")
        print(f"Source type: {doc['source_type']}")
        print(f"Title: {doc['title']}")
        print(f"Topic: {doc['metadata']['topic']}")
        preview = doc["text"][:180].replace("\n", " ")
        print(f"Text preview: {preview}...")

    print()
    print("=" * 80)
    print("PREPARE KNOWLEDGE BASE: CHUNK DOCUMENTS")
    print("=" * 80)
    print(f"Input documents: {len(documents)}")
    print(f"Output chunks: {len(all_chunks)}")
    print(f"Chunk size: {CHUNK_SIZE} characters")
    print(f"Chunk overlap: {CHUNK_OVERLAP} characters")
    print(f"Output file: {CHUNKS_OUTPUT_PATH}")
    print()

    for chunk in all_chunks[:3]:
        print("-" * 80)
        print(f"Chunk ID: {chunk['chunk_id']}")
        print(f"Source: {chunk['metadata']['source_file']}")
        print(f"Chunk index: {chunk['metadata']['chunk_index']}")
        preview = chunk["text"][:220].replace("\n", " ")
        print(f"Text preview: {preview}...")


if __name__ == "__main__":
    main()
