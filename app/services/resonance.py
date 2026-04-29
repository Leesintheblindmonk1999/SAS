"""
app/services/resonance.py — SAS Resonance Engine v1.0
═══════════════════════════════════════════════════════════════════════════════
Manages per-session semantic coherence state.

Equation: E(t+1) = E(t) * (1 - α) + ISI(t) * α
  · α = 0.3  (inertia constant — smooth persistence)
  · E(0) = 0.5 (neutral initial state)

The resonance state is in-memory only. It resets on server restart.
For persistent sessions, replace _SESSIONS with a Redis/DB backend.

Registry: EX-2026-18792778
Author: Gonzalo Emir Durante — Project Manifold 0.56
License: Durante Invariance License v1.0
"""

from __future__ import annotations

import threading
from typing import Dict

# ── Constants ──────────────────────────────────────────────────────────────────
ALPHA: float       = 0.3   # inertia constant
INITIAL_STATE: float = 0.5  # E(0) — neutral

# ── Thread-safe session store ──────────────────────────────────────────────────
_SESSIONS: Dict[str, float] = {}
_LOCK = threading.Lock()


def get_resonance(session_id: str) -> float:
    """Return current resonance state for a session. Creates it if new."""
    with _LOCK:
        return _SESSIONS.setdefault(session_id, INITIAL_STATE)


def update_resonance(session_id: str, isi: float) -> float:
    """
    Apply the inertia equation and return the new resonance state.

    E(t+1) = E(t) * (1 - α) + ISI(t) * α
    """
    with _LOCK:
        e_t = _SESSIONS.get(session_id, INITIAL_STATE)
        e_next = round(e_t * (1 - ALPHA) + isi * ALPHA, 6)
        _SESSIONS[session_id] = e_next
        return e_next


def reset_resonance(session_id: str) -> None:
    """Reset a session to initial state."""
    with _LOCK:
        _SESSIONS[session_id] = INITIAL_STATE


def delete_session(session_id: str) -> None:
    """Remove a session entirely."""
    with _LOCK:
        _SESSIONS.pop(session_id, None)


def list_sessions() -> Dict[str, float]:
    """Return a snapshot of all active sessions (admin use)."""
    with _LOCK:
        return dict(_SESSIONS)
