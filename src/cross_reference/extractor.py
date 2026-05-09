"""
Core cross-reference extractor.

Design contract
---------------
- Input : a single segment's text (str) + its metadata (doc_id, article_uid, …)
- Output: ExtractionResult — pure dataclasses, zero Neo4j I/O

Neo4j resolution (lookup + MERGE) is done by a SEPARATE writer layer
(cross_reference/writer.py) so this module can be unit-tested offline.

Usage
-----
    from cross_reference import CrossReferenceExtractor

    extractor = CrossReferenceExtractor(lookup_table)   # dict from so_ky_hieu_lookup.json

    result = extractor.extract_from_article(
        doc_id="...",
        article_uid="...",
        article_text="Theo quy định tại Điều 5 và khoản 2 Điều 10 Nghị định số 46/2014/NĐ-CP ...",
        is_modifying_doc=False,
    )
"""
from __future__ import annotations

import re
import json
import logging
from pathlib import Path
from typing import Optional

from .models import (
    InternalRef, ExternalRef, ModificationRef,
    ExtractionResult, DocType, ModAction,
)

logger = logging.getLogger(__name__)


# ===========================================================================
# Regex catalogue
# ===========================================================================

# ── Internal references ─────────────────────────────────────────────────────

# Matches: "Điều 5", "điều 10", "Ðiều 3" (alternate Đ)
_RE_DIEU = r"[ĐĐð][iíì]ều\s+(\d+)"

# Full pattern set — most specific first
_INTERNAL_PATTERNS: list[tuple[str, re.Pattern]] = [
    # "tại điểm a khoản 2 Điều 10"
    ("diem_khoan_dieu",
     re.compile(
         r"(?:tại\s+)?điểm\s+([a-z])\s+khoản\s+(\d+)\s+" + _RE_DIEU,
         re.IGNORECASE | re.UNICODE,
     )),
    # "tại khoản 2 Điều 10"
    ("khoan_dieu",
     re.compile(
         r"(?:tại\s+)?khoản\s+(\d+)\s+" + _RE_DIEU,
         re.IGNORECASE | re.UNICODE,
     )),
    # "tại các Điều 5, 6, 7"  — multi-article
    ("cac_dieu",
     re.compile(
         r"(?:tại\s+)?(?:các\s+)?" + _RE_DIEU + r"(?:\s*,\s*(\d+))+",
         re.IGNORECASE | re.UNICODE,
     )),
    # bare "Điều 10"
    ("dieu",
     re.compile(
         _RE_DIEU,
         re.IGNORECASE | re.UNICODE,
     )),
]

# ── External references ─────────────────────────────────────────────────────
# Each entry: (doc_type, pattern)
# Groups must be: (so_ky_hieu_full)  — i.e. the number/year/issuer block

_EXTERNAL_PATTERNS: list[tuple[DocType, re.Pattern]] = [
    # Luật / Bộ luật — e.g. "Luật Doanh nghiệp số 59/2020/QH14"
    (DocType.LUAT,
     re.compile(
         r"(?:Bộ\s+)?[Ll]uật\s+[\w\s]+?số\s+"
         r"(\d{1,3}/\d{4}/QH\d{1,2})",
         re.UNICODE,
     )),
    # Nghị định — e.g. "Nghị định số 46/2014/NĐ-CP"
    (DocType.NGHI_DINH,
     re.compile(
         r"[Nn]ghị\s+đ[iị]nh\s+(?:số\s+)?"
         r"(\d{1,3}/\d{4}/NĐ-CP)",
         re.UNICODE,
     )),
    # Thông tư liên tịch (before plain Thông tư — more specific)
    (DocType.TTLT,
     re.compile(
         r"[Tt]hông\s+tư\s+li[eê]n\s+t[ịi]ch\s+(?:số\s+)?"
         r"(\d{1,3}/\d{4}/TTLT-[\w-]+)",
         re.UNICODE,
     )),
    # Thông tư — e.g. "Thông tư số 12/2018/TT-BTC"
    (DocType.THONG_TU,
     re.compile(
         r"[Tt]hông\s+tư\s+(?:số\s+)?"
         r"(\d{1,3}/\d{4}/TT-[\w]+)",
         re.UNICODE,
     )),
]

# ── Modification patterns ───────────────────────────────────────────────────

_MOD_ACTION_MAP: list[tuple[ModAction, re.Pattern]] = [
    (ModAction.THAY_THE,
     re.compile(r"[Tt]hay\s+thế", re.UNICODE)),
    (ModAction.BAI_BO,
     re.compile(r"[Bb]ãi\s+bỏ", re.UNICODE)),
    (ModAction.BO_SUNG,
     re.compile(r"[Bb]ổ\s+sung", re.UNICODE)),
    (ModAction.HET_HIEU_LUC,
     re.compile(r"hết\s+hiệu\s+lực", re.UNICODE | re.IGNORECASE)),
    (ModAction.SUA_DOI,
     re.compile(r"[Ss]ửa\s+đổi", re.UNICODE)),  # least specific — check last
]

# Captures the target Điều/Khoản/Điểm inside a modification paragraph
_MOD_TARGET_PATTERN = re.compile(
    r"(?:điểm\s+(?P<point>[a-z])\s+)??"
    r"(?:khoản\s+(?P<khoan>\d+)\s+)??"
    r"[Đđ][iíì]ều\s+(?P<dieu>\d+)"
    r"(?:\s+[\w\s]+?(?:số\s+(?P<skh>\S+)))?",
    re.UNICODE,
)

# New text introduced by "như sau:" or "như sau :" block
_NEW_TEXT_PATTERN = re.compile(
    r"như\s+sau\s*:\s*[\""]?(.*?)[\""]?$",
    re.DOTALL | re.UNICODE,
)


# ===========================================================================
# Main extractor class
# ===========================================================================

class CrossReferenceExtractor:
    """
    Stateless extractor.  Create once, call repeatedly.

    Parameters
    ----------
    lookup_table : dict[str, str]
        Mapping from normalized so_ky_hieu (e.g. "ND-046-2014") → doc_id.
        Built by team-member A (T0.1 / T0.5).
        Pass an empty dict ({}) to run offline / in unit tests.
    fuzzy_enabled : bool
        Whether to attempt Levenshtein fuzzy match when exact lookup fails.
    """

    def __init__(
        self,
        lookup_table: dict[str, str],
        *,
        fuzzy_enabled: bool = True,
    ) -> None:
        self._lookup: dict[str, str] = lookup_table
        self._fuzzy_enabled = fuzzy_enabled

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def extract_from_article(
        self,
        doc_id: str,
        article_uid: str,
        article_text: str,
        *,
        clause_uid: Optional[str] = None,
        point_uid: Optional[str] = None,
        is_modifying_doc: bool = False,
    ) -> ExtractionResult:
        """
        Extract all references from a single article's text.

        Parameters
        ----------
        doc_id : str
            The Document node id this article belongs to.
        article_uid : str
            The Article.uid of this article.
        article_text : str
            Plain/clean text of the article (no HTML).
        clause_uid : str, optional
            If the text being extracted is from a specific clause, pass its uid.
        point_uid : str, optional
            If the text being extracted is from a specific point.
        is_modifying_doc : bool
            Set True for documents tagged as "Văn bản sửa đổi/bổ sung" (T2.3).
            Enables modification reference extraction.

        Returns
        -------
        ExtractionResult
            Contains parsed (not yet Neo4j-resolved) references.
            Caller is responsible for resolution + persistence (writer.py).
        """
        result = ExtractionResult(doc_id=doc_id)

        try:
            result.internal_refs = self._extract_internal(
                doc_id, article_uid, article_text, clause_uid, point_uid
            )
        except Exception as exc:
            result.parse_errors.append(f"internal [{article_uid}]: {exc}")
            logger.warning("Internal ref extraction failed for %s: %s", article_uid, exc)

        try:
            result.external_refs = self._extract_external(
                doc_id, article_uid, article_text, clause_uid, point_uid
            )
        except Exception as exc:
            result.parse_errors.append(f"external [{article_uid}]: {exc}")
            logger.warning("External ref extraction failed for %s: %s", article_uid, exc)

        if is_modifying_doc:
            try:
                result.modification_refs = self._extract_modifications(
                    doc_id, article_uid, article_text
                )
            except Exception as exc:
                result.parse_errors.append(f"modification [{article_uid}]: {exc}")
                logger.warning("Modification ref extraction failed for %s: %s", article_uid, exc)

        return result

    def resolve_external(self, ref: ExternalRef) -> ExternalRef:
        """
        Attempt to resolve ref.raw_so_ky_hieu → target_doc_id via lookup.

        Mutates `ref` in place and returns it.

        Resolution order:
        1. Exact match on normalized so_ky_hieu
        2. Fuzzy Levenshtein ≤ 2 (if fuzzy_enabled)
        3. Year + type substring fallback

        This is separated from extraction so team-member B can call it
        after the lookup table is ready, without re-running parsing.
        """
        normalized = _normalize_so_ky_hieu(ref.raw_so_ky_hieu, ref.target_doc_type)
        ref.normalized_so_ky_hieu = normalized

        # 1. Exact
        if normalized in self._lookup:
            ref.target_doc_id = self._lookup[normalized]
            ref.match_method = "exact"
            ref.confidence = 1.0
            return ref

        if not self._fuzzy_enabled:
            return ref

        # 2. Fuzzy Levenshtein
        best, dist = _fuzzy_levenshtein(normalized, self._lookup)
        if dist <= 2:
            ref.target_doc_id = self._lookup[best]
            ref.match_method = "fuzzy_levenshtein"
            ref.confidence = max(0.0, 1.0 - dist * 0.15)
            return ref

        # 3. Substring fallback (year + doc_type prefix)
        year_match = re.search(r"\d{4}", normalized)
        if year_match:
            year = year_match.group()
            prefix = normalized.split("-")[0]  # e.g. "ND", "TT", "LUAT"
            for key, doc_id in self._lookup.items():
                if year in key and key.startswith(prefix):
                    ref.target_doc_id = doc_id
                    ref.match_method = "fuzzy_substring"
                    ref.confidence = 0.6
                    return ref

        # Unresolved
        ref.target_doc_id = None
        ref.match_method = "unresolved"
        ref.confidence = 0.0
        return ref

    # -----------------------------------------------------------------------
    # Internal helpers (private)
    # -----------------------------------------------------------------------

    def _extract_internal(
        self,
        doc_id: str,
        article_uid: str,
        text: str,
        clause_uid: Optional[str],
        point_uid: Optional[str],
    ) -> list[InternalRef]:
        """
        TODO (Team B — T2.1):
        Implement using _INTERNAL_PATTERNS above.

        Expected logic:
        1. Iterate _INTERNAL_PATTERNS from most-specific to least-specific.
        2. For each regex match, build an InternalRef with:
           - target_article_index from Điều group
           - target_clause_index from Khoản group (if present)
           - target_point_label  from Điểm group (if present)
           - context_text = matched span
        3. Deduplicate (same article+clause+point = 1 ref).
        4. DO NOT resolve to UIDs here — that is done by writer.py.

        Return: list[InternalRef]
        """
        raise NotImplementedError("T2.1: implement _extract_internal")

    def _extract_external(
        self,
        doc_id: str,
        article_uid: str,
        text: str,
        clause_uid: Optional[str],
        point_uid: Optional[str],
    ) -> list[ExternalRef]:
        """
        TODO (Team B — T2.2):
        Implement using _EXTERNAL_PATTERNS above.

        Expected logic:
        1. Iterate _EXTERNAL_PATTERNS (TTLT before TT — already ordered).
        2. For each regex match:
           a. Capture raw so_ky_hieu string.
           b. Check if the match is followed by a Điều/Khoản/Điểm specifier
              using _INTERNAL_PATTERNS — if yes, populate target_article_index etc.
           c. Create ExternalRef (target_doc_id left None — resolved separately).
        3. Call self.resolve_external(ref) for each ref if lookup_table is available.

        Return: list[ExternalRef]
        """
        raise NotImplementedError("T2.2: implement _extract_external")

    def _extract_modifications(
        self,
        doc_id: str,
        article_uid: str,
        text: str,
    ) -> list[ModificationRef]:
        """
        TODO (Team B — T2.3):
        Implement using _MOD_ACTION_MAP + _MOD_TARGET_PATTERN above.

        Expected logic:
        1. Split text into sentences/clauses on Vietnamese punctuation.
        2. For each sentence:
           a. Detect action type using _MOD_ACTION_MAP (first match wins).
           b. Extract target coordinates using _MOD_TARGET_PATTERN:
              - named groups: point, khoan, dieu, skh (so_ky_hieu of target doc)
           c. If "như sau:" present, capture new_text using _NEW_TEXT_PATTERN.
           d. Build ModificationRef.
        3. If no so_ky_hieu found in the sentence, assume modification targets
           the document referenced in the article's parent Document's own citations
           (fallback: log and set raw_target_so_ky_hieu = "").

        Return: list[ModificationRef]
        """
        raise NotImplementedError("T2.3: implement _extract_modifications")


# ===========================================================================
# Utility functions (public — usable by writer.py and tests)
# ===========================================================================

def _normalize_so_ky_hieu(raw: str, doc_type: DocType) -> str:
    """
    Convert a raw so_ky_hieu string to normalized form.

    Examples
    --------
    "46/2014/NĐ-CP"          →  "ND-046-2014"
    "59/2020/QH14"            →  "LUAT-059-2020"
    "12/2018/TT-BTC"          →  "TT-012-2018"
    "05/2016/TTLT-NHNN-BTC"   →  "TTLT-005-2016"
    """
    # TODO (Team A — T0.1): replace with real implementation
    # Placeholder: strip slashes and dash-join
    cleaned = raw.strip().replace("/", "-")
    prefix = {
        DocType.LUAT:      "LUAT",
        DocType.BO_LUAT:   "LUAT",
        DocType.NGHI_DINH: "ND",
        DocType.THONG_TU:  "TT",
        DocType.TTLT:      "TTLT",
    }.get(doc_type, "DOC")
    return f"{prefix}-{cleaned}"


def _fuzzy_levenshtein(query: str, lookup: dict[str, str]) -> tuple[str, int]:
    """
    Return (best_key, edit_distance) for the closest key in lookup.
    Returns ("", 999) if lookup is empty.
    """
    if not lookup:
        return "", 999

    def _lev(a: str, b: str) -> int:
        if len(a) < len(b):
            return _lev(b, a)
        if not b:
            return len(a)
        prev = list(range(len(b) + 1))
        for i, ca in enumerate(a):
            curr = [i + 1]
            for j, cb in enumerate(b):
                curr.append(min(prev[j + 1] + 1, curr[j] + 1,
                                prev[j] + (ca != cb)))
            prev = curr
        return prev[-1]

    best_key = min(lookup.keys(), key=lambda k: _lev(query, k))
    return best_key, _lev(query, best_key)


def load_lookup_table(path: str | Path) -> dict[str, str]:
    """
    Load so_ky_hieu_lookup.json produced by Team A (T0.5).

    Expected JSON format:
        {"ND-046-2014": "doc_id_abc123", ...}
    """
    with open(path, encoding="utf-8") as f:
        return json.load(f)
