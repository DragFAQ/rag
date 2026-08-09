# Tool Examples — `get_token_status`

Tool: `get_token_status`
Type: read tool
Purpose: returns the current status (ACTIVE / SUSPENDED / DELETED), masked PAN,
expiry, and last-updated date of a specific Card-on-File token from a mock
token-vault API (`scripts/external_tool.py`).
When to call: the user asks about the current state of a specific token
reference (format `TKN-XXXXXX`).
When NOT to call: the user asks how tokenization, registration, or payments
work conceptually — that's static documentation, answered by retrieval.

Orchestration: `scripts/agent_with_tool.py` — retrieves top-k chunks for
context, offers the model the tool via OpenAI function calling, validates and
executes any tool call in `execute_tool_call()` / `get_token_status()`
(never runs the model's arguments directly), feeds the result back, and asks
for a final grounded answer. See `PROMPT_TEMPLATE.md` conventions for the
retrieval+prompt half of this pipeline.

---

## Example 1 — valid token, active

```
User question: What is the status of token TKN-100234?

Tool called: get_token_status
Input: {"token_reference": "TKN-100234"}
Result: {"token_reference": "TKN-100234", "status": "ACTIVE", "masked_pan": "**** **** **** 4421", "expiry": "2027-09", "last_updated": "2026-07-15"}

Final answer:
The status of token TKN-100234 is ACTIVE. The masked PAN associated with this
token ends in 4421, and the token expires in September 2027. The token was
last updated in July 2026.

Why tool is better than retrieval:
Token status is live, per-token state that changes over time (ACTIVE ->
SUSPENDED -> DELETED). It is not documented anywhere in the static knowledge
base — no amount of retrieval over the Markdown docs could answer "what is
token TKN-100234's status right now." A tool querying the token vault is the
only correct approach.
```

## Example 2 — valid format, token not found

```
User question: Is token TKN-999999 still active?

Tool called: get_token_status
Input: {"token_reference": "TKN-999999"}
Result: {"error": "Token TKN-999999 not found"}

Final answer:
I do not have enough information in the provided documentation to answer this
question. The live status check for token TKN-999999 returned that the token
was not found.

Why tool is better than retrieval:
Same reasoning as example 1 — this is a live lookup, not a documentation
question. The tool also demonstrates graceful validation: a not-found
token returns a structured error instead of crashing or letting the model
invent a plausible-sounding status.
```

## Example 3 — invalid format, rejected before lookup

```
User question: What about token abc123, is it valid?

Tool called: get_token_status
Input: {"token_reference": "TKN-abc123"}
Result: {"error": "Invalid token_reference format: 'TKN-abc123'. Expected: TKN-XXXXXX (6+ digits)"}

Final answer:
The token reference you provided "abc123" does not match the required format
"TKN-XXXXXX" (with 6 or more digits). Please provide the token reference in
the correct format so I can check its status.

Why tool is better than retrieval:
This case is really about validation, not retrieval: the model proposed a
malformed token_reference, and the tool's format check (regex
`^TKN-\d{6,}$` in `external_tool.py`) rejected it before ever touching the
mock token vault. The model never gets to run an arbitrary lookup — it only
proposes arguments, the backend decides whether they're safe to execute.
```

## Example 4 — conceptual question, no tool call (contrast case)

```
User question: How is a serviceId created and what is it used for?

Tool called: (none)
Input: (none)
Result: (none — answered from retrieved documentation context only)

Final answer:
A serviceId is a unique identifier created by Mastercard for an entity based
on the provided programName. Mastercard generates the serviceId during
onboarding; the Integrator then uses this serviceId to create tokens for that
entity. It can also be used to group Sponsored Merchants under a Payment
Facilitator, with up to 5 shared serviceIds per grouping.
(sources: mastercard_register_entities_chunk_004, _chunk_006, _chunk_010, _chunk_003)

Why retrieval is better than the tool here:
This is a "how does the system work" question with a stable, documented
answer — exactly what the static knowledge base is for. Calling
get_token_status would be meaningless (there's no specific token in the
question) and the model correctly chose not to call it, retrieving from
`mastercard_register_entities` chunks instead.
```

## Example 5 — hybrid: tool + retrieval together

```
User question: What's the current status of token TKN-100987, and how do I update its expiry once it's suspended?

Tool called: get_token_status
Input: {"token_reference": "TKN-100987"}
Result: {"token_reference": "TKN-100987", "status": "SUSPENDED", "masked_pan": "**** **** **** 7789", "expiry": "2026-11", "last_updated": "2026-08-01"}

Final answer:
The current status of token TKN-100987 is SUSPENDED — per the documentation,
a suspended token cannot transact, and the UI should show a grayed card
without panLastFour. The documentation does not describe updating expiry
during suspension directly, but a TOKEN_REFRESH notification indicates the
token/expiry may have changed; on receiving one, decrypt the paymentData
object with your payload encryption keys and update the stored token record.
(sources: mastercard_managing_tokens_chunk_006, _chunk_010; token status
checked: TKN-100987)

Why tool is better than retrieval here:
Neither source alone answers the full question. The live status
(SUSPENDED) can only come from the tool; the expiry-update procedure only
exists in the static docs (`managing_tokens` / reason codes). This example
shows the tool and retrieval composing in one orchestration turn rather than
being mutually exclusive.
```
