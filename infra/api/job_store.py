"""
In-memory job store for async contract review.

Stores job status, progress, and results.
Jobs are keyed by job_id (UUID string).
"""
from __future__ import annotations

import threading
import uuid
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
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
    matches: Optional[list[dict]] = None
    compliance: Optional[dict] = None
    citations: Optional[list[dict]] = None
    error: Optional[str] = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class JobStore:
    """
    In-memory job store.

    Thread-safe for concurrent access.
    """

    def __init__(self, path: str = "output/contract_jobs.json"):
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()
        self._path = Path(path)
        self._load()

    def create_job(self, filename: str) -> str:
        """Create a new job and return job_id."""
        job_id = f"job_{uuid.uuid4().hex[:8]}"
        job = Job(job_id=job_id, filename=filename, status="uploading", progress=0)
        with self._lock:
            self._jobs[job_id] = job
            self._save_locked()
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
                self._save_locked()
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
                self._save_locked()
                return True
            return False

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            self._jobs = {item["job_id"]: Job(**item) for item in data}
        except Exception:
            self._jobs = {}

    def _save_locked(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = [asdict(job) for job in self._jobs.values()]
        self._path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# Global job store instance
job_store = JobStore()
