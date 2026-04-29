"""
app/models/request.py — Omni-Scanner API v1.0 + SAS v1.0
═══════════════════════════════════════════════════════════════════════════════
Request models. Existing models (AuditRequest, DiffRequest) are preserved.
New models for SAS endpoints are appended.

Registry: EX-2026-18792778
Author: Gonzalo Emir Durante — Project Manifold 0.56
License: Durante Invariance License v1.0
"""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


# ── Existing models (unchanged) ────────────────────────────────────────────────

class AuditRequest(BaseModel):
    text:        str  = Field(..., description="Text to audit")
    input_type:  str  = Field("generic", description="Domain hint")
    experimental: bool = Field(False, description="Enable v10.1 experimental modules")
    enable_modules: Optional[List[str]] = Field(None, description="Optional SAS modules to enable, e.g. ['E9','E10']")


class DiffRequest(BaseModel):
    text_a:      str  = Field(..., description="Reference text")
    text_b:      str  = Field(..., description="Suspect text")
    experimental: bool = Field(False, description="Enable experimental modules")
    enable_modules: Optional[List[str]] = Field(None, description="Optional SAS modules to enable, e.g. ['E9','E10']")
    domain:      Optional[str] = Field(None, description="Domain override")


# ── SAS Chat ───────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    prompt:      str  = Field(..., description="User prompt")
    session_id:  str  = Field("default", description="Session identifier for resonance tracking")
    model:       str  = Field("llama3.2", description="Ollama model name")
    max_retries: int  = Field(2, ge=0, le=5, description="Max regeneration attempts if ISI < κD")
    filter_mode: bool = Field(True, description="Regenerate if ISI < κD=0.56")
    experimental: bool = Field(True, description="Enable v10.1 modules in audit")


# ── SAS Conversation Audit ─────────────────────────────────────────────────────

class ConversationMessage(BaseModel):
    role:    str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class ConversationAuditRequest(BaseModel):
    messages:        List[ConversationMessage] = Field(..., description="Full conversation")
    conversation_id: Optional[str] = Field(None, description="UUID — generated if omitted")
    experimental:    bool = Field(True, description="Enable v10.1 modules per message")
    
class ExternalAuditRequest(BaseModel):
    model_name: str = Field(..., description="Nombre del modelo externo (ej. 'claude-3.5-sonnet')")
    api_key: str = Field(..., description="API key del modelo externo")
    prompt: str = Field(..., description="Prompt de prueba")
    