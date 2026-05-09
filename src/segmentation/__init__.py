"""
Segmentation Module — Phase 1 (T1.1 → T1.6)
=============================================
Parses Vietnamese legal document HTML into a hierarchical graph
(Chương → Điều → Khoản → Điểm) and ingests into Neo4j with embeddings.

Owner: Người B
Depends on: clean_html from Người A (T0.4), Neo4j schema from Người A (T1.4),
            embedding service from Người A (T6.2)
"""

from .models import (
    HierarchyType,
    Segment,
    ParseResult,
    ConfidenceLevel,
)
from .parser import LegalDocumentParser
from .confidence import ConfidenceScorer
from .writer import SegmentWriter
from .embedder import ArticleEmbedder

__all__ = [
    # Models
    "HierarchyType",
    "Segment",
    "ParseResult",
    "ConfidenceLevel",
    # Core classes
    "LegalDocumentParser",
    "ConfidenceScorer",
    "SegmentWriter",
    "ArticleEmbedder",
]
