"""
Neo4j writer for EffectiveArticle nodes — T3.3 (Người B)

Only file in effective_text/ that imports neo4j driver.
Uses MERGE for idempotency.

Interface contract with Người C (T4.3, T5.2)
---------------------------------------------
After write_all() completes, Người C can query:

  # Get current effective text for an article:
  MATCH (ea:EffectiveArticle {is_current: true})-[:COMPOSED_FROM]->(a:Article {uid: $uid})
  RETURN ea.effective_text, ea.as_of_date, ea.amendment_chain

  # Get full amendment history:
  MATCH (ea:EffectiveArticle)-[:AMENDED_BY {order: $n}]->(src:Article)
  RETURN src.uid, src.text_content

  # Check if article is still valid:
  MATCH (a:Article {uid: $uid})
  RETURN a.is_current, a.effective_date
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .models import ComposedArticle, ValidityReport, ArticleValidity

if TYPE_CHECKING:
    from neo4j import Driver, Session

logger = logging.getLogger(__name__)

WRITE_BATCH_SIZE = 500   # EffectiveArticle nodes per transaction


class EffectiveArticleWriter:
    """
    Persists ComposedArticle objects as EffectiveArticle nodes in Neo4j.

    Usage
    -----
        writer = EffectiveArticleWriter(driver)
        counts = writer.write_all(composed_articles)
        # {"created": N, "skipped": N, "errors": N}
        writer.close()
    """

    def __init__(self, driver: "Driver") -> None:
        self._driver = driver

    def close(self) -> None:
        self._driver.close()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def write(self, composed: ComposedArticle) -> bool:
        """
        Write one EffectiveArticle to Neo4j.
        Returns True on success, False on error.

        TODO (T3.3): implement using _merge_effective_article() and _link_relationships().
        """
        with self._driver.session() as session:
            try:
                session.execute_write(self._merge_effective_article, composed)
                session.execute_write(self._link_composed_from, composed)
                session.execute_write(self._link_amended_by, composed)
                return True
            except NotImplementedError:
                raise
            except Exception as exc:
                logger.error("Failed to write EffectiveArticle %s: %s", composed.uid, exc)
                return False

    def write_all(self, composed_articles: list[ComposedArticle]) -> dict[str, int]:
        """
        Write all composed articles in batches.
        Returns {"created": N, "skipped": N, "errors": N}.
        """
        counts = {"created": 0, "skipped": 0, "errors": 0}
        for i, composed in enumerate(composed_articles):
            success = self.write(composed)
            if success:
                counts["created"] += 1
            else:
                counts["errors"] += 1
            if (i + 1) % 500 == 0:
                logger.info("Written %d / %d EffectiveArticle nodes", i + 1, len(composed_articles))
        return counts

    def write_validity(self, report: ValidityReport) -> dict[str, int]:
        """
        Apply is_current updates to Article + EffectiveArticle nodes (T3.5).

        Returns {"updated": N, "errors": N}.

        TODO (T3.5): implement.

        Cypher template per ArticleValidity:
            MATCH (a:Article {uid: $uid})
            SET a.is_current = $is_current
            WITH a
            OPTIONAL MATCH (ea:EffectiveArticle)-[:COMPOSED_FROM]->(a)
            SET ea.is_current = CASE WHEN ea.as_of_date = max(ea.as_of_date) THEN $is_current ELSE false END
        """
        raise NotImplementedError("T3.5: implement write_validity()")

    # ------------------------------------------------------------------
    # Private Cypher helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _merge_effective_article(tx, composed: ComposedArticle) -> None:
        """
        TODO (T3.3): implement.

        Cypher:
            MERGE (ea:EffectiveArticle {uid: $uid})
            SET ea.as_of_date      = date($as_of_date),
                ea.effective_text  = $effective_text,
                ea.amendment_chain = $amendment_chain,
                ea.is_current      = $is_current,
                ea.changes_count   = $changes_count
        """
        raise NotImplementedError("T3.3: implement _merge_effective_article()")

    @staticmethod
    def _link_composed_from(tx, composed: ComposedArticle) -> None:
        """
        TODO (T3.3): implement.

        Cypher:
            MATCH (ea:EffectiveArticle {uid: $uid})
            MATCH (a:Article {uid: $article_uid})
            MERGE (ea)-[:COMPOSED_FROM]->(a)
        """
        raise NotImplementedError("T3.3: implement _link_composed_from()")

    @staticmethod
    def _link_amended_by(tx, composed: ComposedArticle) -> None:
        """
        TODO (T3.3): implement.
        Create AMENDED_BY relationships with order property.

        Cypher (per amendment in chain):
            MATCH (ea:EffectiveArticle {uid: $ea_uid})
            MATCH (src:Article {uid: $src_uid})
            MERGE (ea)-[:AMENDED_BY {order: $order}]->(src)
        """
        raise NotImplementedError("T3.3: implement _link_amended_by()")
