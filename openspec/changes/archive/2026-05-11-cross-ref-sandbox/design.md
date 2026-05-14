## Context

Hiện tại, hệ thống có hơn 150.000 văn bản pháp luật lưu trong Parquet. Việc nạp toàn bộ vào Neo4j để test quan hệ chéo (Cross-Reference) là quá nặng và không cần thiết trong giai đoạn phát triển logic. Người B cần một công cụ cho phép chọn nhanh 100 luật tiêu biểu để chạy thử nghiệm bóc tách và nối đồ thị.

## Goals / Non-Goals

**Goals:**
- Tạo script nạp 100 văn bản Luật một cách cô lập.
- Thiết lập cơ chế "Stubbing" (Giả lập node) để đồ thị không bị đứt đoạn khi dẫn chiếu tới các văn bản ngoài phạm vi 100 mẫu.
- Tối ưu hóa tốc độ tra cứu ID văn bản bằng bộ nhớ đệm (RAM).

**Non-Goals:**
- Không thực hiện nạp dữ liệu thật cho 150k văn bản (đây là việc của Người A).
- Không thực hiện vector hóa (Embedding) trong phạm vi sandbox này.

## Decisions

### 1. Sử dụng Dictionary Cache cho Lookup Table
**Quyết định**: Load file `so_ky_hieu_lookup.json` vào một Python `dict` khi bắt đầu script.
**Lý do**: Tra cứu trong dict là O(1), nhanh hơn hàng nghìn lần so với việc quét Parquet hoặc chạy Regex chuẩn hóa cho mỗi lần gặp dẫn chiếu.
**Giải pháp thay thế**: Chạy Regex on-the-fly (Chậm, tốn CPU).

### 2. Stub Node ở cấp độ Article (Điều)
**Quyết định**: Khi gặp dẫn chiếu đến "Điều 5 Luật X", nếu Luật X chưa có trong DB, script sẽ tạo cả node `Document(Luật X)` và node `Article(Điều 5)`.
**Lý do**: Phần lớn các dẫn chiếu pháp lý đều trỏ đích danh đến cấp Điều. Việc chỉ tạo node Document sẽ làm mất đi tính chi tiết của đồ thị.
**Ràng buộc**: UID của stub node phải tuân thủ quy ước `doc_{id}_dieu_{n}` để có thể gộp (MERGE) với dữ liệu thật sau này.

### 3. Thuộc tính `is_stub` và cơ chế MERGE
**Quyết định**: Sử dụng câu lệnh `MERGE` trong Cypher kèm theo `ON CREATE SET n.is_stub = true`.
**Lý do**: Đảm bảo nếu node đã tồn tại (dữ liệu thật) thì không đánh dấu là stub. Nếu tạo mới thì đánh dấu là stub để dễ dàng lọc và quản lý.

## Risks / Trade-offs

- **[Risk] Sai lệch UID cho Stub Article** → **Mitigation**: Luôn tra cứu `doc_id` từ mã chuẩn hóa trước khi sinh UID cho Article. Nếu không tìm thấy `doc_id` trong lookup table, sẽ tạo UID dựa trên mã chuẩn hóa tạm thời.
- **[Risk] Database bị phình to do Stub Nodes** → **Mitigation**: Chạy lệnh xóa sạch (`DETACH DELETE`) trước mỗi lần chạy sandbox để làm mới môi trường.
