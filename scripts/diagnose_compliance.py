#!/usr/bin/env python3
"""Diagnostic script to see what provisions are retrieved and what LLM outputs."""
import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["GRAPH_REPOSITORY_MODE"] = "neo4j"
os.environ["EMBEDDING_SERVICE_MODE"] = "real"
os.environ["LLM_PROVIDER"] = "openai"

async def main():
    from src.contract.review_pipeline import ContractReviewPipeline
    from src.contract.compliance_analyzer import ComplianceAnalyzer
    from src.contract.matcher import LegalMatcher
    from src.contract.clause_extractor import ClauseExtractor
    from src.contract.parser import ContractParser
    
    filepath = "data/sample_contracts/sample_hop_dong_lao_dong.md"
    print(f"Diagnostic: {filepath}\n")
    
    parser = ContractParser()
    extractor = ClauseExtractor()
    matcher = LegalMatcher()
    analyzer = ComplianceAnalyzer()
    
    # Parse
    contract = parser.parse(filepath)
    print(f"Parsed: {len(contract.raw_text)} chars\n")
    
    # Extract clauses
    clauses = await extractor.extract(contract)
    print(f"Extracted {len(clauses)} clauses\n")
    
    # For each clause, show matches and compliance analysis
    for i, clause in enumerate(clauses, 1):
        print(f"{'='*70}")
        print(f"CLAUSE {i}: [{clause.clause_type}]")
        print(f"Text: {clause.text_content[:100]}...")
        print(f"{'='*70}")
        
        # Get matches
        plan, matches = await matcher.match_with_plan(clause)
        print(f"\nRetrieved {len(matches)} provisions:")
        for j, match in enumerate(matches, 1):
            print(f"  {j}. {match.display_citation} (score: {match.combined_score:.3f})")
            print(f"     Text: {match.effective_text or match.article_text[:150]}...")
        
        # Get compliance analysis
        compliance = await analyzer.analyze(clause, matches)
        print(f"\nLLM Output:")
        print(f"  Status: {compliance.compliance_status}")
        print(f"  Summary: {compliance.summary}")
        print(f"  Violations: {len(compliance.violations)}")
        for v in compliance.violations:
            print(f"    ✗ {v.clause}: {v.description}")
            print(f"      Citation: {v.citation}")
        print(f"  Risks: {len(compliance.risks)}")
        for r in compliance.risks:
            print(f"    ⚠ {r}")
        print(f"  Suggestions: {len(compliance.suggestions)}")
        for s in compliance.suggestions:
            print(f"    → {s}")
        print(f"  Citations: {len(compliance.citations)}")
        print()

if __name__ == "__main__":
    asyncio.run(main())
