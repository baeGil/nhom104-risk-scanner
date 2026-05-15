"""
Policy Review Extension — T4.6

Extends contract review pipeline for internal policy compliance checking.
Classifies policy provisions as compliant_and_efficient, compliant_but_restrictive, or non_compliant.

Usage:
    from src.contract.policy_review import PolicyReview
    review = PolicyReview()
    result = await review.review(policy_document, matched_provisions)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING

from src.contract.models import (
    ContractClause,
    ComplianceResult,
    PolicyClassification,
)
from src.contract.matcher import MatchedProvision
from src.contract.compliance_analyzer import ComplianceAnalyzer

if TYPE_CHECKING:
    from src.contract.review_pipeline import ContractReviewPipeline


@dataclass
class PolicyProvisionReview:
    """
    Review result for a single policy provision.

    Attributes:
        clause: The policy clause reviewed
        classification: compliant_and_efficient, compliant_but_restrictive, or non_compliant
        compliance_result: Full compliance analysis
        restriction_details: Explanation of how policy exceeds legal requirements
    """
    clause: ContractClause
    classification: PolicyClassification
    compliance_result: ComplianceResult
    restriction_details: str = ""


@dataclass
class PolicyReviewResult:
    """
    Full policy review result.

    Attributes:
        provisions: List of provision reviews
        summary: Overall classification summary
    """
    provisions: list[PolicyProvisionReview] = field(default_factory=list)
    summary: dict[str, int] = field(default_factory=dict)


class PolicyReview:
    """
    Review policy documents for compliance with legal requirements.

    Uses the same pipeline as contract review (matching + compliance analysis)
    with additional classification logic.
    """

    def __init__(self, pipeline: Optional["ContractReviewPipeline"] = None) -> None:
        self._analyzer = ComplianceAnalyzer()
        self._pipeline = pipeline

    async def review(
        self,
        clauses: list[ContractClause],
        all_provisions: dict[str, list[MatchedProvision]],
    ) -> PolicyReviewResult:
        """
        Review a policy document.

        Args:
            clauses: Policy clauses to review
            all_provisions: Dict mapping clause_id to matched legal provisions

        Returns:
            PolicyReviewResult with classifications
        """
        result = PolicyReviewResult()
        summary = {
            "compliant_and_efficient": 0,
            "compliant_but_restrictive": 0,
            "non_compliant": 0,
        }

        for clause in clauses:
            provisions = all_provisions.get(clause.id, [])
            compliance = await self._analyzer.analyze(clause, provisions)

            # Classify the provision
            classification = self._classify(clause, compliance, provisions)

            # Get restriction details if applicable
            restriction_details = ""
            if classification == PolicyClassification.COMPLIANT_BUT_RESTRICTIVE:
                restriction_details = self._get_restriction_details(clause, provisions)

            provision_review = PolicyProvisionReview(
                clause=clause,
                classification=classification,
                compliance_result=compliance,
                restriction_details=restriction_details,
            )
            result.provisions.append(provision_review)
            summary[classification.value] += 1

        result.summary = summary
        return result

    async def review_file(self, file_path: str) -> PolicyReviewResult:
        """
        Review a policy document through the shared contract review pipeline.
        """
        if self._pipeline is None:
            from src.contract.review_pipeline import ContractReviewPipeline
            self._pipeline = ContractReviewPipeline()

        pipeline_result = await self._pipeline.review_file(file_path)
        clauses = [item.clause for item in pipeline_result.clauses]
        provisions = {item.clause.id: item.matches for item in pipeline_result.clauses}
        return await self.review(clauses, provisions)

    def _classify(
        self,
        clause: ContractClause,
        compliance: ComplianceResult,
        provisions: list[MatchedProvision],
    ) -> PolicyClassification:
        """
        Classify a policy provision.

        - non_compliant: Has violations
        - compliant_but_restrictive: No violations but more restrictive than law
        - compliant_and_efficient: No violations, meets requirements exactly
        """
        # If there are violations, it's non-compliant
        if compliance.violations:
            return PolicyClassification.NON_COMPLIANT

        # Check if policy is more restrictive than law
        if self._is_more_restrictive(clause, provisions):
            return PolicyClassification.COMPLIANT_BUT_RESTRICTIVE

        return PolicyClassification.COMPLIANT_AND_EFFICIENT

    def _is_more_restrictive(
        self,
        clause: ContractClause,
        provisions: list[MatchedProvision],
    ) -> bool:
        """
        Check if a policy clause is more restrictive than the law requires.

        Heuristic: Look for keywords indicating excess restrictions.
        """
        restrictive_keywords = [
            "nghiêm cấm", "không được phép", "bắt buộc",
            "phải", "tuyệt đối", "không cho phép",
            "xử lý nghiêm", "tước quyền", "đình chỉ",
        ]

        clause_text = clause.text_content.lower()
        for keyword in restrictive_keywords:
            if keyword in clause_text:
                # Check if the law also has this restriction
                for prov in provisions:
                    prov_text = (prov.effective_text or prov.article_text).lower()
                    if keyword not in prov_text:
                        # Policy has restriction that law doesn't
                        return True

        return False

    def _get_restriction_details(
        self,
        clause: ContractClause,
        provisions: list[MatchedProvision],
    ) -> str:
        """Generate explanation of how policy exceeds legal requirements."""
        details = []
        for prov in provisions:
            details.append(
                f"Chính sách yêu cầu: {clause.text_content[:100]}...\n"
                f"Pháp luật quy định: {prov.article_text[:100]}..."
            )
        return "\n\n".join(details) if details else "Không có chi tiết."
