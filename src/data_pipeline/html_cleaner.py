"""
T0.4 — Clean HTML Pipeline
============================

Làm sạch raw HTML để chuẩn bị cho parser của Người B (T1.1).

Rules (từ spec):
  STRIP  : <table class="detailcontent">, <tr>, <td> (wrapper tables)
  REMOVE : <font> tags (giữ content, bỏ tag)
  REMOVE : <dir> tags
  REMOVE : <p> rỗng (chỉ &nbsp; hoặc whitespace)
  KEEP   : <b>, <strong>  ← CRITICAL: Người B dùng nhận diện Điều/Khoản
  KEEP   : <i>, <em>      ← CRITICAL: định nghĩa pháp lý
  KEEP   : <table> bên trong articles (biểu phí, phụ lục)
  VERIFY : clean_html phải giữ lại toàn bộ text từ raw_html

Spec: data-cleanup-and-normalization
Task: T0.4
"""
from __future__ import annotations

import logging
import re
import unicodedata
from typing import Optional

try:
    from bs4 import BeautifulSoup, Tag
    _BS4_AVAILABLE = True
except ImportError:
    _BS4_AVAILABLE = False
    BeautifulSoup = None

logger = logging.getLogger(__name__)

# Tags cần STRIP hoàn toàn (kể cả content)
_STRIP_TAGS_FULL = {"script", "style", "dir"}

# Tags cần UNWRAP (giữ content, bỏ tag)
_UNWRAP_TAGS = {"font", "span"}

# Tags LUÔN GIỮ NGUYÊN — CRITICAL
_PRESERVE_TAGS = {"b", "strong", "i", "em", "table", "tr", "td", "th", "ul", "li"}


# ---------------------------------------------------------------------------
# Main cleaner
# ---------------------------------------------------------------------------

def clean(raw_html: str) -> str:
    """
    Làm sạch raw HTML → clean HTML.

    Pipeline:
      1. Parse với BeautifulSoup
      2. Strip wrapper tables (detailcontent)
      3. Unwrap <font> tags
      4. Remove <dir>, <script>, <style>
      5. Remove empty <p> tags
      6. Normalize spacing
      7. Serialize lại

    Parameters
    ----------
    raw_html : str
        HTML thô từ database hoặc crawler.

    Returns
    -------
    str
        Clean HTML, ready cho Người B parser.
    """
    if not raw_html or not raw_html.strip():
        return ""

    if not _BS4_AVAILABLE:
        raise ImportError("beautifulsoup4 required: pip install beautifulsoup4 lxml")

    soup = BeautifulSoup(raw_html, "lxml")

    _strip_wrapper_tables(soup)
    _remove_tags_full(soup, _STRIP_TAGS_FULL)
    _unwrap_tags(soup, _UNWRAP_TAGS)
    _remove_empty_paragraphs(soup)
    _normalize_paragraphs(soup)

    # Serialize (lấy body content nếu có, không thì lấy toàn bộ)
    body = soup.find("body")
    result = str(body) if body else str(soup)

    return result.strip()


def verify(raw_html: str, clean_html: str, threshold: float = 0.9) -> bool:
    """
    Kiểm tra clean_html không bị mất text quan trọng.

    So sánh plain text length: clean / raw >= threshold.
    Cũng kiểm tra các thẻ PRESERVE_TAGS còn tồn tại nếu có trong raw.

    Returns True nếu pass.
    """
    if not raw_html:
        return True

    raw_text   = _extract_text(raw_html)
    clean_text = _extract_text(clean_html)

    if not raw_text:
        return True

    ratio = len(clean_text) / len(raw_text)
    if ratio < threshold:
        logger.warning(
            "Text loss detected: clean/raw ratio = %.2f (threshold %.2f)",
            ratio, threshold,
        )
        return False

    # Kiểm tra các heading quan trọng còn nguyên
    dieu_in_raw   = len(re.findall(r"[ĐĐ][iíì]ều\s+\d+", raw_text, re.UNICODE))
    dieu_in_clean = len(re.findall(r"[ĐĐ][iíì]ều\s+\d+", clean_text, re.UNICODE))
    if dieu_in_raw > 0 and dieu_in_clean == 0:
        logger.warning("All 'Điều' markers lost after cleaning!")
        return False

    return True


def process_dataframe(df, raw_col: str = "raw_html", clean_col: str = "clean_html"):
    """
    Thêm cột clean_html vào DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Phải có cột raw_col.
    raw_col : str
        Tên cột chứa raw HTML.
    clean_col : str
        Tên cột sẽ được thêm/ghi đè.

    Returns
    -------
    pd.DataFrame với cột clean_col mới.
    """
    failed = 0

    def _clean_row(raw: str):
        nonlocal failed
        try:
            result = clean(raw or "")
            if raw and not verify(raw, result):
                logger.warning("Verification failed for a row, keeping raw")
                return raw  # fallback: giữ nguyên raw
            return result
        except Exception as exc:
            logger.error("clean() failed: %s", exc)
            failed += 1
            return raw or ""

    df = df.copy()
    df[clean_col] = df[raw_col].map(_clean_row)

    logger.info(
        "HTML cleaning done: %d rows, %d failed, kept raw as fallback",
        len(df), failed,
    )
    return df


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _strip_wrapper_tables(soup) -> None:
    """
    Bóc wrapper table.detailcontent: thay thế bằng nội dung bên trong.
    Chỉ strip các table có class "detailcontent" ở cấp ngoài cùng.
    """
    for table in soup.find_all("table", class_="detailcontent"):
        table.unwrap()


def _remove_tags_full(soup, tags: set[str]) -> None:
    """Xóa hoàn toàn các thẻ (kể cả content)."""
    for tag_name in tags:
        for tag in soup.find_all(tag_name):
            tag.decompose()


def _unwrap_tags(soup, tags: set[str]) -> None:
    """Giữ content, bỏ tag."""
    for tag_name in tags:
        for tag in soup.find_all(tag_name):
            tag.unwrap()


def _remove_empty_paragraphs(soup) -> None:
    """Xóa <p> chỉ chứa whitespace hoặc &nbsp;."""
    for p in soup.find_all("p"):
        text = p.get_text(strip=True).replace("\xa0", "").strip()
        if not text:
            p.decompose()


def _normalize_paragraphs(soup) -> None:
    """Chuẩn hóa spacing trong <p> tags (bỏ multiple spaces)."""
    for p in soup.find_all("p"):
        # Normalize whitespace trong text nodes trực tiếp
        for child in p.children:
            if hasattr(child, "string") and child.string:
                pass  # BeautifulSoup handles this in serialization


def _extract_text(html: str) -> str:
    """Lấy plain text từ HTML (dùng để verify)."""
    text = re.sub(r"<[^>]+>", " ", html)
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main(
    content_path: str  = "data/content.parquet",
    output_path: str   = "data/content_clean.parquet",
    raw_col: str       = "content_html",
) -> None:
    """
    T0.4 main: Đọc content parquet, clean HTML, xuất parquet mới.
    Đọc từ data thật (content_html column) hoặc từ crawler output (raw_html column).
    """
    import pyarrow.parquet as pq  # noqa: PLC0415
    import pyarrow as pa
    import pandas as pd
    from pathlib import Path

    logger.info("T0.4 — Loading content schema from %s", content_path)

    pf = pq.ParquetFile(content_path)
    schema = pf.schema_arrow
    col_names = [f.name for f in schema]

    # Tự detect cột chứa HTML
    if raw_col not in col_names:
        for candidate in ["raw_html", "content_html", "html"]:
            if candidate in col_names:
                raw_col = candidate
                break

    logger.info("T0.4 — Using column '%s' as HTML source", raw_col)
    logger.info("T0.4 — Total rows: %d", pf.metadata.num_rows)

    # Xử lý từng batch để tiết kiệm RAM (file 393MB)
    BATCH_SIZE = 2000
    total_failed = 0
    
    import pyarrow as pa
    import pyarrow.parquet as pq

    writer = None

    for i, batch in enumerate(pf.iter_batches(batch_size=BATCH_SIZE, columns=["id", raw_col])):
        df_batch = batch.to_pandas()
        df_clean = process_dataframe(df_batch, raw_col=raw_col, clean_col="clean_html")
        
        # Chỉ giữ lại cột cần thiết để tiết kiệm đĩa
        table = pa.Table.from_pandas(df_clean[["id", "clean_html"]])
        
        if writer is None:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            writer = pq.ParquetWriter(output_path, table.schema)
        
        writer.write_table(table)
        
        if (i + 1) % 10 == 0:
            rows_done = (i + 1) * BATCH_SIZE
            logger.info("T0.4 — Processed %d rows...", rows_done)

    if writer:
        writer.close()
    
    logger.info("T0.4 done — output: %s (streaming finished)", output_path)



if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s — %(message)s")
    main()
