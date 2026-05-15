import json
import pandas as pd
import os
import logging
import re
from neo4j import GraphDatabase
from src.segmentation.parser import LegalDocumentParser
from src.segmentation.writer import SegmentWriter
from src.segmentation.confidence import ConfidenceScorer
from src.cross_reference.extractor import CrossReferenceExtractor
from src.segmentation.models import HierarchyType

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s — %(message)s")
logger = logging.getLogger(__name__)

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASSWORD", "password")

def normalize_so_hieu(so_hieu):
    so_hieu = str(so_hieu).strip().upper()
    match = re.search(r'(\d+/\d+/[A-ZĐ0-9\-]+)', so_hieu)
    if match:
        core_skh = match.group(1)
    else:
        match_fallback = re.search(r'^([^\s\(\)]+)', so_hieu)
        if match_fallback:
            core_skh = match_fallback.group(1)
        else:
            core_skh = so_hieu
    parts = core_skh.split('/')
    stripped_parts = [re.sub(r'^0+', '', p) if re.match(r'^0+\d+', p) else p for p in parts]
    return '/'.join(stripped_parts)

def parse_uid_parts(uid):
    if not uid: return "", "", ""
    p = uid.split('_')
    d = k = di = ""
    if 'dieu' in p: d = p[p.index('dieu')+1]
    if 'khoan' in p: k = p[p.index('khoan')+1]
    if 'diem' in p: di = p[p.index('diem')+1]
    return d, k, di

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
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
    parser = LegalDocumentParser()
    writer = SegmentWriter(driver)
    
    logger.info("Đọc data_updated_with_ids.json...")
    target_docs = set()
    with open("data_updated_with_ids.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        for cat in data:
            for doc in cat.get("van_ban", []):
                doc_id = doc.get("doc_id")
                if doc_id:
                    target_docs.add(str(doc_id))
    
    logger.info(f"Tổng số văn bản mục tiêu cần nạp từ JSON: {len(target_docs)}")
    
    logger.info("Đọc metadata_deduped.parquet...")
    meta_df = pd.read_parquet("data/metadata_deduped.parquet")
    meta_df['id'] = meta_df['id'].astype(str)
    
    # Lọc chỉ những văn bản có trong list mục tiêu
    filtered_meta = meta_df[meta_df['id'].isin(target_docs)].copy()
    filtered_meta['ngay_ban_hanh'] = pd.to_datetime(filtered_meta['ngay_ban_hanh'], errors='coerce')
    logger.info(f"Số lượng văn bản tìm thấy trong Parquet metadata: {len(filtered_meta)}")
    
    # Load lookup table from JSON
    lookup_path = "data/so_ky_hieu_lookup.json"
    if not os.path.exists(lookup_path):
        logger.info("Không thấy bảng tra cứu JSON, đang tạo mới...")
        from src.data_pipeline.build_lookup_json import build
        build()
        
    with open(lookup_path, "r", encoding="utf-8") as f:
        lookup = json.load(f)
    logger.info(f"Đã nạp bảng tra cứu từ JSON ({len(lookup)} mục).")
            
    extractor = CrossReferenceExtractor(lookup_table=lookup)
    
    logger.info("Đọc content_clean.parquet...")
    content_df = pd.read_parquet("data/content_clean.parquet")
    content_df['id'] = content_df['id'].astype(str)
    content_dict = content_df[content_df['id'].isin(target_docs)].set_index('id')['clean_html'].to_dict()
    
    total_docs = 0
    batch_size = 50
    batch_segments = []
    part_idx = 0
    
    # Lists for relationships
    internal_refs_data = []
    external_refs_data = []
    modifies_refs_data = []
    
    
    with driver.session() as session:
        for idx, row in filtered_meta.iterrows():
            doc_id = str(row['id'])
            all_relationships = []
            # Stage 1: Shell Ingestion
            try:
                session.execute_write(ingest_document_shell, row)
            except Exception as e:
                logger.error(f"Lỗi nạp shell {doc_id}: {e}")
                continue
                
            html = content_dict.get(doc_id, "")
            if not html:
                continue
                
            try:
                # Stage 2: Preamble Extraction
                preamble_text = ""
                parts = re.split(r'(<[^>]+>\s*Điều\s+1[\.:\s])', html, maxsplit=1, flags=re.IGNORECASE)
                if len(parts) > 1:
                    preamble_text = parts[0]
                primary_target_ref = extractor._extract_preamble_anchor(preamble_text)
                
                # Stage 3: Segmentation
                result = parser.parse(
                    doc_id=doc_id,
                    clean_html=html,
                    loai_van_ban=row.get('loai_van_ban', '')
                )
                batch_segments.append(result)
                
                # Stage 4: Cross-Reference & Context-Aware Extraction
                # is_modifying = (primary_target_ref is not None) or ("sửa đổi" in str(row.get('title', '')).lower())
                # uid_to_seg = {s.uid: s for s in result.segments if s.uid}
                
                # last_target_doc_id = primary_target_ref.target_doc_id if primary_target_ref else None
                # last_target_article = None
                
                # for seg in result.segments:
                #     if seg.hierarchy_type not in [HierarchyType.DIEU, HierarchyType.KHOAN, HierarchyType.DIEM]:
                #         continue
                    
                #     art_uid = cl_uid = pt_uid = None
                #     curr = seg
                #     if curr.hierarchy_type == HierarchyType.DIEM:
                #         pt_uid = curr.uid
                #         curr = uid_to_seg.get(curr.parent_uid)
                #     if curr and curr.hierarchy_type == HierarchyType.KHOAN:
                #         cl_uid = curr.uid
                #         curr = uid_to_seg.get(curr.parent_uid)
                #     if curr and curr.hierarchy_type == HierarchyType.DIEU:
                #         art_uid = curr.uid
                    
                #     if not art_uid: continue

                #     ext_result = extractor.extract_from_article(
                #         doc_id=doc_id,
                #         article_uid=art_uid,
                #         clause_uid=cl_uid,
                #         point_uid=pt_uid,
                #         article_text=seg.clean_text,
                #         is_modifying_doc=is_modifying
                #     )

                #     src_art, src_cl, src_pt = parse_uid_parts(seg.uid)

                #     # Thu thập Internal Refs
                #     for r in ext_result.internal_refs:
                #         target_uid = f"doc_{doc_id}_dieu_{r.target_article_index}"
                #         if r.target_clause_index: target_uid += f"_khoan_{r.target_clause_index}"
                #         if r.target_point_label: target_uid += f"_diem_{r.target_point_label}"
                #         if seg.uid != target_uid:
                #             internal_refs_data.append({
                #                 "source_uid": seg.uid,
                #                 "target_uid": target_uid,
                #                 "is_exception": getattr(r, 'is_exception', False),
                #                 "context": r.context_text.replace('\n', ' ')
                #             })

                #     # Thu thập External Refs
                #     for r in ext_result.external_refs:
                #         target_uid = f"doc_{r.target_doc_id}_dieu_{r.target_article_index}" if r.target_doc_id and r.target_article_index else ""
                #         if target_uid and r.target_clause_index: target_uid += f"_khoan_{r.target_clause_index}"
                #         if target_uid and r.target_point_label: target_uid += f"_diem_{r.target_point_label}"
                #         external_refs_data.append({
                #             "source_uid": seg.uid,
                #             "target_doc_id": r.target_doc_id or "",
                #             "target_uid": target_uid,
                #             "raw_skh": r.raw_so_ky_hieu,
                #             "is_exception": getattr(r, 'is_exception', False),
                #             "context": r.context_text.replace('\n', ' ')
                #         })
                       

                #     # Thu thập Modification Refs (có Rollback)
                #     for r in ext_result.modification_refs:
                #         if not r.target_doc_id:
                #             if last_target_doc_id:
                #                 r.target_doc_id = last_target_doc_id
                #             elif primary_target_ref and primary_target_ref.target_doc_id:
                #                 r.target_doc_id = primary_target_ref.target_doc_id
                                
                #         if r.target_doc_id and last_target_doc_id != r.target_doc_id:
                #             last_target_doc_id = r.target_doc_id
                #             last_target_article = None

                #         if getattr(r, 'is_partial_ref', False) and not r.target_article_index:
                #             r.target_article_index = last_target_article
                #         elif r.target_article_index:
                #             last_target_article = r.target_article_index
                            
                #         target_uid = f"doc_{r.target_doc_id}_dieu_{r.target_article_index}" if r.target_doc_id and r.target_article_index else ""
                #         if target_uid and r.target_clause_index: target_uid += f"_khoan_{r.target_clause_index}"
                #         if target_uid and r.target_point_label: target_uid += f"_diem_{r.target_point_label}"

                #         action_str = r.action.value if hasattr(r.action, 'value') else str(r.action)
                #         modifies_refs_data.append({
                #             "source_uid": seg.uid,
                #             "target_uid": target_uid,
                #             "target_doc_id": r.target_doc_id or "",
                #             "action": action_str,
                #             "raw_skh": r.raw_target_so_ky_hieu,
                #             "context": r.context_text.replace('\n', ' ')
                #         })

            except Exception as e:
                logger.error(f"Lỗi xử lý nội dung văn bản {doc_id}: {e}")    
            total_docs += 1
            if len(batch_segments) >= batch_size:
                writer.write_batch(batch_segments)
                batch_segments = []
                logger.info(f"Đã xử lý và nạp {total_docs} văn bản cốt lõi...")
                
            # if total_docs % 100 == 0:
            #     os.makedirs("data/relationships", exist_ok=True)
            #     pd.DataFrame(internal_refs_data).to_parquet(f"data/relationships/internal_refs_part_{part_idx}.parquet")
            #     pd.DataFrame(external_refs_data).to_parquet(f"data/relationships/external_refs_part_{part_idx}.parquet")
            #     pd.DataFrame(modifies_refs_data).to_parquet(f"data/relationships/modifies_refs_part_{part_idx}.parquet")
            #     logger.info(f"Đã checkpoint quan hệ part {part_idx} và giải phóng RAM.")
            #     part_idx += 1
            #     internal_refs_data.clear()
            #     external_refs_data.clear()
            #     modifies_refs_data.clear()
                
        if batch_segments:
            writer.write_batch(batch_segments)
            logger.info(f"Hoàn thành toàn bộ {total_docs} văn bản.")
            
    # os.makedirs("data/relationships", exist_ok=True)
    # pd.DataFrame(internal_refs_data).to_parquet(f"data/relationships/internal_refs_part_{part_idx}.parquet")
    # pd.DataFrame(external_refs_data).to_parquet(f"data/relationships/external_refs_part_{part_idx}.parquet")
    # pd.DataFrame(modifies_refs_data).to_parquet(f"data/relationships/modifies_refs_part_{part_idx}.parquet")
    # logger.info("Đã lưu toàn bộ các quan hệ cuối cùng vào thư mục data/relationships/")

    driver.close()
    logger.info("=== HOÀN TẤT UNIFIED PIPELINE ===")

if __name__ == "__main__":
    run_unified_pipeline()
