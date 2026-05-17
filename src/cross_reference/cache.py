import os
import json
from loguru import logger
from typing import Optional
from src.data_pipeline.normalize import normalize

class ReferenceCache:
    def __init__(self, lookup_path: str = "data/so_ky_hieu_lookup.json"):
        self.lookup_path = lookup_path
        self.cache: dict[str, str] = {}
        self._load_cache()

    def _load_cache(self):
        """Nạp dữ liệu từ file JSON vào RAM."""
        if not os.path.exists(self.lookup_path):
            logger.warning(f"File lookup không tồn tại: {self.lookup_path}. Cache sẽ trống.")
            return

        try:
            with open(self.lookup_path, "r", encoding="utf-8") as f:
                self.cache = json.load(f)
            logger.success(f"Đã nạp {len(self.cache)} bản ghi vào ReferenceCache.")
        except Exception as e:
            logger.error(f"Lỗi khi nạp ReferenceCache: {e}")

    def get_doc_id(self, raw_so_ky_hieu: str, loai_van_ban: str = "") -> Optional[str]:
        """
        Chuẩn hóa số ký hiệu thô và tra cứu doc_id.
        """
        if not raw_so_ky_hieu:
            return None

        # 1. Chuẩn hóa nhẹ (xóa khoảng trắng thừa)
        clean_raw = str(raw_so_ky_hieu).strip()
        
        # 2. Sử dụng hàm normalize của Người A
        normalized_id = normalize(clean_raw, loai_van_ban)
        if not normalized_id:
            return None

        # 3. Tra cứu trong RAM
        doc_id = self.cache.get(normalized_id)
        if doc_id:
            return str(doc_id)
            
        return None

if __name__ == "__main__":
    # Test nhanh
    cache = ReferenceCache()
    test_cases = ["46/2014/NĐ-CP", "59/2020/QH14", "12/2018/TT-BTC"]
    for case in test_cases:
        doc_id = cache.get_doc_id(case)
        print(f"Raw: {case} -> Doc ID: {doc_id}")
