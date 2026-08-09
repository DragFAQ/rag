"""
External tool: get_token_status — live status lookup for a Card-on-File token.

Type: read tool.
Purpose: returns the *current* status of a specific payment token (ACTIVE /
SUSPENDED / DELETED), masked PAN, expiry, and last-updated timestamp, from a
mock token-vault API.

When to call: the user asks about the current state of a specific token or
token reference (e.g. "is token TKN-100234 still active?").
When NOT to call: the user asks how tokenization, registration, or payments
work conceptually — that is static documentation and belongs to retrieval
(RAG), not this tool. Token status is dynamic data that changes over time and
cannot be reliably stored in a static knowledge base.

Run standalone for a quick check:
    python scripts/external_tool.py TKN-100234
"""

from __future__ import annotations

import re
import sys
from typing import Any

from pydantic import BaseModel, ValidationError

TOKEN_REFERENCE_PATTERN = re.compile(r"^TKN-\d{6,}$")

# Mock token vault. In a real integration this would be an HTTP call to the
# issuer/token-vault API; the contract (input/output/validation) stays the same.
MOCK_TOKENS: dict[str, dict[str, Any]] = {
    "TKN-100234": {
        "status": "ACTIVE",
        "masked_pan": "**** **** **** 4421",
        "expiry": "2027-09",
        "last_updated": "2026-07-15",
    },
    "TKN-100987": {
        "status": "SUSPENDED",
        "masked_pan": "**** **** **** 7789",
        "expiry": "2026-11",
        "last_updated": "2026-08-01",
    },
    "TKN-200555": {
        "status": "DELETED",
        "masked_pan": "**** **** **** 3310",
        "expiry": "2025-04",
        "last_updated": "2025-12-20",
    },
}


class TokenStatusInput(BaseModel):
    """Input contract for get_token_status."""

    token_reference: str


# OpenAI function-calling schema, doubles as the tool's documented contract.
TOOL_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "get_token_status",
        "description": (
            "Look up the current status of a Card-on-File token by its token "
            "reference. Returns status (ACTIVE, SUSPENDED, DELETED), masked PAN, "
            "expiry, and last-updated date from the token vault. Use this only "
            "when the user asks about a specific token's current state, not for "
            "questions about how tokenization works in general."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "token_reference": {
                    "type": "string",
                    "description": "Token reference, format TKN-XXXXXX (6+ digits).",
                }
            },
            "required": ["token_reference"],
            "additionalProperties": False,
        },
    },
}


def get_token_status(token_reference: str) -> dict[str, Any]:
    """
    Tool: get_token_status
    Type: read tool
    Purpose: returns the current status of a Card-on-File token from a mock
    token-vault API.
    """
    try:
        validated = TokenStatusInput(token_reference=token_reference)
    except ValidationError:
        return {"error": "token_reference is required and must be a string"}

    ref = validated.token_reference
    if not TOKEN_REFERENCE_PATTERN.match(ref):
        return {
            "error": (
                f"Invalid token_reference format: {ref!r}. "
                "Expected: TKN-XXXXXX (6+ digits)"
            )
        }

    record = MOCK_TOKENS.get(ref)
    if not record:
        return {"error": f"Token {ref} not found"}

    return {"token_reference": ref, **record}


def main() -> None:
    token_reference = sys.argv[1] if len(sys.argv) > 1 else "TKN-100234"
    result = get_token_status(token_reference)
    print(result)


if __name__ == "__main__":
    main()
