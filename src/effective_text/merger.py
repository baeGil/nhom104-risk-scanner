"""
Rule-based text merger — T3.2 (Người B)

Applies an ordered AmendmentChain to produce ComposedArticle (effective text).
PURE PYTHON — no Neo4j, no LLM, no I/O.
This is the most complex module in Phase 3.

Design notes
------------
The merger works at TWO levels:
  1. Article level  : whole-article replacements (e.g. "thay thế Điều X")
  2. Khoản/Điểm level: clause/point-level replacements (most common)

Input  : AmendmentChain (from chain.py)
Output : ComposedArticle (ready for writer.py)
"""
from __future__ import annotations

import re
import logging
from datetime import date
from typing import Optional

from .models import (
    Amendment, AmendmentAction, AmendmentChain,
    ComposedArticle,
)

logger = logging.getLogger(__name__)

# Pattern to detect "Khoản N." header inside clean_text
# Used to locate clause boundaries for surgical replacement
_RE_KHOAN_HEADER = re.compile(r"(?:^|\n)(\d+)\.\s", re.MULTILINE)

# Pattern to detect "điểm X)" header inside a clause text
_RE_DIEM_HEADER = re.compile(r"(?:^|\n)([a-zđ])\)\s", re.MULTILINE | re.UNICODE)

# Sentinel for voided content
VOIDED_MARKER = "[Đã bãi bỏ]"


class TextMerger:
    """
    Applies an AmendmentChain to compose the effective text of an Article.

    Usage
    -----
        merger = TextMerger()
        composed = merger.compose(chain)

    Notes for implementer (T3.2)
    ----------------------------
    The general algorithm:
      1. Start with `chain.original_text` as the working text.
      2. Iterate chain.amendments in order (already chronological from T3.1).
      3. For each Amendment, call the appropriate _apply_* method.
      4. Collect merge_warnings for any amendment that could not be applied.
      5. Return ComposedArticle with the final working_text as effective_text.

    Key challenge: locating the RIGHT clause/point in the working text.
    Recommended approach: split original_text into a dict of
      {khoan_index: khoan_text, "diem_a": diem_text, ...}
    then reassemble after all amendments.
    """

    def compose(self, chain: AmendmentChain) -> ComposedArticle:
        """
        Compose effective text from original + ordered amendments.

        Parameters
        ----------
        chain : AmendmentChain
            Output of AmendmentChainTraverser.traverse_article().
            amendments must be in chronological order (ASC).

        Returns
        -------
        ComposedArticle
            - effective_text  : final composed text
            - changes_count   : number of amendments successfully applied
            - merge_warnings  : list of warnings for failed/partial applications
            - voided_khoans   : Khoản indices marked as BAI_BO
            - voided_diems    : Điểm letters marked as BAI_BO
            - is_current      : True by default (overridden by CurrentStatusComputer)

        TODO (T3.2): implement this method.

        Suggested skeleton:
            working_text = chain.original_text
            voided_khoans = []
            voided_diems  = []
            warnings      = []
            applied       = 0

            for amendment in chain.amendments:
                if amendment.action == AmendmentAction.SUA_DOI:
                    working_text, ok = self._apply_sua_doi(working_text, amendment)
                elif amendment.action == AmendmentAction.BO_SUNG:
                    working_text, ok = self._apply_bo_sung(working_text, amendment)
                elif amendment.action == AmendmentAction.THAY_THE:
                    working_text, ok = self._apply_thay_the(working_text, amendment)
                elif amendment.action == AmendmentAction.BAI_BO:
                    working_text, ok, v_k, v_d = self._apply_bai_bo(working_text, amendment)
                    voided_khoans.extend(v_k)
                    voided_diems.extend(v_d)
                elif amendment.action == AmendmentAction.HET_HIEU_LUC:
                    working_text, ok = self._apply_het_hieu_luc(working_text, amendment)
                if ok:
                    applied += 1
                else:
                    warnings.append(f"Could not apply {amendment.action} from {amendment.source_article_uid}")

            as_of = chain.latest_date or date.today()
            return ComposedArticle(
                article_uid     = chain.article_uid,
                uid             = f"eff_{chain.article_uid}_{as_of.isoformat()}",
                as_of_date      = as_of,
                effective_text  = working_text,
                amendment_chain = chain.amendment_chain_uids,
                changes_count   = applied,
                voided_khoans   = voided_khoans,
                voided_diems    = voided_diems,
                merge_warnings  = warnings,
            )
        """
        raise NotImplementedError("T3.2: implement TextMerger.compose()")

    def compose_batch(self, chains: list[AmendmentChain]) -> list[ComposedArticle]:
        """
        Compose effective text for a batch of amendment chains.
        Also handles Articles with NO amendments — creates base EffectiveArticle.

        Parameters
        ----------
        chains : list[AmendmentChain]
            Include both amended and unamended articles.
            For unamended: chain.amendments is empty, original_text is used as-is.

        Returns
        -------
        list[ComposedArticle]
        """
        results = []
        for chain in chains:
            try:
                composed = self.compose(chain)
            except NotImplementedError:
                raise
            except Exception as exc:
                logger.error("Compose failed for %s: %s", chain.article_uid, exc)
                # Fallback: use original text unchanged
                composed = ComposedArticle(
                    article_uid=chain.article_uid,
                    uid=f"eff_{chain.article_uid}_fallback",
                    as_of_date=date.today(),
                    effective_text=chain.original_text,
                    amendment_chain=[],
                    changes_count=0,
                    merge_warnings=[f"compose() raised: {exc}"],
                )
            results.append(composed)
        return results

    # ------------------------------------------------------------------
    # Private application methods (one per AmendmentAction)
    # ------------------------------------------------------------------

    def _apply_sua_doi(
        self, text: str, amendment: Amendment
    ) -> tuple[str, bool]:
        """
        Replace the text of target_khoan_index (and optionally target_diem_letter)
        with amendment.new_text.

        Returns (modified_text, success: bool).

        TODO (T3.2): implement.

        Algorithm:
          1. Split text into khoản sections using _split_into_khoans().
          2. Locate the target khoản by index.
          3. If target_diem_letter is set, further locate the điểm within the khoản.
          4. Replace the located section with amendment.new_text.
          5. Reassemble and return.
        """
        raise NotImplementedError("T3.2: implement _apply_sua_doi()")

    def _apply_bo_sung(
        self, text: str, amendment: Amendment
    ) -> tuple[str, bool]:
        """
        Insert a new Điểm at the end of target_khoan_index.
        Or insert a new Khoản if target_khoan_index is None.

        Returns (modified_text, success: bool).

        TODO (T3.2): implement.
        """
        raise NotImplementedError("T3.2: implement _apply_bo_sung()")

    def _apply_thay_the(
        self, text: str, amendment: Amendment
    ) -> tuple[str, bool]:
        """
        Replace entire Khoản or a specific phrase with new_text.
        "Thay thế" can also replace specific wording within a khoản.

        Returns (modified_text, success: bool).

        TODO (T3.2): implement.
        """
        raise NotImplementedError("T3.2: implement _apply_thay_the()")

    def _apply_bai_bo(
        self, text: str, amendment: Amendment
    ) -> tuple[str, bool, list[int], list[str]]:
        """
        Mark target_khoan_index (or target_diem_letter) as voided.
        Replace the content with VOIDED_MARKER.

        Returns (modified_text, success, voided_khoans, voided_diems).

        TODO (T3.2): implement.
        """
        raise NotImplementedError("T3.2: implement _apply_bai_bo()")

    def _apply_het_hieu_luc(
        self, text: str, amendment: Amendment
    ) -> tuple[str, bool]:
        """
        Partial invalidation — same as bãi bỏ for the specified provision.

        TODO (T3.2): implement.
        """
        raise NotImplementedError("T3.2: implement _apply_het_hieu_luc()")

    # ------------------------------------------------------------------
    # Text structure helpers (implement these first — used by all _apply_*)
    # ------------------------------------------------------------------

    @staticmethod
    def _split_into_khoans(text: str) -> dict[int, str]:
        """
        Split article clean_text into a dict of {khoan_index: khoan_text}.
        Key 0 = text before the first numbered clause (article intro).

        Example:
          "Điều 5. Tiêu chuẩn\n1. Tiêu chuẩn A.\n2. Tiêu chuẩn B."
          → {0: "Điều 5. Tiêu chuẩn", 1: "1. Tiêu chuẩn A.", 2: "2. Tiêu chuẩn B."}

        TODO (T3.2): implement using _RE_KHOAN_HEADER.
        """
        raise NotImplementedError("T3.2: implement _split_into_khoans()")

    @staticmethod
    def _join_khoans(khoans: dict[int, str]) -> str:
        """
        Inverse of _split_into_khoans(). Reassemble text in order.
        Skips entries where value == VOIDED_MARKER? No — keep marker in text.

        TODO (T3.2): implement.
        """
        raise NotImplementedError("T3.2: implement _join_khoans()")

    @staticmethod
    def _split_into_diems(khoan_text: str) -> dict[str, str]:
        """
        Split a clause text into {diem_letter: diem_text}.
        Key "" = text before the first lettered point.

        TODO (T3.2): implement using _RE_DIEM_HEADER.
        """
        raise NotImplementedError("T3.2: implement _split_into_diems()")
