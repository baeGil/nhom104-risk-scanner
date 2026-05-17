import json
import logging
import os
import sys
import time

import pandas as pd

# Thêm thư mục gốc vào path để import được crawler
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.crawl_thuvienphapluat import ThuVienPhapLuatCrawler

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def build_targets(schema_items):
    """Chuyển schema phẳng thành danh sách target chuẩn để xử lý."""
    targets = []
    for doc in schema_items:
        doc_id = doc.get("doc_id")
        if not doc_id:
            continue

        targets.append(
            {
                "id": str(doc_id),
                "so_ky_hieu": doc.get("so_ky_hieu"),
                "title": doc.get("title", ""),
                "loai_van_ban": doc.get("loai_van_ban", ""),
                "match_method": doc.get("match_method", ""),
            }
        )
    return targets


def find_and_fill_missing_content():
    JSON_INPUT = "chu_de_lao_dong_schema_with_ids.json"
    CONTENT_PARQUET = "data/content_clean.parquet"

    if not os.path.exists(JSON_INPUT):
        logger.error(f"❌ Input JSON không tìm thấy: {JSON_INPUT}")
        return

    logger.info(f"📖 Đang đọc danh sách văn bản mục tiêu từ {JSON_INPUT}...")
    with open(JSON_INPUT, "r", encoding="utf-8") as f:
        schema_items = json.load(f)

    targets = build_targets(schema_items)
    logger.info(f"📊 Tổng số văn bản mục tiêu từ JSON: {len(targets)}")

    if not os.path.exists(CONTENT_PARQUET):
        logger.warning(f"⚠️ {CONTENT_PARQUET} không tồn tại. Sẽ tạo mới.")
        content_df = pd.DataFrame(columns=["id", "clean_html"])
    else:
        logger.info(f"📖 Đang tải nội dung hiện có từ {CONTENT_PARQUET}...")
        content_df = pd.read_parquet(CONTENT_PARQUET)
        content_df["id"] = content_df["id"].astype(str)

    existing_ids = set(content_df["id"].tolist()) if not content_df.empty else set()

    short_content_ids = set()
    if not content_df.empty and "clean_html" in content_df.columns:
        short_content_ids = set(
            content_df[content_df["clean_html"].fillna("").str.len() < 500]["id"].tolist()
        )

    missing_targets = []
    for t in targets:
        if t["id"] not in existing_ids or t["id"] in short_content_ids:
            missing_targets.append(t)

    logger.info(
        f"🎯 Tìm thấy {len(missing_targets)} văn bản bị thiếu hoặc nội dung ngắn (< 500 ký tự)."
    )

    if not missing_targets:
        logger.info("✅ Không có nội dung nào bị thiếu. Hệ thống đã đầy đủ!")
        return

    crawler = ThuVienPhapLuatCrawler()
    new_contents = []

    try:
        for i, target in enumerate(missing_targets):
            display_name = target["title"] or target["so_ky_hieu"] or target["id"]
            logger.info(
                f"[{i+1}/{len(missing_targets)}] Đang xử lý: {display_name} "
                f"({target.get('so_ky_hieu') or 'none'})"
            )

            search_terms = []
            if target.get("so_ky_hieu"):
                search_terms.append(target["so_ky_hieu"])
            if target.get("title"):
                search_terms.append(target["title"])

            urls = []
            for term in search_terms:
                urls = crawler.search_documents(term)
                if urls:
                    logger.info(f"  ✅ Tìm thấy URL bằng từ khóa: {term}")
                    break

            if not urls:
                logger.warning(f"  ❌ Không tìm thấy URL cho văn bản: {display_name}")
                continue

            url = urls[0]
            if not url.startswith("http"):
                url = "https://thuvienphapluat.vn" + url

            html = crawler.scrape_content_only(url)

            if html and len(html) > 500:
                new_contents.append({"id": target["id"], "clean_html": html})
                logger.info(f"  ✅ Đã lấy được nội dung ({len(html)} ký tự)")
            else:
                logger.warning(f"  ⚠️ Nội dung lấy về vẫn quá ngắn hoặc rỗng cho {display_name}")

            time.sleep(2)

            if (i + 1) % 10 == 0 and new_contents:
                logger.info(f"💾 Đang lưu checkpoint vào {CONTENT_PARQUET}...")
                new_df = pd.DataFrame(new_contents)
                content_df = pd.concat([content_df, new_df]).drop_duplicates(
                    subset=["id"], keep="last"
                )
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
            content_df = pd.concat([content_df, new_df]).drop_duplicates(
                subset=["id"], keep="last"
            )
            content_df.to_parquet(CONTENT_PARQUET, index=False)
            logger.info(f"✅ Đã cập nhật {CONTENT_PARQUET}. Tổng số văn bản: {len(content_df)}")


if __name__ == "__main__":
    find_and_fill_missing_content()
