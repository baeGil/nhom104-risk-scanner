"""
T0.1 — Normalize so_ky_hieu
============================

Parse raw so_ky_hieu thành các thành phần chuẩn và
tạo normalized key dạng: {TYPE}-{ZERO_PADDED_NUM}-{YEAR}

Ví dụ:
  "Nghị định 46/2014/NĐ-CP"   →  "ND-046-2014"
  "59/2020/QH14"               →  "LT-059-2020"
  "12/2018/TT-BTC"             →  "TT-012-2018"
  "05/2016/TTLT-NHNN-BTC"     →  "TTLT-005-2016"

Spec: data-cleanup-and-normalization
Task: T0.1
"""
from __future__ import annotations

import re
import json
import logging
from pathlib import Path
from typing import Optional
import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Mapping loai_van_ban → normalized prefix
LOAI_VAN_BAN_PREFIX: dict[str, str] = {
    "Luật":                  "LT",
    "Bộ luật":               "BL",
    "Nghị định":             "ND",
    "Thông tư":              "TT",
    "Thông tư liên tịch":    "TTLT",
}

# Regex patterns (ordered: most specific → least specific)
_PATTERNS: list[tuple[str, re.Pattern]] = [
    # "05/2016/TTLT-NHNN-BTC" — Thông tư liên tịch
    ("TTLT", re.compile(
        r"(\d{1,3})/(\d{4})/TTLT-([\w-]+)",
        re.IGNORECASE,
    )),
    # "12/2018/TT-BTC" — Thông tư
    ("TT", re.compile(
        r"(\d{1,3})/(\d{4})/TT-([\w]+)",
        re.IGNORECASE,
    )),
    # "46/2014/NĐ-CP" — Nghị định
    ("ND", re.compile(
        r"(\d{1,3})/(\d{4})/N[ĐD]-CP",
        re.IGNORECASE,
    )),
    # "59/2020/QH14" — Luật/Bộ luật
    ("LT", re.compile(
        r"(\d{1,3})/(\d{4})/QH(\d+)",
        re.IGNORECASE,
    )),
    # Fallback: bare "số 12/2018" patterns
    ("UNKNOWN", re.compile(
        r"(?:số\s+)?(\d{1,3})/(\d{4})",
        re.IGNORECASE,
    )),
]


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def parse_so_ky_hieu(raw: str) -> dict:
    """
    Parse raw so_ky_hieu thành dict các thành phần.

    Returns
    -------
    dict với keys: type, number, year, issuer, raw, is_standard
    """
    if not raw or not isinstance(raw, str):
        return {"type": None, "number": None, "year": None,
                "issuer": None, "raw": raw, "is_standard": False}

    raw_stripped = raw.strip()

    # Phát hiện "Không số"
    if _is_khong_so(raw_stripped):
        logger.debug("Flagging 'Không số' document: %s", raw_stripped)
        return {"type": "UNKNOWN", "number": None, "year": None,
                "issuer": None, "raw": raw_stripped, "is_standard": False,
                "flag": "khong_so"}

    for type_prefix, pattern in _PATTERNS:
        m = pattern.search(raw_stripped)
        if m:
            number = m.group(1).zfill(3)
            year   = m.group(2)
            issuer = m.group(3) if len(m.groups()) >= 3 else None
            return {
                "type":        type_prefix,
                "number":      number,
                "year":        year,
                "issuer":      issuer,
                "raw":         raw_stripped,
                "is_standard": type_prefix != "UNKNOWN",
            }

    # Không match được pattern nào
    logger.warning("Could not parse so_ky_hieu: %s", raw_stripped)
    return {"type": None, "number": None, "year": None,
            "issuer": None, "raw": raw_stripped, "is_standard": False}


def normalize(raw: str, loai_van_ban: str = "") -> Optional[str]:
    """
    Chuyển raw so_ky_hieu thành normalized key.

    Parameters
    ----------
    raw : str
        Số ký hiệu thô từ database.
    loai_van_ban : str
        Loại văn bản ("Nghị định", "Thông tư", ...) để ưu tiên prefix.

    Returns
    -------
    str | None
        Normalized key, ví dụ "ND-046-2014". None nếu không parse được.

    Examples
    --------
    >>> normalize("46/2014/NĐ-CP", "Nghị định")
    'ND-046-2014'
    >>> normalize("59/2020/QH14", "Luật")
    'LT-059-2020'
    """
    parsed = parse_so_ky_hieu(raw)

    if not parsed["number"] or not parsed["year"]:
        return None

    # Nếu loai_van_ban cung cấp, ưu tiên prefix từ đó
    prefix = LOAI_VAN_BAN_PREFIX.get(str(loai_van_ban).strip() if loai_van_ban and not pd.isna(loai_van_ban) else "", parsed["type"] or "UNKNOWN")

    return f"{prefix}-{parsed['number']}-{parsed['year']}"


def build_lookup_table(records: list[dict]) -> dict[str, str]:
    """
    Tạo lookup table: normalized_so_ky_hieu → doc_id.

    Parameters
    ----------
    records : list of dict
        Mỗi record có keys: doc_id, so_ky_hieu, loai_van_ban

    Returns
    -------
    dict[str, str]
        {"ND-046-2014": "doc_id_xyz", ...}

    Notes
    -----
    - Nếu 2 records cùng normalized key (sau dedup T0.2): giữ record đầu tiên,
      log warning.
    - Records không normalize được: bỏ qua, log warning.
    """
    lookup: dict[str, str] = {}
    skipped = 0

    for rec in records:
        doc_id      = rec.get("doc_id") or rec.get("id")
        raw_skh     = rec.get("so_ky_hieu", "")
        loai_vb     = rec.get("loai_van_ban", "")

        if not doc_id:
            logger.warning("Record missing doc_id: %s", rec)
            skipped += 1
            continue

        normalized = normalize(raw_skh, loai_vb)
        if not normalized:
            logger.warning("Could not normalize: %s (doc_id=%s)", raw_skh, doc_id)
            skipped += 1
            continue

        if normalized in lookup:
            logger.warning(
                "Duplicate normalized key '%s': existing=%s, new=%s — keeping existing",
                normalized, lookup[normalized], doc_id,
            )
        else:
            lookup[normalized] = doc_id

    logger.info(
        "Built lookup table: %d entries, %d skipped", len(lookup), skipped
    )
    return lookup


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def save_lookup(lookup: dict[str, str], path: str | Path) -> None:
    """Ghi lookup table ra JSON file."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(lookup, f, ensure_ascii=False, indent=2, sort_keys=True)
    logger.info("Saved lookup table to %s (%d entries)", path, len(lookup))


def load_lookup(path: str | Path) -> dict[str, str]:
    """Đọc lookup table từ JSON file."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _is_khong_so(text: str) -> bool:
    """Phát hiện văn bản 'Không số' (không có số hiệu chính thức)."""
    return bool(re.search(r"không\s+số", text, re.IGNORECASE))


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main(
    metadata_path: str = "data/metadata.parquet",
    output_path: str = "output/so_ky_hieu_lookup.json",
) -> None:
    """
    T0.1 main: Đọc metadata.parquet, normalize, xuất lookup JSON.
    """
    import pandas as pd  # noqa: PLC0415

    logger.info("T0.1 — Loading metadata from %s", metadata_path)
    df = pd.read_parquet(metadata_path)

    logger.info("T0.1 — Building lookup table from %d records", len(df))
    records = df[["id", "so_ky_hieu", "loai_van_ban"]].rename(
        columns={"id": "doc_id"}
    ).to_dict("records")

    lookup = build_lookup_table(records)
    save_lookup(lookup, output_path)

    # Report
    total     = len(df)
    resolved  = len(lookup)
    skipped   = total - resolved
    logger.info(
        "T0.1 done — resolved: %d/%d (%.1f%%), skipped: %d",
        resolved, total, resolved / total * 100 if total else 0, skipped,
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s — %(message)s")
    main()
