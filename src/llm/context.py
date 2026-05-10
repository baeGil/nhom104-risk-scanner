"""
Conversation Manager — T5.1 (Người C)

Manages conversation state for follow-up resolution.
In-memory storage with TTL and max-turns expiration.
"""
from __future__ import annotations

import uuid
from typing import Any, Optional

from .models import ConversationContext, IntentClassification


class ConversationManager:
    """
    Manages conversation contexts with in-memory storage.

    Usage:
        manager = ConversationManager()
        ctx = manager.create_context()
        manager.add_turn(ctx.conversation_id, user_input, classification)
        resolved = manager.resolve_reference(ctx.conversation_id, "điều khoản đó")
    """

    def __init__(
        self,
        max_turns: int = 50,
        ttl_minutes: int = 60,
        max_conversations: int = 1000,
    ) -> None:
        """
        Initialize ConversationManager.

        Args:
            max_turns: Maximum turns per conversation
            ttl_minutes: Time-to-live in minutes
            max_conversations: Maximum concurrent conversations (LRU eviction)
        """
        self._contexts: dict[str, ConversationContext] = {}
        self._max_turns = max_turns
        self._ttl_minutes = ttl_minutes
        self._max_conversations = max_conversations

    def create_context(
        self,
        conversation_id: Optional[str] = None,
    ) -> ConversationContext:
        """
        Create new conversation context.

        Args:
            conversation_id: Custom ID (auto-generated if None)

        Returns:
            New ConversationContext
        """
        cid = conversation_id or f"conv_{uuid.uuid4().hex[:8]}"
        ctx = ConversationContext(
            conversation_id=cid,
            max_turns=self._max_turns,
            ttl_minutes=self._ttl_minutes,
        )
        self._contexts[cid] = ctx
        self._evict_if_needed()
        return ctx

    def get_context(self, conversation_id: str) -> Optional[ConversationContext]:
        """Get conversation context by ID."""
        ctx = self._contexts.get(conversation_id)
        if ctx and ctx.is_expired():
            del self._contexts[conversation_id]
            return None
        return ctx

    def add_turn(
        self,
        conversation_id: str,
        user_input: str,
        classification: IntentClassification,
    ) -> Optional[ConversationContext]:
        """
        Add a turn to conversation.

        Args:
            conversation_id: Conversation ID
            user_input: User's message
            classification: Intent classification result

        Returns:
            Updated context or None if expired
        """
        ctx = self.get_context(conversation_id)
        if ctx is None:
            ctx = self.create_context(conversation_id)
        ctx.add_turn(user_input, classification)
        return ctx

    def resolve_reference(
        self,
        conversation_id: str,
        reference: str,
    ) -> Optional[dict[str, Any]]:
        """
        Resolve follow-up reference to previous entity.

        Handles references like:
        - "điều khoản đó" → last discussed clause
        - "luật này" → last discussed document
        - "hợp đồng trên" → last discussed contract

        Args:
            conversation_id: Conversation ID
            reference: Reference phrase

        Returns:
            Resolved entity dict or None
        """
        ctx = self.get_context(conversation_id)
        if ctx is None:
            return None

        reference_lower = reference.lower()
        last_entities = ctx.last_entities

        # Map reference phrases to entity keys
        reference_map = {
            "điều khoản đó": "clause",
            "điều đó": "article",
            "luật này": "document",
            "văn bản này": "document",
            "nghị định này": "document",
            "hợp đồng trên": "contract",
            "hợp đồng này": "contract",
            "nó": None,  # Context-dependent
        }

        for phrase, entity_type in reference_map.items():
            if phrase in reference_lower:
                if entity_type and entity_type in last_entities:
                    return last_entities[entity_type]
                return last_entities  # Return all last entities

        return last_entities if last_entities else None

    def get_referenced_contracts(self, conversation_id: str) -> list[str]:
        """Get list of contracts referenced in conversation."""
        ctx = self.get_context(conversation_id)
        return ctx.referenced_contracts if ctx else []

    def delete_context(self, conversation_id: str) -> bool:
        """Delete conversation context."""
        if conversation_id in self._contexts:
            del self._contexts[conversation_id]
            return True
        return False

    def clear_expired(self) -> int:
        """Remove all expired conversations. Returns count removed."""
        expired = [
            cid for cid, ctx in self._contexts.items()
            if ctx.is_expired()
        ]
        for cid in expired:
            del self._contexts[cid]
        return len(expired)

    def _evict_if_needed(self) -> None:
        """Evict oldest conversations if over limit."""
        if len(self._contexts) > self._max_conversations:
            # Sort by last_active, remove oldest
            sorted_ctx = sorted(
                self._contexts.items(),
                key=lambda x: x[1].last_active,
            )
            to_remove = len(self._contexts) - self._max_conversations
            for cid, _ in sorted_ctx[:to_remove]:
                del self._contexts[cid]

    @property
    def active_count(self) -> int:
        """Number of active conversations."""
        return len(self._contexts)
