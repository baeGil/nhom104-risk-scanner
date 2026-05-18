import os
import logging
import pandas as pd
from src.embeddings.retriever import EmbeddingRetriever
from src.env_utils import load_project_env

load_project_env()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s — %(message)s")
logger = logging.getLogger(__name__)

def export_to_parquet():
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")
    
    logger.info("--- BẮT ĐẦU TRÍCH XUẤT TOÀN BỘ DỮ LIỆU TỪ NEO4J ---")
    retriever = EmbeddingRetriever(uri, user, password)
    
    try:
        # Lấy toàn bộ segments (không truyền doc_id)
        segments = retriever.get_all_segments()
        logger.info(f"Đã lấy xong {len(segments)} segments.")
        
        if not segments:
            logger.warning("Không có dữ liệu để xuất!")
            return

        # Chuyển sang DataFrame
        df = pd.DataFrame(segments)
        
        # Đường dẫn file output
        output_path = "data/legal_segments_for_colab.parquet"
        
        # Xuất ra Parquet (yêu cầu pyarrow hoặc fastparquet)
        logger.info(f"Đang ghi dữ liệu ra file: {output_path}...")
        df.to_parquet(output_path, engine='pyarrow', index=False)
        
        logger.info(f"=== XUẤT DỮ LIỆU THÀNH CÔNG ===")
        logger.info(f"Tổng số bản ghi: {len(df)}")
        logger.info(f"File path: {os.path.abspath(output_path)}")
        
    except ImportError:
        logger.error("Thiếu thư viện 'pyarrow'. Hãy chạy: pip install pyarrow")
    except Exception as e:
        logger.error(f"Lỗi khi xuất dữ liệu: {e}")
    finally:
        retriever.close()

if __name__ == "__main__":
    export_to_parquet()
