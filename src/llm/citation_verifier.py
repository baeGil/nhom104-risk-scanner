"""
Citation Verifier — T4.5 / T5.4

Automated verification of legal citations against Neo4j graph.
Parses Vietnamese legal citation format and verifies against graph nodes.

Usage:
    from src.llm.citation_verifier import CitationVerifier
    verifier = CitationVerifier()
    results = await verifier.verify(citations)
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from neo4j import GraphDatabase

from src.config import NEO4J_URI, NEO4J_TIMEOUT, neo4j_auth


@dataclass
class ParsedCitation:
    """
    Parsed legal citation.

    Attributes:
        raw_text: Original citation text
        article_number: Article number (Điều X)
        clause_number: Clause number (Khoản Y), optional
        point_letter: Point letter (Điểm Z), optional
        document_type: Luật, Nghị định, Thông tư
        so_ky_hieu: Normalized document identifier
    """
    raw_text: str
    article_number: Optional[int] = None
    clause_number: Optional[int] = None
    point_letter: Optional[str] = None
    document_type: str = ""
    so_ky_hieu: str = ""


@dataclass
class VerificationResult:
    """
    Result of citation verification.

    Attributes:
        citation: Original ParsedCitation
        verified: True if citation resolves to existing Neo4j node
        is_current: True if the provision is currently effective
        reason: Explanation if not verified
        article_uid: Resolved Article UID if found
    """
    citation: ParsedCitation
    verified: bool = False
    is_current: bool = False
    reason: str = ""
    article_uid: str = ""


class CitationVerifier:
    """
    Verify legal citations against Neo4j graph.

    Parses Vietnamese legal citation format:
    "Điều {N} khoản {K} {Loại_văn_bản} {so_ky_hieu}"
    """

    # Citation pattern: Điều N (khoản K)? (điểm L)? (Luật|NĐ|TT) (so_ky_hieu)?
    CITATION_PATTERN = re.compile(
        r"Điều\s+(\d+)"
        r"(?:\s+khoản\s+(\d+))?"
        r"(?:\s+điểm\s+([a-z]))?"
        r"(?:\s+(Luật|Bộ luật|Nghị định|Thông tư))?"
        r"(?:\s+([\w\-/]+))?",
        re.IGNORECASE,
    )

    def __init__(self) -> None:
        self._driver = GraphDatabase.driver(NEO4J_URI, auth=neo4j_auth())

    async def verify(self, citation_text: str) -> VerificationResult:
        """
        Verify a single citation.

        Args:
            citation_text: Citation string to verify

        Returns:
            VerificationResult with verified status and reason
        """
        parsed = self.parse_citation(citation_text)
        return await self._verify_parsed(parsed)

    async def verify_batch(self, citations: list[str]) -> list[VerificationResult]:
        """
        Verify multiple citations.

        Args:
            citations: List of citation strings

        Returns:
            List of VerificationResult for each citation
        """
        return [await self.verify(c) for c in citations]

    def parse_citation(self, citation_text: str) -> ParsedCitation:
        """
        Parse a Vietnamese legal citation.

        Args:
            citation_text: e.g., "Điều 301 khoản 2 Luật Thương mại 2005"

        Returns:
            ParsedCitation with extracted fields
        """
        match = self.CITATION_PATTERN.search(citation_text)
        if not match:
            return ParsedCitation(raw_text=citation_text)

        return ParsedCitation(
            raw_text=citation_text,
            article_number=int(match.group(1)),
            clause_number=int(match.group(2)) if match.group(2) else None,
            point_letter=match.group(3),
            document_type=match.group(4) or "",
            so_ky_hieu=match.group(5) or "",
        )

    async def _verify_parsed(self, parsed: ParsedCitation) -> VerificationResult:
        """Verify a parsed citation against Neo4j."""
        if not parsed.article_number:
            return VerificationResult(
                citation=parsed,
                verified=False,
                reason="Could not parse article number",
            )

        # Build query based on available info
        if parsed.so_ky_hieu:
            cypher = """
            MATCH (a:Article {index: $article_index})
            <-[:HAS_ARTICLE]-(d:Document {so_ky_hieu: $so_ky_hieu})
            RETURN a.uid AS uid, a.is_current AS is_current
            """
            params = {"article_index": parsed.article_number, "so_ky_hieu": parsed.so_ky_hieu}
        else:
            cypher = """
            MATCH (a:Article {index: $article_index})
            RETURN a.uid AS uid, a.is_current AS is_current
            LIMIT 1
            """
            params = {"article_index": parsed.article_number}

        try:
            with self._driver.session(default_access_mode="READ", database="neo4j") as session:
                result = session.run(cypher, params, config={"maxTransactionRetryTime": NEO4J_TIMEOUT * 1000})
                record = result.single()

                if record:
                    return VerificationResult(
                        citation=parsed,
                        verified=True,
                        is_current=record["is_current"],
                        article_uid=record["uid"],
                    )
                else:
                    return VerificationResult(
                        citation=parsed,
                        verified=False,
                        reason="Article not found in graph",
                    )
        except Exception as e:
            return VerificationResult(
                citation=parsed,
                verified=False,
                reason=f"Neo4j query failed: {str(e)}",
            )
