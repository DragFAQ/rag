# Prompt Template — Grounded RAG Answer Generation

Used by `scripts/rag_answer.py` for all answers in `outputs/rag_answers_examples.md`.

## System prompt

```
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
```

## User message

```
Context:
{context}

Developer question:
{question}

Answer:
```

`{context}` is built by `format_context()` in `scripts/rag_answer.py` by concatenating the
top-k retrieved chunks, each rendered as:

```
Source chunk ID: {chunk_id}
Source file: {source_file}
Content:
{chunk text}
```

separated by `---`.

## Design notes

- **Grounding rule** ("only the provided context", "do not invent") — prevents the model
  from filling gaps with general knowledge about tokenization or payments.
- **Fallback rule** — a fixed, literal refusal string rather than free-form "I don't know"
  phrasing, so downstream code can detect abstention by exact string match instead of
  parsing prose.
- **Citation rule** — the model must name `chunk_id` and source file, which is only
  possible because those are pushed into the context block per chunk (no separate lookup
  needed at answer time).
- **Weak baseline** for comparison (see `outputs/prompt_improvements.md`) has none of the
  three rules above:

  ```
  Answer the question using the context.
  Context:
  {context}
  Question:
  {question}
  ```

See `README.md` → "Grounded Answer Generation" for how this fits into the full
retrieve → prompt → answer pipeline, and `outputs/prompt_improvements.md` for concrete
before/after examples of what the grounding/fallback/citation rules change in practice.
