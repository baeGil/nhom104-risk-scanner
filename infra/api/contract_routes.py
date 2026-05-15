"""Contract review API routes."""
from __future__ import annotations

import asyncio
import logging
import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File

from infra.api.models import JobStatusResponse, ContractClauseResponse, ComplianceResultResponse, LegalMatchResponse, CitationResponse
from infra.api.job_store import job_store
from src.contract.review_pipeline import ContractReviewPipeline, ContractReviewPipelineError

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

    for item in result.clauses:
        has_high = bool(item.compliance and item.compliance.violations)
        clauses.append({
            "id": item.clause.id,
            "type": item.clause.clause_type,
            "text": item.clause.text_content,
            "riskLevel": "high" if has_high else "low",
        })

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
