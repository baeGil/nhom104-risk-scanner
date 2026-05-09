"""
Contract Parser Module — T4.1 (Người C)
========================================
Parses contract documents (PDF, DOCX, TXT) to Markdown using MinerU,
with PII detection and redaction for Vietnamese contracts.

Owner: Người C
Dependencies: MinerU (Apache 2.0)
Output: Contract dataclass with raw_text, redacted_text, pii_map
"""

from .models import Contract, ParseError
from .parser import ContractParser
from .pii import detect_pii, redact_pii, reconstruct_text

__all__ = [
    "Contract",
    "ParseError",
    "ContractParser",
    "detect_pii",
    "redact_pii",
    "reconstruct_text",
]
