## ADDED Requirements

### Requirement: Batch Ingest with UNWIND
Hệ thống SHALL sử dụng kỹ thuật batching với câu lệnh Cypher UNWIND để nạp dữ liệu vào Neo4j.

#### Scenario: Nạp Article theo lô
- **WHEN** Có 10,000 Article được tạo ra từ quá trình parse
- **THEN** Hệ thống SHALL chia nhỏ thành các lô 5,000 bản ghi và gửi 2 yêu cầu UNWIND tới Neo4j.

### Requirement: Article Embedding Generation
Hệ thống SHALL tạo vector embedding cho mỗi Node Article và lưu trữ vào thuộc tính embedding trong Neo4j.

#### Scenario: Tạo embedding 1024 chiều
- **WHEN** Một Article được nạp vào hệ thống
- **THEN** Hệ thống SHALL gọi dịch vụ embedding và nhận về một mảng 1024 số thực, sau đó cập nhật vào Article node.
