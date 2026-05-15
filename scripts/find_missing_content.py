import pandas as pd
import os
import json
import time
import logging
import sys

# Thêm thư mục gốc vào path để import được crawler
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.crawl_thuvienphapluat import ThuVienPhapLuatCrawler

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def find_and_fill_missing_content():
    JSON_INPUT = "data_updated_with_ids.json"
    CONTENT_PARQUET = "data/content_clean.parquet"
    
    if not os.path.exists(JSON_INPUT):
        logger.error(f"❌ Input JSON không tìm thấy: {JSON_INPUT}")
        return

    logger.info(f"📖 Đang đọc danh sách văn bản mục tiêu từ {JSON_INPUT}...")
    with open(JSON_INPUT, "r", encoding="utf-8") as f:
        categories = json.load(f)
    
    targets = []
    for cat in categories:
        for doc in cat.get("van_ban", []):
            if doc.get("doc_id") and doc.get("so_hieu"):
                targets.append({
                    "id": str(doc["doc_id"]),
                    "so_ky_hieu": doc["so_hieu"],
                    "ten": doc.get("ten", "")
                })
    
    logger.info(f"📊 Tổng số văn bản mục tiêu từ JSON: {len(targets)}")

    if not os.path.exists(CONTENT_PARQUET):
        logger.warning(f"⚠️ {CONTENT_PARQUET} không tồn tại. Sẽ tạo mới.")
        content_df = pd.DataFrame(columns=["id", "clean_html"])
    else:
        logger.info(f"📖 Đang tải nội dung hiện có từ {CONTENT_PARQUET}...")
        content_df = pd.read_parquet(CONTENT_PARQUET)
        content_df["id"] = content_df["id"].astype(str)

    # Tìm các văn bản bị thiếu hoặc nội dung quá ngắn
    existing_ids = set(content_df["id"].tolist())
    
    short_content_ids = set()
    if not content_df.empty:
        # Lọc các id có độ dài html < 500
        short_content_ids = set(content_df[content_df["clean_html"].str.len() < 500]["id"].tolist())

    missing_targets = []
    for t in targets:
        if t["id"] not in existing_ids or t["id"] in short_content_ids:
            missing_targets.append(t)

    logger.info(f"🎯 Tìm thấy {len(missing_targets)} văn bản bị thiếu hoặc nội dung ngắn (< 500 ký tự).")

    if not missing_targets:
        logger.info("✅ Không có nội dung nào bị thiếu. Hệ thống đã đầy đủ!")
        return

    # Bắt đầu crawl
    crawler = ThuVienPhapLuatCrawler()
    new_contents = []
    
    try:
        for i, target in enumerate(missing_targets):
            logger.info(f"[{i+1}/{len(missing_targets)}] Đang xử lý: {target['ten']} ({target['so_ky_hieu']})")
            
            # Tìm kiếm URL
            urls = crawler.search_documents(target["so_ky_hieu"])
            if not urls:
                logger.warning(f"  ❌ Không tìm thấy URL cho số hiệu {target['so_ky_hieu']}")
                continue
                
            # Lấy URL đầu tiên
            url = urls[0]
            if not url.startswith("http"):
                url = "https://thuvienphapluat.vn" + url
                
            html = crawler.scrape_content_only(url)
            
            if html and len(html) > 500:
                new_contents.append({"id": target["id"], "clean_html": html})
                logger.info(f"  ✅ Đã lấy được nội dung ({len(html)} ký tự)")
            else:
                logger.warning(f"  ⚠️ Nội dung lấy về vẫn quá ngắn hoặc rỗng cho {target['so_ky_hieu']}")
            
            # Chờ 2 giây sau mỗi văn bản theo yêu cầu
            time.sleep(2)
            
            # Lưu checkpoint mỗi 10 văn bản để tránh mất dữ liệu nếu crash
            if (i + 1) % 10 == 0 and new_contents:
                logger.info(f"💾 Đang lưu checkpoint vào {CONTENT_PARQUET}...")
                new_df = pd.DataFrame(new_contents)
                content_df = pd.concat([content_df, new_df]).drop_duplicates(subset=["id"], keep="last")
                content_df.to_parquet(CONTENT_PARQUET, index=False)
                new_contents = []

    except KeyboardInterrupt:
        logger.info("🛑 Đã dừng theo yêu cầu người dùng. Đang lưu kết quả hiện tại...")
    except Exception as e:
        logger.error(f"💥 Lỗi nghiêm trọng: {e}")
    finally:
        if new_contents:
            logger.info(f"💾 Đang lưu kết quả cuối cùng vào {CONTENT_PARQUET}...")
            new_df = pd.DataFrame(new_contents)
            content_df = pd.concat([content_df, new_df]).drop_duplicates(subset=["id"], keep="last")
            content_df.to_parquet(CONTENT_PARQUET, index=False)
            logger.info(f"✅ Đã cập nhật {CONTENT_PARQUET}. Tổng số văn bản: {len(content_df)}")

if __name__ == "__main__":
    find_and_fill_missing_content()

