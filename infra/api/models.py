"""Pydantic schemas for API request/response models."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ── QA Schemas ──────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    conversationId: Optional[str] = None


class IntentResult(BaseModel):
    type: str
    confidence: float


class Provision(BaseModel):
    documentName: str
    articleNumber: str
    text: str
    verified: bool = False


class ChatChunk(BaseModel):
    token: Optional[str] = None
    intents: Optional[list[IntentResult]] = None
    provisions: Optional[list[Provision]] = None
    done: Optional[bool] = None


class ConversationSummary(BaseModel):
    id: str
    title: str
    lastMessage: str
    createdAt: str


class CreateConversationRequest(BaseModel):
    title: str = "New conversation"


# ── Contract Schemas ────────────────────────────────────────────────────────

class UploadResponse(BaseModel):
    jobId: str


class ContractClauseResponse(BaseModel):
    id: str
    type: str
    text: str
    riskLevel: str = "medium"


class ComplianceViolationResponse(BaseModel):
    clause: str
    description: str
    citation: str
    verified: bool = False


class ComplianceResultResponse(BaseModel):
    violations: list[ComplianceViolationResponse] = []
    risks: list[str] = []
    suggestions: list[str] = []


class JobStatusResponse(BaseModel):
    jobId: str
    status: str  # uploading, parsing, analyzing, completed, failed
    progress: int = Field(ge=0, le=100)
    filename: str
    createdAt: str
    clauses: Optional[list[ContractClauseResponse]] = None
    compliance: Optional[ComplianceResultResponse] = None
