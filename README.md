# RAG Project

## Subject Area

**Mastercard Secure Card on File (Card-on-File tokenization) developer documentation.**
The knowledge base covers how integrators register entities, tokenize cards, manage
tokens, and make payments using Mastercard's Secure Card on File APIs.

## Sources

All documents were fetched from the Mastercard Developers portal
(`developer.mastercard.com`) and saved as Markdown with YAML frontmatter into `data/raw/`:

| Document | Source URL |
|---|---|
| Register Entities to Create Tokens | https://developer.mastercard.com/mastercard-checkout-solutions/documentation/use-cases/card-on-file/register_entities/ |
| Manage Tokens | https://developer.mastercard.com/mastercard-checkout-solutions/documentation/use-cases/card-on-file/managing-tokens/ |
| Display Tokenized PAN Details | https://developer.mastercard.com/mastercard-checkout-solutions/documentation/use-cases/card-on-file/displaying-tokenized-pan-details/ |
| Make Payments | https://developer.mastercard.com/mastercard-checkout-solutions/documentation/use-cases/card-on-file/making-payments/ |
| Tokenization of an Existing Card | https://developer.mastercard.com/mastercard-checkout-solutions/documentation/use-cases/card-on-file/create-tokens/tokenization-of-existing-card/ |
| Tokenization while Transacting | https://developer.mastercard.com/mastercard-checkout-solutions/documentation/use-cases/card-on-file/create-tokens/tokenization-while-transacting/ |
| Tokenization While Adding a Card | https://developer.mastercard.com/mastercard-checkout-solutions/documentation/use-cases/card-on-file/create-tokens/tokenization-while-adding-card/ |

These are JS-rendered SPA pages, so raw HTML fetches return no content — pages were
rendered with headless Chrome, then the `<article>` content was converted to Markdown.

## Metadata Structure

`scripts/prepare_knowledge_base.py` produces two JSONL files in `data/processed/`.

**`normalized_documents.jsonl`** — one record per source document:

```json
{
  "document_id": "mastercard_register_entities",
  "source_file": "data/raw/mastercard_register_entities.md",
  "source_type": "markdown",
  "title": "Register Entities to Create Tokens",
  "text": "...full document body...",
  "metadata": {
    "language": "en",
    "domain": "payments",
    "document_type": "api_documentation",
    "source_url": "https://developer.mastercard.com/.../register_entities/",
    "retrieved": "2026-07-20"
  }
}
```

**`chunks.jsonl`** — one record per chunk, carrying denormalized parent-document metadata:

```json
{
  "chunk_id": "mastercard_register_entities_chunk_004",
  "text": "...chunk text...",
  "metadata": {
    "document_id": "mastercard_register_entities",
    "source_file": "data/raw/mastercard_register_entities.md",
    "source_type": "markdown",
    "title": "Register Entities to Create Tokens",
    "section": "ServiceId Creation",
    "chunk_index": 4,
    "language": "en",
    "domain": "payments",
    "document_type": "api_documentation",
    "source_url": "https://developer.mastercard.com/.../register_entities/"
  }
}
```

`section` holds the nearest Markdown heading at or before the start of the chunk, so a
chunk can be traced back to its place in the document without re-reading the source file.

## Chunking Strategy

- **Method**: unit-based packing with overlap (`chunk_units_with_overlap` in
  `scripts/prepare_knowledge_base.py`), not a raw character sliding window. The document
  is first split into semantic units — one per non-empty line: a heading, paragraph, list
  item, or table row (Markdown source already has one such unit per line). Units are then
  packed greedily into a chunk until adding the next one would exceed `chunk_size`; the
  chunk is closed on a unit boundary and a trailing overlap of whole units carries into
  the next chunk. A unit that is larger than `chunk_size` on its own (e.g. one very long
  table row) is split on sentence boundaries instead, falling back to a hard character
  split only if a single sentence still doesn't fit.
- **Chunk size**: target 700 characters (actual chunks range ~70–800 characters, since
  boundaries snap to whole units rather than a hard cutoff — still within the 500–1000
  character guideline; short chunks are complete short paragraphs, not truncated ones)
- **Overlap**: 150 characters, carried as whole trailing units (not raw characters)
- **Chunk ID**: `{document_id}_chunk_{index:03d}`, stable and predictable across reruns

This guarantees every chunk boundary lands on a paragraph/heading/list-item/table-row
edge — no chunk starts or ends mid-word or mid-sentence (verified: 0/100 chunks start
with a lowercase letter, down from 83% under an earlier plain character-offset splitter).

## Example Chunks

**1. `mastercard_displaying-tokenized-pan-details_chunk_001`** (section: *Display Tokenized PAN Details*)
```
# Display Tokenized PAN Details
Cardholders may view, use, or manage their cards during the profile management or
checkout experience.
Integrators can also choose to provide a visual representation of their cards (that is,
by using card art) that allows consumers to easily recogn...
```

**2. `mastercard_making-payments_chunk_009`** (section: *Cardholder-Initiated Transaction*)
```
**Warning**:
- The acquirer that will process these transactions must accept DSRP card-on-file tokens
  and e-commerce Security Level Indicator (SLI) values of **246** for standard payments
  and **247** for recurring/partial shipment payments. DSRP cryptogram is required to be
  sent...
```

**3. `mastercard_managing_tokens_chunk_012`** (section: *Reason Code Updates* — sentence-split
fallback piece of the one table row that exceeds 700 characters on its own)
```
If only expiry changes, calling the Checkout API is optional.<br><br>For TOKEN_REFRESH,
you will receive both `maskedCard` and encrypted `paymentData` (containing DPAN and DPAN
expiry). For events other than TOKEN_REFRESH, you will only receive `maskedCard`. |
```

**4. `mastercard_register_entities_chunk_004`** (section: *ServiceId Creation*)
```
- If no, consider registering entities separately under different program names.
## ServiceId Creation
---
Using the `programName`, Mastercard creates a `serviceId`, which is a unique identifier
for that entity. The Integrator uses this `serviceId` to create tokens for that entit...
```

**5. `mastercard_making-payments_chunk_004`** (section: *Cardholder-Initiated Transaction* —
shortest chunk in the set, 69 characters; complete on its own, not truncated)
```
Detailed steps are explained below:
**Call the Checkout API request**
```

## What Worked Well / What to Improve

**Worked well:**
- Packing whole units (paragraphs/headings/list items/table rows) instead of raw
  character offsets means chunk boundaries never fall mid-word or mid-sentence.
- Denormalizing document metadata (title, section, source URL, domain) onto every chunk
  means each chunk is self-describing for retrieval and citation, no join needed at
  query time.
- Predictable, stable chunk IDs (`{document_id}_chunk_{index:03d}`) make chunks easy to
  debug and re-index across reruns.
- Keeping `raw/` and `processed/` separate, with `processed/` fully regenerable from
  `raw/`, makes the pipeline safe to re-run after edits.

**To improve:**
- Chunk size now varies (~70–800 characters) instead of being uniform, because
  boundaries snap to whole units. This trades size consistency for readability — a
  reasonable trade for this use case, but worth watching if very short chunks turn out
  to be too thin on context during retrieval evaluation.
- Table rows (e.g. Reason Code Updates, Token Status) are still occasionally split
  across chunks when a single row exceeds `chunk_size`; the sentence-boundary fallback
  keeps text readable but loses the row's original column framing (see example 3 above).
- `section` is derived from the nearest heading only — nested subsections under the same
  H2 aren't distinguished, so retrieval can't tell "Program Name" apart from a deeper
  subsection under it without reading the chunk text itself.

## Semantic Retrieval

`scripts/build_faiss_index.py` embeds every chunk in `data/processed/chunks.jsonl` with
`sentence-transformers/all-MiniLM-L6-v2` (384-dim, CPU) and builds a FAISS `IndexFlatIP`
index over the L2-normalized vectors (inner product on normalized vectors = cosine
similarity).

Generated in `data/`:
- `data/processed/embeddings.npy` — normalized embedding matrix, shape `(num_chunks, 384)`
- `data/index/faiss.index` — FAISS index, one vector per chunk in the same order as
  `chunks.jsonl`

`scripts/semantic_search.py` embeds a query with the same model and returns the top-k
chunks by cosine similarity, each with its score, `chunk_id`, and metadata. Its `search()`
function is written to be imported by later pipelines (e.g. answer generation) rather
than only run standalone.

This is baseline vector search only — no metadata filtering, hybrid scoring, or
reranking.

`scripts/generate_retrieval_examples.py` runs 8 test queries (direct-topic,
rephrased, exact field code, descriptive phrasing, out-of-domain) through
`search()` and writes `outputs/retrieval_examples.md` — Top-3 per query with
score/text preview/source, a relevance comment, and a conclusion on where
retrieval works well vs. poorly.

## Grounded Answer Generation

`scripts/rag_answer.py` adds an LLM answer on top of retrieval:

```text
question -> retrieve top-k chunks (FAISS) -> prompt with context -> OpenAI chat
completion -> grounded answer with chunk_id / source citations
```

The system prompt requires the model to:
- answer only from the retrieved context, never from general knowledge;
- say explicitly that it does not have enough information when context is
  insufficient, instead of guessing;
- cite the `chunk_id` and source file it used.

Requires `OPENAI_API_KEY` (and optionally `OPENAI_MODEL`, default `gpt-4.1-mini`) —
copy `.env.example` to `.env` and fill in the key.

`scripts/run_qa_examples.py` runs a fixed set of test questions (clear answer,
rephrased question, out-of-domain/insufficient context, weak retrieval) through the
pipeline and writes:
- `outputs/rag_answers_examples.md` — question, retrieved chunks, answer, source
- `outputs/prompt_improvements.md` — before/after comparison of a naive prompt vs.
  the grounded prompt on a few selected questions

## Directory Layout

```text
rag/
  data/
    raw/        # Source documents (Markdown with YAML frontmatter)
    processed/  # Generated: normalized_documents.jsonl, chunks.jsonl, embeddings.npy
    index/      # Generated: faiss.index
    README.md
  scripts/
    prepare_knowledge_base.py  # Normalize raw/ into processed/
    build_faiss_index.py       # Embed chunks and build the FAISS index
    semantic_search.py         # Query the FAISS index
    generate_retrieval_examples.py  # Run test queries and write outputs/retrieval_examples.md
    rag_answer.py              # Retrieve + prompt + call the LLM for one question
    run_qa_examples.py         # Run the test question set and write outputs/
  outputs/      # Generated: retrieval_examples.md, rag_answers_examples.md,
                #            prompt_improvements.md
  .env.example  # Copy to .env and fill in OPENAI_API_KEY
  .venv/        # Local Python 3.10 virtual environment (not committed)
  README.md
```

## Quick Start

1. Create and activate the virtual environment (Python 3.10+):
   ```
   python3.10 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Add source documents to `data/raw/` (Markdown, with `source` / `title` / `retrieved`
   frontmatter — see existing files for the expected format).
3. Run the preparation script:
   ```
   python scripts/prepare_knowledge_base.py
   ```
4. Check the output in `data/processed/normalized_documents.jsonl` and
   `data/processed/chunks.jsonl`.
5. Build embeddings and the FAISS index:
   ```
   python scripts/build_faiss_index.py
   ```
6. Try semantic search:
   ```
   python scripts/semantic_search.py "How does a device generate a token for a card during checkout?"
   ```
7. Generate the retrieval-quality report (no API key needed):
   ```
   python scripts/generate_retrieval_examples.py
   ```
8. Copy `.env.example` to `.env` and set `OPENAI_API_KEY`.
9. Ask a grounded question:
   ```
   python scripts/rag_answer.py "How is a serviceId created and what is it used for?"
   ```
10. Generate the full test-question report:
    ```
    python scripts/run_qa_examples.py
    ```

## Development Principles

- Treat `data/processed/` as regenerable output — never hand-edit it, re-run the script instead.
- Keep raw and processed data in separate subfolders.
- Document the source URL and retrieval date for every raw document.
