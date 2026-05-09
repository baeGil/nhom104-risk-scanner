"""
Validity computer for Articles and EffectiveArticles — T3.5 (Người B)

Determines is_current based on:
  1. Document.tinh_trang_hieu_luc
  2. Incoming SUPERSEDES / PARTIALLY_SUPERSEDES doc-level relationships (from T1.7, Người A)
  3. Article-level BAI_BO modifications (from T2.3 MODIFIES edges)

Input : Neo4j graph
Output: ValidityReport (pure data) → passed to EffectiveArticleWriter.write_validity()
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .models import ValidityReport, ArticleValidity, ValidityStatus

if TYPE_CHECKING:
    from neo4j import Driver

logger = logging.getLogger(__name__)

# Map from Vietnamese tinh_trang_hieu_luc to ValidityStatus enum
_TINH_TRANG_MAP = {
    "Còn hiệu lực":            ValidityStatus.CON_HIEU_LUC,
    "Hết hiệu lực toàn bộ":    ValidityStatus.HET_HIEU_LUC,
    "Hết hiệu lực một phần":   ValidityStatus.HET_HIEU_LUC_MOT_PHAN,
    "Ngưng hiệu lực":          ValidityStatus.NGUNG_HIEU_LUC,
}


class CurrentStatusComputer:
    """
    Computes is_current for all Article nodes by walking Neo4j graph.

    Usage
    -----
        computer = CurrentStatusComputer(driver)
        report = computer.compute_all()
        # report.decisions contains one ArticleValidity per article

        # Then persist:
        writer.write_validity(report)
    """

    def __init__(self, driver: "Driver") -> None:
        self._driver = driver

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def compute_all(self) -> ValidityReport:
        """
        Compute is_current for every Article in Neo4j.

        Algorithm (in priority order):
          1. Doc is "Hết hiệu lực toàn bộ" or "Ngưng hiệu lực"
             → ALL its Articles: is_current=False, reason="doc_het_hieu_luc"
          2. Doc has incoming [:SUPERSEDES] edge from another doc
             → ALL its Articles: is_current=False, reason="superseded"
          3. Doc has incoming [:PARTIALLY_SUPERSEDES] from another doc
             → SPECIFIC Khoản/Điểm: is_current=False, reason="partially_superseded"
          4. Article has MODIFIES edge with action="bai_bo" targeting it
             → That Article: is_current=False, reason="bai_bo"
          5. Default: is_current=True, reason="con_hieu_luc"

        Returns
        -------
        ValidityReport
            decisions: one ArticleValidity per Article

        TODO (T3.5): implement this method.

        Suggested query to get doc-level validity:
            MATCH (d:Document)
            OPTIONAL MATCH (sup:Document)-[:SUPERSEDES]->(d)
            RETURN d.id, d.tinh_trang_hieu_luc, count(sup) > 0 AS is_superseded

        Then for each doc, if HET_HIEU_LUC or is_superseded:
            MATCH (d:Document {id: $doc_id})-[:HAS_ARTICLE]->(a:Article)
            RETURN a.uid, d.loai_van_ban
        """
        raise NotImplementedError("T3.5: implement compute_all()")

    def compute_for_doc(self, doc_id: str) -> list[ArticleValidity]:
        """
        Compute is_current for all Articles of one document.
        Useful for incremental updates when a new amendment is processed.

        TODO (T3.5): implement.
        """
        raise NotImplementedError("T3.5: implement compute_for_doc()")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _tinh_trang_to_status(raw: str) -> ValidityStatus:
        """Map Document.tinh_trang_hieu_luc string to ValidityStatus enum."""
        return _TINH_TRANG_MAP.get(raw.strip() if raw else "", ValidityStatus.UNKNOWN)

    @staticmethod
    def _make_decision(
        article_uid: str,
        doc_id: str,
        loai_van_ban: str,
        is_current: bool,
        reason: str,
    ) -> ArticleValidity:
        return ArticleValidity(
            article_uid=article_uid,
            doc_id=doc_id,
            loai_van_ban=loai_van_ban,
            is_current=is_current,
            reason=reason,
        )
