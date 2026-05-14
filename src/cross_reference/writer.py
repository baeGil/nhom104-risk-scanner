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
from typing import TYPE_CHECKING, Optional

from .models import ExtractionResult, InternalRef, ExternalRef, ModificationRef

if TYPE_CHECKING:
    from neo4j import Driver

logger = logging.getLogger(__name__)


class CrossReferenceWriter:
    """
    Persists ExtractionResult to Neo4j with Stubbing support.
    """

    def __init__(self, driver: "Driver") -> None:
        self._driver = driver
        self.stub_counts = {"document": 0, "article": 0}

    def close(self) -> None:
        self._driver.close()

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def write(self, result: ExtractionResult) -> dict[str, int]:
        """
        Write all references in result to Neo4j.
        """
        counts = {"internal": 0, "external": 0, "modification": 0, "errors": len(result.parse_errors)}
        self.stub_counts = {"document": 0, "article": 0}

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
                    continue
                try:
                    session.execute_write(self._write_external_ref, ref)
                    counts["external"] += 1
                except Exception as exc:
                    logger.warning("Failed to write external ref %s: %s", ref, exc)
                    counts["errors"] += 1

            for ref in result.modification_refs:
                if ref.target_doc_id is None:
                    continue
                try:
                    session.execute_write(self._write_modification_ref, ref)
                    counts["modification"] += 1
                except Exception as exc:
                    logger.warning("Failed to write mod ref %s: %s", ref, exc)
                    counts["errors"] += 1

        # Trả về cả counts và stub counts
        final_summary = {**counts, "stub_doc": self.stub_counts["document"], "stub_art": self.stub_counts["article"]}
        return final_summary

    # ------------------------------------------------------------------
    # Private Cypher helpers
    # ------------------------------------------------------------------

    def _ensure_doc_stub(self, tx, doc_id: str) -> None:
        """Đảm bảo node Document tồn tại (tạo stub nếu chưa có)."""
        query = """
        MERGE (d:Document {id: $id})
        ON CREATE SET d.is_stub = true, d.title = 'Stub Document'
        RETURN id(d) as node_id, d.is_stub as is_stub
        """
        result = tx.run(query, id=str(doc_id))
        record = result.single()
        if record and record["is_stub"]:
            self.stub_counts["document"] += 1

    def _ensure_article_stub(self, tx, doc_id: str, article_index: str) -> str:
        """Đảm bảo node Article tồn tại (tạo stub nếu chưa có) và trả về UID."""
        # 1. Đảm bảo Doc cha tồn tại
        self._ensure_doc_stub(tx, doc_id)

        # 2. Tạo UID theo quy ước doc_{id}_dieu_{n}
        uid = f"doc_{doc_id}_dieu_{article_index}"

        # 3. MERGE Article
        query = """
        MATCH (d:Document {id: $doc_id})
        MERGE (a:Article {uid: $uid})
        ON CREATE SET 
            a.index = $idx,
            a.is_stub = true,
            a.title = 'Stub Article'
        MERGE (d)-[:HAS_ARTICLE]->(a)
        RETURN a.is_stub as is_stub
        """
        result = tx.run(query, doc_id=str(doc_id), uid=uid, idx=article_index)
        record = result.single()
        if record and record["is_stub"]:
            self.stub_counts["article"] += 1
        
        return uid

    def _write_internal_ref(self, tx, ref: InternalRef) -> None:
        """Write [:REFERENCES_INTERNAL] relationship."""
        # Nội bộ thì không cần stub Document vì source đã tồn tại, 
        # nhưng đích Article có thể chưa có (ví dụ dẫn chiếu đến Điều chưa được bóc tách).
        target_uid = self._ensure_article_stub(tx, str(ref.source_doc_id), str(ref.target_article_index))

        query_merge = """
        MATCH (src:Article {uid: $source_uid})
        MATCH (tgt:Article {uid: $target_uid})
        MERGE (src)-[r:REFERENCES_INTERNAL]->(tgt)
        SET r.context_text = $context,
            r.confidence   = $conf
        """
        tx.run(query_merge, source_uid=ref.source_article_uid, target_uid=target_uid, 
               context=ref.context_text, conf=ref.confidence)

    def _write_external_ref(self, tx, ref: ExternalRef) -> None:
        """Write [:REFERENCES_EXTERNAL] relationship."""
        doc_id = str(ref.target_doc_id)
        
        if ref.target_article_index:
            # Tạo stub Article (bao gồm cả Doc cha)
            target_uid = self._ensure_article_stub(tx, doc_id, str(ref.target_article_index))
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
        else:
            # Chỉ tạo stub Document
            self._ensure_doc_stub(tx, doc_id)
            query_doc = """
            MATCH (src:Article {uid: $source_uid})
            MATCH (tgt:Document {id: $target_doc_id})
            MERGE (src)-[r:REFERENCES_EXTERNAL]->(tgt)
            SET r.context_text = $context,
                r.raw_so_ky_hieu = $skh,
                r.match_method = $method,
                r.confidence = $conf
            """
            tx.run(query_doc, source_uid=ref.source_article_uid, target_doc_id=doc_id,
                   context=ref.context_text, skh=ref.raw_so_ky_hieu, 
                   method=ref.match_method, conf=ref.confidence)

    def _write_modification_ref(self, tx, ref: ModificationRef) -> None:
        """Write [:MODIFIES] relationship."""
        doc_id = str(ref.target_doc_id)
        
        target_label = "Document"
        target_key_name = "id"
        target_key_val = doc_id

        if ref.target_article_index:
            target_uid = self._ensure_article_stub(tx, doc_id, str(ref.target_article_index))
            target_label = "Article"
            target_key_name = "uid"
            target_key_val = target_uid
        else:
            self._ensure_doc_stub(tx, doc_id)

        query_merge = f"""
        MATCH (src:Article {{uid: $source_uid}})
        MATCH (tgt:{target_label} {{{target_key_name}: $target_val}})
        MERGE (src)-[r:MODIFIES]->(tgt)
        SET r.action = $action,
            r.context_text = $context,
            r.confidence = $conf,
            r.new_text = $new_text
        """
        tx.run(query_merge, source_uid=ref.source_article_uid, target_val=target_key_val,
               action=ref.action, context=ref.context_text, conf=ref.confidence, new_text=ref.new_text)
