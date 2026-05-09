"""
Effective Text Composition Module — Phase 3 (T3.1 → T3.5)
==========================================================
Traverses amendment chains in Neo4j, composes effective text for each Article,
creates EffectiveArticle nodes, validates against VB hợp nhất, and computes is_current.

Owner: Người B
Depends on:
  - T2.3 (cross_reference/ — MODIFIES relationships in Neo4j)  [Người B Phase 2]
  - T1.7 (SUPERSEDES/PARTIALLY_SUPERSEDES doc-level edges)     [Người A]
  - T1.5 (Article/Clause/Point nodes in Neo4j)                 [Người B Phase 1]
Provides to:
  - Người C (T4.3, T5.2): EffectiveArticle nodes + is_current + vector index
"""

from .models import (
    AmendmentAction,
    Amendment,
    AmendmentChain,
    ComposedArticle,
    ValidityStatus,
    ValidityReport,
    ValidationMatch,
    HopNhatReport,
)
from .chain import AmendmentChainTraverser
from .merger import TextMerger
from .writer import EffectiveArticleWriter
from .validator import HopNhatValidator
from .current import CurrentStatusComputer

__all__ = [
    # Models
    "AmendmentAction",
    "Amendment",
    "AmendmentChain",
    "ComposedArticle",
    "ValidityStatus",
    "ValidityReport",
    "ValidationMatch",
    "HopNhatReport",
    # Core classes
    "AmendmentChainTraverser",
    "TextMerger",
    "EffectiveArticleWriter",
    "HopNhatValidator",
    "CurrentStatusComputer",
]
