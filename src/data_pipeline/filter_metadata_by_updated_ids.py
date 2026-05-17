import argparse
import json
import logging
from pathlib import Path
from typing import Any, Set

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s — %(message)s")
logger = logging.getLogger(__name__)


def extract_doc_ids(node: Any, ids: Set[str]) -> None:
    """Thu thập toàn bộ `doc_id` xuất hiện trong JSON, kể cả các object lồng nhau."""
    if isinstance(node, dict):
        doc_id = node.get("doc_id")
        if doc_id is not None:
            ids.add(str(doc_id))
        for value in node.values():
            extract_doc_ids(value, ids)
    elif isinstance(node, list):
        for item in node:
            extract_doc_ids(item, ids)


def filter_metadata(
    json_path: Path,
    metadata_path: Path,
    output_path: Path,
    titles_output_path: Path,
) -> int:
    logger.info("Đọc JSON nguồn: %s", json_path)
    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    target_ids: Set[str] = set()
    extract_doc_ids(data, target_ids)
    logger.info("Tìm thấy %d doc_id cần giữ.", len(target_ids))

    logger.info("Đọc parquet metadata: %s", metadata_path)
    df = pd.read_parquet(metadata_path)

    if "id" not in df.columns:
        raise KeyError("File metadata.parquet không có cột `id`.")

    df = df.copy()
    df["id"] = df["id"].astype(str)
    filtered_df = df[df["id"].isin(target_ids)].copy()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    filtered_df.to_parquet(output_path, index=False)
    logger.info("Đã ghi %d dòng ra %s", len(filtered_df), output_path)

    if "title" not in filtered_df.columns or "so_ky_hieu" not in filtered_df.columns:
        raise KeyError("File metadata.parquet phải có đủ cột `title` và `so_ky_hieu`.")

    titles_df = (
        filtered_df.loc[:, ["title", "so_ky_hieu"]]
        .dropna(subset=["title", "so_ky_hieu"])
        .drop_duplicates()
        .sort_values(by=["title", "so_ky_hieu"], kind="stable")
    )
    titles_output_path.parent.mkdir(parents=True, exist_ok=True)
    titles_payload = titles_df.to_dict(orient="records")
    with titles_output_path.open("w", encoding="utf-8") as f:
        json.dump(titles_payload, f, ensure_ascii=False, indent=2)
    logger.info("Đã ghi %d mục title/so_ky_hieu ra %s", len(titles_payload), titles_output_path)
    return len(filtered_df)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Lọc data/metadata.parquet theo các doc_id xuất hiện trong data_updated_with_ids.json."
    )
    parser.add_argument(
        "--json-path",
        type=Path,
        default=Path("data_updated_with_ids.json"),
        help="Đường dẫn tới file JSON đầu vào.",
    )
    parser.add_argument(
        "--metadata-path",
        type=Path,
        default=Path("data/metadata.parquet"),
        help="Đường dẫn tới file metadata parquet gốc.",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=Path("data/metadata_filtered.parquet"),
        help="Đường dẫn file parquet đầu ra.",
    )
    parser.add_argument(
        "--titles-output-path",
        type=Path,
        default=Path("data/docs_title.json"),
        help="Đường dẫn file JSON đầu ra chứa title và so_ky_hieu.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    filter_metadata(
        args.json_path,
        args.metadata_path,
        args.output_path,
        args.titles_output_path,
    )


if __name__ == "__main__":
    main()
