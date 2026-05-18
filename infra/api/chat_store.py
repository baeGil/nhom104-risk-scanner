"""Supabase-backed persistence for Legal QA chat conversations."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Optional

import requests
from src.env_utils import load_project_env

load_project_env()


class ChatStoreError(RuntimeError):
    """Raised when chat persistence cannot complete."""


class ChatStore:
    """Small PostgREST client for Supabase chat tables."""

    def __init__(self) -> None:
        self.supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL", "").rstrip("/")
        self.service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        if not self.supabase_url or not self.service_key:
            raise ChatStoreError("Supabase URL or service role key is not configured")
        self.rest_url = f"{self.supabase_url}/rest/v1"

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "apikey": self.service_key,
            "Authorization": f"Bearer {self.service_key}",
            "Content-Type": "application/json",
        }

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[dict[str, Any]] = None,
        json: Any = None,
        prefer: Optional[str] = None,
    ) -> Any:
        headers = self._headers
        if prefer:
            headers["Prefer"] = prefer
        response = requests.request(
            method,
            f"{self.rest_url}/{path}",
            headers=headers,
            params=params,
            json=json,
            timeout=20,
        )
        if response.status_code >= 400:
            raise ChatStoreError(f"Supabase {method} {path} failed: {response.status_code} {response.text}")
        if not response.text:
            return None
        return response.json()

    def get_conversation(self, user_id: str, conversation_id: str) -> Optional[dict[str, Any]]:
        rows = self._request(
            "GET",
            "chat_conversations",
            params={
                "select": "*",
                "id": f"eq.{conversation_id}",
                "user_id": f"eq.{user_id}",
                "deleted_at": "is.null",
                "limit": "1",
            },
        )
        return rows[0] if rows else None

    def get_conversation_by_tab(self, user_id: str, tab_id: str) -> Optional[dict[str, Any]]:
        rows = self._request(
            "GET",
            "chat_conversations",
            params={
                "select": "*",
                "user_id": f"eq.{user_id}",
                "tab_id": f"eq.{tab_id}",
                "deleted_at": "is.null",
                "limit": "1",
            },
        )
        return rows[0] if rows else None

    def create_conversation(self, user_id: str, tab_id: str, title: str = "New conversation") -> dict[str, Any]:
        existing = self.get_conversation_by_tab(user_id, tab_id)
        if existing:
            return existing
        rows = self._request(
            "POST",
            "chat_conversations",
            json={
                "user_id": user_id,
                "tab_id": tab_id,
                "title": title,
                "title_source": "fallback",
            },
            prefer="return=representation",
        )
        return rows[0]

    def list_conversations(self, user_id: str) -> list[dict[str, Any]]:
        return self._request(
            "GET",
            "chat_conversations",
            params={
                "select": "*",
                "user_id": f"eq.{user_id}",
                "deleted_at": "is.null",
                "order": "last_message_at.desc.nullslast",
            },
        )

    def list_messages(self, user_id: str, conversation_id: str) -> list[dict[str, Any]]:
        if not self.get_conversation(user_id, conversation_id):
            raise ChatStoreError("Conversation not found")
        return self._request(
            "GET",
            "chat_messages",
            params={
                "select": "*",
                "conversation_id": f"eq.{conversation_id}",
                "user_id": f"eq.{user_id}",
                "order": "sequence.asc",
            },
        )

    def last_message(self, user_id: str, conversation_id: str) -> str:
        rows = self._request(
            "GET",
            "chat_messages",
            params={
                "select": "content",
                "conversation_id": f"eq.{conversation_id}",
                "user_id": f"eq.{user_id}",
                "order": "sequence.desc",
                "limit": "1",
            },
        )
        return rows[0]["content"] if rows else ""

    def insert_message(
        self,
        *,
        user_id: str,
        conversation_id: str,
        role: str,
        content: str,
        token_count: int = 0,
        citations: Optional[list[dict[str, Any]]] = None,
        provisions: Optional[list[dict[str, Any]]] = None,
        intents: Optional[list[dict[str, Any]]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        if not self.get_conversation(user_id, conversation_id):
            raise ChatStoreError("Conversation not found")

        for _ in range(3):
            sequence = self._next_sequence(user_id, conversation_id)
            try:
                rows = self._request(
                    "POST",
                    "chat_messages",
                    json={
                        "conversation_id": conversation_id,
                        "user_id": user_id,
                        "role": role,
                        "content": content,
                        "sequence": sequence,
                        "token_count": max(0, token_count),
                        "citations": citations or [],
                        "provisions": provisions or [],
                        "intents": intents or [],
                        "metadata": metadata or {},
                    },
                    prefer="return=representation",
                )
                return rows[0]
            except ChatStoreError as exc:
                if "idx_chat_messages_conversation_sequence" not in str(exc):
                    raise
        raise ChatStoreError("Could not allocate message sequence")

    def rename_conversation(self, user_id: str, conversation_id: str, title: str) -> dict[str, Any]:
        if not self.get_conversation(user_id, conversation_id):
            raise ChatStoreError("Conversation not found")
        rows = self._request(
            "PATCH",
            "chat_conversations",
            params={"id": f"eq.{conversation_id}", "user_id": f"eq.{user_id}", "deleted_at": "is.null"},
            json={"title": title.strip(), "title_source": "manual"},
            prefer="return=representation",
        )
        return rows[0]

    def update_title_if_fallback(self, user_id: str, conversation_id: str, title: str, source: str) -> None:
        conversation = self.get_conversation(user_id, conversation_id)
        if not conversation or conversation.get("title_source") == "manual":
            return
        self._request(
            "PATCH",
            "chat_conversations",
            params={"id": f"eq.{conversation_id}", "user_id": f"eq.{user_id}", "deleted_at": "is.null"},
            json={"title": title[:120], "title_source": source},
            prefer="return=minimal",
        )

    def soft_delete_conversation(self, user_id: str, conversation_id: str) -> None:
        if not self.get_conversation(user_id, conversation_id):
            raise ChatStoreError("Conversation not found")
        self._request(
            "PATCH",
            "chat_conversations",
            params={"id": f"eq.{conversation_id}", "user_id": f"eq.{user_id}", "deleted_at": "is.null"},
            json={"deleted_at": datetime.now(timezone.utc).isoformat()},
            prefer="return=minimal",
        )

    def _next_sequence(self, user_id: str, conversation_id: str) -> int:
        rows = self._request(
            "GET",
            "chat_messages",
            params={
                "select": "sequence",
                "conversation_id": f"eq.{conversation_id}",
                "user_id": f"eq.{user_id}",
                "order": "sequence.desc",
                "limit": "1",
            },
        )
        return int(rows[0]["sequence"]) + 1 if rows else 0


def estimate_token_count(text: str) -> int:
    """Lightweight token estimate for usage tracking until provider usage is wired."""
    return max(1, len(text.split())) if text else 0


def get_chat_store() -> ChatStore:
    return ChatStore()
