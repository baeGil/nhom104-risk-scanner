"""Contract review API routes."""
from __future__ import annotations

import asyncio
import logging
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse

from infra.api.models import JobStatusResponse, ContractClauseResponse, ComplianceResultResponse, ComplianceViolationResponse
from infra.api.job_store import job_store

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
        compliance=ComplianceResultResponse(**job.compliance) if job.compliance else None,
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
        )
        for j in jobs
    ]


async def process_contract(job_id: str, content: bytes, filename: str):
    """
    Process a contract file asynchronously.

    Pipeline: parsing → clause extraction → legal matching → compliance analysis
    """
    try:
        # Step 1: Parsing (20%)
        job_store.update_job(job_id, status="parsing", progress=20)
        await asyncio.sleep(0.5)  # Simulate parsing

        # Step 2: Clause extraction (50%)
        job_store.update_job(job_id, status="analyzing", progress=50)
        await asyncio.sleep(1)  # Simulate LLM clause extraction

        # Step 3: Compliance analysis (80%)
        job_store.update_job(job_id, progress=80)
        await asyncio.sleep(0.5)  # Simulate compliance analysis

        # Step 4: Complete (100%)
        # TODO: Replace with real pipeline when ready
        mock_clauses = [
            {"id": "c1", "type": "Thanh toán", "text": "Giá thuê: 50.000.000 VNĐ/tháng", "riskLevel": "low"},
            {"id": "c2", "type": "Phạt vi phạm", "text": "Phạt 30% giá trị hợp đồng", "riskLevel": "high"},
        ]
        mock_compliance = {
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
        }

        job_store.update_job(
            job_id,
            status="completed",
            progress=100,
            clauses=mock_clauses,
            compliance=mock_compliance,
        )

    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        job_store.update_job(job_id, status="failed", progress=0, error=str(e))
