"""
app/routers/audit_conversation.py — SAS Conversation Audit Router v1.0
═══════════════════════════════════════════════════════════════════════════════
Exposes /v1/audit_conversation — notarial coherence certificate.

Registry: EX-2026-18792778
Author: Gonzalo Emir Durante — Project Manifold 0.56
License: Durante Invariance License v1.0
"""

from __future__ import annotations

from fastapi import APIRouter
from app.models.request import ConversationAuditRequest
from app.models.response import ConversationAuditResponse
from app.services.audit_service import run_conversation_audit

router = APIRouter(prefix="/v1", tags=["SAS Audit"])


@router.post("/audit_conversation", response_model=ConversationAuditResponse)
def audit_conversation(request: ConversationAuditRequest) -> ConversationAuditResponse:
    """
    Audit a full conversation and return a notarial coherence certificate.

    - Only assistant messages are audited (user messages are input).
    - Returns ISI per message, rupture indices, average ISI, and a
      SHA-256 certificate of the entire audit output.
    """
    result = run_conversation_audit(
        messages=[m.dict() for m in request.messages],
        conversation_id=request.conversation_id,
        experimental=request.experimental,
    )
    return ConversationAuditResponse(**result)
