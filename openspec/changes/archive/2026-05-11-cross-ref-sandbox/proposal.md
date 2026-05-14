## Why

Việc triển khai toàn bộ pipeline nạp dữ liệu (của Người A) rất tốn thời gian và hiện tại chưa hoàn thiện đầy đủ, gây khó khăn cho việc kiểm thử độc lập các tính năng trích xuất quan hệ (của Người B). Chúng ta cần một môi trường "Sandbox" với tập dữ liệu mẫu (100 văn bản Luật) để có thể tinh chỉnh logic trích xuất, xử lý dẫn chiếu nội bộ/ngoại bộ và kiểm chứng đồ thị Neo4j một cách nhanh chóng và cô lập.

## What Changes

- **Hệ thống nạp dữ liệu mẫu**: Hệ thống SHALL cung cấp script để trích xuất 100 văn bản loại "Luật" từ các file Parquet gốc.
- **Cơ chế Stub Node (Nút giả lập)**: Logic ghi Neo4j SHALL tự động tạo các node `Document` và `Article` giả lập (stubs) cho các văn bản nằm ngoài tập mẫu nhưng có dẫn chiếu tới.
- **Tối ưu hóa tra cứu**: Hệ thống SHALL triển khai bộ nhớ đệm (In-memory Lookup) từ file JSON để ánh xạ nhanh số ký hiệu văn bản sang ID.
- **Hệ thống báo cáo**: Hệ thống SHALL ghi log hiển thị số lượng dẫn chiếu nội bộ, ngoại bộ và số lượng Stub Node đã được tạo ra sau mỗi lượt chạy.
- **Xóa sạch dữ liệu test**: Hệ thống SHALL cung cấp tính năng tự động làm sạch (Clear) database Neo4j trước khi nạp tập mẫu.


## Capabilities

### New Capabilities
- `cross-ref-sandbox`: Khả năng tạo môi trường kiểm thử cô lập với tập dữ liệu mẫu và cơ chế giả lập node để kiểm chứng quan hệ pháp lý.

### Modified Capabilities
- `cross-reference-extraction`: Bổ sung yêu cầu về việc xử lý dẫn chiếu đến các văn bản chưa tồn tại trong hệ thống (Stubbing).

## Impact

- **Cấu trúc dữ liệu**: Ảnh hưởng đến cách thức tạo node trong Neo4j (thêm thuộc tính `is_stub`).
- **Phát triển**: Giúp Người B có thể làm việc độc lập với Người A.
- **Hạ tầng**: Yêu cầu kết nối Neo4j và file `so_ky_hieu_lookup.json` phải sẵn sàng.
