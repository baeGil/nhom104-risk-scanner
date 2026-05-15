"""
Retrieval Engine — T5.2

Multi-strategy retrieval pipeline consuming SubQuery objects from intent analysis.
Supports: direct_lookup, vector_search, graph_traversal, hybrid_search, validity_check, comparison.

Usage:
    from src.llm.retriever import RetrievalEngine
    engine = RetrievalEngine()
    results = await engine.retrieve(sub_query)
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

from neo4j import GraphDatabase

from src.config import NEO4J_URI, NEO4J_TIMEOUT, neo4j_auth
from src.llm.models import SubQuery
from src.contract.mock_bridge import create_embedding_service


@dataclass
class RetrievedProvision:
    """
    A legal provision retrieved for a query.

    Attributes:
        article_uid: Article unique identifier
        article_index: Article number
        article_title: Article title
        article_text: Article clean_text
        effective_text: Composed effective text
        document_so_ky_hieu: Normalized document identifier
        document_title: Document title
        document_type: Luật, Nghị định, etc.
        score: Combined reranking score
        strategy: Strategy that found this provision
        is_current: Whether currently effective
        amendment_history: List of amendments
    """
    article_uid: str
    article_index: int
    article_title: str
    article_text: str
    effective_text: str = ""
    document_so_ky_hieu: str = ""
    document_title: str = ""
    document_type: str = ""
    score: float = 0.0
    strategy: str = ""
    is_current: bool = True
    amendment_history: list[dict] = field(default_factory=list)


@dataclass
class RetrievalResult:
    """
    Full retrieval result for a query.

    Attributes:
        query: Original SubQuery
        provisions: List of retrieved provisions
        strategy_used: Strategy that was executed
        total_found: Total number of candidates before reranking
    """
    query: SubQuery
    provisions: list[RetrievedProvision] = field(default_factory=list)
    strategy_used: str = ""
    total_found: int = 0


# Authority weights
AUTHORITY_WEIGHTS = {
    "Bộ luật": 3.0,
    "Luật": 3.0,
    "Nghị định": 2.0,
    "Thông tư": 1.5,
    "Thông tư liên tịch": 1.0,
}


class RetrievalStrategy(ABC):
    """Abstract base for retrieval strategies."""

    @abstractmethod
    async def execute(self, query: SubQuery) -> list[RetrievedProvision]:
        """Execute retrieval strategy."""
        ...


class DirectLookupStrategy(RetrievalStrategy):
    """
    Direct lookup by article reference.

    Resolves so_ky_hieu → doc_id, MATCH Article by uid.
    """

    def __init__(self) -> None:
        self._driver = GraphDatabase.driver(NEO4J_URI, auth=neo4j_auth())

    async def execute(self, query: SubQuery) -> list[RetrievedProvision]:
        extracted = query.query  # Use query text as-is for now
        # Parse article number and document reference from query
        # This is a simplified version - full implementation would parse entities
        import re
        match = re.search(r"Điều\s+(\d+)", extracted, re.IGNORECASE)
        article_num = int(match.group(1)) if match else None

        if not article_num:
            return []

        cypher = """
        MATCH (a:Article {index: $index})<-[:HAS_ARTICLE]-(d:Document)
        RETURN a, d
        LIMIT 5
        """
        with self._driver.session() as session:
            result = session.run(cypher, index=article_num)
            provisions = []
            for record in result:
                article = dict(record["a"])
                doc = dict(record["d"])
                provisions.append(RetrievedProvision(
                    article_uid=article.get("uid", ""),
                    article_index=article.get("index", 0),
                    article_title=article.get("title", ""),
                    article_text=article.get("clean_text", ""),
                    document_so_ky_hieu=doc.get("so_ky_hieu", ""),
                    document_title=doc.get("title", ""),
                    document_type=doc.get("loai_van_ban", ""),
                    score=1.0,
                    strategy="direct_lookup",
                    is_current=article.get("is_current", True),
                ))
            return provisions


class VectorSearchStrategy(RetrievalStrategy):
    """
    Vector similarity search against article_embeddings.

    Embeds query text, searches vector index, filters by is_current.
    """

    def __init__(self, top_k: int = 20) -> None:
        self._driver = GraphDatabase.driver(NEO4J_URI, auth=neo4j_auth())
        self._embedding_service = create_embedding_service()
        self._top_k = top_k

    async def execute(self, query: SubQuery) -> list[RetrievedProvision]:
        try:
            embedding = await self._embedding_service.embed(query.query)
        except Exception:
            return []

        cypher = """
        CALL db.index.vector.queryNodes("article_embeddings", $top_k, $vector)
        YIELD node AS article, score
        MATCH (article)<-[:HAS_ARTICLE]-(doc:Document)
        WHERE article.is_current = true
        RETURN article, doc, score
        ORDER BY score DESC
        """
        with self._driver.session() as session:
            result = session.run(cypher, vector=embedding, top_k=self._top_k)
            provisions = []
            for record in result:
                article = dict(record["article"])
                doc = dict(record["doc"])
                provisions.append(RetrievedProvision(
                    article_uid=article.get("uid", ""),
                    article_index=article.get("index", 0),
                    article_title=article.get("title", ""),
                    article_text=article.get("clean_text", ""),
                    document_so_ky_hieu=doc.get("so_ky_hieu", ""),
                    document_title=doc.get("title", ""),
                    document_type=doc.get("loai_van_ban", ""),
                    score=float(record["score"]),
                    strategy="vector_search",
                    is_current=article.get("is_current", True),
                ))
            return provisions


class GraphTraversalStrategy(RetrievalStrategy):
    """
    Graph traversal from matched articles.

    Traverses REFERENCES_INTERNAL, REFERENCES_EXTERNAL, MODIFIES, DETAILS.
    """

    def __init__(self, seed_article_uid: str) -> None:
        self._driver = GraphDatabase.driver(NEO4J_URI, auth=neo4j_auth())
        self._seed_uid = seed_article_uid

    async def execute(self, query: SubQuery) -> list[RetrievedProvision]:
        cypher = """
        MATCH (seed:Article {uid: $uid})
        OPTIONAL MATCH (seed)-[:REFERENCES_INTERNAL|REFERENCES_EXTERNAL]->(ref)
        OPTIONAL MATCH (seed)<-[:MODIFIES]-(mod)
        RETURN ref, mod
        """
        with self._driver.session() as session:
            result = session.run(cypher, uid=self._seed_uid)
            provisions = []
            for record in result:
                ref = record.get("ref")
                if ref:
                    ref_dict = dict(ref)
                    provisions.append(RetrievedProvision(
                        article_uid=ref_dict.get("uid", ""),
                        article_index=ref_dict.get("index", 0),
                        article_title=ref_dict.get("title", ""),
                        article_text=ref_dict.get("clean_text", ""),
                        score=0.8,
                        strategy="graph_traversal",
                    ))
            return provisions


class HybridSearchStrategy(RetrievalStrategy):
    """
    Hybrid search combining fulltext + vector results.

    Deduplicates and reranks combined results.
    """

    def __init__(self, top_k: int = 20) -> None:
        self._driver = GraphDatabase.driver(NEO4J_URI, auth=neo4j_auth())
        self._embedding_service = create_embedding_service()
        self._top_k = top_k

    async def execute(self, query: SubQuery) -> list[RetrievedProvision]:
        results = {}

        # Vector search
        try:
            embedding = await self._embedding_service.embed(query.query)
            vector_results = await self._vector_search(embedding)
            for p in vector_results:
                results[p.article_uid] = p
        except Exception:
            pass

        # Fulltext search
        fulltext_results = await self._fulltext_search(query.query)
        for p in fulltext_results:
            if p.article_uid not in results:
                results[p.article_uid] = p
            else:
                # Average scores
                existing = results[p.article_uid]
                existing.score = (existing.score + p.score) / 2

        return sorted(results.values(), key=lambda p: p.score, reverse=True)

    async def _vector_search(self, embedding: list[float]) -> list[RetrievedProvision]:
        cypher = """
        CALL db.index.vector.queryNodes("article_embeddings", $top_k, $vector)
        YIELD node AS article, score
        MATCH (article)<-[:HAS_ARTICLE]-(doc:Document)
        WHERE article.is_current = true
        RETURN article, doc, score
        """
        with self._driver.session() as session:
            result = session.run(cypher, vector=embedding, top_k=self._top_k)
            return [
                RetrievedProvision(
                    article_uid=dict(r["a"]).get("uid", ""),
                    article_index=dict(r["a"]).get("index", 0),
                    article_title=dict(r["a"]).get("title", ""),
                    article_text=dict(r["a"]).get("clean_text", ""),
                    document_so_ky_hieu=dict(r["d"]).get("so_ky_hieu", ""),
                    document_title=dict(r["d"]).get("title", ""),
                    document_type=dict(r["d"]).get("loai_van_ban", ""),
                    score=float(r["score"]),
                    strategy="hybrid",
                )
                for r in result
            ]

    async def _fulltext_search(self, text: str) -> list[RetrievedProvision]:
        cypher = """
        CALL db.index.fulltext.queryNodes("article_fulltext", $text, {limit: $top_k})
        YIELD node AS article, score
        MATCH (article)<-[:HAS_ARTICLE]-(doc:Document)
        WHERE article.is_current = true
        RETURN article, doc, score
        """
        with self._driver.session() as session:
            result = session.run(cypher, text=text, top_k=self._top_k)
            return [
                RetrievedProvision(
                    article_uid=dict(r["a"]).get("uid", ""),
                    article_index=dict(r["a"]).get("index", 0),
                    article_title=dict(r["a"]).get("title", ""),
                    article_text=dict(r["a"]).get("clean_text", ""),
                    document_so_ky_hieu=dict(r["d"]).get("so_ky_hieu", ""),
                    document_title=dict(r["d"]).get("title", ""),
                    document_type=dict(r["d"]).get("loai_van_ban", ""),
                    score=float(r["score"]),
                    strategy="hybrid",
                )
                for r in result
            ]


class ValidityCheckStrategy(RetrievalStrategy):
    """
    Check validity of an article/document.

    Looks up is_current flag and SUPERSEDED_BY relationships.
    """

    def __init__(self) -> None:
        self._driver = GraphDatabase.driver(NEO4J_URI, auth=neo4j_auth())

    async def execute(self, query: SubQuery) -> list[RetrievedProvision]:
        import re
        match = re.search(r"Điều\s+(\d+)", query.query, re.IGNORECASE)
        article_num = int(match.group(1)) if match else None

        if not article_num:
            return []

        cypher = """
        MATCH (a:Article {index: $index})<-[:HAS_ARTICLE]-(d:Document)
        OPTIONAL MATCH (d)-[:SUPERSEDED_BY]->(superseded)
        RETURN a, d, superseded
        """
        with self._driver.session() as session:
            result = session.run(cypher, index=article_num)
            provisions = []
            for record in result:
                article = dict(record["a"])
                doc = dict(record["d"])
                provisions.append(RetrievedProvision(
                    article_uid=article.get("uid", ""),
                    article_index=article.get("index", 0),
                    article_title=article.get("title", ""),
                    article_text=article.get("clean_text", ""),
                    document_so_ky_hieu=doc.get("so_ky_hieu", ""),
                    document_title=doc.get("title", ""),
                    document_type=doc.get("loai_van_ban", ""),
                    score=1.0,
                    strategy="validity_check",
                    is_current=article.get("is_current", True),
                ))
            return provisions


class ComparisonStrategy(RetrievalStrategy):
    """
    Parallel direct lookups for comparison.

    Returns side-by-side results.
    """

    def __init__(self) -> None:
        self._driver = GraphDatabase.driver(NEO4J_URI, auth=neo4j_auth())

    async def execute(self, query: SubQuery) -> list[RetrievedProvision]:
        # Extract all article references from query
        import re
        matches = re.findall(r"Điều\s+(\d+)", query.query, re.IGNORECASE)
        article_nums = [int(m) for m in matches]

        if not article_nums:
            return []

        cypher = """
        MATCH (a:Article {index: $index})<-[:HAS_ARTICLE]-(d:Document)
        RETURN a, d
        """
        provisions = []
        with self._driver.session() as session:
            for num in article_nums:
                result = session.run(cypher, index=num)
                for record in result:
                    article = dict(record["a"])
                    doc = dict(record["d"])
                    provisions.append(RetrievedProvision(
                        article_uid=article.get("uid", ""),
                        article_index=article.get("index", 0),
                        article_title=article.get("title", ""),
                        article_text=article.get("clean_text", ""),
                        document_so_ky_hieu=doc.get("so_ky_hieu", ""),
                        document_title=doc.get("title", ""),
                        document_type=doc.get("loai_van_ban", ""),
                        score=1.0,
                        strategy="comparison",
                    ))
        return provisions


class RetrievalEngine:
    """
    Multi-strategy retrieval engine.

    Routes SubQuery objects to appropriate strategy based on retrieval_strategy.
    """

    def __init__(self) -> None:
        self._strategies: dict[str, RetrievalStrategy] = {
            "direct_lookup": DirectLookupStrategy(),
            "vector_search": VectorSearchStrategy(),
            "graph_traversal": GraphTraversalStrategy(""),  # seed_uid set at runtime
            "hybrid_search": HybridSearchStrategy(),
            "validity_check": ValidityCheckStrategy(),
            "comparison": ComparisonStrategy(),
        }

    async def retrieve(self, query: SubQuery) -> RetrievalResult:
        """
        Execute retrieval for a SubQuery.

        Args:
            query: SubQuery from intent analysis

        Returns:
            RetrievalResult with provisions
        """
        strategy = self._strategies.get(query.retrieval_strategy)
        if not strategy:
            # Default to hybrid_search
            strategy = self._strategies["hybrid_search"]

        provisions = await strategy.execute(query)

        # Apply reranking
        provisions = self._rerank(provisions)

        return RetrievalResult(
            query=query,
            provisions=provisions[:5],  # Top-5
            strategy_used=query.retrieval_strategy,
            total_found=len(provisions),
        )

    def _rerank(self, provisions: list[RetrievedProvision]) -> list[RetrievedProvision]:
        """Rerank by authority weight."""
        for p in provisions:
            authority = AUTHORITY_WEIGHTS.get(p.document_type, 1.0)
            p.score *= authority
        return sorted(provisions, key=lambda p: p.score, reverse=True)
