"""
Neo4j writer for segmentation — T1.5 (Người B)

Responsibility: take ParseResult (pure data) and persist to Neo4j.
This is the ONLY file in the segmentation module that imports the neo4j driver.

Interface contract with Người A (T1.4)
---------------------------------------
- Neo4j must be running with schema already applied (constraints + indexes).
- Assumes Document nodes already exist (doc_id must be valid).
- Uses MERGE so re-runs are idempotent.

Interface contract with cross_reference/ (Người B, Phase 2)
-------------------------------------------------------------
- After write(), Article nodes exist with uid = "doc_{id}_dieu_{index}"
- Clause nodes exist with uid = "doc_{id}_dieu_{dieu}_khoan_{k}"
- These UIDs are used in InternalRef / ExternalRef / ModificationRef.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .models import ParseResult, Segment, HierarchyType

if TYPE_CHECKING:
    from neo4j import Driver, Session

logger = logging.getLogger(__name__)

# Batch size from spec (T1.5)
DEFAULT_BATCH_SIZE = 5_000


class SegmentWriter:
    """
    Persists ParseResult(s) to Neo4j using MERGE operations.

    Usage
    -----
        from neo4j import GraphDatabase
        from segmentation.writer import SegmentWriter

        driver = GraphDatabase.driver(uri, auth=(user, password))
        writer = SegmentWriter(driver)

        counts = writer.write(result)
        # {"chapters": N, "articles": N, "clauses": N, "points": N, "errors": N}

        writer.close()
    """

    def __init__(self, driver: "Driver", batch_size: int = DEFAULT_BATCH_SIZE) -> None:
        self._driver = driver
        self._batch_size = batch_size

    def close(self) -> None:
        self._driver.close()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def write(self, result: ParseResult) -> dict[str, int]:
        """
        Write one document's segments to Neo4j.

        Returns summary dict: {chapters, articles, clauses, points, errors}

        Ingest order (matches spec T1.5):
          Document (must already exist) → Chapter → Article → Clause → Point
        """
        counts = {"chapters": 0, "articles": 0, "clauses": 0, "points": 0, "errors": 0}

        chapters  = [s for s in result.segments if s.hierarchy_type == HierarchyType.CHUONG]
        articles  = [s for s in result.segments if s.hierarchy_type == HierarchyType.DIEU]
        clauses   = [s for s in result.segments if s.hierarchy_type == HierarchyType.KHOAN]
        points    = [s for s in result.segments if s.hierarchy_type == HierarchyType.DIEM]

        with self._driver.session() as session:
            counts["chapters"] += self._write_batch(session, chapters, self._merge_chapter)
            counts["articles"] += self._write_batch(session, articles, self._merge_article)
            counts["clauses"]  += self._write_batch(session, clauses,  self._merge_clause)
            counts["points"]   += self._write_batch(session, points,   self._merge_point)

        return counts

    def write_batch(self, results: list[ParseResult]) -> dict[str, int]:
        """Write many documents. Returns aggregated counts."""
        totals = {"chapters": 0, "articles": 0, "clauses": 0, "points": 0, "errors": 0}
        for result in results:
            try:
                c = self.write(result)
                for k in totals:
                    totals[k] += c.get(k, 0)
            except Exception as exc:
                logger.error("Write failed for doc %s: %s", result.doc_id, exc)
                totals["errors"] += 1
        return totals

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _write_batch(self, session: "Session", segments: list[Segment], fn) -> int:
        count = 0
        for i in range(0, len(segments), self._batch_size):
            batch = segments[i : i + self._batch_size]
            for seg in batch:
                try:
                    session.execute_write(fn, seg)
                    count += 1
                except Exception as exc:
                    logger.warning("Failed to write segment %s: %s", seg.uid, exc)
        return count

    @staticmethod
    def _merge_chapter(tx, seg: Segment) -> None:
        """
        TODO (T1.5):
        Cypher template:
            MATCH (d:Document {id: $doc_id})
            MERGE (c:Chapter {doc_id: $doc_id, index: $index})
            SET c.roman  = $roman,
                c.title  = $title
            MERGE (d)-[:HAS_CHAPTER {order: $index}]->(c)
        """
        raise NotImplementedError("T1.5: implement _merge_chapter")

    @staticmethod
    def _merge_article(tx, seg: Segment) -> None:
        """
        TODO (T1.5):
        Cypher template:
            MATCH (d:Document {id: $doc_id})
            OPTIONAL MATCH (ch:Chapter {doc_id: $doc_id, index: $chapter_index})
            MERGE (a:Article {uid: $uid})
            SET a.index        = $index,
                a.title        = $title,
                a.text_content = $text_content,
                a.clean_text   = $clean_text,
                a.is_current   = true,
                a.effective_date = null
            // Link to chapter if exists, else directly to document
            WITH a, d, ch
            FOREACH (_ IN CASE WHEN ch IS NOT NULL THEN [1] ELSE [] END |
                MERGE (ch)-[:HAS_ARTICLE {order: $index}]->(a)
            )
            FOREACH (_ IN CASE WHEN ch IS NULL THEN [1] ELSE [] END |
                MERGE (d)-[:HAS_ARTICLE {order: $index}]->(a)
            )
        """
        raise NotImplementedError("T1.5: implement _merge_article")

    @staticmethod
    def _merge_clause(tx, seg: Segment) -> None:
        """
        TODO (T1.5):
        Cypher template:
            MATCH (a:Article {uid: $parent_uid})
            MERGE (c:Clause {uid: $uid})
            SET c.index        = $index,
                c.text_content = $text_content,
                c.clean_text   = $clean_text
            MERGE (a)-[:HAS_CLAUSE {order: $index}]->(c)
        """
        raise NotImplementedError("T1.5: implement _merge_clause")

    @staticmethod
    def _merge_point(tx, seg: Segment) -> None:
        """
        TODO (T1.5):
        Cypher template:
            MATCH (c:Clause {uid: $parent_uid})
            MERGE (p:Point {uid: $uid})
            SET p.letter       = $letter,
                p.text_content = $text_content,
                p.clean_text   = $clean_text
            MERGE (c)-[:HAS_POINT {order: $order}]->(p)
        """
        raise NotImplementedError("T1.5: implement _merge_point")
