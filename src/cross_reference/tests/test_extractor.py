"""
Unit tests for CrossReferenceExtractor — NO Neo4j required.

Run:
    pytest src/cross_reference/tests/test_extractor.py -v
"""
from __future__ import annotations

import pytest
from src.cross_reference.models import DocType, ModAction
from src.cross_reference.extractor import CrossReferenceExtractor, _normalize_so_ky_hieu, _fuzzy_levenshtein

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_LOOKUP = {
    "ND-046-2014": "doc_001",
    "TT-012-2018": "doc_002",
    "LUAT-059-2020": "doc_003",
    "TTLT-005-2016": "doc_004",
}

@pytest.fixture
def extractor():
    return CrossReferenceExtractor(SAMPLE_LOOKUP, fuzzy_enabled=True)


# ---------------------------------------------------------------------------
# Internal reference tests (T2.1)
# ---------------------------------------------------------------------------

class TestInternalRefs:
    """Tests for _extract_internal — Người B implements."""

    @pytest.mark.skip(reason="T2.1 not yet implemented")
    def test_bare_dieu(self, extractor):
        result = extractor.extract_from_article(
            doc_id="doc_x", article_uid="art_1",
            article_text="theo quy định tại Điều 5 của Luật này",
        )
        assert len(result.internal_refs) == 1
        ref = result.internal_refs[0]
        assert ref.target_article_index == 5
        assert ref.target_clause_index is None

    @pytest.mark.skip(reason="T2.1 not yet implemented")
    def test_khoan_dieu(self, extractor):
        result = extractor.extract_from_article(
            doc_id="doc_x", article_uid="art_1",
            article_text="tại khoản 2 Điều 10 của Luật này",
        )
        assert len(result.internal_refs) == 1
        ref = result.internal_refs[0]
        assert ref.target_article_index == 10
        assert ref.target_clause_index == 2

    @pytest.mark.skip(reason="T2.1 not yet implemented")
    def test_diem_khoan_dieu(self, extractor):
        result = extractor.extract_from_article(
            doc_id="doc_x", article_uid="art_1",
            article_text="tại điểm a khoản 3 Điều 7",
        )
        ref = result.internal_refs[0]
        assert ref.target_article_index == 7
        assert ref.target_clause_index == 3
        assert ref.target_point_label == "a"

    @pytest.mark.skip(reason="T2.1 not yet implemented")
    def test_multi_article_reference(self, extractor):
        result = extractor.extract_from_article(
            doc_id="doc_x", article_uid="art_1",
            article_text="tại các Điều 5, 6 và 7",
        )
        assert len(result.internal_refs) == 3


# ---------------------------------------------------------------------------
# External reference tests (T2.2)
# ---------------------------------------------------------------------------

class TestExternalRefs:
    """Tests for _extract_external — Người B implements."""

    @pytest.mark.skip(reason="T2.2 not yet implemented")
    def test_nghi_dinh_exact(self, extractor):
        result = extractor.extract_from_article(
            doc_id="doc_x", article_uid="art_1",
            article_text="theo Nghị định số 46/2014/NĐ-CP của Chính phủ",
        )
        assert len(result.external_refs) == 1
        ref = result.external_refs[0]
        assert ref.raw_so_ky_hieu == "46/2014/NĐ-CP"
        assert ref.target_doc_id == "doc_001"
        assert ref.match_method == "exact"

    @pytest.mark.skip(reason="T2.2 not yet implemented")
    def test_thong_tu_exact(self, extractor):
        result = extractor.extract_from_article(
            doc_id="doc_x", article_uid="art_1",
            article_text="theo Thông tư số 12/2018/TT-BTC",
        )
        ref = result.external_refs[0]
        assert ref.target_doc_id == "doc_002"

    @pytest.mark.skip(reason="T2.2 not yet implemented")
    def test_ttlt_before_tt(self, extractor):
        """TTLT must not be matched by the plain TT pattern."""
        result = extractor.extract_from_article(
            doc_id="doc_x", article_uid="art_1",
            article_text="theo Thông tư liên tịch số 05/2016/TTLT-NHNN-BTC",
        )
        ref = result.external_refs[0]
        assert ref.target_doc_type == DocType.TTLT

    @pytest.mark.skip(reason="T2.2 not yet implemented")
    def test_external_with_article_specifier(self, extractor):
        result = extractor.extract_from_article(
            doc_id="doc_x", article_uid="art_1",
            article_text="khoản 2 Điều 5 Nghị định số 46/2014/NĐ-CP",
        )
        ref = result.external_refs[0]
        assert ref.target_article_index == 5
        assert ref.target_clause_index == 2


# ---------------------------------------------------------------------------
# Modification reference tests (T2.3)
# ---------------------------------------------------------------------------

class TestModificationRefs:
    """Tests for _extract_modifications — Người B implements."""

    @pytest.mark.skip(reason="T2.3 not yet implemented")
    def test_sua_doi_khoan_dieu(self, extractor):
        result = extractor.extract_from_article(
            doc_id="doc_mod", article_uid="art_mod_1",
            article_text="Sửa đổi khoản 2 Điều 10 Nghị định số 46/2014/NĐ-CP như sau: Nội dung mới.",
            is_modifying_doc=True,
        )
        assert len(result.modification_refs) == 1
        ref = result.modification_refs[0]
        assert ref.action == ModAction.SUA_DOI
        assert ref.target_article_index == 10
        assert ref.target_clause_index == 2
        assert ref.new_text is not None and "Nội dung mới" in ref.new_text

    @pytest.mark.skip(reason="T2.3 not yet implemented")
    def test_bai_bo(self, extractor):
        result = extractor.extract_from_article(
            doc_id="doc_mod", article_uid="art_mod_2",
            article_text="Bãi bỏ điểm a khoản 1 Điều 3",
            is_modifying_doc=True,
        )
        ref = result.modification_refs[0]
        assert ref.action == ModAction.BAI_BO
        assert ref.target_point_label == "a"

    @pytest.mark.skip(reason="T2.3 not yet implemented")
    def test_non_modifying_doc_skips_modification(self, extractor):
        result = extractor.extract_from_article(
            doc_id="doc_x", article_uid="art_1",
            article_text="Sửa đổi khoản 2 Điều 10",
            is_modifying_doc=False,
        )
        assert len(result.modification_refs) == 0


# ---------------------------------------------------------------------------
# Utility function tests (can run NOW — no TODO stubs)
# ---------------------------------------------------------------------------

class TestUtilities:

    def test_fuzzy_levenshtein_empty_lookup(self):
        key, dist = _fuzzy_levenshtein("ND-046-2014", {})
        assert dist == 999

    def test_fuzzy_levenshtein_exact_match(self):
        key, dist = _fuzzy_levenshtein("ND-046-2014", {"ND-046-2014": "x"})
        assert dist == 0 and key == "ND-046-2014"

    def test_fuzzy_levenshtein_close_match(self):
        key, dist = _fuzzy_levenshtein("ND-046-2014", {"ND-046-2015": "x", "TT-012-2018": "y"})
        assert key == "ND-046-2015" and dist == 1

    def test_resolve_external_exact(self):
        from src.cross_reference.models import ExternalRef
        ext = CrossReferenceExtractor(SAMPLE_LOOKUP)
        ref = ExternalRef(
            source_doc_id="d", source_article_uid="a",
            raw_so_ky_hieu="46/2014/NĐ-CP",
            target_doc_type=DocType.NGHI_DINH,
        )
        # Temporarily replace normalizer with one that produces our fixture key
        import src.cross_reference.extractor as mod
        orig = mod._normalize_so_ky_hieu
        mod._normalize_so_ky_hieu = lambda raw, dt: "ND-046-2014"
        ext.resolve_external(ref)
        mod._normalize_so_ky_hieu = orig
        assert ref.target_doc_id == "doc_001"
        assert ref.match_method == "exact"
