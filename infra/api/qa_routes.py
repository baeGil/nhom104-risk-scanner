"""QA API routes with SSE streaming."""
from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from infra.api.models import ChatRequest, ConversationSummary, CreateConversationRequest
from infra.api.sse import answer_stream, format_sse
from src.llm.mock_provider import MockLLMProvider

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory conversation store
conversations: dict[str, dict] = {}
mock_llm = MockLLMProvider()


@router.post("/chat")
async def qa_chat(request: ChatRequest):
    """
    QA chat endpoint with SSE streaming.

    Processes message through: intent → retrieval → answer → citation verification.
    Streams answer token-by-token.
    """
    conversation_id = request.conversationId or f"conv_{uuid.uuid4().hex[:8]}"

    # Intent analysis
    intent_result = await mock_llm.chat(request.message)

    # Extract intents for frontend
    intents = []
    if isinstance(intent_result, dict) and "intents" in intent_result:
        intents = [
            {"type": i.get("type", "SEARCH"), "confidence": i.get("confidence", 0.5)}
            for i in intent_result["intents"]
        ]

    # Generate answer (mock for now, replace with real pipeline)
    answer_result = await mock_llm.chat(f"Trả lời: {request.message}")
    if isinstance(answer_result, dict) and "answer" in answer_result:
        answer_text = answer_result["answer"]
        citations = answer_result.get("citations", [])
    else:
        answer_text = "Tôi đang xử lý câu hỏi của bạn..."
        citations = []

    # Format provisions for frontend
    provisions = [
        {
            "documentName": c.get("document", ""),
            "articleNumber": c.get("article", ""),
            "text": c.get("text", ""),
            "verified": True,
        }
        for c in citations
    ]

    # Store conversation
    if conversation_id not in conversations:
        conversations[conversation_id] = {
            "id": conversation_id,
            "title": request.message[:50],
            "messages": [],
            "createdAt": str(uuid.uuid4()),
        }
    conversations[conversation_id]["messages"].append({
        "role": "user",
        "content": request.message,
    })
    conversations[conversation_id]["messages"].append({
        "role": "assistant",
        "content": answer_text,
    })

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
