"""
T0.5 — Fuzzy Lookup Table
==========================

Tra cứu doc_id từ raw so_ky_hieu với nhiều chiến lược fallback.

Resolution order:
  1. Exact match trên normalized key
  2. Fuzzy Levenshtein ≤ 2
  3. Year + type + substring fallback
  4. Unresolved — flag manual review

Spec: data-cleanup-and-normalization
Task: T0.5
Depends on: T0.1 (normalize.py)
"""
from __future__ import annotations

import re
import logging
from typing import Optional

from .normalize import normalize, load_lookup

logger = logging.getLogger(__name__)

# Resolution method labels
METHOD_EXACT      = "exact"
METHOD_FUZZY_LEV  = "fuzzy_levenshtein"
METHOD_SUBSTRING  = "fuzzy_substring"
METHOD_UNRESOLVED = "unresolved"


# ---------------------------------------------------------------------------
# Main resolver class
# ---------------------------------------------------------------------------

class SoKyHieuResolver:
    """
    Tra cứu doc_id từ raw so_ky_hieu.

    Usage
    -----
        resolver = SoKyHieuResolver.from_json("output/so_ky_hieu_lookup.json")
        doc_id, method, confidence = resolver.resolve("46/2014/NĐ-CP", "Nghị định")

    Parameters
    ----------
    lookup : dict[str, str]
        Mapping normalized_so_ky_hieu → doc_id (từ T0.1).
    fuzzy_enabled : bool
        Cho phép fuzzy matching (default: True).
    max_levenshtein : int
        Ngưỡng khoảng cách Levenshtein (default: 2).
    """

    def __init__(
        self,
        lookup: dict[str, str],
        *,
        fuzzy_enabled: bool = True,
        max_levenshtein: int = 2,
    ) -> None:
        self._lookup         = lookup
        self._fuzzy_enabled  = fuzzy_enabled
        self._max_lev        = max_levenshtein

        # Stats
        self._stats = {
            METHOD_EXACT:      0,
            METHOD_FUZZY_LEV:  0,
            METHOD_SUBSTRING:  0,
            METHOD_UNRESOLVED: 0,
        }

    @classmethod
    def from_json(cls, path: str, **kwargs) -> "SoKyHieuResolver":
        """Load lookup từ JSON file (output của T0.1)."""
        lookup = load_lookup(path)
        logger.info("Loaded lookup table: %d entries from %s", len(lookup), path)
        return cls(lookup, **kwargs)

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def resolve(
        self,
        raw_so_ky_hieu: str,
        loai_van_ban: str = "",
    ) -> tuple[Optional[str], str, float]:
        """
        Tìm doc_id cho raw so_ky_hieu.

        Returns
        -------
        (doc_id, method, confidence)
          - doc_id     : str | None
          - method     : "exact" | "fuzzy_levenshtein" | "fuzzy_substring" | "unresolved"
          - confidence : float 0.0–1.0
        """
        normalized = normalize(raw_so_ky_hieu, loai_van_ban)
        if not normalized:
            self._stats[METHOD_UNRESOLVED] += 1
            return None, METHOD_UNRESOLVED, 0.0

        # 1. Exact match
        if normalized in self._lookup:
            self._stats[METHOD_EXACT] += 1
            return self._lookup[normalized], METHOD_EXACT, 1.0

        if not self._fuzzy_enabled:
            self._stats[METHOD_UNRESOLVED] += 1
            return None, METHOD_UNRESOLVED, 0.0

        # 2. Fuzzy Levenshtein
        best_key, dist = _fuzzy_levenshtein(normalized, self._lookup)
        if dist <= self._max_lev:
            confidence = max(0.0, 1.0 - dist * 0.15)
            self._stats[METHOD_FUZZY_LEV] += 1
            logger.debug(
                "Fuzzy match: '%s' → '%s' (dist=%d, conf=%.2f)",
                normalized, best_key, dist, confidence,
            )
            return self._lookup[best_key], METHOD_FUZZY_LEV, confidence

        # 3. Substring fallback (year + type prefix)
        doc_id = self._substring_fallback(normalized)
        if doc_id:
            self._stats[METHOD_SUBSTRING] += 1
            return doc_id, METHOD_SUBSTRING, 0.6

        # 4. Unresolved
        self._stats[METHOD_UNRESOLVED] += 1
        logger.debug("Unresolved: %s (normalized='%s')", raw_so_ky_hieu, normalized)
        return None, METHOD_UNRESOLVED, 0.0

    def resolve_batch(
        self,
        records: list[dict],
    ) -> list[dict]:
        """
        Resolve nhiều records cùng lúc.

        Parameters
        ----------
        records : list of dict, mỗi dict có keys:
          - raw_so_ky_hieu : str
          - loai_van_ban   : str (optional)

        Returns
        -------
        list of dict, thêm keys: doc_id, resolution_method, confidence
        """
        results = []
        for rec in records:
            doc_id, method, conf = self.resolve(
                rec.get("raw_so_ky_hieu", ""),
                rec.get("loai_van_ban", ""),
            )
            results.append({
                **rec,
                "doc_id":            doc_id,
                "resolution_method": method,
                "confidence":        conf,
            })
        return results

    def report(self) -> dict:
        """Trả về thống kê resolution."""
        total = sum(self._stats.values())
        if total == 0:
            return {"total": 0}
        resolved = total - self._stats[METHOD_UNRESOLVED]
        return {
            "total":              total,
            "resolved":           resolved,
            "resolution_rate":    resolved / total,
            "by_method":          dict(self._stats),
        }

    # -----------------------------------------------------------------------
    # Private
    # -----------------------------------------------------------------------

    def _substring_fallback(self, normalized: str) -> Optional[str]:
        """Year + type prefix substring fallback."""
        year_match = re.search(r"\d{4}", normalized)
        if not year_match:
            return None
        year   = year_match.group()
        prefix = normalized.split("-")[0]  # e.g. "ND", "TT"
        for key, doc_id in self._lookup.items():
            if year in key and key.startswith(prefix):
                return doc_id
        return None


# ---------------------------------------------------------------------------
# Utility — Levenshtein distance
# ---------------------------------------------------------------------------

def _fuzzy_levenshtein(query: str, lookup: dict[str, str]) -> tuple[str, int]:
    """
    Trả về (best_key, edit_distance) với key gần nhất trong lookup.
    Returns ("", 999) nếu lookup rỗng.
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
