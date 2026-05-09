"""
Cross-Reference Extraction Module
==================================
Extracts internal, external, and modification references
from Vietnamese legal document segments stored in Neo4j.
"""

from .models import (
    InternalRef,
    ExternalRef,
    ModificationRef,
    RefType,
    ModAction,
    ExtractionResult,
)
from .extractor import CrossReferenceExtractor

__all__ = [
    "CrossReferenceExtractor",
    "InternalRef",
    "ExternalRef",
    "ModificationRef",
    "RefType",
    "ModAction",
    "ExtractionResult",
]
