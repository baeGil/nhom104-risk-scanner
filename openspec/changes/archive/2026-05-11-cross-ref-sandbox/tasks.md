## 1. Chuẩn bị dữ liệu Sandbox

- [x] 1.1 Tạo script `scratch/prepare_sandbox_data.py` để lọc 100 văn bản loại "Luật".
- [x] 1.2 Thực hiện Join giữa `metadata_deduped.parquet` và `content_clean.parquet` để lấy HTML sạch.
- [x] 1.3 Lưu tập dữ liệu mẫu ra file `data/sandbox_sample_100.parquet`.


## 2. Hạ tầng và Tra cứu nhanh

- [x] 2.1 Xây dựng tiện ích `Neo4jSanitizer` để thực hiện lệnh xóa sạch database (`DETACH DELETE`).
- [x] 2.2 Xây dựng lớp `ReferenceCache` để nạp `so_ky_hieu_lookup.json` vào Dictionary trong RAM.
- [x] 2.3 Viết hàm tra cứu ID nhanh kết hợp chuẩn hóa nhẹ (strip whitespace).


## 3. Nâng cấp logic ghi Neo4j (Stubbing)

- [x] 3.1 Cập nhật `CrossReferenceWriter` để sử dụng câu lệnh `MERGE` với thuộc tính `is_stub`.
- [x] 3.2 Triển khai phương thức `ensure_article_stub` để tạo các node Điều giả lập khi thiếu dữ liệu nguồn.
- [x] 3.3 Đảm bảo các Stub Article được nối đúng quan hệ `[:MEMBER_OF]` với Stub Document tương ứng.


## 4. Thực thi và Báo cáo

- [x] 4.1 Tạo script chạy sandbox tích hợp (executor) sử dụng tập dữ liệu 100 mẫu.
- [x] 4.2 Tích hợp bộ đếm (Counter) cho các loại node stub được tạo ra trong quá trình nạp.
- [x] 4.3 Thêm bước in báo cáo tổng kết (Metrics) sau khi kết thúc pipeline.


## 5. Kiểm chứng (Verification)

- [x] 5.1 Chạy thử nghiệm toàn bộ sandbox và kiểm tra đồ thị trên giao diện Neo4j Browser.
- [x] 5.2 Xác nhận các node giả lập có thuộc tính `is_stub: true` và được nối quan hệ chính xác.
- [x] 5.3 Kiểm tra tính chính xác của báo cáo số lượng stub trong log.

