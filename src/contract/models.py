"""
Data models for the contract parser module.

Contract: Output of ContractParser with raw/redacted text and PII mapping.
ParseError: Exception class for parsing failures.
ContractClause: Extracted clause from a contract (T4.2).
ComplianceResult: Compliance analysis output (T4.4).
PolicyClassification: Policy review classification (T4.6).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional


@dataclass
class Contract:
    """
    Parsed contract document.

    Attributes:
        id: UUID string uniquely identifying this contract
        raw_text: Original Markdown output from MinerU (contains PII)
        redacted_text: Markdown with PII replaced by placeholders
        source_format: "pdf" | "docx" | "txt"
        upload_date: Date the contract was parsed
        pii_map: Mapping of placeholder → original PII value
            Example: {"[REDACTED_CCCD_1]": "079087654321"}
        contract_type: Detected contract type (set by T4.2)
        metadata: Additional metadata (page count, file size, etc.)
    """
    id: str
    raw_text: str
    redacted_text: str
    source_format: str
    upload_date: date
    pii_map: dict[str, str] = field(default_factory=dict)
    contract_type: Optional[str] = None
    metadata: dict[str, str | int | float] = field(default_factory=dict)


class ParseError(Exception):
    """
    Exception raised when contract parsing fails.

    Attributes:
        message: Human-readable error description
        file_path: Path to the file that failed to parse
        error_type: Category of error ("corrupted", "unsupported", "ocr_failure", "unknown")
        original_exception: The underlying exception (if any)
    """
    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        error_type: str = "unknown",
        original_exception: Optional[Exception] = None,
    ) -> None:
        self.file_path = file_path
        self.error_type = error_type
        self.original_exception = original_exception
        super().__init__(message)

    def __str__(self) -> str:
        parts = [self.args[0]]
        if self.file_path:
            parts.append(f"File: {self.file_path}")
        if self.error_type != "unknown":
            parts.append(f"Error type: {self.error_type}")
        return " | ".join(parts)


# ── Contract Clause Models (T4.2) ──────────────────────────────────────────

class ClauseType(str, Enum):
    """Predefined contract clause types."""
    THANH_TOAN = "thanh_toán"
    BAO_HANH = "bảo_hành"
    PHAT = "phạt"
    CHAM_DUT = "chấm_dứt"
    BOI_THUONG = "bồi_thường"
    BAO_MAT = "bảo_mật"
    GIAI_QUYET_TRANH_CHAP = "giải_quyết_tranh_chấp"
    FORCE_MAJEURE = "force_majeure"
    NGHIA_VU = "nghĩa_vụ"
    QUYEN_HAN = "quyền_hạn"
    THOI_HAN = "thời_hạn"
    KHAC = "khác"


@dataclass
class ContractClause:
    """
    Extracted clause from a contract.

    Attributes:
        id: UUID string uniquely identifying this clause
        index: Sequential clause number (1, 2, 3...)
        clause_type: Type of clause (thanh_toán, phạt, etc.)
        text_content: Full text of the clause
        parties_involved: List of party names mentioned
        obligations: List of obligations described
        amount: Monetary value if present
        deadline: Deadline/date if present
        embedding: 1024-dim vector embedding (set by T4.2)
    """
    id: str
    index: int
    clause_type: str
    text_content: str
    parties_involved: list[str] = field(default_factory=list)
    obligations: list[str] = field(default_factory=list)
    amount: Optional[str] = None
    deadline: Optional[str] = None
    embedding: Optional[list[float]] = None


# ── Compliance Analysis Models (T4.4) ──────────────────────────────────────

class RiskLevel(str, Enum):
    """Risk severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class ComplianceViolation:
    """
    A specific legal violation found in a contract clause.

    Attributes:
        clause: Clause type or description
        description: What the violation is
        citation: Legal citation (e.g., "Điều 301 Luật Thương mại 2005")
        severity: low, medium, high
        verified: Whether the citation has been verified against Neo4j
    """
    clause: str
    description: str
    citation: str
    severity: str = "medium"
    verified: bool = False


@dataclass
class ComplianceResult:
    """
    Full compliance analysis result for a contract.

    Attributes:
        compliance_status: "compliant" | "non_compliant" | "partially_compliant"
        summary: Brief analysis summary in Vietnamese
        violations: List of legal violations found
        risks: List of legal risks identified
        suggestions: List of suggested text changes
        citations: List of legal citations with verification status
    """
    compliance_status: str = "compliant"
    summary: str = ""
    violations: list[ComplianceViolation] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    citations: list[dict] = field(default_factory=list)


# ── Policy Review Models (T4.6) ────────────────────────────────────────────

class PolicyClassification(str, Enum):
    """Policy compliance classification."""
    COMPLIANT_AND_EFFICIENT = "compliant_and_efficient"
    COMPLIANT_BUT_RESTRICTIVE = "compliant_but_restrictive"
    NON_COMPLIANT = "non_compliant"
