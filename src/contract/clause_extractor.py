"""
Contract Clause Extractor — T4.2

LLM-based extraction of clauses from contract Markdown text.
Generates embeddings for each extracted clause.

Usage:
    from src.contract.clause_extractor import ClauseExtractor
    from src.contract.parser import ContractParser

    parser = ContractParser()
    contract = parser.parse("path/to/contract.pdf")

    extractor = ClauseExtractor()
    clauses = await extractor.extract(contract)
"""
from __future__ import annotations

import json
import uuid
from typing import Any, Optional

from src.llm.client import LLMClient, create_client
from src.llm.prompts import PromptTemplate
from src.contract.models import Contract, ContractClause
from src.contract.mock_bridge import create_embedding_service


class ClauseExtractor:
    """
    Extract clauses from contract documents using LLM.

    Uses the clause_extraction prompt template to identify and structure
    individual clauses from contract Markdown text.
    """

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        generate_embeddings: bool = True,
    ) -> None:
        self._llm = llm_client or create_client()
        self._generate_embeddings = generate_embeddings
        self._embedding_service = create_embedding_service() if generate_embeddings else None

    async def extract(self, contract: Contract) -> list[ContractClause]:
        """
        Extract clauses from a contract document.

        Args:
            contract: Parsed contract with redacted_text

        Returns:
            List of ContractClause objects with embeddings
        """
        # Build prompt
        prompt = self._build_prompt(contract.redacted_text)

        # Call LLM
        raw_result = await self._llm.chat(prompt)

        # Parse output
        clauses = self._parse_llm_output(raw_result, contract.id)

        # Generate embeddings
        if self._generate_embeddings and clauses:
            await self._generate_clause_embeddings(clauses)

        return clauses

    def _build_prompt(self, contract_text: str) -> str:
        """Build clause extraction prompt."""
        template = PromptTemplate("clause_extraction")
        return template.render(contract_text=contract_text)

    def _parse_llm_output(self, raw: Any, contract_id: str) -> list[ContractClause]:
        """
        Parse LLM output into ContractClause objects.

        Handles both dict and str responses.
        """
        # Handle string response (needs JSON parsing)
        if isinstance(raw, str):
            # Strip markdown code blocks if present
            if "```" in raw:
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            raw = json.loads(raw.strip())

        # Handle list of clauses
        if isinstance(raw, list):
            clauses_data = raw
        elif isinstance(raw, dict) and "clauses" in raw:
            clauses_data = raw["clauses"]
        else:
            clauses_data = raw if isinstance(raw, list) else []

        clauses = []
        for i, clause_data in enumerate(clauses_data, 1):
            clause = ContractClause(
                id=str(uuid.uuid4()),
                index=i,
                clause_type=clause_data.get("clause_type", "khác"),
                text_content=clause_data.get("text_content", ""),
                parties_involved=clause_data.get("parties_involved", []),
                obligations=clause_data.get("obligations", []),
                amount=clause_data.get("amount"),
                deadline=clause_data.get("deadline"),
            )
            clauses.append(clause)

        return clauses

    async def _generate_clause_embeddings(self, clauses: list[ContractClause]) -> None:
        """Generate embeddings for all clauses in batch."""
        if not self._embedding_service or not clauses:
            return

        texts = [c.text_content for c in clauses]
        embeddings = await self._embedding_service.embed_batch(texts)

        for clause, embedding in zip(clauses, embeddings):
            clause.embedding = embedding
