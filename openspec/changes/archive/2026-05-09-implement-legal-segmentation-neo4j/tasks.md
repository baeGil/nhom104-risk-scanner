## 1. Parser & Models (T1.1, T1.2)

- [x] 1.1 Cập nhật `src/segmentation/models.py`: Thêm thuộc tính `section` vào dataclass `Segment` và cấu hình 1024 chiều cho embedding.
- [x] 1.2 Triển khai `LegalDocumentParser.parse()`: Xây dựng state machine sử dụng BeautifulSoup để bóc tách Chương, Điều, Khoản, Điểm.
- [x] 1.3 Triển khai Logic Reset Hierarchy: Đảm bảo xóa bỏ ngữ cảnh `Mục` (Section) khi gặp `Chương` hoặc `Phần` mới.
- [x] 1.4 Triển khai `ConfidenceScorer.score()`: Tính toán độ tin cậy dựa trên tỷ lệ Điều tìm thấy và tính nhất quán của định dạng HTML.

## 2. Ingest & Embedding (T1.5, T1.6)

- [x] 2.1 Triển khai `SegmentWriter`: Viết các câu lệnh Cypher sử dụng `UNWIND` với batch size 5,000 để nạp dữ liệu vào Neo4j.
- [x] 2.2 Triển khai Logic "Rich Contextualization": Ghép Tên luật + Điều vào nội dung trước khi gọi Embedding API.
- [x] 2.3 Triển khai `ArticleEmbedder`: Gọi API embedding 1024 chiều và cập nhật thuộc tính `embedding` cho Article nodes trong Neo4j.
- [x] 2.4 Cập nhật Neo4j Schema: Chỉnh sửa `article_embeddings` vector index từ 768 lên 1024 dimensions.

## 3. Execution & Batch Processing (T1.3)

- [x] 3.1 Triển khai luồng đọc dữ liệu (Option 1): Load Metadata vào RAM dictionary và Join với file Content theo `doc_id`.
- [x] 3.2 Chạy Parser trên toàn bộ 12,921 văn bản: Theo dõi tiến độ và log các văn bản có độ tin cậy thấp (Low Confidence).
- [x] 3.3 Thực hiện Ingest và Embedding toàn bộ dữ liệu: Kiểm tra tính toàn vẹn của Graph và hiệu suất của Vector Index 1024-dim.
