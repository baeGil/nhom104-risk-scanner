from __future__ import annotations

import asyncio
from pathlib import Path

from dotenv import load_dotenv

from src.llm.client import create_client


def main() -> int:
    env_path = Path(__file__).resolve().parent / ".env"
    load_dotenv(env_path, override=True)

    client = create_client()
    result = asyncio.run(
        client.chat(
            'Return only valid JSON: {"status":"ok"}',
        )
    )
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
