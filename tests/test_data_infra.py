#!/usr/bin/env python3
"""
Test Suite — Người A: Data & Infrastructure
============================================
Chạy lệnh: python tests/test_data_infra.py

Kiểm tra đầy đủ:
  ✅ T0.1 - Normalize so_ky_hieu
  ✅ T0.2 - Deduplicate
  ✅ T0.3 - Crawler (kiểm tra file output)
  ✅ T0.4 - HTML Cleaner
  ✅ T0.5 - Fuzzy Lookup
  ✅ T1.4 - Neo4j Schema (constraints + indexes)
  ✅ T1.7 - Neo4j Connection
  ✅ T6.2 - Embedding Service (nếu đang chạy)
"""

import json
import os
import sys
from pathlib import Path

# Thêm root vào sys.path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

os.chdir(ROOT)  # đảm bảo relative paths hoạt động

PASS = "✅"
FAIL = "❌"
SKIP = "⚠️ "

results = []


def test(name, fn):
    """Chạy một test case và ghi lại kết quả."""
    try:
        fn()
        results.append((PASS, name))
        print(f"  {PASS}  {name}")
    except AssertionError as e:
        results.append((FAIL, name, str(e)))
        print(f"  {FAIL}  {name}: {e}")
    except Exception as e:
        results.append((FAIL, name, str(e)))
        print(f"  {FAIL}  {name}: {type(e).__name__}: {e}")


def skip(name, reason=""):
    results.append((SKIP, name, reason))
    print(f"  {SKIP} {name} [SKIP] {reason}")


# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  NGƯỜI A — DATA & INFRA TEST SUITE")
print("=" * 60)

# ─────────────────────────────────────────────────────────────────────────────
print("\n[T0.1] Normalize so_ky_hieu")

def t01_parse_nd():
    from src.data_pipeline.normalize import normalize
    result = normalize("46/2014/NĐ-CP", "Nghị định")
    assert result == "ND-046-2014", f"Expected ND-046-2014, got {result}"
test("T0.1 - Parse Nghị định → ND-046-2014", t01_parse_nd)

def t01_parse_luat():
    from src.data_pipeline.normalize import normalize
    result = normalize("59/2020/QH14", "Luật")
    assert result == "LT-059-2020", f"Expected LT-059-2020, got {result}"
test("T0.1 - Parse Luật → LT-059-2020", t01_parse_luat)

def t01_parse_thongtu():
    from src.data_pipeline.normalize import normalize
    result = normalize("12/2018/TT-BTC", "Thông tư")
    assert result == "TT-012-2018", f"Expected TT-012-2018, got {result}"
test("T0.1 - Parse Thông tư → TT-012-2018", t01_parse_thongtu)

def t01_lookup_file():
    p = Path("output/so_ky_hieu_lookup.json")
    assert p.exists(), f"File không tồn tại: {p}"
    with open(p) as f:
        data = json.load(f)
    assert len(data) >= 2, f"Lookup table quá ít entries: {len(data)}"
test("T0.1 - Lookup JSON file tồn tại và có dữ liệu", t01_lookup_file)

# ─────────────────────────────────────────────────────────────────────────────
print("\n[T0.2] Deduplication")

def t02_output_file():
    p = Path("data/metadata_deduped.parquet")
    assert p.exists(), f"File không tồn tại: {p}"
    import pandas as pd
    df = pd.read_parquet(p)
    assert len(df) > 0, "metadata_deduped.parquet trống!"
test("T0.2 - metadata_deduped.parquet tồn tại và có dữ liệu", t02_output_file)

def t02_log_file():
    p = Path("output/dedup_log.json")
    assert p.exists(), f"File không tồn tại: {p}"
test("T0.2 - dedup_log.json tồn tại", t02_log_file)

def t02_no_duplicates():
    import pandas as pd
    from src.data_pipeline.normalize import normalize
    df = pd.read_parquet("data/metadata_deduped.parquet")
    keys = df.apply(lambda r: normalize(r.get("so_ky_hieu",""), r.get("loai_van_ban","")), axis=1)
    keys_valid = keys.dropna()
    assert len(keys_valid) == keys_valid.nunique(), \
        f"Vẫn còn {len(keys_valid) - keys_valid.nunique()} duplicates!"
test("T0.2 - Không còn duplicates trong output", t02_no_duplicates)

# ─────────────────────────────────────────────────────────────────────────────
print("\n[T0.3] Crawler")

def t03_enriched_file():
    p = Path("data/content_enriched.parquet")
    assert p.exists(), f"File không tồn tại: {p}"
    import pandas as pd
    df = pd.read_parquet(p)
    assert len(df) > 0, "content_enriched.parquet trống!"
test("T0.3 - content_enriched.parquet tồn tại và có nội dung", t03_enriched_file)

def t03_crawled_content_valid():
    import pandas as pd
    import re
    df = pd.read_parquet("data/content_enriched.parquet")
    # Kiểm tra ít nhất 1 doc có HTML chứa từ khóa pháp luật
    has_content = df["raw_html"].dropna()
    assert len(has_content) > 0, "Không có HTML nào được crawl!"
    sample = has_content.iloc[0]
    # Nội dung phải dài ít nhất 500 ký tự
    assert len(sample) > 500, f"HTML quá ngắn: {len(sample)} ký tự"
test("T0.3 - Nội dung crawl hợp lệ (>500 chars)", t03_crawled_content_valid)

def t03_checkpoint_file():
    p = Path("output/crawl_checkpoint.json")
    assert p.exists(), f"File không tồn tại: {p}"
    with open(p) as f:
        data = json.load(f)
    assert "done" in data, "Checkpoint thiếu key 'done'"
test("T0.3 - Checkpoint file hợp lệ", t03_checkpoint_file)

# ─────────────────────────────────────────────────────────────────────────────
print("\n[T0.4] HTML Cleaner")

def t04_clean_file():
    p = Path("data/content_clean.parquet")
    assert p.exists(), f"File không tồn tại: {p}"
    import pandas as pd
    df = pd.read_parquet(p)
    assert len(df) > 0, "content_clean.parquet trống!"
    assert "clean_html" in df.columns, "Thiếu cột 'clean_html'"
test("T0.4 - content_clean.parquet có cột clean_html", t04_clean_file)

def t04_no_junk_tags():
    import pandas as pd
    df = pd.read_parquet("data/content_clean.parquet")
    sample = df["clean_html"].dropna().iloc[0] if len(df) > 0 else ""
    # Sau khi clean, không được có các thẻ rác phổ biến
    junk_tags = ["<font", "<dir", "<center"]
    for tag in junk_tags:
        assert tag not in sample.lower(), f"Vẫn còn thẻ rác: {tag}"
test("T0.4 - clean_html không còn thẻ rác (<font, <dir)", t04_no_junk_tags)

# ─────────────────────────────────────────────────────────────────────────────
print("\n[T0.5] Fuzzy Lookup")

def t05_lookup_exact():
    from src.data_pipeline.lookup import SoKyHieuResolver
    import json
    with open("output/so_ky_hieu_lookup.json") as f:
        lookup = json.load(f)
    resolver = SoKyHieuResolver(lookup)
    result = resolver.resolve("ND-046-2014")
    assert result is not None, "Không tìm thấy ND-046-2014"
test("T0.5 - Lookup khớp chính xác (ND-046-2014)", t05_lookup_exact)

# ─────────────────────────────────────────────────────────────────────────────
print("\n[T1.4] Neo4j Schema")

def t14_neo4j_constraints():
    from neo4j import GraphDatabase
    from dotenv import load_dotenv
    load_dotenv()
    uri  = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    pwd  = os.getenv("NEO4J_PASSWORD", "password")
    
    driver = GraphDatabase.driver(uri, auth=(user, pwd))
    with driver.session() as s:
        result = s.run("SHOW CONSTRAINTS")
        constraints = [r["name"] for r in result]
    driver.close()
    assert len(constraints) >= 4, f"Chỉ có {len(constraints)} constraints (cần ≥4)"
test("T1.4 - Neo4j có đủ constraints (≥4)", t14_neo4j_constraints)

def t14_neo4j_indexes():
    from neo4j import GraphDatabase
    from dotenv import load_dotenv
    load_dotenv()
    uri  = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    pwd  = os.getenv("NEO4J_PASSWORD", "password")
    
    driver = GraphDatabase.driver(uri, auth=(user, pwd))
    with driver.session() as s:
        result = s.run("SHOW INDEXES")
        indexes = [r["name"] for r in result]
    driver.close()
    assert len(indexes) >= 5, f"Chỉ có {len(indexes)} indexes (cần ≥5)"
test("T1.4 - Neo4j có đủ indexes (≥5)", t14_neo4j_indexes)

# ─────────────────────────────────────────────────────────────────────────────
print("\n[T1.7] Neo4j Connection")

def t17_connect():
    from neo4j import GraphDatabase
    from dotenv import load_dotenv
    load_dotenv()
    uri  = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    pwd  = os.getenv("NEO4J_PASSWORD", "password")
    
    driver = GraphDatabase.driver(uri, auth=(user, pwd))
    with driver.session() as s:
        result = s.run("RETURN 1 AS ping")
        assert result.single()["ping"] == 1
    driver.close()
test("T1.7 - Kết nối Neo4j thành công", t17_connect)

# ─────────────────────────────────────────────────────────────────────────────
print("\n[T6.2] Embedding Service")

def t62_health_check():
    import requests as req
    # Port 8080 bị chiếm, Embedding Service chạy trên 8001
    for port in [8001, 8000, 8080]:
        try:
            resp = req.get(f"http://localhost:{port}/health", timeout=2)
            if resp.status_code == 200 and resp.json().get("status") == "ok":
                return  # found it
        except Exception:
            continue
    raise AssertionError("Embedding Service chưa chạy — hãy start: uvicorn app:app --port 8001 (trong infra/embedding_service/)")
test("T6.2 - Embedding Service /health", t62_health_check)

# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
passed = sum(1 for r in results if r[0] == PASS)
failed = sum(1 for r in results if r[0] == FAIL)
skipped = sum(1 for r in results if r[0] == SKIP)
total = len(results)

print(f"\n  KẾT QUẢ: {passed}/{total} PASSED   |   {failed} FAILED   |   {skipped} SKIPPED")
print("=" * 60)

if failed > 0:
    print("\n  Chi tiết lỗi:")
    for r in results:
        if r[0] == FAIL:
            print(f"    {FAIL} {r[1]}")
            print(f"       → {r[2]}")

sys.exit(0 if failed == 0 else 1)
