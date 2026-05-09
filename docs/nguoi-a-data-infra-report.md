# Báo cáo Hoàn thành: Người A — Data & Infrastructure

> **Dự án**: Vietnamese Legal Knowledge Graph  
> **Vai trò**: Người A — Data & Infrastructure  
> **Trạng thái**: ✅ Hoàn thành (16/17 tests PASSED — T6.2 chờ start service)

---

## Tổng Quan Pipeline

```
[Raw Data]
    │
    ▼
T0.1 Normalize so_ky_hieu ──────────────► output/so_ky_hieu_lookup.json
    │
    ▼
T0.5 Build Fuzzy Lookup ────────────────► (embedded in T0.1)
    │
    ▼
T0.2 Deduplicate ───────────────────────► data/metadata_deduped.parquet
    │                                     output/dedup_log.json
    ▼
T0.3 Crawl Missing Content ─────────────► data/content_enriched.parquet
    │                                     output/crawl_checkpoint.json
    ▼
T0.4 HTML Clean ────────────────────────► data/content_clean.parquet
    │
    ▼
T1.4 Neo4j Schema ──────────────────────► 5 constraints + 10 indexes in Neo4j
    │
    ▼
T1.7 Ingest Relationships ──────────────► (ready — chờ relationships.parquet thật)
    │
T6.1 Neo4j Setup ───────────────────────► neo4j.service running (port 7687, 7474)
T6.2 Embedding Service ─────────────────► FastAPI /embed endpoint (port 8001)
T6.3 Pipeline Orchestrator ─────────────► python -m src.data_pipeline.pipeline
```

---

## Chi tiết Từng Task

### 🟢 T0.1 — Normalize `so_ky_hieu`
**File**: `src/data_pipeline/normalize.py`  
**Mục tiêu**: Chuyển số ký hiệu thô sang định danh chuẩn để tra cứu và so sánh.

**Logic thực hiện:**
- Dùng regex multi-pattern để nhận diện từng loại văn bản (NĐ, TT, TTLT, Luật, BL).
- Tạo mã chuẩn dạng `{TYPE}-{ZERO_PADDED_NUM}-{YEAR}`.
- Phát hiện văn bản "Không số" và đánh flag đặc biệt.
- Xuất file `output/so_ky_hieu_lookup.json`.

**Ví dụ kết quả:**
| Input | Output |
|-------|--------|
| `46/2014/NĐ-CP` | `ND-046-2014` |
| `59/2020/QH14` | `LT-059-2020` |
| `12/2018/TT-BTC` | `TT-012-2018` |
| `05/2016/TTLT-NHNN-BTC` | `TTLT-005-2016` |

**Test**: ✅ 4/4 PASSED

---

### 🟢 T0.5 — Fuzzy Lookup Resolver
**File**: `src/data_pipeline/lookup.py`  
**Mục tiêu**: Tìm kiếm văn bản kể cả khi số ký hiệu bị sai chính tả nhẹ.

**Logic thực hiện:**
- **Tier 1**: Exact match.
- **Tier 2**: Levenshtein distance ≤ 2 (sai 1–2 ký tự).
- **Tier 3**: Substring / Year-based fallback.
- Tích hợp trực tiếp vào output của T0.1.

**Test**: ✅ 1/1 PASSED

---

### 🟢 T0.2 — Deduplicate Records
**File**: `src/data_pipeline/dedup.py`  
**Mục tiêu**: Loại bỏ các bản ghi văn bản trùng lặp, đảm bảo tính nhất quán của dữ liệu.

**Logic thực hiện:**
- Gom nhóm theo `(normalized_so_ky_hieu, loai_van_ban)`.
- Giữ lại bản ghi có `content_bytes` lớn nhất làm đại diện.
- Merge metadata: điền vào các trường `None` từ các bản ghi bị loại.
- Ghi log đầy đủ mọi quyết định merge vào `output/dedup_log.json`.
- Output: `data/metadata_deduped.parquet`.

**Test**: ✅ 3/3 PASSED

---

### 🟢 T0.3 — Crawl Missing Content
**File**: `src/data_pipeline/crawler.py`  
**Mục tiêu**: Tự động tải HTML nội dung các văn bản còn thiếu từ `thuvienphapluat.vn`.

**Logic thực hiện:**
- `search_document()`: Gọi URL tìm kiếm TVPL, bóc link trang chi tiết từ kết quả đầu tiên (selector `.nqTitle a`).
- `extract_content_html()`: GET trang chi tiết, bóc block nội dung (`div.content1` hoặc `div#divContentDoc`).
- `validate_content()`: Kiểm tra HTML phải chứa marker "Điều" (≥1 lần).
- `crawl_batch()`: Chạy vòng lặp với Rate limit (1.5s), retry tối đa 3 lần, ghi checkpoint sau mỗi doc thành công.
- Merge kết quả cào được vào `data/content_enriched.parquet`.

**Thiết kế nổi bật:**
- **Idempotent**: Có thể dừng/resume bất cứ lúc nào nhờ `output/crawl_checkpoint.json`.
- **Rate-limited**: 1.5 giây giữa các request để tránh bị chặn.

**Test**: ✅ 3/3 PASSED

---

### 🟢 T0.4 — HTML Cleaner
**File**: `src/data_pipeline/html_cleaner.py`  
**Mục tiêu**: Làm sạch HTML thô, loại bỏ thẻ rác, chuẩn hóa cấu trúc để Người B có thể parse.

**Logic thực hiện:**
- Xóa các thẻ rác: `<font>`, `<dir>`, `<center>`, `<marquee>`, `<blink>`, ...
- **Bắt buộc giữ lại** các thẻ cấu trúc: `<b>`, `<strong>`, `<i>`, `<em>`, `<table>`, `<p>`.
- Chuẩn hóa whitespace và encoding.
- Output: `data/content_clean.parquet` (gồm cả `raw_html` và `clean_html`).

**Test**: ✅ 2/2 PASSED

---

### 🟢 T1.4 — Neo4j Schema
**File**: `output/neo4j_schema.cypher`  
**Mục tiêu**: Thiết lập cấu trúc cơ sở dữ liệu đồ thị với đầy đủ constraints và indexes.

**Đã tạo:**
- **5 Constraints** (uniqueness): Document, Article, Clause, Point, Chapter.
- **10 Indexes**: Các index thường và full-text search cho Document (title, so_ky_hieu).
- **1 Vector Index** `article_embeddings`: 768 chiều (phục vụ vector search của T6.2).

**Apply vào Neo4j:**
```bash
cypher-shell -u neo4j -p thinhtran -f output/neo4j_schema.cypher
```

**Test**: ✅ 2/2 PASSED

---

### 🟢 T1.7 — Ingest Document-Level Relationships
**File**: `src/data_pipeline/neo4j_ingest.py`  
**Mục tiêu**: Nạp 659K mối quan hệ giữa các văn bản vào Neo4j.

**Mapping quan hệ** (17 loại):
| Tiếng Việt | Neo4j Type |
|-----------|-----------|
| Văn bản hết hiệu lực | `SUPERSEDED_BY` |
| Văn bản sửa đổi | `AMENDS` |
| Văn bản dẫn chiếu | `REFERRED_BY` |
| Văn bản bổ sung | `SUPPLEMENTS` |
| ... (17 loại tổng cộng) | ... |

**Cơ chế:**
- Batch MERGE (5,000 records/transaction) — an toàn với Neo4j.
- Validate endpoints: kiểm tra 2 đầu mối quan hệ phải tồn tại trước khi ingest.
- Ghi orphan log ra `output/orphan_relationships.json`.
- Đọc credentials từ biến môi trường (`.env`).
- **Skip gracefully** nếu `relationships.parquet` trống (dùng data thật sẽ chạy đầy đủ).

**Test**: ✅ 1/1 PASSED (kết nối thành công)

---

### 🟢 T6.1 — Neo4j Setup
**File**: `infra/neo4j/setup.sh`  
**Trạng thái**: ✅ Đang chạy (`neo4j.service active (running)`)

**Cấu hình tối ưu hóa:**
- Heap: `4GB` (cấu hình cho 900K+ nodes)
- Page Cache: `2GB`
- Bolt: `localhost:7687`
- HTTP Browser: `localhost:7474`

---

### 🟡 T6.2 — Embedding Service
**File**: `infra/embedding_service/app.py`  
**Trạng thái**: ⚠️ Code sẵn sàng, chưa khởi động

**Để start:**
```bash
cd infra/embedding_service
pip install fastapi uvicorn
uvicorn app:app --host 0.0.0.0 --port 8001
```

**API Spec (theo Interface Contract A→B):**
```
POST /embed
Body: {"texts": ["Điều 1. Phạm vi điều chỉnh..."]}
Response: {"embeddings": [[0.12, -0.34, ...]], "dims": 768}

GET /health
Response: {"status": "ok", "model": "mainguyen9/vietlegal-harrier-0.6b", "dims": 768}
```

**Model**: `mainguyen9/vietlegal-harrier-0.6b` (768 chiều, tối ưu cho văn bản pháp luật Việt Nam)  
**Test**: ❌ Chưa start service

---

### 🟢 T6.3 — Pipeline Orchestrator
**File**: `src/data_pipeline/pipeline.py`  
**Mục tiêu**: Điều phối toàn bộ pipeline theo thứ tự, idempotent, có thể resume.

**Tính năng:**
- Checkpoint: Lưu trạng thái sau mỗi task vào `output/pipeline_checkpoint.json`.
- **Resume**: Tự bỏ qua task đã xong, chỉ chạy task tiếp theo.
- **Reset**: `--reset T0.3` để chạy lại 1 task cụ thể.
- Log chi tiết với thời gian thực thi từng task.

**Chạy:**
```bash
python -m src.data_pipeline.pipeline           # Chạy từ checkpoint
python -m src.data_pipeline.pipeline --force   # Chạy lại toàn bộ
python -m src.data_pipeline.pipeline --reset T0.3  # Reset 1 task
```

---

## Kết Quả Test

```
============================================================
  NGƯỜI A — DATA & INFRA TEST SUITE
============================================================

[T0.1] Normalize so_ky_hieu
  ✅  T0.1 - Parse Nghị định → ND-046-2014
  ✅  T0.1 - Parse Luật → LT-059-2020
  ✅  T0.1 - Parse Thông tư → TT-012-2018
  ✅  T0.1 - Lookup JSON file tồn tại và có dữ liệu

[T0.2] Deduplication
  ✅  T0.2 - metadata_deduped.parquet tồn tại và có dữ liệu
  ✅  T0.2 - dedup_log.json tồn tại
  ✅  T0.2 - Không còn duplicates trong output

[T0.3] Crawler
  ✅  T0.3 - content_enriched.parquet tồn tại và có nội dung
  ✅  T0.3 - Nội dung crawl hợp lệ (>500 chars)
  ✅  T0.3 - Checkpoint file hợp lệ

[T0.4] HTML Cleaner
  ✅  T0.4 - content_clean.parquet có cột clean_html
  ✅  T0.4 - clean_html không còn thẻ rác (<font, <dir)

[T0.5] Fuzzy Lookup
  ✅  T0.5 - Lookup khớp chính xác (ND-046-2014)

[T1.4] Neo4j Schema
  ✅  T1.4 - Neo4j có đủ constraints (≥4)
  ✅  T1.4 - Neo4j có đủ indexes (≥5)

[T1.7] Neo4j Connection
  ✅  T1.7 - Kết nối Neo4j thành công

[T6.2] Embedding Service
  ❌  T6.2 - Chưa start service

============================================================
  KẾT QUẢ: 16/17 PASSED | 1 FAILED (chờ start T6.2)
============================================================
```

---

## Output Artifacts (Bàn Giao cho Người B)

| Artifact | Đường dẫn | Mục đích |
|---------|-----------|---------|
| Lookup Table | `output/so_ky_hieu_lookup.json` | Tra cứu normalized ID → doc_id |
| Clean HTML | `data/content_clean.parquet` | Nguồn để parse Điều/Khoản |
| Dedup Metadata | `data/metadata_deduped.parquet` | Danh sách văn bản không trùng |
| Neo4j Schema | `output/neo4j_schema.cypher` | Schema đã apply vào DB |
| Embedding API | `http://localhost:8001/embed` | Vector hóa đoạn văn bản |
| Neo4j Browser | `http://localhost:7474` | Xem/query đồ thị trực tiếp |

---

## Còn Lại

- **T6.2**: Start Embedding Service (`uvicorn app:app --port 8001` trong `infra/embedding_service/`)
- **T1.7**: Chạy lại khi có `data/relationships.parquet` thật (659K relationships)
- **Export 200 docs mẫu**: Xuất `sample_docs.parquet` cho Người B test parser ngay (theo Interface Contract)
