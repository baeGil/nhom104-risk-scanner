import os
import logging
import json
from dotenv import load_dotenv
from src.cross_reference.llm_extractor import LLMExtractor

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s — %(message)s")
logger = logging.getLogger(__name__)

def run_test_pipeline(doc_id: str):
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASS = os.getenv("NEO4J_PASSWORD", "password")
    
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY environment variable is not set!")
        return

    extractor = LLMExtractor(NEO4J_URI, NEO4J_USER, NEO4J_PASS)
    try:
        logger.info(f"Đang lấy dữ liệu waterfall context cho văn bản {doc_id}...")
        contexts = extractor.get_waterfall_context(doc_id)
        logger.info(f"Tìm thấy {len(contexts)} leaf nodes.")
        
        if not contexts:
            logger.warning("Không tìm thấy dữ liệu.")
            return

        # Gom batch (ví dụ lấy batch đầu tiên để test)
        batches = extractor.batch_by_word_count(contexts, max_words=1000)
        logger.info(f"Đã chia thành {len(batches)} batches.")
        
        # Chạy toàn bộ các batch
        all_results = {}
        total_batches = len(batches)
        
        for i, batch in enumerate(batches[:2]):
            logger.info(f"--- Đang xử lý Batch {i+1}/{total_batches} ({len(batch)} nodes) ---")
            try:
                batch_result = extractor.extract_batch(batch)
                if "results" in batch_result:
                    all_results.update(batch_result["results"])
                else:
                    logger.error(f"Batch {i+1} trả về kết quả không hợp lệ: {batch_result}")
            except Exception as e:
                logger.error(f"Lỗi khi xử lý Batch {i+1}: {e}")

        # Lưu kết quả ra file
        output_file = f"scratch/output_{doc_id}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump({"results": all_results}, f, ensure_ascii=False, indent=2)
        
        logger.info(f"=== HOÀN THÀNH — Đã trích xuất {len(all_results)} nodes ===")
        logger.info(f"Kết quả chi tiết đã được lưu tại: {output_file}")
        
        # In ra 5 node đầu tiên để kiểm tra thứ tự
        first_5_keys = list(all_results.keys())[:5]
        logger.info("5 node đầu tiên trong kết quả:")
        for k in first_5_keys:
            logger.info(f"  - {k}")
        
    finally:
        extractor.close()

if __name__ == "__main__":
    import sys
    target_doc = "153913"
    if len(sys.argv) > 1:
        target_doc = sys.argv[1]
    run_test_pipeline(target_doc)
