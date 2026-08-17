# Agent Flow Examples (HW6)

5 questions run through `scripts/agent_flow.py`. Routing is plain keyword
matching, no model call - see the script docstring for why. State is shown
after the step runs, trimmed where it's just restating the tool result above
it.

---

Question: How is a serviceId created and what is it used for?
Route: policy_rag
Tool called: search(query="How is a serviceId created and what is it used for?", top_k=3)
Observation: top chunks = [register_entities_chunk_006, register_entities_chunk_004, register_entities_chunk_010]
State after step: { selected_route: policy_rag, tool_calls: [search -> 3 chunk_ids], final_answer: set }
Final answer: "| On-Behalf-Of Sub-Merchant | ... | Up to 5 shared serviceIds ..." (source: mastercard_register_entities_chunk_006)

Not the answer I'd actually want here - rank 1 is a table row about
sub-merchant grouping, not the "ServiceId Creation" section that explains the
concept directly (that one's chunk_004, which shows up at rank 2). Same thing
HW3's retrieval comparison already flagged for this exact query: baseline
semantic search puts a near-tied table chunk ahead of the conceptual one.
Metadata filtering wouldn't help since both chunks share a topic, and
`agent_flow.py` just takes rank 1 without any reranking, so the router
faithfully reproduces the retrieval bug instead of hiding it.

---

Question: What is the status of token TKN-100234?
Route: token_status
Tool called: get_token_status(token_reference="TKN-100234")
Observation: {status: ACTIVE, masked_pan: **** **** **** 4421, expiry: 2027-09, last_updated: 2026-07-15}
State after step: { selected_route: token_status, tool_calls: [get_token_status -> ACTIVE record], final_answer: set }
Final answer: "Token TKN-100234 is ACTIVE (masked PAN **** **** **** 4421, expires 2027-09, last updated 2026-07-15)."

Clean case, this is what the token_status route is for. No LLM needed to
turn a dict into a sentence.

---

Question: Is TKN-999999 still active?
Route: token_status
Tool called: get_token_status(token_reference="TKN-999999")
Observation: {error: "Token TKN-999999 not found"}
State after step: { selected_route: token_status, tool_calls: [get_token_status -> error], final_answer: set }
Final answer: "Couldn't look that up - Token TKN-999999 not found"

The regex still finds `TKN-999999` and routes correctly even though the token
doesn't exist in the mock vault - the router only checks the shape of the
reference, `get_token_status` itself is what checks existence. Failure comes
back as a normal observation, not an exception, so the flow doesn't need a
try/except around the tool call.

---

Question: Tell me something interesting.
Route: clarification
Tool called: list_supported_topics()
Observation: {topics: {token_creation, token_management, payments, entity_registration, token_display}}
State after step: { selected_route: clarification, tool_calls: [list_supported_topics -> 5 topics], final_answer: set }
Final answer: "Not sure what you're asking - I can help with: token_creation, token_management, payments, entity_registration, token_display. If you meant a specific token, give me its reference (TKN-XXXXXX) and I'll check its status."

This is the second mock tool in action. Without it the clarification route
would just be a static "please rephrase" string; with it, the fallback
actually tells the user what's in scope.

---

Question: How do I get a masked PAN displayed to the cardholder?
Route: policy_rag
Tool called: search(query="How do I get a masked PAN displayed to the cardholder?", top_k=3)
Observation: top chunks = [tokenization-while-transacting_chunk_001, displaying-tokenized-pan-details_chunk_001, managing_tokens_chunk_007]
State after step: { selected_route: policy_rag, tool_calls: [search -> 3 chunk_ids], final_answer: set }
Final answer: "Cardholders can initiate payment with a card that is not yet tokenized. In this case, create a token by enrolling a PAN..." (source: mastercard_tokenization-while-transacting_chunk_001)

Another spot where rank 1 isn't the best match - the actual "Display
Tokenized PAN Details" doc is right there at rank 2, but the router doesn't
look past rank 1. A topic filter (`--topic token_display`, from HW3) would
fix this, but `agent_flow.py` doesn't wire that in; it's calling the plain
baseline `search()`. Worth adding if this route goes further.

---

## Takeaway

Routing and state management worked exactly as designed - every question
landed on the route it should, the state dict shows a clean trace of what
ran and why, and the two failure paths (unknown token, off-topic question)
both return a normal observation instead of blowing up. The rough edges are
all downstream, in retrieval quality that HW3 already knows about, not in the
workflow logic itself. Wiring the topic filter or the hybrid score into the
`policy_rag` route would be the obvious next step before this stops being a
homework flow and turns into something closer to what `agent_with_tool.py`
already does with the model in the loop.
