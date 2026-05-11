Ran command: `git stash pop`
Ran command: `clear`
Ran command: `cd ..`
Ran command: `git pull`
Ran command: `clear`
Viewed team-assignment.md:31-46

Để biết các bạn của bạn (Người A và Người C) đã làm xong đến đâu và hệ thống đang "khớp" với nhau như thế nào, chúng ta cần kiểm tra các **điểm giao thoa (interfaces)** giữa các giai đoạn.

Dựa trên tài liệu `team-assignment.md` và các việc bạn vừa làm, đây là cách chúng ta kiểm chứng:

### 1. Kiểm tra phần việc của "Người A" (Data Cleanup & Schema)
Người A cung cấp "nguyên liệu" đầu vào cho Parser của bạn. Bạn hãy kiểm tra xem các file sau đã tồn tại và có dữ liệu chuẩn chưa:

*   **Dữ liệu HTML sạch:** Kiểm tra xem file `data/content.parquet` đã có cột `clean_html` chưa. Đây là kết quả của Task **T0.4**. Nếu cột này chỉ toàn thẻ `<table>` rác thì chứng tỏ pipeline của Người A chưa xong.
*   **Neo4j Schema:** Người A phụ trách **T1.4**. Bạn hãy mở Neo4j Browser và chạy lệnh:
    ```cypher
    SHOW CONSTRAINTS;
    SHOW INDEXES;
    ```
    Nếu thấy có các constraint trên `Document(id)`, `Article(uid)` và index `article_embeddings` (1024-dim) thì phần nền móng của Người A đã sẵn sàng.
*   **Quan hệ cấp văn bản (T1.7):** Thử kiểm tra xem các văn bản đã có quan hệ với nhau chưa:
    ```cypher
    MATCH ()-[r:AMENDS|CITES]->() RETURN count(r) LIMIT 10;
    ```

### 2. Cách kiểm tra "Code đang phối hợp tốt" (Integration Testing)
Để biết Parser của bạn và Dữ liệu của Người A có "ăn rơ" không, bạn hãy chạy script test mà chúng ta vừa viết:
```bash
python -m segmentation.test_parser_data
```

**Dấu hiệu phối hợp tốt:**
1.  **Parser không lỗi:** Đọc được `clean_html` từ Người A mà không bị crash.
2.  **Writer thành công:** Node `Document` (do Người A tạo) được tìm thấy, và các `Article` (do bạn tạo) được gắn đúng vào `Document` đó qua quan hệ `HAS_ARTICLE`.
3.  **Embedder thông suốt:** Gọi được đến `EMBED_SERVICE_URL` (do Người A hoặc hạ tầng cung cấp) và nhận về đúng vector 1024 chiều.

### 3. Trạng thái hiện tại của Team (Ước tính)
Dựa trên `tasks.md` và code hiện tại:

| Giai đoạn | Trạng thái | Người phụ trách | Ghi chú |
| :--- | :--- | :--- | :--- |
| **Phase 0 (Cleanup)** | 🟢 Hoàn thành | Người A | Đã có dữ liệu sạch để bạn Parse. |
| **Phase 1 (Segmentation)** | 🟢 Hoàn thành | **Bạn (Người B)** | Đã bóc tách xong Điều/Khoản và nạp vào Neo4j. |
| **Phase 2 (Cross-Ref)** | 🟡 Đang làm | Người C | Sẽ dùng `uid` bạn tạo ra để nối các tham chiếu cụ thể. |

**Lời khuyên:** Bạn nên thử `MATCH (a:Article) RETURN a LIMIT 5` trong Neo4j. Nếu thấy thuộc tính `section` (Mục) và `embedding` đã đầy đủ, nghĩa là code của bạn đã phối hợp cực tốt với Schema và Embedding Service!

Bạn có muốn tôi viết một script nhỏ để **tự động kiểm tra sức khỏe (Health Check)** toàn bộ các điểm nối này không?