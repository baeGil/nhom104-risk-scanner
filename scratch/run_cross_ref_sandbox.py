import pandas as pd
import re
import os
from neo4j import GraphDatabase
from loguru import logger
from src.infra.neo4j_utils import Neo4jSanitizer
from src.cross_reference.cache import ReferenceCache
from src.cross_reference.extractor import CrossReferenceExtractor
from src.cross_reference.writer import CrossReferenceWriter

# Cấu hình
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASSWORD", "password")

def mini_segment(html_content):
    """Bóc tách thô các Điều từ HTML để phục vụ test."""
    # Tìm các đoạn "Điều X."
    articles = []
    # Regex tìm Điều: "Điều 1.", "Điều 1a."
    pattern = re.compile(r"(Điều\s+(\d+[a-zđ]?)\..*?)(?=Điều\s+\d+[a-zđ]?\.|$)", re.DOTALL | re.IGNORECASE)
    
    for match in pattern.finditer(html_content):
        full_text = match.group(1).strip()
        index = match.group(2)
        articles.append({
            "index": index,
            "content": full_text
        })
    return articles

def run_sandbox():
    logger.info("--- BẮT ĐẦU CHẠY CROSS-REFERENCE SANDBOX ---")
    
    # 1. Làm sạch database
    sanitizer = Neo4jSanitizer(NEO4J_URI, NEO4J_USER, NEO4J_PASS)
    sanitizer.clear_all()
    
    # 2. Chuẩn bị các thành phần
    cache = ReferenceCache()
    extractor = CrossReferenceExtractor(lookup_table=cache.cache)
    
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
    writer = CrossReferenceWriter(driver)
    
    # 3. Đọc dữ liệu mẫu
    data_path = "data/sandbox_sample_100.parquet"
    if not os.path.exists(data_path):
        logger.error(f"Không tìm thấy file dữ liệu mẫu: {data_path}")
        return
        
    df = pd.read_parquet(data_path)
    logger.info(f"Đã load {len(df)} bản ghi từ sandbox sample.")
    
    total_metrics = {
        "docs_processed": 0,
        "articles_created": 0,
        "internal_refs": 0,
        "external_refs": 0,
        "mod_refs": 0,
        "stub_docs": 0,
        "stub_articles": 0
    }

    # 4. Xử lý từng văn bản
    for _, row in df.iterrows():
        doc_id = str(row['doc_id'])
        html = row['clean_html']
        
        # Tạo node Document gốc (không phải stub)
        with driver.session() as session:
            session.run(
                "MERGE (d:Document {id: $id}) SET d.title = $title, d.is_stub = false",
                id=doc_id, title=row.get('title', 'Unknown')
            )
        
        # Phân đoạn thô
        articles = mini_segment(html)
        total_metrics["docs_processed"] += 1
        
        for art in articles:
            art_idx = art['index']
            art_content = art['content']
            art_uid = f"doc_{doc_id}_dieu_{art_idx}"
            
            # Ghi node Article gốc
            with driver.session() as session:
                session.run(
                    """
                    MATCH (d:Document {id: $doc_id})
                    MERGE (a:Article {uid: $uid})
                    SET a.index = $idx, a.content = $content, a.is_stub = false
                    MERGE (d)-[:HAS_ARTICLE]->(a)
                    """,
                    doc_id=doc_id, uid=art_uid, idx=art_idx, content=art_content
                )
            total_metrics["articles_created"] += 1
            
            # Trích xuất quan hệ
            result = extractor.extract_from_article(
                doc_id=doc_id,
                article_uid=art_uid,
                article_text=art_content
            )
            
            # Ghi vào Neo4j
            summary = writer.write(result)
            
            # Cập nhật metrics
            total_metrics["internal_refs"] += summary.get("internal", 0)
            total_metrics["external_refs"] += summary.get("external", 0)
            total_metrics["mod_refs"] += summary.get("modification", 0)
            total_metrics["stub_docs"] += summary.get("stub_doc", 0)
            total_metrics["stub_articles"] += summary.get("stub_art", 0)

    # 5. In báo cáo tổng kết
    logger.info("--- BÁO CÁO TỔNG KẾT SANDBOX ---")
    logger.info(f"Số văn bản đã xử lý: {total_metrics['docs_processed']}")
    logger.info(f"Số Điều (Article) đã tạo: {total_metrics['articles_created']}")
    logger.info(f"Số quan hệ nội luật (INTERNAL): {total_metrics['internal_refs']}")
    logger.info(f"Số quan hệ ngoại luật (EXTERNAL): {total_metrics['external_refs']}")
    logger.info(f"Số quan hệ sửa đổi (MODIFIES): {total_metrics['mod_refs']}")
    logger.info(f"--- THÔNG SỐ STUBBING ---")
    logger.info(f"Số Stub Document được tạo: {total_metrics['stub_docs']}")
    logger.info(f"Số Stub Article được tạo: {total_metrics['stub_articles']}")
    
    writer.close()
    logger.success("Hoàn thành pipeline sandbox!")

if __name__ == "__main__":
    run_sandbox()
