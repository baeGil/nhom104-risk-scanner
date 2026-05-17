from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Optional

import pandas as pd
from neo4j import GraphDatabase

from src.config import NEO4J_PASSWORD, NEO4J_URI, NEO4J_USER
from src.data_pipeline.normalize import normalize

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s — %(message)s")
logger = logging.getLogger(__name__)

RELATIONS_JSON_PATH = Path("data/extracted_relations_batched.json")
LEGACY_RELATIONS_DIR = Path("data/relationships")
LOOKUP_PATH = Path("data/so_ky_hieu_lookup.json")
SHORT_TITLE_PATH = Path("data/short_title_mapping.json")
CHUNK_SIZE = 5000

INTERNAL_SELF_REF_TITLES = {
    "luật này",
    "nghị định này",
    "thông tư này",
    "quyết định này",
    "bộ luật này",
}

MODIFY_ACTION_MAP = {
    "sua_doi": "sua_doi",
    "thay_the": "sua_doi",
    "bo_sung": "bo_sung",
    "bai_bo": "bai_bo",
    "het_hieu_luc": "bai_bo",
}


def load_json(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON array in {path}")
    return data


def load_lookup_table() -> dict[str, str]:
    if LOOKUP_PATH.exists():
        with LOOKUP_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def load_short_title_map() -> dict[str, str]:
    if SHORT_TITLE_PATH.exists():
        with SHORT_TITLE_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def extract_doc_id_from_uid(uid: str | None) -> Optional[str]:
    if not uid:
        return None
    match = re.match(r"^doc_(\d+)", uid)
    return match.group(1) if match else None


def extract_article_index_from_uid(uid: str | None) -> Optional[str]:
    if not uid:
        return None
    match = re.match(r"^doc_\d+_dieu_([^_]+)", uid)
    return match.group(1) if match else None


def resolve_target_doc_id(target_doc: str, lookup_table: dict[str, str], short_title_map: dict[str, str]) -> Optional[str]:
    if not target_doc or not isinstance(target_doc, str):
        return None

    normalized = normalize(target_doc)
    if normalized in lookup_table:
        return str(lookup_table[normalized])

    target_doc_clean = target_doc.strip()
    short_title = short_title_map.get(target_doc_clean)
    if short_title:
        normalized_short_title = normalize(short_title)
        if normalized_short_title in lookup_table:
            return str(lookup_table[normalized_short_title])

    return None


def build_uid(doc_id: str, article: Any = None, clause: Any = None, point: Any = None) -> str:
    uid = f"doc_{doc_id}"
    if article not in (None, "", "null"):
        article_idx = str(article).strip().lower().replace("điều", "").strip()
        if article_idx:
            uid += f"_dieu_{article_idx}"
            if clause not in (None, "", "null"):
                clause_idx = str(clause).strip().lower().replace("khoản", "").strip()
                if clause_idx:
                    uid += f"_khoan_{clause_idx}"
                    if point not in (None, "", "null"):
                        point_idx = str(point).strip().lower().replace("điểm", "").strip()
                        if point_idx:
                            uid += f"_diem_{point_idx}"
    return uid


def normalize_modify_action(action: Optional[str]) -> Optional[str]:
    if action is None:
        return None
    return MODIFY_ACTION_MAP.get(str(action).strip().lower())


def load_legacy_relations() -> list[dict[str, Any]]:
    relations: list[dict[str, Any]] = []
    parquet_files = sorted(LEGACY_RELATIONS_DIR.glob("*_refs_part_*.parquet"))
    for file_path in parquet_files:
        df = pd.read_parquet(file_path)
        if not df.empty:
            df = df.where(pd.notnull(df), None)
            relations.extend(df.to_dict("records"))
    return relations


def prepare_relation_rows(relations: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    lookup_table = load_lookup_table()
    short_title_map = load_short_title_map()
    prepared: list[dict[str, Any]] = []
    skipped_targets: list[str] = []

    for rel in relations:
        source_uid = rel.get("source_uid")
        if not source_uid:
            continue

        target_doc_raw = rel.get("target_doc")
        if not target_doc_raw:
            continue

        rel_type = str(rel.get("relationship_type", "")).strip().lower()
        source_doc_id = extract_doc_id_from_uid(source_uid)
        if not source_doc_id:
            continue

        is_internal = rel_type == "internal" or str(target_doc_raw).strip().lower() in INTERNAL_SELF_REF_TITLES
        target_doc_id = source_doc_id if is_internal else resolve_target_doc_id(str(target_doc_raw), lookup_table, short_title_map)
        if not target_doc_id:
            skipped_targets.append(str(target_doc_raw))
            continue

        target_article = rel.get("target_article")
        target_clause = rel.get("target_clause")
        target_point = rel.get("target_diem")
        if target_article in (None, "", "null") and (target_clause not in (None, "", "null") or target_point not in (None, "", "null")):
            target_article = extract_article_index_from_uid(source_uid)

        target_uid = build_uid(target_doc_id, target_article, target_clause, target_point)
        if source_uid == target_uid:
            continue

        neo4j_rel_type = "MODIFIES" if "modify" in rel_type else "REFERENCES"
        target_label = "Article" if target_article not in (None, "", "null") else "Document"
        target_key_value = target_uid if target_label == "Article" else str(target_doc_id)

        prepared.append(
            {
                "source_uid": source_uid,
                "target_label": target_label,
                "target_key_value": target_key_value,
                "rel_type": neo4j_rel_type,
                "raw_type": rel_type,
                "ref_type": rel_type if neo4j_rel_type == "REFERENCES" else None,
                "target_doc_raw": target_doc_raw,
                "target_doc_id": str(target_doc_id),
                "target_article": target_article,
                "target_clause": target_clause,
                "target_point": target_point,
                "action": normalize_modify_action(rel.get("modify_action")) or ("sua_doi" if neo4j_rel_type == "MODIFIES" else None),
                "raw_action": rel.get("modify_action"),
            }
        )

    return prepared, skipped_targets


def ingest_rows(tx, batch: list[dict[str, Any]]) -> None:
    by_type: dict[str, list[dict[str, Any]]] = {}
    for row in batch:
        by_type.setdefault(row["rel_type"], []).append(row)

    for rel_type, rows in by_type.items():
        by_target_label: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            by_target_label.setdefault(row["target_label"], []).append(row)

        for target_label, target_rows in by_target_label.items():
            if rel_type == "REFERENCES":
                if target_label == "Article":
                    query = """
                    UNWIND $batch AS row
                    MATCH (src:Article {uid: row.source_uid})
                    MATCH (tgt:Article {uid: row.target_key_value})
                    MERGE (src)-[r:REFERENCES]->(tgt)
                    ON CREATE SET r.created_at = datetime()
                    SET r.llm_extracted = true,
                        r.raw_type = row.raw_type,
                        r.ref_type = row.ref_type,
                        r.target_so_ky_hieu = row.target_doc_raw,
                        r.target_article = row.target_article,
                        r.target_clause = row.target_clause,
                        r.target_point = row.target_point
                    """
                else:
                    query = """
                    UNWIND $batch AS row
                    MATCH (src:Article {uid: row.source_uid})
                    MATCH (tgt:Document {id: row.target_key_value})
                    MERGE (src)-[r:REFERENCES]->(tgt)
                    ON CREATE SET r.created_at = datetime()
                    SET r.llm_extracted = true,
                        r.raw_type = row.raw_type,
                        r.ref_type = row.ref_type,
                        r.target_so_ky_hieu = row.target_doc_raw,
                        r.target_article = row.target_article,
                        r.target_clause = row.target_clause,
                        r.target_point = row.target_point
                    """
            else:
                if target_label == "Article":
                    query = """
                    UNWIND $batch AS row
                    MATCH (src:Article {uid: row.source_uid})
                    MATCH (tgt:Article {uid: row.target_key_value})
                    MERGE (src)-[r:MODIFIES]->(tgt)
                    ON CREATE SET r.created_at = datetime()
                    SET r.llm_extracted = true,
                        r.raw_type = row.raw_type,
                        r.action = row.action,
                        r.raw_action = row.raw_action,
                        r.target_clause = row.target_clause,
                        r.target_point = row.target_point,
                        r.target_so_ky_hieu = row.target_doc_raw
                    """
                else:
                    query = """
                    UNWIND $batch AS row
                    MATCH (src:Article {uid: row.source_uid})
                    MATCH (tgt:Document {id: row.target_key_value})
                    MERGE (src)-[r:MODIFIES]->(tgt)
                    ON CREATE SET r.created_at = datetime()
                    SET r.llm_extracted = true,
                        r.raw_type = row.raw_type,
                        r.action = row.action,
                        r.raw_action = row.raw_action,
                        r.target_clause = row.target_clause,
                        r.target_point = row.target_point,
                        r.target_so_ky_hieu = row.target_doc_raw
                    """

            tx.run(query, batch=target_rows)


def ingest_relations() -> None:
    if RELATIONS_JSON_PATH.exists():
        logger.info("Loading relations from %s", RELATIONS_JSON_PATH)
        relations = load_json(RELATIONS_JSON_PATH)
    else:
        logger.info("JSON file not found, falling back to legacy parquet relations.")
        relations = load_legacy_relations()

    logger.info("Loaded %d raw relations.", len(relations))
    prepared, skipped_targets = prepare_relation_rows(relations)
    logger.info("Prepared %d relations for Neo4j.", len(prepared))

    if skipped_targets:
        examples = sorted(set(skipped_targets))[:10]
        logger.warning("Skipped %d unresolved target docs. Examples: %s", len(skipped_targets), examples)

    if not prepared:
        logger.info("No valid relations to ingest.")
        return

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        with driver.session() as session:
            for i in range(0, len(prepared), CHUNK_SIZE):
                batch = prepared[i : i + CHUNK_SIZE]
                session.execute_write(ingest_rows, batch)
                logger.info("Ingested %d/%d relations.", min(i + CHUNK_SIZE, len(prepared)), len(prepared))
    finally:
        driver.close()

    logger.info("=== HOAN TAT NAP QUAN HE ===")


if __name__ == "__main__":
    ingest_relations()
