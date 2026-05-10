## Why

Văn bản pháp luật Việt Nam có cấu trúc phân cấp phức tạp (Chương, Điều, Khoản, Điểm) và thường xuyên bị sửa đổi bổ sung. Để xây dựng một hệ thống Legal AI chính xác, chúng ta cần phân rã văn bản thô thành các đơn vị thông tin nhỏ nhất có ngữ cảnh đầy đủ (Rich Chunking) và lưu trữ vào Graph Database (Neo4j). Điều này cho phép thực hiện Hybrid Search (Vector + Keyword) và là tiền đề để xử lý chuỗi sửa đổi (Phase 3) một cách chính xác.

## What Changes

- Triển khai bộ máy Parser (State Machine) dựa trên BeautifulSoup để phân tách cấu trúc pháp luật từ HTML sạch.
- Xây dựng cơ chế "Rich Chunking" để làm giàu ngữ cảnh (ghép metadata của văn bản vào từng Điều/Khoản) trước khi tạo Embedding.
- Tích hợp dịch vụ Embedding 1024 chiều (thay vì 768) để tối ưu hóa tìm kiếm ngữ nghĩa.
- Triển khai cơ chế Batch Ingest (UNWIND) để nạp dữ liệu hiệu suất cao vào Neo4j Article/Clause/Point nodes.
- Thiết hệ thống đánh giá độ tin cậy (Confidence Scoring) để kiểm soát chất lượng dữ liệu nạp.

## Capabilities

### New Capabilities
- `legal-segmentation-engine`: Bộ máy bóc tách cấu trúc pháp luật Việt Nam (Phần, Chương, Mục, Điều, Khoản, Điểm) từ dữ liệu HTML.
- `legal-graph-ingestor`: Hệ thống nạp dữ liệu phân cấp và vector embedding vào Neo4j với hiệu suất cao.

### Modified Capabilities
- `segmentation`: Cập nhật yêu cầu về kích thước vector embedding (1024) và logic xử lý "Mục" (không tạo node riêng, chuyển thành metadata).

## Impact

- **Database**: Tạo và cập nhật hàng trăm nghìn node (Article, Clause, Point) và quan hệ phân cấp trong Neo4j.
- **Search**: Thay đổi kiến trúc vector index từ 768 lên 1024 chiều.
- **Data Flow**: Kết nối file Metadata và file Content thông qua `doc_id` trong quá trình parse.
- **Dependencies**: Phụ thuộc vào Neo4j 5.x và Embedding Service 1024-dim.
