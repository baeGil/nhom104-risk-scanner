"""
Amendment chain traverser — T3.1 (Người B)

Queries Neo4j to collect all [:MODIFIES] edges for each Article,
orders them chronologically, and handles transitive chains.

Input : Neo4j graph (Article nodes + MODIFIES relationships from T2.3)
Output: AmendmentChain per Article — pure data, no Neo4j in output
"""
from __future__ import annotations

import logging
from datetime import date
from typing import TYPE_CHECKING, Optional

from .models import Amendment, AmendmentAction, AmendmentChain

if TYPE_CHECKING:
    from neo4j import Driver, Session

logger = logging.getLogger(__name__)

# Max recursion depth for transitive chain resolution
MAX_CHAIN_DEPTH = 10


class AmendmentChainTraverser:
    """
    Traverses [:MODIFIES] edges in Neo4j to build ordered AmendmentChain objects.

    Usage
    -----
        traverser = AmendmentChainTraverser(driver)

        # Single article
        chain = traverser.traverse_article("doc_42_dieu_5")

        # All articles that have at least one MODIFIES edge
        chains = traverser.traverse_all()
        # Returns list[AmendmentChain], one per amended Article
    """

    def __init__(self, driver: "Driver") -> None:
        self._driver = driver

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def traverse_article(self, article_uid: str) -> AmendmentChain:
        """
        Build the full AmendmentChain for one Article.

        Parameters
        ----------
        article_uid : str
            Article.uid of the target Article (the one being amended).
            Format: "doc_{doc_id}_dieu_{index}"

        Returns
        -------
        AmendmentChain
            amendments list is ordered by source_doc.ngay_ban_hanh ASC.
            is_transitive=True if any source document was itself modified by another.

        TODO (T3.1): implement this method.

        Suggested Cypher:
            MATCH (src:Article)-[r:MODIFIES]->(tgt:Article {uid: $uid})
            MATCH (src)<-[:HAS_ARTICLE]-(sdoc:Document)
            RETURN
              src.uid                  AS source_uid,
              sdoc.id                  AS source_doc_id,
              sdoc.ngay_ban_hanh       AS ngay_ban_hanh,
              r.action                 AS action,
              r.target_clause          AS target_khoan,
              r.target_point           AS target_diem,
              r.new_text               AS new_text,
              r.context_text           AS context_text,
              r.confidence             AS confidence
            ORDER BY sdoc.ngay_ban_hanh ASC

        For transitive detection:
            MATCH (src:Article)-[:MODIFIES]->(tgt {uid: $uid})
            MATCH ()-[:MODIFIES]->(src)
            RETURN count(*) > 0 AS is_transitive
        """
        raise NotImplementedError("T3.1: implement traverse_article()")

    def traverse_all(
        self,
        *,
        min_confidence: float = 0.0,
        batch_size: int = 1000,
    ) -> list[AmendmentChain]:
        """
        Build AmendmentChains for ALL Articles that have at least one MODIFIES edge.

        Parameters
        ----------
        min_confidence : float
            Skip MODIFIES edges with confidence < this threshold.
        batch_size : int
            How many articles to process per Neo4j query round-trip.

        Returns
        -------
        list[AmendmentChain]

        Notes for implementer
        ---------------------
        1. First query: get distinct target Article UIDs with ≥1 MODIFIES edge
           MATCH ()-[:MODIFIES]->(a:Article) RETURN DISTINCT a.uid
        2. Then call traverse_article() per UID (can be batched with UNWIND).
        3. Log progress every 100 articles.

        TODO (T3.1): implement this method.
        """
        raise NotImplementedError("T3.1: implement traverse_all()")

    def get_amended_article_uids(self) -> list[str]:
        """
        Return UIDs of all Articles that have ≥1 incoming MODIFIES edge.
        Utility method — used by other parts of the pipeline.

        Cypher:
            MATCH ()-[:MODIFIES]->(a:Article)
            RETURN DISTINCT a.uid

        TODO (T3.1): implement.
        """
        raise NotImplementedError("T3.1: implement get_amended_article_uids()")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_action(raw: str) -> AmendmentAction:
        """
        Convert raw action string from Neo4j to AmendmentAction enum.
        Handles both enum values and raw Vietnamese strings.
        """
        _map = {
            "sua_doi":      AmendmentAction.SUA_DOI,
            "bo_sung":      AmendmentAction.BO_SUNG,
            "thay_the":     AmendmentAction.THAY_THE,
            "bai_bo":       AmendmentAction.BAI_BO,
            "het_hieu_luc": AmendmentAction.HET_HIEU_LUC,
            # Vietnamese originals (fallback)
            "sửa đổi":      AmendmentAction.SUA_DOI,
            "bổ sung":      AmendmentAction.BO_SUNG,
            "thay thế":     AmendmentAction.THAY_THE,
            "bãi bỏ":       AmendmentAction.BAI_BO,
        }
        return _map.get(str(raw).lower().strip(), AmendmentAction.SUA_DOI)

    @staticmethod
    def _parse_date(raw) -> date:
        """Parse Neo4j Date or ISO string to Python date. Returns date.min on failure."""
        if raw is None:
            return date.min
        if isinstance(raw, date):
            return raw
        try:
            return date.fromisoformat(str(raw))
        except ValueError:
            logger.warning("Could not parse date: %s", raw)
            return date.min
