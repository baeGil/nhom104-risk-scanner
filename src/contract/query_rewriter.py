"""
Contract clause query rewriting for legal hybrid retrieval.

Turns a contract clause into a structured search plan before retrieval.
The LLM path is preferred, with deterministic fallback behavior for tests
and degraded operation.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Optional

from src.contract.models import ContractClause
from src.llm.client import LLMClient, create_client
from src.llm.prompts import PromptTemplate


@dataclass
class LegalRetrievalPlan:
    original_text: str
    legal_issue: str = ""
    search_queries: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    expected_domains: list[str] = field(default_factory=list)
    title_hints: list[str] = field(default_factory=list)
    risk_type: str = "general"
    filters: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    source: str = "fallback"

    def normalized_queries(self) -> list[str]:
        queries = [self.original_text, *self.search_queries, self.legal_issue]
        seen: set[str] = set()
        result: list[str] = []
        for query in queries:
            value = (query or "").strip()
            key = value.lower()
            if value and key not in seen:
                result.append(value)
                seen.add(key)
        return result


class QueryRewriter:
    def __init__(self, llm_client: Optional[LLMClient] = None) -> None:
        self._llm = llm_client

    async def rewrite(self, clause: ContractClause | str) -> LegalRetrievalPlan:
        text = clause.text_content if isinstance(clause, ContractClause) else str(clause)
        clause_type = clause.clause_type if isinstance(clause, ContractClause) else ""

        try:
            llm = self._llm or create_client()
            prompt = PromptTemplate("legal_query_rewrite").render(
                clause_text=text,
                clause_type=clause_type,
            )
            raw = await llm.chat(prompt, temperature=0.0)
            plan = self.parse_llm_output(raw, original_text=text)
            if plan.search_queries or plan.keywords or plan.legal_issue:
                return plan
        except Exception:
            pass

        return self.fallback(text)

    def parse_llm_output(self, raw: Any, original_text: str) -> LegalRetrievalPlan:
        data = self._coerce_json(raw)
        if "retrieval_plan" in data and isinstance(data["retrieval_plan"], dict):
            data = data["retrieval_plan"]

        return LegalRetrievalPlan(
            original_text=str(data.get("original_text") or original_text),
            legal_issue=str(data.get("legal_issue") or ""),
            search_queries=self._coerce_str_list(data.get("search_queries")),
            keywords=self._coerce_str_list(data.get("keywords")),
            expected_domains=self._coerce_str_list(data.get("expected_domains")),
            title_hints=self._coerce_str_list(data.get("title_hints")),
            risk_type=str(data.get("risk_type") or "general"),
            filters=data.get("filters") if isinstance(data.get("filters"), dict) else {},
            confidence=float(data.get("confidence") or 0.0),
            source="llm",
        )

    def fallback(self, text: str) -> LegalRetrievalPlan:
        lowered = text.lower()
        issue = "rà soát điều khoản hợp đồng"
        risk_type = "general"
        keywords: list[str] = []
        domains = ["Bộ luật Dân sự"]

        if any(term in lowered for term in ["phạt", "vi phạm", "30%", "8%"]):
            issue = "mức phạt vi phạm hợp đồng"
            risk_type = "penalty_cap"
            keywords = ["phạt vi phạm", "mức phạt", "8%", "nghĩa vụ bị vi phạm"]
            domains = ["Luật Thương mại", "Bộ luật Dân sự"]
        elif any(term in lowered for term in ["chấm dứt", "đơn phương", "hủy bỏ"]):
            issue = "đơn phương chấm dứt hợp đồng"
            risk_type = "termination"
            keywords = ["chấm dứt hợp đồng", "đơn phương chấm dứt", "thông báo trước"]
            domains = ["Bộ luật Dân sự", "Luật Thương mại", "Bộ luật Lao động"]
        elif any(term in lowered for term in ["lương", "tiền lương", "phụ cấp", "bảo hiểm"]):
            issue = "tiền lương và nghĩa vụ bảo hiểm trong hợp đồng lao động"
            risk_type = "wage_benefits"
            keywords = ["tiền lương", "phụ cấp", "bảo hiểm xã hội", "người lao động"]
            domains = ["Bộ luật Lao động", "Luật Bảo hiểm xã hội"]
        elif any(term in lowered for term in ["bảo mật", "thông tin mật", "bí mật"]):
            issue = "nghĩa vụ bảo mật thông tin trong hợp đồng"
            risk_type = "confidentiality"
            keywords = ["bảo mật", "thông tin mật", "bí mật kinh doanh"]
            domains = ["Bộ luật Dân sự", "Luật Sở hữu trí tuệ"]
        elif any(term in lowered for term in ["tranh chấp", "tòa án", "trọng tài"]):
            issue = "giải quyết tranh chấp hợp đồng"
            risk_type = "dispute_resolution"
            keywords = ["giải quyết tranh chấp", "tòa án", "trọng tài", "thẩm quyền"]
            domains = ["Bộ luật Tố tụng dân sự", "Luật Trọng tài thương mại"]

        search_queries = [
            issue,
            *keywords,
            self._compact_text(text),
        ]

        return LegalRetrievalPlan(
            original_text=text,
            legal_issue=issue,
            search_queries=self._dedupe(search_queries),
            keywords=self._dedupe(keywords),
            expected_domains=domains,
            title_hints=domains,
            risk_type=risk_type,
            filters={},
            confidence=0.45,
            source="fallback",
        )

    def _coerce_json(self, raw: Any) -> dict[str, Any]:
        if isinstance(raw, dict):
            return raw
        if isinstance(raw, str):
            content = raw.strip()
            if content.startswith("```"):
                content = content.strip("`")
                if content.startswith("json"):
                    content = content[4:].strip()
            parsed = json.loads(content)
            return parsed if isinstance(parsed, dict) else {}
        return {}

    def _coerce_str_list(self, value: Any) -> list[str]:
        if isinstance(value, list):
            return self._dedupe(str(v).strip() for v in value if str(v).strip())
        if isinstance(value, str) and value.strip():
            return [value.strip()]
        return []

    def _compact_text(self, text: str, max_chars: int = 240) -> str:
        compacted = re.sub(r"\s+", " ", text).strip()
        return compacted[:max_chars]

    def _dedupe(self, values) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for value in values:
            item = str(value).strip()
            key = item.lower()
            if item and key not in seen:
                result.append(item)
                seen.add(key)
        return result
