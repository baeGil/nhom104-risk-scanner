"""
data_pipeline — Người A: Data & Infrastructure
===============================================

Package structure:
  normalize.py      T0.1  — Chuẩn hóa so_ky_hieu
  lookup.py         T0.5  — Fuzzy lookup table
  dedup.py          T0.2  — Khử trùng documents
  crawler.py        T0.3  — Crawl missing content
  html_cleaner.py   T0.4  — Clean HTML pipeline
  neo4j_ingest.py   T1.7  — Ingest relationships vào Neo4j
  pipeline.py       T6.3  — Orchestration runner

Interface outputs (cho Người B):
  output/so_ky_hieu_lookup.json
  output/neo4j_schema.cypher
  data/clean_html/   (parquet với cột clean_html)
"""

__version__ = "0.1.0"
__author__ = "Người A"
