import pandas as pd
import json
import re
import os
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s — %(message)s")
logger = logging.getLogger(__name__)

def normalize_so_hieu(so_hieu):
    """Chuẩn hóa số ký hiệu để làm key tra cứu."""
    so_hieu = str(so_hieu).strip().upper()
    # Tìm định dạng chuẩn 123/2024/ABC
    match = re.search(r'(\d+/\d+/[A-ZĐ0-9\-]+)', so_hieu)
    if match:
        core_skh = match.group(1)
    else:
        # Fallback lấy phần đầu tiên trước khoảng trắng hoặc ngoặc
        match_fallback = re.search(r'^([^\s\(\)]+)', so_hieu)
        if match_fallback:
            core_skh = match_fallback.group(1)
        else:
            core_skh = so_hieu
            
    parts = core_skh.split('/')
    # Loại bỏ số 0 ở đầu các phần (ví dụ: 08 -> 8)
    stripped_parts = [re.sub(r'^0+', '', p) if re.match(r'^0+\d+', p) else p for p in parts]
    return '/'.join(stripped_parts)

from src.data_pipeline.normalize import normalize

def build():
    meta_path = "data/metadata_deduped.parquet"
    output_path = "data/so_ky_hieu_lookup.json"
    
    if not os.path.exists(meta_path):
        logger.error(f"Không tìm thấy file {meta_path}")
        return

    logger.info(f"Đang đọc {meta_path}...")
    df = pd.read_parquet(meta_path)
    
    lookup = {}
    for _, row in df.iterrows():
        skh_raw = str(row.get('so_ky_hieu', ''))
        loai_vb = str(row.get('loai_van_ban', ''))
        doc_id = str(row.get('id') or row.get('doc_id', ''))
        
        if skh_raw and skh_raw.lower() != 'nan' and doc_id:
            # Dùng hàm normalize chuẩn (dạng LT-038-2019)
            skh_clean = normalize(skh_raw, loai_vb)
            if skh_clean:
                lookup[skh_clean] = doc_id
            
    logger.info(f"Đã tạo bảng tra cứu với {len(lookup)} mục.")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(lookup, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Đã lưu bảng tra cứu ra {output_path}")

if __name__ == "__main__":
    build()
