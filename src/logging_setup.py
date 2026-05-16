"""Shared logging helpers for human-friendly console output."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from rich.logging import RichHandler


def configure_logging(level: str = "INFO", log_path: Optional[str] = None) -> None:
    """Configure root logging with Rich and an optional file handler."""
    handlers: list[logging.Handler] = [
        RichHandler(
            rich_tracebacks=True,
            markup=False,
            show_time=False,
            show_level=True,
            show_path=False,
        )
    ]

    if log_path:
        path = Path(log_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(path, encoding="utf-8"))

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(message)s",
        handlers=handlers,
        force=True,
    )
