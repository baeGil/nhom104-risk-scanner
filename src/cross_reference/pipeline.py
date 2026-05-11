"""
Integrated Legal Pipeline: Preamble -> Segmentation -> Relationship Extraction -> Neo4j
Ensures zero mismatch between document structure and extracted links.
"""
import logging
from typing import Optional, Dict, Any

from bs4 import BeautifulSoup
from neo4j import Driver

# Import từ module segmentation (Phase 1)
from segmentation.parser import LegalDocumentParser
from segmentation.writer import SegmentWriter
from segmentation.models import HierarchyType

# Import từ module cross_reference (Phase 2)
from cross_reference.extractor import CrossReferenceExtractor
from cross_reference.writer import CrossReferenceWriter

logger = logging.getLogger(__name__)

class IntegratedLegalPipeline:
    def __init__(
        self,
        neo4j_driver: Driver,
        lookup_table: Dict[str, str],
        short_title_map_path: Optional[str] = "data/short_title_mapping.json"
    ):
        self.driver = neo4j_driver
        self.parser = LegalDocumentParser()
        self.segment_writer = SegmentWriter(neo4j_driver)
        self.extractor = CrossReferenceExtractor(
            lookup_table=lookup_table,
            short_title_map_path=short_title_map_path
        )
        self.ref_writer = CrossReferenceWriter(neo4j_driver)

    def process_document(self, doc_id: str, clean_html: str, metadata: Dict[str, Any]):
        """
        Runs the full pipeline for one document.
        """
        logger.info(f"Starting integrated pipeline for doc: {doc_id}")
        
        # 1. PREAMBLE ANALYSIS
        # Extract preamble (everything before the first "Điều 1")
        soup = BeautifulSoup(clean_html, 'html.parser')
        full_text = soup.get_text(separator=' ', strip=True)
        
        # Simple split to get preamble
        import re
        preamble_match = re.search(r'^(.*?)Điều\s+1[\.\s]', full_text, re.DOTALL | re.IGNORECASE)
        preamble_text = preamble_match.group(1) if preamble_match else full_text[:2000]
        
        anchor = self.extractor._extract_preamble_anchor(preamble_text)
        is_modifying = any(kw in metadata.get('title', '').lower() for kw in ["sửa đổi", "bổ sung"])
        
        if anchor:
            logger.info(f"Found Preamble Anchor: {anchor.raw_so_ky_hieu} (Target ID: {anchor.target_doc_id})")
        
        # 2. SEGMENTATION
        parse_result = self.parser.parse(
            doc_id=doc_id,
            clean_html=clean_html,
            loai_van_ban=metadata.get('loai_van_ban', '')
        )
        
        # Write segments to Neo4j first (Structural Nodes)
        self.segment_writer.write_batch([parse_result])
        
        # 3. RELATIONSHIP EXTRACTION
        all_extraction_results = []
        
        # Track current hierarchy context to fill source coordinates
        current_art_idx = None
        current_khoan_idx = None

        for segment in parse_result.segments:
            # Update hierarchy context
            if segment.hierarchy_type == HierarchyType.DIEU:
                current_art_idx = str(segment.index)
                current_khoan_idx = None
            elif segment.hierarchy_type == HierarchyType.KHOAN:
                current_khoan_idx = str(segment.index)
            
            # Extract references from this specific segment (Article, Clause, or Point)
            extraction_result = self.extractor.extract_from_article(
                doc_id=doc_id,
                article_uid=segment.uid or f"{doc_id}_misc",
                article_text=segment.clean_text,
                is_modifying_doc=is_modifying
            )
            
            # Enrich with source coordinates from parser
            for ref in extraction_result.modification_refs:
                # Use parser-provided indices if not already set
                if not ref.source_clause_index:
                    ref.source_clause_index = current_khoan_idx
                
                # Apply preamble anchor logic
                if anchor and not ref.raw_target_so_ky_hieu:
                    ref.raw_target_so_ky_hieu = anchor.raw_so_ky_hieu
                    ref.target_doc_id = anchor.target_doc_id
            
            # Also enrich external/internal refs with source clause if needed
            for ref in extraction_result.external_refs + extraction_result.internal_refs:
                if not ref.source_clause_uid and segment.hierarchy_type == HierarchyType.KHOAN:
                    ref.source_clause_uid = segment.uid

            all_extraction_results.append(extraction_result)
            
        # 4. RELATIONSHIP INGESTION
        # Write all extracted relationships to Neo4j
        for result in all_extraction_results:
            self.ref_writer.write(result)
            
        logger.info(f"Completed integrated pipeline for doc: {doc_id}. "
                    f"Processed {len(all_extraction_results)} articles.")
        
        return {
            "doc_id": doc_id,
            "segments_count": len(parse_result.segments),
            "articles_processed": len(all_extraction_results),
            "anchor_found": anchor.raw_so_ky_hieu if anchor else None
        }

    def close(self):
        self.segment_writer.close()
        self.ref_writer.close()
