# Prompt Improvements

## Example 1: What is Mastercard's current stock price?

### Before (weak prompt, no fallback/citation rule)
```
Answer the question using the context.
Context:
{context}
Question:
{question}
```

Model answer:
The provided context contains information about Mastercard's tokenized PAN details and card display guidelines but does not include any information about Mastercard's current stock price. Therefore, I cannot answer the question about Mastercard's current stock price based on the given context.

### After (grounded prompt with fallback + citation rule)
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

Model answer:
I do not have enough information in the provided documentation to answer this question. (source chunks: mastercard_displaying-tokenized-pan-details_chunk_001, _003, _004, _007)

### What changed
Both prompts correctly avoided answering — the weak prompt happens to work here because the retrieved chunks are visibly about PAN display, not stock prices, so the gap is obvious even without an explicit rule. The real problem with the weak prompt is that it has no *fixed* refusal phrase and no citation requirement: its answer is a paragraph of reasoning rather than a consistent, machine-checkable fallback string, and it never names which chunks it looked at. The grounded prompt produces a stable, literal fallback sentence plus explicit chunk IDs — needed for any downstream logic (e.g. "did the pipeline abstain?") or UI citation rendering.

---

## Example 2: How do I reset a cardholder's online banking password?

### Before (weak prompt, no fallback/citation rule)
```
Answer the question using the context.
Context:
{context}
Question:
{question}
```

Model answer:
The provided context does not include information or instructions on how to reset a cardholder's online banking password. The context focuses on Mastercard tokenization, token statuses, and updating token and masked card details, but does not cover online banking password management.

To reset a cardholder's online banking password, please refer to the specific bank or financial institution's online banking support resources or customer service. Typically, this involves a process on the bank's website or app where the cardholder can select "Forgot Password" and follow prompts to verify identity and reset the password.

### After (grounded prompt with fallback + citation rule)
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

Model answer:
I do not have enough information in the provided documentation to answer this question. (source: mastercard_tokenization-of-existing-card_chunk_005, mastercard_managing_tokens_chunk_008, mastercard_managing_tokens_chunk_011, mastercard_managing_tokens_chunk_019)

### What changed
This is the clearest failure of the weak prompt: after correctly noting the context doesn't cover password resets, it went on to answer anyway from general knowledge ("select 'Forgot Password' and follow prompts...") — exactly the hallucination risk the HW is testing for. The grounded prompt's explicit rule ("Do not use any knowledge outside the provided context") and fixed refusal string stop this. This is the strongest before/after example of the three: same weak retrieval, but the weak prompt actively fabricates an answer while the grounded prompt abstains.

---

## Example 3: What is the difference between tokenization while adding a card and tokenization while transacting?

### Before (weak prompt, no fallback/citation rule)
```
Answer the question using the context.
Context:
{context}
Question:
{question}
```

Model answer:
The difference between **tokenization while adding a card** and **tokenization while transacting** lies in the timing and process of token creation:

- **Tokenization While Adding a Card**: This occurs when the cardholder proactively adds their PAN (Primary Account Number) to a merchant's website or app before any transaction takes place. The Integrator initiates a tokenization request by enrolling the card details (PAN, Expiry Date, CVC2) with Mastercard. Mastercard then sends a Tokenization Authorization Request to the Issuer, which approves it. Mastercard creates the token and returns the digital card details to the Integrator, who stores the token linked to the customer profile for future use. This process happens as part of card enrollment or card addition flow.

- **Tokenization While Transacting**: This happens when the cardholder initiates a payment using a card that has not yet been tokenized. During the transaction, the system creates a token by enrolling the PAN into Secure Card on File as part of the transaction flow. The token is then associated with the cardholder’s profile so future transactions can use the token instead of the PAN.

In summary, **tokenization while adding a card** is a pre-emptive process done at card enrollment time, while **tokenization while transacting** happens on the fly during a transaction if the card isn’t tokenized yet.

### After (grounded prompt with fallback + citation rule)
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

Model answer:
The difference between tokenization while adding a card and tokenization while transacting is:

- **Tokenization while adding a card**: The cardholder proactively adds a PAN (card number) to the merchant website/app. The Integrator then initiates token creation by calling Enroll Card with the card details. Mastercard contacts the Issuer for authorization, and if approved, provisions the token and returns an active token response to the Integrator for storing and future transactions. (Source: mastercard_tokenization-while-adding-card_chunk_001)

- **Tokenization while transacting**: The cardholder initiates a payment using a card that is not yet tokenized at the time of transaction. During the payment, the token is created by enrolling the PAN into Secure Card on File, and the token is associated with the cardholder’s profile for future transactions. (Source: mastercard_tokenization-while-transacting_chunk_001)

In summary, adding a card tokenizes the PAN ahead of any transaction, while tokenization while transacting creates the token during the payment process itself.

### What changed
Here both prompts land on a factually similar, correct comparison — the weak prompt isn't wrong on content because the context happened to be sufficient and unambiguous. The visible difference is citation: the weak answer never names a single chunk_id or source file, so there's no way to verify or trace it back to the docs, while the grounded answer cites the exact chunk per bullet point. For questions with a clean, unambiguous context match, the prompt's main value-add is enforceable traceability rather than correctness.
