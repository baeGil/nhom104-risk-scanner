import pandas as pd
import os
import logging
from neo4j import GraphDatabase
from src.config import NEO4J_PASSWORD, NEO4J_URI, NEO4J_USER

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s — %(message)s")
logger = logging.getLogger(__name__)

def ingest_documents(file_path: str):
    logger.info(f"Đang đọc dữ liệu metadata từ {file_path}...")
    df = pd.read_parquet(file_path)
    logger.info(f"Tìm thấy {len(df)} văn bản.")

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    query = """
    UNWIND $batch AS row
    MERGE (d:Document {id: row.doc_id})
    SET d.title = row.title,
        d.so_ky_hieu = row.so_ky_hieu,
        d.loai_van_ban = row.loai_van_ban,
        d.ngay_ban_hanh = row.ngay_ban_hanh,
        d.is_stub = false
    """

    batch_size = 5000
    total = 0
    
    with driver.session() as session:
        # Chuẩn bị dữ liệu (ép kiểu string để tránh lỗi Neo4j)
        records = []
        for _, row in df.iterrows():
            records.append({
                "doc_id": str(row.get("doc_id", "")),
                "title": str(row.get("title", "Unknown")),
                "so_ky_hieu": str(row.get("so_ky_hieu", "")),
                "loai_van_ban": str(row.get("loai_van_ban", "")),
                "ngay_ban_hanh": str(row.get("ngay_ban_hanh", ""))
            })

        # Chạy theo batch
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            session.run(query, batch=batch)
            total += len(batch)
            logger.info(f"Đã nạp {total}/{len(records)} văn bản...")

    driver.close()
    logger.info("HOÀN THÀNH: Đã tạo xong tất cả Node Document!")

if __name__ == "__main__":
    path = "data/metadata_deduped.parquet"
    if os.path.exists(path):
        ingest_documents(path)
    else:
        logger.error(f"Không tìm thấy file: {path}")
