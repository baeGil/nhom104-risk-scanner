"""Contract review API routes."""
from __future__ import annotations

import asyncio
import logging
import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File
from neo4j import GraphDatabase

from infra.api.models import JobStatusResponse, ContractClauseResponse, ComplianceResultResponse, LegalMatchResponse, CitationResponse
from infra.api.job_store import job_store
from src.contract.review_pipeline import ContractReviewPipeline, ContractReviewPipelineError
from src.config import NEO4J_URI, neo4j_auth

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/upload", response_model=dict)
async def upload_contract(file: UploadFile = File(...)):
    """
    Upload a contract file for review.

    Returns a jobId for async processing.
    """
    # Validate file type
    allowed_types = {".pdf", ".docx", ".txt", ".md"}
    file_ext = Path(file.filename or "").suffix.lower()
    if file_ext not in allowed_types:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_ext}. Allowed: {allowed_types}")

    # Validate file size (10MB max)
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum size: 10MB")

    # Create job
    job_id = job_store.create_job(filename=file.filename or "unknown")

    # Start async processing
    asyncio.create_task(process_contract(job_id, content, file.filename or "unknown"))

    return {"jobId": job_id}


@router.get("/{job_id}/status")
async def get_job_status(job_id: str):
    """Get the status of a contract review job."""
    job = job_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobStatusResponse(
        jobId=job.job_id,
        status=job.status,
        progress=job.progress,
        filename=job.filename,
        createdAt=job.created_at,
        clauses=[ContractClauseResponse(**c) for c in job.clauses] if job.clauses else None,
        matches=[LegalMatchResponse(**m) for m in job.matches] if job.matches else None,
        compliance=ComplianceResultResponse(**job.compliance) if job.compliance else None,
        citations=[CitationResponse(**c) for c in job.citations] if job.citations else None,
        error=job.error,
    )


@router.get("/history")
async def get_job_history():
    """Get all contract review jobs."""
    jobs = job_store.get_all_jobs()
    return [
        JobStatusResponse(
            jobId=j.job_id,
            status=j.status,
            progress=j.progress,
            filename=j.filename,
            createdAt=j.created_at,
            error=j.error,
        )
        for j in jobs
    ]


@router.get("/documents/{doc_title}")
async def get_document_content(doc_title: str):
    """Get full content of a legal document by title."""
    driver = GraphDatabase.driver(NEO4J_URI, auth=neo4j_auth())
    try:
        with driver.session(default_access_mode="READ", database="neo4j") as session:
            # Get document metadata and all articles/clauses/points
            result = session.run("""
            MATCH (doc:Document)
            WHERE doc.title = $title
            OPTIONAL MATCH (doc)-[:HAS_ARTICLE]->(article:Article)
            OPTIONAL MATCH (article)-[:HAS_CLAUSE]->(clause:Clause)
            OPTIONAL MATCH (clause)-[:HAS_POINT]->(point:Point)
            RETURN doc, collect(DISTINCT article) as articles, collect(DISTINCT clause) as clauses, collect(DISTINCT point) as points
            """, title=doc_title)
            
            record = result.single()
            if not record:
                raise HTTPException(status_code=404, detail="Document not found")
            
            doc = dict(record["doc"])
            articles = [dict(a) for a in record["articles"] if a]
            clauses = [dict(c) for c in record["clauses"] if c]
            points = [dict(p) for p in record["points"] if p]
            
            # Build structured content
            content = {
                "title": doc.get("title", ""),
                "so_ky_hieu": doc.get("so_ky_hieu", ""),
                "loai_van_ban": doc.get("loai_van_ban", ""),
                "ngay_ban_hanh": doc.get("ngay_ban_hanh", ""),
                "co_quan_ban_hanh": doc.get("co_quan_ban_hanh", ""),
                "articles": []
            }
            
            # Group clauses and points by article
            article_map = {}
            for article in articles:
                article_map[article["uid"]] = {
                    "uid": article["uid"],
                    "index": article.get("index", 0),
                    "title": article.get("title", ""),
                    "text": article.get("clean_text", ""),
                    "clauses": []
                }
            
            for clause in clauses:
                article_uid = clause.get("article_uid", "")
                if article_uid in article_map:
                    article_map[article_uid]["clauses"].append({
                        "uid": clause["uid"],
                        "index": clause.get("index", 0),
                        "text": clause.get("clean_text", ""),
                        "points": []
                    })
            
            for point in points:
                clause_uid = point.get("clause_uid", "")
                for article_data in article_map.values():
                    for clause_data in article_data["clauses"]:
                        if clause_data["uid"] == clause_uid:
                            clause_data["points"].append({
                                "uid": point["uid"],
                                "letter": point.get("letter", ""),
                                "text": point.get("clean_text", "")
                            })
            
            content["articles"] = list(article_map.values())
            content["articles"].sort(key=lambda x: x["index"])
            
            return content
    finally:
        driver.close()


async def process_contract(job_id: str, content: bytes, filename: str):
    """
    Process a contract file asynchronously.

    Pipeline: parsing → clause extraction → query rewrite → hybrid retrieval → compliance analysis → verification
    """
    try:
        if os.getenv("CONTRACT_REVIEW_USE_MOCK", "").lower() in {"1", "true", "yes"}:
            await process_contract_mock(job_id)
            return

        suffix = Path(filename).suffix.lower() or ".txt"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        job_store.update_job(job_id, status="parsing", progress=10)
        pipeline = ContractReviewPipeline()
        result = await pipeline.review_file(tmp_path)
        payload = serialize_review_result(result)

        job_store.update_job(
            job_id,
            status="completed",
            progress=100,
            clauses=payload["clauses"],
            matches=payload["matches"],
            compliance=payload["compliance"],
            citations=payload["citations"],
        )

    except ContractReviewPipelineError as e:
        logger.error(f"Job {job_id} failed at {e.stage}: {e}")
        job_store.update_job(job_id, status="failed", progress=0, error=str(e))
    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        job_store.update_job(job_id, status="failed", progress=0, error=str(e))


def serialize_review_result(result) -> dict:
    clauses = []
    matches = []
    citations = []
    all_violations = []
    all_risks = []
    all_suggestions = []
    clause_compliance = []

    for item in result.clauses:
        violations = item.compliance.violations if item.compliance else []
        severities = [v.severity for v in violations if hasattr(v, 'severity')]
        if "high" in severities:
            risk_level = "high"
        elif "medium" in severities:
            risk_level = "medium"
        elif violations:
            risk_level = "low"
        else:
            risk_level = "low"

        clause_data = {
            "id": item.clause.id,
            "type": item.clause.clause_type,
            "text": item.clause.text_content,
            "riskLevel": risk_level,
        }

        # Add per-clause compliance data
        if item.compliance:
            clause_data["compliance"] = {
                "status": item.compliance.compliance_status,
                "summary": item.compliance.summary,
                "violations": [
                    {
                        "clause": v.clause,
                        "description": v.description,
                        "citation": v.citation,
                        "severity": v.severity,
                        "verified": v.verified,
                        "contractClauseId": item.clause.id,
                        "contractClauseType": item.clause.clause_type,
                    }
                    for v in item.compliance.violations
                ],
                "risks": item.compliance.risks,
                "suggestions": item.compliance.suggestions,
            }
            clause_compliance.append(clause_data["compliance"])

        clauses.append(clause_data)

        for match in item.matches:
            matches.append({
                "clauseId": item.clause.id,
                "uid": match.segment_uid or match.article_uid,
                "citation": match.display_citation,
                "documentTitle": match.document_title,
                "segmentType": match.segment_type,
                "score": match.combined_score,
                "validitySignal": match.validity_signal,
                "scoreFactors": match.score_factors,
            })

        for citation, verification in zip(item.citations, item.verification_results):
            citations.append({
                "displayText": citation.display_text,
                "uid": citation.uid,
                "verified": verification.verified,
                "reason": verification.reason,
                "documentTitle": verification.document_title or citation.document_title,
            })

        if item.compliance:
            for violation in item.compliance.violations:
                all_violations.append({
                    "clause": violation.clause,
                    "description": violation.description,
                    "citation": violation.citation,
                    "verified": violation.verified,
                    "contractClauseId": item.clause.id,
                    "contractClauseType": item.clause.clause_type,
                })
            all_risks.extend(item.compliance.risks)
            all_suggestions.extend(item.compliance.suggestions)

    return {
        "clauses": clauses,
        "matches": matches,
        "citations": citations,
        "compliance": {
            "violations": all_violations,
            "risks": all_risks,
            "suggestions": all_suggestions,
            "citations": citations,
            "clauseResults": clause_compliance,
        },
    }


async def process_contract_mock(job_id: str):
    job_store.update_job(job_id, status="parsing", progress=20)
    await asyncio.sleep(0.1)
    job_store.update_job(job_id, status="analyzing", progress=80)
    await asyncio.sleep(0.1)
    job_store.update_job(
        job_id,
        status="completed",
        progress=100,
        clauses=[
            {"id": "c1", "type": "Thanh toán", "text": "Giá thuê: 50.000.000 VNĐ/tháng", "riskLevel": "low"},
            {"id": "c2", "type": "Phạt vi phạm", "text": "Phạt 30% giá trị hợp đồng", "riskLevel": "high"},
        ],
        compliance={
            "violations": [
                {
                    "clause": "Phạt vi phạm",
                    "description": "Mức phạt 30% vượt quá 8% theo Luật Thương mại",
                    "citation": "Điều 301 Luật Thương mại 2005",
                    "verified": True,
                }
            ],
            "risks": ["Mức phạt quá cao có thể bị tòa án tuyên vô hiệu"],
            "suggestions": ["Giảm mức phạt xuống tối đa 8% giá trị phần nghĩa vụ bị vi phạm"],
            "citations": [],
        },
        matches=[],
        citations=[],
    )
