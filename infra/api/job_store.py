"""
In-memory job store for async contract review.

Stores job status, progress, and results.
Jobs are keyed by job_id (UUID string).
"""
from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class Job:
    """Represents an async contract review job."""
    job_id: str
    filename: str
    status: str  # uploading, parsing, analyzing, completed, failed
    progress: int = 0
    created_at: str = ""
    clauses: Optional[list[dict]] = None
    compliance: Optional[dict] = None
    error: Optional[str] = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class JobStore:
    """
    In-memory job store.

    Thread-safe for concurrent access.
    """

    def __init__(self):
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()

    def create_job(self, filename: str) -> str:
        """Create a new job and return job_id."""
        job_id = f"job_{uuid.uuid4().hex[:8]}"
        job = Job(job_id=job_id, filename=filename, status="uploading", progress=0)
        with self._lock:
            self._jobs[job_id] = job
        return job_id

    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        with self._lock:
            return self._jobs.get(job_id)

    def update_job(self, job_id: str, **kwargs: Any) -> Optional[Job]:
        """Update job fields."""
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                for key, value in kwargs.items():
                    setattr(job, key, value)
            return job

    def get_all_jobs(self) -> list[Job]:
        """Get all jobs sorted by created_at descending."""
        with self._lock:
            return sorted(
                self._jobs.values(),
                key=lambda j: j.created_at,
                reverse=True,
            )

    def delete_job(self, job_id: str) -> bool:
        """Delete a job."""
        with self._lock:
            if job_id in self._jobs:
                del self._jobs[job_id]
                return True
            return False


# Global job store instance
job_store = JobStore()
