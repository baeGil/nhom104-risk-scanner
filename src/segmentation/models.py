"""
Data models for the segmentation pipeline.

All dataclasses are pure Python — no BeautifulSoup or Neo4j dependency.
This lets cross_reference/ and the application layer import them freely.

UID conventions (must match Neo4j schema from T1.4 / Người A):
  Article.uid  = "doc_{doc_id}_dieu_{index}"
  Clause.uid   = "doc_{doc_id}_dieu_{dieu_idx}_khoan_{idx}"
  Point.uid    = "doc_{doc_id}_dieu_{dieu_idx}_khoan_{khoan_idx}_diem_{letter}"
  Chapter has no uid — identified by (doc_id, roman_index)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class HierarchyType(str, Enum):
    """Structural level of a parsed segment."""
    PHAN    = "Phần"       # Part  — above Chương, used in Bộ luật (gap in spec)
    CHUONG  = "Chương"     # Chapter
    MUC     = "Mục"        # Section — between Chương and Điều
    DIEU    = "Điều"       # Article
    KHOAN   = "Khoản"      # Clause
    DIEM    = "Điểm"       # Point
    UNKNOWN = "unknown"


class ConfidenceLevel(str, Enum):
    HIGH   = "high"    # ≥ 0.9
    MEDIUM = "medium"  # 0.6 – 0.9
    LOW    = "low"     # < 0.6


# ---------------------------------------------------------------------------
# Core segment dataclass
# ---------------------------------------------------------------------------

@dataclass
class Segment:
    """
    One structural node produced by the parser.

    This is the primary output unit of LegalDocumentParser and the
    primary input unit of SegmentWriter and ArticleEmbedder.

    Interface note for Người A:
      - doc_id must match Document.id already in Neo4j (from T1.4 / T1.5)
    Interface note for cross_reference/ (Người B, Phase 2):
      - article_uid, clause_uid, point_uid are the stable IDs used in
        InternalRef.source_article_uid / target_article_uid
    """
    # Identity
    doc_id: str
    hierarchy_type: HierarchyType
    index: int                          # integer position within parent (1-based)

    # Hierarchy path — human-readable, e.g. "Chương I / Điều 5 / Khoản 2"
    path: str = ""

    # Content
    text_content: str = ""              # raw HTML of this segment
    clean_text: str = ""                # plain text, no HTML tags

    # Parent linkage
    parent_uid: Optional[str] = None    # UID of parent segment; None for top-level

    # Computed UIDs (set after parsing, before Neo4j write)
    uid: Optional[str] = None           # own stable UID

    # Chapter-specific
    roman_index: Optional[str] = None   # "I", "II", "III"...
    title: Optional[str] = None         # heading text (Chương/Điều/Mục title)
    section: Optional[str] = None       # section context (Mục), stored as metadata instead of separate node

    # Embedding (set by ArticleEmbedder, only for DIEU level)
    embedding: Optional[list[float]] = None  # 1024-dim vector

    # Parser metadata
    parse_notes: list[str] = field(default_factory=list)  # warnings / edge cases

    # ── Computed properties ────────────────────────────────────────────────

    @property
    def article_uid(self) -> Optional[str]:
        """Convenience accessor used by cross_reference/."""
        return self.uid if self.hierarchy_type == HierarchyType.DIEU else None


@dataclass
class ParseResult:
    """
    Full output for one document from LegalDocumentParser.

    Consumed by:
      - SegmentWriter  (T1.5) → Neo4j ingest
      - ArticleEmbedder (T1.6) → embedding generation
      - ConfidenceScorer (T1.2) → quality check
      - cross_reference/extractor.py (T2.1-T2.3) → reference extraction
    """
    doc_id: str
    segments: list[Segment] = field(default_factory=list)

    # Confidence (set by ConfidenceScorer after parsing)
    confidence_score: float = 0.0
    confidence_level: ConfidenceLevel = ConfidenceLevel.LOW
    confidence_notes: list[str] = field(default_factory=list)

    # Parse statistics
    chapter_count: int = 0
    article_count: int = 0
    clause_count: int = 0
    point_count: int = 0
    parse_errors: list[str] = field(default_factory=list)

    # ── Convenience accessors ──────────────────────────────────────────────

    def articles(self) -> list[Segment]:
        return [s for s in self.segments if s.hierarchy_type == HierarchyType.DIEU]

    def clauses_of(self, article_uid: str) -> list[Segment]:
        return [s for s in self.segments
                if s.hierarchy_type == HierarchyType.KHOAN
                and s.parent_uid == article_uid]

    def points_of(self, clause_uid: str) -> list[Segment]:
        return [s for s in self.segments
                if s.hierarchy_type == HierarchyType.DIEM
                and s.parent_uid == clause_uid]
