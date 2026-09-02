# LangGraph Workflow Examples (HW7)

3 questions, one per route, run through `scripts/langgraph_flow.py`.

---

Question: How is a serviceId created and what is it used for?
Route: policy_rag
Nodes: classify_request -> run_policy_rag -> build_answer
Tool called: search({'query': 'How is a serviceId created and what is it used for?', 'top_k': 3})
Final answer: | **On-Behalf-Of Sub-Merchant** | Payment Facilitator | Payment Facilitator | Sponsored Merchant | Each group of sponsored merchants |
**Note**: Payment Facilitators can group their sponsored merchants under common attributes and each group is assigned a `serviceId`. The token, provisioned under the serviceId, can be shared provided that adequate PAN checks are in-place. Up to 5 shared serviceIds 

(source: mastercard_register_entities_chunk_006, data/raw/mastercard_register_entities.md)

---

Question: What is the status of token TKN-100234?
Route: token_status
Nodes: classify_request -> run_token_status -> build_answer
Tool called: get_token_status({'token_reference': 'TKN-100234'})
Final answer: Token TKN-100234 is ACTIVE (masked PAN **** **** **** 4421, expires 2027-09, last updated 2026-07-15).

---

Question: Tell me something interesting.
Route: clarification
Nodes: classify_request -> ask_clarification -> build_answer
Tool called: list_supported_topics({})
Final answer: Not sure what you're asking - I can help with: token_creation, token_management, payments, entity_registration, token_display. If you meant a specific token, give me its reference (TKN-XXXXXX) and I'll check its status.

---
