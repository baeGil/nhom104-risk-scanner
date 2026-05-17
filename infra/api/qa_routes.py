"""QA API routes with SSE streaming."""
from __future__ import annotations

import logging
import os
from time import perf_counter

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI

from infra.api.chat_store import ChatStoreError, estimate_token_count, get_chat_store
from infra.api.models import (
    ChatMessageResponse,
    ChatRequest,
    ConversationDetail,
    ConversationSummary,
    CreateConversationRequest,
    RenameConversationRequest,
)
from infra.api.sse import answer_stream
from src.auth import CurrentUser, get_current_user
from src.llm.qa_pipeline import answer_legal_question

logger = logging.getLogger(__name__)
router = APIRouter()


def _chunk_to_provisions(answer: dict) -> list[dict]:
    provisions = []
    verified_map = {}
    cited_uids = set()
    for citation in answer.get("citations", []) or []:
        uid = citation.get("uid")
        if uid:
            cited_uids.add(uid)
            is_verified = bool(citation.get("verified"))
            reason = citation.get("reason", "")
            if uid not in verified_map or is_verified:
                verified_map[uid] = {
                    "verified": is_verified,
                    "reason": reason
                }

    for provision in answer.get("retrieved_provisions", []) or []:
        uid = provision.get("uid", "")
        # Chỉ giữ lại điều khoản thực sự được LLM sử dụng/trích dẫn
        if uid not in cited_uids:
            continue

        display = provision.get("display_citation") or provision.get("article_title") or provision.get("uid", "")
        article_number = provision.get("article_index")
        if article_number is None:
            article_number = provision.get("article") or ""
            
        is_verified = bool(provision.get("validity", {}).get("status") == "verified")
        if uid in verified_map:
            is_verified = is_verified or verified_map[uid]["verified"]

        provisions.append(
            {
                "documentName": provision.get("document_title", ""),
                "articleNumber": f"Điều {article_number}" if article_number not in ("", None) else "",
                "text": provision.get("effective_text") or provision.get("text", ""),
                "verified": is_verified,
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


def _chunk_to_citations(answer: dict) -> list[dict]:
    citations = []
    verified_map = {}
    cited_uids = set()
    for citation in answer.get("citations", []) or []:
        uid = citation.get("uid")
        if uid:
            cited_uids.add(uid)
            is_verified = bool(citation.get("verified"))
            reason = citation.get("reason", "")
            if uid not in verified_map or is_verified:
                verified_map[uid] = {
                    "verified": is_verified,
                    "reason": reason
                }

    for provision in answer.get("retrieved_provisions", []) or []:
        uid = provision.get("uid", "")
        # Chỉ giữ lại trích dẫn thực sự được LLM sử dụng/trích dẫn
        if uid not in cited_uids:
            continue

        validity = provision.get("validity") or {}
        display = provision.get("display_citation") or provision.get("article_title") or provision.get("uid", "")
        
        is_verified = bool(validity.get("status") == "verified")
        reason = validity.get("reason", "")
        if uid in verified_map:
            is_verified = is_verified or verified_map[uid]["verified"]
            if verified_map[uid]["reason"]:
                reason = verified_map[uid]["reason"]

        citations.append(
            {
                "displayText": display,
                "uid": uid,
                "verified": is_verified,
                "reason": reason,
                "documentTitle": provision.get("document_title", ""),
            }
        )
    return citations


def _fallback_title(question: str) -> str:
    title = " ".join(question.strip().split())
    return title[:60] if title else "New conversation"


async def _generate_title(question: str, answer: str) -> tuple[str, str]:
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        return _fallback_title(question), "fallback"
    try:
        client = AsyncOpenAI(api_key=api_key)
        response = await client.chat.completions.create(
            model=os.getenv("OPENAI_TITLE_MODEL", os.getenv("OPENAI_MODEL", "gpt-4o-mini")),
            messages=[
                {
                    "role": "system",
                    "content": "Create a concise Vietnamese title for a legal QA conversation. Return only the title, maximum 8 words.",
                },
                {"role": "user", "content": f"Question: {question}\nAnswer: {answer[:1000]}"},
            ],
            temperature=0.2,
            max_tokens=32,
        )
        title = (response.choices[0].message.content or "").strip().strip('"')
        return (title[:120] or _fallback_title(question)), "ai"
    except Exception:
        logger.exception("QA title generation failed")
        return _fallback_title(question), "fallback"


def _message_response(row: dict) -> ChatMessageResponse:
    return ChatMessageResponse(
        id=row["id"],
        role=row["role"],
        content=row.get("content", ""),
        timestamp=row.get("created_at", ""),
        intents=row.get("intents") or [],
        provisions=row.get("provisions") or [],
        citations=row.get("citations") or [],
        tokenCount=row.get("token_count") or 0,
    )


@router.post("/chat")
async def qa_chat(request: ChatRequest, user: CurrentUser = Depends(get_current_user)):
    """
    QA chat endpoint with SSE streaming.

    Processes message through: intent → retrieval → answer → citation verification.
    Streams answer token-by-token.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message is required")

    store = get_chat_store()
    try:
        if request.conversationId:
            conversation = store.get_conversation(user.id, request.conversationId)
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
        else:
            if not request.tabId:
                raise HTTPException(status_code=400, detail="tabId is required for a new conversation")
            conversation = store.create_conversation(user.id, request.tabId)
        conversation_id = conversation["id"]
        user_message = store.insert_message(
            user_id=user.id,
            conversation_id=conversation_id,
            role="user",
            content=request.message,
            token_count=estimate_token_count(request.message),
        )
    except ChatStoreError as exc:
        logger.exception("QA persistence failed before pipeline")
        raise HTTPException(status_code=500, detail=str(exc))

    started = perf_counter()
    logger.info("QA HTTP request received conversation_id=%s message_chars=%d", conversation_id, len(request.message))

    try:
        payload = await answer_legal_question(request.message, conversation_id=conversation_id)
        answer_text = payload.get("answer", "")
        intents = _intent_chunks(payload)
        provisions = _chunk_to_provisions(payload)
        citations = _chunk_to_citations(payload)
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

    try:
        store.insert_message(
            user_id=user.id,
            conversation_id=conversation_id,
            role="assistant",
            content=answer_text,
            token_count=estimate_token_count(answer_text),
            citations=citations,
            provisions=provisions,
            intents=intents,
            metadata={"user_message_id": user_message["id"]},
        )
        if conversation.get("message_count", 0) == 0:
            title, source = await _generate_title(request.message, answer_text)
            store.update_title_if_fallback(user.id, conversation_id, title, source)
    except ChatStoreError as exc:
        logger.exception("QA persistence failed after pipeline")
        raise HTTPException(status_code=500, detail=str(exc))

    # Stream response
    return StreamingResponse(
        answer_stream(answer_text, conversation_id=conversation_id, intents=intents, provisions=provisions),
        media_type="text/event-stream",
    )


@router.post("/conversations")
async def create_conversation(request: CreateConversationRequest, user: CurrentUser = Depends(get_current_user)):
    """Create a new conversation."""
    if not request.tabId:
        raise HTTPException(status_code=400, detail="tabId is required")
    try:
        conversation = get_chat_store().create_conversation(user.id, request.tabId, request.title)
        return {"id": conversation["id"]}
    except ChatStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/conversations")
async def get_conversations(user: CurrentUser = Depends(get_current_user)):
    """List all conversations."""
    store = get_chat_store()
    try:
        summaries = []
        for conv in store.list_conversations(user.id):
            summaries.append(
                ConversationSummary(
                    id=conv["id"],
                    title=conv["title"],
                    lastMessage=store.last_message(user.id, conv["id"]),
                    createdAt=conv.get("created_at", ""),
                    lastMessageAt=conv.get("last_message_at"),
                    tabId=conv.get("tab_id"),
                )
            )
        return summaries
    except ChatStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/conversations/tab/{tab_id}", response_model=ConversationDetail)
async def get_tab_conversation(tab_id: str, user: CurrentUser = Depends(get_current_user)):
    """Load the active conversation for a browser tab."""
    store = get_chat_store()
    try:
        conversation = store.get_conversation_by_tab(user.id, tab_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        messages = [_message_response(row) for row in store.list_messages(user.id, conversation["id"])]
        return ConversationDetail(
            id=conversation["id"],
            title=conversation["title"],
            createdAt=conversation.get("created_at", ""),
            lastMessageAt=conversation.get("last_message_at"),
            messages=messages,
        )
    except ChatStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/conversations/{conv_id}", response_model=ConversationDetail)
async def get_conversation(conv_id: str, user: CurrentUser = Depends(get_current_user)):
    """Load a conversation and its ordered messages."""
    store = get_chat_store()
    try:
        conversation = store.get_conversation(user.id, conv_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        messages = [_message_response(row) for row in store.list_messages(user.id, conv_id)]
        return ConversationDetail(
            id=conversation["id"],
            title=conversation["title"],
            createdAt=conversation.get("created_at", ""),
            lastMessageAt=conversation.get("last_message_at"),
            messages=messages,
        )
    except ChatStoreError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.patch("/conversations/{conv_id}", response_model=ConversationSummary)
async def rename_conversation(conv_id: str, request: RenameConversationRequest, user: CurrentUser = Depends(get_current_user)):
    """Rename a conversation."""
    title = request.title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="Title is required")
    store = get_chat_store()
    try:
        conv = store.rename_conversation(user.id, conv_id, title)
        return ConversationSummary(
            id=conv["id"],
            title=conv["title"],
            lastMessage=store.last_message(user.id, conv["id"]),
            createdAt=conv.get("created_at", ""),
            lastMessageAt=conv.get("last_message_at"),
            tabId=conv.get("tab_id"),
        )
    except ChatStoreError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/conversations/{conv_id}")
async def delete_conversation(conv_id: str, user: CurrentUser = Depends(get_current_user)):
    """Soft-delete a conversation."""
    try:
        get_chat_store().soft_delete_conversation(user.id, conv_id)
    except ChatStoreError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {"status": "deleted"}
