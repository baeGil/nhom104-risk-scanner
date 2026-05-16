"""
T0.2 — Deduplicate Documents
==============================

Phát hiện và merge 1,273 bản ghi trùng lặp.
Tiêu chí trùng: cùng (normalized_so_ky_hieu, loai_van_ban).

Strategy:
  - Giữ bản ghi có nhiều content bytes nhất
  - Merge metadata: ưu tiên trường non-null
  - Log toàn bộ quyết định merge

Spec: data-cleanup-and-normalization
Task: T0.2
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def find_duplicates(records: list[dict]) -> dict[str, list[dict]]:
    """
    Nhóm các records có cùng (normalized_so_ky_hieu, loai_van_ban).

    Parameters
    ----------
    records : list[dict]
        Mỗi record phải có: normalized_so_ky_hieu, loai_van_ban, doc_id.

    Returns
    -------
    dict[str, list[dict]]
        {group_key: [record, ...]} — chỉ nhóm có ≥ 2 records (duplicates).
    """
    groups: dict[str, list[dict]] = {}

    for rec in records:
        skh  = rec.get("normalized_so_ky_hieu", "") or ""
        lvb  = rec.get("loai_van_ban", "") or ""
        key  = f"{skh}||{lvb}"

        groups.setdefault(key, []).append(rec)

    duplicates = {k: v for k, v in groups.items() if len(v) > 1}
    logger.info(
        "Found %d duplicate groups (%d total duplicate records)",
        len(duplicates),
        sum(len(v) for v in duplicates.values()),
    )
    return duplicates


def merge_records(group: list[dict]) -> tuple[dict, list[dict]]:
    """
    Merge một nhóm bản ghi trùng thành 1 bản ghi đại diện.

    Strategy:
      1. Chọn bản có content_bytes lớn nhất làm base.
      2. Với mỗi field khác: lấy giá trị non-null đầu tiên trong nhóm.

    Returns
    -------
    (merged_record, removed_records)
    """
    if not group:
        raise ValueError("group must not be empty")
    if len(group) == 1:
        return group[0], []

    # Chọn base record (nhiều content bytes nhất)
    base = max(group, key=lambda r: r.get("content_bytes", 0) or 0)
    removed = [r for r in group if r["doc_id"] != base["doc_id"]]

    merged = dict(base)  # copy

    # Merge metadata: điền vào các field None/empty từ các records khác
    for rec in removed:
        for field, value in rec.items():
            if field == "doc_id":
                continue  # giữ doc_id của base
            if not merged.get(field) and value:
                merged[field] = value
                logger.debug(
                    "Merged field '%s' from %s → %s",
                    field, rec["doc_id"], base["doc_id"],
                )

    return merged, removed


def deduplicate(records: list[dict]) -> tuple[list[dict], list[dict]]:
    """
    Khử trùng toàn bộ danh sách records.

    Parameters
    ----------
    records : list[dict]
        Phải có: doc_id, normalized_so_ky_hieu, loai_van_ban, content_bytes.

    Returns
    -------
    (deduped_records, merge_log)
      - deduped_records : list[dict] — không còn trùng
      - merge_log       : list[dict] — log decisions (kept, removed, reason)
    """
    groups   = find_duplicates(records)
    kept_ids = set()
    removed_ids: set[str] = set()
    merge_log: list[dict] = []

    for group_key, group in groups.items():
        merged, removed = merge_records(group)
        kept_ids.add(merged["doc_id"])
        for rec in removed:
            removed_ids.add(rec["doc_id"])
            merge_log.append({
                "action":      "merged",
                "kept_doc_id": merged["doc_id"],
                "removed_doc_id": rec["doc_id"],
                "group_key":   group_key,
                "reason":      "duplicate so_ky_hieu+loai_van_ban",
                "kept_content_bytes":    merged.get("content_bytes"),
                "removed_content_bytes": rec.get("content_bytes"),
            })

    # Kết quả: unique records (không bị remove) + merged bases
    result = [r for r in records if r["doc_id"] not in removed_ids]

    logger.info(
        "Deduplication done: %d → %d records (%d removed)",
        len(records), len(result), len(removed_ids),
    )
    return result, merge_log


def log_decisions(merge_log: list[dict], path: str | Path) -> None:
    """Ghi merge log ra JSON file."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(merge_log, f, ensure_ascii=False, indent=2)
    logger.info("Merge log saved: %d decisions → %s", len(merge_log), path)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main(
    metadata_path: str  = "data/metadata.parquet",
    lookup_path: str    = "data/output/so_ky_hieu_lookup.json",
    output_path: str    = "data/metadata_deduped.parquet",
    log_path: str       = "output/dedup_log.json",
) -> None:
    """
    T0.2 main: Đọc metadata đã có lookup, khử trùng, xuất kết quả.
    """
    import json
    import pandas as pd  # noqa: PLC0415

    logger.info("T0.2 — Loading metadata from %s", metadata_path)
    df = pd.read_parquet(metadata_path)

    # Load lookup để có normalized_so_ky_hieu
    with open(lookup_path, encoding="utf-8") as f:
        lookup = json.load(f)

    # Thêm cột normalized_so_ky_hieu ngược từ lookup (value → key)
    reverse_lookup = {v: k for k, v in lookup.items()}
    df["normalized_so_ky_hieu"] = df["id"].map(reverse_lookup)

    records = df.rename(columns={"id": "doc_id"}).to_dict("records")

    deduped_records, merge_log = deduplicate(records)

    # Ghi output
    deduped_df = pd.DataFrame(deduped_records).rename(columns={"doc_id": "id"})
    deduped_df.to_parquet(output_path, index=False)
    log_decisions(merge_log, log_path)

    logger.info("T0.2 done — output: %s", output_path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s — %(message)s")
    main()
