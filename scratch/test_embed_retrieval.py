import os
import logging
import json
import sys
from dotenv import load_dotenv
from src.embeddings.retriever import EmbeddingRetriever

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s — %(message)s")
logger = logging.getLogger(__name__)

def test_retrieval():
    doc_id = sys.argv[1] if len(sys.argv) > 1 else "153913"
    
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")
    
    logger.info(f"--- BẮT ĐẦU TEST RETRIEVAL CHO DOC {doc_id} ---")
    retriever = EmbeddingRetriever(uri, user, password)
    
    try:
        segments = retriever.get_all_segments(doc_id=doc_id)
        logger.info(f"Tìm thấy tổng cộng {len(segments)} segments.")
        
        # In ra 5 segment đầu tiên để kiểm tra
        logger.info("=== 5 SEGMENTS ĐẦU TIÊN ===")
        for i, seg in enumerate(segments[:50]):
            print(f"\n[{i+1}] UID: {seg['uid']}")
            print("-" * 30)
            print(seg['text'])
            print("-" * 30)
            
        if not segments:
            logger.warning("Không tìm thấy dữ liệu. Hãy kiểm tra lại doc_id hoặc kết nối Neo4j.")
            
    finally:
        retriever.close()
        logger.info("--- KẾT THÚC TEST ---")

if __name__ == "__main__":
    test_retrieval()
