#!/usr/bin/env python3
"""Quick test of labor contract review pipeline."""
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
    
    filepath = "data/sample_contracts/sample_hop_dong_lao_dong.md"
    print(f"Testing: {filepath}\n")
    
    pipeline = ContractReviewPipeline()
    result = await pipeline.review_file(filepath)
    
    # Summary
    print(f"{'='*60}")
    print(f"CLAUSES: {len(result.clauses)}")
    print(f"{'='*60}")
    for item in result.clauses:
        clause = item.clause
        compliance = item.compliance
        violations = compliance.violations if compliance else []
        risks = compliance.risks if compliance else []
        suggestions = compliance.suggestions if compliance else []
        
        print(f"\n[{clause.clause_type}] {clause.text_content[:80]}...")
        print(f"  Matches: {len(item.matches)}")
        print(f"  Citations: {len(item.citations)}")
        print(f"  Verified: {sum(1 for v in item.verification_results if v.verified)}/{len(item.verification_results)}")
        
        if violations:
            print(f"  VIOLATIONS ({len(violations)}):")
            for v in violations:
                print(f"    ✗ {v.clause}: {v.description}")
                print(f"      Citation: {v.citation} (severity: {v.severity}, verified: {v.verified})")
        
        if risks:
            print(f"  RISKS ({len(risks)}):")
            for r in risks:
                print(f"    ⚠ {r}")
        
        if suggestions:
            print(f"  SUGGESTIONS ({len(suggestions)}):")
            for s in suggestions:
                print(f"    → {s}")
    
    # Full JSON output
    print(f"\n{'='*60}")
    print("FULL JSON OUTPUT")
    print(f"{'='*60}")
    
    output = {
        "clauses": [],
        "total_violations": 0,
        "total_risks": 0,
        "total_suggestions": 0,
        "total_citations": 0,
        "total_verified": 0,
    }
    
    for item in result.clauses:
        clause_data = {
            "id": item.clause.id,
            "type": item.clause.clause_type,
            "text": item.clause.text_content,
            "matches_count": len(item.matches),
            "citations_count": len(item.citations),
        }
        
        if item.compliance:
            clause_data["compliance"] = {
                "violations": [
                    {
                        "clause": v.clause,
                        "description": v.description,
                        "citation": v.citation,
                        "severity": v.severity,
                        "verified": v.verified,
                    }
                    for v in item.compliance.violations
                ],
                "risks": item.compliance.risks,
                "suggestions": item.compliance.suggestions,
            }
            output["total_violations"] += len(item.compliance.violations)
            output["total_risks"] += len(item.compliance.risks)
            output["total_suggestions"] += len(item.compliance.suggestions)
        
        clause_data["citations"] = [
            {
                "displayText": c.display_text,
                "uid": c.uid,
                "verified": v.verified,
                "reason": v.reason,
            }
            for c, v in zip(item.citations, item.verification_results)
        ]
        output["total_citations"] += len(item.citations)
        output["total_verified"] += sum(1 for v in item.verification_results if v.verified)
        
        output["clauses"].append(clause_data)
    
    print(json.dumps(output, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
