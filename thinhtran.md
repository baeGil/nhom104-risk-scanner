# 📘 Hướng Dẫn Chạy Pipeline — Người A (Thịnh Trần)
---

## Mục lục

1. [Yêu cầu hệ thống](#1-yêu-cầu-hệ-thống)
2. [Cài đặt môi trường](#2-cài-đặt-môi-trường)
3. [Cấu hình biến môi trường](#3-cấu-hình-biến-môi-trường)
4. [Cài đặt Neo4j](#4-cài-đặt-neo4j-t61)
5. [Chạy Pipeline tự động](#5-chạy-pipeline-tự-động-t63)
6. [Chạy từng bước thủ công](#6-chạy-từng-bước-thủ-công)
7. [Ingest Document Nodes (nhanh)](#7-ingest-document-nodes-nhanh)
8. [Ingest Relationships từ content](#8-ingest-relationships-từ-content)
9. [Chạy Admin Portal (Streamlit)](#9-chạy-admin-portal-streamlit)
10. [Cấu trúc thư mục dữ liệu](#10-cấu-trúc-thư-mục-dữ-liệu)
11. [Xử lý lỗi thường gặp](#11-xử-lý-lỗi-thường-gặp)

---

## 1. Yêu cầu hệ thống

| Thành phần | Phiên bản tối thiểu |
|---|---|
| Python | 3.10+ |
| Neo4j | 5.18.0 |
| Java | 17 (cho Neo4j) |
| RAM | ≥ 8 GB (Neo4j cần 4 GB heap + 2 GB page cache) |
| Disk | ≥ 10 GB (data + Neo4j store) |

**Python packages cần thiết:**
```bash
pip install pandas pyarrow neo4j python-dotenv streamlit beautifulsoup4 tqdm lxml
```

---

## 2. Cài đặt môi trường

```bash
# Clone project (nếu chưa có)
cd nhom104-risk-scanner

# Tạo virtual environment
python -m venv .venv
source .venv/bin/activate

# Cài packages
pip install pandas pyarrow neo4j python-dotenv streamlit beautifulsoup4 tqdm lxml
```

---

## 3. Cấu hình biến môi trường

Tạo file `.env` từ template:

```bash
cp .env.example .env
```

Chỉnh sửa `.env` — thêm các biến Neo4j:

```env
# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=thinhtran

# LLM (tuỳ chọn, dùng cho các phase sau)
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

> ⚠️ **Lưu ý:** `NEO4J_PASSWORD` phải khớp với mật khẩu bạn đặt khi cài Neo4j.

---

## 4. Cài đặt Neo4j (T6.1)

### Cách 1: Chạy script tự động (Ubuntu/Debian)

```bash
chmod +x infra/neo4j/setup.sh
sudo ./infra/neo4j/setup.sh
```

Script sẽ tự động:
- Cài Java 17
- Cài Neo4j 5.18.0
- Cấu hình memory (heap 4 GB, page cache 2 GB)
- Bật remote connections (port 7687 Bolt, 7474 HTTP)
- Start service

### Cách 2: Thủ công

```bash
# Kiểm tra Neo4j đang chạy
sudo systemctl status neo4j

# Start Neo4j
sudo systemctl start neo4j

# Kiểm tra kết nối
curl http://localhost:7474
```

### Apply schema vào Neo4j

Sau khi Neo4j đã chạy, apply schema (tạo constraints + indexes):

```bash
cypher-shell -u neo4j -p <mật_khẩu> -f output/neo4j_schema.cypher
```

Hoặc mở Neo4j Browser tại `http://localhost:7474` và paste nội dung file `output/neo4j_schema.cypher`.

---

## 5. Chạy Pipeline tự động (T6.3)

Pipeline orchestrator chạy tất cả các bước theo thứ tự, có checkpoint (có thể resume khi lỗi).

```bash
# Chạy toàn bộ pipeline (Phase 0 + Phase 1)
python -m src.data_pipeline.pipeline

# Chỉ chạy Phase 0 (data cleanup)
python -m src.data_pipeline.pipeline --phase 0

# Chỉ chạy Phase 1 (Neo4j ingest)
python -m src.data_pipeline.pipeline --phase 1

# Xem trạng thái các task
python -m src.data_pipeline.pipeline --status

# Reset một task cụ thể để chạy lại
python -m src.data_pipeline.pipeline --reset T0.2

# Force chạy lại dù đã done
python -m src.data_pipeline.pipeline --force --phase 0
```

### Thứ tự chạy trong pipeline

```
Phase 0: Data Cleanup & Normalization
  ├── T0.1  Normalize so_ky_hieu → output/so_ky_hieu_lookup.json
  ├── T0.5  (embedded trong T0.1) Fuzzy lookup table
  ├── T0.2  Deduplicate → data/metadata_deduped.parquet
  ├── T0.3  [SKIPPED] Crawl — website thuvienphapluat.vn đã thay đổi cấu trúc
  └── T0.4  Clean HTML → data/content_clean.parquet

Phase 1: Neo4j Ingest
  ├── T1.4  Verify schema file exists (output/neo4j_schema.cypher)
  └── T1.7  Ingest 659K relationships → Neo4j
```

> ℹ️ **T0.3 (Crawl)** đã được bỏ qua vì cấu trúc trang thuvienphapluat.vn đã thay đổi. Pipeline sẽ tự động skip và tiếp tục.

---

## 6. Chạy từng bước thủ công

Nếu muốn kiểm soát từng bước hoặc debug, có thể chạy riêng lẻ:

### T0.1 — Normalize so_ky_hieu

```bash
python -m src.data_pipeline.normalize
```

- **Input:** `data/metadata.parquet`
- **Output:** `output/so_ky_hieu_lookup.json`
- **Tác dụng:** Parse số ký hiệu (vd: `46/2014/NĐ-CP` → `ND-046-2014`), build lookup table `normalized_key → doc_id`

### T0.2 — Deduplicate Documents

```bash
python -m src.data_pipeline.dedup
```

- **Input:** `data/metadata.parquet`, `output/so_ky_hieu_lookup.json`
- **Output:** `data/metadata_deduped.parquet`, `output/dedup_log.json`
- **Tác dụng:** Phát hiện và merge ~1,273 bản ghi trùng lặp, giữ bản có nhiều content nhất

### T0.3 — Crawl (SKIPPED)

> ❌ Bước này hiện bị bỏ qua. Thuvienphapluat.vn đã thay đổi cấu trúc HTML nên crawler không hoạt động.  
> Tiếp tục với dữ liệu đã có trong `data/content.parquet`.

### T0.4 — Clean HTML

```bash
python -m src.data_pipeline.html_cleaner
```

- **Input:** `data/content.parquet` (hoặc `data/content_enriched.parquet` nếu T0.3 thành công)
- **Output:** `data/content_clean.parquet`
- **Tác dụng:** Xóa thẻ `<font>`, chuẩn hóa `<p>`, giữ `<b>/<strong>` cho phát hiện hierarchy

### T1.7 — Ingest Relationships vào Neo4j

```bash
python -m src.data_pipeline.neo4j_ingest
```

- **Input:** `data/relationships.parquet`
- **Output:** Neo4j graph (17 loại relationship: CITES, AMENDS, SUPERSEDES, ...)
- **Yêu cầu:** Neo4j đang chạy và schema đã được apply (T1.4)

---

## 7. Ingest Document Nodes (nhanh)

Script nhanh để nạp ~21K Document nodes vào Neo4j (không cần chạy pipeline đầy đủ):

```bash
python scratch_ingest_nodes.py
```

- **Input:** `data/metadata_deduped.parquet`
- **Output:** ~21,000 nodes `:Document` trong Neo4j
- **Batch size:** 5,000 nodes/transaction
- **Properties:** `id`, `so_ky_hieu`, `title`, `ngay_ban_hanh`, `loai_van_ban`

---

## 8. Ingest Relationships từ content

Script extract quan hệ từ nội dung văn bản (text mining) rồi lưu ra `data/relationships.parquet`:

```bash
python scratch_extract_relations.py
```

- **Input:** `data/content_clean.parquet`, `output/final_lookup_ui.json`
- **Output:** `data/relationships.parquet`
- **Tác dụng:** Quét nội dung các văn bản, phát hiện số hiệu được nhắc đến, phân loại quan hệ theo context:
  - `CAN_CU` — "căn cứ", "theo", "chiếu"
  - `SUA_DOI` — "sửa đổi", "bổ sung"
  - `HUONG_DAN` — "hướng dẫn", "thi hành", "quy định chi tiết"
  - `THAY_THE` — "thay thế", "hủy bỏ", "bãi bỏ"
  - `LIEN_QUAN` — mặc định

Sau khi có `data/relationships.parquet`, chạy T1.7 để ingest vào Neo4j:

```bash
python -m src.data_pipeline.neo4j_ingest
```

---

## 9. Chạy Admin Portal (Streamlit)

```bash
streamlit run app.py
```

Truy cập: `http://localhost:8501`

**Các tab:**
- **🔍 Tra cứu văn bản** — Tìm kiếm theo số hiệu, xem nội dung sạch
- **🕸️ Đồ thị quan hệ** — Xem các quan hệ của văn bản trong Neo4j
- **📊 Thống kê dữ liệu** — Tổng quan, phân bổ theo loại văn bản

> **Yêu cầu:** Neo4j đang chạy + file `data/metadata_deduped.parquet` tồn tại

---

## 10. Cấu trúc thư mục dữ liệu

```
nhom104-risk-scanner/
├── .env                          # Biến môi trường (tạo từ .env.example)
├── app.py                        # Streamlit Admin Portal
├── scratch_ingest_nodes.py       # Quick script: nạp Document nodes
├── scratch_extract_relations.py  # Quick script: extract relationships từ content
│
├── data/                         # Dữ liệu (không commit vào git)
│   ├── metadata.parquet          # Raw metadata ~21K văn bản
│   ├── metadata_deduped.parquet  # Sau T0.2 dedup
│   ├── content.parquet           # Nội dung HTML thô (393 MB)
│   ├── content_clean.parquet     # Sau T0.4 clean HTML
│   └── relationships.parquet     # Quan hệ giữa văn bản
│
├── output/                       # Kết quả pipeline
│   ├── so_ky_hieu_lookup.json    # Lookup: normalized_key → doc_id (T0.1)
│   ├── final_lookup_ui.json      # Lookup đã tối ưu cho UI
│   ├── neo4j_schema.cypher       # Schema Cypher cho Neo4j (T1.4)
│   ├── dedup_log.json            # Log merge decisions (T0.2)
│   ├── orphan_relationships.json # Relationships không resolve được (T1.7)
│   └── pipeline_checkpoint.json  # Trạng thái pipeline (T6.3)
│
├── src/data_pipeline/            # Source code pipeline
│   ├── normalize.py              # T0.1: Normalize so_ky_hieu
│   ├── dedup.py                  # T0.2: Deduplicate
│   ├── crawler.py                # T0.3: Crawl (hiện bị skip)
│   ├── html_cleaner.py           # T0.4: Clean HTML
│   ├── neo4j_ingest.py           # T1.7: Ingest relationships
│   └── pipeline.py               # T6.3: Orchestrator
│
└── infra/
    ├── neo4j/setup.sh            # T6.1: Cài đặt Neo4j
    └── embedding_service/        # T6.2: Embedding service (FastAPI)
        ├── Dockerfile
        └── requirements.txt
```

---

## 11. Xử lý lỗi thường gặp

### ❌ `Neo4j: Disconnected`

```bash
# Kiểm tra service
sudo systemctl status neo4j

# Restart nếu cần
sudo systemctl restart neo4j

# Kiểm tra port
curl http://localhost:7474
```

### ❌ `FileNotFoundError: data/metadata_deduped.parquet`

- Chạy T0.2 trước: `python -m src.data_pipeline.dedup`
- Hoặc chạy toàn bộ Phase 0: `python -m src.data_pipeline.pipeline --phase 0`

### ❌ `FileNotFoundError: output/neo4j_schema.cypher`

- Chạy pipeline để generate schema: `python -m src.data_pipeline.pipeline --phase 1`
- Hoặc copy từ bạn trong nhóm đã có file này

### ❌ Pipeline bị lỗi ở giữa, muốn resume

```bash
# Xem task nào đã done, task nào failed
python -m src.data_pipeline.pipeline --status

# Reset task bị lỗi rồi chạy lại
python -m src.data_pipeline.pipeline --reset T0.4
python -m src.data_pipeline.pipeline --phase 0
```

### ❌ `relationships.parquet` chưa có

Chạy script extract relations:
```bash
python scratch_extract_relations.py
```
> Yêu cầu `data/content_clean.parquet` và `output/final_lookup_ui.json` tồn tại

---

## Thứ tự chạy đề xuất (lần đầu)

```bash
# 1. Cài môi trường
source .venv/bin/activate

# 2. Setup Neo4j (chỉ cần 1 lần)
sudo ./infra/neo4j/setup.sh

# 3. Cấu hình .env
cp .env.example .env
# Edit .env: thêm NEO4J_PASSWORD

# 4. Chạy Phase 0 (data cleanup)
python -m src.data_pipeline.pipeline --phase 0

# 5. Nạp Document nodes nhanh vào Neo4j
python scratch_ingest_nodes.py

# 6. Extract và nạp relationships
python scratch_extract_relations.py
python -m src.data_pipeline.neo4j_ingest

# 7. Kiểm tra trên Admin Portal
streamlit run app.py
```

---

*README này được viết bởi Thịnh Trần — Người A (Data & Infrastructure).*
