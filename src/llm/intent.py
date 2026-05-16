"""
Intent Analyzer — T5.1 Core (Người C)

Analyzes user queries to determine domain, intent, and extract entities.
Uses LLM with structured prompt for consistent output.
"""
from __future__ import annotations

from typing import Any, Optional

from .models import IntentClassification, SubIntent, SubQuery, ConversationContext
from .client import LLMClient, create_client
from .prompts import PromptTemplate
from .qa_planner import normalize_retrieval_strategy, normalize_requires


class IntentAnalyzer:
    """
    Analyzes user queries for domain, intent, and entity extraction.
    """

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        confidence_threshold: float = 0.7,
        clarification_threshold: float = 0.4,
    ) -> None:
        self._llm = llm_client or create_client()
        self._confidence_threshold = confidence_threshold
        self._clarification_threshold = clarification_threshold

    async def analyze(
        self,
        query: str,
        context: Optional[ConversationContext] = None,
    ) -> IntentClassification:
        conversation_id = context.conversation_id if context else "conv_new"
        turn_number = (context.turn_number + 1) if context else 1

        result = await self._analyze_with_llm(query, conversation_id, turn_number, context)

        result.is_unknown = result.confidence < self._clarification_threshold
        result.clarification_needed = (
            self._clarification_threshold <= result.confidence < self._confidence_threshold
        )

        if result.clarification_needed:
            result.fallback_response = "Bạn có thể nói rõ hơn không?"
        elif result.is_unknown:
            result.fallback_response = "Tôi chưa hiểu rõ câu hỏi của bạn. Bạn đang hỏi về văn bản pháp luật, hợp đồng, hay chủ đề khác?"

        return result

    async def _analyze_with_llm(
        self,
        query: str,
        conversation_id: str,
        turn_number: int,
        context: Optional[ConversationContext],
    ) -> IntentClassification:
        history = []
        if context:
            for turn in context.history[-5:]:
                history.append(f"User: {turn['user_input']} → {turn['domain']}")

        template = PromptTemplate("intent_analysis")
        prompt = template.render(
            user_input=query,
            conversation_history="\n".join(history) if history else "No previous turns",
        )

        raw_result = await self._llm.chat(prompt)

        return self._parse_llm_result(raw_result, query, conversation_id, turn_number)

    def _parse_llm_result(
        self,
        raw: dict[str, Any],
        query: str,
        conversation_id: str,
        turn_number: int,
    ) -> IntentClassification:
        intents = []
        for intent_data in raw.get("intents", []):
            intent = SubIntent(
                type=intent_data.get("type", "LOOKUP"),
                confidence=intent_data.get("confidence", 0.5),
                query_span=intent_data.get("query_span", [0, len(query)]),
                extracted=intent_data.get("extracted", {}),
            )
            intents.append(intent)

        sub_queries = []
        for sq_data in raw.get("sub_queries", []):
            intent_type = str(sq_data.get("intent", "LOOKUP")).upper()
            strategy = normalize_retrieval_strategy(
                str(sq_data.get("retrieval_strategy", "direct_lookup")),
                intent_type,
            )
            requires = normalize_requires(list(sq_data.get("requires", [])), intent_type, strategy)
            sub_queries.append(SubQuery(
                intent=intent_type,
                query=sq_data.get("query", query),
                retrieval_strategy=strategy,
                requires=requires,
            ))

        return IntentClassification(
            conversation_id=raw.get("conversation_id", conversation_id),
            turn_number=raw.get("turn_number", turn_number),
            domain=raw.get("domain", "QA"),
            confidence=raw.get("confidence", 0.5),
            intents=intents,
            sub_queries=sub_queries,
            context_references=raw.get("context_references", {}),
            routing=raw.get("routing", {}),
        )
