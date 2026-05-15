"""SSE streaming utilities for the QA chat endpoint."""
from __future__ import annotations

import json
from typing import Any, AsyncGenerator


def format_sse(data: dict[str, Any], event: str | None = None) -> str:
    """
    Format data as SSE event.

    Wire format: data: {json}\n
    """
    json_str = json.dumps(data, ensure_ascii=False)
    if event:
        return f"event: {event}\ndata: {json_str}\n\n"
    return f"data: {json_str}\n\n"


def format_done() -> str:
    """Format stream termination signal."""
    return "data: [DONE]\n\n"


async def answer_stream(
    answer_text: str,
    intents: list[dict] | None = None,
    provisions: list[dict] | None = None,
    chunk_size: int = 5,
) -> AsyncGenerator[str, None]:
    """
    Stream answer text token-by-token.

    Sends intents and provisions as a mid-stream chunk.
    """
    # Send first chunk with intents/provisions
    first_chunk = {"token": ""}
    if intents:
        first_chunk["intents"] = intents
    if provisions:
        first_chunk["provisions"] = provisions
    yield format_sse(first_chunk)

    # Stream text in chunks
    for i in range(0, len(answer_text), chunk_size):
        chunk = answer_text[i : i + chunk_size]
        yield format_sse({"token": chunk})

    # Terminate
    yield format_done()
