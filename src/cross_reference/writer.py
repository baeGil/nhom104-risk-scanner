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
        TODO (Team B — T2.1):
        Implement Cypher MERGE for [:REFERENCES_INTERNAL].

        Template:
            MATCH (src:Article {uid: $source_uid})
            MATCH (tgt:Article {uid: $target_uid})
            MERGE (src)-[r:REFERENCES_INTERNAL]->(tgt)
            SET r.context_text = $context_text,
                r.confidence   = $confidence
        Note: target_article_uid must be pre-resolved (lookup by doc_id + index).
        """
        raise NotImplementedError("T2.1: implement _write_internal_ref Cypher")

    @staticmethod
    def _write_external_ref(tx, ref: ExternalRef) -> None:
        """
        TODO (Team B — T2.2):
        Implement Cypher MERGE for [:REFERENCES_EXTERNAL].

        Template:
            MATCH (src:Article {uid: $source_uid})
            MATCH (tgt:Document {id: $target_doc_id})
            MERGE (src)-[r:REFERENCES_EXTERNAL]->(tgt)
            SET r.context_text        = $context_text,
                r.raw_so_ky_hieu      = $raw_so_ky_hieu,
                r.match_method        = $match_method,
                r.confidence          = $confidence
        If target_article_uid is resolved, point to Article node instead.
        """
        raise NotImplementedError("T2.2: implement _write_external_ref Cypher")

    @staticmethod
    def _write_modification_ref(tx, ref: ModificationRef) -> None:
        """
        TODO (Team B — T2.3):
        Implement Cypher MERGE for [:MODIFIES].

        Template:
            MATCH (src:Article {uid: $source_article_uid})
            MATCH (tgt:Article {uid: $target_article_uid})
            MERGE (src)-[r:MODIFIES]->(tgt)
            SET r.action         = $action,
                r.target_clause  = $target_clause_index,
                r.target_point   = $target_point_label,
                r.new_text       = $new_text,
                r.context_text   = $context_text,
                r.confidence     = $confidence
        """
        raise NotImplementedError("T2.3: implement _write_modification_ref Cypher")
