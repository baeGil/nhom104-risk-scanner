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
        """
        Compute and assign confidence score to a ParseResult.

        Mutates result.confidence_score, .confidence_level, .confidence_notes in place
        and returns the same object.

        Parameters
        ----------
        result : ParseResult
            Output from LegalDocumentParser.parse().
        expected_article_count : int, optional
            Ground truth number of Điều expected. Obtained from:
              - document metadata cross-references
              - title patterns ("gồm X điều")
              If None, article ratio factor is skipped.
        bold_heading_count : int, optional
            Number of <b>/<strong> tags detected in clean_html.
            Passed through from parser context. Used for formatting factor.

        Returns
        -------
        ParseResult  (same object, mutated)

        TODO (T1.2): implement this method.
        """
        raise NotImplementedError("T1.2: implement ConfidenceScorer.score()")

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
        ratio = articles_with_clauses / len(articles)
        return ratio, f"{articles_with_clauses}/{len(articles)} articles have clauses"

    @staticmethod
    def _hierarchy_completeness_factor(result: ParseResult) -> tuple[float, str]:
        """
        Checks for orphan segments (clause/point with missing parent_uid).
        """
        orphans = [
            s for s in result.segments
            if s.hierarchy_type in (ConfidenceLevel.HIGH,)  # placeholder
            and s.parent_uid is None
        ]
        # TODO: implement properly in T1.2
        return 1.0, "hierarchy_completeness: TODO"
