# Đánh Giá Spec Cross-Reference & Scaffold Summary

## 1. Coverage Analysis — 4 Loại Văn Bản

### Tổng quan coverage

| Loại văn bản | Internal Ref | External Ref (là target) | Modification Ref (là target) | Ghi chú |
|---|---|---|---|---|
| **Luật / Bộ luật** | ✅ 95% | ✅ Pattern có (`QH{session}`) | ✅ Được sửa đổi bởi ND/TT | Cấu trúc chuẩn, parser dễ |
| **Nghị định** | ✅ 95% | ✅ Pattern có (`NĐ-CP`) | ✅ Được sửa đổi bởi ND/TT khác | Flat Điều, ít Chương |
| **Thông tư** | ✅ 90% | ✅ Pattern có (`TT-{agency}`) | ✅ Được sửa đổi bởi TT khác | Nhiều format agency khác nhau |
| **Thông tư liên tịch** | ✅ 90% | ✅ Pattern có (`TTLT-{agencies}`) | ✅ Handled | Nhiều agency trong số hiệu |

**Ước tính coverage thực tế: ~85-90%** với spec hiện tại.

---

## 2. Những Gì CHƯA Được Spec Cover (Gaps)

### 🔴 Gap quan trọng

#### G1: Quyết định (QĐ) không có pattern
- Rất nhiều ND/TT dẫn chiếu đến "Quyết định số 1234/QĐ-TTg"
- Spec **không có** regex cho `QĐ-TTg`, `QĐ-BTC`, `QĐ-BCT`...
- **Ảnh hưởng**: ~15-20% external refs của TT/ND sẽ bị miss

#### G2: Tên rút gọn / viết tắt không có số hiệu
- Pattern: *"theo Luật Doanh nghiệp"* (không có "số 59/2020/QH14")
- Cần NLP/fuzzy lookup theo tên luật → doc_id
- **Ảnh hưởng**: ~10-15% trong preamble "Căn cứ..."

#### G3: Số hiệu không chuẩn — Luật cũ (trước 1999)
- Format cũ: `"Luật số 35-L/CTN"`, `"Pháp lệnh số 52-LCT/HĐNN8"`
- Regex `QH\d{2}` không match
- **Ảnh hưởng**: Nhỏ (~2-3%) nhưng cần log để không bỏ sót

#### G4: Multi-action modification trong 1 Điều
- Pattern: *"Sửa đổi khoản 1; bổ sung khoản 2; bãi bỏ khoản 3 Điều 5"*
- `_MOD_TARGET_PATTERN` hiện tại chỉ capture 1 action
- **Ảnh hưởng**: ~20% modification docs

#### G5: Dẫn chiếu ngầm (implicit reference)
- Pattern: *"theo quy định hiện hành"*, *"theo pháp luật về..."*
- Không thể resolve bằng regex — cần LLM (out of scope phase hiện tại)

### 🟡 Gap trung bình (cần workaround)

#### G6: Agency variations trong Thông tư
- `TT-BTC`, `TT-BGDĐT`, `TT-BLĐTBXH` → agency list cần được duy trì
- Nếu agency mới xuất hiện, regex sẽ miss

#### G7: Số hiệu có khoảng trắng hoặc dấu chấm
- `"Nghị định số 46 /2014/NĐ-CP"` (có space trước /)
- `"Nghị định 46.2014.NĐ-CP"` (dùng dấu chấm)
- Nên normalize trước khi match

---

## 3. Khuyến Nghị Bổ Sung Spec

```
1. Thêm DocType.QUYET_DINH với pattern: (\d{1,4}/QĐ-[A-ZĐƠƯ]+)
2. Thêm tên-luật → so_ky_hieu mapping table (lookup by keyword)
3. Multi-action split: tách câu trên dấu ";" trước khi apply _MOD_TARGET_PATTERN  
4. Pre-normalize so_ky_hieu: strip whitespace quanh "/"
```

---

## 4. Scaffold Files Đã Tạo

```
src/cross_reference/
├── __init__.py          — public API exports
├── models.py            — pure dataclasses (InternalRef, ExternalRef, ModificationRef, ...)
├── extractor.py         — CrossReferenceExtractor class + regex catalogue + TODO stubs
├── writer.py            — CrossReferenceWriter (Neo4j MERGE, chỉ file này import neo4j)
├── validator.py         — CrossReferenceValidator + ValidationReport dataclass
└── tests/
    └── test_extractor.py — pytest stubs (skipped) + runnable utility tests
```

### Interface tóm gọn

```python
# ── Người B triển khai (extractor.py) ──────────────────────────────────────
extractor = CrossReferenceExtractor(lookup_table: dict[str, str])

result: ExtractionResult = extractor.extract_from_article(
    doc_id        = "...",
    article_uid   = "...",
    article_text  = "plain text of article",
    is_modifying_doc = False,   # True cho văn bản sửa đổi
)

# result.internal_refs      → list[InternalRef]
# result.external_refs      → list[ExternalRef]
# result.modification_refs  → list[ModificationRef]
# result.parse_errors       → list[str]

# ── Người A cung cấp ───────────────────────────────────────────────────────
lookup = load_lookup_table("output/so_ky_hieu_lookup.json")
# {"ND-046-2014": "doc_id_abc", ...}

# ── Người B dùng để persist (writer.py) ────────────────────────────────────
writer = CrossReferenceWriter(neo4j_driver)
counts = writer.write(result)
# {"internal": N, "external": N, "modification": N, "errors": N}

# ── Người C đọc từ Neo4j (không cần import module này) ─────────────────────
# MATCH (a:Article)-[r:REFERENCES_EXTERNAL]->(d:Document)
# MATCH (a:Article)-[r:MODIFIES]->(b:Article)
```

### Những gì mỗi người cần làm ngay

| Người | Việc cần làm |
|-------|-------------|
| **A** | Implement `_normalize_so_ky_hieu()` trong `extractor.py` + cung cấp `so_ky_hieu_lookup.json` |
| **B** | Implement 3 stub: `_extract_internal`, `_extract_external`, `_extract_modifications` + Cypher trong `writer.py` |
| **C** | Chỉ cần đọc **Interface section** ở trên — không cần implement gì trong module này |
