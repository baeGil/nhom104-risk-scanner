import pandas as pd
import os
from loguru import logger

def prepare_sandbox():
    metadata_path = "data/metadata_deduped.parquet"
    content_path = "data/content_clean.parquet"
    output_path = "data/sandbox_sample_100.parquet"

    if not os.path.exists(metadata_path) or not os.path.exists(content_path):
        logger.error("Không tìm thấy file Parquet gốc trong thư mục data/")
        return

    logger.info("Đang đọc metadata...")
    df_meta = pd.read_parquet(metadata_path)
    
    logger.info("Đang lọc 100 văn bản Luật...")
    df_luat = df_meta[df_meta['loai_van_ban'] == 'Luật'].head(100).copy()
    
    if df_luat.empty:
        logger.warning("Không tìm thấy văn bản nào có loại là 'Luật'")
        return

    logger.info(f"Đã chọn {len(df_luat)} văn bản Luật. Đang đọc nội dung...")
    df_content = pd.read_parquet(content_path)
    
    logger.info("Đang ép kiểu ID về string để Join...")
    df_luat['id'] = df_luat['id'].astype(str)
    df_content['id'] = df_content['id'].astype(str)
    
    logger.info("Đang thực hiện Join dữ liệu...")
    df_sandbox = pd.merge(df_luat, df_content, on='id', how='inner')
    
    # Đổi tên 'id' thành 'doc_id'
    df_sandbox = df_sandbox.rename(columns={'id': 'doc_id'})
    
    logger.info(f"Kết quả sau khi Join: {len(df_sandbox)} bản ghi.")
    
    logger.info(f"Đang lưu dữ liệu ra {output_path}...")
    df_sandbox.to_parquet(output_path, index=False)
    logger.success("Hoàn thành chuẩn bị dữ liệu Sandbox!")

if __name__ == "__main__":
    prepare_sandbox()
