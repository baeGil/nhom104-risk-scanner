import pandas as pd
import os
import logging
import re

from src.segmentation.parser import LegalDocumentParser
from src.segmentation.writer import SegmentWriter
from src.segmentation.confidence import ConfidenceScorer
from src.cross_reference.extractor import CrossReferenceExtractor

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s — %(message)s")
logger = logging.getLogger(__name__)

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASSWORD", "password")

def run_unified_pipeline():
    # 1.1 Infrastructure Skeleton
    scorer = ConfidenceScorer()
    parser = LegalDocumentParser()
    
    logger.info("Đọc metadata_deduped.parquet...")
    meta_df = pd.read_parquet("data/metadata_deduped.parquet")
    meta_df['id'] = meta_df['id'].astype(str)
    
    # 1.2 Filter loai_van_ban and ngay_ban_hanh
    core_types = ['Thông tư', 'Nghị định', 'Luật', 'Bộ luật']
    validity = ['Còn hiệu lực','Hết hiệu lực một phần']
    meta_df['ngay_ban_hanh'] = pd.to_datetime(meta_df['ngay_ban_hanh'], errors='coerce', dayfirst=True)
    filtered_meta = meta_df[
        (meta_df['loai_van_ban'].isin(core_types)) &
        (meta_df['tinh_trang_hieu_luc'].isin(validity)) &
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
    content_df['id'] = content_df['id'].astype(str)
    content_dict = content_df.set_index('id')['clean_html'].to_dict()
    
    total_docs = 0
    batch_size = 50  # 3.1 Batching to prevent memory issues
    batch_segments = []
    part_idx = 0
    
    # Lists for relationships
    internal_refs_data = []
    external_refs_data = []
    modifies_refs_data = []
    
    doc_id = '146983'
    meta_row = filtered_meta[filtered_meta['id'] == doc_id]
    if meta_row.empty:
        logger.error(f"Văn bản ID {doc_id} không tìm thấy trong metadata.")
        return
    row = meta_row.iloc[0]
    
    html = content_dict.get(doc_id, "")
        
    try:
        # 2.1 Stage 2: Preamble Extraction
        logger.info(f"Start stage 2: Preamble Extraction...")
        preamble_text = ""
        parts = re.split(r'(<[^>]+>\s*Điều\s+1[\.:\s])', html, maxsplit=1, flags=re.IGNORECASE)
        if len(parts) > 1:
            preamble_text = parts[0]
        
        primary_target_ref = extractor._extract_preamble_anchor(preamble_text)
        if primary_target_ref:
            logger.info(f"Tìm thấy văn bản đích từ lời nói đầu: {primary_target_ref.raw_so_ky_hieu} (ID: {primary_target_ref.target_doc_id})")
        
        # 2.2 Stage 3: Segmentation
        logger.info(f"Start stage 3: Segmentation...")
        result = parser.parse(
            doc_id=doc_id,
            clean_html=html,
            loai_van_ban=row.get('loai_van_ban', '')
        )
        
        # 2.3 & 2.4 Stage 4: Cross-Reference & Context-Aware Extraction
        logger.info(f"Start stage 4: Cross-Reference & Context-Aware Extraction...")
        is_modifying = (primary_target_ref is not None) or ("sửa đổi" in str(row.get('title', '')).lower())
        
        from src.segmentation.models import HierarchyType
        all_relationships = []

        def parse_uid_parts(uid):
            if not uid: return "", "", ""
            p = uid.split('_')
            d = k = di = ""
            if 'dieu' in p: d = p[p.index('dieu')+1]
            if 'khoan' in p: k = p[p.index('khoan')+1]
            if 'diem' in p: di = p[p.index('diem')+1]
            return d, k, di
        logger.info(f"Executing stage 4: Parse done...")
        uid_to_seg = {s.uid: s for s in result.segments if s.uid}
        last_target_doc_id = None
        last_target_article = None

        for seg in result.segments:
            if seg.hierarchy_type not in [HierarchyType.DIEU, HierarchyType.KHOAN, HierarchyType.DIEM]:
                continue
            
            # Xác định article_uid, clause_uid, point_uid cho source
            art_uid = cl_uid = pt_uid = None
            curr = seg
            if curr.hierarchy_type == HierarchyType.DIEM:
                pt_uid = curr.uid
                curr = uid_to_seg.get(curr.parent_uid)
            if curr and curr.hierarchy_type == HierarchyType.KHOAN:
                cl_uid = curr.uid
                curr = uid_to_seg.get(curr.parent_uid)
            if curr and curr.hierarchy_type == HierarchyType.DIEU:
                art_uid = curr.uid
            
            if not art_uid: continue

            ext_result = extractor.extract_from_article(
                doc_id=doc_id,
                article_uid=art_uid,
                clause_uid=cl_uid,
                point_uid=pt_uid,
                article_text=seg.clean_text,
                is_modifying_doc=is_modifying
            )

            src_art, src_cl, src_pt = parse_uid_parts(seg.uid)

            # Thu thập Internal Refs
            for r in ext_result.internal_refs:
                all_relationships.append({
                    "src_doc": doc_id, "src_art": src_art, "src_cl": src_cl, "src_pt": src_pt,
                    "tgt_doc": doc_id, "tgt_art": r.target_article_index or "", 
                    "tgt_cl": r.target_clause_index or "", "tgt_pt": r.target_point_label or "",
                    "type": "Internal", "context": r.context_text.replace('\n', ' ')
                })

            # Thu thập External Refs
            for r in ext_result.external_refs:
                all_relationships.append({
                    "src_doc": doc_id, "src_art": src_art, "src_cl": src_cl, "src_pt": src_pt,
                    "tgt_doc": r.target_doc_id or r.raw_so_ky_hieu, "tgt_art": r.target_article_index or "", 
                    "tgt_cl": r.target_clause_index or "", "tgt_pt": r.target_point_label or "",
                    "type": "External", "context": r.context_text.replace('\n', ' ')
                })

            # Thu thập Modification Refs
            for r in ext_result.modification_refs:
                # Bổ sung thông tin target_doc_id nếu thiếu từ primary target (lời nói đầu)
                if not r.target_doc_id and primary_target_ref:
                    r.target_doc_id = primary_target_ref.target_doc_id

                # Logic ROLL BACK: Nếu ref thiếu Điều đích, lấy từ ref trước đó
                if r.is_partial_ref and last_target_article:
                    r.target_article_index = last_target_article
                    if not r.target_doc_id:
                        r.target_doc_id = last_target_doc_id
                
                # Cập nhật state cho các ref tiếp theo
                if r.target_article_index:
                    last_target_article = r.target_article_index
                    last_target_doc_id = r.target_doc_id

                all_relationships.append({
                    "src_doc": doc_id, "src_art": src_art, "src_cl": src_cl, "src_pt": src_pt,
                    "tgt_doc": r.target_doc_id or r.raw_target_so_ky_hieu, "tgt_art": r.target_article_index or "", 
                    "tgt_cl": r.target_clause_index or "", "tgt_pt": r.target_point_label or "",
                    "type": f"Modification ({r.action.value if hasattr(r.action, 'value') else r.action})", 
                    "context": r.context_text.replace('\n', ' ')
                })
        logger.info(f"Executing stage 4: Extract done...")

        # Xuất file Markdown
        output_file = f"test_{doc_id}.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"# Kết quả trích dẫn quan hệ - Văn bản {doc_id}\n\n")
            f.write("| Source Docs | Article | Clause | Point | Target Docs | Article | Clause | Point | Type | Context |\n")
            f.write("|-------------|---------|--------|-------|-------------|---------|--------|-------|------|---------|\n")
            for rel in all_relationships:
                f.write(f"| {rel['src_doc']} | {rel['src_art']} | {rel['src_cl']} | {rel['src_pt']} | "
                        f"{rel['tgt_doc']} | {rel['tgt_art']} | {rel['tgt_cl']} | {rel['tgt_pt']} | "
                        f"{rel['type']} | {rel['context']} |\n")
        
        logger.info(f"Đã xuất kết quả ra file: {output_file}")

    except Exception as e:
        logger.error(f"Lỗi xử lý nội dung văn bản {doc_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())

    logger.info("=== HOÀN TẤT UNIFIED PIPELINE ===")

if __name__ == "__main__":
    run_unified_pipeline()
