import pandas as pd
import os
import logging
import re
from neo4j import GraphDatabase
from src.segmentation.parser import LegalDocumentParser
from src.segmentation.writer import SegmentWriter
from src.segmentation.confidence import ConfidenceScorer
from src.cross_reference.extractor import CrossReferenceExtractor

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s — %(message)s")
logger = logging.getLogger(__name__)

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASSWORD", "password")

def ingest_document_shell(tx, row):
    query = """
    MERGE (d:Document {id: $id})
    SET d.so_ky_hieu = $so_ky_hieu,
        d.normalized_so_ky_hieu = $normalized_so_ky_hieu,
        d.title = $title,
        d.loai_van_ban = $loai_van_ban,
        d.ngay_ban_hanh = date($ngay_ban_hanh),
        d.is_stub = false
    """
    params = {
        "id": str(row['id']),
        "so_ky_hieu": str(row.get('so_ky_hieu', '')),
        "normalized_so_ky_hieu": str(row.get('normalized_so_ky_hieu', '')),
        "title": str(row.get('title', '')),
        "loai_van_ban": str(row.get('loai_van_ban', '')),
        "ngay_ban_hanh": row['ngay_ban_hanh'].strftime('%Y-%m-%d') if pd.notna(row['ngay_ban_hanh']) else None
    }
    tx.run(query, **params)



def run_unified_pipeline():
    # 1.1 Infrastructure Skeleton
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
    parser = LegalDocumentParser()
    scorer = ConfidenceScorer()
    writer = SegmentWriter(driver)
    
    logger.info("Đọc metadata_deduped.parquet...")
    meta_df = pd.read_parquet("data/metadata_deduped.parquet")
    
    # 1.2 Filter loai_van_ban and ngay_ban_hanh
    core_types = ['Thông tư', 'Nghị định', 'Luật', 'Bộ luật']
    meta_df['ngay_ban_hanh'] = pd.to_datetime(meta_df['ngay_ban_hanh'], errors='coerce')
    filtered_meta = meta_df[
        (meta_df['loai_van_ban'].isin(core_types)) &
        (meta_df['ngay_ban_hanh'] >= '2000-01-01')
    ]
    logger.info(f"Tổng số văn bản sau khi lọc: {len(filtered_meta)}")
    
    # Build lookup table for extractor
    lookup = {}
    for _, row in filtered_meta.iterrows():
        if pd.notna(row.get('normalized_so_ky_hieu')):
            lookup[row['normalized_so_ky_hieu']] = str(row['id'])
            
    extractor = CrossReferenceExtractor(lookup_table=lookup)
    
    logger.info("Đọc content_clean.parquet...")
    content_df = pd.read_parquet("data/content_clean.parquet")
    content_dict = content_df.set_index('id')['clean_html'].to_dict()
    
    total_docs = 0
    batch_size = 50  # 3.1 Batching to prevent memory issues
    batch_segments = []
    part_idx = 0
    
    # Lists for relationships
    internal_refs_data = []
    external_refs_data = []
    modifies_refs_data = []
    
    with driver.session() as session:
        for idx, row in filtered_meta.iterrows():
            doc_id = str(row['id'])
            
            # 1.3 Stage 1: Shell Ingestion
            try:
                session.execute_write(ingest_document_shell, row)
            except Exception as e:
                logger.error(f"Lỗi nạp shell {doc_id}: {e}")
                continue # 3.2 Error handling skip
                
            html = content_dict.get(doc_id, "")
            if not html:
                continue
                
            try:
                # 2.1 Stage 2: Preamble Extraction
                preamble_text = ""
                parts = re.split(r'(<[^>]+>\s*Điều\s+1[\.:\s])', html, maxsplit=1, flags=re.IGNORECASE)
                if len(parts) > 1:
                    preamble_text = parts[0]
                primary_target_ref = extractor._extract_preamble_anchor(preamble_text)

                
                # 2.2 Stage 3: Segmentation
                result = parser.parse(
                    doc_id=doc_id,
                    clean_html=html,
                    loai_van_ban=row.get('loai_van_ban', '')
                )
                # result = scorer.score(result, expected_article_count=None)
                batch_segments.append(result)
                
                # 2.3 & 2.4 Stage 4: Cross-Reference & Context-Aware Extraction
                is_modifying = (primary_target_ref is not None) or ("sửa đổi" in str(row.get('title', '')).lower())
                
                for article in result.articles():
                    ext_result = extractor.extract_from_article(
                        doc_id=doc_id,
                        article_uid=article.uid,
                        article_text=article.text_content,
                        is_modifying_doc=is_modifying
                    )
                    
                    # Inject primary target if implicit
                    for mod_ref in ext_result.modification_refs:
                        if not mod_ref.target_doc_id and primary_target_ref and primary_target_ref.target_doc_id:
                            mod_ref.target_doc_id = primary_target_ref.target_doc_id
                            
                    # Ingest relationships to list
                    for r in ext_result.internal_refs:
                        if r.target_article_index:
                            target_uid = f"doc_{doc_id}_dieu_{r.target_article_index}"
                            if article.uid != target_uid:
                                internal_refs_data.append({
                                    "source_uid": article.uid,
                                    "target_uid": target_uid,
                                    "context": r.context_text
                                })
                            
                    for r in ext_result.external_refs:
                        if r.target_doc_id:
                            external_refs_data.append({
                                "source_uid": article.uid,
                                "target_doc_id": r.target_doc_id,
                                "raw_skh": r.raw_so_ky_hieu,
                                "context": r.context_text
                            })
                            
                    for r in ext_result.modification_refs:
                        if r.target_doc_id and r.target_article_index:
                            action_str = r.action.value if hasattr(r.action, 'value') else str(r.action)
                            modifies_refs_data.append({
                                "source_uid": article.uid,
                                "target_uid": f"doc_{r.target_doc_id}_dieu_{r.target_article_index}",
                                "action": action_str,
                                "target_clause": r.target_clause_index,
                                "target_point": r.target_point_label,
                                "context": r.context_text
                            })

            except Exception as e: # 3.2 Error handling
                logger.error(f"Lỗi xử lý nội dung văn bản {doc_id}: {e}")
                
            total_docs += 1
            if len(batch_segments) >= batch_size:
                writer.write_batch(batch_segments)
                batch_segments = []
                logger.info(f"Đã xử lý và nạp {total_docs} văn bản cốt lõi...")
                
            # Checkpoint quan hệ mỗi 200 văn bản
            if total_docs % 200 == 0:
                os.makedirs("data/relationships", exist_ok=True)
                pd.DataFrame(internal_refs_data).to_parquet(f"data/relationships/internal_refs_part_{part_idx}.parquet")
                pd.DataFrame(external_refs_data).to_parquet(f"data/relationships/external_refs_part_{part_idx}.parquet")
                pd.DataFrame(modifies_refs_data).to_parquet(f"data/relationships/modifies_refs_part_{part_idx}.parquet")
                logger.info(f"Đã checkpoint quan hệ part {part_idx} và giải phóng RAM.")
                part_idx += 1
                internal_refs_data.clear()
                external_refs_data.clear()
                modifies_refs_data.clear()
                
        # Flush remaining
        if batch_segments:
            writer.write_batch(batch_segments)
            logger.info(f"Hoàn thành toàn bộ {total_docs} văn bản.")
            
    # Save remaining relationships
    os.makedirs("data/relationships", exist_ok=True)
    pd.DataFrame(internal_refs_data).to_parquet(f"data/relationships/internal_refs_part_{part_idx}.parquet")
    pd.DataFrame(external_refs_data).to_parquet(f"data/relationships/external_refs_part_{part_idx}.parquet")
    pd.DataFrame(modifies_refs_data).to_parquet(f"data/relationships/modifies_refs_part_{part_idx}.parquet")
    logger.info("Đã lưu toàn bộ các quan hệ cuối cùng vào thư mục data/relationships/")

    driver.close()
    logger.info("=== HOÀN TẤT UNIFIED PIPELINE ===")

if __name__ == "__main__":
    run_unified_pipeline()
