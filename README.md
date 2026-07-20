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
- No embeddings/indexing step yet — `chunks.jsonl` is the last stage implemented so far.

## Directory Layout

```text
rag/
  data/
    raw/        # Source documents (Markdown with YAML frontmatter)
    processed/  # Generated: normalized_documents.jsonl, chunks.jsonl
    README.md
  scripts/
    prepare_knowledge_base.py  # Normalize raw/ into processed/
  .venv/        # Local Python 3.10 virtual environment (not committed)
  README.md
```

## Quick Start

1. Create and activate the virtual environment (Python 3.10+):
   ```
   python3.10 -m venv .venv
   source .venv/bin/activate
   ```
2. Add source documents to `data/raw/` (Markdown, with `source` / `title` / `retrieved`
   frontmatter — see existing files for the expected format).
3. Run the preparation script:
   ```
   python scripts/prepare_knowledge_base.py
   ```
4. Check the output in `data/processed/normalized_documents.jsonl` and
   `data/processed/chunks.jsonl`.

## Development Principles

- Treat `data/processed/` as regenerable output — never hand-edit it, re-run the script instead.
- Keep raw and processed data in separate subfolders.
- Document the source URL and retrieval date for every raw document.
