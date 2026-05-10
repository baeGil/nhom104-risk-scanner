"""
Data models for the LLM module.

IntentClassification: Output of IntentAnalyzer
SubIntent: Individual intent within a classification
SubQuery: Decomposed sub-query for parallel retrieval
ConversationContext: Conversation state tracking
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Intent Analysis Models
# ---------------------------------------------------------------------------

@dataclass
class SubIntent:
    """
    Individual intent within a multi-intent classification.

    Attributes:
        type: Intent type (LOOKUP, TOPIC, VALIDITY, COMPARISON, CHECKLIST, NUMERIC, SCENARIO, SEARCH)
        confidence: Confidence score (0-1)
        query_span: [start, end] character positions in original query
        extracted: Extracted entities specific to this intent
    """
    type: str
    confidence: float
    query_span: list[int] = field(default_factory=lambda: [0, 0])
    extracted: dict[str, Any] = field(default_factory=dict)


@dataclass
class SubQuery:
    """
    Decomposed sub-query for parallel retrieval by T5.2.

    Attributes:
        intent: Intent type this sub-query addresses
        query: Natural language query for retrieval
        retrieval_strategy: Strategy name for T5.2 (direct_lookup, validity_check, etc.)
        requires: List of data sources needed (contract_context, legal_provision, effective_text)
    """
    intent: str
    query: str
    retrieval_strategy: str
    requires: list[str] = field(default_factory=list)


@dataclass
class IntentClassification:
    """
    Output of IntentAnalyzer.analyze().

    Attributes:
        conversation_id: Unique conversation identifier
        turn_number: Current turn in conversation
        domain: QA | CONTRACT_REVIEW | CONTRACT_QA | EXPLAIN | CHITCHAT
        confidence: Overall classification confidence (0-1)
        intents: List of detected intents (multi-intent support)
        sub_queries: Decomposed sub-queries for T5.2
        context_references: References to conversation context (contract_id, clause_index, etc.)
        routing: Routing information for pipeline selection
        is_unknown: True if confidence < threshold
        clarification_needed: True if ambiguous (0.4 <= confidence < 0.7)
        fallback_response: Suggested response if unknown/ambiguous
    """
    conversation_id: str
    turn_number: int
    domain: str
    confidence: float
    intents: list[SubIntent] = field(default_factory=list)
    sub_queries: list[SubQuery] = field(default_factory=list)
    context_references: dict[str, Any] = field(default_factory=dict)
    routing: dict[str, Any] = field(default_factory=dict)
    is_unknown: bool = False
    clarification_needed: bool = False
    fallback_response: Optional[str] = None


# ---------------------------------------------------------------------------
# Conversation Context Models
# ---------------------------------------------------------------------------

@dataclass
class ConversationContext:
    """
    Tracks conversation state for follow-up resolution.

    Attributes:
        conversation_id: Unique conversation identifier
        turn_number: Current turn number (1-based)
        history: List of previous (user_input, intent_classification) pairs
        referenced_contracts: List of contract_ids discussed in this conversation
        last_entities: Entities from last turn (for follow-up resolution)
        created_at: Conversation creation time
        last_active: Last activity time (for TTL)
        max_turns: Maximum turns before expiration
        ttl_minutes: Time-to-live in minutes
    """
    conversation_id: str
    turn_number: int = 0
    history: list[dict[str, Any]] = field(default_factory=list)
    referenced_contracts: list[str] = field(default_factory=list)
    last_entities: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    max_turns: int = 50
    ttl_minutes: int = 60

    def is_expired(self) -> bool:
        """Check if conversation has expired."""
        if self.turn_number >= self.max_turns:
            return True
        if datetime.now() - self.last_active > timedelta(minutes=self.ttl_minutes):
            return True
        return False

    def add_turn(self, user_input: str, classification: IntentClassification) -> None:
        """Add a turn to conversation history."""
        self.turn_number += 1
        self.history.append({
            "user_input": user_input,
            "domain": classification.domain,
            "intents": [i.type for i in classification.intents],
            "entities": classification.context_references,
        })
        self.last_active = datetime.now()
        # Update referenced contracts
        if "contract_id" in classification.context_references:
            cid = classification.context_references["contract_id"]
            if cid not in self.referenced_contracts:
                self.referenced_contracts.append(cid)
        # Store last entities for follow-up resolution
        self.last_entities = classification.context_references
