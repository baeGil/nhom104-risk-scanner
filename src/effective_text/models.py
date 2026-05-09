"""
Data models for effective text composition.

All dataclasses are pure Python — no Neo4j dependency.
These are shared between chain.py, merger.py, writer.py, validator.py, and
consumed by Người C's application layer queries.

UID conventions (must align with segmentation/models.py and Neo4j schema):
  Article.uid        = "doc_{doc_id}_dieu_{index}"
  EffectiveArticle.uid = "eff_{article_uid}_{iso_date}"   e.g. "eff_doc_42_dieu_5_2024-01-01"
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from datetime import date


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class AmendmentAction(str, Enum):
    """Legal action performed by a modifying article."""
    SUA_DOI      = "sua_doi"        # sửa đổi     — replace clause/point text
    BO_SUNG      = "bo_sung"        # bổ sung      — insert new clause/point
    THAY_THE     = "thay_the"       # thay thế     — replace entire clause/segment
    BAI_BO       = "bai_bo"         # bãi bỏ       — void/remove
    HET_HIEU_LUC = "het_hieu_luc"   # hết hiệu lực một phần — partial invalidation


class ValidityStatus(str, Enum):
    """Validity state of a Document or Article."""
    CON_HIEU_LUC     = "con_hieu_luc"      # Còn hiệu lực
    HET_HIEU_LUC     = "het_hieu_luc"      # Hết hiệu lực toàn bộ
    HET_HIEU_LUC_MOT_PHAN = "het_hieu_luc_mot_phan"  # Hết hiệu lực một phần
    NGUNG_HIEU_LUC   = "ngung_hieu_luc"    # Ngưng hiệu lực
    UNKNOWN          = "unknown"


# ---------------------------------------------------------------------------
# Amendment models
# ---------------------------------------------------------------------------

@dataclass
class Amendment:
    """
    One modification action extracted from a [:MODIFIES] relationship in Neo4j.
    Produced by AmendmentChainTraverser, consumed by TextMerger.

    Source: cross_reference/models.py ModificationRef (written to Neo4j in T2.3)
    """
    # The modifying Article (source of MODIFIES edge)
    source_article_uid: str
    source_doc_id: str
    source_doc_ngay_ban_hanh: date          # used for chronological ordering

    # The action
    action: AmendmentAction

    # Target within the original Article
    target_khoan_index: Optional[int] = None    # Khoản number (1-based), None = whole article
    target_diem_letter: Optional[str] = None    # Điểm letter (a/b/c), None = whole clause

    # Replacement/inserted text (for SUA_DOI, BO_SUNG, THAY_THE)
    new_text: Optional[str] = None

    # Original context phrase from modifying document
    context_text: str = ""

    # Confidence from cross_reference extraction (0-1)
    confidence: float = 1.0


@dataclass
class AmendmentChain:
    """
    Ordered list of all amendments applicable to one Article.
    Produced by AmendmentChainTraverser.traverse_article().
    Consumed by TextMerger.compose().

    Interface note for Người C:
      - amendment_chain_uids is stored on EffectiveArticle.amendment_chain in Neo4j
      - Người C can query it to show amendment history
    """
    article_uid: str                                    # target Article being amended
    original_text: str                                  # Article.clean_text before any amendment
    amendments: list[Amendment] = field(default_factory=list)  # chronological order (ASC)
    is_transitive: bool = False                         # True if any amendment was itself amended
    max_depth: int = 1                                  # amendment chain depth

    @property
    def amendment_chain_uids(self) -> list[str]:
        """Ordered list of source_article_uid — used as EffectiveArticle.amendment_chain."""
        return [a.source_article_uid for a in self.amendments]

    @property
    def latest_date(self) -> Optional[date]:
        """Date of the most recent amendment (= as_of_date of the EffectiveArticle)."""
        if not self.amendments:
            return None
        return max(a.source_doc_ngay_ban_hanh for a in self.amendments)


# ---------------------------------------------------------------------------
# Composition result
# ---------------------------------------------------------------------------

@dataclass
class ComposedArticle:
    """
    Output of TextMerger.compose(). Ready to be written as EffectiveArticle node.

    Interface note for Người C:
      - effective_text is what retrieval pipeline (T4.3, T5.2) should display
      - is_current is set later by CurrentStatusComputer (T3.5)
      - uid format: "eff_{article_uid}_{as_of_date}"
    """
    article_uid: str
    uid: str                            # "eff_{article_uid}_{as_of_date}"
    as_of_date: date                    # date of last amendment applied
    effective_text: str                 # composed text (original + all amendments merged)
    amendment_chain: list[str]          # ordered source_article_uids
    changes_count: int = 0              # number of amendments applied

    # Set by CurrentStatusComputer (T3.5) — default True, may be overridden
    is_current: bool = True

    # Sections that were voided (BAI_BO) — needed by Người C for display
    voided_khoans: list[int] = field(default_factory=list)      # Khoản indices
    voided_diems: list[str] = field(default_factory=list)       # Điểm letters

    # Merge warnings (e.g., "could not locate Khoản 3 for replacement")
    merge_warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Validation models
# ---------------------------------------------------------------------------

@dataclass
class ValidationMatch:
    """
    Result of comparing one composed Điều against VB hợp nhất ground truth.
    Produced by HopNhatValidator.
    """
    article_uid: str
    hop_nhat_doc_id: str

    char_similarity: float      # 0-1, character-level diff ratio
    structural_match: bool      # same number of Khoản/Điểm?
    semantic_score: float       # 0-1, embedding cosine similarity (optional)

    composed_text: str
    ground_truth_text: str

    @property
    def is_match(self) -> bool:
        """Treat as match if char_similarity ≥ 0.90."""
        return self.char_similarity >= 0.90


@dataclass
class HopNhatReport:
    """Aggregate result of validation against all 35 VB hợp nhất documents."""
    total_articles_checked: int = 0
    matched: int = 0
    mismatched: int = 0
    matches: list[ValidationMatch] = field(default_factory=list)

    @property
    def agreement_rate(self) -> float:
        if self.total_articles_checked == 0:
            return 0.0
        return self.matched / self.total_articles_checked


# ---------------------------------------------------------------------------
# is_current validity report
# ---------------------------------------------------------------------------

@dataclass
class ArticleValidity:
    """Per-article validity decision with reasoning."""
    article_uid: str
    doc_id: str
    loai_van_ban: str
    is_current: bool
    reason: str                 # human-readable: "doc_het_hieu_luc" | "bai_bo" | "superseded" | ...


@dataclass
class ValidityReport:
    """
    Output of CurrentStatusComputer.compute_all().
    Interface note for Người C:
      - current_by_type shows how many Articles are queryable per doc type
    """
    total_articles: int = 0
    current_count: int = 0
    voided_count: int = 0
    decisions: list[ArticleValidity] = field(default_factory=list)

    # Breakdown by loai_van_ban — useful for Người C's monitoring dashboard
    current_by_type: dict[str, int] = field(default_factory=dict)
    voided_by_type: dict[str, int] = field(default_factory=dict)
