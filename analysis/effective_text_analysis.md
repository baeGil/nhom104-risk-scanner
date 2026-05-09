# Đánh Giá Spec Effective Text Composition & Scaffold Summary

## 1. Coverage Analysis — Spec Hiện Tại

**Ước tính coverage: ~75–80%** — spec đủ để bắt đầu implement nhưng có nhiều edge case quan trọng chưa được định nghĩa.

---

## 2. Gaps Trong Spec — Những Gì Cần Bổ Sung

### 🔴 Gap 1: Không định nghĩa cách LOCATE Khoản/Điểm trong văn bản gốc

Spec nói "replace the text of the specified Khoản" nhưng KHÔNG định nghĩa:
- Khoản được định vị bằng **số thứ tự** hay **nội dung**?
- Nếu text parse sai và Khoản 3 của Điều 5 không tìm thấy → xử lý thế nào?

**Cần thêm**: Spec rõ ràng về cách split Article.clean_text thành dict `{khoan_index: text}`.

---

### 🔴 Gap 2: "bổ sung" — chèn vào đâu?

Spec nói "Insert a new Điểm after existing points" nhưng:
- **Bổ sung Khoản mới** (không phải Điểm): chèn sau Khoản cuối cùng? hay vị trí cụ thể?
- Pattern thực tế: *"Bổ sung khoản 2a vào sau khoản 2 Điều 5"* — số thứ tự fractional?
- **Bổ sung vào cuối Điều** mà không có số khoản cụ thể?

**Cần thêm**: Phân loại rõ 3 sub-case của bổ sung:
- `bo_sung_diem`: thêm Điểm vào cuối Khoản đã có
- `bo_sung_khoan`: thêm Khoản mới vào cuối Điều
- `bo_sung_khoan_chen`: chèn Khoản vào vị trí cụ thể (hiếm, cần LLM)

---

### 🔴 Gap 3: "thay thế cụm từ" — substring replacement

Pattern thực tế: *"Thay thế cụm từ 'A' tại khoản 2 Điều 5 bằng cụm từ 'B'"*
→ Đây là **substring replacement**, khác hoàn toàn với clause replacement.

Spec gộp chung "thay thế" không phân biệt 2 loại:
- `thay_the_khoan`: replace toàn bộ Khoản
- `thay_the_cum_tu`: replace cụm từ (cần regex/string search)

**Cần thêm**: 2 sub-action rõ ràng.

---

### 🔴 Gap 4: Transitive chain — spec mơ hồ

Spec đề cập "handle transitive chains (A modifies B which was modified by C)"
nhưng KHÔNG định nghĩa:
- Thứ tự áp dụng: áp C trước hay áp sửa đổi của A trước?
- Nếu A sửa Khoản 1 và B cũng sửa Khoản 1 từ kết quả của A → dùng text sau A làm gốc?

**Khuyến nghị**: Luôn dùng **original Article text** làm gốc, áp tất cả amendments theo ngày_ban_hanh ASC. Không "compose on top of compose".

---

### 🟡 Gap 5: EffectiveArticle versioning — nhiều phiên bản qua thời gian

Spec cho phép nhiều EffectiveArticle cho cùng một Article (as_of_date khác nhau) nhưng không định nghĩa:
- Khi nào tạo phiên bản mới vs cập nhật phiên bản cũ?
- Người C cần phiên bản **tại thời điểm X** → không chỉ is_current=true là đủ

**Cần thêm**: API cho time-travel query: *"EffectiveArticle có hiệu lực vào ngày 2023-01-01 là gì?"*

---

### 🟡 Gap 6: 35 VB hợp nhất — cách xác định "nào ghép với nào"?

Spec nói "find the corresponding original Document" nhưng không định nghĩa cách map:
- Theo relationship type trong Neo4j? (DETAILS/DETAILED_BY? hay COMPOSED_FROM?)
- Theo tên? ("Văn bản hợp nhất số X/Y/VBHN-...")
- VB hợp nhất có thể gộp nhiều văn bản gốc → cần map 1-nhiều

**Cần thêm**: Rõ ràng VB hợp nhất được link qua relationship type nào trong Neo4j.

---

### 🟡 Gap 7: BAI_BO toàn bộ Điều

Spec chỉ đề cập bãi bỏ Khoản/Điểm, không đề cập **bãi bỏ toàn bộ Điều**:
- Pattern: *"Bãi bỏ Điều 5 Nghị định số 46/2014/NĐ-CP"*
- → Toàn bộ Article.is_current = False

**Cần thêm**: Case bãi bỏ toàn Article (không chỉ Khoản).

---

## 3. Bổ Sung Khuyến Nghị vào Spec

```
1. Định nghĩa _split_into_khoans() algorithm: regex r"^\d+\.\s" với re.MULTILINE
2. Phân loại rõ bo_sung thành 3 sub-case
3. Phân loại rõ thay_the thành 2 sub-case (khoan vs cum_tu)
4. Transitive chain: luôn dùng original text làm gốc, apply theo ngay_ban_hanh ASC
5. Thêm BAI_BO toàn Article (target_khoan_index = None, target_diem_letter = None)
6. Định nghĩa VB hợp nhất linkage: dùng relationship type VBHN_OF (cần add vào schema)
7. Time-travel query interface cho EffectiveArticle
```

---

## 4. Scaffold Files Đã Tạo (Người B — Phase 3)

```
src/effective_text/
├── __init__.py          — public API
├── models.py            — AmendmentAction, Amendment, AmendmentChain,
│                          ComposedArticle, ValidationMatch, ValidityReport, ...
├── chain.py             — AmendmentChainTraverser (T3.1) + TODO stubs
├── merger.py            — TextMerger (T3.2) — PURE PYTHON, no DB
│                          + _split_into_khoans/_join_khoans/_split_into_diems stubs
├── writer.py            — EffectiveArticleWriter (T3.3) + T3.5 Cypher stubs
├── validator.py         — HopNhatValidator (T3.4) — char_similarity/structural_match ĐÃ IMPLEMENT
├── current.py           — CurrentStatusComputer (T3.5) + priority algorithm docs
└── tests/
    └── test_merger.py   — ValidationUtils tests chạy ngay ✅ + merger tests (skipped)
```

---

## 5. Interface Summary

### Input từ Người B (Phase 2 — Cross-reference)

| Artifact | Mô tả |
|---|---|
| `[:MODIFIES]` relationships | Phải tồn tại trong Neo4j trước khi Phase 3 bắt đầu |
| `Amendment.action` values | Enum strings: `"sua_doi"`, `"bo_sung"`, `"thay_the"`, `"bai_bo"`, `"het_hieu_luc"` |
| `Amendment.new_text` | Không được NULL với action = SUA_DOI/BO_SUNG/THAY_THE |

### Input từ Người A

| Artifact | Mô tả |
|---|---|
| `[:SUPERSEDES]`, `[:PARTIALLY_SUPERSEDES]` | Doc-level relationships từ T1.7 |
| `Document.tinh_trang_hieu_luc` | String field trên Document node |

### Output cho Người C (T4.3, T5.2)

| Artifact | Neo4j Query |
|---|---|
| Effective text hiện tại | `MATCH (ea:EffectiveArticle {is_current:true})-[:COMPOSED_FROM]->(a:Article {uid:$uid}) RETURN ea.effective_text` |
| Lịch sử sửa đổi | `MATCH (ea:EffectiveArticle)-[:AMENDED_BY]->(src:Article) RETURN src.uid ORDER BY r.order` |
| Validity check | `MATCH (a:Article {uid:$uid}) RETURN a.is_current, a.effective_date` |
| Điều đã bị bãi bỏ | `MATCH (a:Article {is_current: false}) RETURN a.uid, a.effective_date` |

---

## 6. Thứ Tự Implement (Giai Đoạn 2, Tuần 3–4)

```
Tiên quyết: T2.3 (MODIFIES relationships) phải xong trước

Ngày 1-2: T3.2 — merger.py (implement từ dưới lên)
  ├── _split_into_khoans() + _join_khoans() + _split_into_diems()
  │   [test ngay với TestTextSplitting]
  ├── _apply_sua_doi() — case quan trọng nhất
  ├── _apply_bai_bo()  — thứ hai
  ├── _apply_bo_sung() + _apply_thay_the()
  └── compose() — gắn tất cả lại

Ngày 3: T3.1 — chain.py
  └── traverse_article() + traverse_all()
  [cần Neo4j có MODIFIES edges]

Ngày 4: T3.3 — writer.py Cypher stubs
  └── merge_effective_article() + link_composed_from() + link_amended_by()

Ngày 5: T3.4 — validator.py
  └── validate() so sánh với 35 VB hợp nhất
  [char_similarity + structural_match đã sẵn sàng]

Ngày 6: T3.5 — current.py + writer.write_validity()
  └── compute_all() 5-step priority algorithm
```

---

## 7. Rủi Ro Đặc Thù Phase 3

| Rủi ro | Xác suất | Mitigation |
|--------|----------|-----------|
| Không locate được Khoản target (parse khác nhau giữa modifying doc và original) | Cao | Dùng fuzzy text match khi exact index match fail; log warning |
| "bổ sung" không biết chèn vào đâu | Trung bình | Mặc định append vào cuối Điều; log để review |
| VB hợp nhất agreement < 90% | Trung bình | Dùng mismatch làm training data; không block release |
| Circular amendment chain (A modifies B modifies A) | Thấp | Detect cycle với visited set; MAX_CHAIN_DEPTH=10 |
