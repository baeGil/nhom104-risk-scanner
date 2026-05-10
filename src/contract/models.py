"""
Data models for the contract parser module.

Contract: Output of ContractParser with raw/redacted text and PII mapping.
ParseError: Exception class for parsing failures.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
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
