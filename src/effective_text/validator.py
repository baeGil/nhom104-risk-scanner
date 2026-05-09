"""
VB hợp nhất validator — T3.4 (Người B)

Compares composed EffectiveArticle text against 35 ground-truth
"Văn bản hợp nhất" documents to measure composition accuracy.

Input:
  - ComposedArticle list (from merger.py)
  - VB hợp nhất parsed content (from Neo4j or parquet)
Output:
  - HopNhatReport (pure data)

This module is the quality gate for T3.2 (TextMerger).
If agreement_rate < 0.90, mismatches become training data
for future LLM-assisted composition.
"""
from __future__ import annotations

import difflib
import json
import logging
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from .models import ValidationMatch, HopNhatReport, ComposedArticle

if TYPE_CHECKING:
    from neo4j import Driver

logger = logging.getLogger(__name__)

# Minimum character similarity to consider a match
MATCH_THRESHOLD = 0.90


class HopNhatValidator:
    """
    Validates composed EffectiveArticle text against VB hợp nhất ground truth.

    Usage
    -----
        validator = HopNhatValidator(driver)
        report = validator.validate(composed_articles)
        report_dict = validator.to_dict(report)
        # Save mismatches for training data
        validator.export_mismatches(report, "output/hop_nhat_mismatches.jsonl")
    """

    def __init__(self, driver: "Driver") -> None:
        self._driver = driver

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def validate(self, composed_articles: list[ComposedArticle]) -> HopNhatReport:
        """
        Compare all relevant composed articles against VB hợp nhất ground truth.

        Parameters
        ----------
        composed_articles : list[ComposedArticle]
            All composed articles from Phase 3 pipeline.
            Only articles whose source document has a VB hợp nhất counterpart
            will be checked.

        Returns
        -------
        HopNhatReport
            matches list contains one ValidationMatch per compared Điều.

        TODO (T3.4): implement this method.

        Algorithm:
          1. Query Neo4j: find all Document nodes with loai_van_ban="Văn bản hợp nhất"
             → 35 documents expected
          2. For each hop_nhat doc, find the original doc it consolidates
             (via DETAILS/DETAILED_BY or doc title pattern)
          3. Parse hop_nhat content into article_index → text mapping
          4. Find corresponding ComposedArticle in composed_articles list
          5. Call self._compare(composed.effective_text, hop_nhat_text)
          6. Accumulate ValidationMatch objects into HopNhatReport
        """
        raise NotImplementedError("T3.4: implement validate()")

    def export_mismatches(
        self, report: HopNhatReport, output_path: str | Path
    ) -> None:
        """
        Export mismatched articles as JSONL for future LLM fine-tuning.

        Each line: {"article_uid": "...", "composed": "...", "ground_truth": "...", "diff": "..."}

        TODO (T3.4): implement.
        """
        raise NotImplementedError("T3.4: implement export_mismatches()")

    # ------------------------------------------------------------------
    # Comparison utilities (implement these first — testable independently)
    # ------------------------------------------------------------------

    @staticmethod
    def char_similarity(text_a: str, text_b: str) -> float:
        """
        Character-level similarity using SequenceMatcher.
        Returns 0.0-1.0.

        This is ALREADY IMPLEMENTED — use in validate() and tests immediately.
        """
        if not text_a and not text_b:
            return 1.0
        if not text_a or not text_b:
            return 0.0
        return difflib.SequenceMatcher(None, text_a.strip(), text_b.strip()).ratio()

    @staticmethod
    def structural_match(text_a: str, text_b: str) -> bool:
        """
        Check if two article texts have the same number of Khoản and Điểm.
        Returns True if structure matches.

        This is ALREADY IMPLEMENTED — use in validate() immediately.
        """
        import re
        khoan_a = len(re.findall(r"(?:^|\n)\d+\.\s", text_a, re.MULTILINE))
        khoan_b = len(re.findall(r"(?:^|\n)\d+\.\s", text_b, re.MULTILINE))
        diem_a  = len(re.findall(r"(?:^|\n)[a-zđ]\)\s", text_a, re.MULTILINE | re.UNICODE))
        diem_b  = len(re.findall(r"(?:^|\n)[a-zđ]\)\s", text_b, re.MULTILINE | re.UNICODE))
        return khoan_a == khoan_b and diem_a == diem_b

    @staticmethod
    def unified_diff(text_a: str, text_b: str) -> str:
        """
        Return a unified diff string between composed and ground truth.
        Used for human review and training data generation.
        """
        lines_a = text_a.splitlines(keepends=True)
        lines_b = text_b.splitlines(keepends=True)
        diff = difflib.unified_diff(lines_a, lines_b,
                                    fromfile="composed", tofile="hop_nhat", lineterm="")
        return "".join(diff)

    def _compare(
        self, composed_text: str, ground_truth_text: str,
        article_uid: str, hop_nhat_doc_id: str,
        semantic_score: float = 0.0,
    ) -> ValidationMatch:
        """Build a ValidationMatch from two texts."""
        return ValidationMatch(
            article_uid=article_uid,
            hop_nhat_doc_id=hop_nhat_doc_id,
            char_similarity=self.char_similarity(composed_text, ground_truth_text),
            structural_match=self.structural_match(composed_text, ground_truth_text),
            semantic_score=semantic_score,
            composed_text=composed_text,
            ground_truth_text=ground_truth_text,
        )
