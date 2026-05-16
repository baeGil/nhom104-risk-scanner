#!/usr/bin/env python3
"""
Full Contract Review Pipeline — Real End-to-End Test
=====================================================
- Real SentenceTransformer embeddings (mainguyen9/vietlegal-harrier-0.6b)
- Real Neo4j graph queries
- Real OpenAI LLM calls
- Tests all 3 sample contracts
- Logs every phase with timing, metrics, and quality assessment

Usage:
    python scripts/full_pipeline_real_test.py
"""

import os
import sys
import json
import time
import asyncio
import logging
import uuid
import re
from dataclasses import dataclass, field
from typing import Any, Optional
from pathlib import Path

# ── Force real mode ──────────────────────────────────────────────────────────
os.environ["GRAPH_REPOSITORY_MODE"] = "neo4j"
os.environ["EMBEDDING_SERVICE_MODE"] = "real"
os.environ["EFFECTIVE_TEXT_SERVICE_MODE"] = "mock"
os.environ["LLM_PROVIDER"] = "openai"

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
from src.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, OPENAI_API_KEY, OPENAI_MODEL, EMBED_DIMENSIONS
from src.contract.parser import ContractParser
from src.contract.pii import detect_pii, redact_pii
from src.contract.models import Contract, ContractClause
from src.contract.query_rewriter import QueryRewriter, LegalRetrievalPlan
from src.contract.hybrid_retriever import LegalHybridRetriever, LegalCandidate
from src.contract.matcher import LegalMatcher, MatchedProvision
from src.contract.clause_extractor import ClauseExtractor
from src.contract.compliance_analyzer import ComplianceAnalyzer
from src.llm.citation_verifier import CitationVerifier
from src.contract.review_pipeline import ContractReviewPipeline
from src.llm.client import OpenAIClient

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)

# ── Real Embedding Service using SentenceTransformer ─────────────────────────
class RealEmbeddingService:
    """Real embedding service using vietlegal-harrier-0.6b."""

    INSTRUCTION = (
        "Instruct: Given a Vietnamese legal question, retrieve relevant legal passages that answer the question\nQuery: "
    )

    def __init__(self, model_name: str = "mainguyen9/vietlegal-harrier-0.6b"):
        logger.info(f"Loading SentenceTransformer model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.dimensions = self.model.get_sentence_embedding_dimension()
        logger.info(f"Model loaded. Embedding dimension: {self.dimensions}")

    async def embed(self, text: str) -> list[float]:
        query_text = self.INSTRUCTION + text
        embedding = self.model.encode([query_text], normalize_embeddings=True)[0]
        return embedding.tolist()

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        query_texts = [self.INSTRUCTION + t for t in texts]
        embeddings = self.model.encode(query_texts, normalize_embeddings=True)
        return [e.tolist() for e in embeddings]


# ── Phase Tracker ────────────────────────────────────────────────────────────
@dataclass
class PhaseLog:
    name: str
    start_time: float = 0.0
    end_time: float = 0.0
    status: str = "pending"
    metrics: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    error: str = ""

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time if self.end_time else 0.0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "status": self.status,
            "duration_sec": round(self.duration, 3),
            "metrics": self.metrics,
            "notes": self.notes,
            "error": self.error,
        }


class PipelineTracker:
    def __init__(self):
        self.phases: list[PhaseLog] = []
        self.current: Optional[PhaseLog] = None

    def start(self, name: str) -> "PipelineTracker":
        phase = PhaseLog(name=name, start_time=time.time())
        self.phases.append(phase)
        self.current = phase
        print(f"\n{'='*70}")
        print(f"  ▶ PHASE: {name}")
        print(f"{'='*70}")
        return self

    def ok(self, key: str, value: Any, detail: str = ""):
        if self.current:
            self.current.metrics[key] = value
            if detail:
                self.current.notes.append(detail)
            icon = "✅" if value else "⚠️"
            print(f"  {icon} {key}: {value}")
            if detail:
                print(f"     {detail}")

    def fail(self, error: str):
        if self.current:
            self.current.status = "failed"
            self.current.error = error
            self.current.end_time = time.time()
            print(f"  ❌ FAILED: {error}")

    def done(self):
        if self.current:
            self.current.status = "completed"
            self.current.end_time = time.time()
            print(f"  ⏱ Duration: {self.current.duration:.3f}s")

    def summary(self) -> dict:
        total_time = sum(p.duration for p in self.phases)
        passed = sum(1 for p in self.phases if p.status == "completed")
        failed = sum(1 for p in self.phases if p.status == "failed")
        return {
            "total_phases": len(self.phases),
            "passed": passed,
            "failed": failed,
            "total_time_sec": round(total_time, 3),
            "phases": [p.to_dict() for p in self.phases],
        }


# ── Retrieval Evaluator ─────────────────────────────────────────────────────
class RetrievalEvaluator:
    """Evaluate retrieval quality for each clause."""

    @staticmethod
    def evaluate(plan: LegalRetrievalPlan, candidates: list[LegalCandidate], clause: ContractClause) -> dict:
        """Return evaluation metrics for a retrieval operation."""
        if not candidates:
            return {
                "num_candidates": 0,
                "sources_used": [],
                "avg_vector_score": 0.0,
                "avg_lexical_score": 0.0,
                "avg_combined_score": 0.0,
                "has_graph_expansion": False,
                "has_validity_signal": False,
                "document_diversity": 0,
                "unique_document_types": [],
                "top_citation": "",
                "quality_score": 0.0,
                "quality_grade": "F",
                "issues": ["No candidates retrieved"],
            }

        sources = set()
        for c in candidates:
            sources.update(c.sources)

        vector_scores = [c.score_factors.vector for c in candidates if c.score_factors.vector > 0]
        lexical_scores = [c.score_factors.lexical for c in candidates if c.score_factors.lexical > 0]
        combined_scores = [c.combined_score for c in candidates]

        doc_titles = set(c.document_title for c in candidates if c.document_title)
        doc_types = set(c.document_type for c in candidates if c.document_type)

        has_graph = any("graph" in c.sources for c in candidates)
        has_validity = any(c.validity_signal != "latest_known" for c in candidates)

        # Quality scoring
        quality = 0.0
        issues = []

        # 1. Candidate count (more is better, up to a point)
        n = len(candidates)
        if n >= 5:
            quality += 20
        elif n >= 3:
            quality += 15
        elif n >= 1:
            quality += 10
            issues.append(f"Only {n} candidate(s) retrieved")

        # 2. Vector score quality
        if vector_scores:
            avg_vec = sum(vector_scores) / len(vector_scores)
            if avg_vec > 0.7:
                quality += 25
            elif avg_vec > 0.5:
                quality += 20
            elif avg_vec > 0.3:
                quality += 10
                issues.append(f"Low vector similarity (avg={avg_vec:.3f})")
            else:
                issues.append(f"Very low vector similarity (avg={avg_vec:.3f})")
        else:
            issues.append("No vector scores (embedding search returned nothing)")

        # 3. Multi-source retrieval
        if len(sources) >= 3:
            quality += 20
        elif len(sources) >= 2:
            quality += 15
        elif len(sources) >= 1:
            quality += 5
            issues.append(f"Only {len(sources)} source(s) used: {sources}")

        # 4. Document diversity
        if len(doc_titles) >= 3:
            quality += 15
        elif len(doc_titles) >= 2:
            quality += 10
        elif len(doc_titles) >= 1:
            quality += 5

        # 5. Graph expansion
        if has_graph:
            quality += 10

        # 6. Validity awareness
        if has_validity:
            quality += 5

        # 7. Plan quality
        if plan.source == "llm" and plan.confidence > 0.5:
            quality += 5
        elif plan.keywords or plan.search_queries:
            quality += 3

        # Grade
        if quality >= 85:
            grade = "A"
        elif quality >= 70:
            grade = "B"
        elif quality >= 55:
            grade = "C"
        elif quality >= 40:
            grade = "D"
        else:
            grade = "F"

        top = candidates[0] if candidates else None

        return {
            "num_candidates": n,
            "sources_used": sorted(sources),
            "avg_vector_score": round(sum(vector_scores) / len(vector_scores), 4) if vector_scores else 0.0,
            "max_vector_score": round(max(vector_scores), 4) if vector_scores else 0.0,
            "avg_lexical_score": round(sum(lexical_scores) / len(lexical_scores), 4) if lexical_scores else 0.0,
            "avg_combined_score": round(sum(combined_scores) / len(combined_scores), 4) if combined_scores else 0.0,
            "max_combined_score": round(max(combined_scores), 4) if combined_scores else 0.0,
            "has_graph_expansion": has_graph,
            "has_validity_signal": has_validity,
            "document_diversity": len(doc_titles),
            "unique_document_types": sorted(doc_types),
            "unique_documents": sorted(doc_titles)[:5],
            "top_citation": top.display_citation() if top else "",
            "top_score": round(top.combined_score, 4) if top else 0.0,
            "plan_source": plan.source,
            "plan_keywords": plan.keywords,
            "plan_search_queries": plan.search_queries[:3],
            "quality_score": quality,
            "quality_grade": grade,
            "issues": issues,
        }


# ── Main Test ────────────────────────────────────────────────────────────────
SAMPLE_CONTRACTS = [
    "data/sample_contracts/sample_hop_dong_thue.md",
    "data/sample_contracts/sample_hop_dong_mua_ban.md",
    "data/sample_contracts/sample_hop_dong_lao_dong.md",
]


async def run_full_pipeline():
    tracker = PipelineTracker()
    evaluator = RetrievalEvaluator()
    all_retrieval_evals = []

    print("\n" + "█" * 70)
    print("  FULL CONTRACT REVIEW PIPELINE — REAL END-TO-END TEST")
    print("  Real embeddings + Real Neo4j + Real LLM")
    print("█" * 70)

    # ── Pre-flight checks ────────────────────────────────────────────────────
    preflight = tracker.start("Pre-flight Checks")

    # Neo4j connection
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        with driver.session(database="neo4j") as session:
            doc_count = session.run("MATCH (d:Document) RETURN count(d) as cnt").single()["cnt"]
            art_count = session.run("MATCH (a:Article) RETURN count(a) as cnt").single()["cnt"]
            emb_count = session.run("MATCH (a:Article) WHERE a.embedding IS NOT NULL RETURN count(a) as cnt").single()["cnt"]
            clause_count = session.run("MATCH (c:Clause) RETURN count(c) as cnt").single()["cnt"]
            point_count = session.run("MATCH (p:Point) RETURN count(p) as cnt").single()["cnt"]
            ref_count = session.run("MATCH ()-[r:REFERENCES_INTERNAL|REFERENCES_EXTERNAL|MODIFIES]->() RETURN count(r) as cnt").single()["cnt"]
            ft_index = session.run("SHOW FULLTEXT INDEXES").data()
            vec_index = session.run("SHOW VECTOR INDEXES").data()

        tracker.ok("Neo4j connected", True, f"URI: {NEO4J_URI}")
        tracker.ok("Documents", doc_count)
        tracker.ok("Articles", art_count)
        tracker.ok("Articles with embeddings", emb_count, f"{emb_count}/{art_count} embedded")
        tracker.ok("Clauses", clause_count)
        tracker.ok("Points", point_count)
        tracker.ok("Graph relationships (REF/MOD)", ref_count)
        tracker.ok("Fulltext indexes", len(ft_index), str([i.get("name") for i in ft_index]))
        tracker.ok("Vector indexes", len(vec_index), str([i.get("name") for i in vec_index]))
        driver.close()
    except Exception as e:
        tracker.fail(f"Neo4j connection failed: {e}")
        print("\n❌ Cannot continue without Neo4j")
        return None

    # Sample contracts exist
    existing_contracts = []
    for path in SAMPLE_CONTRACTS:
        full = Path(__file__).resolve().parent.parent / path
        if full.exists():
            existing_contracts.append(str(full))
            tracker.ok(f"Contract exists", True, path)
        else:
            tracker.ok(f"Contract missing", False, path)

    if not existing_contracts:
        tracker.fail("No sample contracts found")
        return None

    tracker.done()

    # ── Load real embedding model ────────────────────────────────────────────
    embed_phase = tracker.start("Load Real Embedding Model (SentenceTransformer)")
    try:
        embed_service = RealEmbeddingService()
        embed_phase.ok("Model loaded", True, f"Dimension: {embed_service.dimensions}")

        # Quick test
        test_vec = await embed_service.embed("phạt vi phạm hợp đồng")
        embed_phase.ok("Test embedding OK", len(test_vec) == embed_service.dimensions, f"Vector length: {len(test_vec)}")
        embed_phase.ok("Vector norm", round(sum(v*v for v in test_vec)**0.5, 4), "Should be ~1.0 (normalized)")
        embed_phase.done()
    except Exception as e:
        embed_phase.fail(f"Failed to load model: {e}")
        print("\n❌ Cannot continue without embedding model")
        return None

    # ── Test LLM connection ──────────────────────────────────────────────────
    llm_phase = tracker.start("Test Real LLM Connection (OpenAI)")
    try:
        llm_client = OpenAIClient()
        test_resp = await llm_client.chat("Trả lời ngắn gọn: 1+1 bằng mấy?", temperature=0.0)
        llm_phase.ok("LLM connected", True, f"Model: {OPENAI_MODEL}")
        llm_phase.ok("Test response", str(test_resp)[:100])
        llm_phase.done()
    except Exception as e:
        llm_phase.fail(f"LLM connection failed: {e}")
        print("\n❌ Cannot continue without LLM")
        return None

    # ── Process each contract ────────────────────────────────────────────────
    for contract_path in existing_contracts:
        contract_name = Path(contract_path).name
        print(f"\n{'#'*70}")
        print(f"  # PROCESSING: {contract_name}")
        print(f"{'#'*70}")

        # Phase 0: Parse
        p0 = tracker.start(f"[{contract_name}] Phase 0: Parse Contract")
        try:
            parser = ContractParser()
            contract = parser.parse(contract_path)
            p0.ok("Parsed", True, f"Format: {contract.source_format}")
            p0.ok("Raw text length", len(contract.raw_text), f"{len(contract.raw_text.split())} words")
            p0.ok("Redacted text length", len(contract.redacted_text))
            p0.ok("PII map size", len(contract.pii_map))
            if contract.pii_map:
                for k, v in list(contract.pii_map.items())[:3]:
                    p0.ok(f"  PII: {k}", v[:30] + "..." if len(v) > 30 else v)
            p0.done()
        except Exception as e:
            p0.fail(str(e))
            continue

        # Phase 1: PII Detection
        p1 = tracker.start(f"[{contract_name}] Phase 1: PII Detection")
        try:
            detections = detect_pii(contract.raw_text)
            p1.ok("PII found", len(detections))
            types = set(d.pii_type for d in detections)
            p1.ok("PII types", sorted(types))
            for d in detections[:5]:
                p1.ok(f"  {d.pii_type}", d.value[:30] + "...", f"Confidence: {d.confidence}")
            p1.done()
        except Exception as e:
            p1.fail(str(e))

        # Phase 2: Clause Extraction (Real LLM)
        p2 = tracker.start(f"[{contract_name}] Phase 2: Clause Extraction (Real LLM)")
        try:
            extractor = ClauseExtractor(llm_client=llm_client, generate_embeddings=True)
            extractor._embedding_service = embed_service  # Override with real embeddings
            clauses = await extractor.extract(contract)
            p2.ok("Clauses extracted", len(clauses))
            for c in clauses[:8]:
                p2.ok(f"  [{c.clause_type}] #{c.index}", c.text_content[:80] + "...")
                p2.ok(f"    Has embedding", c.embedding is not None, f"Dim: {len(c.embedding) if c.embedding else 0}")
            p2.done()
        except Exception as e:
            p2.fail(str(e))
            continue

        if not clauses:
            print(f"  ⚠️ No clauses for {contract_name}, skipping remaining phases")
            continue

        # Phase 3: Retrieval (THE MOST IMPORTANT PHASE)
        p3 = tracker.start(f"[{contract_name}] Phase 3: Legal Retrieval (Real Neo4j + Real Embeddings)")
        try:
            hybrid_retriever = LegalHybridRetriever(
                embedding_service=embed_service,
                top_k=20,
                return_top_n=5,
            )
            query_rewriter = QueryRewriter(llm_client=llm_client)

            clause_retrieval_results = []
            for clause in clauses:
                # Rewrite query
                plan = await query_rewriter.rewrite(clause)

                # Retrieve
                candidates = await hybrid_retriever.retrieve(plan)

                # Evaluate
                eval_result = evaluator.evaluate(plan, candidates, clause)
                clause_retrieval_results.append({
                    "clause_index": clause.index,
                    "clause_type": clause.clause_type,
                    "clause_text": clause.text_content[:100],
                    "plan": {
                        "source": plan.source,
                        "legal_issue": plan.legal_issue,
                        "keywords": plan.keywords,
                        "search_queries": plan.search_queries[:3],
                        "title_hints": plan.title_hints,
                        "confidence": plan.confidence,
                    },
                    "retrieval": eval_result,
                })

                p3.ok(f"Clause #{clause.index} [{clause.clause_type}]",
                      f"Grade: {eval_result['quality_grade']} (score={eval_result['quality_score']})",
                      f"{eval_result['num_candidates']} candidates from {eval_result['sources_used']}")
                if eval_result["top_citation"]:
                    p3.ok(f"  Top match", eval_result["top_citation"], f"Score: {eval_result['top_score']}")
                if eval_result["unique_documents"]:
                    p3.ok(f"  Documents", eval_result["document_diversity"], str(eval_result["unique_documents"][:3]))
                if eval_result["issues"]:
                    for issue in eval_result["issues"]:
                        p3.ok(f"  ⚠ Issue", "", issue)

            # Aggregate retrieval stats
            all_grades = [r["retrieval"]["quality_grade"] for r in clause_retrieval_results]
            all_scores = [r["retrieval"]["quality_score"] for r in clause_retrieval_results]
            all_candidates = [r["retrieval"]["num_candidates"] for r in clause_retrieval_results]

            grade_counts = {}
            for g in all_grades:
                grade_counts[g] = grade_counts.get(g, 0) + 1

            p3.ok("Retrieval summary", True)
            p3.ok("  Grade distribution", grade_counts)
            p3.ok("  Avg quality score", round(sum(all_scores) / len(all_scores), 1))
            p3.ok("  Avg candidates/clause", round(sum(all_candidates) / len(all_candidates), 1))

            all_retrieval_evals.extend(clause_retrieval_results)
            p3.done()

            hybrid_retriever.close()

        except Exception as e:
            p3.fail(str(e))
            import traceback
            traceback.print_exc()

        # Phase 4: Full Matcher (LegalMatcher)
        p4 = tracker.start(f"[{contract_name}] Phase 4: Legal Provision Matching")
        try:
            matcher = LegalMatcher(
                embedding_service=embed_service,
                top_k=20,
                return_top_n=5,
            )

            all_matches = []
            for clause in clauses[:5]:  # Test first 5 clauses
                plan, matches = await matcher.match_with_plan(clause)
                all_matches.extend(matches)
                p4.ok(f"Clause #{clause.index} [{clause.clause_type}]", len(matches), f"Plan source: {plan.source}")
                for m in matches[:3]:
                    p4.ok(f"  → {m.display_citation}", f"score={m.combined_score:.4f}",
                          f"doc: {m.document_so_ky_hieu} ({m.document_type})")

            p4.ok("Total matches", len(all_matches))
            p4.done()

        except Exception as e:
            p4.fail(str(e))
            import traceback
            traceback.print_exc()

        # Phase 5: Compliance Analysis (Real LLM)
        p5 = tracker.start(f"[{contract_name}] Phase 5: Compliance Analysis (Real LLM)")
        try:
            analyzer = ComplianceAnalyzer(llm_client=llm_client)

            # Build provisions from matches
            provisions = {}
            for clause in clauses[:5]:
                # Re-match to get provisions for each clause
                _, matches = await matcher.match_with_plan(clause)
                provisions[clause.id] = matches

            results = await analyzer.analyze_all(clauses[:5], provisions)

            total_violations = 0
            total_risks = 0
            total_suggestions = 0
            for clause_id, r in results.items():
                total_violations += len(r.violations)
                total_risks += len(r.risks)
                total_suggestions += len(r.suggestions)
                if r.violations:
                    for v in r.violations[:2]:
                        p5.ok(f"  ✗ Violation", f"[{v.severity}]", f"{v.description[:80]}")
                        p5.ok(f"    Citation", v.citation, f"Verified: {v.verified}")

            p5.ok("Violations found", total_violations)
            p5.ok("Risks found", total_risks)
            p5.ok("Suggestions", total_suggestions)
            p5.done()

        except Exception as e:
            p5.fail(str(e))
            import traceback
            traceback.print_exc()

        # Phase 6: Citation Verification (Real Neo4j)
        p6 = tracker.start(f"[{contract_name}] Phase 6: Citation Verification (Real Neo4j)")
        try:
            verifier = CitationVerifier()

            # Collect citations from compliance results
            all_citations = []
            for clause_id, r in results.items():
                for v in r.violations:
                    if v.citation:
                        all_citations.append(v.citation)

            if all_citations:
                verified_count = 0
                for cit in all_citations[:5]:
                    try:
                        vr = await verifier.verify(cit)
                        if vr.verified:
                            verified_count += 1
                        p6.ok(f"  {cit[:50]}", "✅" if vr.verified else "❌", vr.reason or "")
                    except Exception as e:
                        p6.ok(f"  {cit[:50]}", "❌ ERROR", str(e))

                p6.ok("Verified", f"{verified_count}/{min(5, len(all_citations))}")
            else:
                p6.ok("No citations to verify", True)

            p6.done()

        except Exception as e:
            p6.fail(str(e))

    # ── Final Summary ────────────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"  PIPELINE SUMMARY")
    print(f"{'='*70}")

    summary = tracker.summary()
    print(f"  Total phases: {summary['total_phases']}")
    print(f"  Passed: {summary['passed']}")
    print(f"  Failed: {summary['failed']}")
    print(f"  Total time: {summary['total_time_sec']:.1f}s")

    # ── Retrieval Quality Report ─────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"  RETRIEVAL QUALITY REPORT (Phase 3 — Most Important)")
    print(f"{'='*70}")

    if all_retrieval_evals:
        grades = [r["retrieval"]["quality_grade"] for r in all_retrieval_evals]
        scores = [r["retrieval"]["quality_score"] for r in all_retrieval_evals]
        avg_score = sum(scores) / len(scores)

        print(f"\n  Total clauses tested: {len(all_retrieval_evals)}")
        print(f"  Average quality score: {avg_score:.1f}/100")
        print(f"  Grade distribution:")
        for g in ["A", "B", "C", "D", "F"]:
            count = grades.count(g)
            if count:
                bar = "█" * count
                print(f"    {g}: {count} {bar}")

        print(f"\n  Source usage:")
        source_counts = {}
        for r in all_retrieval_evals:
            for s in r["retrieval"]["sources_used"]:
                source_counts[s] = source_counts.get(s, 0) + 1
        for s, c in sorted(source_counts.items(), key=lambda x: -x[1]):
            print(f"    {s}: {c}/{len(all_retrieval_evals)} clauses")

        print(f"\n  Plan quality:")
        llm_plans = sum(1 for r in all_retrieval_evals if r["plan"]["source"] == "llm")
        fallback_plans = sum(1 for r in all_retrieval_evals if r["plan"]["source"] == "fallback")
        print(f"    LLM-generated plans: {llm_plans}")
        print(f"    Fallback plans: {fallback_plans}")

        print(f"\n  Common issues:")
        issue_counts = {}
        for r in all_retrieval_evals:
            for issue in r["retrieval"]["issues"]:
                issue_counts[issue] = issue_counts.get(issue, 0) + 1
        for issue, count in sorted(issue_counts.items(), key=lambda x: -x[1]):
            print(f"    ⚠ {issue} ({count}x)")

        print(f"\n  Detailed per-clause results:")
        for r in all_retrieval_evals:
            print(f"\n    Clause #{r['clause_index']} [{r['clause_type']}]:")
            print(f"      Text: {r['clause_text']}...")
            print(f"      Plan: {r['plan']['source']} (issue: {r['plan']['legal_issue']})")
            print(f"      Keywords: {r['plan']['keywords']}")
            print(f"      Grade: {r['retrieval']['quality_grade']} (score={r['retrieval']['quality_score']})")
            print(f"      Candidates: {r['retrieval']['num_candidates']}")
            print(f"      Sources: {r['retrieval']['sources_used']}")
            print(f"      Avg vector: {r['retrieval']['avg_vector_score']:.4f}")
            print(f"      Top: {r['retrieval']['top_citation']} (score={r['retrieval']['top_score']})")
            print(f"      Documents: {r['retrieval']['unique_documents'][:3]}")
            if r['retrieval']['issues']:
                print(f"      Issues: {r['retrieval']['issues']}")

    # ── Save report ──────────────────────────────────────────────────────────
    report = {
        "summary": summary,
        "retrieval_evaluations": all_retrieval_evals,
    }

    output_dir = Path(__file__).resolve().parent.parent / "output"
    output_dir.mkdir(exist_ok=True)
    report_path = output_dir / "full_pipeline_test_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n  📄 Report saved to: {report_path}")

    return report


if __name__ == "__main__":
    asyncio.run(run_full_pipeline())
