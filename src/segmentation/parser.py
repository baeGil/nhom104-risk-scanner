"""
Hierarchical legal document parser — T1.1 (Người B)

Design
------
- Input : clean_html string produced by Người A (T0.4)
- Output: ParseResult with flat list of Segment objects in document order
- Pure Python + BeautifulSoup. No Neo4j, no embedding, no I/O.
- Stateless: create once, call parse() many times.

State machine tracks:
  current_phan → current_chuong → current_muc → current_dieu
                                               → current_khoan → current_diem

Priority order (must be checked top-to-bottom per line/element):
  1. Phần   (only in Bộ luật)
  2. Chương
  3. Mục    (between Chương and Điều)
  4. Điều
  5. Khoản  (only valid inside a Điều)
  6. Điểm   (only valid inside a Khoản)
"""
from __future__ import annotations

import re
import logging
from typing import Optional

from .models import HierarchyType, Segment, ParseResult

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Regex catalogue — all patterns anchored to start of stripped text
# ---------------------------------------------------------------------------

# Phần — Part (Bộ luật only): "Phần thứ nhất", "Phần I"
RE_PHAN = re.compile(
    r"^Phần\s+(?:thứ\s+\w+|[IVX]+)",
    re.UNICODE | re.IGNORECASE,
)

# Chương — Chapter: "Chương I", "Chương II.", "CHƯƠNG III"
RE_CHUONG = re.compile(
    r"^Chương\s+([IVXLCDM]+)\s*[.:]?\s*(.*)?$",
    re.UNICODE | re.IGNORECASE,
)

# Mục — Section: "Mục 1.", "Mục 2. Tên mục"
RE_MUC = re.compile(
    r"^Mục\s+(\d+)[.:]?\s*(.*)?$",
    re.UNICODE | re.IGNORECASE,
)

# Điều — Article: "Điều 5.", "Điều 10:", "điều 3 ", "Ðiều 1", "Điều thứ 1"
RE_DIEU = re.compile(
    r"^[ĐĐð][iíìĩị]ều\s+(?:thứ\s+)?(\d+)[.\s:]\s*(.*)?$",
    re.UNICODE | re.IGNORECASE,
)

# Khoản — Clause: "1. text" — ONLY valid after a Điều is active
# NOTE: Must NOT match numbered list items like "1. Tên:" in preamble
RE_KHOAN = re.compile(
    r"^(\d+)\.\s+(.+)$",
    re.UNICODE,
)

# Điểm — Point: "a) text", "b) text" (after Khoản)
RE_DIEM = re.compile(
    r"^([a-zđ])\)\s+(.+)$",
    re.UNICODE,
)

# Điểm nhỏ — sub-point: "i) text", "ii) text", "iii) text" (rare)
RE_DIEM_NHO = re.compile(
    r"^([ivxlcdm]+)\)\s+(.+)$",
    re.UNICODE,
)

# Preamble markers — skip these blocks entirely
_PREAMBLE_MARKERS = [
    "Căn cứ",
    "Theo đề nghị",
    "Xét đề nghị",
    "Thực hiện",
    "Quốc hội nước",
    "Chính phủ nước",
]

# Signature / closing block — stop parsing after these appear
_CLOSING_MARKERS = [
    "Nơi nhận:",
    "TM. CHÍNH PHỦ",
    "TM. BỘ",
    "KT.",
    "CHỦ TỊCH",
    "BỘ TRƯỞNG",
    "TỔNG CỤC TRƯỞNG",
]


# ---------------------------------------------------------------------------
# UID builder (must match T1.4 schema from Người A)
# ---------------------------------------------------------------------------

def build_uid(
    doc_id: str,
    hierarchy_type: HierarchyType,
    dieu_idx: Optional[int] = None,
    khoan_idx: Optional[int] = None,
    diem_letter: Optional[str] = None,
) -> str:
    """
    Build stable UID for a segment node.

    Examples:
      Article  → "doc_42_dieu_5"
      Clause   → "doc_42_dieu_5_khoan_2"
      Point    → "doc_42_dieu_5_khoan_2_diem_a"
    """
    base = f"doc_{doc_id}"
    if hierarchy_type == HierarchyType.DIEU:
        return f"{base}_dieu_{dieu_idx}"
    if hierarchy_type == HierarchyType.KHOAN:
        return f"{base}_dieu_{dieu_idx}_khoan_{khoan_idx}"
    if hierarchy_type == HierarchyType.DIEM:
        return f"{base}_dieu_{dieu_idx}_khoan_{khoan_idx}_diem_{diem_letter}"
    # Chapter/Mục/Phan — no uid in current schema
    return f"{base}_{hierarchy_type.value.lower()}_{dieu_idx}"


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

class LegalDocumentParser:
    """
    Stateless hierarchical parser for Vietnamese legal documents.

    Usage
    -----
        parser = LegalDocumentParser()
        result = parser.parse(doc_id="42", clean_html="<p>Điều 1...</p>")

    Notes for implementer (T1.1)
    ----------------------------
    1. Use BeautifulSoup to extract text lines from clean_html.
       Recommended: soup.find_all(['p', 'div', 'li']) for line iteration.
    2. Strip each element's text before matching against regexes.
    3. Keep track of current_dieu_idx, current_khoan_idx throughout iteration.
    4. Attach table content (<table> elements) to the last active clause/article.
    5. "Phần" is only found in Bộ luật — safe to skip detection for ND/TT.
    6. Watch out for numbered preamble items (e.g., "1. Luật này...") that look
       like Khoản — only activate Khoản detection AFTER a Điều is seen.
    """

    def parse(
        self,
        doc_id: str,
        clean_html: str,
        *,
        expected_article_count: Optional[int] = None,
        loai_van_ban: str = "",
    ) -> ParseResult:
        """
        Parse a single document's HTML into a flat list of Segments.

        Parameters
        ----------
        doc_id : str
            Document identifier matching Document.id in Neo4j.
        clean_html : str
            Cleaned HTML string from Người A (T0.4).
            Must have <b>/<strong> preserved for heading detection.
        expected_article_count : int, optional
            If provided, used by ConfidenceScorer to compute ratio.
            Obtain from document metadata cross-references.
        loai_van_ban : str
            "Luật" | "Bộ luật" | "Nghị định" | "Thông tư" | "Thông tư liên tịch"
            Affects: Phần detection (only for Bộ luật), preamble handling.

        Returns
        -------
        ParseResult
            Flat list of Segment objects in document order.
            confidence_score is NOT set yet — call ConfidenceScorer.score() next.

        TODO (T1.1): implement this method.
        Replace the NotImplementedError below with the state machine.
        """
        from bs4 import BeautifulSoup
        result = ParseResult(doc_id=doc_id)

        soup = BeautifulSoup(clean_html, 'html.parser')
        
        # Find all block-level elements
        elements = soup.find_all(['p', 'div', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        
        # Filter out elements that contain other block elements to avoid text duplication
        block_tags = {'p', 'div', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}
        leaf_elements = []
        for el in elements:
            has_block_child = any(child.name in block_tags for child in el.find_all(True))
            if not has_block_child:
                leaf_elements.append(el)
        
        current_phan: Optional[Segment] = None
        current_chuong: Optional[Segment] = None
        current_muc_title: Optional[str] = None
        current_dieu: Optional[Segment] = None
        current_khoan: Optional[Segment] = None
        current_diem: Optional[Segment] = None
        
        for el in leaf_elements:
            raw_html = str(el)
            text = el.get_text(separator=' ', strip=True)
            
            if not text:
                continue
                
            if _is_preamble(text):
                continue
                
            # Chỉ dừng (break) khi đã có Điều (Article) được parse.
            # Tránh lỗi nhận diện nhầm "CHỦ TỊCH" / "BỘ TRƯỞNG" ở phần tiêu đề đầu văn bản.
            if result.article_count > 0 and _is_closing(text):
                break
                
            # 1. Phần
            if RE_PHAN.match(text) and "luật" in loai_van_ban.lower():
                current_phan = Segment(doc_id=doc_id, hierarchy_type=HierarchyType.PHAN, index=1, text_content=raw_html, clean_text=text, title=text)
                # Reset lower levels
                current_chuong = None
                current_muc_title = None
                current_dieu = None
                current_khoan = None
                current_diem = None
                continue
                
            # 2. Chương
            m_chuong = RE_CHUONG.match(text)
            if m_chuong:
                roman = m_chuong.group(1)
                title_text = m_chuong.group(2) or ""
                result.chapter_count += 1
                current_chuong = Segment(doc_id=doc_id, hierarchy_type=HierarchyType.CHUONG, index=result.chapter_count, text_content=raw_html, clean_text=text, roman_index=roman, title=title_text)
                result.segments.append(current_chuong)
                
                # Reset lower levels
                current_muc_title = None
                current_dieu = None
                current_khoan = None
                current_diem = None
                continue
                
            # 3. Mục
            m_muc = RE_MUC.match(text)
            if m_muc:
                current_muc_title = text
                # Reset lower levels
                current_dieu = None
                current_khoan = None
                current_diem = None
                continue
                
            # 4. Điều
            m_dieu = RE_DIEU.match(text)
            if m_dieu:
                dieu_idx = int(m_dieu.group(1))
                title_text = m_dieu.group(2) or ""
                uid = build_uid(doc_id, HierarchyType.DIEU, dieu_idx=dieu_idx)
                
                parent_uid = None
                if current_chuong:
                    # Chapter uid is not really used for cross-reference, but we use index as id
                    parent_uid = build_uid(doc_id, HierarchyType.CHUONG, dieu_idx=current_chuong.index)
                    
                path = f"Điều {dieu_idx}"
                if current_chuong:
                    path = f"Chương {current_chuong.roman_index} / {path}"
                
                current_dieu = Segment(
                    doc_id=doc_id,
                    hierarchy_type=HierarchyType.DIEU,
                    index=dieu_idx,
                    path=path,
                    text_content=raw_html,
                    clean_text=text,
                    parent_uid=parent_uid,
                    uid=uid,
                    title=title_text,
                    section=current_muc_title
                )
                result.segments.append(current_dieu)
                result.article_count += 1
                
                # Reset lower levels
                current_khoan = None
                current_diem = None
                continue
                
            # 5. Khoản
            m_khoan = RE_KHOAN.match(text)
            if m_khoan and current_dieu:
                khoan_idx = int(m_khoan.group(1))
                uid = build_uid(doc_id, HierarchyType.KHOAN, dieu_idx=current_dieu.index, khoan_idx=khoan_idx)
                
                current_khoan = Segment(
                    doc_id=doc_id,
                    hierarchy_type=HierarchyType.KHOAN,
                    index=khoan_idx,
                    path=f"{current_dieu.path} / Khoản {khoan_idx}",
                    text_content=raw_html,
                    clean_text=text,
                    parent_uid=current_dieu.uid,
                    uid=uid
                )
                result.segments.append(current_khoan)
                result.clause_count += 1
                
                # Reset lower levels
                current_diem = None
                continue
                
            # 6. Điểm
            m_diem = RE_DIEM.match(text) or RE_DIEM_NHO.match(text)
            if m_diem and current_khoan:
                letter = m_diem.group(1)
                uid = build_uid(doc_id, HierarchyType.DIEM, dieu_idx=current_dieu.index, khoan_idx=current_khoan.index, diem_letter=letter)
                
                current_diem = Segment(
                    doc_id=doc_id,
                    hierarchy_type=HierarchyType.DIEM,
                    index=0, 
                    path=f"{current_khoan.path} / Điểm {letter}",
                    text_content=raw_html,
                    clean_text=text,
                    parent_uid=current_khoan.uid,
                    uid=uid
                )
                result.segments.append(current_diem)
                result.point_count += 1
                continue
                
            # Content
            active_node = current_diem or current_khoan or current_dieu or current_chuong or current_phan
            if active_node:
                active_node.text_content += f"\n{raw_html}"
                active_node.clean_text += f"\n{text}"
                
        return result

    def parse_batch(
        self,
        documents: list[dict],
        *,
        loai_van_ban: str = "",
    ) -> list[ParseResult]:
        """
        Parse multiple documents.

        Parameters
        ----------
        documents : list of dict, each with keys:
            - "doc_id": str
            - "clean_html": str
            - "expected_article_count": int (optional)
            - "loai_van_ban": str (optional — overrides method param)

        Returns
        -------
        list[ParseResult]  — same order as input
        """
        results = []
        for doc in documents:
            lvb = doc.get("loai_van_ban", loai_van_ban)
            try:
                r = self.parse(
                    doc_id=doc["doc_id"],
                    clean_html=doc["clean_html"],
                    expected_article_count=doc.get("expected_article_count"),
                    loai_van_ban=lvb,
                )
            except NotImplementedError:
                raise
            except Exception as exc:
                logger.error("Parse failed for doc %s: %s", doc["doc_id"], exc)
                r = ParseResult(doc_id=doc["doc_id"])
                r.parse_errors.append(str(exc))
            results.append(r)
        return results


# ---------------------------------------------------------------------------
# Internal helpers (stubs — implement alongside parse())
# ---------------------------------------------------------------------------

def _is_preamble(text: str) -> bool:
    """Return True if the line is part of the preamble and should be skipped."""
    return any(text.startswith(marker) for marker in _PREAMBLE_MARKERS)


def _is_closing(text: str) -> bool:
    """Return True if the line signals end of operative content."""
    return any(marker in text for marker in _CLOSING_MARKERS)


def _strip_html_tags(html: str) -> str:
    """
    Quick tag stripper (no BeautifulSoup) for single-line use.
    For full documents, use BeautifulSoup.get_text().
    """
    return re.sub(r"<[^>]+>", "", html).strip()
