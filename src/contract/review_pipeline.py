from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from src.contract.citations import LegalCitation
from src.contract.clause_extractor import ClauseExtractor
from src.contract.compliance_analyzer import ComplianceAnalyzer
from src.contract.matcher import LegalMatcher, MatchedProvision
from src.contract.models import ComplianceResult, Contract, ContractClause
from src.contract.parser import ContractParser
from src.contract.query_rewriter import LegalRetrievalPlan
from src.llm.citation_verifier import CitationVerifier, VerificationResult


class ContractReviewPipelineError(Exception):
    def __init__(self, stage: str, message: str, original: Optional[Exception] = None) -> None:
        self.stage = stage
        self.original = original
        super().__init__(f"{stage}: {message}")


@dataclass
class ClauseReviewResult:
    clause: ContractClause
    retrieval_plan: LegalRetrievalPlan
    matches: list[MatchedProvision] = field(default_factory=list)
    compliance: Optional[ComplianceResult] = None
    citations: list[LegalCitation] = field(default_factory=list)
    verification_results: list[VerificationResult] = field(default_factory=list)


@dataclass
class ContractReviewResult:
    contract: Contract
    clauses: list[ClauseReviewResult] = field(default_factory=list)


class ContractReviewPipeline:
    """Real Task 4 orchestration service."""

    def __init__(
        self,
        parser: Optional[ContractParser] = None,
        clause_extractor: Optional[ClauseExtractor] = None,
        matcher: Optional[LegalMatcher] = None,
        analyzer: Optional[ComplianceAnalyzer] = None,
        citation_verifier: Optional[CitationVerifier] = None,
    ) -> None:
        self._parser = parser or ContractParser()
        self._clause_extractor = clause_extractor or ClauseExtractor()
        self._matcher = matcher or LegalMatcher()
        self._analyzer = analyzer or ComplianceAnalyzer()
        self._citation_verifier = citation_verifier or CitationVerifier()

    async def review_file(self, file_path: str) -> ContractReviewResult:
        contract = self._run_stage("parsing", lambda: self._parser.parse(file_path))
        return await self.review_contract(contract)

    async def review_contract(self, contract: Contract) -> ContractReviewResult:
        clauses = await self._run_async_stage("extracting", self._clause_extractor.extract(contract))
        result = ContractReviewResult(contract=contract)

        # Process all clauses in parallel
        async def process_clause(clause: ContractClause) -> ClauseReviewResult:
            plan, matches = await self._run_async_stage("retrieving", self._matcher.match_with_plan(clause))
            compliance = await self._run_async_stage("analyzing", self._analyzer.analyze(clause, matches))
            citations = self._citations_from_matches(matches)
            verification_results = await self._run_async_stage("verifying", self._citation_verifier.verify_batch(citations))

            # Verify compliance citations too
            compliance_citations = self._citations_from_compliance(compliance)
            if compliance_citations:
                compliance_verification = await self._citation_verifier.verify_batch(compliance_citations)
                for violation, verification in zip(compliance.violations, compliance_verification):
                    violation.verified = verification.verified

            return ClauseReviewResult(
                clause=clause,
                retrieval_plan=plan,
                matches=matches,
                compliance=compliance,
                citations=citations,
                verification_results=verification_results,
            )

        # Run all clauses in parallel with concurrency limit
        import asyncio
        semaphore = asyncio.Semaphore(3)  # Limit concurrency to avoid API rate limits
        
        async def bounded_process(clause):
            async with semaphore:
                return await process_clause(clause)

        clause_results = await asyncio.gather(*(bounded_process(c) for c in clauses))
        result.clauses.extend(clause_results)

        return result

    def _citations_from_matches(self, matches: list[MatchedProvision]) -> list[LegalCitation]:
        citations: list[LegalCitation] = []
        for match in matches:
            citations.append(
                LegalCitation(
                    display_text=match.display_citation or match.article_title or match.segment_uid,
                    uid=match.segment_uid or match.article_uid,
                    document_title=match.document_title,
                    article=str(match.article_index) if match.article_index else None,
                    clause=str(match.clause_index) if match.clause_index else None,
                    point=str(match.point_label) if match.point_label else None,
                )
            )
        return citations

    def _citations_from_compliance(self, compliance: Optional[ComplianceResult]) -> list[LegalCitation]:
        """Extract citations from compliance analysis results for verification."""
        if not compliance or not compliance.citations:
            return []
        citations: list[LegalCitation] = []
        for cit in compliance.citations:
            if isinstance(cit, dict):
                citations.append(
                    LegalCitation(
                        display_text=cit.get("display_text") or cit.get("citation", ""),
                        uid=cit.get("uid", ""),
                        document_title=cit.get("document_title") or cit.get("documentTitle", ""),
                        article=cit.get("article"),
                        clause=cit.get("clause"),
                        point=cit.get("point"),
                    )
                )
        return citations

    def _run_stage(self, stage: str, fn):
        try:
            return fn()
        except ContractReviewPipelineError:
            raise
        except Exception as e:
            raise ContractReviewPipelineError(stage, str(e), e) from e

    async def _run_async_stage(self, stage: str, awaitable):
        try:
            return await awaitable
        except ContractReviewPipelineError:
            raise
        except Exception as e:
            raise ContractReviewPipelineError(stage, str(e), e) from e
