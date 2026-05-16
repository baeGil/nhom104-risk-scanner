#!/usr/bin/env python3
"""
Contract Review Pipeline — End-to-End Test with Real Neo4j Data.
Logs each phase with timing and results.

Usage:
    python scripts/test_contract_pipeline.py
"""

import os
import sys
import json
import time
import asyncio
import logging
import uuid

# Force real Neo4j mode
os.environ["GRAPH_REPOSITORY_MODE"] = "neo4j"
os.environ["EMBEDDING_SERVICE_MODE"] = "real"
os.environ["EFFECTIVE_TEXT_SERVICE_MODE"] = "mock"
os.environ["LLM_PROVIDER"] = "mock"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neo4j import GraphDatabase
from src.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

SAMPLE_CONTRACT = "data/sample_contracts/sample_hop_dong_thue.md"
RESULTS = {}


def log_phase(name: str):
    print(f"\n{'='*60}")
    print(f"  PHASE: {name}")
    print(f"{'='*60}")


def log_result(key: str, value, detail=""):
    RESULTS[key] = value
    status = "✅" if value else "❌"
    print(f"  {status} {key}: {value}")
    if detail:
        print(f"     {detail}")


def neo4j_session():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    return driver.session()


# ─── Phase 0: Contract Parsing ───────────────────────────────────────────────
def phase_0_parse():
    log_phase("0. Contract Parsing")
    t0 = time.time()

    if not os.path.exists(SAMPLE_CONTRACT):
        log_result("Parse", False, f"File not found: {SAMPLE_CONTRACT}")
        return None

    with open(SAMPLE_CONTRACT, "r", encoding="utf-8") as f:
        raw_text = f.read()

    word_count = len(raw_text.split())
    char_count = len(raw_text)

    import re
    clause_titles = re.findall(r"## (ĐIỀU \d+[:\.]?.*?)\n", raw_text)

    elapsed = time.time() - t0
    log_result("File loaded", True, f"{char_count} chars, {word_count} words")
    log_result("Clauses detected", len(clause_titles), f"{clause_titles}")
    log_result("Parse time", f"{elapsed:.3f}s")

    return raw_text


# ─── Phase 1: PII Detection & Redaction ──────────────────────────────────────
def phase_1_pii(raw_text):
    log_phase("1. PII Detection & Redaction")
    t0 = time.time()

    from src.contract.pii import detect_pii, redact_pii

    detections = detect_pii(raw_text)

    elapsed = time.time() - t0
    types_found = set(d.pii_type for d in detections) if detections else set()
    log_result("PII detections", len(detections), f"Types: {types_found}")
    log_result("PII scan time", f"{elapsed:.3f}s")

    if detections:
        redacted_text, pii_map = redact_pii(raw_text, detections)
        log_result("Redaction", True, f"{len(pii_map)} placeholders created")
        return redacted_text, pii_map
    else:
        log_result("Redaction skipped", True, "No PII found in sample contract")
        return raw_text, {}


# ─── Phase 2: Clause Extraction (Mock LLM) ───────────────────────────────────
async def phase_2_extract_clauses(redacted_text):
    log_phase("2. Clause Extraction (Mock LLM)")
    t0 = time.time()

    from src.contract.clause_extractor import ClauseExtractor
    from src.contract.models import Contract
    from src.llm.mock_provider import MockLLMProvider

    contract = Contract(
        id=str(uuid.uuid4()),
        raw_text=redacted_text,
        redacted_text=redacted_text,
        source_format="txt",
        upload_date="2026-05-16",
        pii_map={},
    )

    llm = MockLLMProvider()
    extractor = ClauseExtractor(llm_client=llm)

    try:
        clauses = await extractor.extract(contract)
        elapsed = time.time() - t0
        log_result("Clauses extracted", len(clauses))
        log_result("Extraction time", f"{elapsed:.3f}s")

        for c in clauses[:5]:
            print(f"    - [{c.clause_type}] {c.text_content[:60]}...")
        return clauses
    except Exception as e:
        elapsed = time.time() - t0
        log_result("Clause extraction", False, str(e))
        log_result("Extraction time", f"{elapsed:.3f}s")
        return []


# ─── Phase 3: Legal Provision Matching (Real Neo4j) ──────────────────────────
async def phase_3_match(clauses):
    log_phase("3. Legal Provision Matching (Real Neo4j)")
    t0 = time.time()

    from src.contract.matcher import LegalMatcher

    matcher = LegalMatcher(top_k=5)

    all_matches = []
    for clause in clauses[:3]:
        try:
            matches = await matcher.match(clause)
            all_matches.extend(matches)
            print(f"    Clause [{clause.clause_type}]: {len(matches)} matches")
            for m in matches[:2]:
                print(f"      → {m.document_so_ky_hieu} / {m.article_uid} (score={m.combined_score:.3f})")
        except Exception as e:
            print(f"    Clause [{clause.clause_type}]: ERROR — {e}")

    elapsed = time.time() - t0
    log_result("Total matches", len(all_matches), f"Across {min(3, len(clauses))} clauses")
    log_result("Matching time", f"{elapsed:.3f}s")
    return all_matches


# ─── Phase 4: Compliance Analysis (Mock LLM) ─────────────────────────────────
async def phase_4_compliance(clauses, matches):
    log_phase("4. Compliance Analysis (Mock LLM)")
    t0 = time.time()

    from src.contract.compliance_analyzer import ComplianceAnalyzer
    from src.llm.mock_provider import MockLLMProvider

    llm = MockLLMProvider()
    analyzer = ComplianceAnalyzer(llm_client=llm)

    # Build provisions dict: clause_id -> list of matches
    provisions = {}
    for clause in clauses:
        provisions[clause.id] = [m for m in matches if True]  # all matches for demo

    try:
        results = await analyzer.analyze_all(clauses, provisions)
        elapsed = time.time() - t0

        all_violations = []
        all_risks = []
        all_suggestions = []
        for clause_id, r in results.items():
            all_violations.extend(r.violations)
            all_risks.extend(r.risks)
            all_suggestions.extend(r.suggestions)

        log_result("Clauses analyzed", len(results))
        log_result("Violations found", len(all_violations))
        for v in all_violations[:3]:
            print(f"    ✗ {v.clause}: {v.description[:80]}")
            print(f"      Citation: {v.citation} (verified={v.verified})")

        log_result("Risks", len(all_risks))
        for r_text in all_risks[:3]:
            print(f"    ⚠ {r_text}")

        log_result("Suggestions", len(all_suggestions))
        for s in all_suggestions[:3]:
            print(f"    → {s}")

        log_result("Analysis time", f"{elapsed:.3f}s")
        return results
    except Exception as e:
        elapsed = time.time() - t0
        log_result("Compliance analysis", False, str(e))
        log_result("Analysis time", f"{elapsed:.3f}s")
        return {}


# ─── Phase 5: Citation Verification (Real Neo4j) ─────────────────────────────
async def phase_5_verify_citations(compliance_results):
    log_phase("5. Citation Verification (Real Neo4j)")
    t0 = time.time()

    from src.llm.citation_verifier import CitationVerifier

    verifier = CitationVerifier()

    all_violations = []
    for clause_id, r in compliance_results.items():
        all_violations.extend(r.violations)

    if not all_violations:
        log_result("Citations to verify", 0, "No violations with citations")
        return

    for v in all_violations:
        try:
            verified = await verifier.verify(v.citation)
            v.verified = verified.verified
            status = "✅ VERIFIED" if verified.verified else "❌ UNVERIFIED"
            print(f"    \"{v.citation}\" → {status}")
            if verified.article_uid:
                print(f"       Article: {verified.article_uid}")
        except Exception as e:
            print(f"    \"{v.citation}\" → ERROR: {e}")

    elapsed = time.time() - t0
    verified_count = sum(1 for v in all_violations if v.verified)
    log_result("Verified", f"{verified_count}/{len(all_violations)}")
    log_result("Verification time", f"{elapsed:.3f}s")


# ─── Phase 6: Policy Review (Mock LLM) ───────────────────────────────────────
async def phase_6_policy(clauses, matches):
    log_phase("6. Policy Review (Mock LLM)")
    t0 = time.time()

    from src.contract.policy_review import PolicyReview
    from src.llm.mock_provider import MockLLMProvider

    llm = MockLLMProvider()
    reviewer = PolicyReview(llm_client=llm)

    provisions = {}
    for clause in clauses:
        provisions[clause.id] = [m for m in matches if True]

    try:
        result = await reviewer.review(clauses, provisions)
        elapsed = time.time() - t0

        log_result("Classification", result.category)
        log_result("Restrictive clauses", len(result.restrictive_clauses))
        for rc in result.restrictive_clauses[:3]:
            print(f"    ⚠ {rc.clause_text[:60]}... (reason: {rc.reason})")
        log_result("Policy review time", f"{elapsed:.3f}s")
        return result
    except Exception as e:
        elapsed = time.time() - t0
        log_result("Policy review", False, str(e))
        log_result("Review time", f"{elapsed:.3f}s")
        return None


# ─── Main ─────────────────────────────────────────────────────────────────────
async def main():
    print("\n" + "█" * 60)
    print("  Contract Review Pipeline — Real Neo4j Test")
    print("█" * 60)

    # Verify Neo4j connection
    try:
        with neo4j_session() as s:
            r = s.run("MATCH (d:Document) RETURN count(d) as cnt")
            doc_count = r.single()["cnt"]
            r2 = s.run("MATCH (a:Article) RETURN count(a) as cnt")
            art_count = r2.single()["cnt"]
            r3 = s.run("MATCH (a:Article) WHERE a.embedding IS NOT NULL RETURN count(a) as cnt")
            emb_count = r3.single()["cnt"]
            print(f"\n  Neo4j: {doc_count} docs, {art_count} articles, {emb_count} embedded")
    except Exception as e:
        print(f"\n  ❌ Neo4j connection failed: {e}")
        sys.exit(1)

    # Phase 0: Parse
    raw = phase_0_parse()
    if not raw:
        print("\n❌ Pipeline aborted: parsing failed")
        return

    # Phase 1: PII
    redacted, pii_map = phase_1_pii(raw)

    # Phase 2: Extract clauses (async)
    clauses = await phase_2_extract_clauses(redacted)
    if not clauses:
        print("\n❌ Pipeline aborted: no clauses extracted")
        return

    # Phase 3: Match provisions (async, real Neo4j)
    matches = await phase_3_match(clauses)

    # Phase 4: Compliance analysis (async)
    compliance_results = await phase_4_compliance(clauses, matches)

    # Phase 5: Verify citations (async, real Neo4j)
    if compliance_results:
        await phase_5_verify_citations(compliance_results)

    # Phase 6: Policy review (async)
    await phase_6_policy(clauses, matches)

    # Summary
    print(f"\n{'='*60}")
    print(f"  PIPELINE SUMMARY")
    print(f"{'='*60}")
    for k, v in RESULTS.items():
        status = "✅" if v and v not in (False, 0, "") else "⚠️"
        print(f"  {status} {k}: {v}")

    total_phases = len([v for v in RESULTS.values() if v and v not in (False, 0, "")])
    print(f"\n  {total_phases}/{len(RESULTS)} phases completed successfully")
    print()


if __name__ == "__main__":
    asyncio.run(main())
