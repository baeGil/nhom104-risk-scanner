"""
Tests for effective text composition — no Neo4j required for most tests.

Run:
    pytest src/effective_text/tests/test_merger.py -v

Implemented (run immediately):
  - TestTextSplitting: _split_into_khoans, _join_khoans, _split_into_diems
  - TestValidationUtils: char_similarity, structural_match, unified_diff
  - TestHelpers: _parse_action, _parse_date, _tinh_trang_to_status

Skipped (waiting for T3.1 / T3.2):
  - TestAmendmentChain: traverse_article, traverse_all
  - TestTextMerger: compose() for all action types
"""
from __future__ import annotations

import pytest
from datetime import date

from effective_text.models import (
    AmendmentAction, Amendment, AmendmentChain,
    ComposedArticle, ValidityStatus,
)
from effective_text.merger import TextMerger, VOIDED_MARKER
from effective_text.validator import HopNhatValidator
from effective_text.chain import AmendmentChainTraverser
from effective_text.current import CurrentStatusComputer


# ---------------------------------------------------------------------------
# Sample texts
# ---------------------------------------------------------------------------

SAMPLE_ARTICLE_TEXT = """\
Điều 5. Tiêu chuẩn kỹ thuật
Hàng hóa lưu thông trên thị trường phải đáp ứng các tiêu chuẩn sau:
1. Đảm bảo chất lượng theo quy định của pháp luật.
2. Có nguồn gốc xuất xứ rõ ràng.
a) Hàng nội địa phải có giấy chứng nhận xuất xứ.
b) Hàng nhập khẩu phải có tờ khai hải quan.
3. Đảm bảo an toàn cho người sử dụng."""

SAMPLE_NEW_KHOAN_TEXT = "Tiêu chuẩn mới được cập nhật theo Nghị định sửa đổi."


# ---------------------------------------------------------------------------
# Validation utilities tests (run immediately — no stubs)
# ---------------------------------------------------------------------------

class TestValidationUtils:
    """char_similarity, structural_match, unified_diff are already implemented."""

    def test_char_similarity_identical(self):
        assert HopNhatValidator.char_similarity("abc", "abc") == 1.0

    def test_char_similarity_empty(self):
        assert HopNhatValidator.char_similarity("", "") == 1.0
        assert HopNhatValidator.char_similarity("abc", "") == 0.0

    def test_char_similarity_partial(self):
        score = HopNhatValidator.char_similarity("hello world", "hello earth")
        assert 0.5 < score < 1.0

    def test_structural_match_same(self):
        text = "1. Khoản 1\na) Điểm a\n2. Khoản 2"
        assert HopNhatValidator.structural_match(text, text) is True

    def test_structural_match_different_khoans(self):
        a = "1. Khoản 1\n2. Khoản 2"
        b = "1. Khoản 1"
        assert HopNhatValidator.structural_match(a, b) is False

    def test_unified_diff_returns_string(self):
        diff = HopNhatValidator.unified_diff("old text", "new text")
        assert isinstance(diff, str)


# ---------------------------------------------------------------------------
# Helper tests (run immediately)
# ---------------------------------------------------------------------------

class TestHelpers:

    def test_parse_action_sua_doi(self):
        action = AmendmentChainTraverser._parse_action("sua_doi")
        assert action == AmendmentAction.SUA_DOI

    def test_parse_action_vietnamese(self):
        action = AmendmentChainTraverser._parse_action("sửa đổi")
        assert action == AmendmentAction.SUA_DOI

    def test_parse_action_bai_bo(self):
        assert AmendmentChainTraverser._parse_action("bai_bo") == AmendmentAction.BAI_BO

    def test_parse_date_iso(self):
        d = AmendmentChainTraverser._parse_date("2023-06-15")
        assert d == date(2023, 6, 15)

    def test_parse_date_none(self):
        d = AmendmentChainTraverser._parse_date(None)
        assert d == date.min

    def test_tinh_trang_map_con_hieu_luc(self):
        s = CurrentStatusComputer._tinh_trang_to_status("Còn hiệu lực")
        assert s == ValidityStatus.CON_HIEU_LUC

    def test_tinh_trang_map_het_hieu_luc(self):
        s = CurrentStatusComputer._tinh_trang_to_status("Hết hiệu lực toàn bộ")
        assert s == ValidityStatus.HET_HIEU_LUC

    def test_tinh_trang_map_unknown(self):
        s = CurrentStatusComputer._tinh_trang_to_status("Chưa có hiệu lực")
        assert s == ValidityStatus.UNKNOWN


# ---------------------------------------------------------------------------
# Text splitting helpers (skipped — implement _split_into_khoans first)
# ---------------------------------------------------------------------------

class TestTextSplitting:

    @pytest.mark.skip(reason="T3.2: implement _split_into_khoans first")
    def test_split_basic(self):
        khoans = TextMerger._split_into_khoans(SAMPLE_ARTICLE_TEXT)
        assert 1 in khoans
        assert 2 in khoans
        assert 3 in khoans
        assert "chất lượng" in khoans[1]

    @pytest.mark.skip(reason="T3.2: implement _split_into_khoans first")
    def test_split_join_roundtrip(self):
        khoans = TextMerger._split_into_khoans(SAMPLE_ARTICLE_TEXT)
        reassembled = TextMerger._join_khoans(khoans)
        # Should reproduce the original (modulo whitespace)
        assert TextMerger._split_into_khoans(reassembled) == khoans

    @pytest.mark.skip(reason="T3.2: implement _split_into_diems first")
    def test_split_diems(self):
        khoan_text = "2. Có nguồn gốc xuất xứ rõ ràng.\na) Hàng nội địa.\nb) Hàng nhập khẩu."
        diems = TextMerger._split_into_diems(khoan_text)
        assert "a" in diems
        assert "b" in diems


# ---------------------------------------------------------------------------
# TextMerger.compose() tests (skipped — all _apply_* not yet implemented)
# ---------------------------------------------------------------------------

class TestTextMerger:

    @pytest.fixture
    def merger(self):
        return TextMerger()

    def _make_chain(self, amendments: list[Amendment]) -> AmendmentChain:
        return AmendmentChain(
            article_uid="doc_42_dieu_5",
            original_text=SAMPLE_ARTICLE_TEXT,
            amendments=amendments,
        )

    @pytest.mark.skip(reason="T3.2: implement compose()")
    def test_no_amendments_returns_original(self, merger):
        chain = self._make_chain([])
        result = merger.compose(chain)
        assert result.effective_text == SAMPLE_ARTICLE_TEXT
        assert result.changes_count == 0

    @pytest.mark.skip(reason="T3.2: implement _apply_sua_doi()")
    def test_sua_doi_khoan(self, merger):
        amendment = Amendment(
            source_article_uid="doc_99_dieu_1",
            source_doc_id="99",
            source_doc_ngay_ban_hanh=date(2024, 1, 1),
            action=AmendmentAction.SUA_DOI,
            target_khoan_index=1,
            new_text=SAMPLE_NEW_KHOAN_TEXT,
        )
        chain = self._make_chain([amendment])
        result = merger.compose(chain)
        assert SAMPLE_NEW_KHOAN_TEXT in result.effective_text
        assert result.changes_count == 1

    @pytest.mark.skip(reason="T3.2: implement _apply_bai_bo()")
    def test_bai_bo_khoan(self, merger):
        amendment = Amendment(
            source_article_uid="doc_99_dieu_2",
            source_doc_id="99",
            source_doc_ngay_ban_hanh=date(2024, 6, 1),
            action=AmendmentAction.BAI_BO,
            target_khoan_index=2,
        )
        chain = self._make_chain([amendment])
        result = merger.compose(chain)
        assert VOIDED_MARKER in result.effective_text
        assert 2 in result.voided_khoans

    @pytest.mark.skip(reason="T3.2: implement compose() — chronological ordering")
    def test_cascading_amendments_applied_in_order(self, merger):
        """Amendment 2 overrides Amendment 1 on same Khoản."""
        a1 = Amendment(
            source_article_uid="doc_99_dieu_1",
            source_doc_id="99",
            source_doc_ngay_ban_hanh=date(2022, 1, 1),
            action=AmendmentAction.SUA_DOI,
            target_khoan_index=1,
            new_text="Phiên bản 2022.",
        )
        a2 = Amendment(
            source_article_uid="doc_100_dieu_1",
            source_doc_id="100",
            source_doc_ngay_ban_hanh=date(2024, 1, 1),
            action=AmendmentAction.SUA_DOI,
            target_khoan_index=1,
            new_text="Phiên bản 2024.",
        )
        chain = self._make_chain([a1, a2])
        result = merger.compose(chain)
        assert "Phiên bản 2024." in result.effective_text
        assert "Phiên bản 2022." not in result.effective_text
