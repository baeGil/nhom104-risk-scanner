import json
import os
import re
import logging
from typing import Optional
from neo4j import GraphDatabase
from src.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
from src.data_pipeline.normalize import normalize

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s — %(message)s")
logger = logging.getLogger(__name__)

# Path configuration
LOOKUP_PATH = "output/so_ky_hieu_lookup.json"
SHORT_TITLE_PATH = "data/short_title_mapping.json"
RELATIONS_PATH = "scratch/extracted_relations_batched.json"

def load_lookup_table():
    if os.path.exists(LOOKUP_PATH):
        with open(LOOKUP_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def load_short_title_map():
    if os.path.exists(SHORT_TITLE_PATH):
        with open(SHORT_TITLE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def resolve_uid(doc_id, article, clause, point):
    """Builds UID from components."""
    if not doc_id:
        return None
    uid = f"doc_{doc_id}"
    if article:
        # Clean article index
        article_idx = str(article).lower().replace('điều', '').strip()
        if article_idx:
            uid += f"_dieu_{article_idx}"
            if clause:
                clause_idx = str(clause).lower().replace('khoản', '').strip()
                if clause_idx:
                    uid += f"_khoan_{clause_idx}"
                    if point:
                        point_idx = str(point).lower().replace('điểm', '').strip()
                        if point_idx:
                            uid += f"_diem_{point_idx}"
    return uid

def extract_doc_id_from_uid(uid):
    match = re.match(r"doc_(\d+)", uid)
    if match:
        return match.group(1)
    return None

def resolve_target_doc_id(target_doc: str, lookup_table: dict, short_title_map: dict) -> Optional[str]:
    """Resolves target_doc string to a numeric doc_id."""
    if not target_doc or not isinstance(target_doc, str):
        return None
    
    # 1. Try direct normalization
    norm = normalize(target_doc)
    if norm and norm in lookup_table:
        return str(lookup_table[norm])
    
    # 2. Try short title lookup
    target_doc_clean = target_doc.strip()
    skh = short_title_map.get(target_doc_clean)
    if skh:
        norm = normalize(skh)
        if norm and norm in lookup_table:
            return str(lookup_table[norm])
            
    return None

def ingest_relations():
    lookup_table = load_lookup_table()
    short_title_map = load_short_title_map()
    
    if not os.path.exists(RELATIONS_PATH):
        logger.error(f"Relations file not found at {RELATIONS_PATH}")
        return
        
    with open(RELATIONS_PATH, "r", encoding="utf-8") as f:
        relations = json.load(f)

    logger.info(f"Loaded {len(relations)} extracted relations.")

    processed_relations = []
    fail_logs = []

    for rel in relations:
        source_uid = rel.get("source_uid")
        if not source_uid:
            continue

        source_doc_id = extract_doc_id_from_uid(source_uid)
        target_doc_raw = rel.get("target_doc")
        rel_type = rel.get("relationship_type", "").lower()

        # 1. Resolve target_doc_id
        target_doc_id = None
        if not target_doc_raw:
            # Skip if target_doc is empty or None
            continue

        if rel_type == "internal" or target_doc_raw.lower() in ["luật này", "nghị định này", "thông tư này", "quyết định này", "bộ luật này"]:
            target_doc_id = source_doc_id
        else:
            target_doc_id = resolve_target_doc_id(target_doc_raw, lookup_table, short_title_map)

        if not target_doc_id:
            fail_logs.append(target_doc_raw)
            continue

        # 2. Construct target_uid
        target_uid = resolve_uid(
            target_doc_id, 
            rel.get("target_article"), 
            rel.get("target_clause"), 
            rel.get("target_diem")
        )
        
        if not target_uid:
            continue
            
        # 2b. Prevent self-referencing
        if source_uid == target_uid:
            logger.debug(f"Skipping self-reference: {source_uid}")
            continue
            
        # 3. Determine Neo4j Relation Label
        neo4j_rel_type = "REFERENCES"
        if "modify" in rel_type:
            neo4j_rel_type = "MODIFIES"

        processed_relations.append({
            "source_uid": source_uid,
            "target_uid": target_uid,
            "rel_type": neo4j_rel_type,
            "raw_type": rel_type,
            "ref_type": rel_type if neo4j_rel_type == "REFERENCES" else None
        })

    # Log failures
    if fail_logs:
        logger.warning(f"Failed to resolve {len(fail_logs)} target docs. Examples: {list(set(fail_logs))[:10]}")

    if not processed_relations:
        logger.info("No valid relations to ingest.")
        return

    # 4. Ingest into Neo4j
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        with driver.session() as session:
            # Group by rel_type for batching
            by_type = {}
            for r in processed_relations:
                t = r["rel_type"]
                if t not in by_type:
                    by_type[t] = []
                by_type[t].append(r)

            for t, batch in by_type.items():
                query = f"""
                UNWIND $batch AS row
                MATCH (s {{uid: row.source_uid}})
                MATCH (t {{uid: row.target_uid}})
                MERGE (s)-[r:{t}]->(t)
                ON CREATE SET r.created_at = datetime()
                SET r.llm_extracted = true,
                    r.raw_type = row.raw_type,
                    r.ref_type = CASE
                        WHEN row.ref_type IS NOT NULL THEN row.ref_type
                        ELSE r.ref_type
                    END
                """
                result = session.run(query, batch=batch)
                summary = result.consume()
                logger.info(f"Ingested {len(batch)} relationships of type {t}. Created: {summary.counters.relationships_created}")

    finally:
        driver.close()

if __name__ == "__main__":
    ingest_relations()
