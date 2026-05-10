# 🛠️ Người A: Quy trình Xử lý Dữ liệu & Hạ tầng (Data & Infra)

Tài liệu này mô tả chi tiết các bước xử lý dữ liệu pháp lý Việt Nam, từ dữ liệu thô (Raw Data) đến khi nạp vào Graph Database (Neo4j).

---

## 📊 Tổng quan Pipeline

Hệ thống được thiết kế để xử lý bộ dữ liệu thực tế gồm:
- **Metadata**: 153,420 bản ghi.
- **Content**: 178,665 bản ghi (~400MB HTML).
- **Relationships**: 659,481 quan hệ.

---

## 🛠️ Chi tiết các Task (Giai đoạn 1: Data Processing)

### [T0.1] Chuẩn hóa Số hiệu (Normalization)
*   **Mục tiêu**: Chuyển đổi các định dạng số hiệu khác nhau về một ID duy nhất.
*   **Input**: `data/metadata.parquet`
*   **Cơ chế**: Dùng Regex tách Loại VB - Số - Năm. (VD: `46/2014/NĐ-CP` -> `ND-046-2014`).
*   **Output**: `output/so_ky_hieu_lookup.json` (Bảng tra cứu cho Người C).

### [T0.2] Khử trùng dữ liệu (Deduplication)
*   **Mục tiêu**: Loại bỏ các bản ghi trùng lặp, chỉ giữ lại bản ghi có nội dung tốt nhất.
*   **Input**: `data/metadata.parquet` + Lookup T0.1.
*   **Kết quả**: Giảm từ 153k bản ghi xuống còn **~20,982 bản ghi duy nhất**.
*   **Output**: `data/metadata_deduped.parquet`.

### [T0.3] Thu thập nội dung bổ sung (Crawler)
*   **Mục tiêu**: Cào thêm nội dung cho những văn bản có metadata nhưng thiếu HTML.
*   **Cơ chế**: Tự động tìm kiếm và tải HTML từ Thư viện Pháp luật. 
*   **Xử lý lỗi**: Tự động bỏ qua (Skip) các văn bản cũ không có trên web (403 Forbidden) để không treo pipeline.
*   **Output**: `data/content_enriched.parquet`.

### [T0.4] Làm sạch HTML (HTML Cleaner)
*   **Mục tiêu**: Loại bỏ rác HTML, chuẩn hóa cấu trúc để AI dễ đọc.
*   **Cơ chế**: Xử lý theo đợt (Batch 2000 dòng) để tiết kiệm RAM. Xóa thẻ font, span, script; giữ lại thẻ b, table, tr, td.
*   **Output**: `data/content_clean.parquet` (Dữ liệu đầu vào cho Người B).

---

## 🏗️ Chi tiết các Task (Giai đoạn 2: Infrastructure)

### [T1.4] Khởi tạo Schema Neo4j
*   **Mục tiêu**: Tạo cấu trúc Index và Constraints cho Graph Database.
*   **Input**: `output/neo4j_schema.cypher`.
*   **Kết quả**: Đảm bảo tìm kiếm văn bản theo ID và Số hiệu đạt tốc độ mili giây.

### [T1.7] Nạp quan hệ (Ingest Relationships)
*   **Mục tiêu**: Xây dựng đồ thị liên kết giữa các văn bản.
*   **Input**: `data/relationships.parquet` (659k dòng).
*   **Cơ chế**: Nạp theo batch (5000 dòng/lần) vào localhost Neo4j.
*   **Output**: Một Knowledge Graph hoàn chỉnh sẵn sàng cho RAG.

---

## 🚀 Cách chạy lại toàn bộ quy trình
Để đồng bộ dữ liệu trên máy mới, chỉ cần chạy chuỗi lệnh sau:

```bash
# 1. Kích hoạt môi trường
pyenv activate Vin_Lab

# 2. Chạy Pipeline (Tự động resume từ bước dở dang)
set -a && source .env && set +a
python -m src.data_pipeline.pipeline
```

## 📂 Sơ đồ lưu trữ file
- `/data`: Lưu trữ các file Parquet (Metadata, Content, Samples).
- `/output`: Lưu trữ nhật ký (logs), bảng tra cứu (lookup) và schema database.
- `/src/data_pipeline`: Chứa mã nguồn xử lý của Người A.
