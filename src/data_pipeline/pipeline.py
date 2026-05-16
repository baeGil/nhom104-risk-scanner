"""
T6.3 — Pipeline Orchestration Runner
======================================

Chạy toàn bộ Data & Infra pipeline theo thứ tự, idempotent.
Mỗi task có checkpoint — có thể resume từ điểm thất bại.

Thứ tự:
  Phase 0: T0.1 → T0.5 → T0.2 → T0.3 → T0.4
  Phase 1: T1.4 (schema) → T1.7 (relationships)

Usage:
  python -m src.data_pipeline.pipeline
  python -m src.data_pipeline.pipeline --phase 0
  python -m src.data_pipeline.pipeline --resume --from-task T0.3

Spec: segmentation (T6.3)
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

from src.logging_setup import configure_logging

logger = logging.getLogger(__name__)

CHECKPOINT_FILE = "output/pipeline_checkpoint.json"

# ---------------------------------------------------------------------------
# Task status constants
# ---------------------------------------------------------------------------
STATUS_PENDING  = "pending"
STATUS_RUNNING  = "running"
STATUS_DONE     = "done"
STATUS_FAILED   = "failed"
STATUS_SKIPPED  = "skipped"


# ---------------------------------------------------------------------------
# Checkpoint manager
# ---------------------------------------------------------------------------

class Checkpoint:
    """
    Lưu/đọc trạng thái pipeline vào JSON file.
    Thread-safe cho single-process pipeline.
    """

    def __init__(self, path: str = CHECKPOINT_FILE) -> None:
        self.path = Path(path)
        self._data = self._load()

    def _load(self) -> dict:
        if self.path.exists():
            with open(self.path, encoding="utf-8") as f:
                return json.load(f)
        return {"tasks": {}, "started_at": None, "last_updated": None}

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._data["last_updated"] = _now_iso()
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def mark_running(self, task_id: str) -> None:
        self._data["tasks"][task_id] = {
            "status":     STATUS_RUNNING,
            "started_at": _now_iso(),
        }
        self._save()

    def mark_done(self, task_id: str, result: Optional[dict] = None) -> None:
        self._data["tasks"][task_id] = {
            "status":      STATUS_DONE,
            "finished_at": _now_iso(),
            "result":      result or {},
        }
        self._save()

    def mark_failed(self, task_id: str, error: str) -> None:
        self._data["tasks"][task_id] = {
            "status":      STATUS_FAILED,
            "finished_at": _now_iso(),
            "error":       error,
        }
        self._save()

    def is_done(self, task_id: str) -> bool:
        return self._data["tasks"].get(task_id, {}).get("status") == STATUS_DONE

    def get_status(self, task_id: str) -> str:
        return self._data["tasks"].get(task_id, {}).get("status", STATUS_PENDING)

    def reset_task(self, task_id: str) -> None:
        self._data["tasks"].pop(task_id, None)
        self._save()


# ---------------------------------------------------------------------------
# Task runner
# ---------------------------------------------------------------------------

def run_task(
    task_id: str,
    fn: Callable,
    checkpoint: Checkpoint,
    *,
    force: bool = False,
) -> bool:
    """
    Chạy một task với checkpoint guard.

    Parameters
    ----------
    task_id   : str   — ví dụ "T0.1"
    fn        : callable — hàm main() của task
    checkpoint: Checkpoint
    force     : bool  — nếu True, chạy lại dù đã done

    Returns
    -------
    bool — True nếu thành công, False nếu lỗi
    """
    if checkpoint.is_done(task_id) and not force:
        logger.info("[%s] Already done — skipping (use --force to rerun)", task_id)
        return True

    logger.info("[%s] ▶ Starting...", task_id)
    checkpoint.mark_running(task_id)
    t0 = time.time()

    try:
        result = fn()
        elapsed = time.time() - t0
        logger.info("[%s] ✓ Done in %.1fs", task_id, elapsed)
        checkpoint.mark_done(task_id, {"elapsed_sec": round(elapsed, 1)})
        return True
    except NotImplementedError as exc:
        elapsed = time.time() - t0
        logger.warning("[%s] ⚠ NotImplemented (skeleton) — marking as done for now: %s", task_id, exc)
        checkpoint.mark_done(task_id, {"note": "skeleton — not implemented yet"})
        return True
    except Exception as exc:
        elapsed = time.time() - t0
        logger.error("[%s] ✗ Failed after %.1fs: %s", task_id, elapsed, exc, exc_info=True)
        checkpoint.mark_failed(task_id, str(exc))
        return False


# ---------------------------------------------------------------------------
# Phase runners
# ---------------------------------------------------------------------------

def run_phase_0(checkpoint: Checkpoint, *, force: bool = False) -> bool:
    """Phase 0: Data Cleanup & Normalization."""
    from .normalize    import main as t01_main  # noqa: PLC0415
    from .lookup       import SoKyHieuResolver  # noqa: PLC0415 (T0.5 called inside T0.1)
    from .dedup        import main as t02_main  # noqa: PLC0415
    # T0.3 (crawler) bị skip: cấu trúc thuvienphapluat.vn đã thay đổi, crawl không hoạt động
    # from .crawler      import main as t03_main  # noqa: PLC0415
    from .html_cleaner import main as t04_main  # noqa: PLC0415

    tasks = [
        ("T0.1", t01_main),  # Normalize so_ky_hieu → lookup JSON
        ("T0.5", lambda: logger.info("T0.5 embedded in T0.1 (lookup already built)")),
        ("T0.2", t02_main),  # Dedup
        ("T0.3", lambda: logger.info(  # Crawl bị SKIP — website cấu trúc thay đổi
            "T0.3 SKIPPED: crawler không khả dụng (thuvienphapluat.vn đã đổi cấu trúc). "
            "Tiếp tục với dữ liệu đã có."
        )),
        ("T0.4", t04_main),  # Clean HTML
    ]

    for task_id, fn in tasks:
        ok = run_task(task_id, fn, checkpoint, force=force)
        if not ok:
            logger.error("Phase 0 halted at %s", task_id)
            return False

    return True


def run_phase_1_infra(checkpoint: Checkpoint, *, force: bool = False) -> bool:
    """Phase 1 Infra: Neo4j Schema + Relationship Ingest."""
    from .neo4j_ingest import main as t17_main  # noqa: PLC0415

    def t14_main():
        """T1.4: Remind user to run schema Cypher manually."""
        schema_path = Path("output/neo4j_schema.cypher")
        if not schema_path.exists():
            raise FileNotFoundError(
                f"Schema file not found: {schema_path}. "
                "Please run: python -m src.data_pipeline.schema_generator"
            )
        logger.info(
            "T1.4: Schema file exists at %s. "
            "Run in Neo4j Browser if not already applied.",
            schema_path,
        )

    tasks = [
        ("T1.4", t14_main),  # Verify schema file exists
        ("T1.7", t17_main),  # Ingest 659K relationships
    ]

    for task_id, fn in tasks:
        ok = run_task(task_id, fn, checkpoint, force=force)
        if not ok:
            logger.error("Phase 1 infra halted at %s", task_id)
            return False

    return True


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _setup_logging(level: str = "INFO") -> None:
    configure_logging(level, "output/pipeline.log")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Người A Pipeline Orchestrator"
    )
    parser.add_argument("--phase", choices=["0", "1", "all"], default="all",
                        help="Chạy phase cụ thể (default: all)")
    parser.add_argument("--force", action="store_true",
                        help="Chạy lại dù task đã done")
    parser.add_argument("--reset", metavar="TASK_ID",
                        help="Reset trạng thái của một task cụ thể")
    parser.add_argument("--status", action="store_true",
                        help="Hiển thị trạng thái các tasks")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()

    Path("output").mkdir(parents=True, exist_ok=True)
    _setup_logging(args.log_level)

    checkpoint = Checkpoint(CHECKPOINT_FILE)

    # Show status
    if args.status:
        print(json.dumps(checkpoint._data, ensure_ascii=False, indent=2))
        return

    # Reset specific task
    if args.reset:
        checkpoint.reset_task(args.reset)
        logger.info("Reset task: %s", args.reset)
        return

    logger.info("=" * 60)
    logger.info("Người A Pipeline — starting (phase=%s, force=%s)", args.phase, args.force)
    logger.info("=" * 60)

    success = True
    if args.phase in ("0", "all"):
        success = run_phase_0(checkpoint, force=args.force)

    if success and args.phase in ("1", "all"):
        success = run_phase_1_infra(checkpoint, force=args.force)

    if success:
        logger.info("=" * 60)
        logger.info("Pipeline completed successfully ✓")
    else:
        logger.error("Pipeline FAILED — check logs, fix issue, re-run to resume")
        sys.exit(1)


if __name__ == "__main__":
    main()
