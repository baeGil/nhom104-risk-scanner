import os
import glob
import logging
import pandas as pd
from neo4j import GraphDatabase
from src.config import NEO4J_PASSWORD, NEO4J_URI, NEO4J_USER

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s — %(message)s")
logger = logging.getLogger(__name__)

def run_ingest_relationships():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    internal_files = glob.glob("data/relationships/internal_refs_part_*.parquet")
    external_files = glob.glob("data/relationships/external_refs_part_*.parquet")
    modifies_files = glob.glob("data/relationships/modifies_refs_part_*.parquet")
    
    with driver.session() as session:
        # 1. Ingest Internal Refs
        logger.info(f"Đang nạp Internal Refs từ {len(internal_files)} files...")
        for fpath in internal_files:
            df = pd.read_parquet(fpath)
            if df.empty: continue
            
            # Chỉ nạp nếu target_uid khác rỗng
            df_valid = df[df['target_uid'] != ""]
            if df_valid.empty: continue
            
            records = df_valid.to_dict('records')
            query = """
            UNWIND $records AS row
            MATCH (a:Segment {uid: row.source_uid})
            MATCH (b:Segment {uid: row.target_uid})
            MERGE (a)-[r:REFERENCES {type: 'INTERNAL'}]->(b)
            SET r.is_exception = coalesce(row.is_exception, false),
                r.context = row.context
            """
            session.run(query, records=records)
            logger.info(f" - Đã nạp {len(records)} internal refs từ {fpath}")

        # 2. Ingest External Refs
        logger.info(f"Đang nạp External Refs từ {len(external_files)} files...")
        for fpath in external_files:
            df = pd.read_parquet(fpath)
            if df.empty: continue
            
            records = df.to_dict('records')
            
            query = """
            UNWIND $records AS row
            MATCH (a:Segment {uid: row.source_uid})
            
            // Tìm Target: Nếu có target_uid cụ thể (đến Khoản/Điểm/Điều)
            OPTIONAL MATCH (b_seg:Segment {uid: row.target_uid})
            
            // Tìm Target: Nếu không có segment cụ thể, nhưng có target_doc_id
            OPTIONAL MATCH (b_doc:Document {id: row.target_doc_id})
            
            // Xử lý tạo Stub Document nếu không tìm thấy cả hai (Văn bản chưa từng nạp)
            WITH a, row, b_seg, b_doc,
                 coalesce(b_seg, b_doc) as existing_target
                 
            CALL {
                WITH row, existing_target
                WITH row, existing_target WHERE existing_target IS NULL AND row.raw_skh <> ''
                MERGE (stub:Document {so_ky_hieu: row.raw_skh})
                ON CREATE SET stub.is_stub = true, stub.title = 'Văn bản được trích dẫn (Chưa nạp)'
                RETURN stub
            }
            
            WITH a, row, coalesce(existing_target, stub) as final_target
            WHERE final_target IS NOT NULL
            
            MERGE (a)-[r:REFERENCES {type: 'EXTERNAL'}]->(final_target)
            SET r.is_exception = coalesce(row.is_exception, false),
                r.context = row.context,
                r.raw_so_ky_hieu = row.raw_skh
            """
            session.run(query, records=records)
            logger.info(f" - Đã nạp {len(records)} external refs từ {fpath}")

        # 3. Ingest Modification Refs
        logger.info(f"Đang nạp Modification Refs từ {len(modifies_files)} files...")
        for fpath in modifies_files:
            df = pd.read_parquet(fpath)
            if df.empty: continue
            
            records = df.to_dict('records')
            query = """
            UNWIND $records AS row
            MATCH (a:Segment {uid: row.source_uid})
            
            OPTIONAL MATCH (b_seg:Segment {uid: row.target_uid})
            OPTIONAL MATCH (b_doc:Document {id: row.target_doc_id})
            
            WITH a, row, b_seg, b_doc, coalesce(b_seg, b_doc) as existing_target
            
            CALL {
                WITH row, existing_target
                WITH row, existing_target WHERE existing_target IS NULL AND row.raw_skh <> ''
                MERGE (stub:Document {so_ky_hieu: row.raw_skh})
                ON CREATE SET stub.is_stub = true, stub.title = 'Văn bản được sửa đổi (Chưa nạp)'
                RETURN stub
            }
            
            WITH a, row, coalesce(existing_target, stub) as final_target
            WHERE final_target IS NOT NULL
            
            MERGE (a)-[r:MODIFIES]->(final_target)
            SET r.action = row.action,
                r.context = row.context,
                r.raw_so_ky_hieu = row.raw_skh
            """
            session.run(query, records=records)
            logger.info(f" - Đã nạp {len(records)} modification refs từ {fpath}")

    driver.close()
    logger.info("=== HOÀN TẤT NẠP QUAN HỆ ===")

if __name__ == "__main__":
    run_ingest_relationships()
