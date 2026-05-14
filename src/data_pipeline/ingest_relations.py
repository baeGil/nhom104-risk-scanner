import pandas as pd
import os
import logging
from neo4j import GraphDatabase

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s — %(message)s")
logger = logging.getLogger(__name__)

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASSWORD", "password")

def ingest_internal_refs(tx, batch):
    q = """
    UNWIND $batch AS row
    MATCH (a:Article {uid: row.source_uid})
    MATCH (b:Article {uid: row.target_uid})
    MERGE (a)-[rel:REFERENCES_INTERNAL]->(b)
    SET rel.context = row.context
    """
    tx.run(q, batch=batch)

def ingest_external_refs(tx, batch):
    q = """
    UNWIND $batch AS row
    MATCH (a:Article {uid: row.source_uid})
    MERGE (d:Document {id: row.target_doc_id})
    ON CREATE SET d.is_stub = true, d.so_ky_hieu = row.raw_skh
    MERGE (a)-[rel:REFERENCES_EXTERNAL]->(d)
    SET rel.context = row.context, rel.target_so_ky_hieu = row.raw_skh
    """
    tx.run(q, batch=batch)

def ingest_modifies_refs(tx, batch):
    q = """
    UNWIND $batch AS row
    MATCH (a:Article {uid: row.source_uid})
    MERGE (b:Article {uid: row.target_uid})
    ON CREATE SET b.is_stub = true
    MERGE (a)-[rel:MODIFIES]->(b)
    SET rel.action = row.action, 
        rel.target_clause = row.target_clause, 
        rel.target_point = row.target_point, 
        rel.context = row.context
    """
    tx.run(q, batch=batch)

def run_ingest_relations():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
    
    import glob
    
    with driver.session() as session:
        # Internal
        internal_files = glob.glob("data/relationships/internal_refs_part_*.parquet")
        if internal_files:
            logger.info(f"Đang nạp INTERNAL refs từ {len(internal_files)} file...")
            for f in internal_files:
                df_int = pd.read_parquet(f)
                # Sửa lỗi thiếu doc_
                if 'target_uid' in df_int.columns:
                    df_int['target_uid'] = df_int['target_uid'].apply(lambda x: f"doc_{x}" if str(x) != 'None' and not str(x).startswith('doc_') else x)
                # Loại bỏ quan hệ tự tham chiếu (Điều 1 trỏ vào Điều 1)
                df_int = df_int[df_int['source_uid'] != df_int['target_uid']]
                
                batch = df_int.to_dict('records')
                chunk_size = 5000
                for i in range(0, len(batch), chunk_size):
                    session.execute_write(ingest_internal_refs, batch[i:i+chunk_size])
            logger.info("Đã nạp xong INTERNAL refs.")
            
        # External
        external_files = glob.glob("data/relationships/external_refs_part_*.parquet")
        if external_files:
            logger.info(f"Đang nạp EXTERNAL refs từ {len(external_files)} file...")
            for f in external_files:
                df_ext = pd.read_parquet(f)
                batch = df_ext.to_dict('records')
                chunk_size = 5000
                for i in range(0, len(batch), chunk_size):
                    session.execute_write(ingest_external_refs, batch[i:i+chunk_size])
            logger.info("Đã nạp xong EXTERNAL refs.")
            
        # Modifies
        modifies_files = glob.glob("data/relationships/modifies_refs_part_*.parquet")
        if modifies_files:
            logger.info(f"Đang nạp MODIFIES refs từ {len(modifies_files)} file...")
            for f in modifies_files:
                df_mod = pd.read_parquet(f)
                df_mod = df_mod.where(pd.notnull(df_mod), None)
                # Sửa lỗi thiếu doc_
                if 'target_uid' in df_mod.columns:
                    df_mod['target_uid'] = df_mod['target_uid'].apply(lambda x: f"doc_{x}" if x is not None and not str(x).startswith('doc_') else x)
                batch = df_mod.to_dict('records')
                chunk_size = 5000
                for i in range(0, len(batch), chunk_size):
                    session.execute_write(ingest_modifies_refs, batch[i:i+chunk_size])
            logger.info("Đã nạp xong MODIFIES refs.")

    driver.close()
    logger.info("=== HOÀN TẤT NẠP QUAN HỆ ===")

if __name__ == "__main__":
    run_ingest_relations()
