"""
Core cross-reference extractor.
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
_RE_DIEU = r"[ĐĐð][iíì]ều\s+(\d+[a-zđ]?)"

_INTERNAL_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("diem_khoan_dieu", re.compile(r"điểm\s+([a-zđ])\s+khoản\s+(\d+)\s+" + _RE_DIEU, re.IGNORECASE | re.UNICODE)),
    ("khoan_dieu", re.compile(r"khoản\s+(\d+)\s+" + _RE_DIEU, re.IGNORECASE | re.UNICODE)),
    ("dieu", re.compile(_RE_DIEU, re.IGNORECASE | re.UNICODE)),
]

# ── External references ─────────────────────────────────────────────────────
_EXTERNAL_PATTERNS: list[tuple[DocType, re.Pattern]] = [
    (DocType.LUAT, re.compile(r"(?:Bộ\s+)?[Ll]uật\s+[\w\s]+?số\s+(\d{1,3}/\d{4}/QH\d{1,2})", re.UNICODE)),
    (DocType.NGHI_DINH, re.compile(r"[Nn]ghị\s+đ[iị]nh\s+(?:số\s+)?(\d{1,3}/\d{4}/NĐ-CP)", re.UNICODE)),
    (DocType.TTLT, re.compile(r"[Tt]hông\s+tư\s+li[eê]n\s+t[ịi]ch\s+(?:số\s+)?(\d{1,3}/\d{4}/TTLT-[\w-]+)", re.UNICODE)),
    (DocType.THONG_TU, re.compile(r"[Tt]hông\s+tư\s+(?:số\s+)?(\d{1,3}/\d{4}/TT-[\w]+)", re.UNICODE)),
]

# ── Modification patterns ───────────────────────────────────────────────────
_MOD_ACTION_MAP: list[tuple[ModAction, re.Pattern]] = [
    (ModAction.THAY_THE, re.compile(r"[Tt]hay\s+thế", re.UNICODE)),
    (ModAction.BAI_BO, re.compile(r"[Bb]ãi\s+bỏ", re.UNICODE)),
    (ModAction.BO_SUNG, re.compile(r"[Bb]ổ\s+sung", re.UNICODE)),
    (ModAction.HET_HIEU_LUC, re.compile(r"hết\s+hiệu\s+lực", re.UNICODE | re.IGNORECASE)),
    (ModAction.SUA_DOI, re.compile(r"[Ss]ửa\s+đổi", re.UNICODE)),
]

_MOD_TARGET_PATTERN = re.compile(
    r"(?:(?:điểm|đpcm)\s+(?P<point>[a-zđ])\s+(?:vào\s+)?)??"
    r"(?:khoản\s+(?P<khoan>\d+)\s+)??"
    r"[Đđ][iíì]ều\s+(?P<dieu>\d+[a-zđ]?)"
    r"(?:\s+[\w\s]+?(?:số\s+(?P<skh>\S+)))?",
    re.UNICODE | re.IGNORECASE,
)

# Matches "vào sau Điều X" — the anchor article for insertion (bo_sung)
_RE_VAO_SAU = re.compile(
    r"vào\s+sau\s+[Đđ][iíì]ều\s+(?P<dieu>\d+[a-zđ]?)",
    re.UNICODE | re.IGNORECASE,
)

# Quoted content — should NOT be scanned for relationships.
# Covers: "straight ASCII", \u201c curved \u201d, and mixed open/close variants.
# Also handles the common Vietnamese legal pattern: ": " ... "" (opened with straight, closed with curved)
_OPEN_QUOTES  = '"\u201c\u2018\u2019'   # ", ", ', '
_CLOSE_QUOTES = '"\u201d\u2018\u2019'   # ", ", ', '
_RE_QUOTED = re.compile(
    r'[' + _OPEN_QUOTES + r'][^' + _CLOSE_QUOTES + r']{0,3000}?[' + _CLOSE_QUOTES + r']',
    re.DOTALL | re.UNICODE,
)


_RE_PREAMBLE_ANCHOR = re.compile(
    r"sửa\s+đổi,\s+bổ\s+sung\s+một\s+số\s+điều\s+của\s+([^,;]+?)\s+số\s+(\d+/\d+/[A-ZĐ-]+\d*)",
    re.IGNORECASE | re.UNICODE
)

_NEW_TEXT_PATTERN = re.compile(r"như\s+sau\s*:\s*['\"]?(.*?)['\"]?$", re.DOTALL | re.UNICODE)


class CrossReferenceExtractor:
    def __init__(
        self,
        lookup_table: dict[str, str],
        *,
        fuzzy_enabled: bool = True,
        short_title_map_path: Optional[str | Path] = "data/short_title_mapping.json",
    ) -> None:
        self._lookup: dict[str, str] = lookup_table
        self._fuzzy_enabled = fuzzy_enabled
        self._short_title_map: dict[str, str] = {}
        
        if short_title_map_path and Path(short_title_map_path).exists():
            try:
                with open(short_title_map_path, encoding="utf-8") as f:
                    self._short_title_map = json.load(f)
            except Exception as e:
                logger.warning("Failed to load short title map: %s", e)

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
        result = ExtractionResult(doc_id=doc_id)
        fragments = self._preprocess_text(article_text, is_modifying_doc)

        for fragment in fragments:
            occupied_spans: list[tuple[int, int]] = []

            if is_modifying_doc:
                try:
                    mods = self._extract_modifications(doc_id, article_uid, fragment)
                    result.modification_refs.extend(mods)
                    for m in mods:
                        occupied_spans.append((m.start_char, m.end_char))
                except Exception as exc:
                    result.parse_errors.append(f"modification [{article_uid}]: {exc}")

            try:
                externals = self._extract_external(doc_id, article_uid, fragment, clause_uid, point_uid)
                for ext in externals:
                    if not any(ext.start_char >= s and ext.end_char <= e for s, e in occupied_spans):
                        result.external_refs.append(ext)
                        occupied_spans.append((ext.start_char, ext.end_char))
            except Exception as exc:
                result.parse_errors.append(f"external [{article_uid}]: {exc}")

            try:
                internals = self._extract_internal(doc_id, article_uid, fragment, clause_uid, point_uid)
                for internal in internals:
                    if not any(internal.start_char >= s and internal.end_char <= e for s, e in occupied_spans):
                        result.internal_refs.append(internal)
            except Exception as exc:
                result.parse_errors.append(f"internal [{article_uid}]: {exc}")

        return result

    def _preprocess_text(self, text: str, is_modifying_doc: bool) -> list[str]:
        if not text: return []
        text = re.sub(r"\s*/\s*", "/", text)
        text = " ".join(text.split())
        if is_modifying_doc:
            # RULE 1: Strip everything after "như sau: <open-quote>" 
            # — the text after that is the NEW inserted content, NOT a reference.
            # This handles the case where the closing quote is missing (truncated segment).
            _RE_NHU_SAU_OPEN = re.compile(
                r'(như\s+sau\s*:?\s*)["' + '\u201c\u2018' + r'].*$',
                re.DOTALL | re.UNICODE | re.IGNORECASE,
            )
            text_for_scan = _RE_NHU_SAU_OPEN.sub(r'\1"…"', text)

            # RULE 2: Also strip fully-closed quoted blocks (e.g. "..." or "...")
            text_for_scan = _RE_QUOTED.sub('"…"', text_for_scan)

            raw_fragments = [f.strip() for f in text_for_scan.split(";") if f.strip()]
            final_fragments = []
            temp = ""
            for i, frag in enumerate(raw_fragments):
                if "điều" in frag.lower() or i == len(raw_fragments) - 1:
                    final_fragments.append((temp + " " + frag).strip())
                    temp = ""
                else:
                    temp += " " + frag
            return final_fragments
        return [text]

    def resolve_external(self, ref: ExternalRef) -> ExternalRef:
        if ref.raw_so_ky_hieu in self._short_title_map:
            raw_skh = self._short_title_map[ref.raw_so_ky_hieu]
            normalized = _normalize_so_ky_hieu(raw_skh, ref.target_doc_type)
            if normalized in self._lookup:
                ref.normalized_so_ky_hieu = normalized
                ref.target_doc_id = self._lookup[normalized]
                ref.match_method = "short_title_map"
                ref.confidence = 1.0
                return ref

        normalized = _normalize_so_ky_hieu(ref.raw_so_ky_hieu, ref.target_doc_type)
        ref.normalized_so_ky_hieu = normalized
        if normalized in self._lookup:
            ref.target_doc_id = self._lookup[normalized]
            ref.match_method = "exact"
            ref.confidence = 1.0
            return ref

        if not self._fuzzy_enabled: return ref
        best, dist = _fuzzy_levenshtein(normalized, self._lookup)
        if dist <= 2:
            ref.target_doc_id = self._lookup[best]
            ref.match_method = "fuzzy_levenshtein"
            ref.confidence = max(0.0, 1.0 - dist * 0.15)
        return ref

    def _extract_internal(self, doc_id, article_uid, text, clause_uid, point_uid) -> list[InternalRef]:
        refs = []; seen = set()
        for p_name, pattern in _INTERNAL_PATTERNS:
            for match in pattern.finditer(text):
                groups = match.groups()
                tp = tc = ta = None
                if p_name == "diem_khoan_dieu": tp, tc, ta = groups
                elif p_name == "khoan_dieu": tc, ta = groups
                elif p_name == "dieu": ta = groups[0]
                key = (ta, tc, tp)
                if key not in seen:
                    refs.append(InternalRef(
                        source_doc_id=doc_id, source_article_uid=article_uid,
                        source_clause_uid=clause_uid, source_point_uid=point_uid,
                        target_article_index=ta, target_clause_index=tc, target_point_label=tp,
                        context_text=match.group(0), start_char=match.start(), end_char=match.end()
                    ))
                    seen.add(key)
        return refs

    def _extract_preamble_anchor(self, preamble_text: str) -> Optional[ExternalRef]:
        if not preamble_text: return None
        start_keywords = ["ban hành", "quy định chi tiết", "hướng dẫn"]
        search_area = preamble_text
        for kw in start_keywords:
            idx = preamble_text.lower().find(kw)
            if idx != -1:
                search_area = preamble_text[idx:]
                break
        boundary = search_area.lower().find("đã được")
        if boundary != -1:
            temp_area = search_area[:boundary]
            if _RE_PREAMBLE_ANCHOR.search(temp_area):
                search_area = temp_area
        match = _RE_PREAMBLE_ANCHOR.search(search_area)
        if not match: match = _RE_PREAMBLE_ANCHOR.search(preamble_text)
        if match:
            ref = ExternalRef(source_doc_id="", source_article_uid="", raw_so_ky_hieu=match.group(2).strip(),
                              target_doc_type=DocType.LUAT, context_text=match.group(0))
            self.resolve_external(ref)
            return ref
        return None

    def _extract_external(self, doc_id, article_uid, text, clause_uid, point_uid) -> list[ExternalRef]:
        refs = []
        for title in self._short_title_map:
            if title in text:
                start_idx = text.find(title)
                ref = ExternalRef(
                    source_doc_id=doc_id, source_article_uid=article_uid, source_clause_uid=clause_uid,
                    source_point_uid=point_uid, raw_so_ky_hieu=title,
                    target_doc_type=DocType.LUAT if "Luật" in title else DocType.NGHI_DINH,
                    context_text=text[max(0, start_idx-20):start_idx+len(title)+50],
                    start_char=start_idx, end_char=start_idx+len(title)
                )
                self.resolve_external(ref)
                refs.append(ref)
        for d_type, pattern in _EXTERNAL_PATTERNS:
            for match in pattern.finditer(text):
                ref = ExternalRef(
                    source_doc_id=doc_id, source_article_uid=article_uid, source_clause_uid=clause_uid,
                    source_point_uid=point_uid, raw_so_ky_hieu=match.group(1), target_doc_type=d_type,
                    context_text=match.group(0), start_char=match.start(), end_char=match.end()
                )
                self.resolve_external(ref)
                refs.append(ref)
        return refs

    def _extract_modifications(self, doc_id, article_uid, text) -> list[ModificationRef]:
        refs = []

        # RULE: Collect "vào sau Điều X" positions so we skip them as standalone refs.
        # E.g. "Bổ sung Điều 37a vào sau Điều 37" → only one ref pointing to Điều 37.
        vao_sau_positions: set[tuple[int,int]] = set()
        for vs in _RE_VAO_SAU.finditer(text):
            vao_sau_positions.add((vs.start(), vs.end()))

        full_matches = list(_MOD_TARGET_PATTERN.finditer(text))

        # Build a set of character-start positions for Điều that are NEWLY NAMED
        # (i.e., followed immediately by "vào sau Điều X").
        # E.g. "Bổ sung Điều 37a vào sau Điều 37": 37a is the new article name → skip.
        # The real target is the Điều inside the "vào sau" span.
        _RE_AFTER_DIEU = re.compile(
            r"[\s,;]+(?:[\w\s]+?\s+)?vào\s+sau\s+[Đđ][iíì]ều",
            re.UNICODE | re.IGNORECASE,
        )

        def _is_new_article_name(m: re.Match) -> bool:
            """Return True if this Điều match is the NEW article name in 'Bổ sung Điều X vào sau Điều Y'."""
            after = text[m.end(): m.end() + 80]
            return bool(_RE_AFTER_DIEU.match(after))

        bare_pattern = re.compile(
            r"(?:điểm\s+(?P<point>[a-zđ])\s+)??"
            r"khoản\s+(?P<khoan>\d+)",
            re.UNICODE | re.IGNORECASE,
        )
        bare_matches = [
            bm for bm in bare_pattern.finditer(text)
            if not any(bm.start() >= fm.start() and bm.end() <= fm.end() for fm in full_matches)
        ]
        all_matches = sorted(full_matches + bare_matches, key=lambda x: x.start())

        last_dieu = last_skh = None
        # Seed last_dieu from the first "real target" full match (not a new-article-name)
        for m in full_matches:
            if not _is_new_article_name(m):
                last_dieu, last_skh = m.group("dieu"), m.group("skh")
                break
        # Also check vao_sau targets as seed (they are the real destination)
        if not last_dieu and vao_sau_positions:
            first_vs = _RE_VAO_SAU.search(text)
            if first_vs:
                last_dieu = first_vs.group("dieu")

        for match in all_matches:
            gd = match.groupdict()

            # If this Điều match is the NEW article name (e.g. "Điều 37a" before "vào sau Điều 37")
            # → skip emitting a ref; the real ref will come from the "vào sau" target below.
            if gd.get("dieu") and _is_new_article_name(match):
                continue

            # For "vào sau Điều X": the Điều inside this span IS the real target
            if gd.get("dieu"):
                last_dieu = gd.get("dieu")
                if gd.get("skh"):
                    last_skh = gd.get("skh")


            # Determine action from text before this match
            local_action = ModAction.SUA_DOI
            pre_text = text[:match.start()]
            for act_type, pattern in reversed(_MOD_ACTION_MAP):
                if pattern.search(pre_text):
                    local_action = act_type
                    break

            # Source Clause detection: look back for numbered list items (e.g. "1.", "2.")
            # but exclude numbers that follow "Điều" (those are article numbers)
            source_clause = None
            clause_search = []
            for cm in re.finditer(r'(?:Khoản\s+)?(\d+)\.(?!\d)', pre_text):
                lookback = pre_text[max(0, cm.start() - 10): cm.start()].lower()
                if "điều" not in lookback:
                    clause_search.append(cm.group(1))
            if clause_search:
                source_clause = clause_search[-1]

            if not last_dieu:
                continue

            ref = ModificationRef(
                source_doc_id=doc_id,
                source_article_uid=article_uid,
                source_clause_index=source_clause,
                action=local_action,
                raw_target_so_ky_hieu=gd.get("skh") or last_skh or "",
                target_article_index=gd.get("dieu") or last_dieu,
                target_clause_index=gd.get("khoan"),
                target_point_label=gd.get("point"),
                context_text=text,
                start_char=match.start(),
                end_char=match.end(),
            )
            if ref.raw_target_so_ky_hieu:
                temp = ExternalRef(
                    source_doc_id=doc_id, source_article_uid=article_uid,
                    raw_so_ky_hieu=ref.raw_target_so_ky_hieu,
                    target_doc_type=DocType.LUAT, context_text="",
                )
                self.resolve_external(temp)
                ref.target_doc_id = temp.target_doc_id
            refs.append(ref)

        # Deduplication logic: Remove general refs if a more specific one exists for the same target
        final_refs = []
        for i, r1 in enumerate(refs):
            is_redundant = False
            for j, r2 in enumerate(refs):
                if i == j: continue
                
                # Same target doc and article?
                same_doc = (r1.target_doc_id == r2.target_doc_id) if (r1.target_doc_id and r2.target_doc_id) else (r1.raw_target_so_ky_hieu == r2.raw_target_so_ky_hieu)
                if same_doc and r1.target_article_index == r2.target_article_index:
                    # R2 is strictly more specific?
                    if not r1.target_clause_index and r2.target_clause_index:
                        is_redundant = True; break
                    if (r1.target_clause_index and r1.target_clause_index == r2.target_clause_index and
                        not r1.target_point_label and r2.target_point_label):
                        is_redundant = True; break
            if not is_redundant:
                final_refs.append(r1)
        return final_refs


def _normalize_so_ky_hieu(raw: str, doc_type: DocType) -> str:
    cleaned = raw.strip().replace("/", "-")
    prefix = {DocType.LUAT: "LUAT", DocType.BO_LUAT: "LUAT", DocType.NGHI_DINH: "ND", DocType.THONG_TU: "TT", DocType.TTLT: "TTLT"}.get(doc_type, "DOC")
    return f"{prefix}-{cleaned}"

def _fuzzy_levenshtein(query, lookup):
    if not lookup: return "", 999
    def _lev(a, b):
        if len(a) < len(b): return _lev(b, a)
        if not b: return len(a)
        prev = list(range(len(b) + 1))
        for i, ca in enumerate(a):
            curr = [i + 1]
            for j, cb in enumerate(b): curr.append(min(prev[j + 1] + 1, curr[j] + 1, prev[j] + (ca != cb)))
            prev = curr
        return prev[-1]
    best_key = min(lookup.keys(), key=lambda k: _lev(query, k))
    return best_key, _lev(query, best_key)
