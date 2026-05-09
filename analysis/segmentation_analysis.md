# Đánh Giá Spec Segmentation & Scaffold Summary

## 1. Coverage Analysis — Spec Hiện Tại

### Tổng quan: **~80–85% coverage** với 4 loại văn bản

| Loại văn bản | Cấu trúc chuẩn | Khó khăn đặc thù | Ước tính |
|---|---|---|---|
| **Luật** | Phần → Chương → Điều → Khoản → Điểm | Ít Phần, cấu trúc tương đối chuẩn | ✅ 90% |
| **Bộ luật** | Phần → Chương → Mục → Điều → Khoản → Điểm | Có cả "Phần" và "Mục" — 2 cấp không có trong spec | ⚠️ 70% |
| **Nghị định** | Chương → Điều → Khoản → Điểm | Flat (ít Chương), preamble dài | ✅ 88% |
| **Thông tư** | Điều → Khoản → Điểm (flat) | Không có Chương, nhiều bảng biểu | ✅ 85% |

---

## 2. Gaps trong Spec — Những Gì Cần Bổ Sung

### 🔴 Gap 1: `Phần` (Part) — THIẾU HOÀN TOÀN

**Ảnh hưởng**: Bộ luật Dân sự, Bộ luật Hình sự, Bộ luật Tố tụng... đều có cấu trúc:

```
Phần thứ nhất — NHỮNG QUY ĐỊNH CHUNG
  Chương I — Phạm vi điều chỉnh
    Điều 1 ...
```

**Spec hiện tại**: Không có regex hay xử lý cho "Phần thứ nhất/hai/ba" hoặc "Phần I/II".
**Cần thêm**: `RE_PHAN = r"^Phần\s+(?:thứ\s+\w+|[IVX]+)"` → HierarchyType.PHAN

---

### 🔴 Gap 2: `Mục` không hoàn chỉnh

**Spec có**: `RE_MUC = /^Mục\s+\d+\./i`
**Thiếu**: Mục có thể có dạng "Mục 1. Tên mục" hoặc "MỤC 1 - TÊN MỤC"
**Quan trọng hơn**: Spec không định nghĩa **Mục nằm ở đâu trong hierarchy**:
- Trong Luật: Mục nằm giữa Chương và Điều
- Trong ND/TT: Mục nằm dưới Điều (như subdivision)
**Cần thêm**: Context rule — Mục sau Chương = section; Mục sau Điều = subsection

---

### 🔴 Gap 3: Bảng (Table) — xử lý chưa rõ

**Spec**: "Table content attached to parent clause/article" — nhưng KHÔNG spec:
- Làm thế nào attach? Append text? Keep as separate node?
- HTML tables thường chứa danh mục, biểu phí — không parse được bằng regex
**Cần thêm**: Rõ ràng "convert table to plain text, append to parent clean_text"

---

### 🟡 Gap 4: Ký hiệu closing block — stop condition

**Spec**: Có đề cập "Căn cứ..." skip nhưng KHÔNG có stop condition khi gặp:
- "Nơi nhận:", "TM. CHÍNH PHỦ", "BỘ TRƯỞNG" → phần ký tên
- "Phụ lục" → phụ lục (thường không phải nội dung điều luật)
**Nếu không stop**: Parser sẽ tạo ra Segment rác từ phần ký tên

---

### 🟡 Gap 5: Điều không có Khoản (atomic article)

Nhiều Điều trong ND/TT không có khoản con — chỉ là 1 đoạn văn:
```
Điều 1. Phạm vi điều chỉnh
Nghị định này quy định về quản lý thuế...
```
**Spec**: Không rõ — text này thuộc về Article.text_content hay tạo Clause giả?
**Khuyến nghị**: Text trực tiếp dưới Điều (không có số thứ tự) → gán vào Article.clean_text, KHÔNG tạo Clause node.

---

### 🟡 Gap 6: Khoản nhìn giống preamble numbered list

Preamble thường có dạng:
```
Căn cứ:
1. Luật Tổ chức Chính phủ...
2. Luật Ban hành văn bản...
```
Regex `RE_KHOAN = /^\d+\.\s/` sẽ **false positive** ở đây.
**Cần thêm**: Flag `in_operative_section` — chỉ bật Khoản detection sau Điều đầu tiên.

---

### 🟡 Gap 7: Encoding & diacritics variants

Thực tế gặp 3 biến thể chữ Đ:
- `Đ` (U+0110) — chuẩn
- `Ð` (U+00D0) — Latin Extended, xuất hiện trong OCR
- `D̀` — tổ hợp dấu

**Spec**: Regex dùng `[ĐĐð][iíì]ều` nhưng chưa cover hết.
**Cần thêm**: Normalize Unicode (NFC) trước khi chạy regex.

---

## 3. Bổ Sung Khuyến Nghị vào Spec

```
1. Thêm HierarchyType.PHAN với regex: r"^Phần\s+(?:thứ\s+\w+|[IVX]+)"
2. Định nghĩa rõ vị trí Mục trong hierarchy (section vs subsection)
3. Stop condition: dừng parse khi gặp "Nơi nhận:" hoặc "TM. CHÍNH PHỦ"
4. Skip Phụ lục (Appendix): "PHỤ LỤC" → separate segment type, không ingest
5. Pre-processing: unicodedata.normalize("NFC", text) trước regex
6. Table handling: soup.find_all("table") → get_text(separator=" | ") → append to parent
```

---

## 4. Scaffold Files Đã Tạo (Người B — Phase 1)

```
src/segmentation/
├── __init__.py          — public API
├── models.py            — Segment, ParseResult, HierarchyType, ConfidenceLevel
├── parser.py            — LegalDocumentParser + regex catalogue + TODO stub (T1.1)
├── confidence.py        — ConfidenceScorer + weighted factors + TODO stub (T1.2)
├── writer.py            — SegmentWriter (Neo4j MERGE, chỉ file này import neo4j)
├── embedder.py          — ArticleEmbedder (gọi API của Người A) + TODO stubs (T1.6)
└── tests/
    └── test_parser.py   — regex tests chạy ngay + parser/confidence tests (skipped)
```

---

## 5. Interface Summary

### Input từ Người A
| Artifact | Format | SLA |
|---|---|---|
| `clean_html.parquet` | columns: `doc_id, clean_html, loai_van_ban` | Cuối tuần 2 |
| `sample_docs.parquet` | 200 docs mẫu để B test parser ngay | Cuối tuần 1 |
| Neo4j running + schema | URL + credentials | Cuối tuần 1 |
| Embedding service | `POST /embed {texts:[str]} → {embeddings:[[float]]}` | Cuối tuần 1 |

### Output cho Người B (Phase 2 — Cross-reference)
| Artifact | Format |
|---|---|
| Article nodes | `Article.uid = "doc_{id}_dieu_{index}"` |
| Clause nodes | `Clause.uid = "doc_{id}_dieu_{d}_khoan_{k}"` |
| Point nodes | `Point.uid = "doc_{id}_dieu_{d}_khoan_{k}_diem_{l}"` |

### Output cho Người C (Application Layer)
| Artifact | Format |
|---|---|
| Vector index | `"article_embeddings"` trên Neo4j (768-dim cosine) |
| `Article.embedding` | 768-dim float array |
| `Article.is_current` | Boolean — set sau Phase 3 |

---

## 6. Thứ Tự Implement (Giai Đoạn 1, Tuần 1–2)

```
Ngày 1-3: T1.1 — implement parser.py
  ├── _is_preamble, _is_closing (đã có skeleton)
  ├── _extract_lines(html) dùng BeautifulSoup
  ├── _ParserState class — state machine
  └── Test với sample_docs từ Người A

Ngày 4-5: T1.2 — implement confidence.py
  └── Chạy trên 200 docs mẫu, check distribution

Tuần 3 (chờ A xong T0.4 + T1.4):
  ├── T1.3 — parse_batch() trên 12,921 docs
  ├── T1.5 — implement writer.py Cypher stubs
  └── T1.6 — implement embedder.py
```
