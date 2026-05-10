"""
Confidence scorer for parsed documents — T1.2 (Người B)

Separated from parser.py so it can be swapped or tuned independently.

Input : ParseResult (from LegalDocumentParser)
Output: ParseResult with confidence_score + confidence_level + confidence_notes filled in
"""
from __future__ import annotations

import logging
from typing import Optional

from .models import ParseResult, ConfidenceLevel

logger = logging.getLogger(__name__)

# Thresholds from spec (T1.2)
_HIGH_THRESHOLD   = 0.9
_MEDIUM_THRESHOLD = 0.6

# Ratio of detected Điều to expected needed for HIGH
_HIGH_ARTICLE_RATIO = 0.80


class ConfidenceScorer:
    """
    Computes a confidence score for a ParseResult.

    Call score() immediately after LegalDocumentParser.parse().

    Scoring factors (weighted sum):
      1. Article detection ratio   (weight 0.50)  — most important
      2. Clause presence rate      (weight 0.20)  — do articles have clauses?
      3. Formatting consistency    (weight 0.15)  — <b>/<strong> used for headings?
      4. Hierarchy completeness    (weight 0.15)  — no orphan clauses/points?

    Usage
    -----
        scorer = ConfidenceScorer()
        result = scorer.score(result, expected_article_count=120)
    """

    def score(
        self,
        result: ParseResult,
        *,
        expected_article_count: Optional[int] = None,
        bold_heading_count: Optional[int] = None,
    ) -> ParseResult:
        if result.article_count == 0 and result.chapter_count == 0:
            result.confidence_score = 0.0
            result.confidence_level = ConfidenceLevel.LOW
            result.confidence_notes.append("No structural elements found.")
            return result

        # 1. Article Ratio
        score_ratio, note_ratio = self._article_ratio_factor(result.article_count, expected_article_count)
        result.confidence_notes.append(note_ratio)
        
        # 2. Clause Presence
        score_clause, note_clause = self._clause_presence_factor(result)
        result.confidence_notes.append(note_clause)
        
        # 3. Formatting
        score_format = 1.0
        if bold_heading_count is not None and result.article_count > 0:
            format_ratio = min(bold_heading_count / result.article_count, 1.0)
            score_format = format_ratio
            result.confidence_notes.append(f"formatting ratio {format_ratio:.0%}")
        else:
            result.confidence_notes.append("formatting unknown - assumed 100%")
            
        # 4. Hierarchy Completeness
        score_hierarchy, note_hierarchy = self._hierarchy_completeness_factor(result)
        result.confidence_notes.append(note_hierarchy)
        
        total_score = (score_ratio * 0.50) + (score_clause * 0.20) + (score_format * 0.15) + (score_hierarchy * 0.15)
        result.confidence_score = total_score
        
        if total_score >= _HIGH_THRESHOLD:
            result.confidence_level = ConfidenceLevel.HIGH
        elif total_score >= _MEDIUM_THRESHOLD:
            result.confidence_level = ConfidenceLevel.MEDIUM
        else:
            result.confidence_level = ConfidenceLevel.LOW
            
        return result

    def score_batch(
        self,
        results: list[ParseResult],
        expected_counts: Optional[dict[str, int]] = None,
    ) -> list[ParseResult]:
        """
        Score a batch of ParseResults.

        Parameters
        ----------
        results : list[ParseResult]
        expected_counts : dict[doc_id → expected_article_count], optional

        Returns
        -------
        list[ParseResult] with confidence fields populated.
        Also logs distribution: High/Medium/Low counts.
        """
        expected_counts = expected_counts or {}
        for r in results:
            self.score(r, expected_article_count=expected_counts.get(r.doc_id))

        high   = sum(1 for r in results if r.confidence_level == ConfidenceLevel.HIGH)
        medium = sum(1 for r in results if r.confidence_level == ConfidenceLevel.MEDIUM)
        low    = sum(1 for r in results if r.confidence_level == ConfidenceLevel.LOW)
        total  = len(results)

        logger.info(
            "Confidence distribution: High=%d (%.1f%%) Medium=%d (%.1f%%) Low=%d (%.1f%%)",
            high,   100 * high / total if total else 0,
            medium, 100 * medium / total if total else 0,
            low,    100 * low / total if total else 0,
        )

        # Target check from spec: ≥80% High, ≤5% Low
        if total > 0:
            if high / total < 0.80:
                logger.warning(
                    "HIGH confidence rate %.1f%% is below target 80%%",
                    100 * high / total,
                )
            if low / total > 0.05:
                logger.warning(
                    "LOW confidence rate %.1f%% exceeds target 5%%",
                    100 * low / total,
                )

        return results

    # ------------------------------------------------------------------
    # Internal scoring helpers (implement alongside score())
    # ------------------------------------------------------------------

    @staticmethod
    def _article_ratio_factor(detected: int, expected: Optional[int]) -> tuple[float, str]:
        """
        Returns (score 0-1, note string).
        If expected is None, returns (0.8, "expected_unknown").
        """
        if expected is None or expected == 0:
            return 0.8, "expected_article_count unavailable — skipping ratio factor"
        ratio = min(detected / expected, 1.0)
        note = f"detected {detected}/{expected} Điều ({ratio:.0%})"
        return ratio, note

    @staticmethod
    def _clause_presence_factor(result: ParseResult) -> tuple[float, str]:
        """
        Fraction of articles that have at least one clause.
        Very short laws (< 5 articles) may legitimately have no clauses.
        """
        articles = result.articles()
        if not articles:
            return 0.0, "no articles found"
        articles_with_clauses = sum(
            1 for a in articles if any(
                s.parent_uid == a.uid for s in result.segments
                if s.hierarchy_type is not None  # any child
            )
        )
        raw_ratio = articles_with_clauses / len(articles)
        
        # Chỉ cần 25% số Điều có chứa Khoản là đạt điểm tối đa ở hạng mục này
        target_ratio = 0.25
        score = min(raw_ratio / target_ratio, 1.0)
        
        return score, f"{articles_with_clauses}/{len(articles)} articles have clauses (score: {score:.2f})"

    @staticmethod
    def _hierarchy_completeness_factor(result: ParseResult) -> tuple[float, str]:
        """
        Checks for orphan segments (clause/point with missing parent_uid).
        """
        from .models import HierarchyType
        children = [s for s in result.segments if s.hierarchy_type in (HierarchyType.KHOAN, HierarchyType.DIEM)]
        if not children:
            return 1.0, "no clauses/points to check for orphans"
            
        orphans = [s for s in children if s.parent_uid is None]
        if not orphans:
            return 1.0, "0 orphans found"
            
        ratio = max(1.0 - (len(orphans) / len(children)), 0.0)
        return ratio, f"{len(orphans)} orphan segments found"
