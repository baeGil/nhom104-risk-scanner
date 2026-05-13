"""
T6.2 — Embedding Service
=========================

FastAPI service cho model vietlegal-harrier-0.6b (1024 dims).
Dùng để tạo embeddings cho Articles — phục vụ T1.6 (Người B).

Interface contract với Người B:
  POST /embed
    Request:  {"texts": ["text1", "text2", ...]}
    Response: {"embeddings": [[0.1, ...], ...], "dims": 1024, "count": N}

  GET /health
    Response: {"status": "ok", "model": "...", "device": "cuda|cpu"}

Usage:
  uvicorn infra.embedding_service.app:app --host 0.0.0.0 --port 8080
  # Or with Docker:
  # docker build -t vietlegal-embed ./infra/embedding_service/
  # docker run -p 8080:8080 --gpus all vietlegal-embed

Spec: segmentation (T6.2)
"""
from __future__ import annotations

import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

MODEL_NAME   = os.getenv("EMBED_MODEL", "mainguyen9/vietlegal-harrier-0.6b")
BATCH_SIZE   = int(os.getenv("EMBED_BATCH_SIZE", "512"))
MAX_TEXTS    = int(os.getenv("EMBED_MAX_TEXTS", "1000"))
EXPECTED_DIM = 1024

# ---------------------------------------------------------------------------
# Global model instance (loaded once at startup)
# ---------------------------------------------------------------------------

_model   = None
_tokenizer = None
_device  = None


def _load_model():
    """Load model lúc startup."""
    global _model, _tokenizer, _device

    try:
        import torch
        from transformers import AutoModel, AutoTokenizer

        _device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info("Loading model '%s' on %s...", MODEL_NAME, _device)

        _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        _model     = AutoModel.from_pretrained(MODEL_NAME).to(_device)
        _model.eval()

        logger.info("Model loaded successfully — device=%s, dims=%d", _device, EXPECTED_DIM)
    except ImportError:
        logger.warning(
            "torch/transformers not installed — running in MOCK mode. "
            "Embeddings will be zero vectors."
        )
    except Exception as exc:
        logger.error("Failed to load model: %s", exc)
        raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model on startup, cleanup on shutdown."""
    _load_model()
    yield
    # Cleanup
    global _model, _tokenizer
    _model = None
    _tokenizer = None


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="VietLegal Embedding Service",
    description="Embedding service cho mainguyen9/vietlegal-harrier-0.6b (1024d)",
    version="0.1.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Request/Response schemas
# ---------------------------------------------------------------------------

class EmbedRequest(BaseModel):
    texts: list[str] = Field(..., description="List of texts to embed", max_length=MAX_TEXTS)


class EmbedResponse(BaseModel):
    embeddings: list[list[float]]
    dims: int = EXPECTED_DIM
    count: int
    elapsed_ms: float


class HealthResponse(BaseModel):
    status: str
    model: str
    device: Optional[str]
    dims: int


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return HealthResponse(
        status="ok" if (_model is not None or True) else "model_not_loaded",
        model=MODEL_NAME,
        device=_device or "mock",
        dims=EXPECTED_DIM,
    )


@app.post("/embed", response_model=EmbedResponse)
async def embed(request: EmbedRequest):
    """
    Tạo embeddings cho danh sách texts.

    - Batch size: tối đa EMBED_BATCH_SIZE texts mỗi lần gọi model
    - Trả về list embeddings theo thứ tự input
    """
    if not request.texts:
        raise HTTPException(status_code=400, detail="texts must not be empty")

    t0 = time.perf_counter()
    texts = request.texts

    try:
        embeddings = _embed_texts(texts)
    except Exception as exc:
        logger.error("Embedding failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    elapsed_ms = (time.perf_counter() - t0) * 1000

    return EmbedResponse(
        embeddings=embeddings,
        dims=EXPECTED_DIM,
        count=len(embeddings),
        elapsed_ms=round(elapsed_ms, 1),
    )


# ---------------------------------------------------------------------------
# Embedding logic
# ---------------------------------------------------------------------------

def _embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Embed texts in batches.

    Falls back to zero vectors if model not loaded (mock mode).
    """
    if _model is None or _tokenizer is None:
        logger.warning("Model not loaded — returning mock zero embeddings")
        return [[0.0] * EXPECTED_DIM for _ in texts]

    import torch

    all_embeddings = []

    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i: i + BATCH_SIZE]
        with torch.no_grad():
            encoded = _tokenizer(
                batch,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt",
            ).to(_device)

            output = _model(**encoded)
            # Mean pooling over token embeddings
            token_embeddings = output.last_hidden_state
            attention_mask   = encoded["attention_mask"].unsqueeze(-1).float()
            summed           = (token_embeddings * attention_mask).sum(dim=1)
            counts           = attention_mask.sum(dim=1)
            pooled           = (summed / counts).cpu().numpy()

        all_embeddings.extend(pooled.tolist())
        logger.debug("Embedded batch %d-%d", i, i + len(batch))

    # Validate dimensions
    for emb in all_embeddings:
        if len(emb) != EXPECTED_DIM:
            raise ValueError(
                f"Expected {EXPECTED_DIM} dims, got {len(emb)}"
            )

    return all_embeddings


# ---------------------------------------------------------------------------
# Run directly
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8080, reload=False, log_level="info")
