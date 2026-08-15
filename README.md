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

These are JS-rendered SPA pages, so raw HTML fetches return no content. Pages were
rendered with headless Chrome, then the `<article>` content was converted to Markdown.

## Metadata Structure

`scripts/prepare_knowledge_base.py` produces two JSONL files in `data/processed/`.

**`normalized_documents.jsonl`**: one record per source document.

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
    "topic": "entity_registration",
    "source_url": "https://developer.mastercard.com/.../register_entities/",
    "retrieved": "2026-07-20"
  }
}
```

**`chunks.jsonl`**: one record per chunk, carrying denormalized parent-document metadata.

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
    "topic": "entity_registration",
    "source_url": "https://developer.mastercard.com/.../register_entities/"
  }
}
```

`section` holds the nearest Markdown heading at or before the start of the chunk, so a
chunk can be traced back to its place in the document without re-reading the source file.

`topic` is declared in each raw document's frontmatter and groups the 7 documents into
5 subject areas. It was added to make metadata filtering possible. The obvious fields to
filter on (`document_type`, `domain`, `language`, `source_type`) have the same value for
every chunk in this corpus, so a filter on any of them excludes nothing.

| Topic | Documents | Chunks |
|---|---|---|
| `token_creation` | tokenization-while-transacting, -while-adding-card, -of-existing-card | 33 |
| `token_management` | managing_tokens | 28 |
| `payments` | making-payments | 22 |
| `entity_registration` | register_entities | 10 |
| `token_display` | displaying-tokenized-pan-details | 7 |

## Chunking Strategy

- **Method**: unit-based packing with overlap (`chunk_units_with_overlap` in
  `scripts/prepare_knowledge_base.py`), not a raw character sliding window. The document
  is first split into semantic units, one per non-empty line: a heading, paragraph, list
  item, or table row (Markdown source already has one such unit per line). Units are then
  packed greedily into a chunk until adding the next one would exceed `chunk_size`; the
  chunk is closed on a unit boundary and a trailing overlap of whole units carries into
  the next chunk. A unit that is larger than `chunk_size` on its own (e.g. one very long
  table row) is split on sentence boundaries instead, falling back to a hard character
  split only if a single sentence still doesn't fit.
- **Chunk size**: target 700 characters (actual chunks range ~70-800 characters, since
  boundaries snap to whole units rather than a hard cutoff, still within the 500-1000
  character guideline; short chunks are complete short paragraphs, not truncated ones)
- **Overlap**: 150 characters, carried as whole trailing units (not raw characters)
- **Chunk ID**: `{document_id}_chunk_{index:03d}`, stable and predictable across reruns

This guarantees every chunk boundary lands on a paragraph/heading/list-item/table-row
edge, so no chunk starts or ends mid-word or mid-sentence (verified: 0/100 chunks start
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

**3. `mastercard_managing_tokens_chunk_012`** (section: *Reason Code Updates*, sentence-split
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

**5. `mastercard_making-payments_chunk_004`** (section: *Cardholder-Initiated Transaction*,
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
- Chunk size now varies (~70-800 characters) instead of being uniform, because
  boundaries snap to whole units. This trades size consistency for readability, which is
  a reasonable trade here, but worth watching if very short chunks turn out
  to be too thin on context during retrieval evaluation.
- Table rows (e.g. Reason Code Updates, Token Status) are still occasionally split
  across chunks when a single row exceeds `chunk_size`; the sentence-boundary fallback
  keeps text readable but loses the row's original column framing (see example 3 above).
- `section` is derived from the nearest heading only, so nested subsections under the same
  H2 aren't distinguished, so retrieval can't tell "Program Name" apart from a deeper
  subsection under it without reading the chunk text itself.

## Semantic Retrieval

`scripts/build_faiss_index.py` embeds every chunk in `data/processed/chunks.jsonl` with
`sentence-transformers/all-MiniLM-L6-v2` (384-dim, CPU) and builds a FAISS `IndexFlatIP`
index over the L2-normalized vectors (inner product on normalized vectors = cosine
similarity).

Generated in `data/`:
- `data/processed/embeddings.npy`: normalized embedding matrix, shape `(num_chunks, 384)`
- `data/index/faiss.index`: FAISS index, one vector per chunk in the same order as
  `chunks.jsonl`

`scripts/semantic_search.py` embeds a query with the same model and returns the top-k
chunks by cosine similarity, each with its score, `chunk_id`, and metadata. Its `search()`
function is written to be imported by later pipelines (e.g. answer generation) rather
than only run standalone.

This is baseline vector search only, with no metadata filtering, hybrid scoring, or
reranking. Those are added in `scripts/retrieval_improved.py` below. This script is left
unchanged so it stays the baseline the comparison measures against.

`scripts/generate_retrieval_examples.py` runs 8 test queries (direct-topic,
rephrased, exact field code, descriptive phrasing, out-of-domain) through
`search()` and writes `outputs/retrieval_examples.md`: Top-3 per query with
score/text preview/source, a relevance comment, and a conclusion on where
retrieval works well vs. poorly.

## Improved Retrieval

`scripts/retrieval_improved.py` adds two improvements on top of the baseline, each
independently switchable:

```text
query -> FAISS top-10 candidates -> metadata post-filter -> hybrid rescoring -> top-3
```

**Metadata filtering** drops candidates whose `topic` does not match the filter. FAISS
stores vectors only, so this runs in Python after the search, not inside the query. That
means the filter can return fewer than `final_k` results (or none), and a matching chunk
ranked below `candidate_k` is never seen. A vector database would push the same
constraint into the query layer instead:

```sql
-- pgvector equivalent, where the filter runs before ranking
SELECT chunk_id, text, metadata FROM chunks
WHERE metadata->>'topic' = 'payments'
ORDER BY embedding <=> :query_embedding LIMIT 3;
```

**Hybrid scoring** blends the semantic score with a keyword overlap score:

```text
hybrid = 0.7 * semantic_score + 0.3 * keyword_overlap
keyword_overlap = |query_terms ∩ chunk_terms| / |query_terms|
```

Overlap is unweighted, so a rare field code counts the same as a stopword, and the two
scores are combined raw even though cosine similarity spans roughly 0.25-0.68 on this
corpus while overlap spans 0-1. Both limitations show up in the comparison report.

```bash
python scripts/retrieval_improved.py "What does the DE104 field contain?"
python scripts/retrieval_improved.py "What does the DE104 field contain?" --topic payments
python scripts/retrieval_improved.py "What does the DE104 field contain?" --topic payments --hybrid
```

With no filter and no `--hybrid`, `retrieve()` returns the same result as the baseline,
since the FAISS candidate list is already ordered by semantic score.

`scripts/generate_retrieval_comparison.py` runs the same 8 queries as HW2 through four
configurations (baseline, filter only, hybrid only, both) and writes
`outputs/retrieval_comparison.md`. Running each improvement alone is the only way to tell
which one caused a change.

It also runs a supplementary set of 11 **cross-topic** queries. The HW2 queries each
target a single document, so the baseline rarely crosses topics on them and the filter
has little to remove, which limits the measurable gain. The cross-topic queries are
worded to pull toward a topic that does not hold the answer.

### Findings

- Metadata filtering was the more effective of the two. It cut the search space from 100
  chunks to 7-33 per query and removed the last off-topic chunk from the top 3, without
  ever making a result worse.
- On the cross-topic queries the filter took correct-topic top-1 from 5/11 to 11/11 and
  answer-chunk-in-top-3 from 8/11 to 10/11, fixing all 6 baseline failures. The margins
  were tiny: the off-topic chunk beat the on-topic one by as little as 0.0006, so no score
  threshold could separate them and only a hard constraint helps. This matches the HW2
  finding that similarity score is not a usable relevance signal here. Only 7 of 40
  probed queries (18%) failed this way, so it guards against an uncommon failure rather
  than giving a broad lift.
- Hybrid scoring was close to neutral. It raised answer-bearing chunks in the top 3 from
  11 to 13, but changed top-1 on only one in-domain query, where the old and new top-1
  both carry the answer.
- Two reasons hybrid underdelivered. With weights 0.7/0.3 a challenger needs a keyword
  advantage of 2.33x its semantic deficit, and in 4 of 6 in-domain queries the baseline
  top-1 already had the higher keyword score. Unweighted overlap can also tie: the top
  three chunks for *"What is a serviceId and how is it created?"* all score 0.6250,
  because `serviceid` appears in all three and the rest of the matches are stopwords.
- Baseline top-1 document accuracy was already 6/6, so there was no document-level recall
  to recover. What was left to improve is the make-up of the top 3.
- One failure neither technique fixes. That same serviceId query still returns a table of
  entity types as top-1, with the answer at rank 2. Filtering cannot help (same topic)
  and unweighted overlap cannot help (exact tie). It needs IDF weighting or a reranker.
- Filtering has a limit. *"Where do I find the wallet or DPA identifier for a payment?"*
  gets the correct topic but the chunks naming `dpaData.dpaURI` still miss the top 3.
  Filtering controls which documents get searched, not how chunks rank inside them.
- Over-aggressive filters are a real risk. Filtering a token-provisioning question to
  `topic=token_management` returns zero results, and post-filtering has no fallback, so
  the answer leaves the candidate set for good.
- Both improvements cost 6-8 ms per query, within noise of the baseline and dominated by
  the query embedding.

## Grounded Answer Generation

See [`PROMPT_TEMPLATE.md`](PROMPT_TEMPLATE.md) for the full prompt template (system
prompt + user message) used below, and the weak baseline it's compared against.

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

Requires `OPENAI_API_KEY` (and optionally `OPENAI_MODEL`, default `gpt-4.1-mini`).
Copy `.env.example` to `.env` and fill in the key.

`scripts/run_qa_examples.py` runs a fixed set of test questions (clear answer,
rephrased question, out-of-domain/insufficient context, weak retrieval) through the
pipeline and writes:
- `outputs/rag_answers_examples.md`: question, retrieved chunks, answer, source
- `outputs/prompt_improvements.md`: before/after comparison of a naive prompt vs.
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
    semantic_search.py         # Query the FAISS index (baseline)
    generate_retrieval_examples.py  # Run test queries and write outputs/retrieval_examples.md
    retrieval_improved.py      # Baseline + metadata filtering + hybrid scoring
    generate_retrieval_comparison.py  # Compare all 4 configurations, write outputs/
    rag_answer.py              # Retrieve + prompt + call the LLM for one question
    run_qa_examples.py         # Run the test question set and write outputs/
  outputs/      # Generated: retrieval_examples.md, retrieval_comparison.md,
                #            rag_answers_examples.md, prompt_improvements.md
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
2. Add source documents to `data/raw/` (Markdown, with `source` / `title` / `topic` /
   `retrieved` frontmatter, see existing files for the expected format).
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
8. Try improved retrieval, and generate the baseline-vs-improved comparison
   (no API key needed):
   ```
   python scripts/retrieval_improved.py "What does the DE104 field contain?" --topic payments --hybrid
   python scripts/generate_retrieval_comparison.py
   ```
9. Copy `.env.example` to `.env` and set `OPENAI_API_KEY`.
10. Ask a grounded question:
    ```
    python scripts/rag_answer.py "How is a serviceId created and what is it used for?"
    ```
11. Generate the full test-question report:
    ```
    python scripts/run_qa_examples.py
    ```

## Development Principles

- Treat `data/processed/` as regenerable output. Never hand-edit it, re-run the script instead.
- Keep raw and processed data in separate subfolders.
- Document the source URL and retrieval date for every raw document.
