"""
Legal Provision Matcher — T4.3

Matches contract clauses to legal provisions using:
- Vector similarity search (article_embeddings index)
- Fulltext search fallback (article_fulltext index)
- Graph traversal for context expansion
- Authority-weighted reranking

Usage:
    from src.contract.matcher import LegalMatcher
    matcher = LegalMatcher()
    matches = await matcher.match(clause)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from neo4j import GraphDatabase

from src.config import (
    NEO4J_URI,
    NEO4J_TIMEOUT,
    neo4j_auth,
    EMBED_SERVICE_URL,
    EMBED_DIMENSIONS,
)
from src.contract.models import ContractClause
from src.contract.mock_bridge import (
    create_embedding_service,
    create_graph_repository,
    create_effective_text_service,
    EmbeddingService,
    GraphRepository,
    EffectiveTextService,
)


@dataclass
class MatchedProvision:
    """
    A legal provision matched to a contract clause.

    Attributes:
        article_uid: Article unique identifier
        article_index: Article number (Điều X)
        article_title: Article title
        article_text: Article clean_text
        effective_text: Composed effective text (if available)
        document_so_ky_hieu: Normalized document identifier
        document_title: Document title
        document_type: Luật, Nghị định, etc.
        semantic_score: Vector similarity score (0-1)
        authority_weight: Document type weight
        graph_boost: 1.5x if found via graph traversal
        combined_score: semantic × authority × graph_boost
        is_current: Whether the provision is currently effective
    """
    article_uid: str
    article_index: int
    article_title: str
    article_text: str
    effective_text: str = ""
    document_so_ky_hieu: str = ""
    document_title: str = ""
    document_type: str = ""
    semantic_score: float = 0.0
    authority_weight: float = 1.0
    graph_boost: float = 1.0
    combined_score: float = 0.0
    is_current: bool = True


# Authority weights by document type
AUTHORITY_WEIGHTS = {
    "Bộ luật": 3.0,
    "Luật": 3.0,
    "Nghị định": 2.0,
    "Thông tư": 1.5,
    "Thông tư liên tịch": 1.0,
}

GRAPH_BOOST = 1.5
DEFAULT_TOP_K = 20
RETURN_TOP_N = 5


class LegalMatcher:
    """
    Match contract clauses to legal provisions.

    Uses a three-step process:
    A. Semantic search (vector or fulltext)
    B. Graph traversal for context expansion
    C. Reranking by combined score
    """

    def __init__(
        self,
        embedding_service: Optional[EmbeddingService] = None,
        graph_repo: Optional[GraphRepository] = None,
        effective_text_service: Optional[EffectiveTextService] = None,
        top_k: int = DEFAULT_TOP_K,
        return_top_n: int = RETURN_TOP_N,
    ) -> None:
        self._embedding_service = embedding_service or create_embedding_service()
        self._graph_repo = graph_repo or create_graph_repository()
        self._effective_text_service = effective_text_service or create_effective_text_service()
        self._top_k = top_k
        self._return_top_n = return_top_n
        self._driver = GraphDatabase.driver(NEO4J_URI, auth=neo4j_auth())

    async def match(self, clause: ContractClause) -> list[MatchedProvision]:
        """
        Find the most relevant legal provisions for a contract clause.

        Args:
            clause: ContractClause to match

        Returns:
            Top-5 matched provisions ranked by combined score
        """
        # Step A: Semantic search
        candidates = await self._semantic_search(clause.text_content)

        # Step B: Graph traversal expansion
        expanded = await self._graph_traverse(candidates)

        # Step C: Reranking
        reranked = self._rerank(expanded)

        return reranked[:self._return_top_n]

    async def match_all(self, clauses: list[ContractClause]) -> dict[str, list[MatchedProvision]]:
        """
        Match multiple clauses to legal provisions.

        Args:
            clauses: List of ContractClause objects

        Returns:
            Dict mapping clause_id to list of MatchedProvision
        """
        results = {}
        for clause in clauses:
            results[clause.id] = await self.match(clause)
        return results

    async def _semantic_search(self, text: str) -> list[MatchedProvision]:
        """
        Search for relevant articles using vector or fulltext search.

        Tries vector search first, falls back to fulltext if embeddings unavailable.
        """
        # Try vector search
        try:
            embedding = await self._embedding_service.embed(text)
            return await self._vector_search(embedding)
        except Exception:
            # Fallback to fulltext search
            return await self._fulltext_search(text)

    async def _vector_search(self, query_vector: list[float]) -> list[MatchedProvision]:
        """Vector similarity search against article_embeddings index."""
        cypher = """
        CALL db.index.vector.queryNodes("article_embeddings", $top_k, $vector)
        YIELD node AS article, score
        MATCH (article)<-[:HAS_ARTICLE]-(doc:Document)
        WHERE article.is_current = true
        RETURN article, doc, score
        ORDER BY score DESC
        """
        with self._driver.session(default_access_mode="READ", database="neo4j") as session:
            result = session.run(cypher, vector=query_vector, top_k=self._top_k, config={"maxTransactionRetryTime": NEO4J_TIMEOUT * 1000})
            provisions = []
            for record in result:
                article = dict(record["article"])
                doc = dict(record["doc"])
                provision = MatchedProvision(
                    article_uid=article.get("uid", ""),
                    article_index=article.get("index", 0),
                    article_title=article.get("title", ""),
                    article_text=article.get("clean_text", ""),
                    document_so_ky_hieu=doc.get("so_ky_hieu", ""),
                    document_title=doc.get("title", ""),
                    document_type=doc.get("loai_van_ban", ""),
                    semantic_score=float(record["score"]),
                    authority_weight=AUTHORITY_WEIGHTS.get(doc.get("loai_van_ban", ""), 1.0),
                    is_current=article.get("is_current", True),
                )
                provisions.append(provision)
            return provisions

    async def _fulltext_search(self, text: str) -> list[MatchedProvision]:
        """Fulltext search fallback using article_fulltext index."""
        cypher = """
        CALL db.index.fulltext.queryNodes("article_fulltext", $text, {limit: $top_k})
        YIELD node AS article, score
        MATCH (article)<-[:HAS_ARTICLE]-(doc:Document)
        WHERE article.is_current = true
        RETURN article, doc, score
        ORDER BY score DESC
        """
        with self._driver.session(default_access_mode="READ", database="neo4j") as session:
            result = session.run(cypher, text=text, top_k=self._top_k, config={"maxTransactionRetryTime": NEO4J_TIMEOUT * 1000})
            provisions = []
            for record in result:
                article = dict(record["article"])
                doc = dict(record["doc"])
                provision = MatchedProvision(
                    article_uid=article.get("uid", ""),
                    article_index=article.get("index", 0),
                    article_title=article.get("title", ""),
                    article_text=article.get("clean_text", ""),
                    document_so_ky_hieu=doc.get("so_ky_hieu", ""),
                    document_title=doc.get("title", ""),
                    document_type=doc.get("loai_van_ban", ""),
                    semantic_score=float(record["score"]),
                    authority_weight=AUTHORITY_WEIGHTS.get(doc.get("loai_van_ban", ""), 1.0),
                    is_current=article.get("is_current", True),
                )
                provisions.append(provision)
            return provisions

    async def _graph_traverse(self, provisions: list[MatchedProvision]) -> list[MatchedProvision]:
        """
        Expand context by traversing graph from matched articles.

        Traverses REFERENCES_INTERNAL, REFERENCES_EXTERNAL, MODIFIES relationships.
        """
        expanded = list(provisions)
        seen_uids = {p.article_uid for p in provisions}

        for provision in provisions:
            # Get effective text
            eff = await self._effective_text_service.get_effective_text(
                provision.article_uid, provision.article_text
            )
            if eff:
                provision.effective_text = eff.get("effective_text", provision.article_text)

            # Traverse references (if graph repo is real)
            refs = await self._graph_repo.traverse_references(provision.article_uid)
            for ref in refs:
                ref_uid = ref.get("uid", "")
                if ref_uid and ref_uid not in seen_uids:
                    seen_uids.add(ref_uid)
                    ref_provision = MatchedProvision(
                        article_uid=ref_uid,
                        article_index=ref.get("index", 0),
                        article_title=ref.get("title", ""),
                        article_text=ref.get("clean_text", ""),
                        document_so_ky_hieu=ref.get("so_ky_hieu", ""),
                        document_title=ref.get("document_title", ""),
                        document_type=ref.get("loai_van_ban", ""),
                        semantic_score=provision.semantic_score * 0.8,  # Slightly lower score
                        authority_weight=AUTHORITY_WEIGHTS.get(ref.get("loai_van_ban", ""), 1.0),
                        graph_boost=GRAPH_BOOST,
                        is_current=ref.get("is_current", True),
                    )
                    expanded.append(ref_provision)

        return expanded

    def _rerank(self, provisions: list[MatchedProvision]) -> list[MatchedProvision]:
        """
        Rerank provisions by combined score.

        combined_score = semantic_score × authority_weight × graph_boost
        """
        for provision in provisions:
            provision.combined_score = (
                provision.semantic_score
                * provision.authority_weight
                * provision.graph_boost
            )

        return sorted(provisions, key=lambda p: p.combined_score, reverse=True)
