"""
Data contracts for the Phase 5 legal QA pipeline.

The objects in this module are deliberately JSON-friendly so backend routes can
return them without reparsing natural-language answer text.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional

from src.contract.citations import LegalCitation
from src.llm.models import IntentClassification, SubQuery


VALIDITY_VERIFIED = "verified"
VALIDITY_LIKELY_CURRENT = "likely_current"
VALIDITY_UNKNOWN = "unknown"


@dataclass
class QAValidity:
    status: str = VALIDITY_UNKNOWN
    reason: str = "Validity has not been checked."
    evidence: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class QACitation:
    display_text: str
    uid: str = ""
    document_title: str = ""
    article: Optional[str] = None
    clause: Optional[str] = None
    point: Optional[str] = None
    text: str = ""
    verified: bool = False
    reason: str = ""

    @classmethod
    def from_raw(cls, raw: Any) -> "QACitation":
        if isinstance(raw, cls):
            return raw
        if isinstance(raw, LegalCitation):
            return cls(
                display_text=raw.display_text,
                uid=raw.uid,
                document_title=raw.document_title,
                article=raw.article,
                clause=raw.clause,
                point=raw.point,
                verified=raw.verified,
                reason=raw.reason,
            )
        if not isinstance(raw, dict):
            return cls(display_text=str(raw or ""))

        display = raw.get("display_text") or raw.get("text") or raw.get("citation") or raw.get("document") or ""
        return cls(
            display_text=str(display),
            uid=str(raw.get("uid") or ""),
            document_title=str(raw.get("document_title") or raw.get("document") or ""),
            article=_clean_optional(raw.get("article")),
            clause=_clean_optional(raw.get("clause")),
            point=_clean_optional(raw.get("point")),
            text=str(raw.get("text") or ""),
            verified=bool(raw.get("verified", False)),
            reason=str(raw.get("reason") or ""),
        )

    def to_legal_citation(self) -> LegalCitation:
        return LegalCitation(
            display_text=self.display_text,
            uid=self.uid,
            document_title=self.document_title,
            article=self.article,
            clause=self.clause,
            point=self.point,
            verified=self.verified,
            reason=self.reason,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class QARetrievedProvision:
    uid: str
    segment_type: str = "Article"
    text: str = ""
    display_citation: str = ""
    article_uid: str = ""
    article_index: Optional[int] = None
    article_title: str = ""
    clause_index: Optional[str] = None
    point_label: str = ""
    document_title: str = ""
    document_so_ky_hieu: str = ""
    document_type: str = ""
    score: float = 0.0
    strategy: str = ""
    validity: QAValidity = field(default_factory=QAValidity)
    effective_text: str = ""
    effective_text_status: str = "fallback"
    references_context: list[dict[str, Any]] = field(default_factory=list)
    modifies_context: list[dict[str, Any]] = field(default_factory=list)
    score_factors: dict[str, Any] = field(default_factory=dict)

    def to_citation(self) -> QACitation:
        article = str(self.article_index) if self.article_index is not None else None
        return QACitation(
            display_text=self.display_citation or self.article_title or self.uid,
            uid=self.uid,
            document_title=self.document_title,
            article=article,
            clause=self.clause_index,
            point=self.point_label or None,
            text=self.effective_text or self.text,
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["validity"] = self.validity.to_dict()
        return data


@dataclass
class QARetrievalResult:
    query: str
    sub_queries: list[SubQuery] = field(default_factory=list)
    provisions: list[QARetrievedProvision] = field(default_factory=list)
    retrieval_status: str = "ok"
    errors: list[str] = field(default_factory=list)
    rewritten_queries: dict[str, str] = field(default_factory=dict)
    query_debug: dict[str, dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "sub_queries": [asdict(sq) for sq in self.sub_queries],
            "provisions": [p.to_dict() for p in self.provisions],
            "retrieval_status": self.retrieval_status,
            "errors": list(self.errors),
            "rewritten_queries": dict(self.rewritten_queries),
            "query_debug": dict(self.query_debug),
        }


@dataclass
class QAAnswer:
    answer: str
    citations: list[QACitation] = field(default_factory=list)
    retrieved_provisions: list[QARetrievedProvision] = field(default_factory=list)
    intent: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    validity: QAValidity = field(default_factory=QAValidity)
    retrieval_status: str = "ok"
    warnings: list[str] = field(default_factory=list)
    raw_output: Any = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "answer": self.answer,
            "citations": [c.to_dict() for c in self.citations],
            "retrieved_provisions": [p.to_dict() for p in self.retrieved_provisions],
            "intent": self.intent,
            "confidence": self.confidence,
            "validity": self.validity.to_dict(),
            "retrieval_status": self.retrieval_status,
            "warnings": list(self.warnings),
            "raw_output": self.raw_output,
        }


@dataclass
class QAResponse:
    answer: QAAnswer
    citation_verifications: list[dict[str, Any]] = field(default_factory=list)
    citations_verified: bool = False
    conversation_id: str = ""
    domain: str = "QA"
    unsupported: bool = False

    def to_dict(self) -> dict[str, Any]:
        data = self.answer.to_dict()
        data["citation_verifications"] = list(self.citation_verifications)
        data["citations_verified"] = self.citations_verified
        data["conversation_id"] = self.conversation_id
        data["domain"] = self.domain
        data["unsupported"] = self.unsupported
        return data


def intent_to_dict(classification: IntentClassification) -> dict[str, Any]:
    return {
        "conversation_id": classification.conversation_id,
        "turn_number": classification.turn_number,
        "domain": classification.domain,
        "confidence": classification.confidence,
        "intents": [asdict(intent) for intent in classification.intents],
        "sub_queries": [asdict(query) for query in classification.sub_queries],
        "context_references": dict(classification.context_references),
        "routing": dict(classification.routing),
    }


def _clean_optional(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"none", "null"}:
        return None
    if text.lower().startswith("điều "):
        return text.split(maxsplit=1)[1]
    if text.lower().startswith("khoản "):
        return text.split(maxsplit=1)[1]
    if text.lower().startswith("điểm "):
        return text.split(maxsplit=1)[1]
    return text
