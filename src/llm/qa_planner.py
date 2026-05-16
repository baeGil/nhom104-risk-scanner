"""QA-first planning helpers for T5.2 retrieval."""
from __future__ import annotations

import re
from dataclasses import replace

from src.llm.models import IntentClassification, SubIntent, SubQuery


HYBRID_INTENTS = {"TOPIC", "SEARCH", "SCENARIO", "CHECKLIST", "NUMERIC"}
DIRECT_INTENTS = {"LOOKUP"}
VALIDITY_INTENTS = {"VALIDITY"}
COMPARISON_INTENTS = {"COMPARISON"}
DIRECT_LOOKUP_REFERENCE_RE = re.compile(
    r"(?i)(?:\bđiều\s+\d+|\bkhoản\s+\d+\s+điều\s+\d+|\bđiểm\s+[a-z]\s+khoản\s+\d+\s+điều\s+\d+)"
)
DIRECT_LOOKUP_SIGNAL_RE = re.compile(
    r"(?i)(?:\bđiều\s+(?:\d+|thứ|đầu|cuối|này|đó)\b|\bkhoản\b|\bđiểm\b)"
)

ALLOWED_STRATEGIES = {"direct_lookup", "hybrid_search", "validity_check", "comparison"}
ALLOWED_REQUIREMENTS = {
    "legal_provision",
    "effective_text",
    "document_metadata",
    "conversation_context",
    "contract_context",
    "citation_validation",
    "amendment_history",
}

STRATEGY_ALIASES = {
    "lookup": "direct_lookup",
    "direct": "direct_lookup",
    "direct_lookup": "direct_lookup",
    "vector_search": "hybrid_search",
    "semantic_search": "hybrid_search",
    "graph_traversal": "hybrid_search",
    "hybrid_search": "hybrid_search",
    "search": "hybrid_search",
    "topic": "hybrid_search",
    "validity": "validity_check",
    "validity_check": "validity_check",
    "currentity": "validity_check",
    "comparison": "comparison",
}


def plan_qa_sub_queries(classification: IntentClassification, original_query: str = "") -> list[SubQuery]:
    """Normalize intent analysis output into Phase 5 QA retrieval strategies."""
    planned = [_normalize_sub_query(query) for query in classification.sub_queries]
    if planned:
        return planned

    return [_sub_query_from_intent(intent, original_query) for intent in classification.intents]


def is_supported_qa_domain(classification: IntentClassification) -> bool:
    return classification.domain.upper() == "QA"


def _normalize_sub_query(query: SubQuery) -> SubQuery:
    intent = query.intent.upper()
    strategy = normalize_retrieval_strategy(query.retrieval_strategy, intent)
    requires = normalize_requires(query.requires, intent, strategy)

    if intent in HYBRID_INTENTS or strategy == "hybrid_search":
        strategy = "hybrid_search"
    elif intent in DIRECT_INTENTS:
        strategy = "direct_lookup" if _has_direct_lookup_reference(query.query) else "hybrid_search"
    elif intent in VALIDITY_INTENTS:
        strategy = "validity_check"
    elif intent in COMPARISON_INTENTS:
        strategy = "comparison"

    if "legal_provision" not in requires:
        requires.append("legal_provision")
    if intent in DIRECT_INTENTS | HYBRID_INTENTS | COMPARISON_INTENTS and "effective_text" not in requires:
        requires.append("effective_text")
    if intent in VALIDITY_INTENTS and "document_metadata" not in requires:
        requires.append("document_metadata")

    return replace(query, intent=intent, retrieval_strategy=strategy, requires=requires)


def _sub_query_from_intent(intent: SubIntent, original_query: str) -> SubQuery:
    intent_type = intent.type.upper()
    extracted = intent.extracted
    query = _query_text_from_extracted(extracted) or original_query

    if intent_type in DIRECT_INTENTS:
        strategy = "direct_lookup" if _has_direct_lookup_reference(query, extracted) else "hybrid_search"
    elif intent_type in VALIDITY_INTENTS:
        strategy = "validity_check"
    else:
        strategy = "hybrid_search"

    requires = ["legal_provision"]
    if strategy != "validity_check":
        requires.append("effective_text")

    return SubQuery(
        intent=intent_type,
        query=query,
        retrieval_strategy=strategy,
        requires=requires,
    )


def normalize_retrieval_strategy(strategy: str, intent: str) -> str:
    raw = (strategy or "").strip().lower()
    if raw in STRATEGY_ALIASES:
        return STRATEGY_ALIASES[raw]
    if raw in ALLOWED_STRATEGIES:
        return raw
    if intent in DIRECT_INTENTS:
        return "direct_lookup"
    if intent in VALIDITY_INTENTS:
        return "validity_check"
    if intent in COMPARISON_INTENTS:
        return "comparison"
    return "hybrid_search"


def _has_direct_lookup_reference(query: str, extracted: dict | None = None) -> bool:
    """Direct lookup needs an article reference or enough citation signal for rewrite."""
    extracted = extracted or {}
    if extracted.get("article_number"):
        return True
    text = query or ""
    return bool(DIRECT_LOOKUP_REFERENCE_RE.search(text) or DIRECT_LOOKUP_SIGNAL_RE.search(text))


def normalize_requires(requires: list[str], intent: str, strategy: str) -> list[str]:
    normalized: list[str] = []
    for requirement in requires:
        normalized_requirement = _normalize_requirement(requirement)
        if normalized_requirement and normalized_requirement not in normalized:
            normalized.append(normalized_requirement)

    if intent in VALIDITY_INTENTS or strategy == "validity_check":
        defaults = ["legal_provision", "document_metadata", "effective_text"]
    elif intent in COMPARISON_INTENTS or strategy == "comparison":
        defaults = ["legal_provision", "effective_text"]
    else:
        defaults = ["legal_provision", "effective_text"]

    for requirement in defaults:
        if requirement not in normalized:
            normalized.append(requirement)

    return [item for item in normalized if item in ALLOWED_REQUIREMENTS]


def _normalize_requirement(requirement: str) -> str | None:
    raw = (requirement or "").strip().lower()
    if not raw:
        return None
    if raw in ALLOWED_REQUIREMENTS:
        return raw
    if "hội thoại" in raw or "context" in raw or "ngữ cảnh" in raw:
        return "conversation_context"
    if "hợp đồng" in raw:
        return "contract_context"
    if "hiệu lực" in raw or "sửa đổi" in raw or "bãi bỏ" in raw or "amend" in raw:
        return "effective_text"
    if "cấu trúc" in raw or "metadata" in raw or "văn bản" in raw or "document" in raw:
        return "document_metadata"
    if "trích dẫn" in raw or "citation" in raw:
        return "citation_validation"
    if "lịch sử sửa đổi" in raw or "amendment" in raw:
        return "amendment_history"
    if "quy định" in raw or "provision" in raw or "điều" in raw or "khoản" in raw or "điểm" in raw:
        return "legal_provision"
    return None


def _query_text_from_extracted(extracted: dict) -> str:
    article = extracted.get("article_number")
    document = extracted.get("document_name") or extracted.get("so_ky_hieu") or extracted.get("topic")
    year = extracted.get("year")
    parts = []
    if article:
        parts.append(f"Điều {article}")
    if document:
        parts.append(str(document))
    if year:
        parts.append(str(year))
    return " ".join(parts).strip()
