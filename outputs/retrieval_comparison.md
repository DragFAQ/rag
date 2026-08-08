# Baseline vs Improved Retrieval

## Setup

- Embedding model: `sentence-transformers/all-MiniLM-L6-v2`
- Index: FAISS `IndexFlatIP` over 100 L2-normalized chunk vectors
- Candidates retrieved from FAISS: 10
- Final results kept: 3
- Hybrid score: `0.7 * semantic + 0.3 * keyword_overlap` (raw scores, no normalization)
- Metadata filter: applied in Python after FAISS, on the `topic` field

The same 8 queries from `outputs/retrieval_examples.md` (HW2) are reused
unchanged, so baseline numbers here match that file exactly.

### Why the filter uses `topic`

The obvious fields to filter on are all constant in this corpus, so a filter
on any of them matches all 100 chunks and excludes nothing:

| Field | Distinct values | Usable as a filter? |
|---|---|---|
| `document_type` | 1 (`api_documentation`) | no |
| `domain` | 1 (`payments`) | no |
| `language` | 1 (`en`) | no |
| `source_type` | 1 (`markdown`) | no |
| `topic` | 5 (added for HW3) | yes |

`topic` was added to the frontmatter of each raw document and propagated
through `prepare_knowledge_base.py` into every chunk:

| Topic | Chunks | Share of corpus |
|---|---|---|
| `token_creation` | 33 | 33% |
| `token_management` | 28 | 28% |
| `payments` | 22 | 22% |
| `entity_registration` | 10 | 10% |
| `token_display` | 7 | 7% |

## 1. Baseline diagnostics

What the baseline returns before any changes, and what kind of failure it is.

| Query | Expected document | Retrieved top-1 document | Score | Issue |
|---|---|---|---|---|
| What is a serviceId and how is it created? | mastercard_register_entities | mastercard_register_entities | 0.4845 | right document, top-1 chunk does not carry the answer |
| How do I get a unique identifier from Mastercard for my program? | mastercard_register_entities | mastercard_register_entities | 0.5984 | OK |
| What HTTP status code indicates successful token provisioning? | mastercard_tokenization-of-existing-card, mastercard_tokenization-while-adding-card, mastercard_tokenization-while-transacting | mastercard_tokenization-while-transacting | 0.6292 | OK |
| What must an acquirer support to process DSRP token transactions? | mastercard_making-payments | mastercard_making-payments | 0.6848 | OK |
| Tell me about card art and visual representation of stored cards | mastercard_displaying-tokenized-pan-details | mastercard_displaying-tokenized-pan-details | 0.5222 | OK |
| What does the DE104 field contain? | mastercard_making-payments | mastercard_making-payments | 0.3073 | OK |
| What is Mastercard's current stock price? | *(none, out of domain)* | mastercard_displaying-tokenized-pan-details | 0.4214 | out of domain, no source can answer this |
| How do I reset a cardholder's online banking password? | *(none, out of domain)* | mastercard_tokenization-of-existing-card | 0.4849 | out of domain, no source can answer this |

## 2. How much the metadata filter narrows the search

| Query | Filter | Corpus chunks kept | Off-topic chunks in top-10 candidates |
|---|---|---|---|
| What is a serviceId and how is it created? | `{'topic': 'entity_registration'}` | 10 / 100 | 2 |
| How do I get a unique identifier from Mastercard for my program? | `{'topic': 'entity_registration'}` | 10 / 100 | 7 |
| What HTTP status code indicates successful token provisioning? | `{'topic': 'token_creation'}` | 33 / 100 | 0 |
| What must an acquirer support to process DSRP token transactions? | `{'topic': 'payments'}` | 22 / 100 | 4 |
| Tell me about card art and visual representation of stored cards | `{'topic': 'token_display'}` | 7 / 100 | 5 |
| What does the DE104 field contain? | `{'topic': 'payments'}` | 22 / 100 | 1 |
| What is Mastercard's current stock price? | *(none)* | 100 / 100 | 0 |
| How do I reset a cardholder's online banking password? | *(none)* | 100 / 100 | 0 |

## 3. Baseline vs improved (top-1)

| Query | Baseline top-1 | Improved top-1 | What changed |
|---|---|---|---|
| What is a serviceId and how is it created? | mastercard_register_entities_chunk_006 | mastercard_register_entities_chunk_006 | no change |
| How do I get a unique identifier from Mastercard for my program? | mastercard_register_entities_chunk_004 | mastercard_register_entities_chunk_004 | top-1 unchanged; filter removed off-topic chunks lower in top-3 (mastercard_displaying-tokenized-pan-details) |
| What HTTP status code indicates successful token provisioning? | mastercard_tokenization-while-transacting_chunk_012 | mastercard_tokenization-while-transacting_chunk_013 | new top-1 via hybrid scoring |
| What must an acquirer support to process DSRP token transactions? | mastercard_making-payments_chunk_010 | mastercard_making-payments_chunk_010 | no change |
| Tell me about card art and visual representation of stored cards | mastercard_displaying-tokenized-pan-details_chunk_001 | mastercard_displaying-tokenized-pan-details_chunk_001 | no change |
| What does the DE104 field contain? | mastercard_making-payments_chunk_009 | mastercard_making-payments_chunk_009 | no change |
| What is Mastercard's current stock price? | mastercard_displaying-tokenized-pan-details_chunk_003 | mastercard_displaying-tokenized-pan-details_chunk_004 | new top-1 via hybrid scoring |
| How do I reset a cardholder's online banking password? | mastercard_tokenization-of-existing-card_chunk_005 | mastercard_tokenization-while-adding-card_chunk_002 | new top-1 via hybrid scoring |

## 4. Ablation: which technique did the work

Each improvement also runs alone, otherwise there is no way to tell which one
caused a change. Top-1 chunk per configuration:

| Query | baseline | filter only | hybrid only | filter + hybrid |
|---|---|---|---|---|
| What is a serviceId and how is it created? | mastercard_register_entities_chunk_006 | mastercard_register_entities_chunk_006 | mastercard_register_entities_chunk_006 | mastercard_register_entities_chunk_006 |
| How do I get a unique identifier from Mastercard for my program? | mastercard_register_entities_chunk_004 | mastercard_register_entities_chunk_004 | mastercard_register_entities_chunk_004 | mastercard_register_entities_chunk_004 |
| What HTTP status code indicates successful token provisioning? | mastercard_tokenization-while-transacting_chunk_012 | mastercard_tokenization-while-transacting_chunk_012 | mastercard_tokenization-while-transacting_chunk_013 | mastercard_tokenization-while-transacting_chunk_013 |
| What must an acquirer support to process DSRP token transactions? | mastercard_making-payments_chunk_010 | mastercard_making-payments_chunk_010 | mastercard_making-payments_chunk_010 | mastercard_making-payments_chunk_010 |
| Tell me about card art and visual representation of stored cards | mastercard_displaying-tokenized-pan-details_chunk_001 | mastercard_displaying-tokenized-pan-details_chunk_001 | mastercard_displaying-tokenized-pan-details_chunk_001 | mastercard_displaying-tokenized-pan-details_chunk_001 |
| What does the DE104 field contain? | mastercard_making-payments_chunk_009 | mastercard_making-payments_chunk_009 | mastercard_making-payments_chunk_009 | mastercard_making-payments_chunk_009 |
| What is Mastercard's current stock price? | mastercard_displaying-tokenized-pan-details_chunk_003 | mastercard_displaying-tokenized-pan-details_chunk_003 | mastercard_displaying-tokenized-pan-details_chunk_004 | mastercard_displaying-tokenized-pan-details_chunk_004 |
| How do I reset a cardholder's online banking password? | mastercard_tokenization-of-existing-card_chunk_005 | mastercard_tokenization-of-existing-card_chunk_005 | mastercard_tokenization-while-adding-card_chunk_002 | mastercard_tokenization-while-adding-card_chunk_002 |

Scored over the 6 in-domain queries:

| Configuration | Correct top-1 document | Answer-bearing top-1 chunk | Answer chunk anywhere in top-3 | Answer chunks in top-3 | Off-topic chunks in top-3 |
|---|---|---|---|---|---|
| baseline | 6 / 6 | 5 / 6 | 6 / 6 | 11 | 1 |
| filter only | 6 / 6 | 5 / 6 | 6 / 6 | 11 | 0 |
| hybrid only | 6 / 6 | 5 / 6 | 6 / 6 | 13 | 1 |
| filter + hybrid | 6 / 6 | 5 / 6 | 6 / 6 | 13 | 0 |

The first three columns are identical across all four configurations. The last
two are where the improvements show up: `answer chunks in top-3` counts how much
of the returned context carries the answer, and `off-topic chunks in top-3`
counts context from a document that cannot answer the query at all.

## 5. When hybrid scoring can overturn the semantic ranking

With weights 0.7 and 0.3, a challenger overtakes the leader only when
`0.3 * keyword_gap > 0.7 * semantic_gap`, so its keyword advantage has to be
2.33x the semantic deficit before anything moves. Each row compares the baseline
top-1 against the candidate that challenges it: the hybrid winner where the
ranking changed, otherwise the closest semantic runner-up.

| Query | Challenger | Semantic gap | Keyword gap needed | Keyword gap available | Top-1 changes? |
|---|---|---|---|---|---|
| What is a serviceId and how is it created? | `register_entities_chunk_004` (rank 2) | +0.0186 | +0.0433 | +0.0000 | no |
| How do I get a unique identifier from Mastercard for my program? | `displaying-tokenized-pan-details_chunk_002` (rank 2) | +0.0363 | +0.0847 | -0.2500 | no |
| What HTTP status code indicates successful token provisioning? | `tokenization-while-transacting_chunk_013` (rank 3) | +0.0711 | +0.1658 | +0.2500 | yes |
| What must an acquirer support to process DSRP token transactions? | `making-payments_chunk_009` (rank 2) | +0.0883 | +0.2061 | -0.1000 | no |
| Tell me about card art and visual representation of stored cards | `displaying-tokenized-pan-details_chunk_004` (rank 2) | +0.0225 | +0.0524 | -0.3636 | no |
| What does the DE104 field contain? | `making-payments_chunk_017` (rank 2) | +0.0377 | +0.0879 | -0.5000 | no |
| What is Mastercard's current stock price? | `displaying-tokenized-pan-details_chunk_004` (rank 2) | +0.0237 | +0.0552 | +0.1429 | yes |
| How do I reset a cardholder's online banking password? | `tokenization-while-adding-card_chunk_002` (rank 5) | +0.0255 | +0.0594 | +0.4000 | yes |

There are two reasons a query does not move: either the keyword gap is too
small, or it is exactly zero because both candidates match the same share of
query terms. Query 1 is the clearest tie case. Its top three chunks all score
0.6250, because the one distinguishing term (`serviceid`) appears in all three
and the rest of the matches are stopwords (`a`, `and`, `is`). Unweighted overlap
cannot separate candidates that all mention the key term.

## 6. Per-query detail

### What is a serviceId and how is it created?

**baseline**

1. `mastercard_register_entities_chunk_006` | score 0.4845  
    | **On-Behalf-Of Sub-Merchant** | Payment Facilitator | Payment Facilitator | Sponsored Merchant | Each group of sponsored merchants | **Not...
2. `mastercard_register_entities_chunk_004` | score 0.4660 **(answer)**  
    - If no, consider registering entities separately under different program names. ## ServiceId Creation --- Using the `programName`, Masterca...
3. `mastercard_register_entities_chunk_010` | score 0.4601  
    Retrieve the `serviceId` for that entity by making a **GET** request to the Merchant Registration API using the `batchId` returned in the pr...

**filter + hybrid**

1. `mastercard_register_entities_chunk_006` | hybrid 0.5267 (semantic 0.4845, keyword 0.6250)  
    | **On-Behalf-Of Sub-Merchant** | Payment Facilitator | Payment Facilitator | Sponsored Merchant | Each group of sponsored merchants | **Not...
2. `mastercard_register_entities_chunk_004` | hybrid 0.5137 (semantic 0.4660, keyword 0.6250) **(answer)**  
    - If no, consider registering entities separately under different program names. ## ServiceId Creation --- Using the `programName`, Masterca...
3. `mastercard_register_entities_chunk_003` | hybrid 0.4605 (semantic 0.3900, keyword 0.6250) **(answer)**  
    If a parent brand owns multiple entities (that is, websites/applications/products), consider the cardholder's experience while storing their...

### How do I get a unique identifier from Mastercard for my program?

**baseline**

1. `mastercard_register_entities_chunk_004` | score 0.5984 **(answer)**  
    - If no, consider registering entities separately under different program names. ## ServiceId Creation --- Using the `programName`, Masterca...
2. `mastercard_displaying-tokenized-pan-details_chunk_002` | score 0.5621  
    - Creating a screen for cardholders to manage cards associated with their profile. - Providing an option for cardholders to select between c...
3. `mastercard_register_entities_chunk_001` | score 0.5530  
    # Register Entities to Create Tokens Before registering your entities, visit [Mastercard Connect](https://www.mastercardconnect.com/-/sign-i...

**filter + hybrid**

1. `mastercard_register_entities_chunk_004` | hybrid 0.5939 (semantic 0.5984, keyword 0.5833) **(answer)**  
    - If no, consider registering entities separately under different program names. ## ServiceId Creation --- Using the `programName`, Masterca...
2. `mastercard_register_entities_chunk_001` | hybrid 0.5121 (semantic 0.5530, keyword 0.4167)  
    # Register Entities to Create Tokens Before registering your entities, visit [Mastercard Connect](https://www.mastercardconnect.com/-/sign-i...
3. `mastercard_register_entities_chunk_002` | hybrid 0.4226 (semantic 0.5323, keyword 0.1667)  
    Each consumer-facing entity must be registered with Secure Card on File by providing the entity name in the `programName` field. ## Program ...

### What HTTP status code indicates successful token provisioning?

**baseline**

1. `mastercard_tokenization-while-transacting_chunk_012` | score 0.6292 **(answer)**  
    ## Understanding Tokenization Results --- **Successful Provisioning** | Result | Response and Details | Action for Integrator | |---|---|---...
2. `mastercard_tokenization-while-adding-card_chunk_008` | score 0.6292 **(answer)**  
    ## Understanding Tokenization Results --- **Successful Provisioning** | Result | Response and Details | Action for Integrator | |---|---|---...
3. `mastercard_tokenization-while-transacting_chunk_013` | score 0.5582 **(answer)**  
    | Result | Response and Details | Action for Integrator | |---|---|---| | 200 | Successful | No additional action is needed. | | 200 with Su...

**filter + hybrid**

1. `mastercard_tokenization-while-transacting_chunk_013` | hybrid 0.5407 (semantic 0.5582, keyword 0.5000) **(answer)**  
    | Result | Response and Details | Action for Integrator | |---|---|---| | 200 | Successful | No additional action is needed. | | 200 with Su...
2. `mastercard_tokenization-while-adding-card_chunk_009` | hybrid 0.5407 (semantic 0.5582, keyword 0.5000) **(answer)**  
    | Result | Response and Details | Action for Integrator | |---|---|---| | 200 | Successful | No additional action is needed. | | 200 with Su...
3. `mastercard_tokenization-of-existing-card_chunk_007` | hybrid 0.5407 (semantic 0.5582, keyword 0.5000) **(answer)**  
    | Result | Response and Details | Action for Integrator | |---|---|---| | 200 | Successful | No additional action is needed. | | 200 with Su...

### What must an acquirer support to process DSRP token transactions?

**baseline**

1. `mastercard_making-payments_chunk_010` | score 0.6848 **(answer)**  
    - The acquirer that will process these transactions must accept DSRP card-on-file tokens and e-commerce Security Level Indicator (SLI) value...
2. `mastercard_making-payments_chunk_009` | score 0.5965 **(answer)**  
    **Warning**: - The acquirer that will process these transactions must accept DSRP card-on-file tokens and e-commerce Security Level Indicato...
3. `mastercard_making-payments_chunk_021` | score 0.5617  
    Consumers may also store their cards and allow the business to make payments (merchant-initiated transaction) on their behalf. For instance,...

**filter + hybrid**

1. `mastercard_making-payments_chunk_010` | hybrid 0.7194 (semantic 0.6848, keyword 0.8000) **(answer)**  
    - The acquirer that will process these transactions must accept DSRP card-on-file tokens and e-commerce Security Level Indicator (SLI) value...
2. `mastercard_making-payments_chunk_009` | hybrid 0.6275 (semantic 0.5965, keyword 0.7000) **(answer)**  
    **Warning**: - The acquirer that will process these transactions must accept DSRP card-on-file tokens and e-commerce Security Level Indicato...
3. `mastercard_making-payments_chunk_008` | hybrid 0.5412 (semantic 0.5161, keyword 0.6000)  
    3. Submit the token (instead of the PAN), cryptogram and token expiry date (returned in the checkout response) to your acquirer or payment p...

### Tell me about card art and visual representation of stored cards

**baseline**

1. `mastercard_displaying-tokenized-pan-details_chunk_001` | score 0.5222 **(answer)**  
    # Display Tokenized PAN Details Cardholders may view, use, or manage their cards during the profile management or checkout experience. Integ...
2. `mastercard_displaying-tokenized-pan-details_chunk_004` | score 0.4997 **(answer)**  
    - If you decide to display card art, utilize the `artUri` found in the [maskedCard.digitalCardData](https://developer.mastercard.com/masterc...
3. `mastercard_displaying-tokenized-pan-details_chunk_003` | score 0.4711 **(answer)**  
    - If you maintain a local version of the token (`srcDigitalCardId`), keep it updated using the GET Card API and by listening to the [Card No...

**filter + hybrid**

1. `mastercard_displaying-tokenized-pan-details_chunk_001` | hybrid 0.5564 (semantic 0.5222, keyword 0.6364) **(answer)**  
    # Display Tokenized PAN Details Cardholders may view, use, or manage their cards during the profile management or checkout experience. Integ...
2. `mastercard_displaying-tokenized-pan-details_chunk_003` | hybrid 0.4389 (semantic 0.4711, keyword 0.3636) **(answer)**  
    - If you maintain a local version of the token (`srcDigitalCardId`), keep it updated using the GET Card API and by listening to the [Card No...
3. `mastercard_displaying-tokenized-pan-details_chunk_004` | hybrid 0.4316 (semantic 0.4997, keyword 0.2727) **(answer)**  
    - If you decide to display card art, utilize the `artUri` found in the [maskedCard.digitalCardData](https://developer.mastercard.com/masterc...

### What does the DE104 field contain?

**baseline**

1. `mastercard_making-payments_chunk_009` | score 0.3073 **(answer)**  
    **Warning**: - The acquirer that will process these transactions must accept DSRP card-on-file tokens and e-commerce Security Level Indicato...
2. `mastercard_making-payments_chunk_017` | score 0.2697  
    - `dpaData.dpaURI` or `dpaData.dpaData` or `dpaData.PresentationName` - `dpaData.dpaName` - `dpaTransactionOptions.transactionAmount.transac...
3. `mastercard_making-payments_chunk_016` | score 0.2580  
    **Digital Transaction Insights (DTI) fraud risk score** Integrators can generate and include a [Mastercard Identity Check](https://developer...

**filter + hybrid**

1. `mastercard_making-payments_chunk_009` | hybrid 0.3651 (semantic 0.3073, keyword 0.5000) **(answer)**  
    **Warning**: - The acquirer that will process these transactions must accept DSRP card-on-file tokens and e-commerce Security Level Indicato...
2. `mastercard_making-payments_chunk_010` | hybrid 0.3059 (semantic 0.2227, keyword 0.5000) **(answer)**  
    - The acquirer that will process these transactions must accept DSRP card-on-file tokens and e-commerce Security Level Indicator (SLI) value...
3. `mastercard_making-payments_chunk_016` | hybrid 0.2306 (semantic 0.2580, keyword 0.1667)  
    **Digital Transaction Insights (DTI) fraud risk score** Integrators can generate and include a [Mastercard Identity Check](https://developer...

### What is Mastercard's current stock price?

**baseline**

1. `mastercard_displaying-tokenized-pan-details_chunk_003` | score 0.4214  
    - If you maintain a local version of the token (`srcDigitalCardId`), keep it updated using the GET Card API and by listening to the [Card No...
2. `mastercard_displaying-tokenized-pan-details_chunk_004` | score 0.3977  
    - If you decide to display card art, utilize the `artUri` found in the [maskedCard.digitalCardData](https://developer.mastercard.com/masterc...
3. `mastercard_displaying-tokenized-pan-details_chunk_001` | score 0.3921  
    # Display Tokenized PAN Details Cardholders may view, use, or manage their cards during the profile management or checkout experience. Integ...

**filter + hybrid**

1. `mastercard_displaying-tokenized-pan-details_chunk_004` | hybrid 0.3641 (semantic 0.3977, keyword 0.2857)  
    - If you decide to display card art, utilize the `artUri` found in the [maskedCard.digitalCardData](https://developer.mastercard.com/masterc...
2. `mastercard_displaying-tokenized-pan-details_chunk_001` | hybrid 0.3602 (semantic 0.3921, keyword 0.2857)  
    # Display Tokenized PAN Details Cardholders may view, use, or manage their cards during the profile management or checkout experience. Integ...
3. `mastercard_tokenization-while-adding-card_chunk_002` | hybrid 0.3543 (semantic 0.3837, keyword 0.2857)  
    Detailed steps are explained below: **Integrator initiates tokenization request** 1. Cardholder enters new card details and saves credential...

### How do I reset a cardholder's online banking password?

**baseline**

1. `mastercard_tokenization-of-existing-card_chunk_005` | score 0.4849  
    **Tip**: To maximize tokenization performance: - Ensure PAN is still active by calling [Mastercard ABU account inquiry](https://developer.ma...
2. `mastercard_managing_tokens_chunk_008` | score 0.4845  
    | **ACTIVE** | Token has been unsuspended and is active to use for transactions. | Show Card with `panLastFour` on the UI. Update the stored...
3. `mastercard_managing_tokens_chunk_011` | score 0.4828  
    Use the decrypted DPAN and expiry values to refresh the corresponding [maskedCard](https://developer.mastercard.com/mastercard-checkout-solu...

**filter + hybrid**

1. `mastercard_tokenization-while-adding-card_chunk_002` | hybrid 0.4416 (semantic 0.4594, keyword 0.4000)  
    Detailed steps are explained below: **Integrator initiates tokenization request** 1. Cardholder enters new card details and saves credential...
2. `mastercard_making-payments_chunk_001` | hybrid 0.4090 (semantic 0.4557, keyword 0.3000)  
    # Make Payments Once cardholders store their cards and the Integrator [tokenizes their PAN details](https://developer.mastercard.com/masterc...
3. `mastercard_managing_tokens_chunk_008` | hybrid 0.3991 (semantic 0.4845, keyword 0.2000)  
    | **ACTIVE** | Token has been unsuspended and is active to use for transactions. | Show Card with `panLastFour` on the UI. Update the stored...

## 7. Supplementary: cross-topic stress queries

Each of the 8 queries above targets a single document, so the baseline almost
never crosses topics there and the filter has little to remove. This set is
worded to pull toward a topic that does not hold the answer.

**How the set was assembled.** Of the 40 candidate queries run against the baseline,
7 put the wrong topic at top-1. One of those was
dropped because its answer exists in two topics, so the ground truth would be
arbitrary. The remaining 6 failures are kept, plus the 5 queries the baseline already handled correctly.
Failures are over-represented below on purpose. The unfiltered baseline failure
rate was 7/40 (18%), not 6/11.

| Query | Answer topic | Baseline top-1 topic | Baseline top-1 | Improved top-1 | Fixed? |
|---|---|---|---|---|---|
| How do I make sure a card is active before tokenizing it? | `token_creation` | `token_management` **wrong** | `managing_tokens_chunk_008` | `tokenization-of-existing-card_chunk_005` | yes |
| What does the integrator do after receiving a card notification? | `token_management` | `token_creation` **wrong** | `tokenization-of-existing-card_chunk_003` | `managing_tokens_chunk_004` | yes |
| How do I get the new expiry date after the issuer updates a card? | `token_management` | `token_display` **wrong** | `displaying-tokenized-pan-details_chunk_003` | `managing_tokens_chunk_011` | yes |
| What does the Integrator receive when a token changes state? | `token_management` | `token_creation` **wrong** | `tokenization-of-existing-card_chunk_003` | `managing_tokens_chunk_017` | yes |
| What should I do if provisioning needs cardholder authentication? | `token_creation` | `entity_registration` **wrong** | `register_entities_chunk_001` | `tokenization-while-transacting_chunk_013` | yes |
| Where do I find the wallet or DPA identifier for a payment? | `payments` | `token_creation` **wrong** | `tokenization-while-transacting_chunk_010` | `making-payments_chunk_002` | yes |
| Which entity types can a Payment Facilitator sponsor for transactions? | `entity_registration` | `entity_registration` | `register_entities_chunk_006` | `register_entities_chunk_006` | n/a |
| Which field gives me the artwork URL for a saved card? | `token_display` | `token_display` | `displaying-tokenized-pan-details_chunk_004` | `displaying-tokenized-pan-details_chunk_004` | n/a |
| What SLI value is needed for partial shipment payments? | `payments` | `payments` | `making-payments_chunk_022` | `making-payments_chunk_021` | n/a |
| How do I handle a 200 response that still requires additional steps? | `token_creation` | `token_creation` | `tokenization-while-transacting_chunk_012` | `tokenization-while-transacting_chunk_013` | n/a |
| How do I remove a card the cardholder no longer wants? | `token_management` | `token_management` | `managing_tokens_chunk_022` | `managing_tokens_chunk_022` | n/a |

Over these 11 queries:

| Metric | baseline | filter + hybrid |
|---|---|---|
| Correct topic at top-1 | 5 / 11 | 11 / 11 |
| Answer chunk in top-3 | 8 / 11 | 10 / 11 |

The margins matter here. The off-topic chunk wins by a very small amount, so no
score cutoff could separate the two. Only a hard metadata constraint can.

| Query | Off-topic top-1 (baseline) | Score | On-topic top-1 (filtered) | Score | Margin |
|---|---|---|---|---|---|
| How do I make sure a card is active before tokenizing it? | `managing_tokens_chunk_008` | 0.6317 | `tokenization-of-existing-card_chunk_005` | 0.6274 | +0.0043 |
| What does the integrator do after receiving a card notification? | `tokenization-of-existing-card_chunk_003` | 0.6826 | `managing_tokens_chunk_004` | 0.6781 | +0.0045 |
| How do I get the new expiry date after the issuer updates a card? | `displaying-tokenized-pan-details_chunk_003` | 0.5103 | `managing_tokens_chunk_019` | 0.5097 | +0.0006 |
| What does the Integrator receive when a token changes state? | `tokenization-of-existing-card_chunk_003` | 0.5970 | `managing_tokens_chunk_017` | 0.5817 | +0.0153 |
| What should I do if provisioning needs cardholder authentication? | `register_entities_chunk_001` | 0.6551 | `tokenization-while-adding-card_chunk_002` | 0.6256 | +0.0294 |
| Where do I find the wallet or DPA identifier for a payment? | `tokenization-while-transacting_chunk_010` | 0.4999 | `making-payments_chunk_022` | 0.4755 | +0.0244 |

One case shows the limit of filtering. *Where do I find the wallet or DPA
identifier for a payment?* gets the correct topic, but the chunks naming
`dpaData.dpaURI` still do not reach the top 3. The filter controls which document
is searched, not how chunks are ordered inside it. That needs a reranker.

## 8. Risk: a filter that is too aggressive

Query: *What HTTP status code indicates successful token provisioning?*

The answer is in the `token_creation` documents. A wrong topic guess does not
just reorder the results, it removes the answer from the candidate set, and
nothing after retrieval can recover it.

| Filter | Top-1 | Answer in top-3? |
|---|---|---|
| `{'topic': 'token_creation'}` | mastercard_tokenization-while-transacting_chunk_012 | yes |
| `{'topic': 'token_management'}` | *(no results)* | no |

## 9. Cost

Wall-clock time for all 8 queries, model and index already
loaded, averaged over 5 repeats:

| Configuration | Total | Per query |
|---|---|---|
| baseline | 65 ms | 8.2 ms |
| filter only | 56 ms | 6.9 ms |
| hybrid only | 57 ms | 7.2 ms |
| filter + hybrid | 56 ms | 7.0 ms |

## Conclusion

### Metadata filtering gave the bigger effect

It was the only change that improved a metric without ever making a result worse:

- search space per query: 100 chunks down to 7-33 (67-93% smaller)
- off-topic chunks in top-3: 1 -> 0
- of the 10 candidates FAISS returned, up to 7 were off-topic and got dropped

Query 2 is the clearest win. The baseline put
`displaying-tokenized-pan-details_chunk_002` at rank 2 for a question about
program identifiers, and the filter replaced it with a `register_entities` chunk.

### Both improvements had little room on the HW2 queries

The baseline already picked the correct document as top-1 for all 6 in-domain
queries, so there was no document-level recall to recover. What was left to
improve is the make-up of the top-3.

The 8 queries also each target a single document, so the baseline rarely crosses
topics on them and the filter has little to remove. That limits the measured gain
regardless of how good the filter is.

The cross-topic set in section 7 shows what happens when topics do collide. On 11
queries worded to pull toward the wrong topic:

- correct topic at top-1: **5/11 -> 11/11**
- answer chunk in top-3: **8/11 -> 10/11**
- all 6 baseline failures fixed

The margins are the interesting part. The off-topic chunk beat the on-topic one by
between 0.0006 and 0.0294. For *"How do I get the new expiry date after the issuer
updates a card?"* the wrong chunk won by 0.0006. No score cutoff can separate
values that close, so a hard metadata constraint is the only thing that fixes it.
This matches the HW2 finding that similarity score is not a usable relevance
signal on this corpus.

Worth noting that this set over-represents failures on purpose. Of the 40 queries
probed, only 7 (18%) put the wrong topic first, so filtering protects against an
uncommon but silent failure rather than giving a broad accuracy lift.

### Hybrid scoring was close to neutral

It changed top-1 on 3 of 8 queries. Only one of those (query 3) was in-domain, and
there both the old and new top-1 carry the answer, so correctness did not change.
The other two were the out-of-domain queries, where one irrelevant chunk replaced
another. The one real gain is answer chunks in top-3 going from 11 to 13.

Two reasons it underdelivered:

1. **The 2.33x threshold.** With weights 0.7 and 0.3, a challenger has to beat the
   leader on keyword score by 2.33x its semantic deficit. In 4 of the 6 in-domain
   queries the keyword gap was negative, meaning the baseline top-1 already had
   the better keyword score, so hybrid just reinforced the existing order.
2. **Unweighted overlap cannot discriminate.** Query 1's top three chunks all
   score 0.6250. The one distinguishing term (`serviceid`) appears in all three,
   so the score comes from stopwords (`a`, `and`, `is`). Adding the same constant
   to every candidate cannot reorder anything.

So the keyword signal either agreed with semantic search or was too flat to
matter. The problem is not lexical matching itself but unweighted lexical
matching, since `DE104` and `serviceId` count the same as `is`.

### What is still broken

Query 1 is still wrong at chunk level. Top-1 is `register_entities_chunk_006`, a
table of entity types, while the answer is in `chunk_004` at rank 2. Filtering
cannot help because both chunks share a topic, and overlap cannot help because
they tie exactly. This needs IDF weighting or a reranker.

Queries 7 and 8 have no topic, so no filter applies, and `IndexFlatIP` returns k
neighbours regardless of similarity. As in HW2, the fallback belongs in the answer
layer, where `scripts/rag_answer.py` already refuses to answer without enough
context, not in a retrieval-side score threshold.

### Risk observed

Filtering a token-provisioning question to `topic=token_management` returns zero
results. Post-filtering has no fallback, so the answer leaves the candidate set
and nothing after retrieval can recover it. The filter values here are declared
per query by hand; in production they would have to come from a query router, and
a wrong route is worse than no filter at all.

### Cost

All four configurations run at 6-8 ms per query, with the differences inside
measurement noise and the query embedding dominating. Filtering is one metadata
comparison per candidate. Hybrid scoring tokenizes candidate text, so its cost
scales with chunk size and candidate count, not corpus size.

### Next steps

1. Replace overlap with IDF weighting (BM25), which targets the tie blocking
   query 1 and the score dilution found in HW2.
2. Add a reranker for chunk ordering inside the correct document, where the
   remaining error is.
3. Derive the filter value from the query instead of declaring it per test case,
   and measure how often the router gets it wrong.
