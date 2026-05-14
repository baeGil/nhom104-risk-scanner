# Spec: Cross-Reference Sandbox

## Overview

Môi trường kiểm thử cô lập (Sandbox) cho phép thực thi pipeline trích xuất dẫn chiếu trên tập dữ liệu mẫu để kiểm chứng logic mà không cần nạp toàn bộ database.

## Capabilities

### cross-ref-sandbox

Khả năng tạo môi trường kiểm thử cô lập với tập dữ liệu mẫu và cơ chế giả lập node để kiểm chứng quan hệ pháp lý.

#### Requirements

- **100-Law Sample Extraction**: Hệ thống SHALL cung cấp cơ chế trích xuất chính xác 100 văn bản loại "Luật" từ các file Parquet gốc (metadata và content) để phục vụ kiểm thử.
- **Article-level Stub Generation**: Hệ thống SHALL có khả năng tạo các "Nút giả lập" (Stub Nodes) cho các Điều (Article) và Văn bản (Document) được dẫn chiếu tới nhưng không tồn tại trong tập dữ liệu mẫu.
- **Database Sanitization**: Hệ thống SHALL làm sạch toàn bộ các node và quan hệ trong database Neo4j mục tiêu trước khi nạp dữ liệu sandbox.
- **Stub Reporting**: Hệ thống SHALL báo cáo tổng số lượng node giả lập đã được tạo ra sau khi kết thúc quá trình nạp.
