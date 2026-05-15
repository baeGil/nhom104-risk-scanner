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
        # Handle string response
        if isinstance(raw, str):
            if "```" in raw:
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            raw = json.loads(raw.strip())

        # Parse violations
        violations = []
        for v in raw.get("violations", []):
            violations.append(ComplianceViolation(
                clause=v.get("clause", ""),
                description=v.get("description", ""),
                citation=v.get("citation", ""),
                severity=v.get("severity", "medium"),
            ))

        return ComplianceResult(
            violations=violations,
            risks=raw.get("risks", []),
            suggestions=raw.get("suggestions", []),
            citations=raw.get("citations", []),
        )
