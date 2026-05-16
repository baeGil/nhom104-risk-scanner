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
from .citations import LegalCitation
from .context_assembler import LegalContextAssembler
from .parser import ContractParser
from .pii import detect_pii, redact_pii, reconstruct_text
from .query_rewriter import LegalRetrievalPlan, QueryRewriter
from .review_pipeline import ContractReviewPipeline, ContractReviewPipelineError

__all__ = [
    "Contract",
    "ParseError",
    "ContractParser",
    "LegalCitation",
    "LegalContextAssembler",
    "LegalRetrievalPlan",
    "QueryRewriter",
    "ContractReviewPipeline",
    "ContractReviewPipelineError",
    "detect_pii",
    "redact_pii",
    "reconstruct_text",
]
