# Phân Công Task — Vietnamese Legal Knowledge Graph

> **Nguyên tắc phân chia**: Dựa trên dependency graph, chia theo lớp dọc (data layer → graph layer → application layer). Mỗi người sở hữu một lớp hoàn chỉnh, giao tiếp qua **interface contracts** rõ ràng.

---

## Dependency Graph Tổng Quan

```
[Người A: Data & Infra]          [Người B: Knowledge Graph]        [Người C: Application Layer]
─────────────────────────        ──────────────────────────        ────────────────────────────
T0.1 → T0.5                      T1.1 → T1.2 → T1.3               T4.1 (skeleton)
T0.2, T0.3 → T0.4           →    T2.1, T2.2 → T2.3 → T2.4    →   T4.2 → T4.3 → T4.4 → T4.5 → T4.6
T6.1, T6.2, T6.3                 T3.1 → T3.2 → T3.3               T5.1 → T5.2 → T5.3 → T5.4
T1.4, T1.7                  →    T1.5, T1.6, T3.4, T3.5           T6.4
```

---

## Giai Đoạn 1 (Song Song — Tuần 1–2)

### 👤 Người A — Data & Infrastructure

**Phạm vi**: Chuẩn bị toàn bộ data sạch và hạ tầng DB. Output là "nguyên liệu đầu vào" cho Người B.

| Task | Mô tả ngắn | Phụ thuộc |
|------|-----------|-----------|
| **T6.1** | Cài Neo4j, cấu hình memory (heap ≥4GB, cache ≥2GB), vector index plugin | — |
| **T6.2** | Deploy embedding service `vietlegal-harrier-0.6b` (FastAPI, GPU batch) | — |
| **T6.3** | Build pipeline orchestration framework (Python, idempotent, logging) | — |
| **T0.1** | Normalize `so_ky_hieu` → parse type/number/year/issuer, tạo lookup table | — |
| **T0.2** | Deduplicate 1,273 bản trùng, merge metadata, log decisions | — |
| **T0.3** | Crawl missing content từ thuvienphapluat.vn cho 2,636 docs thiếu | — |
| **T0.4** | Clean HTML pipeline (strip tables/font, chuẩn hóa p/b/i tags) | T0.3 |
| **T0.5** | Build fuzzy matching lookup (Levenshtein ≤2, fallback) | T0.1 |
| **T1.4** | Set up Neo4j schema (node labels, constraints, indexes) | T6.1 |
| **T1.7** | Ingest 659K document-level relationships từ `relationships.parquet` | T1.4 |

**Output / Interface cho Người B**:
- `output/so_ky_hieu_lookup.json` — bảng tra cứu normalized so_ky_hieu → doc_id
- `data/clean_html/` — parquet với cả `raw_html` và `clean_html`
- Neo4j instance chạy, schema đã tạo (constraints + indexes)
- `output/neo4j_schema.cypher` — schema Cypher file
- Document-level relationships đã ingest vào Neo4j
- Embedding service API endpoint (URL + format spec)

---

### 👤 Người B — Knowledge Graph Builder

**Phạm vi**: Xây dựng parser, ingest segments, extract cross-references, compose effective text. Làm việc song song với Người A dùng **data mẫu (100-500 docs)** trong Giai đoạn 1, switch sang full data khi A xong.

| Task | Mô tả ngắn | Phụ thuộc |
|------|-----------|-----------|
| **T1.1** | Implement hierarchical parser (Chương→Điều→Khoản→Điểm state machine) | *(dùng sample data)* |
| **T1.2** | Implement confidence scoring (High/Medium/Low per doc) | T1.1 |
| **T1.3** | Parse toàn bộ 12,921 effective core docs → 104,962 segments | T0.4✓, T1.1, T1.2 |
| **T1.5** | Batch ingest segments vào Neo4j (MERGE, batch 5K) | T1.3, T1.4✓ |
| **T1.6** | Generate Article embeddings (harrier-0.6b, 768d), tạo vector index | T1.4✓, T1.5, T6.2✓ |

> **Lưu ý Giai đoạn 1**: B dùng Neo4j local + sample 200 docs do A export để test T1.1/T1.2 ngay mà không đợi full pipeline.

---

### 👤 Người C — Application Layer

**Phạm vi**: Trong Giai đoạn 1, xây dựng **skeleton/mock** của toàn bộ pipeline ứng dụng dùng data giả, để sẵn sàng "cắm" graph thật vào sau.

| Task | Mô tả ngắn | Phụ thuộc |
|------|-----------|-----------|
| **T4.1** | Implement contract parser (PyMuPDF, python-docx, Tesseract OCR) | — |
| **T5.1** | Implement question intent analysis (LLM classifier, 4 loại query) | — |
| **T6.4** | Build testing & validation suite (unit + integration test stubs) | — |

> **Lưu ý Giai đoạn 1**: C nên dùng **Neo4j mock** hoặc fixture data nhỏ (export 100 articles mẫu từ Người B) để test pipeline mà không đợi full graph.

---

## Giai Đoạn 2 (Phụ thuộc nhau — Tuần 3–4)

> **Điều kiện bắt đầu**: Người A hoàn thành T0.4 và T1.4 trước; Người B có thể bắt đầu Cross-Reference khi T1.3 xong.

### 👤 Người B — Cross-Reference & Effective Text (tiếp)

| Task | Mô tả ngắn | Phụ thuộc |
|------|-----------|-----------|
| **T2.1** | Extract internal references (regex Điều/khoản/điểm, ~100K links) | T1.3✓ |
| **T2.2** | Extract external references (cross-doc, dùng lookup từ A) | T0.5✓, T1.3✓ |
| **T2.3** | Extract modification references (3,092 modifying docs, parse MODIFIES) | T1.3✓, T2.2 |
| **T2.4** | Validate cross-references, tạo resolution report | T2.1, T2.2, T2.3 |
| **T3.1** | Implement amendment chain traversal (ordered by ngay_ban_hanh) | T2.3✓ |
| **T3.2** | Implement rule-based text merge (sửa đổi/bổ sung/thay thế/bãi bỏ) | T3.1 |
| **T3.3** | Create EffectiveArticle nodes (COMPOSED_FROM, AMENDED_BY) | T3.2 |
| **T3.4** | Validate against 35 VB hợp nhất (≥90% agreement) | T3.3 |
| **T3.5** | Compute `is_current` cho all Articles | T3.3, T1.7✓ |

---

### 👤 Người C — Application Pipeline (tiếp)

> **Điều kiện bắt đầu**: T1.6 (vector index) và T3.3 (EffectiveArticle) phải xong.

| Task | Mô tả ngắn | Phụ thuộc |
|------|-----------|-----------|
| **T4.2** | Contract clause extractor (LLM + embeddings, ContractClause nodes) | T4.1✓, T1.6✓ |
| **T4.3** | Legal provision matching (vector search top-20 + graph traversal + rerank) | T4.2, T1.6✓, T3.3✓ |
| **T4.4** | Compliance analysis (LLM: violations/risks/suggestions + citations) | T4.3 |
| **T4.5** | Citation verification (lookup Neo4j, VERIFIED/UNVERIFIED) | T4.4 |
| **T4.6** | Policy review extension (3-class classification) | T4.3, T4.4 |
| **T5.2** | Retrieval pipeline (direct lookup + vector + graph traversal) | T3.3✓, T1.6✓ |
| **T5.3** | Answer generation (LLM + cited provisions) | T5.2 |
| **T5.4** | QA citation verification (same as T4.5) | T5.3 |
| **T6.4** | Hoàn thiện test suite (integration + e2e tests) | Tất cả xong |

---

## Tóm Tắt Timeline

```
Tuần 1-2 (Song song)
├── Người A: T6.1 → T6.2 → T6.3 → T0.1 → T0.2 → T0.3 → T0.4 → T0.5 → T1.4 → T1.7
├── Người B: T1.1 → T1.2  [dùng sample data từ A]
└── Người C: T4.1 → T5.1 → T6.4 stub  [dùng mock/fixture data]

Tuần 3 (Người B bắt đầu khi A xong T0.4 + T1.4)
├── Người B: T1.3 → T1.5 → T1.6 → T2.1 → T2.2 → T2.3 → T2.4
└── Người C: Chuẩn bị T4.2 (chờ T1.6)

Tuần 4 (Người C bắt đầu khi B xong T1.6 + T3.3)
├── Người B: T3.1 → T3.2 → T3.3 → T3.4 → T3.5
└── Người C: T4.2 → T4.3 → T4.4 → T4.5 → T4.6 → T5.2 → T5.3 → T5.4 → T6.4 full
```

---

## Interface Contracts Giữa Các Thành Viên

### A → B
| Artifact | Format | SLA |
|----------|--------|-----|
| `so_ky_hieu_lookup.json` | `{"ND-046-2014": "doc_id_xyz"}` | Cuối tuần 2 |
| `clean_html.parquet` | columns: `doc_id, raw_html, clean_html` | Cuối tuần 2 |
| Neo4j instance running | URL + credentials (shared doc) | Cuối tuần 1 |
| Embedding service | `POST /embed {texts: [str]} → {embeddings: [[float]]}` | Cuối tuần 1 |
| Sample export 200 docs | `sample_docs.parquet` cho B test parser | Cuối tuần 1 |

### B → C
| Artifact | Format | SLA |
|----------|--------|-----|
| Vector index ready | Neo4j index name: `article_embeddings` | Cuối tuần 3 |
| EffectiveArticle properties | `{uid, text, is_current, as_of_date, amendment_chain}` documented | Cuối tuần 4 |
| Fixture export 100 EffectiveArticles | JSON, cho C test trước | Cuối tuần 3 |

---

## Rủi Ro & Mitigation

| Rủi Ro | Người liên quan | Mitigation |
|--------|----------------|-----------|
| Crawler T0.3 bị block (thuvienphapluat.vn đổi cấu trúc) | A | Selenium + rate limiting; fallback: skip docs thiếu content, đánh dấu để crawl sau |
| Parser T1.1 độ chính xác thấp cho edge cases | B | Bắt đầu với 100 docs mẫu, iterate nhanh; track confidence score distribution |
| LLM latency cao trong T4.2-T4.4 | C | Mock LLM với fixture response trong dev, chỉ test end-to-end cuối |
| Neo4j OOM với 900K nodes | A | Test với 10K nodes trước, tune heap/cache; dùng batch MERGE thay vì bulk import |
| T3.2 text merge sai cho edge cases phức tạp | B | Validate sớm với 35 VB hợp nhất (T3.4), dùng mismatch làm training data |
