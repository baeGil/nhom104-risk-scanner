from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv


def load_project_env() -> None:
    """
    Load environment variables from the repository root.

    The root .env overrides existing values, while frontend/.env.local can
    supply UI-specific variables without overriding explicit root values.
    """
    project_root = Path(__file__).resolve().parent.parent
    load_dotenv(project_root / ".env", override=True)
    load_dotenv(project_root / "frontend" / ".env.local", override=False)
