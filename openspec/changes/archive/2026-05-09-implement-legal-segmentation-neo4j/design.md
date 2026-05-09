## Context

Dự án đang ở Phase 1: Segmentation. Chúng ta cần chuyển đổi 12,921 văn bản pháp luật từ dạng HTML sang dạng Graph (Neo4j). Thách thức nằm ở tính phi cấu trúc của HTML gốc, khối lượng dữ liệu lớn (~900k nodes), và nhu cầu bảo toàn ngữ cảnh cho AI (RAG).

## Goals / Non-Goals

**Goals:**
- Parser bóc tách chính xác cấu trúc Phần, Chương, Mục, Điều, Khoản, Điểm với độ tin cậy cao.
- Nạp dữ liệu vào Neo4j với tốc độ xử lý nhanh bằng kỹ thuật batching.
- Đảm bảo mỗi Article/Clause embedding đều chứa thông tin ngữ cảnh từ Document cha.
- Hỗ trợ vector index 1024 chiều.

**Non-Goals:**
- Không xử lý bóc tách nội dung bên trong các bảng biểu (Tables) phức tạp (chỉ lấy text thuần).
- Không xử lý các văn bản có định dạng quá cũ hoặc bị lỗi scan nặng (xử lý thủ công sau).
- Không thực hiện trích dẫn tham chiếu (XRef) trong phase này (đây là Phase 2).

## Decisions

### 1. State Machine Parser (BeautifulSoup based)
- **Quyết định**: Duyệt tuần tự các thẻ HTML (`<p>`, `<li>`, `<div>`) và sử dụng Regex để phát hiện các dấu mốc phân cấp.
- **Lý do**: HTML pháp luật Việt Nam không có cấu trúc lồng nhau chuẩn (thường là một danh sách phẳng các thẻ `<p>`). State machine cho phép theo dõi "trạng thái hiện tại" (đang ở Chương nào, Điều nào) để gán quan hệ cha-con chính xác.
- **Hierarchy Reset Rules**: Khi gặp cấp cao hơn, phải reset tất cả các biến trạng thái của cấp thấp hơn để tránh nhầm lẫn ngữ cảnh.

### 2. "Mục" (Section) as Metadata
- **Quyết định**: Không tạo node `Chapter` riêng cho `Mục`. Thay vào đó, thông tin `Mục` được lưu thành thuộc tính `section` trên các node `Article`.
- **Lý do**: Giảm độ phức tạp của Graph schema mà vẫn bảo toàn được thông tin phân cấp cho việc hiển thị và tìm kiếm.

### 3. Option 1 Data Join (Metadata dict in RAM)
- **Quyết định**: Load toàn bộ file Metadata vào một Python dictionary `{doc_id: metadata}` trước khi parse file Content.
- **Lý do**: Truy xuất thông tin văn bản (Tên, Số hiệu) theo `doc_id` với độ phức tạp O(1), tối ưu hóa tốc độ khi parse hàng triệu dòng HTML.

### 4. Rich Chunking & 1024-dim Embeddings
- **Quyết định**: Trước khi gửi sang Embedding Service, text của mỗi segment sẽ được ghép thêm prefix: `[Tên văn bản] - [Chương] - [Tiêu đề Điều]`. Sử dụng model 1024 chiều.
- **Lý do**: Tránh hiện tượng AI "mất gốc" ngữ cảnh khi truy xuất các đoạn văn lẻ. 1024 chiều cung cấp độ phân giải ngữ nghĩa tốt hơn cho các thuật ngữ pháp lý chuyên biệt.

### 5. Neo4j Batch Ingest (UNWIND)
- **Quyết định**: Sử dụng câu lệnh Cypher `UNWIND` với batch size 5,000.
- **Lý do**: Giảm thiểu round-trip giữa ứng dụng và database, tối ưu hóa transaction log của Neo4j, tăng tốc độ nạp dữ liệu lên gấp nhiều lần.

## Risks / Trade-offs

- **[Risk]**: Parser không bắt được các biến thể Regex của Điều/Khoản (ví dụ: "Điều 5 bis", "Khoản 2a").
  - **Mitigation**: Xây dựng bộ Regex catalogue phong phú và sử dụng Confidence Scoring để đánh dấu các văn bản cần review thủ công.
- **[Risk]**: RAM không đủ để chứa toàn bộ Metadata dict.
  - **Mitigation**: Chỉ load các trường cần thiết (`doc_id`, `so_ky_hieu`, `title`). Nếu vẫn thiếu, chuyển sang dùng SQLite tạm thời cho lookup.
- **[Trade-off]**: Việc ghép Metadata vào chunk text làm tăng kích thước token gửi sang Embedding API.
  - **Result**: Tăng chi phí/thời gian tính toán nhưng đổi lại chất lượng Retrieval vượt trội.
