"""
Data models for cross-reference extraction.

All dataclasses are pure Python (no Neo4j dependency) so they can be
used/tested independently by any team member without a running DB.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class RefType(str, Enum):
    """Top-level classification of a reference."""
    INTERNAL = "INTERNAL"       # same document, different Điều/Khoản/Điểm
    EXTERNAL = "EXTERNAL"       # cross-document reference
    MODIFICATION = "MODIFICATION"  # sửa đổi / bổ sung / bãi bỏ link


class ModAction(str, Enum):
    """The legal action performed by a modifying document."""
    SUA_DOI      = "sua_doi"       # sửa đổi  — replace content
    BO_SUNG      = "bo_sung"       # bổ sung   — insert new content
    THAY_THE     = "thay_the"      # thay thế  — replace a segment
    BAI_BO       = "bai_bo"        # bãi bỏ    — void/remove
    HET_HIEU_LUC = "het_hieu_luc"  # hết hiệu lực một phần


class DocType(str, Enum):
    """Loại văn bản supported by the system."""
    LUAT   = "Luật"
    BO_LUAT = "Bộ luật"
    NGHI_DINH = "Nghị định"
    THONG_TU  = "Thông tư"
    TTLT      = "Thông tư liên tịch"
    QUYET_DINH = "Quyết định"   # out-of-scope but kept for logging
    UNKNOWN    = "unknown"


# ---------------------------------------------------------------------------
# Reference dataclasses (plain data, no DB coupling)
# ---------------------------------------------------------------------------

@dataclass
class InternalRef:
    """
    A reference from one structural element to another within the same document.

    Produced by: T2.1 — extract_internal_references()
    Written to Neo4j as: [:REFERENCES_INTERNAL]
    """
    source_doc_id: str          # Document node id
    source_article_uid: str     # Article.uid of the citing element
    source_clause_uid: Optional[str] = None   # Clause.uid if reference is inside a clause
    source_point_uid: Optional[str] = None    # Point.uid if reference is inside a point

    # Target within the same document
    target_article_index: int = 0             # Điều number (integer)
    target_clause_index: Optional[int] = None # Khoản number
    target_point_label: Optional[str] = None  # Điểm letter, e.g. "a", "b"

    # Resolved node UIDs (filled in after lookup; None = unresolved)
    target_article_uid: Optional[str] = None
    target_clause_uid: Optional[str] = None
    target_point_uid: Optional[str] = None

    context_text: str = ""      # original phrase where the reference was found
    confidence: float = 1.0     # 1.0 = exact regex match, <1.0 = fuzzy/ambiguous
    start_char: int = 0         # Start position in the original fragment
    end_char: int = 0           # End position in the original fragment
    is_exception: bool = False  # Phase 2: Đánh dấu quan hệ ngoại trừ


@dataclass
class ExternalRef:
    """
    A reference from a provision in one document to a provision in another.

    Produced by: T2.2 — extract_external_references()
    Written to Neo4j as: [:REFERENCES_EXTERNAL]
    """
    source_doc_id: str
    source_article_uid: str
    source_clause_uid: Optional[str] = None
    source_point_uid: Optional[str] = None

    # Raw parsed fields (before lookup)
    raw_so_ky_hieu: str = ""            # e.g. "46/2014/NĐ-CP"
    normalized_so_ky_hieu: str = ""     # e.g. "ND-046-2014"
    target_doc_type: DocType = DocType.UNKNOWN
    target_article_index: Optional[int] = None
    target_clause_index: Optional[int] = None
    target_point_label: Optional[str] = None

    # Resolved IDs (filled in after lookup)
    target_doc_id: Optional[str] = None
    target_article_uid: Optional[str] = None
    target_clause_uid: Optional[str] = None
    target_point_uid: Optional[str] = None

    context_text: str = ""
    match_method: str = "exact"         # "exact" | "fuzzy_levenshtein" | "fuzzy_substring"
    confidence: float = 1.0
    start_char: int = 0
    end_char: int = 0
    is_exception: bool = False          # Phase 2: Đánh dấu nếu là quan hệ ngoại trừ (trừ trường hợp...)


@dataclass
class ModificationRef:
    """
    An article-level modification link produced from a "sửa đổi/bổ sung" document.

    Produced by: T2.3 — extract_modification_references()
    Written to Neo4j as: [:MODIFIES]
    """
    # The modifying document
    source_doc_id: str
    source_article_uid: str     # Article in the modifying doc that contains the action
    source_clause_index: Optional[str] = None # Clause number in the source document

    # The action
    action: ModAction = ModAction.SUA_DOI

    # The target (resolved)
    raw_target_so_ky_hieu: str = ""
    target_doc_id: Optional[str] = None
    target_article_index: Optional[int] = None
    target_clause_index: Optional[int] = None
    target_point_label: Optional[str] = None

    target_doc_uid: Optional[str] = None
    target_article_uid: Optional[str] = None
    target_clause_uid: Optional[str] = None
    target_point_uid: Optional[str] = None

    new_text: Optional[str] = None      # replacement/inserted text (for sửa đổi/bổ sung)
    context_text: str = ""
    confidence: float = 1.0
    start_char: int = 0
    end_char: int = 0

    # T2.3 improvement: flag to indicate this ref needs target_doc_id/article from context
    is_partial_ref: bool = False


# ---------------------------------------------------------------------------
# Aggregate result container
# ---------------------------------------------------------------------------

@dataclass
class ExtractionResult:
    """
    Returned by CrossReferenceExtractor for a single document.
    All lists contain only successfully *parsed* references
    (resolution happens in a separate step).
    """
    doc_id: str

    internal_refs: list[InternalRef] = field(default_factory=list)
    external_refs: list[ExternalRef] = field(default_factory=list)
    modification_refs: list[ModificationRef] = field(default_factory=list)

    # Counts for monitoring
    parse_errors: list[str] = field(default_factory=list)   # human-readable error strings

    @property
    def total(self) -> int:
        return len(self.internal_refs) + len(self.external_refs) + len(self.modification_refs)
