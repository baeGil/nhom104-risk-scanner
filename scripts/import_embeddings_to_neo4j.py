import os
import logging
import pandas as pd
from neo4j import GraphDatabase
from src.env_utils import load_project_env

load_project_env()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s — %(message)s")
logger = logging.getLogger(__name__)

def import_embeddings():
    # 1. Cấu hình
    INPUT_FILE = 'data/legal_embeddings_results.parquet' # File tải từ Colab về
    
    if not os.path.exists(INPUT_FILE):
        logger.error(f"Không tìm thấy file {INPUT_FILE}. Hãy đảm bảo bạn đã tải kết quả từ Colab về thư mục scratch/")
        return

    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")

    # 2. Đọc dữ liệu từ Parquet
    logger.info(f"Đang đọc dữ liệu từ {INPUT_FILE}...")
    df = pd.read_parquet(INPUT_FILE)
    data = df.to_dict('records') # Chuyển thành list of dicts [{'uid':..., 'embedding':...}]
    
    # 3. Kết nối Neo4j và cập nhật
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    # Câu lệnh Cypher UNWIND cực nhanh: Cập nhật bất kể node đó là Article, Clause hay Point
    query = """
    UNWIND $batch AS item
    MATCH (n {uid: item.uid})
    SET n.embedding = item.embedding
    """
    
    batch_size = 5000
    total = len(data)
    
    try:
        with driver.session() as session:
            logger.info(f"Bắt đầu nạp {total} embeddings vào Neo4j...")
            for i in range(0, total, batch_size):
                batch = data[i:i+batch_size]
                session.run(query, batch=batch)
                logger.info(f"Đã nạp: {min(i + batch_size, total)}/{total}")
                
        logger.info("=== NẠP DỮ LIỆU THÀNH CÔNG! ===")
        
    except Exception as e:
        logger.error(f"Lỗi khi nạp dữ liệu vào Neo4j: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    import_embeddings()
