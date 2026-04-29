"""
app/routers/chat.py — SAS Chat Router v1.0
═══════════════════════════════════════════════════════════════════════════════
Exposes /v1/chat with resonance and κD filter.

Registry: EX-2026-18792778
Author: Gonzalo Emir Durante — Project Manifold 0.56
License: Durante Invariance License v1.0
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from app.models.request import ChatRequest
from app.models.response import ChatResponse
from app.services.chat_service import run_chat

router = APIRouter(prefix="/v1", tags=["SAS Chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """
    Send a prompt to the local LLM with SAS coherence guarantees.

    - Each response is audited with the κD detector.
    - If ISI < 0.56 and filter_mode=True, the response is regenerated.
    - Resonance state is tracked per session_id.
    """
    result = run_chat(
        prompt=request.prompt,
        session_id=request.session_id,
        model=request.model,
        max_retries=request.max_retries,
        filter_mode=request.filter_mode,
        experimental=request.experimental,
    )

    if result.get("verdict") == "ERROR" and not result.get("response"):
        raise HTTPException(
            status_code=503,
            detail=result.get("error", "LLM service unavailable"),
        )

    return ChatResponse(**result)
