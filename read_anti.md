Ran command: `g-ThinkBook-14-G6-AHP:~/Desktop/python/VinUni/nhom104-risk-scanner$ clear`

Có chứ! Thực ra **chúng ta ĐÃ VÀ ĐANG dùng `UNWIND` để nạp Điều, Khoản, Điểm rồi!** 

Nếu bạn mở file `src/segmentation/writer.py` (từ dòng 147), bạn sẽ thấy hàm `_merge_article` của tôi viết như thế này:
```cypher
    @staticmethod
    def _merge_article(tx, batch_data: list[dict]) -> None:
        query = """
        UNWIND $batch AS row
        MATCH (d:Document {id: row.doc_id})
        MERGE (a:Article {uid: row.uid})
        SET a.index        = row.index,
            ...
```
Tương tự cho Chapter, Clause, Point, tôi đều thiết kế dùng `UNWIND` và gom nhóm `batch_size = 5000` (5 nghìn node nạp cùng lúc) để đảm bảo tốc độ cực cao.

Câu nói lúc nãy của tôi: *"dùng UNWIND nạp thẳng thay vì nạp lẻ tẻ"* là tôi đang so sánh với file `full_ingest_neo4j.py` cũ. Trong file cũ đó (khi chưa tách ra), cứ mỗi vòng lặp `for r in ext_result.modification_refs:`, lệnh `session.execute_write` lại gọi tới cơ sở dữ liệu **1 lần cho 1 quan hệ** (bị nạp lẻ tẻ). Do đó tách ra dùng `UNWIND` sẽ giúp giai đoạn 2 nhanh bằng với tốc độ của giai đoạn 1.

Bạn cứ để script Giai đoạn 1 chạy tiếp nhé (như tôi thấy trên hệ thống là nó đang chạy được hơn 1 phút rồi, chuẩn bị ra file Parquet đấy)! Chạy xong bạn gõ lệnh ở Giai đoạn 2 là hoàn hảo.