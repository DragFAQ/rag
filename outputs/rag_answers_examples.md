# RAG Answer Examples

## 1. What is a serviceId and how is it created?

Category: clear answer in context

Retrieved chunks: mastercard_register_entities_chunk_006, mastercard_register_entities_chunk_004, mastercard_register_entities_chunk_010, mastercard_register_entities_chunk_003

Answer:
A `serviceId` is a unique identifier created by Mastercard using the `programName` for an entity. It is used by the Integrator to create tokens for that entity. The `serviceId` is assigned based on the Program Type, which is a Mastercard-defined business category assigned during onboarding. You can retrieve the `serviceId` by making a GET request to the Merchant Registration API using a `batchId` returned from a previous request or by receiving Merchant status notifications. (Source: mastercard_register_entities_chunk_004, mastercard_register_entities_chunk_010, mastercard_register_entities_chunk_003)

Source: data/raw/mastercard_register_entities.md

Comment: Good. Fully grounded, cites the specific chunks used, no invented fields.

---

## 2. How do I get a unique identifier from Mastercard for my program so I can create tokens?

Category: rephrased question (same topic as above)

Retrieved chunks: mastercard_register_entities_chunk_001, mastercard_register_entities_chunk_004, mastercard_tokenization-of-existing-card_chunk_004, mastercard_displaying-tokenized-pan-details_chunk_007

Answer:
You get a unique identifier called `serviceId` from Mastercard by registering your consumer-facing entity with Secure Card on File and providing your entity name in the `programName` field. Mastercard uses the `programName` to create the `serviceId`, which you then use to create tokens for that entity. The `serviceId` assignment depends on your Program Type, which is a Mastercard-defined business category assigned during onboarding (mastercard_register_entities_chunk_001 and mastercard_register_entities_chunk_004).

Source: data/raw/mastercard_displaying-tokenized-pan-details.md, data/raw/mastercard_register_entities.md, data/raw/mastercard_tokenization-of-existing-card.md

Comment: Good. Different wording ("unique identifier for my program") still retrieved the same `serviceId` chunks as Q1 and produced a consistent, grounded answer — confirms the embedding model generalizes across phrasing for this topic. One retrieved chunk (`mastercard_tokenization-of-existing-card_chunk_004`) was noise, but the model correctly ignored it rather than citing it.

---

## 3. What is Mastercard's current stock price?

Category: insufficient context (out of domain)

Retrieved chunks: mastercard_displaying-tokenized-pan-details_chunk_003, mastercard_displaying-tokenized-pan-details_chunk_004, mastercard_displaying-tokenized-pan-details_chunk_001, mastercard_displaying-tokenized-pan-details_chunk_007

Answer:
I do not have enough information in the provided documentation to answer this question. (source chunks: mastercard_displaying-tokenized-pan-details_chunk_001, _003, _004, _007)

Source: data/raw/mastercard_displaying-tokenized-pan-details.md

Comment: Correct fallback. FAISS has no relevance threshold, so it still returns its top-4 nearest chunks (all from an unrelated PAN-display doc, scores well below the ~0.5+ range seen on relevant queries) — the fallback rule in the prompt is what prevents the model from fabricating a stock price using those irrelevant chunks.

---

## 4. How do I reset a cardholder's online banking password?

Category: insufficient context / weak retrieved chunk

Retrieved chunks: mastercard_tokenization-of-existing-card_chunk_005, mastercard_managing_tokens_chunk_008, mastercard_managing_tokens_chunk_011, mastercard_managing_tokens_chunk_019

Answer:
I do not have enough information in the provided documentation to answer this question. (source: mastercard_tokenization-of-existing-card_chunk_005, mastercard_managing_tokens_chunk_008, mastercard_managing_tokens_chunk_011, mastercard_managing_tokens_chunk_019)

Source: data/raw/mastercard_managing_tokens.md, data/raw/mastercard_tokenization-of-existing-card.md

Comment: Correct fallback, and the harder case — retrieval returned token-management chunks that are topically adjacent (both mention "tokens") but don't answer the question. Semantic similarity alone can't distinguish "token status" from "password reset"; the prompt's fallback rule is what stops the model from stretching those chunks into an answer.

---

## 5. What HTTP status code indicates successful token provisioning?

Category: clear answer in context

Retrieved chunks: mastercard_tokenization-while-transacting_chunk_012, mastercard_tokenization-while-adding-card_chunk_008, mastercard_tokenization-while-adding-card_chunk_009, mastercard_tokenization-of-existing-card_chunk_007

Answer:
The HTTP status code that indicates successful token provisioning is **200**. This applies when the response is simply "Successful" or "Successful but requires additional verification" (in which case a `pendingEvents` object will be populated but the token is still provisioned in an active state with no additional action required).

Reference: 
- mastercard_tokenization-while-adding-card_chunk_009
- mastercard_tokenization-of-existing-card_chunk_007
- mastercard_tokenization-while-adding-card_chunk_008
- mastercard_tokenization-while-transacting_chunk_012

Source: data/raw/mastercard_tokenization-of-existing-card.md, data/raw/mastercard_tokenization-while-adding-card.md, data/raw/mastercard_tokenization-while-transacting.md

Comment: Good. Correctly identifies 200 as the status code and adds the "Successful but requires additional verification" nuance from a second chunk without contradicting itself — a reasonable multi-chunk synthesis.

---

## 6. What is the difference between tokenization while adding a card and tokenization while transacting?

Category: clear answer in context (multi-chunk synthesis)

Retrieved chunks: mastercard_tokenization-while-transacting_chunk_001, mastercard_tokenization-while-adding-card_chunk_001, mastercard_tokenization-of-existing-card_chunk_001, mastercard_tokenization-of-existing-card_chunk_002

Answer:
The difference between tokenization while adding a card and tokenization while transacting is:

- **Tokenization while adding a card**: The cardholder proactively adds a PAN (card number) to the merchant website/app. The Integrator then initiates token creation by calling Enroll Card with the card details. Mastercard contacts the Issuer for authorization, and if approved, provisions the token and returns an active token response to the Integrator for storing and future transactions. (Source: mastercard_tokenization-while-adding-card_chunk_001)

- **Tokenization while transacting**: The cardholder initiates a payment using a card that is not yet tokenized at the time of transaction. During the payment, the token is created by enrolling the PAN into Secure Card on File, and the token is associated with the cardholder’s profile for future transactions. (Source: mastercard_tokenization-while-transacting_chunk_001)

In summary, adding a card tokenizes the PAN ahead of any transaction, while tokenization while transacting creates the token during the payment process itself.

Source: data/raw/mastercard_tokenization-of-existing-card.md, data/raw/mastercard_tokenization-while-adding-card.md, data/raw/mastercard_tokenization-while-transacting.md

Comment: Good. Correctly synthesizes across two different source documents (one chunk per flow) into a clear side-by-side comparison, with per-flow citations.

---

## 7. What must an acquirer support to process DSRP card-on-file token transactions?

Category: clear answer in context

Retrieved chunks: mastercard_making-payments_chunk_010, mastercard_making-payments_chunk_009, mastercard_making-payments_chunk_021, mastercard_making-payments_chunk_008

Answer:
An acquirer that processes DSRP card-on-file token transactions must support acceptance of DSRP card-on-file tokens and e-commerce Security Level Indicator (SLI) values of 246 for standard payments and 247 for recurring/partial shipment payments. Additionally, the DSRP cryptogram must be sent in the DE104 – DPD (Digital Payment Data) field. (source: mastercard_making-payments_chunk_010 and mastercard_making-payments_chunk_009 of mastercard_making-payments.md)

Source: data/raw/mastercard_making-payments.md

Comment: Good. Correctly extracts the DSRP/SLI 246/247 requirement and cites source chunks precisely; verified against the raw chunk text — no hallucinated values.

---

## 8. As an acquirer, what do I need to support to accept these recurring payment tokens?

Category: rephrased question (same topic as above)

Retrieved chunks: mastercard_making-payments_chunk_008, mastercard_making-payments_chunk_009, mastercard_making-payments_chunk_010, mastercard_making-payments_chunk_021

Answer:
As an acquirer, to accept recurring payment tokens you must:

- Accept DSRP (Digital Secure Remote Payment) card-on-file tokens.
- Support e-commerce Security Level Indicator (SLI) values of **247** for recurring/partial shipment payments.
- For the initial payment, the DSRP cryptogram is required and must be sent in the DE104 – DPD (Digital Payment Data) field.
- Subsequent recurring or merchant-initiated transactions may be sent without the DSRP cryptogram.
- If a transaction declines, you must request the Token Requester for the latest token and cryptogram for authorization and avoid retrying an invalid cryptogram more than 10 times to prevent token lock.

Reference: mastercard_making-payments_chunk_009, mastercard_making-payments_chunk_010, mastercard_making-payments_chunk_021 (mastercard_making-payments.md)

Source: data/raw/mastercard_making-payments.md

Comment: Good, and more complete than Q7 — the rephrased "recurring payment" wording pulled in `chunk_021` (the recurring/partial-shipment DSRP details) in addition to the chunks Q7 retrieved, so the answer picked up the extra retry-limit detail. Verified against raw chunk text (`chunk_010`): "Retrying the invalid cryptogram more than 10 times may potentially lock the token" — not hallucinated. Shows that phrasing changes which chunks surface even for the same underlying topic.
