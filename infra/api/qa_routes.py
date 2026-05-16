"""QA API routes with SSE streaming."""
from __future__ import annotations

import logging
import uuid
from time import perf_counter

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from infra.api.models import ChatRequest, ConversationSummary, CreateConversationRequest
from infra.api.sse import answer_stream
from src.llm.qa_pipeline import answer_legal_question

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory conversation store
conversations: dict[str, dict] = {}


def _chunk_to_provisions(answer: dict) -> list[dict]:
    provisions = []
    for provision in answer.get("retrieved_provisions", []) or []:
        display = provision.get("display_citation") or provision.get("article_title") or provision.get("uid", "")
        article_number = provision.get("article_index")
        if article_number is None:
            article_number = provision.get("article") or ""
        provisions.append(
            {
                "documentName": provision.get("document_title", ""),
                "articleNumber": f"Điều {article_number}" if article_number not in ("", None) else "",
                "text": provision.get("effective_text") or provision.get("text", ""),
                "verified": bool(provision.get("validity", {}).get("status") == "verified"),
                "citation": display,
            }
        )
    return provisions


def _intent_chunks(answer: dict) -> list[dict]:
    intents = []
    intent = answer.get("intent") or {}
    for item in intent.get("intents", []) or []:
        intents.append(
            {
                "type": item.get("type", "SEARCH"),
                "confidence": item.get("confidence", answer.get("confidence", 0.0)),
            }
        )
    return intents


@router.post("/chat")
async def qa_chat(request: ChatRequest):
    """
    QA chat endpoint with SSE streaming.

    Processes message through: intent → retrieval → answer → citation verification.
    Streams answer token-by-token.
    """
    conversation_id = request.conversationId or f"conv_{uuid.uuid4().hex[:8]}"
    started = perf_counter()
    logger.info("QA HTTP request received conversation_id=%s message_chars=%d", conversation_id, len(request.message))

    try:
        payload = await answer_legal_question(request.message, conversation_id=conversation_id)
        answer_text = payload.get("answer", "")
        intents = _intent_chunks(payload)
        provisions = _chunk_to_provisions(payload)
        logger.info(
            "QA HTTP pipeline done conversation_id=%s status=%s citations_verified=%s elapsed_ms=%.1f",
            conversation_id,
            payload.get("retrieval_status", "ok"),
            payload.get("citations_verified", False),
            (perf_counter() - started) * 1000.0,
        )
    except Exception as exc:
        logger.exception("QA HTTP pipeline failed conversation_id=%s", conversation_id)
        raise HTTPException(status_code=500, detail=str(exc))

    if conversation_id not in conversations:
        conversations[conversation_id] = {
            "id": conversation_id,
            "title": request.message[:50],
            "messages": [],
            "createdAt": str(uuid.uuid4()),
        }
    conversations[conversation_id]["messages"].append({"role": "user", "content": request.message})
    conversations[conversation_id]["messages"].append({"role": "assistant", "content": answer_text})

    # Stream response
    return StreamingResponse(
        answer_stream(answer_text, intents=intents, provisions=provisions),
        media_type="text/event-stream",
    )


@router.post("/conversations")
async def create_conversation(request: CreateConversationRequest):
    """Create a new conversation."""
    conv_id = f"conv_{uuid.uuid4().hex[:8]}"
    conversations[conv_id] = {
        "id": conv_id,
        "title": request.title,
        "messages": [],
        "createdAt": str(uuid.uuid4()),
    }
    return {"id": conv_id}


@router.get("/conversations")
async def get_conversations():
    """List all conversations."""
    return [
        ConversationSummary(
            id=conv["id"],
            title=conv["title"],
            lastMessage=conv["messages"][-1]["content"] if conv["messages"] else "",
            createdAt=conv["createdAt"],
        )
        for conv in conversations.values()
    ]


@router.delete("/conversations/{conv_id}")
async def delete_conversation(conv_id: str):
    """Delete a conversation."""
    if conv_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    del conversations[conv_id]
    return {"status": "deleted"}
