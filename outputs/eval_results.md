| id | question | expected_behavior | answer | retrieved_chunks | route_or_mode | tools_used | task_success | groundedness | answer_quality | latency_ms | errors | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | How is a serviceId created and what is it used for? | Answer from KB: serviceId comes from Mastercard once an entity registers a programName; used to cre… | A serviceId is created by Mastercard using the programName provided during onboarding. It is a uniq… | mastercard_register_entities_chunk_006, mastercard_register_entities_chunk_004, mastercard_register… | RAG | none | yes | good | good | 5057 | none | Straightforward single-topic question, this is the corpus's best-covered concept |
| 2 | What happens to maskedCard and paymentData when a TOKEN_REFRESH event occurs? | Answer from KB (managing_tokens): TOKEN_REFRESH returns both maskedCard and encrypted paymentData w… | When a TOKEN_REFRESH event occurs, you will receive both the `maskedCard` and the encrypted `paymen… | mastercard_managing_tokens_chunk_012, mastercard_managing_tokens_chunk_014, mastercard_managing_tok… | RAG | none | yes | good | good | 2749 | none | Targets the table row that's split across two chunks by the sentence-fallback splitter (see README … |
| 3 | What is a serviceId and how is it created? | Answer from KB, same content as case 1 but phrased to hit the tied-score retrieval case flagged in … | A serviceId is a unique identifier created by Mastercard for an entity, which is used by the Integr… | mastercard_register_entities_chunk_006, mastercard_register_entities_chunk_004, mastercard_register… | RAG | none | yes | good | good | 5159 | none | Same 4 chunks retrieved as case 1, in the same order - the tied-score issue documented in the READM… |
| 4 | What is the status of token TKN-100234? | Use get_token_status tool, report ACTIVE / masked PAN / expiry / last updated | The status of token TKN-100234 is ACTIVE. The masked PAN associated is **** **** **** 4421, with an… | mastercard_managing_tokens_chunk_016, mastercard_managing_tokens_chunk_015, mastercard_managing_tok… | tool | get_token_status | yes | not_applicable | good | 2772 | none | Known-good token in MOCK_TOKENS, baseline tool case |
| 5 | Is TKN-999999 still active? | Call the tool, tool returns not-found, model reports it can't find that token instead of guessing a… | I do not have enough information in the provided documentation to answer this question. The token r… | mastercard_managing_tokens_chunk_016, mastercard_managing_tokens_chunk_001, mastercard_managing_tok… | tool | get_token_status | yes | not_applicable | good | 2392 | none | Checks whether a tool error gets surfaced honestly or the model fills in a plausible-sounding statu… |
| 6 | What are the PCI-DSS fines for a card data breach? | Say not enough information - topic is entirely outside this KB (tokenization/registration/payments … | I do not have enough information in the provided documentation to answer this question. | mastercard_making-payments_chunk_016, mastercard_making-payments_chunk_009, mastercard_making-payme… | fallback | none | yes | not_applicable | good | 726 | none | Correctly declined. Side finding: the model appends its citation list after the exact fallback sent… |
| 7 | Where do I find the wallet or DPA identifier for a payment? | Answer from KB (making-payments, dpaData.dpaURI), flagged in README as a case where filtering can't… | The wallet or Digital Payment Application (DPA) identifier for a payment can be found in the paymen… | mastercard_tokenization-while-transacting_chunk_010, mastercard_making-payments_chunk_022, masterca… | RAG | none | yes | good | good | 1639 | none | README's version of this failure was measured at final_k=3 through retrieval_improved.py; at top_k=… |
| 8 | Tell me about tokens. | Ambiguous - ideally asks for clarification or gives a narrow, hedged answer instead of picking one … | Tokens in Mastercard Secure Card on File represent a digital substitute for the card's Primary Acco… | mastercard_register_entities_chunk_006, mastercard_managing_tokens_chunk_001, mastercard_tokenizati… | RAG | none | partial | good | good | 3307 | none | Didn't ask for clarification (there's no clarification route in this script, that's agent_flow.py's… |
| 9 | Can I use a token that was tokenized while adding a card for a cardholder-initiated payment later? | Answer requires connecting token_creation and payments topics - two different source documents | Yes, you can use a token that was created while adding a card for a cardholder-initiated payment la… | mastercard_tokenization-while-transacting_chunk_001, mastercard_making-payments_chunk_001, masterca… | RAG | none | yes | good | good | 3250 | none | Retrieved chunks spanned 3 topics (token_creation, payments, token_display) in one top_k=4 call, an… |
| 10 | What is the reason code for a token that was suspended due to a lost device? | Answer from KB (managing_tokens reason codes) or explicit not-enough-info if the specific device-lo… | I do not have enough information in the provided documentation to answer this question. The context… | mastercard_managing_tokens_chunk_006, mastercard_managing_tokens_chunk_009, mastercard_managing_tok… | RAG | none | yes | not_applicable | good | 2194 | none | Correctly declined instead of inventing a reason code - the retrieved managing_tokens chunks cover … |

## Full answers

### Case 1: How is a serviceId created and what is it used for?

**Retrieved chunks:** mastercard_register_entities_chunk_006, mastercard_register_entities_chunk_004, mastercard_register_entities_chunk_010, mastercard_register_entities_chunk_003

**Answer:**

A serviceId is created by Mastercard using the programName provided during onboarding. It is a unique identifier assigned to an entity and used by the Integrator to create tokens for that entity. The serviceId is linked to Mastercard-defined program types and helps differentiate entities, especially when a parent brand owns multiple entities or when grouping sponsored merchants under a Payment Facilitator model.

The serviceId can be retrieved by making a GET request to the Merchant Registration API with a batchId or by receiving Merchant status notifications.

In summary:
- Created by Mastercard from the programName.
- Used as a unique identifier for entities.
- Used by Integrators to create tokens.
- Supports grouping under Payment Facilitators with shared serviceIds.

References: mastercard_register_entities_chunk_003, mastercard_register_entities_chunk_004, mastercard_register_entities_chunk_006, mastercard_register_entities_chunk_010

### Case 2: What happens to maskedCard and paymentData when a TOKEN_REFRESH event occurs?

**Retrieved chunks:** mastercard_managing_tokens_chunk_012, mastercard_managing_tokens_chunk_014, mastercard_managing_tokens_chunk_019, mastercard_managing_tokens_chunk_010

**Answer:**

When a TOKEN_REFRESH event occurs, you will receive both the `maskedCard` and the encrypted `paymentData` (which contains the DPAN and DPAN expiry). You must use your payload encryption keys stored on Mastercard Connect to decrypt the `paymentData` object and update the stored token record with the decrypted DPAN and expiry values. This update includes token number (paymentToken), token expiry (tokenExpirationMonth, tokenExpirationYear), and any other changed parameters. Additionally, you should update the corresponding `maskedCard` object with the new DPAN last four, PAN expiry, token last four, token expiry, and any other updated fields.

References: mastercard_managing_tokens_chunk_012, mastercard_managing_tokens_chunk_019, mastercard_managing_tokens_chunk_010, mastercard_managing_tokens_chunk_014

### Case 3: What is a serviceId and how is it created?

**Retrieved chunks:** mastercard_register_entities_chunk_006, mastercard_register_entities_chunk_004, mastercard_register_entities_chunk_010, mastercard_register_entities_chunk_003

**Answer:**

A serviceId is a unique identifier created by Mastercard for an entity, which is used by the Integrator to create tokens for that entity. It is created based on the programName provided during registration. Program Types, which are business categories assigned during onboarding, influence how the serviceId and srcClientId are assigned.

To obtain a serviceId, you can make a GET request to the Merchant Registration API using the batchId returned in a previous request, or receive Merchant status notifications that contain the serviceId.

In certain cases, such as Payment Facilitators grouping sponsored merchants, each group is assigned its own serviceId, which can be shared under certain conditions.

Sources: mastercard_register_entities_chunk_004, mastercard_register_entities_chunk_010, mastercard_register_entities_chunk_006, mastercard_register_entities_chunk_003

### Case 4: What is the status of token TKN-100234?

**Retrieved chunks:** mastercard_managing_tokens_chunk_016, mastercard_managing_tokens_chunk_015, mastercard_managing_tokens_chunk_013, mastercard_tokenization-while-transacting_chunk_015

**Answer:**

The status of token TKN-100234 is ACTIVE. The masked PAN associated is **** **** **** 4421, with an expiry date of September 2027, and it was last updated in July 2026. (Source: token_reference TKN-100234)

### Case 5: Is TKN-999999 still active?

**Retrieved chunks:** mastercard_managing_tokens_chunk_016, mastercard_managing_tokens_chunk_001, mastercard_managing_tokens_chunk_013, mastercard_managing_tokens_chunk_003

**Answer:**

I do not have enough information in the provided documentation to answer this question. The token reference TKN-999999 was not found in the current system status. (Source: mastercard_managing_tokens_chunk_001)

### Case 6: What are the PCI-DSS fines for a card data breach?

**Retrieved chunks:** mastercard_making-payments_chunk_016, mastercard_making-payments_chunk_009, mastercard_making-payments_chunk_010, mastercard_managing_tokens_chunk_028

**Answer:**

I do not have enough information in the provided documentation to answer this question.

### Case 7: Where do I find the wallet or DPA identifier for a payment?

**Retrieved chunks:** mastercard_tokenization-while-transacting_chunk_010, mastercard_making-payments_chunk_022, mastercard_register_entities_chunk_009, mastercard_making-payments_chunk_017

**Answer:**

The wallet or Digital Payment Application (DPA) identifier for a payment can be found in the payment request data under fields such as `dpaData.dpaURI`, `dpaData.dpaData`, or `dpaData.PresentationName`. Additionally, `dpaData.dpaName` may also provide identifying information about the DPA. 

These fields represent the wallet or DPA identifier involved in the transaction (source chunk ID: mastercard_making-payments_chunk_017).

### Case 8: Tell me about tokens.

**Retrieved chunks:** mastercard_register_entities_chunk_006, mastercard_managing_tokens_chunk_001, mastercard_tokenization-while-transacting_chunk_001, mastercard_managing_tokens_chunk_002

**Answer:**

Tokens in Mastercard Secure Card on File represent a digital substitute for the card's Primary Account Number (PAN). They are generated and managed in various scenarios such as when a cardholder initiates a payment with a card not yet tokenized (creating a token during the transaction) or when card details are updated due to lifecycle events like card expiration, loss, or compromise.

Tokens can be provisioned under serviceIds, which Payment Facilitators use to group sponsored merchants. These tokens may be shared within the group if proper PAN checks are implemented. Up to five shared serviceIds can be created by a Payment Facilitator.

Token lifecycle management includes receiving notifications for status changes such as Cancelled, Suspended, or Active, deleting tokens when cards are removed, and retrieving transaction lists associated with a token.

Issuers can trigger account updates that may result in token updates when PANs are replaced, either within the same account range or across different account ranges, reflecting changes like card replacement. 

This overview spans token creation, lifecycle events, status management, and usage within merchant groupings under Payment Facilitators. (Sources: mastercard_register_entities_chunk_006, mastercard_managing_tokens_chunk_001, mastercard_managing_tokens_chunk_002, mastercard_tokenization-while-transacting_chunk_001)

### Case 9: Can I use a token that was tokenized while adding a card for a cardholder-initiated payment later?

**Retrieved chunks:** mastercard_tokenization-while-transacting_chunk_001, mastercard_making-payments_chunk_001, mastercard_tokenization-while-transacting_chunk_002, mastercard_displaying-tokenized-pan-details_chunk_002

**Answer:**

Yes, you can use a token that was created while adding a card for a cardholder-initiated payment later. Once a token is created for the consumer (by enrolling the PAN during the transaction and associating it with the cardholder's profile), that token should be used for all future transactions done by that consumer. You should not re-tokenize the card for each transaction or checkout.

This is confirmed by the documentation stating to use the stored tokens (instead of PAN) for seamless and secure transactions and that tokens created during card enrollment are associated with the cardholder's profile for future use. (Source chunk IDs: mastercard_tokenization-while-transacting_chunk_001, mastercard_tokenization-while-transacting_chunk_002, mastercard_making-payments_chunk_001)

### Case 10: What is the reason code for a token that was suspended due to a lost device?

**Retrieved chunks:** mastercard_managing_tokens_chunk_006, mastercard_managing_tokens_chunk_009, mastercard_managing_tokens_chunk_007, mastercard_managing_tokens_chunk_001

**Answer:**

I do not have enough information in the provided documentation to answer this question. The context describes token statuses like SUSPENDED and CANCELLED and refers to reason codes that guide integrators on required actions, but it does not provide specific reason codes or their descriptions related to suspension reasons such as a lost device. (source chunks: mastercard_managing_tokens_chunk_006, mastercard_managing_tokens_chunk_009, mastercard_managing_tokens_chunk_007)
