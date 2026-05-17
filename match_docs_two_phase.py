import json
import re

import pandas as pd

from match_docs import normalize_so_hieu


def normalize_text(text: str) -> str:
    """Chuẩn hóa title để match ổn định hơn."""
    text = str(text or "").strip().lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[\"'`´“”‘’]", "", text)
    text = re.sub(r"[.,;:!?(){}\[\]]", "", text)
    return text


def strip_trailing_year(text: str) -> str:
    """Bỏ năm ở cuối title nếu có, ví dụ '... 2020' -> '...'."""
    text = str(text or "").strip()
    return re.sub(r"\s+(?:19|20)\d{2}$", "", text).strip()


def title_aliases(title: str, loai_van_ban: str | None = None) -> list[str]:
    """Sinh các biến thể title để match tốt hơn."""
    aliases = []
    raw = str(title or "").strip()
    if not raw:
        return aliases

    base = normalize_text(raw)
    core = normalize_text(strip_trailing_year(raw))

    def add(value: str) -> None:
        value = normalize_text(value)
        if value and value not in aliases:
            aliases.append(value)

    add(base)
    add(core)

    # Bỏ các tiền tố loại văn bản để khớp cả tên rút gọn và tên đầy đủ.
    for variant in (base, core):
        if variant.startswith("luat "):
            add(variant[len("luat "):])
        if variant.startswith("bo luat "):
            add(variant[len("bo luat "):])

    # Thêm tiền tố theo loại nếu schema chỉ ghi phần tên rút gọn.
    loai_norm = normalize_text(loai_van_ban or "")
    if loai_norm == "luat":
        add(f"luat {core}")
    elif loai_norm == "bo luat":
        add(f"bo luat {core}")

    return aliases


def build_lookup_tables(df: pd.DataFrame) -> tuple[dict[str, str], dict[str, str]]:
    """Tạo 2 bảng tra cứu: theo số hiệu và theo title."""
    lookup_by_so_hieu: dict[str, str] = {}
    lookup_by_title: dict[str, str] = {}

    df = df.copy()
    df["id"] = df["id"].astype(str)

    for _, row in df.iterrows():
        doc_id = str(row.get("id", "")).strip()
        if not doc_id:
            continue

        so_hieu_raw = row.get("so_ky_hieu", "")
        title_raw = row.get("title", "")
        loai_raw = row.get("loai_van_ban", "")

        if pd.notna(so_hieu_raw) and str(so_hieu_raw).strip().lower() != "nan":
            skh_clean = normalize_so_hieu(so_hieu_raw)
            if skh_clean:
                lookup_by_so_hieu[skh_clean] = doc_id

        if pd.notna(title_raw) and str(title_raw).strip().lower() != "nan":
            for alias in title_aliases(title_raw, loai_raw if pd.notna(loai_raw) else None):
                lookup_by_title[alias] = doc_id

    return lookup_by_so_hieu, lookup_by_title


def extract_title_candidates(doc: dict) -> list[str]:
    """Lấy các biến thể title có thể dùng để match."""
    candidates = []
    loai_van_ban = doc.get("loai_van_ban")
    for key in ("title", "ten"):
        value = doc.get(key)
        if value and str(value).strip().lower() != "nan":
            candidates.extend(title_aliases(str(value).strip(), loai_van_ban))
    return candidates


def extract_so_hieu_candidates(doc: dict) -> list[str]:
    """Lấy các biến thể số hiệu có thể dùng để match."""
    candidates = []
    for key in ("so_ky_hieu", "so_hieu"):
        value = doc.get(key)
        if value and str(value).strip().lower() != "nan":
            candidates.append(str(value).strip())
    return candidates


def main() -> None:
    metadata_path = "data/metadata.parquet"
    schema_path = "chu_de_lao_dong_schema.json"
    output_path = "chu_de_lao_dong_schema_with_ids.json"

    print(f"Đang đọc metadata từ {metadata_path}...")
    df = pd.read_parquet(metadata_path)

    if "id" not in df.columns:
        raise KeyError("metadata.parquet không có cột `id`.")
    if "so_ky_hieu" not in df.columns:
        raise KeyError("metadata.parquet không có cột `so_ky_hieu`.")
    if "title" not in df.columns:
        raise KeyError("metadata.parquet không có cột `title`.")

    lookup_by_so_hieu, lookup_by_title = build_lookup_tables(df)
    print(
        f"Đã tạo lookup: {len(lookup_by_so_hieu)} so_ky_hieu, {len(lookup_by_title)} title."
    )

    print(f"Đang đọc schema từ {schema_path}...")
    with open(schema_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    matched_by_so_hieu = 0
    matched_by_title = 0
    total_count = 0

    for item in data:
        total_count += 1

        doc_id = None
        matched_method = None

        for so_hieu_raw in extract_so_hieu_candidates(item):
            so_hieu_clean = normalize_so_hieu(so_hieu_raw)
            doc_id = lookup_by_so_hieu.get(so_hieu_clean)
            if doc_id:
                matched_method = "so_ky_hieu"
                matched_by_so_hieu += 1
                break

        if not doc_id:
            for title_raw in extract_title_candidates(item):
                title_clean = normalize_text(title_raw)
                doc_id = lookup_by_title.get(title_clean)
                if doc_id:
                    matched_method = "title"
                    matched_by_title += 1
                    break

        if doc_id:
            item["doc_id"] = doc_id
            item["match_method"] = matched_method
        else:
            print(
                f"CẢNH BÁO: Không tìm thấy doc_id cho '{item.get('title')}' / '{item.get('so_ky_hieu')}'"
            )

    print(
        f"Tổng kết: match {matched_by_so_hieu + matched_by_title}/{total_count} văn bản "
        f"(theo so_ky_hieu: {matched_by_so_hieu}, theo title: {matched_by_title})."
    )

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Đã lưu kết quả ra file: {output_path}")


if __name__ == "__main__":
    main()
