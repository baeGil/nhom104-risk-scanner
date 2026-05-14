import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug():
    meta_path = "data/metadata_deduped.parquet"
    logger.info(f"Đang đọc {meta_path}...")
    df = pd.read_parquet(meta_path)
    
    doc_id = '178737'
    
    # Kiểm tra xem ID có tồn tại không
    # Chú ý kiểu dữ liệu của ID (có thể là int hoặc str)
    if 'id' in df.columns:
        # Thử cả string và int
        row = df[df['id'].astype(str) == doc_id]
        if row.empty:
            logger.error(f"Không tìm thấy ID {doc_id} trong toàn bộ dataframe.")
            # In ra một vài ID mẫu để xem định dạng
            logger.info(f"Mẫu ID: {df['id'].head().tolist()}")
            return
        
        row = row.iloc[0]
        logger.info(f"Tìm thấy văn bản {doc_id}:")
        logger.info(f"  - loai_van_ban: '{row.get('loai_van_ban')}'")
        logger.info(f"  - ngay_ban_hanh: '{row.get('ngay_ban_hanh')}'")
        logger.info(f"  - so_ky_hieu: '{row.get('so_ky_hieu')}'")
        
        # Kiểm tra điều kiện lọc
        core_types = ['Thông tư', 'Nghị định', 'Luật', 'Bộ luật']
        type_match = row.get('loai_van_ban') in core_types
        logger.info(f"  - Khớp loại văn bản ({core_types}): {type_match}")
        
        dt = pd.to_datetime(row.get('ngay_ban_hanh'), errors='coerce')
        logger.info(f"  - Datetime parse: {dt}")
        date_match = dt >= pd.Timestamp('2000-01-01') if pd.notna(dt) else False
        logger.info(f"  - Khớp ngày (>2000): {date_match}")
        
    else:
        logger.error("Cột 'id' không tồn tại trong metadata.")

if __name__ == "__main__":
    debug()
