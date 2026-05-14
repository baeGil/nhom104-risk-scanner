## ADDED Requirements

### Requirement: 100-Law Sample Extraction
Hệ thống SHALL cung cấp cơ chế trích xuất chính xác 100 văn bản loại "Luật" từ các file Parquet gốc (metadata và content) để phục vụ kiểm thử.

#### Scenario: Trích xuất thành công
- **WHEN** chạy script chuẩn bị dữ liệu mẫu (sandbox prepare)
- **THEN** hệ thống SHALL tạo ra một tập dữ liệu gồm 100 văn bản Luật có đầy đủ `doc_id`, `so_ky_hieu`, `normalized_id` và `clean_html`.

### Requirement: Article-level Stub Generation
Hệ thống SHALL có khả năng tạo các "Nút giả lập" (Stub Nodes) cho các Điều (Article) và Văn bản (Document) được dẫn chiếu tới nhưng không tồn tại trong tập dữ liệu 100 mẫu.

#### Scenario: Dẫn chiếu ngoại tới văn bản thiếu
- **WHEN** tìm thấy dẫn chiếu tới "Điều 5 Luật Đất đai" nhưng "Luật Đất đai" không có trong tập 100 mẫu
- **THEN** hệ thống SHALL tạo một node `Document` stub cho "Luật Đất đai" và một node `Article` stub cho "Điều 5", sau đó kết nối chúng với nhau và với node nguồn.

### Requirement: Database Sanitization
Hệ thống SHALL làm sạch toàn bộ các node và quan hệ trong database Neo4j mục tiêu trước khi nạp dữ liệu sandbox.

#### Scenario: Làm mới database
- **WHEN** script sandbox bắt đầu thực thi
- **THEN** database Neo4j SHALL ở trạng thái trống (0 nodes, 0 relationships) trước khi quá trình nạp bắt đầu.

### Requirement: Stub Reporting
Hệ thống SHALL báo cáo tổng số lượng node giả lập đã được tạo ra sau khi kết thúc quá trình nạp.

#### Scenario: Hiển thị báo cáo kết quả
- **WHEN** quá trình nạp dữ liệu và trích xuất quan hệ kết thúc
- **THEN** một thông báo log SHALL hiển thị rõ số lượng Document stubs và Article stubs đã được khởi tạo.

