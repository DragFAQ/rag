# Retrieval Examples

## Query 1: What is a serviceId and how is it created?

Top-1: mastercard_register_entities_chunk_006 | score: 0.4845
  Text: | **On-Behalf-Of Sub-Merchant** | Payment Facilitator | Payment Facilitator | Sponsored Merchant | Each group of sponsored merchants | **Note**: Payment Facilit...
  Source: data/raw/mastercard_register_entities.md
Top-2: mastercard_register_entities_chunk_004 | score: 0.4660
  Text: - If no, consider registering entities separately under different program names. ## ServiceId Creation --- Using the `programName`, Mastercard creates a `servic...
  Source: data/raw/mastercard_register_entities.md
Top-3: mastercard_register_entities_chunk_010 | score: 0.4601
  Text: Retrieve the `serviceId` for that entity by making a **GET** request to the Merchant Registration API using the `batchId` returned in the previous request. Alte...
  Source: data/raw/mastercard_register_entities.md

Comment: relevant

---

## Query 2: How do I get a unique identifier from Mastercard for my program?

Top-1: mastercard_register_entities_chunk_004 | score: 0.5984
  Text: - If no, consider registering entities separately under different program names. ## ServiceId Creation --- Using the `programName`, Mastercard creates a `servic...
  Source: data/raw/mastercard_register_entities.md
Top-2: mastercard_displaying-tokenized-pan-details_chunk_002 | score: 0.5621
  Text: - Creating a screen for cardholders to manage cards associated with their profile. - Providing an option for cardholders to select between cards before making a...
  Source: data/raw/mastercard_displaying-tokenized-pan-details.md
Top-3: mastercard_register_entities_chunk_001 | score: 0.5530
  Text: # Register Entities to Create Tokens Before registering your entities, visit [Mastercard Connect](https://www.mastercardconnect.com/-/sign-in) to onboard, creat...
  Source: data/raw/mastercard_register_entities.md

Comment: relevant

---

## Query 3: What HTTP status code indicates successful token provisioning?

Top-1: mastercard_tokenization-while-transacting_chunk_012 | score: 0.6292
  Text: ## Understanding Tokenization Results --- **Successful Provisioning** | Result | Response and Details | Action for Integrator | |---|---|---| | 200 | Successful...
  Source: data/raw/mastercard_tokenization-while-transacting.md
Top-2: mastercard_tokenization-while-adding-card_chunk_008 | score: 0.6292
  Text: ## Understanding Tokenization Results --- **Successful Provisioning** | Result | Response and Details | Action for Integrator | |---|---|---| | 200 | Successful...
  Source: data/raw/mastercard_tokenization-while-adding-card.md
Top-3: mastercard_tokenization-while-adding-card_chunk_009 | score: 0.5582
  Text: | Result | Response and Details | Action for Integrator | |---|---|---| | 200 | Successful | No additional action is needed. | | 200 with Successful but *requir...
  Source: data/raw/mastercard_tokenization-while-adding-card.md

Comment: relevant

---

## Query 4: What must an acquirer support to process DSRP token transactions?

Top-1: mastercard_making-payments_chunk_010 | score: 0.6848
  Text: - The acquirer that will process these transactions must accept DSRP card-on-file tokens and e-commerce Security Level Indicator (SLI) values of **246** for sta...
  Source: data/raw/mastercard_making-payments.md
Top-2: mastercard_making-payments_chunk_009 | score: 0.5965
  Text: **Warning**: - The acquirer that will process these transactions must accept DSRP card-on-file tokens and e-commerce Security Level Indicator (SLI) values of **...
  Source: data/raw/mastercard_making-payments.md
Top-3: mastercard_making-payments_chunk_021 | score: 0.5617
  Text: Consumers may also store their cards and allow the business to make payments (merchant-initiated transaction) on their behalf. For instance, businesses submit p...
  Source: data/raw/mastercard_making-payments.md

Comment: relevant

---

## Query 5: Tell me about card art and visual representation of stored cards

Top-1: mastercard_displaying-tokenized-pan-details_chunk_001 | score: 0.5222
  Text: # Display Tokenized PAN Details Cardholders may view, use, or manage their cards during the profile management or checkout experience. Integrators can also choo...
  Source: data/raw/mastercard_displaying-tokenized-pan-details.md
Top-2: mastercard_displaying-tokenized-pan-details_chunk_004 | score: 0.4997
  Text: - If you decide to display card art, utilize the `artUri` found in the [maskedCard.digitalCardData](https://developer.mastercard.com/mastercard-checkout-solutio...
  Source: data/raw/mastercard_displaying-tokenized-pan-details.md
Top-3: mastercard_displaying-tokenized-pan-details_chunk_003 | score: 0.4711
  Text: - If you maintain a local version of the token (`srcDigitalCardId`), keep it updated using the GET Card API and by listening to the [Card Notifications](https:/...
  Source: data/raw/mastercard_displaying-tokenized-pan-details.md

Comment: partially relevant

---

## Query 6: What does the DE104 field contain?

Top-1: mastercard_making-payments_chunk_009 | score: 0.3073
  Text: **Warning**: - The acquirer that will process these transactions must accept DSRP card-on-file tokens and e-commerce Security Level Indicator (SLI) values of **...
  Source: data/raw/mastercard_making-payments.md
Top-2: mastercard_making-payments_chunk_017 | score: 0.2697
  Text: - `dpaData.dpaURI` or `dpaData.dpaData` or `dpaData.PresentationName` - `dpaData.dpaName` - `dpaTransactionOptions.transactionAmount.transactionAmount` - `dpaTr...
  Source: data/raw/mastercard_making-payments.md
Top-3: mastercard_making-payments_chunk_016 | score: 0.2580
  Text: **Digital Transaction Insights (DTI) fraud risk score** Integrators can generate and include a [Mastercard Identity Check](https://developer.mastercard.com/prod...
  Source: data/raw/mastercard_making-payments.md

Comment: relevant, but low confidence — Top-1 does contain the answer, but it's a small part of a chunk mostly about SLI values, so its score is lower than several clearly irrelevant results (see Conclusion).

---

## Query 7: What is Mastercard's current stock price?

Top-1: mastercard_displaying-tokenized-pan-details_chunk_003 | score: 0.4214
  Text: - If you maintain a local version of the token (`srcDigitalCardId`), keep it updated using the GET Card API and by listening to the [Card Notifications](https:/...
  Source: data/raw/mastercard_displaying-tokenized-pan-details.md
Top-2: mastercard_displaying-tokenized-pan-details_chunk_004 | score: 0.3977
  Text: - If you decide to display card art, utilize the `artUri` found in the [maskedCard.digitalCardData](https://developer.mastercard.com/mastercard-checkout-solutio...
  Source: data/raw/mastercard_displaying-tokenized-pan-details.md
Top-3: mastercard_displaying-tokenized-pan-details_chunk_001 | score: 0.3921
  Text: # Display Tokenized PAN Details Cardholders may view, use, or manage their cards during the profile management or checkout experience. Integrators can also choo...
  Source: data/raw/mastercard_displaying-tokenized-pan-details.md

Comment: not relevant

---

## Query 8: How do I reset a cardholder's online banking password?

Top-1: mastercard_tokenization-of-existing-card_chunk_005 | score: 0.4849
  Text: **Tip**: To maximize tokenization performance: - Ensure PAN is still active by calling [Mastercard ABU account inquiry](https://developer.mastercard.com/automat...
  Source: data/raw/mastercard_tokenization-of-existing-card.md
Top-2: mastercard_managing_tokens_chunk_008 | score: 0.4845
  Text: | **ACTIVE** | Token has been unsuspended and is active to use for transactions. | Show Card with `panLastFour` on the UI. Update the stored token's status to A...
  Source: data/raw/mastercard_managing_tokens.md
Top-3: mastercard_managing_tokens_chunk_011 | score: 0.4828
  Text: Use the decrypted DPAN and expiry values to refresh the corresponding [maskedCard](https://developer.mastercard.com/mastercard-checkout-solutions/documentation/...
  Source: data/raw/mastercard_managing_tokens.md

Comment: not relevant

---

## Conclusion

**Where retrieval works well:**
- Direct-topic and rephrased queries about a concept the docs name explicitly
  (`serviceId`, DSRP/SLI acquirer requirements, token provisioning status
  codes) reliably surface the correct chunk as Top-1, scoring 0.48-0.68.
  Rephrasing "serviceId" as "unique identifier for my program" (Query 2, 0.60)
  actually scored *higher* than the literal term (Query 1, 0.48) — the model
  is matching meaning, not just shared vocabulary.

**Where retrieval is weak, and the biggest finding — score is not a reliable
relevance signal in this corpus:**
- The two out-of-domain queries (stock price, password reset) still return
  top-3 chunks, since `IndexFlatIP` always returns its k nearest neighbors with
  no similarity threshold. Query 7 (stock price) scored 0.39-0.42 as expected
  for something unrelated — but Query 8 (password reset) scored 0.48-0.49,
  landing squarely inside the same range as clearly *relevant* Query 1
  (0.46-0.48). A fixed score cutoff would either accept the irrelevant
  password-reset chunks or reject the relevant serviceId chunks — it can't do
  both correctly at once.
- Worse, the DE104 query (Query 6) scored only 0.26-0.31 even though its Top-1
  chunk genuinely contains the answer — the answering sentence is a small part
  of a chunk mostly about SLI values, so the chunk's embedding isn't pulled
  strongly toward the specific field code. This chunk scored *lower* than the
  irrelevant password-reset chunks. Exact codes/field names get diluted by
  whatever else is in the same chunk; a keyword/BM25 pass (Lesson 5's hybrid
  retrieval) would catch this reliably where semantic similarity doesn't.
- Descriptive phrasing ("card art and visual representation") retrieved the
  right document but ranked the introductory chunk above the chunk that
  actually names the `artUri` field — right document, imperfect chunk-level
  ranking.
- **Practical implication:** since similarity score alone can't separate
  relevant from irrelevant here, the answer-generation layer (HW4) needs an
  explicit LLM-side fallback rule ("say you don't have enough information")
  rather than a retrieval-side score threshold — which is exactly what
  `scripts/rag_answer.py` implements and what Examples 3/4 in
  `outputs/rag_answers_examples.md` demonstrate.