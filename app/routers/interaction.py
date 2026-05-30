"""FastAPI router for interaction stability.

Experimental endpoints:
- GET  /v1/interaction/stability/example
- POST /v1/interaction/stability

POST is protected with get_api_key. Do not rely on global /v1 middleware.
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
    LIKELIHOOD_NOTE,
    MAX_CONVERSATION_TURNS,
    OMEGA_NOTE,
    SIGMA_NOTE,
    THEORY_DOI,
    THRESHOLD_NOTE,
    analyze_conversation,
    example_conversation,
)


router = APIRouter(prefix="/v1/interaction", tags=["interaction stability"])


class ConversationTurn(BaseModel):
    role: str = Field(..., description="Turn role. Supported values: 'user' or 'assistant'.")
    content: str = Field(..., description="Text content for this turn.")


class StabilityRequest(BaseModel):
    conversation: List[ConversationTurn] = Field(
        ...,
        min_length=1,
        max_length=MAX_CONVERSATION_TURNS,
        description="Role-based conversation. Must include at least one assistant turn.",
    )
    gamma: float = Field(0.85, gt=0.0, lt=1.0, description="Exponential decay factor for historical demand.")
    window: int = Field(4, ge=1, le=50, description="Sliding demand window size.")
    kappa_d: float = Field(DEFAULT_KAPPA_D, gt=0.0, lt=1.0, description="SAS-aligned experimental threshold.")
    alpha: float = Field(2.0, ge=0.0, description="Post-threshold penalty strength.")
    mode: str = Field("analyze", description="MVP supports only 'analyze'. Future: estimate, advise.")
    normalize_demand: bool = Field(
        True,
        description="Use normalized exponentially decayed historical demand so D_A(t) remains bounded.",
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


def _dump_model(obj: BaseModel) -> Dict[str, Any]:
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    return obj.dict()


@router.get(
    "/stability/example",
    description="Return a ready-to-use demo payload for the experimental interaction stability endpoint.",
)
async def interaction_stability_example() -> Dict[str, Any]:
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


@router.post(
    "/stability",
    response_model=StabilityResponse,
    description=(
        "Experimental heuristic endpoint for interaction stability research. "
        "Outputs are model constructs from a technical preprint, not empirical measurements, "
        "psychological diagnosis, legal certification, or behavioral intervention guidance. "
        "Requires X-API-Key."
    ),
)
async def interaction_stability(
    request: StabilityRequest,
    _api_key: dict = Depends(get_api_key),
) -> StabilityResponse:
    if request.mode not in {"analyze", "estimate", "advise"}:
        raise HTTPException(status_code=422, detail="mode must be one of: analyze, estimate, advise.")

    if request.mode != "analyze":
        raise HTTPException(
            status_code=501,
            detail=f"Mode '{request.mode}' is reserved for a future release. Only mode='analyze' is implemented in the MVP.",
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
    )
