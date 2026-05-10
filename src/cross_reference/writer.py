"""
Neo4j writer for cross-reference relationships.

Responsibility: take ExtractionResult (pure data) and persist to Neo4j.
This is the ONLY file that imports neo4j driver — keeps extractor.py testable.

Interface contract with Team A
-------------------------------
- Neo4j URL, user, password passed via environment or config dict.
- Node UIDs follow schema from T1.4: Article.uid, Clause.uid, Point.uid.

Interface contract with Team C
-------------------------------
- Relationships written:
    [:REFERENCES_INTERNAL {context_text, confidence}]
    [:REFERENCES_EXTERNAL {context_text, raw_so_ky_hieu, match_method, confidence}]
    [:MODIFIES {action, target_clause, target_point, context_text, new_text, confidence}]
- All MERGE operations (idempotent — safe to re-run).
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .models import ExtractionResult, InternalRef, ExternalRef, ModificationRef

if TYPE_CHECKING:
    from neo4j import Driver

logger = logging.getLogger(__name__)


class CrossReferenceWriter:
    """
    Persists ExtractionResult to Neo4j.

    Usage
    -----
        from neo4j import GraphDatabase
        from cross_reference.writer import CrossReferenceWriter

        driver = GraphDatabase.driver(uri, auth=(user, password))
        writer = CrossReferenceWriter(driver)
        writer.write(result)
        writer.close()
    """

    def __init__(self, driver: "Driver") -> None:
        self._driver = driver

    def close(self) -> None:
        self._driver.close()

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def write(self, result: ExtractionResult) -> dict[str, int]:
        """
        Write all references in result to Neo4j.

        Returns a summary dict: {internal: N, external: N, modification: N, errors: N}
        """
        counts = {"internal": 0, "external": 0, "modification": 0, "errors": len(result.parse_errors)}
        with self._driver.session() as session:
            for ref in result.internal_refs:
                try:
                    session.execute_write(self._write_internal_ref, ref)
                    counts["internal"] += 1
                except Exception as exc:
                    logger.warning("Failed to write internal ref %s: %s", ref, exc)
                    counts["errors"] += 1

            for ref in result.external_refs:
                if ref.target_doc_id is None:
                    logger.debug("Skipping unresolved external ref %s", ref.raw_so_ky_hieu)
                    continue
                try:
                    session.execute_write(self._write_external_ref, ref)
                    counts["external"] += 1
                except Exception as exc:
                    logger.warning("Failed to write external ref %s: %s", ref, exc)
                    counts["errors"] += 1

            for ref in result.modification_refs:
                if ref.target_doc_id is None:
                    logger.debug("Skipping unresolved mod ref %s", ref.raw_target_so_ky_hieu)
                    continue
                try:
                    session.execute_write(self._write_modification_ref, ref)
                    counts["modification"] += 1
                except Exception as exc:
                    logger.warning("Failed to write mod ref %s: %s", ref, exc)
                    counts["errors"] += 1

        return counts

    # ------------------------------------------------------------------
    # Private Cypher helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _write_internal_ref(tx, ref: InternalRef) -> None:
        """
        Write [:REFERENCES_INTERNAL] relationship.
        """
        # 1. Resolve target Article UID within the same document
        query_resolve = """
        MATCH (d:Document {id: $doc_id})-[:HAS_ARTICLE]->(tgt:Article {index: $idx})
        RETURN tgt.uid as uid
        """
        result = tx.run(query_resolve, doc_id=ref.source_doc_id, idx=ref.target_article_index)
        record = result.single()
        if not record:
            logger.debug("Internal target Article %s not found in doc %s", ref.target_article_index, ref.source_doc_id)
            return

        target_uid = record["uid"]

        # 2. MERGE relationship
        query_merge = """
        MATCH (src:Article {uid: $source_uid})
        MATCH (tgt:Article {uid: $target_uid})
        MERGE (src)-[r:REFERENCES_INTERNAL]->(tgt)
        SET r.context_text = $context,
            r.confidence   = $conf
        """
        tx.run(query_merge, source_uid=ref.source_article_uid, target_uid=target_uid, context=ref.context_text, conf=ref.confidence)

    @staticmethod
    def _write_external_ref(tx, ref: ExternalRef) -> None:
        """
        Write [:REFERENCES_EXTERNAL] relationship.
        """
        # If target_article_index is present, try to link to Article instead of Document
        if ref.target_article_index:
            query_resolve = """
            MATCH (d:Document {id: $doc_id})-[:HAS_ARTICLE]->(tgt:Article {index: $idx})
            RETURN tgt.uid as uid
            """
            result = tx.run(query_resolve, doc_id=ref.target_doc_id, idx=ref.target_article_index)
            record = result.single()
            if record:
                target_uid = record["uid"]
                query_merge = """
                MATCH (src:Article {uid: $source_uid})
                MATCH (tgt:Article {uid: $target_uid})
                MERGE (src)-[r:REFERENCES_EXTERNAL]->(tgt)
                SET r.context_text = $context,
                    r.raw_so_ky_hieu = $skh,
                    r.confidence = $conf
                """
                tx.run(query_merge, source_uid=ref.source_article_uid, target_uid=target_uid, 
                       context=ref.context_text, skh=ref.raw_so_ky_hieu, conf=ref.confidence)
                return

        # Fallback: Link to Document
        query_doc = """
        MATCH (src:Article {uid: $source_uid})
        MATCH (tgt:Document {id: $target_doc_id})
        MERGE (src)-[r:REFERENCES_EXTERNAL]->(tgt)
        SET r.context_text = $context,
            r.raw_so_ky_hieu = $skh,
            r.match_method = $method,
            r.confidence = $conf
        """
        tx.run(query_doc, source_uid=ref.source_article_uid, target_doc_id=ref.target_doc_id,
               context=ref.context_text, skh=ref.raw_so_ky_hieu, method=ref.match_method, conf=ref.confidence)

    @staticmethod
    def _write_modification_ref(tx, ref: ModificationRef) -> None:
        """
        Write [:MODIFIES] relationship.
        """
        # 1. Resolve target node
        target_label = "Document"
        target_query_part = "{id: $target_doc_id}"
        params = {"source_uid": ref.source_article_uid, "target_doc_id": ref.target_doc_id, 
                  "action": ref.action, "context": ref.context_text, "conf": ref.confidence, "new_text": ref.new_text}

        if ref.target_article_index:
            query_resolve = """
            MATCH (d:Document {id: $doc_id})-[:HAS_ARTICLE]->(tgt:Article {index: $idx})
            RETURN tgt.uid as uid
            """
            res = tx.run(query_resolve, doc_id=ref.target_doc_id, idx=ref.target_article_index)
            rec = res.single()
            if rec:
                target_label = "Article"
                target_query_part = "{uid: $target_uid}"
                params["target_uid"] = rec["uid"]
            else:
                # If target article not found, link to Doc as fallback
                pass

        # 2. MERGE relationship
        query_merge = f"""
        MATCH (src:Article {{uid: $source_uid}})
        MATCH (tgt:{target_label} {target_query_part})
        MERGE (src)-[r:MODIFIES]->(tgt)
        SET r.action = $action,
            r.context_text = $context,
            r.confidence = $conf,
            r.new_text = $new_text
        """
        tx.run(query_merge, **params)
