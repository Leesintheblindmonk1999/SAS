"""FastAPI router for interaction stability.

Experimental endpoints:
- GET  /v1/interaction/stability/example  — public, no auth required
- POST /v1/interaction/stability          — protected with get_api_key

C4/C5: Double protection architecture:
  Layer 1 — main.py: router is only imported/registered when
            ENABLE_INTERACTION_STABILITY env var is set to 'true'.
  Layer 2 — This router: each handler checks INTERACTION_STABILITY_ENABLED
            from the service module and returns 503 if disabled.
  Layer 3 — POST endpoint: requires X-API-Key via get_api_key dependency.

Do not rely on global /v1 middleware for auth. Auth is explicit per endpoint.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.dependencies import get_api_key
from app.services.interaction_stability import (
    CONJECTURE_NOTE,
    DEFAULT_KAPPA_D,
    DEMAND_NOTE,
    EXPERIMENTAL_NOTICE,
    is_interaction_stability_enabled,
    LIKELIHOOD_NOTE,
    MAX_ALPHA,
    MAX_CONVERSATION_TURNS,
    OMEGA_NOTE,
    SIGMA_NOTE,
    THEORY_DOI,
    THRESHOLD_NOTE,
    analyze_conversation,
    example_conversation,
)


router = APIRouter(prefix="/v1/interaction", tags=["interaction stability"])


# ── Schema ────────────────────────────────────────────────────────────────────

class ConversationTurn(BaseModel):
    # D3: explicit max_length to prevent oversized payloads
    role: str = Field(..., max_length=50, description="Turn role: 'user' or 'assistant'.")
    content: str = Field(
        ...,
        max_length=4000,
        description="Text content for this turn. Max 4000 characters.",
    )


class StabilityRequest(BaseModel):
    conversation: List[ConversationTurn] = Field(
        ...,
        min_length=1,
        max_length=MAX_CONVERSATION_TURNS,
        description=(
            "Role-based conversation. Must include at least one assistant turn. "
            f"Max {MAX_CONVERSATION_TURNS} turns."
        ),
    )
    gamma: float = Field(
        0.85,
        gt=0.0,
        lt=1.0,
        description="Exponential decay factor for historical demand. Range (0, 1). Default 0.85.",
    )
    window: int = Field(
        4,
        ge=1,
        le=50,
        description="Sliding demand window size. Range [1, 50]. Default 4.",
    )
    kappa_d: float = Field(
        DEFAULT_KAPPA_D,
        gt=0.0,
        lt=1.0,
        description="SAS-aligned experimental threshold. Default 0.56.",
    )
    # D2: alpha capped at MAX_ALPHA to prevent sigma numerical collapse
    alpha: float = Field(
        2.0,
        ge=0.0,
        le=MAX_ALPHA,
        description=(
            f"Post-threshold penalty strength. Range [0, {MAX_ALPHA}]. "
            "Default 2.0 per v1.2.0 calibration."
        ),
    )
    mode: str = Field(
        "analyze",
        description="MVP supports only 'analyze'. Future modes: estimate, advise.",
    )
    normalize_demand: bool = Field(
        True,
        description=(
            "Use normalized exponentially decayed historical demand so D_A(t) "
            "remains bounded in [0, 1]."
        ),
    )


class StabilityResponse(BaseModel):
    status: str
    mode: str
    model_version: str
    theory_reference: str
    theory_doi: str
    experimental_notice: str
    likelihood_note: str
    omega_note: str
    chi_note: str
    sigma_note: str
    threshold_note: str
    conjecture_note: str
    demand_note: str
    kappa_d_ref: float
    theta_hat: Optional[float]
    alpha: float
    trajectory: List[Dict[str, Any]]
    summary: Dict[str, Any]
    # C3: Traceability fields
    request_id: str
    executed_at: str
    input_hash: str
    content_fingerprint: str
    # D5: skipped_turns at top level
    skipped_turns: List[Dict[str, Any]]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _check_enabled() -> None:
    """C4: Layer-2 feature flag check. Reads env var dynamically — no redeploy needed."""
    if not is_interaction_stability_enabled():
        raise HTTPException(
            status_code=503,
            detail={
                "error": "endpoint_disabled",
                "message": (
                    "The interaction stability endpoint is currently disabled. "
                    "Set ENABLE_INTERACTION_STABILITY=true in the environment "
                    "to enable it for research use."
                ),
            },
        )


def _dump_model(obj: BaseModel) -> Dict[str, Any]:
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    return obj.dict()


# ── GET /stability/example ────────────────────────────────────────────────────

@router.get(
    "/stability/example",
    description=(
        "Return a ready-to-use demo payload for the experimental interaction "
        "stability endpoint. Public endpoint — no API key required."
    ),
)
async def interaction_stability_example() -> Dict[str, Any]:
    # GET example is public but still respects the feature flag so the
    # demo payload is not served when the feature is globally disabled.
    _check_enabled()
    return {
        "experimental_notice": EXPERIMENTAL_NOTICE,
        "likelihood_note": LIKELIHOOD_NOTE,
        "omega_note": OMEGA_NOTE,
        "sigma_note": SIGMA_NOTE,
        "threshold_note": THRESHOLD_NOTE,
        "conjecture_note": CONJECTURE_NOTE,
        "demand_note": DEMAND_NOTE,
        "theory_doi": THEORY_DOI,
        "conversation": example_conversation(),
        "gamma": 0.85,
        "window": 4,
        "kappa_d": DEFAULT_KAPPA_D,
        "alpha": 2.0,
        "mode": "analyze",
        "normalize_demand": True,
    }


# ── POST /stability ───────────────────────────────────────────────────────────

@router.post(
    "/stability",
    response_model=StabilityResponse,
    description=(
        "Experimental heuristic endpoint for interaction stability research. "
        "Outputs are model constructs from a technical preprint (DOI: 10.5281/zenodo.20335612), "
        "not empirical measurements, psychological diagnosis, legal certification, "
        "or behavioral intervention guidance. "
        "Requires X-API-Key header."
    ),
)
async def interaction_stability(
    request: StabilityRequest,
    # C5: Explicit auth dependency — do not rely on global /v1 middleware.
    _api_key: dict = Depends(get_api_key),
) -> StabilityResponse:
    # C4: Layer-2 feature flag check
    _check_enabled()

    if request.mode not in {"analyze", "estimate", "advise"}:
        raise HTTPException(
            status_code=422,
            detail="mode must be one of: analyze, estimate, advise.",
        )

    if request.mode != "analyze":
        raise HTTPException(
            status_code=501,
            detail=(
                f"Mode '{request.mode}' is reserved for a future release. "
                "Only mode='analyze' is implemented in the MVP."
            ),
        )

    try:
        result = analyze_conversation(
            conversation=[_dump_model(turn) for turn in request.conversation],
            gamma=request.gamma,
            window=request.window,
            kappa_d=request.kappa_d,
            alpha=request.alpha,
            mode=request.mode,
            normalize_demand=request.normalize_demand,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc
    except RuntimeError as exc:
        # C4: Catches INTERACTION_STABILITY_ENABLED=False raised inside service
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return StabilityResponse(
        status=result.status,
        mode=result.mode,
        model_version=result.model_version,
        theory_reference=result.theory_reference,
        theory_doi=result.theory_doi,
        experimental_notice=result.experimental_notice,
        likelihood_note=result.likelihood_note,
        omega_note=result.omega_note,
        chi_note=result.chi_note,
        sigma_note=result.sigma_note,
        threshold_note=result.threshold_note,
        conjecture_note=result.conjecture_note,
        demand_note=result.demand_note,
        kappa_d_ref=result.kappa_d_ref,
        theta_hat=result.theta_hat,
        alpha=result.alpha,
        trajectory=result.trajectory,
        summary=result.summary,
        # C3: Traceability
        request_id=result.request_id,
        executed_at=result.executed_at,
        input_hash=result.input_hash,
        content_fingerprint=result.content_fingerprint,
        # D5: skipped_turns at top level
        skipped_turns=result.skipped_turns,
    )
