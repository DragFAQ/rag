"""
Compare baseline retrieval against metadata filtering and hybrid scoring on the
same test queries used in HW2, and write outputs/retrieval_comparison.md.

Run from the project root:
    python scripts/generate_retrieval_comparison.py

Each query declares the filter to search under, the documents that can answer it,
and the chunks that carry the answer. All four configurations run on every query
so each improvement can be scored on its own.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

OUTPUTS_DIR = Path("outputs")
OUTPUT_PATH = OUTPUTS_DIR / "retrieval_comparison.md"

BASELINE = "baseline"
FILTER_ONLY = "filter only"
HYBRID_ONLY = "hybrid only"
IMPROVED = "filter + hybrid"
CONFIGURATIONS = [BASELINE, FILTER_ONLY, HYBRID_ONLY, IMPROVED]
TIMING_REPEATS = 5

# Same 8 queries as outputs/retrieval_examples.md (HW2).
#   metadata_filter    declared per query
#   expected_documents documents that can answer the query ([] = out of domain)
#   answer_chunks      chunks that carry the answer text
TEST_QUERIES: list[dict[str, Any]] = [
    {
        "query": "What is a serviceId and how is it created?",
        "metadata_filter": {"topic": "entity_registration"},
        "expected_documents": ["mastercard_register_entities"],
        "answer_chunks": [
            "mastercard_register_entities_chunk_003",
            "mastercard_register_entities_chunk_004",
        ],
    },
    {
        "query": "How do I get a unique identifier from Mastercard for my program?",
        "metadata_filter": {"topic": "entity_registration"},
        "expected_documents": ["mastercard_register_entities"],
        "answer_chunks": [
            "mastercard_register_entities_chunk_003",
            "mastercard_register_entities_chunk_004",
        ],
    },
    {
        "query": "What HTTP status code indicates successful token provisioning?",
        "metadata_filter": {"topic": "token_creation"},
        "expected_documents": [
            "mastercard_tokenization-of-existing-card",
            "mastercard_tokenization-while-adding-card",
            "mastercard_tokenization-while-transacting",
        ],
        "answer_chunks": [
            "mastercard_tokenization-of-existing-card_chunk_006",
            "mastercard_tokenization-of-existing-card_chunk_007",
            "mastercard_tokenization-while-adding-card_chunk_008",
            "mastercard_tokenization-while-adding-card_chunk_009",
            "mastercard_tokenization-while-transacting_chunk_012",
            "mastercard_tokenization-while-transacting_chunk_013",
        ],
    },
    {
        "query": "What must an acquirer support to process DSRP token transactions?",
        "metadata_filter": {"topic": "payments"},
        "expected_documents": ["mastercard_making-payments"],
        "answer_chunks": [
            "mastercard_making-payments_chunk_009",
            "mastercard_making-payments_chunk_010",
        ],
    },
    {
        "query": "Tell me about card art and visual representation of stored cards",
        "metadata_filter": {"topic": "token_display"},
        "expected_documents": ["mastercard_displaying-tokenized-pan-details"],
        "answer_chunks": [
            "mastercard_displaying-tokenized-pan-details_chunk_001",
            "mastercard_displaying-tokenized-pan-details_chunk_003",
            "mastercard_displaying-tokenized-pan-details_chunk_004",
        ],
    },
    {
        "query": "What does the DE104 field contain?",
        "metadata_filter": {"topic": "payments"},
        "expected_documents": ["mastercard_making-payments"],
        "answer_chunks": [
            "mastercard_making-payments_chunk_009",
            "mastercard_making-payments_chunk_010",
        ],
    },
    {
        "query": "What is Mastercard's current stock price?",
        "metadata_filter": None,
        "expected_documents": [],
        "answer_chunks": [],
    },
    {
        "query": "How do I reset a cardholder's online banking password?",
        "metadata_filter": None,
        "expected_documents": [],
        "answer_chunks": [],
    },
]

# Supplementary set. The 8 queries above each target a single document, so the
# baseline rarely crosses topics on them. These are worded to pull toward a topic
# that does not hold the answer, to test the filter when topics collide.
CROSS_TOPIC_QUERIES: list[dict[str, Any]] = [
    {
        "query": "How do I make sure a card is active before tokenizing it?",
        "topic": "token_creation",
        "answer_chunks": ["mastercard_tokenization-of-existing-card_chunk_005"],
    },
    {
        "query": "What does the integrator do after receiving a card notification?",
        "topic": "token_management",
        "answer_chunks": [
            "mastercard_managing_tokens_chunk_003",
            "mastercard_managing_tokens_chunk_004",
        ],
    },
    {
        "query": "How do I get the new expiry date after the issuer updates a card?",
        "topic": "token_management",
        "answer_chunks": [
            "mastercard_managing_tokens_chunk_010",
            "mastercard_managing_tokens_chunk_012",
            "mastercard_managing_tokens_chunk_018",
            "mastercard_managing_tokens_chunk_019",
            "mastercard_managing_tokens_chunk_020",
        ],
    },
    {
        "query": "What does the Integrator receive when a token changes state?",
        "topic": "token_management",
        "answer_chunks": [
            "mastercard_managing_tokens_chunk_003",
            "mastercard_managing_tokens_chunk_004",
            "mastercard_managing_tokens_chunk_017",
        ],
    },
    {
        "query": "What should I do if provisioning needs cardholder authentication?",
        "topic": "token_creation",
        "answer_chunks": [
            "mastercard_tokenization-of-existing-card_chunk_007",
            "mastercard_tokenization-while-adding-card_chunk_009",
            "mastercard_tokenization-while-transacting_chunk_013",
        ],
    },
    {
        "query": "Where do I find the wallet or DPA identifier for a payment?",
        "topic": "payments",
        "answer_chunks": [
            "mastercard_making-payments_chunk_016",
            "mastercard_making-payments_chunk_017",
        ],
    },
    {
        "query": "Which entity types can a Payment Facilitator sponsor for transactions?",
        "topic": "entity_registration",
        "answer_chunks": [
            "mastercard_register_entities_chunk_005",
            "mastercard_register_entities_chunk_006",
            "mastercard_register_entities_chunk_009",
        ],
    },
    {
        "query": "Which field gives me the artwork URL for a saved card?",
        "topic": "token_display",
        "answer_chunks": [
            "mastercard_displaying-tokenized-pan-details_chunk_003",
            "mastercard_displaying-tokenized-pan-details_chunk_004",
        ],
    },
    {
        "query": "What SLI value is needed for partial shipment payments?",
        "topic": "payments",
        "answer_chunks": [
            "mastercard_making-payments_chunk_021",
            "mastercard_making-payments_chunk_022",
        ],
    },
    {
        "query": "How do I handle a 200 response that still requires additional steps?",
        "topic": "token_creation",
        "answer_chunks": [
            "mastercard_tokenization-of-existing-card_chunk_007",
            "mastercard_tokenization-while-adding-card_chunk_009",
            "mastercard_tokenization-while-transacting_chunk_013",
        ],
    },
    {
        "query": "How do I remove a card the cardholder no longer wants?",
        "topic": "token_management",
        "answer_chunks": [
            "mastercard_managing_tokens_chunk_022",
            "mastercard_managing_tokens_chunk_024",
            "mastercard_managing_tokens_chunk_025",
        ],
    },
]

# How the set above was assembled.
CROSS_TOPIC_PROBED = 40
CROSS_TOPIC_FAILURES_FOUND = 7
CROSS_TOPIC_FAILURES_DROPPED = 1

# One wrong filter, to show what an over-aggressive filter does.
OVER_FILTER_DEMO = {
    "query": "What HTTP status code indicates successful token provisioning?",
    "correct_filter": {"topic": "token_creation"},
    "wrong_filter": {"topic": "token_management"},
}


def document_of(result: dict[str, Any]) -> str:
    return result["metadata"].get("document_id", "?")


def config_options(
    configuration: str, test_case: dict[str, Any]
) -> tuple[dict[str, str] | None, bool]:
    """Map a configuration name onto (metadata_filter, use_hybrid)."""
    metadata_filter = test_case["metadata_filter"]
    return {
        BASELINE: (None, False),
        FILTER_ONLY: (metadata_filter, False),
        HYBRID_ONLY: (None, True),
        IMPROVED: (metadata_filter, True),
    }[configuration]


def diagnose(test_case: dict[str, Any], results: list[dict[str, Any]]) -> str:
    """Classify what kind of failure a baseline result is."""
    if not test_case["expected_documents"]:
        return "out of domain, no source can answer this"
    if not results:
        return "nothing retrieved"
    retrieved_documents = [document_of(result) for result in results]
    if retrieved_documents[0] in test_case["expected_documents"]:
        if results[0]["chunk_id"] in test_case["answer_chunks"]:
            return "OK"
        return "right document, top-1 chunk does not carry the answer"
    if any(document in test_case["expected_documents"] for document in retrieved_documents):
        return "wrong top-1 document, expected document lower in top-k (ranking)"
    return "expected document missing from top-k (recall)"


def format_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


def top_1_label(results: list[dict[str, Any]]) -> str:
    return results[0]["chunk_id"] if results else "*(no results)*"


def describe_change(
    test_case: dict[str, Any], per_config: dict[str, list[dict[str, Any]]]
) -> str:
    """Describe what moved between baseline and the improved configuration."""
    baseline_top = top_1_label(per_config[BASELINE])
    improved_top = top_1_label(per_config[IMPROVED])
    filter_top = top_1_label(per_config[FILTER_ONLY])
    hybrid_top = top_1_label(per_config[HYBRID_ONLY])

    if baseline_top == improved_top:
        baseline_documents = {document_of(r) for r in per_config[BASELINE]}
        improved_documents = {document_of(r) for r in per_config[IMPROVED]}
        removed = baseline_documents - improved_documents
        if removed:
            return (
                "top-1 unchanged; filter removed off-topic chunks lower in top-3 ("
                + ", ".join(sorted(removed))
                + ")"
            )
        return "no change"

    causes = []
    if filter_top != baseline_top:
        causes.append("metadata filter")
    if hybrid_top != baseline_top:
        causes.append("hybrid scoring")
    if not causes:
        causes.append("filter and hybrid only in combination")
    return "new top-1 via " + " + ".join(causes)


def build_report(
    per_query: list[dict[str, Any]],
    topic_counts: dict[str, int],
    total_chunks: int,
    timings: dict[str, float],
    over_filter: dict[str, list[dict[str, Any]]],
    cross_topic: list[dict[str, Any]],
    settings: dict[str, Any],
) -> str:
    sections: list[str] = ["# Baseline vs Improved Retrieval", ""]

    sections += [
        "## Setup",
        "",
        f"- Embedding model: `{settings['model_name']}`",
        f"- Index: FAISS `IndexFlatIP` over {total_chunks} L2-normalized chunk vectors",
        f"- Candidates retrieved from FAISS: {settings['candidate_k']}",
        f"- Final results kept: {settings['final_k']}",
        f"- Hybrid score: `{settings['semantic_weight']} * semantic"
        f" + {settings['keyword_weight']} * keyword_overlap` (raw scores, no normalization)",
        "- Metadata filter: applied in Python after FAISS, on the `topic` field",
        "",
        "The same 8 queries from `outputs/retrieval_examples.md` (HW2) are reused",
        "unchanged, so baseline numbers here match that file exactly.",
        "",
        "### Why the filter uses `topic`",
        "",
        "The obvious fields to filter on are all constant in this corpus, so a filter",
        "on any of them matches all "
        f"{total_chunks} chunks and excludes nothing:",
        "",
        format_table(
            ["Field", "Distinct values", "Usable as a filter?"],
            [
                ["`document_type`", "1 (`api_documentation`)", "no"],
                ["`domain`", "1 (`payments`)", "no"],
                ["`language`", "1 (`en`)", "no"],
                ["`source_type`", "1 (`markdown`)", "no"],
                ["`topic`", f"{len(topic_counts)} (added for HW3)", "yes"],
            ],
        ),
        "",
        "`topic` was added to the frontmatter of each raw document and propagated",
        "through `prepare_knowledge_base.py` into every chunk:",
        "",
        format_table(
            ["Topic", "Chunks", "Share of corpus"],
            [
                [f"`{topic}`", str(count), f"{count / total_chunks:.0%}"]
                for topic, count in sorted(
                    topic_counts.items(), key=lambda item: -item[1]
                )
            ],
        ),
        "",
    ]

    sections += [
        "## 1. Baseline diagnostics",
        "",
        "What the baseline returns before any changes, and what kind of failure it is.",
        "",
        format_table(
            ["Query", "Expected document", "Retrieved top-1 document", "Score", "Issue"],
            [
                [
                    entry["query"],
                    ", ".join(entry["expected_documents"]) or "*(none, out of domain)*",
                    document_of(entry["per_config"][BASELINE][0]),
                    f"{entry['per_config'][BASELINE][0]['score']:.4f}",
                    entry["issue"],
                ]
                for entry in per_query
            ],
        ),
        "",
    ]

    sections += [
        "## 2. How much the metadata filter narrows the search",
        "",
        format_table(
            [
                "Query",
                "Filter",
                "Corpus chunks kept",
                "Off-topic chunks in top-10 candidates",
            ],
            [
                [
                    entry["query"],
                    f"`{entry['metadata_filter']}`" if entry["metadata_filter"] else "*(none)*",
                    (
                        f"{entry['filter_corpus_size']} / {total_chunks}"
                        if entry["metadata_filter"]
                        else f"{total_chunks} / {total_chunks}"
                    ),
                    str(entry["off_topic_candidates"]),
                ]
                for entry in per_query
            ],
        ),
        "",
    ]

    sections += [
        "## 3. Baseline vs improved (top-1)",
        "",
        format_table(
            ["Query", "Baseline top-1", "Improved top-1", "What changed"],
            [
                [
                    entry["query"],
                    top_1_label(entry["per_config"][BASELINE]),
                    top_1_label(entry["per_config"][IMPROVED]),
                    entry["what_changed"],
                ]
                for entry in per_query
            ],
        ),
        "",
    ]

    in_domain = [entry for entry in per_query if entry["expected_documents"]]
    sections += [
        "## 4. Ablation: which technique did the work",
        "",
        "Each improvement also runs alone, otherwise there is no way to tell which one",
        "caused a change. Top-1 chunk per configuration:",
        "",
        format_table(
            ["Query"] + CONFIGURATIONS,
            [
                [entry["query"]]
                + [top_1_label(entry["per_config"][name]) for name in CONFIGURATIONS]
                for entry in per_query
            ],
        ),
        "",
        f"Scored over the {len(in_domain)} in-domain queries:",
        "",
        format_table(
            [
                "Configuration",
                "Correct top-1 document",
                "Answer-bearing top-1 chunk",
                "Answer chunk anywhere in top-3",
                "Answer chunks in top-3",
                "Off-topic chunks in top-3",
            ],
            [
                [
                    name,
                    f"{sum(1 for e in in_domain if document_of(e['per_config'][name][0]) in e['expected_documents'])} / {len(in_domain)}",
                    f"{sum(1 for e in in_domain if e['per_config'][name][0]['chunk_id'] in e['answer_chunks'])} / {len(in_domain)}",
                    f"{sum(1 for e in in_domain if any(r['chunk_id'] in e['answer_chunks'] for r in e['per_config'][name]))} / {len(in_domain)}",
                    str(
                        sum(
                            1
                            for e in in_domain
                            for r in e["per_config"][name]
                            if r["chunk_id"] in e["answer_chunks"]
                        )
                    ),
                    str(
                        sum(
                            1
                            for e in in_domain
                            for r in e["per_config"][name]
                            if document_of(r) not in e["expected_documents"]
                        )
                    ),
                ]
                for name in CONFIGURATIONS
            ],
        ),
        "",
        "The first three columns are identical across all four configurations. The last",
        "two are where the improvements show up: `answer chunks in top-3` counts how much",
        "of the returned context carries the answer, and `off-topic chunks in top-3`",
        "counts context from a document that cannot answer the query at all.",
        "",
        "## 5. When hybrid scoring can overturn the semantic ranking",
        "",
        "With weights 0.7 and 0.3, a challenger overtakes the leader only when",
        "`0.3 * keyword_gap > 0.7 * semantic_gap`, so its keyword advantage has to be",
        "2.33x the semantic deficit before anything moves. Each row compares the baseline",
        "top-1 against the candidate that challenges it: the hybrid winner where the",
        "ranking changed, otherwise the closest semantic runner-up.",
        "",
        format_table(
            [
                "Query",
                "Challenger",
                "Semantic gap",
                "Keyword gap needed",
                "Keyword gap available",
                "Top-1 changes?",
            ],
            [
                [
                    entry["query"],
                    f"`{entry['gap']['challenger'].replace('mastercard_', '')}` "
                    f"(rank {entry['gap']['challenger_rank']})",
                    f"{entry['gap']['semantic_gap']:+.4f}",
                    f"{entry['gap']['keyword_gap_needed']:+.4f}",
                    f"{entry['gap']['keyword_gap_available']:+.4f}",
                    "yes" if entry["gap"]["swaps"] else "no",
                ]
                for entry in per_query
            ],
        ),
        "",
        "There are two reasons a query does not move: either the keyword gap is too",
        "small, or it is exactly zero because both candidates match the same share of",
        "query terms. Query 1 is the clearest tie case. Its top three chunks all score",
        "0.6250, because the one distinguishing term (`serviceid`) appears in all three",
        "and the rest of the matches are stopwords (`a`, `and`, `is`). Unweighted overlap",
        "cannot separate candidates that all mention the key term.",
        "",
    ]

    sections += ["## 6. Per-query detail", ""]
    for entry in per_query:
        sections += [f"### {entry['query']}", ""]
        for name in (BASELINE, IMPROVED):
            results = entry["per_config"][name]
            sections.append(f"**{name}**")
            sections.append("")
            if not results:
                sections += ["*(no results, the filter excluded every candidate)*", ""]
                continue
            for rank, result in enumerate(results, start=1):
                score_text = f"score {result['score']:.4f}"
                if "hybrid_score" in result:
                    score_text = (
                        f"hybrid {result['hybrid_score']:.4f} "
                        f"(semantic {result['semantic_score']:.4f}, "
                        f"keyword {result['keyword_score']:.4f})"
                    )
                marker = " **(answer)**" if result["chunk_id"] in entry["answer_chunks"] else ""
                preview = result["text"][:140].replace("\n", " ")
                sections.append(
                    f"{rank}. `{result['chunk_id']}` | {score_text}{marker}  \n    {preview}..."
                )
            sections.append("")

    baseline_topic_hits = sum(1 for e in cross_topic if e["baseline_topic_ok"])
    improved_topic_hits = sum(1 for e in cross_topic if e["improved_topic_ok"])
    baseline_answer_hits = sum(1 for e in cross_topic if e["baseline_has_answer"])
    improved_answer_hits = sum(1 for e in cross_topic if e["improved_has_answer"])
    fixed = [e for e in cross_topic if not e["baseline_topic_ok"] and e["improved_topic_ok"]]

    sections += [
        "## 7. Supplementary: cross-topic stress queries",
        "",
        "Each of the 8 queries above targets a single document, so the baseline almost",
        "never crosses topics there and the filter has little to remove. This set is",
        "worded to pull toward a topic that does not hold the answer.",
        "",
        "**How the set was assembled.** Of the"
        f" {CROSS_TOPIC_PROBED} candidate queries run against the baseline,",
        f"{CROSS_TOPIC_FAILURES_FOUND} put the wrong topic at top-1. One of those was",
        "dropped because its answer exists in two topics, so the ground truth would be",
        "arbitrary. The remaining"
        f" {CROSS_TOPIC_FAILURES_FOUND - CROSS_TOPIC_FAILURES_DROPPED} failures are kept,"
        " plus the"
        f" {len(CROSS_TOPIC_QUERIES) - (CROSS_TOPIC_FAILURES_FOUND - CROSS_TOPIC_FAILURES_DROPPED)}"
        " queries the baseline already handled correctly.",
        "Failures are over-represented below on purpose. The unfiltered baseline failure",
        f"rate was {CROSS_TOPIC_FAILURES_FOUND}/{CROSS_TOPIC_PROBED}"
        f" ({CROSS_TOPIC_FAILURES_FOUND / CROSS_TOPIC_PROBED:.0%}), not"
        f" {len(CROSS_TOPIC_QUERIES) - baseline_topic_hits}/{len(CROSS_TOPIC_QUERIES)}.",
        "",
        format_table(
            [
                "Query",
                "Answer topic",
                "Baseline top-1 topic",
                "Baseline top-1",
                "Improved top-1",
                "Fixed?",
            ],
            [
                [
                    entry["query"],
                    f"`{entry['topic']}`",
                    f"`{entry['baseline_topic']}`"
                    + ("" if entry["baseline_topic_ok"] else " **wrong**"),
                    f"`{entry['per_config'][BASELINE][0]['chunk_id'].replace('mastercard_', '')}`",
                    f"`{top_1_label(entry['per_config'][IMPROVED]).replace('mastercard_', '')}`",
                    "yes"
                    if not entry["baseline_topic_ok"] and entry["improved_topic_ok"]
                    else ("n/a" if entry["baseline_topic_ok"] else "no"),
                ]
                for entry in cross_topic
            ],
        ),
        "",
        f"Over these {len(CROSS_TOPIC_QUERIES)} queries:",
        "",
        format_table(
            ["Metric", BASELINE, IMPROVED],
            [
                [
                    "Correct topic at top-1",
                    f"{baseline_topic_hits} / {len(cross_topic)}",
                    f"{improved_topic_hits} / {len(cross_topic)}",
                ],
                [
                    "Answer chunk in top-3",
                    f"{baseline_answer_hits} / {len(cross_topic)}",
                    f"{improved_answer_hits} / {len(cross_topic)}",
                ],
            ],
        ),
        "",
        "The margins matter here. The off-topic chunk wins by a very small amount, so no",
        "score cutoff could separate the two. Only a hard metadata constraint can.",
        "",
        format_table(
            [
                "Query",
                "Off-topic top-1 (baseline)",
                "Score",
                "On-topic top-1 (filtered)",
                "Score",
                "Margin",
            ],
            [
                [
                    entry["query"],
                    f"`{entry['per_config'][BASELINE][0]['chunk_id'].replace('mastercard_', '')}`",
                    f"{entry['per_config'][BASELINE][0]['score']:.4f}",
                    f"`{entry['per_config'][FILTER_ONLY][0]['chunk_id'].replace('mastercard_', '')}`",
                    f"{entry['per_config'][FILTER_ONLY][0]['score']:.4f}",
                    f"{entry['per_config'][BASELINE][0]['score'] - entry['per_config'][FILTER_ONLY][0]['score']:+.4f}",
                ]
                for entry in cross_topic
                if not entry["baseline_topic_ok"] and entry["per_config"][FILTER_ONLY]
            ],
        ),
        "",
        "One case shows the limit of filtering. *Where do I find the wallet or DPA",
        "identifier for a payment?* gets the correct topic, but the chunks naming",
        "`dpaData.dpaURI` still do not reach the top 3. The filter controls which document",
        "is searched, not how chunks are ordered inside it. That needs a reranker.",
        "",
    ]

    sections += [
        "## 8. Risk: a filter that is too aggressive",
        "",
        f"Query: *{OVER_FILTER_DEMO['query']}*",
        "",
        "The answer is in the `token_creation` documents. A wrong topic guess does not",
        "just reorder the results, it removes the answer from the candidate set, and",
        "nothing after retrieval can recover it.",
        "",
        format_table(
            ["Filter", "Top-1", "Answer in top-3?"],
            [
                [
                    f"`{OVER_FILTER_DEMO['correct_filter']}`",
                    top_1_label(over_filter["correct"]),
                    "yes" if over_filter["correct_has_answer"] else "no",
                ],
                [
                    f"`{OVER_FILTER_DEMO['wrong_filter']}`",
                    top_1_label(over_filter["wrong"]),
                    "yes" if over_filter["wrong_has_answer"] else "no",
                ],
            ],
        ),
        "",
    ]

    sections += [
        "## 9. Cost",
        "",
        f"Wall-clock time for all {len(TEST_QUERIES)} queries, model and index already",
        f"loaded, averaged over {TIMING_REPEATS} repeats:",
        "",
        format_table(
            ["Configuration", "Total", "Per query"],
            [
                [
                    name,
                    f"{timings[name] * 1000:.0f} ms",
                    f"{timings[name] / len(TEST_QUERIES) * 1000:.1f} ms",
                ]
                for name in CONFIGURATIONS
            ],
        ),
        "",
    ]

    sections += [CONCLUSION, ""]
    return "\n".join(sections)


CONCLUSION = """
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
""".strip()


def main() -> None:
    from build_faiss_index import load_jsonl_records
    from semantic_search import CHUNKS_PATH, MODEL_NAME, load_retrieval_components
    from retrieval_improved import (
        CANDIDATE_K,
        FINAL_K,
        KEYWORD_WEIGHT,
        SEMANTIC_WEIGHT,
        keyword_overlap_score,
        metadata_matches,
        retrieve,
    )

    model, index, chunks = load_retrieval_components()
    all_chunks = load_jsonl_records(CHUNKS_PATH)

    topic_counts: dict[str, int] = {}
    for chunk in all_chunks:
        topic = chunk["metadata"]["topic"]
        topic_counts[topic] = topic_counts.get(topic, 0) + 1

    per_query: list[dict[str, Any]] = []
    timings = {name: 0.0 for name in CONFIGURATIONS}

    # Warm up before timing. The first encode() call pays one-off setup costs that
    # would otherwise be charged to whichever configuration ran first.
    retrieve(query=TEST_QUERIES[0]["query"], model=model, index=index, chunks=chunks)

    for position, test_case in enumerate(TEST_QUERIES, start=1):
        per_config: dict[str, list[dict[str, Any]]] = {}
        for name in CONFIGURATIONS:
            metadata_filter, use_hybrid = config_options(name, test_case)
            started = time.perf_counter()
            for _ in range(TIMING_REPEATS):
                per_config[name] = retrieve(
                    query=test_case["query"],
                    model=model,
                    index=index,
                    chunks=chunks,
                    metadata_filter=metadata_filter,
                    use_hybrid=use_hybrid,
                )
            timings[name] += (time.perf_counter() - started) / TIMING_REPEATS

        candidates = retrieve(
            query=test_case["query"],
            model=model,
            index=index,
            chunks=chunks,
            final_k=CANDIDATE_K,
        )
        metadata_filter = test_case["metadata_filter"]
        off_topic_candidates = (
            sum(1 for c in candidates if not metadata_matches(c, metadata_filter))
            if metadata_filter
            else 0
        )
        filter_corpus_size = (
            sum(1 for c in all_chunks if metadata_matches(c, metadata_filter))
            if metadata_filter
            else len(all_chunks)
        )

        keyword_scores = [
            keyword_overlap_score(test_case["query"], candidate["text"])
            for candidate in candidates
        ]
        # Compare the baseline leader against the candidate that challenges it:
        # the hybrid winner if the ranking changed, else the semantic runner-up.
        hybrid_winner_id = per_config[HYBRID_ONLY][0]["chunk_id"]
        swaps = hybrid_winner_id != candidates[0]["chunk_id"]
        challenger_position = (
            next(
                position
                for position, candidate in enumerate(candidates)
                if candidate["chunk_id"] == hybrid_winner_id
            )
            if swaps
            else 1
        )
        semantic_gap = candidates[0]["score"] - candidates[challenger_position]["score"]
        gap = {
            "challenger": candidates[challenger_position]["chunk_id"],
            "challenger_rank": challenger_position + 1,
            "semantic_gap": semantic_gap,
            "keyword_gap_needed": semantic_gap * SEMANTIC_WEIGHT / KEYWORD_WEIGHT,
            "keyword_gap_available": keyword_scores[challenger_position] - keyword_scores[0],
            "swaps": swaps,
        }

        per_query.append(
            {
                **test_case,
                "position": position,
                "per_config": per_config,
                "issue": diagnose(test_case, per_config[BASELINE]),
                "what_changed": describe_change(test_case, per_config),
                "off_topic_candidates": off_topic_candidates,
                "filter_corpus_size": filter_corpus_size,
                "keyword_scores": keyword_scores,
                "gap": gap,
            }
        )
        print(f"[{position}/{len(TEST_QUERIES)}] {test_case['query']}")

    answer_chunks = next(
        case["answer_chunks"]
        for case in TEST_QUERIES
        if case["query"] == OVER_FILTER_DEMO["query"]
    )
    cross_topic: list[dict[str, Any]] = []
    for position, test_case in enumerate(CROSS_TOPIC_QUERIES, start=1):
        metadata_filter = {"topic": test_case["topic"]}
        per_config = {
            BASELINE: retrieve(
                query=test_case["query"], model=model, index=index, chunks=chunks
            ),
            FILTER_ONLY: retrieve(
                query=test_case["query"],
                model=model,
                index=index,
                chunks=chunks,
                metadata_filter=metadata_filter,
            ),
            IMPROVED: retrieve(
                query=test_case["query"],
                model=model,
                index=index,
                chunks=chunks,
                metadata_filter=metadata_filter,
                use_hybrid=True,
            ),
        }
        improved = per_config[IMPROVED]
        cross_topic.append(
            {
                **test_case,
                "per_config": per_config,
                "baseline_topic": per_config[BASELINE][0]["metadata"]["topic"],
                "baseline_topic_ok": (
                    per_config[BASELINE][0]["metadata"]["topic"] == test_case["topic"]
                ),
                "improved_topic_ok": bool(improved)
                and improved[0]["metadata"]["topic"] == test_case["topic"],
                "baseline_has_answer": any(
                    r["chunk_id"] in test_case["answer_chunks"] for r in per_config[BASELINE]
                ),
                "improved_has_answer": any(
                    r["chunk_id"] in test_case["answer_chunks"] for r in improved
                ),
            }
        )
        print(f"[cross-topic {position}/{len(CROSS_TOPIC_QUERIES)}] {test_case['query']}")

    over_filter: dict[str, Any] = {}
    for label, filter_key in (("correct", "correct_filter"), ("wrong", "wrong_filter")):
        results = retrieve(
            query=OVER_FILTER_DEMO["query"],
            model=model,
            index=index,
            chunks=chunks,
            metadata_filter=OVER_FILTER_DEMO[filter_key],
        )
        over_filter[label] = results
        over_filter[f"{label}_has_answer"] = any(
            result["chunk_id"] in answer_chunks for result in results
        )

    report = build_report(
        per_query=per_query,
        topic_counts=topic_counts,
        total_chunks=len(all_chunks),
        timings=timings,
        over_filter=over_filter,
        cross_topic=cross_topic,
        settings={
            "model_name": MODEL_NAME,
            "candidate_k": CANDIDATE_K,
            "final_k": FINAL_K,
            "semantic_weight": SEMANTIC_WEIGHT,
            "keyword_weight": KEYWORD_WEIGHT,
        },
    )

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(report, encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
