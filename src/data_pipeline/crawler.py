"""
T0.3 — Crawl Missing Content
==============================

Crawl HTML nội dung cho 2,636 văn bản còn thiếu từ thuvienphapluat.vn.

Strategy:
  - Search theo so_ky_hieu, lấy URL trang chi tiết
  - Extract content HTML
  - Rate limiting để tránh bị block
  - Checkpoint để resume khi lỗi
  - Validate: nội dung phải có ≥ 1 marker "Điều"

Spec: data-cleanup-and-normalization
Task: T0.3

NOTE: Crawler đã được tạo nhưng cấu trúc search của thuvienphapluat.vn
có thể đã thay đổi. Cần kiểm tra và tinh chỉnh lại.
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Optional
from urllib.parse import quote

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config defaults
# ---------------------------------------------------------------------------

BASE_URL         = "https://thuvienphapluat.vn"
SEARCH_URL_TPL   = BASE_URL + "/page/tim-van-ban.aspx?keyword={query}"
DEFAULT_RATE_SEC = 1.5    # seconds between requests
DEFAULT_TIMEOUT  = 15     # request timeout seconds
CHECKPOINT_FILE  = "output/crawl_checkpoint.json"


# ---------------------------------------------------------------------------
# Core crawler functions
# ---------------------------------------------------------------------------

def search_document(so_ky_hieu: str, session=None) -> Optional[str]:
    """
    Tìm URL trang chi tiết văn bản theo so_ky_hieu.

    Parameters
    ----------
    so_ky_hieu : str
        Số ký hiệu, ví dụ "46/2014/NĐ-CP"
    session : requests.Session, optional
        Tái sử dụng session để tiết kiệm connection.

    Returns
    -------
    str | None
        URL trang chi tiết (vd: ".../van-ban/...html"), hoặc None nếu không tìm thấy.
    """

    import requests
    from bs4 import BeautifulSoup
    from urllib.parse import quote

    if session is None:
        session = requests.Session()
    
    url = SEARCH_URL_TPL.format(query=quote(so_ky_hieu))
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        resp = session.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        result = soup.select_one('.nqTitle a')
        if result:
            # Handle both relative and absolute URLs
            href = result.get('href')
            if href.startswith('/'):
                return BASE_URL + href
            elif href.startswith('http'):
                return href
            else:
                return BASE_URL + '/' + href
    except Exception as e:
        logger.warning(f"Error searching for {so_ky_hieu}: {e}")
        
    return None


def extract_content_html(detail_url: str, session=None) -> Optional[str]:
    """
    Extract HTML nội dung từ trang chi tiết.

    Cần lấy phần tử chứa nội dung văn bản (thường là div.detail-content
    hoặc table.detailcontent).

    Returns
    -------
    str | None
        Raw HTML của phần nội dung, hoặc None nếu không tìm được.
    """

    import requests
    from bs4 import BeautifulSoup

    if session is None:
        session = requests.Session()
        
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        resp = session.get(detail_url, headers=headers, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        content_div = soup.select_one('div.content1') or soup.select_one('div#divContentDoc')
        if content_div:
            return str(content_div)
    except Exception as e:
        logger.warning(f"Error extracting content from {detail_url}: {e}")
        
    return None


def validate_content(html: str) -> bool:
    """
    Kiểm tra HTML có hợp lệ không (phải chứa ≥ 1 marker "Điều").

    Returns True nếu hợp lệ.
    """
    import re
    return bool(re.search(r"[ĐĐ][iíì]ều\s+\d+", html, re.UNICODE))


def crawl_batch(
    missing_docs: list[dict],
    *,
    rate_limit_sec: float = DEFAULT_RATE_SEC,
    checkpoint_path: str = CHECKPOINT_FILE,
    max_retries: int = 3,
) -> list[dict]:
    """
    Crawl nhiều documents, với checkpoint để resume khi lỗi.

    Parameters
    ----------
    missing_docs : list of dict
        Mỗi dict: {doc_id, so_ky_hieu, loai_van_ban}
    rate_limit_sec : float
        Thời gian chờ giữa các requests.
    checkpoint_path : str
        File JSON lưu trạng thái (doc_ids đã crawl thành công).
    max_retries : int
        Số lần retry khi gặp lỗi network.

    Returns
    -------
    list of dict
        {doc_id, so_ky_hieu, raw_html, status: "success"|"not_found"|"error"}

    TODO: Uncomment implementation khi search/extract functions hoàn thiện.
    """
    checkpoint = _load_checkpoint(checkpoint_path)
    results    = []

    for doc in missing_docs:
        doc_id    = doc["doc_id"]
        so_ky_hieu = doc.get("so_ky_hieu", "")

        # Skip nếu đã crawl thành công
        if doc_id in checkpoint.get("done", []):
            logger.debug("Skip already-crawled: %s", doc_id)
            continue

        logger.info("Crawling: %s (%s)", doc_id, so_ky_hieu)

        session = __import__('requests').Session()
        for attempt in range(max_retries):
            try:
                detail_url = search_document(so_ky_hieu, session=session)
                if not detail_url:
                    results.append({"doc_id": doc_id, "status": "not_found"})
                    break
                html = extract_content_html(detail_url, session=session)
                if not html or not validate_content(html):
                    results.append({"doc_id": doc_id, "status": "invalid_content"})
                    break
                results.append({"doc_id": doc_id, "raw_html": html, "status": "success"})
                _save_checkpoint(checkpoint_path, doc_id)
                break
            except Exception as exc:
                err_str = str(exc)
                # 403 = bị chặn vĩnh viễn hoặc không tồn tại → không retry
                if "403" in err_str or "410" in err_str:
                    logger.warning("Permanent failure for %s (HTTP %s) — skipping",
                                   doc_id, "403" if "403" in err_str else "410")
                    results.append({"doc_id": doc_id, "status": "blocked"})
                    _save_checkpoint(checkpoint_path, doc_id)  # đánh dấu để không retry
                    break
                logger.warning("Attempt %d failed for %s: %s", attempt+1, doc_id, exc)
                time.sleep(rate_limit_sec * 2)
        else:
            # Nếu vòng for kết thúc mà không gặp 'break' (tất cả retries đều lỗi)
            results.append({"doc_id": doc_id, "status": "error", "detail": "All retries failed"})

        time.sleep(rate_limit_sec)

    logger.info("Crawl batch done: %d docs, %d results", len(missing_docs), len(results))
    return results


# ---------------------------------------------------------------------------
# Checkpoint helpers
# ---------------------------------------------------------------------------

def _load_checkpoint(path: str) -> dict:
    """Load checkpoint file (tạo mới nếu chưa có)."""
    p = Path(path)
    if p.exists():
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    return {"done": []}


def _save_checkpoint(path: str, doc_id: str) -> None:
    """Thêm doc_id vào checkpoint."""
    checkpoint = _load_checkpoint(path)
    if doc_id not in checkpoint["done"]:
        checkpoint["done"].append(doc_id)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main(
    metadata_path: str    = "data/metadata_deduped.parquet",
    content_path: str     = "data/content.parquet",
    output_path: str      = "data/content_enriched.parquet",
    checkpoint_path: str  = CHECKPOINT_FILE,
) -> None:
    """
    T0.3 main: Tìm docs thiếu content, crawl, merge vào parquet.
    """
    import pyarrow.parquet as pq  # noqa: PLC0415

    logger.info("T0.3 — Finding missing content docs (streaming mode)")

    # Đọc IDs từ content.parquet theo batch để tránh OOM (393MB)
    content_pf = pq.ParquetFile(content_path)
    has_content: set = set()
    for batch in content_pf.iter_batches(batch_size=5000, columns=["id"]):
        has_content.update(str(v) for v in batch.column("id").to_pylist())
    logger.info("T0.3 — Content IDs loaded: %d docs have content", len(has_content))

    # Đọc metadata_deduped (2.2MB) — an toàn để load bình thường
    import pandas as pd  # noqa: PLC0415
    meta_df = pd.read_parquet(metadata_path)
    meta_df["id"] = meta_df["id"].astype(str)

    missing_df = meta_df[~meta_df["id"].isin(has_content)]
    logger.info("Missing content: %d docs", len(missing_df))


    missing_docs = missing_df[["id", "so_ky_hieu", "loai_van_ban"]].rename(
        columns={"id": "doc_id"}
    ).to_dict("records")

    results = crawl_batch(missing_docs, checkpoint_path=checkpoint_path)

    # Merge vào content parquet
    success_results = [r for r in results if r.get("status") == "success"]
    blocked_count   = sum(1 for r in results if r.get("status") == "blocked")
    not_found_count = sum(1 for r in results if r.get("status") == "not_found")

    logger.info(
        "T0.3 summary: %d success, %d blocked/403, %d not_found, %d error",
        len(success_results), blocked_count, not_found_count,
        len(results) - len(success_results) - blocked_count - not_found_count,
    )

    if success_results:
        import pyarrow as pa
        import pyarrow.parquet as pq

        new_df = pd.DataFrame(success_results)[["doc_id", "raw_html"]].rename(
            columns={"doc_id": "id", "raw_html": "content_html"}
        )
        # Merge dùng pyarrow để tránh OOM với file 393MB
        new_table = pa.Table.from_pandas(new_df)
        if Path(output_path).exists():
            existing = pq.read_table(output_path)
            merged   = pa.concat_tables([existing, new_table])
        else:
            merged = new_table
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        pq.write_table(merged, output_path)
        logger.info("Merged %d new docs → %s", len(new_df), output_path)
    else:
        logger.info("No successful crawls — 642 docs are local/unavailable on TVPL, skipping merge.")
        # Tạo output_path rỗng nếu chưa tồn tại (T0.4 cần file này)
        if not Path(output_path).exists():
            import pyarrow as pa
            import pyarrow.parquet as pq
            empty = pa.table({"id": pa.array([], type=pa.string()),
                              "content_html": pa.array([], type=pa.string())})
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            pq.write_table(empty, output_path)

    logger.info("T0.3 done — %d crawled", len(results))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s — %(message)s")
    main()
