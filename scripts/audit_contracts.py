#!/usr/bin/env python3
"""
Contract Review Pipeline — Multi-Contract Audit.
Runs all 3 sample contracts through the pipeline, logs each phase, and produces a summary report.

Usage:
    python scripts/audit_contracts.py
"""

import os
import sys
import json
import time
import asyncio
import logging
import uuid
from datetime import datetime

os.environ["GRAPH_REPOSITORY_MODE"] = "neo4j"
os.environ["EMBEDDING_SERVICE_MODE"] = "real"
os.environ["EFFECTIVE_TEXT_SERVICE_MODE"] = "mock"
os.environ["LLM_PROVIDER"] = "mock"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neo4j import GraphDatabase
from src.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

SAMPLE_CONTRACTS = [
    "data/sample_contracts/sample_hop_dong_thue.md",
    "data/sample_contracts/sample_hop_dong_lao_dong.md",
    "data/sample_contracts/sample_hop_dong_mua_ban.md",
]

CONTRACT_NAMES = {
    "sample_hop_dong_thue.md": "Hợp đồng thuê văn phòng",
    "sample_hop_dong_lao_dong.md": "Hợp đồng lao động",
    "sample_hop_dong_mua_ban.md": "Hợp đồng mua bán",
}

ALL_RESULTS = {}


def log_phase(name: str):
    print(f"\n{'='*60}")
    print(f"  PHASE: {name}")
    print(f"{'='*60}")


def log_result(contract_key: str, phase: str, key: str, value, detail=""):
    if contract_key not in ALL_RESULTS:
        ALL_RESULTS[contract_key] = {}
    if phase not in ALL_RESULTS[contract_key]:
        ALL_RESULTS[contract_key][phase] = {}
    ALL_RESULTS[contract_key][phase][key] = {"value": value, "detail": detail}
    status = "PASS" if value and value not in (False, 0, "") else "FAIL"
    print(f"  [{status}] {key}: {value}")
    if detail:
        print(f"         {detail}")


def neo4j_session():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    return driver.session()


def phase_0_parse(file_path: str, contract_key: str):
    log_phase("0. Contract Parsing")
    t0 = time.time()

    if not os.path.exists(file_path):
        log_result(contract_key, "parse", "File loaded", False, f"File not found: {file_path}")
        return None

    with open(file_path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    word_count = len(raw_text.split())
    char_count = len(raw_text)

    import re
    clause_titles = re.findall(r"## (ĐIỀU \d+[:\.]?.*?)\n", raw_text)

    elapsed = time.time() - t0
    log_result(contract_key, "parse", "File loaded", True, f"{char_count} chars, {word_count} words")
    log_result(contract_key, "parse", "Clauses detected", len(clause_titles), f"{clause_titles}")
    log_result(contract_key, "parse", "Parse time", f"{elapsed:.3f}s")

    return raw_text


def phase_1_pii(raw_text, contract_key: str):
    log_phase("1. PII Detection & Redaction")
    t0 = time.time()

    from src.contract.pii import detect_pii, redact_pii

    detections = detect_pii(raw_text)

    elapsed = time.time() - t0
    types_found = set(d.pii_type for d in detections) if detections else set()
    log_result(contract_key, "pii", "PII detections", len(detections), f"Types: {types_found}")
    log_result(contract_key, "pii", "PII scan time", f"{elapsed:.3f}s")

    if detections:
        redacted_text, pii_map = redact_pii(raw_text, detections)
        log_result(contract_key, "pii", "Redaction", True, f"{len(pii_map)} placeholders created")
        for d in detections:
            print(f"    - {d.pii_type}: {d.value[:30]}...")
        return redacted_text, pii_map
    else:
        log_result(contract_key, "pii", "Redaction skipped", True, "No PII found")
        return raw_text, {}


async def phase_2_extract_clauses(redacted_text, contract_key: str):
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
        log_result(contract_key, "extract", "Clauses extracted", len(clauses))
        log_result(contract_key, "extract", "Extraction time", f"{elapsed:.3f}s")

        for c in clauses[:5]:
            print(f"    - [{c.clause_type}] {c.text_content[:60]}...")
        return clauses
    except Exception as e:
        elapsed = time.time() - t0
        log_result(contract_key, "extract", "Clause extraction", False, str(e))
        log_result(contract_key, "extract", "Extraction time", f"{elapsed:.3f}s")
        return []


async def phase_3_match(clauses, contract_key: str):
    log_phase("3. Legal Provision Matching (Real Neo4j)")
    t0 = time.time()

    from src.contract.matcher import LegalMatcher

    matcher = LegalMatcher(top_k=5)

    all_matches = []
    clauses_to_match = clauses[:3]
    for clause in clauses_to_match:
        try:
            matches = await matcher.match(clause)
            all_matches.extend(matches)
            print(f"    Clause [{clause.clause_type}]: {len(matches)} matches")
            for m in matches[:2]:
                print(f"      → {m.document_so_ky_hieu} / {m.article_uid} (score={m.combined_score:.3f})")
        except Exception as e:
            print(f"    Clause [{clause.clause_type}]: ERROR — {e}")

    elapsed = time.time() - t0
    log_result(contract_key, "match", "Total matches", len(all_matches), f"Across {len(clauses_to_match)} clauses")
    log_result(contract_key, "match", "Matching time", f"{elapsed:.3f}s")
    return all_matches


async def phase_4_compliance(clauses, matches, contract_key: str):
    log_phase("4. Compliance Analysis (Mock LLM)")
    t0 = time.time()

    from src.contract.compliance_analyzer import ComplianceAnalyzer
    from src.llm.mock_provider import MockLLMProvider

    llm = MockLLMProvider()
    analyzer = ComplianceAnalyzer(llm_client=llm)

    provisions = {}
    for clause in clauses:
        provisions[clause.id] = [m for m in matches if True]

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

        log_result(contract_key, "compliance", "Clauses analyzed", len(results))
        log_result(contract_key, "compliance", "Violations found", len(all_violations))
        for v in all_violations[:3]:
            print(f"    ✗ {v.clause}: {v.description[:80]}")
            print(f"      Citation: {v.citation} (verified={v.verified})")

        log_result(contract_key, "compliance", "Risks", len(all_risks))
        for r_text in all_risks[:3]:
            print(f"    ⚠ {r_text}")

        log_result(contract_key, "compliance", "Suggestions", len(all_suggestions))
        for s in all_suggestions[:3]:
            print(f"    → {s}")

        log_result(contract_key, "compliance", "Analysis time", f"{elapsed:.3f}s")
        return results
    except Exception as e:
        elapsed = time.time() - t0
        log_result(contract_key, "compliance", "Compliance analysis", False, str(e))
        log_result(contract_key, "compliance", "Analysis time", f"{elapsed:.3f}s")
        return {}


async def phase_5_verify_citations(compliance_results, contract_key: str):
    log_phase("5. Citation Verification (Real Neo4j)")
    t0 = time.time()

    from src.llm.citation_verifier import CitationVerifier

    verifier = CitationVerifier()

    all_violations = []
    for clause_id, r in compliance_results.items():
        all_violations.extend(r.violations)

    if not all_violations:
        log_result(contract_key, "verify", "Citations to verify", 0, "No violations with citations")
        return

    verified_count = 0
    for v in all_violations:
        try:
            verified = await verifier.verify(v.citation)
            v.verified = verified.verified
            if verified.verified:
                verified_count += 1
            status = "PASS" if verified.verified else "FAIL"
            print(f"    \"{v.citation}\" → [{status}]")
            if verified.article_uid:
                print(f"       Article: {verified.article_uid}")
        except Exception as e:
            print(f"    \"{v.citation}\" → ERROR: {e}")

    elapsed = time.time() - t0
    log_result(contract_key, "verify", "Verified", f"{verified_count}/{len(all_violations)}")
    log_result(contract_key, "verify", "Verification time", f"{elapsed:.3f}s")


async def phase_6_policy(clauses, matches, contract_key: str):
    log_phase("6. Policy Review (Mock LLM)")
    t0 = time.time()

    from src.contract.policy_review import PolicyReview
    from src.llm.mock_provider import MockLLMProvider

    llm = MockLLMProvider()
    reviewer = PolicyReview()

    provisions = {}
    for clause in clauses:
        provisions[clause.id] = [m for m in matches if True]

    try:
        result = await reviewer.review(clauses, provisions)
        elapsed = time.time() - t0

        log_result(contract_key, "policy", "Classification summary", json.dumps(result.summary, ensure_ascii=False))
        log_result(contract_key, "policy", "Provisions reviewed", len(result.provisions))
        log_result(contract_key, "policy", "Policy review time", f"{elapsed:.3f}s")
        return result
    except Exception as e:
        elapsed = time.time() - t0
        log_result(contract_key, "policy", "Policy review", False, str(e))
        log_result(contract_key, "policy", "Review time", f"{elapsed:.3f}s")
        return None


async def run_contract(file_path: str):
    basename = os.path.basename(file_path)
    contract_key = basename.replace(".md", "")
    contract_name = CONTRACT_NAMES.get(basename, basename)

    print(f"\n{'█'*60}")
    print(f"  Contract: {contract_name} ({basename})")
    print(f"{'█'*60}")

    # Phase 0: Parse
    raw = phase_0_parse(file_path, contract_key)
    if not raw:
        print(f"\n  ABORTED: parsing failed for {basename}")
        return None

    # Phase 1: PII
    redacted, pii_map = phase_1_pii(raw, contract_key)

    # Phase 2: Extract clauses
    clauses = await phase_2_extract_clauses(redacted, contract_key)
    if not clauses:
        print(f"\n  ABORTED: no clauses extracted for {basename}")
        return None

    # Phase 3: Match provisions
    matches = await phase_3_match(clauses, contract_key)

    # Phase 4: Compliance analysis
    compliance_results = await phase_4_compliance(clauses, matches, contract_key)

    # Phase 5: Verify citations
    if compliance_results:
        await phase_5_verify_citations(compliance_results, contract_key)

    # Phase 6: Policy review
    await phase_6_policy(clauses, matches, contract_key)

    return contract_key


def print_summary():
    print(f"\n{'='*80}")
    print(f"  OVERALL PIPELINE SUMMARY")
    print(f"{'='*80}")

    phases = ["parse", "pii", "extract", "match", "compliance", "verify", "policy"]
    phase_names = {
        "parse": "Parsing",
        "pii": "PII Detection",
        "extract": "Clause Extraction",
        "match": "Provision Matching",
        "compliance": "Compliance Analysis",
        "verify": "Citation Verification",
        "policy": "Policy Review",
    }

    # Header
    print(f"\n  {'Contract':<35}", end="")
    for p in phases:
        print(f" {phase_names[p]:<18}", end="")
    print()
    print(f"  {'-'*35}", end="")
    for p in phases:
        print(f" {'-'*18}", end="")
    print()

    for contract_key, phases_data in ALL_RESULTS.items():
        name = CONTRACT_NAMES.get(contract_key + ".md", contract_key)
        print(f"  {name:<35}", end="")
        for p in phases:
            if p in phases_data:
                phase_data = phases_data[p]
                # Find the main result key
                main_key = list(phase_data.keys())[0]
                val = phase_data[main_key]["value"]
                status = "PASS" if val and val not in (False, 0, "") else "FAIL"
                print(f" {status:<18}", end="")
            else:
                print(f" {'N/A':<18}", end="")
        print()

    # Detailed per-contract results
    print(f"\n{'='*80}")
    print(f"  DETAILED RESULTS")
    print(f"{'='*80}")

    for contract_key, phases_data in ALL_RESULTS.items():
        name = CONTRACT_NAMES.get(contract_key + ".md", contract_key)
        print(f"\n  ── {name} ──")
        for phase, results in phases_data.items():
            print(f"\n  [{phase_names.get(phase, phase)}]")
            for key, data in results.items():
                status = "PASS" if data["value"] and data["value"] not in (False, 0, "") else "FAIL"
                print(f"    [{status}] {key}: {data['value']}")
                if data["detail"]:
                    print(f"           {data['detail']}")


async def main():
    print("\n" + "█" * 80)
    print("  Contract Review Pipeline — Multi-Contract Audit")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("█" * 80)

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
        print(f"\n  Neo4j connection failed: {e}")
        sys.exit(1)

    total_start = time.time()

    for file_path in SAMPLE_CONTRACTS:
        await run_contract(file_path)

    total_elapsed = time.time() - total_start

    # Summary
    print_summary()

    print(f"\n  Total pipeline time: {total_elapsed:.3f}s")
    print(f"  Contracts processed: {len(ALL_RESULTS)}/{len(SAMPLE_CONTRACTS)}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
