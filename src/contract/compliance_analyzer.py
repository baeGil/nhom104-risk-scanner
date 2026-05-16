"""
Compliance Analyzer — T4.4

Analyzes contract clauses against matched legal provisions using LLM.
Generates structured compliance reports with violations, risks, suggestions, and citations.

Usage:
    from src.contract.compliance_analyzer import ComplianceAnalyzer
    analyzer = ComplianceAnalyzer()
    result = await analyzer.analyze(clause, matched_provisions)
"""
from __future__ import annotations

import json
from typing import Any, Optional

from src.llm.client import LLMClient, create_client
from src.llm.prompts import PromptTemplate
from src.contract.models import (
    ContractClause,
    ComplianceResult,
    ComplianceViolation,
)
from src.contract.matcher import MatchedProvision


class ComplianceAnalyzer:
    """
    Analyze contract clause compliance against legal provisions.

    Uses LLM with context including:
    - Clause text
    - Matched legal provisions (EffectiveArticle text)
    - Amendment history
    - Document metadata
    """

    def __init__(self, llm_client: Optional[LLMClient] = None) -> None:
        self._llm = llm_client or create_client()

    async def analyze(
        self,
        clause: ContractClause,
        provisions: list[MatchedProvision],
        amendment_history: Optional[list[dict]] = None,
    ) -> ComplianceResult:
        """
        Analyze compliance for a single clause.

        Args:
            clause: ContractClause to analyze
            provisions: Matched legal provisions
            amendment_history: Optional amendment history

        Returns:
            ComplianceResult with violations, risks, suggestions, citations
        """
        # Build prompt
        prompt = self._build_prompt(clause, provisions, amendment_history)

        # Call LLM
        raw_result = await self._llm.chat(prompt)

        # Parse output
        return self._parse_llm_output(raw_result)

    async def analyze_all(
        self,
        clauses: list[ContractClause],
        all_provisions: dict[str, list[MatchedProvision]],
    ) -> dict[str, ComplianceResult]:
        """
        Analyze compliance for multiple clauses.

        Args:
            clauses: List of ContractClause objects
            all_provisions: Dict mapping clause_id to matched provisions

        Returns:
            Dict mapping clause_id to ComplianceResult
        """
        results = {}
        for clause in clauses:
            provisions = all_provisions.get(clause.id, [])
            results[clause.id] = await self.analyze(clause, provisions)
        return results

    def _build_prompt(
        self,
        clause: ContractClause,
        provisions: list[MatchedProvision],
        amendment_history: Optional[list[dict]] = None,
    ) -> str:
        """Build compliance analysis prompt."""
        # Format provisions
        provisions_text = ""
        for i, prov in enumerate(provisions, 1):
            display_citation = getattr(prov, "display_citation", "") or prov.article_title
            segment_uid = getattr(prov, "segment_uid", "") or prov.article_uid
            validity_signal = getattr(prov, "validity_signal", "latest_known")
            provisions_text += f"\n{i}. {display_citation}\n"
            provisions_text += f"   uid: {segment_uid}\n"
            provisions_text += f"   document: {prov.document_title}\n"
            provisions_text += f"   validity_signal: {validity_signal}\n"
            provisions_text += f"   {prov.effective_text or prov.article_text}\n"

        # Format amendment history
        amendment_text = "Không có lịch sử sửa đổi."
        if amendment_history:
            amendment_text = "\n".join(
                f"- {a.get('source', '')}: {a.get('action', '')} ({a.get('date', '')})"
                for a in amendment_history
            )

        template = PromptTemplate("compliance_analysis")
        return template.render(
            clause_text=clause.text_content,
            legal_provisions=provisions_text,
            amendment_history=amendment_text,
        )

    def _parse_llm_output(self, raw: Any) -> ComplianceResult:
        """Parse LLM output into ComplianceResult."""
        raw = self._coerce_json_object(raw)

        # Parse violations
        violations = []
        for v in self._coerce_violation_list(raw.get("violations")):
            violations.append(ComplianceViolation(
                clause=v.get("clause", ""),
                description=v.get("description", ""),
                citation=v.get("citation", ""),
                severity=v.get("severity", "medium"),
            ))

        return ComplianceResult(
            violations=violations,
            risks=self._coerce_str_list(raw.get("risks"), field_name="risks"),
            suggestions=self._coerce_str_list(raw.get("suggestions"), field_name="suggestions"),
            citations=self._coerce_dict_list(raw.get("citations"), field_name="citations"),
        )

    def _coerce_json_object(self, raw: Any) -> dict[str, Any]:
        """Normalize LLM output to a JSON object."""
        if isinstance(raw, dict):
            return raw

        if isinstance(raw, str):
            raw = raw.strip()
            if raw.startswith("```"):
                segments = raw.split("```")
                if len(segments) >= 3:
                    raw = segments[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()

            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Compliance analyzer expected JSON object from LLM, got non-JSON text: {raw[:200]}") from exc

            if isinstance(parsed, dict):
                return parsed
            raise ValueError(f"Compliance analyzer expected JSON object from LLM, got {type(parsed).__name__}")

        raise ValueError(f"Compliance analyzer expected dict or JSON string from LLM, got {type(raw).__name__}")

    def _coerce_str_list(self, value: Any, field_name: str) -> list[str]:
        """Normalize optional list[str] fields from LLM output."""
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError(f"Compliance analyzer expected '{field_name}' to be a list, got {type(value).__name__}")
        return [str(item) for item in value]

    def _coerce_dict_list(self, value: Any, field_name: str) -> list[dict[str, Any]]:
        """Normalize optional list[dict] fields from LLM output."""
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError(f"Compliance analyzer expected '{field_name}' to be a list, got {type(value).__name__}")

        normalized: list[dict[str, Any]] = []
        for item in value:
            if not isinstance(item, dict):
                raise ValueError(
                    f"Compliance analyzer expected items in '{field_name}' to be objects, got {type(item).__name__}"
                )
            normalized.append(item)
        return normalized

    def _coerce_violation_list(self, value: Any) -> list[dict[str, Any]]:
        """Normalize violations from either object or string format."""
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError(f"Compliance analyzer expected 'violations' to be a list, got {type(value).__name__}")

        normalized: list[dict[str, Any]] = []
        for item in value:
            if isinstance(item, dict):
                normalized.append(item)
                continue
            if isinstance(item, str):
                normalized.append(
                    {
                        "clause": "",
                        "description": item,
                        "citation": "",
                        "severity": "medium",
                    }
                )
                continue
            raise ValueError(
                f"Compliance analyzer expected items in 'violations' to be objects or strings, got {type(item).__name__}"
            )
        return normalized
