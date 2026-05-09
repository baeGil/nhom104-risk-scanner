"""
Unit tests for segmentation module — NO Neo4j or embedding service required.

Run:
    pytest src/segmentation/tests/test_parser.py -v

Fixtures below include real Vietnamese legal text snippets to test against.
"""
from __future__ import annotations

import pytest
from segmentation.models import HierarchyType, ConfidenceLevel
from segmentation.parser import (
    LegalDocumentParser,
    _is_preamble,
    _is_closing,
    _strip_html_tags,
    build_uid,
    RE_DIEU, RE_KHOAN, RE_CHUONG, RE_DIEM,
)
from segmentation.confidence import ConfidenceScorer


# ---------------------------------------------------------------------------
# Sample HTML fixtures
# ---------------------------------------------------------------------------

SAMPLE_LUAT_HTML = """
<p><b>Chương I</b></p>
<p><b>QUY ĐỊNH CHUNG</b></p>
<p><b>Điều 1. Phạm vi điều chỉnh</b></p>
<p>Luật này quy định về...</p>
<p>1. Doanh nghiệp tư nhân;</p>
<p>2. Công ty trách nhiệm hữu hạn;</p>
<p><b>Điều 2. Đối tượng áp dụng</b></p>
<p>1. Luật này áp dụng đối với:</p>
<p>a) Doanh nghiệp thành lập, hoạt động;</p>
<p>b) Tổ chức, cá nhân liên quan.</p>
<p>2. Luật này không áp dụng đối với doanh nghiệp nhà nước.</p>
"""

SAMPLE_ND_HTML = """
<p>Căn cứ Luật Tổ chức Chính phủ ngày 19 tháng 6 năm 2015;</p>
<p>Xét đề nghị của Bộ trưởng Bộ Tài chính;</p>
<p><b>Điều 1. Phạm vi điều chỉnh</b></p>
<p>Nghị định này quy định chi tiết...</p>
<p><b>Điều 2. Giải thích từ ngữ</b></p>
<p>Trong Nghị định này, các từ ngữ dưới đây được hiểu như sau:</p>
<p>1. \"Hàng hóa\" là...</p>
<p>2. \"Dịch vụ\" là...</p>
"""

SAMPLE_BO_LUAT_HTML = """
<p><b>Phần thứ nhất</b></p>
<p><b>NHỮNG QUY ĐỊNH CHUNG</b></p>
<p><b>Chương I</b></p>
<p><b>Điều 1. Nhiệm vụ của Bộ luật hình sự</b></p>
<p>Bộ luật hình sự có nhiệm vụ...</p>
"""


# ---------------------------------------------------------------------------
# Regex tests (run immediately — no TODO dependency)
# ---------------------------------------------------------------------------

class TestRegexPatterns:
    """These tests run immediately — just testing the regex catalogue."""

    def test_re_dieu_basic(self):
        m = RE_DIEU.match("Điều 5. Phạm vi")
        assert m is not None
        assert m.group(1) == "5"
        assert "Phạm vi" in m.group(2)

    def test_re_dieu_with_colon(self):
        assert RE_DIEU.match("Điều 10: Giải thích") is not None

    def test_re_dieu_lowercase(self):
        assert RE_DIEU.match("điều 3 Quy định") is not None

    def test_re_chuong(self):
        m = RE_CHUONG.match("Chương I")
        assert m and m.group(1) == "I"

    def test_re_chuong_with_title(self):
        m = RE_CHUONG.match("Chương II. QUY ĐỊNH CHUNG")
        assert m and m.group(1) == "II"

    def test_re_khoan(self):
        m = RE_KHOAN.match("1. Doanh nghiệp tư nhân")
        assert m and m.group(1) == "1"

    def test_re_khoan_no_match_bare_number(self):
        # "1)" is a Điểm, not a Khoản
        assert RE_KHOAN.match("1) something") is None

    def test_re_diem(self):
        m = RE_DIEM.match("a) Tổ chức, cá nhân")
        assert m and m.group(1) == "a"

    def test_re_diem_d_with_stroke(self):
        # đ) is a valid Điểm letter
        m = RE_DIEM.match("đ) Trường hợp khác")
        assert m is not None


class TestHelpers:
    def test_is_preamble(self):
        assert _is_preamble("Căn cứ Luật Tổ chức Chính phủ") is True
        assert _is_preamble("Điều 1. Phạm vi") is False

    def test_is_closing(self):
        assert _is_closing("Nơi nhận:") is True
        assert _is_closing("TM. CHÍNH PHỦ") is True
        assert _is_closing("Điều 5.") is False

    def test_strip_html_tags(self):
        assert _strip_html_tags("<b>Điều 1</b>") == "Điều 1"
        assert _strip_html_tags("<p>text</p>") == "text"

    def test_build_uid_article(self):
        uid = build_uid("42", HierarchyType.DIEU, dieu_idx=5)
        assert uid == "doc_42_dieu_5"

    def test_build_uid_clause(self):
        uid = build_uid("42", HierarchyType.KHOAN, dieu_idx=5, khoan_idx=2)
        assert uid == "doc_42_dieu_5_khoan_2"

    def test_build_uid_point(self):
        uid = build_uid("42", HierarchyType.DIEM, dieu_idx=5, khoan_idx=2, diem_letter="a")
        assert uid == "doc_42_dieu_5_khoan_2_diem_a"


# ---------------------------------------------------------------------------
# Parser tests (skipped until T1.1 implemented)
# ---------------------------------------------------------------------------

class TestParser:
    """Người B: un-skip and implement alongside parser.py."""

    @pytest.fixture
    def parser(self):
        return LegalDocumentParser()

    @pytest.mark.skip(reason="T1.1 not yet implemented")
    def test_parse_luat_basic(self, parser):
        result = parser.parse(doc_id="1", clean_html=SAMPLE_LUAT_HTML, loai_van_ban="Luật")
        assert result.article_count == 2
        assert result.chapter_count == 1

    @pytest.mark.skip(reason="T1.1 not yet implemented")
    def test_parse_nd_skips_preamble(self, parser):
        result = parser.parse(doc_id="2", clean_html=SAMPLE_ND_HTML, loai_van_ban="Nghị định")
        # Preamble "Căn cứ..." should be skipped
        assert result.article_count == 2
        # First article should be Điều 1, not a preamble segment
        assert result.articles()[0].index == 1

    @pytest.mark.skip(reason="T1.1 not yet implemented")
    def test_parse_bo_luat_detects_phan(self, parser):
        result = parser.parse(doc_id="3", clean_html=SAMPLE_BO_LUAT_HTML, loai_van_ban="Bộ luật")
        phan_segs = [s for s in result.segments if s.hierarchy_type == HierarchyType.PHAN]
        assert len(phan_segs) == 1

    @pytest.mark.skip(reason="T1.1 not yet implemented")
    def test_parse_clauses_have_parent_uid(self, parser):
        result = parser.parse(doc_id="1", clean_html=SAMPLE_LUAT_HTML)
        for clause in result.segments:
            if clause.hierarchy_type == HierarchyType.KHOAN:
                assert clause.parent_uid is not None, "Clause must have parent Article UID"

    @pytest.mark.skip(reason="T1.1 not yet implemented")
    def test_parse_article_uid_format(self, parser):
        result = parser.parse(doc_id="42", clean_html=SAMPLE_LUAT_HTML)
        for art in result.articles():
            assert art.uid == f"doc_42_dieu_{art.index}"

    @pytest.mark.skip(reason="T1.1 not yet implemented")
    def test_parse_empty_html(self, parser):
        result = parser.parse(doc_id="0", clean_html="")
        assert result.article_count == 0
        assert len(result.parse_errors) == 0  # empty is not an error, just 0 segments


# ---------------------------------------------------------------------------
# Confidence scorer tests (skipped until T1.2 implemented)
# ---------------------------------------------------------------------------

class TestConfidenceScorer:
    @pytest.fixture
    def scorer(self):
        return ConfidenceScorer()

    @pytest.mark.skip(reason="T1.2 not yet implemented (also needs T1.1)")
    def test_high_confidence_when_all_articles_found(self, scorer):
        from segmentation.models import ParseResult, Segment
        result = ParseResult(doc_id="1", article_count=10)
        scored = scorer.score(result, expected_article_count=10)
        assert scored.confidence_level == ConfidenceLevel.HIGH
        assert scored.confidence_score >= 0.9

    @pytest.mark.skip(reason="T1.2 not yet implemented")
    def test_low_confidence_when_few_articles_found(self, scorer):
        from segmentation.models import ParseResult
        result = ParseResult(doc_id="2", article_count=3)
        scored = scorer.score(result, expected_article_count=100)
        assert scored.confidence_level == ConfidenceLevel.LOW
