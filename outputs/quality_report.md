# Quality Report - Card-on-File Assistant (agent_with_tool.py)

## What was tested

10 questions through `agent_with_tool.py::answer_question()`: a single-topic KB
question, a question targeting the table row that gets split across two chunks by
the sentence-fallback splitter, two questions rebuilt from retrieval problems the
main README documents at a smaller `top_k`, two token-status tool calls (one hit,
one not-found), an out-of-domain question, a cross-topic question needing two
source documents, an ambiguous one-liner, and a plausible-sounding but undocumented
question. Full table and every answer in `outputs/eval_results.md`, the numbers in
`outputs/eval_summary.md`.

## Results

9/10 success, 1/10 partial, 0/10 failure. Groundedness good on all 6 cases it
applies to (the other 4 are tool calls or correct declines - "grounded in retrieved
context" isn't the right question for those). Average latency 2.5s, max 3.7s.
Zero hallucinations, zero wrong tool calls, zero wrong-retrieval failures.

Cleaner than expected. Cases 3 and 7 were deliberately built from retrieval
failures the Improved Retrieval section documents against `semantic_search.py` /
`retrieval_improved.py` at `top_k=3` / `final_k=3`, on the assumption they'd
reproduce here too. They didn't - `agent_with_tool.py` runs at `top_k=4`, one
candidate more, and that was enough to pull the right chunk into context both
times. Worth remembering next time a "known" retrieval issue gets reused across
scripts with different `k`: it's not automatically the same experiment.

## Where it works and where it doesn't

Direct single-document questions (serviceId, TOKEN_REFRESH) come back clean and
correctly cited. Tool routing is solid - the model only calls `get_token_status`
when a token reference is actually named, never for conceptual questions, and on
a not-found token it says so instead of inventing a status. Both refusal cases
(out-of-domain PCI-DSS question, the undocumented lost-device reason code) got an
honest "not enough information" instead of a guess. Case 9's cross-topic question
pulled chunks from two different source documents in one retrieval call and
combined them correctly - the one case built to test multi-document reasoning
actually worked.

The weak spot is case 8, "Tell me about tokens." No clarification happens - the
model just picks a broad answer spanning three of the five topics. The answer
itself is accurate and grounded, so nothing is technically wrong with it, but a
real user asking something this vague probably wanted one specific thing, and the
system decided the scope for them without saying so. `agent_with_tool.py` has no
clarification route; that logic only lives in `agent_flow.py`'s keyword router,
which this script doesn't share.

Second problem, found by accident while building `route_for()` in `run_eval.py`:
the system prompt requires citing sources on every answer, including declines, so
the "answer exactly this sentence" instruction for the no-info case never actually
comes out character-for-character - the model appends citations after it every
time (cases 6 and 10). A person reading the answer can't tell the difference, but
`route_for()`'s exact-string match can, and it mislabeled both fallback cases as
`route_or_mode: RAG` instead of `fallback`. Any code trying to classify runs this
way needs `.startswith()`, not `==`.

Third: this eval set didn't actually find where the system breaks. Every question
landed inside `top_k=4`'s comfort zone, including the two picked specifically to
reproduce known retrieval failures at a smaller `k`. That's a real result, not a
wasted one, but 10/10 is a statement about these 10 questions, not a general claim
that `top_k=4` is safe - a wider set (deeper multi-hop questions, more of the
near-tied-score queries from the README, a bigger KB) would be needed before
trusting that.

## Next steps

- Add a clarification path to `agent_with_tool.py`, or route ambiguous questions
  through `agent_flow.py`'s router first, so a vague question gets a follow-up
  instead of a silent broad answer
- Relax the "say exactly" instruction to tolerate the citation suffix, or switch
  any decline-detection code to `answer.startswith(...)`
- Rebuild the eval set with questions chosen to actually stress `top_k=4` - the
  near-tied-score serviceId query and the DPA-identifier query need a version that
  still fails at this script's real settings, not one that was already known to
  fail at a smaller `k` tested somewhere else
