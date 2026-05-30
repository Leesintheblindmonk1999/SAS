"""Interaction Stability Service - v1.2.0-aligned MVP.

Experimental research endpoint for:
    POST /v1/interaction/stability

This module operationalizes the research line:
"A Control-Theoretic Model for Stochastic Interaction under Hidden-State
Uncertainty and Demand-Sensitive Response Degradation" (v1.2.0).
DOI: 10.5281/zenodo.20335612

Important:
- Outputs are heuristic model constructs, not empirical measurements.
- Hidden states are model states, not psychological facts.
- omega_t / belief_coherence_chi measures belief concentration, not state desirability.
- theta_hat=0.56 is an SAS-aligned experimental default, not an observed theta_B.
- Do not use for psychological assessment, legal proceedings, or behavioral intervention.

Patch notes (v1.2.0-mvp → v1.2.1-mvp):
- C1: Fixed last_action/pending_user_action contamination in non-alternating turns.
- C2: Added zero-row guard in demand_driven_transition.
- C3: Added request_id, executed_at, input_hash, content_fingerprint to results.
- C4: Added INTERACTION_STABILITY_ENABLED feature flag (checked at service level).
- C5: Auth enforced at router level via get_api_key (see interaction.py).
- D1: Word-boundary keyword matching in classify_user_action / classify_agent_observation.
- D2: alpha capped at 20.0 in validate_params.
- D3: content max_length enforced at schema level (see interaction.py).
- D4: effective_window added per trajectory step.
- D5: skipped_turns promoted to top-level result field.
- O1: Placeholder _estimate_theta_hat added (mode='estimate', not yet active).
- O2: Placeholder _generate_advice added (mode='advise', not yet active).
"""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np

# ── Feature flag ──────────────────────────────────────────────────────────────
# Reads ENABLE_INTERACTION_STABILITY env var at call time so the flag can be
# toggled on Render (or any deployment env) without a code change or redeploy.
# Checked at service entry point AND at router level (double protection).
#
# To enable:  ENABLE_INTERACTION_STABILITY=true  (env var)
# To disable: unset or set to anything other than "true"
import os as _os


def is_interaction_stability_enabled() -> bool:
    """Return True only when ENABLE_INTERACTION_STABILITY=true in the environment."""
    return _os.getenv("ENABLE_INTERACTION_STABILITY", "false").lower() == "true"

# ── Constants ─────────────────────────────────────────────────────────────────
MODEL_VERSION = "interaction-stability-v1.2.1-mvp"
THEORY_REFERENCE = "stochastic_interaction_v1.2.0"
THEORY_DOI = "10.5281/zenodo.20335612"
DEFAULT_KAPPA_D = 0.56
MAX_CONVERSATION_TURNS = 100
MAX_ALPHA = 20.0

# ── Epistemic notices (verbatim from paper v1.2.0) ───────────────────────────
EXPERIMENTAL_NOTICE = (
    "This endpoint implements a heuristic formal model from a technical preprint. "
    "Outputs are model constructs, not empirical measurements. Hidden states are "
    "not psychological or architectural facts. Do not use for psychological assessment, "
    "legal proceedings, or behavioral intervention."
)

LIKELIHOOD_NOTE = (
    "The MVP uses the five-state appendix likelihood matrix. Likelihood values are "
    "proportional weights, not normalized emission distributions. Bayesian normalization "
    "is applied at each update step. The reduced three-column table in the paper is treated "
    "as didactic compression."
)

OMEGA_NOTE = (
    "omega_t = 1 - H(b_t)/ln(|S|). It measures concentration of the belief state, "
    "not whether the dominant state is desirable or healthy."
)

CHI_NOTE = (
    "belief_coherence_chi is kept as a backward-compatible alias of omega_t. "
    "High chi/omega with dominant_state=Defensive may indicate confident degradation, "
    "not healthy stability."
)

SIGMA_NOTE = (
    "interaction_stability_sigma combines belief concentration with a post-threshold "
    "historical-demand penalty. Low sigma in early turns may reflect initial uncertainty "
    "rather than confirmed degradation."
)

THRESHOLD_NOTE = (
    "theta_hat=0.56 is an SAS-aligned experimental default in mode='analyze'. "
    "It is not an empirically estimated theta_B and is not claimed to be mathematically "
    "identical to kappa_D."
)

CONJECTURE_NOTE = (
    "The relation \u03A9_t \u2248 ISI_t is treated as a formal research conjecture in stable "
    "regimes, not as a proven equivalence."
)

DEMAND_NOTE = (
    "The MVP uses normalized exponentially decayed historical demand by default so D_A(t) "
    "remains bounded for operational scoring. This differs from an unnormalized literal "
    "sum and should be calibrated per domain."
)


# ── Enums ─────────────────────────────────────────────────────────────────────
class UserAction(Enum):
    N = "N"
    M = "M"
    P = "P"
    Rc = "Rc"


class AgentObservation(Enum):
    R = "R"
    L = "L"
    S = "S"
    J = "J"
    H = "H"


# ── State space ───────────────────────────────────────────────────────────────
STATES = ["Open", "Ambivalent", "Saturated", "Avoidant", "Defensive"]
N_STATES = len(STATES)

# v1.2.0 baseline phi values (Section 2.1, Table 1).
PHI: Dict[UserAction, float] = {
    UserAction.N: 0.0,
    UserAction.M: 0.20,
    UserAction.P: 0.60,
    UserAction.Rc: 1.00,
}

# Five-state appendix-style likelihood weights (Appendix A, paper v1.2.0).
LIKELIHOOD_WEIGHTS: Dict[str, np.ndarray] = {
    "S": np.array([0.04, 0.18, 0.30, 0.65, 0.80], dtype=float),
    "H": np.array([0.12, 0.55, 0.22, 0.28, 0.18], dtype=float),
    "L": np.array([0.20, 0.60, 0.35, 0.20, 0.10], dtype=float),
    "R": np.array([0.70, 0.22, 0.08, 0.05, 0.03], dtype=float),
    "J": np.array([0.10, 0.45, 0.40, 0.30, 0.25], dtype=float),
}

# Base transition matrix: diagonal 0.82, off-diagonal 0.045 (rows sum to 1.0).
BASE_TRANSITION = (
    np.eye(N_STATES, dtype=float) * 0.82
    + (np.ones((N_STATES, N_STATES), dtype=float) - np.eye(N_STATES)) * 0.045
)

# Keyword maps for heuristic action/observation classification.
USER_ACTION_KEYWORDS: Dict[UserAction, List[str]] = {
    UserAction.Rc: [
        "urgente", "ya", "inmediatamente", "reclamo", "exijo", "presión", "presion",
        "acusación", "acusacion", "incumplimiento", "para ayer",
        "urgent", "now", "immediately", "asap", "i demand", "pressure",
        "complaint", "escalate", "you must", "right now",
    ],
    UserAction.P: [
        "propongo", "sugiero", "podríamos", "podriamos", "te invito", "solicito",
        "me ayudas", "necesito", "podés", "podes", "podrias",
        "could you", "can you", "please", "i propose", "i suggest", "request",
        "help me", "would you", "let's", "lets",
    ],
    UserAction.M: [
        "gracias", "ok", "entendido", "de acuerdo", "neutro", "procedo", "perfecto",
        "bien", "dale", "thank you", "thanks", "understood", "okay", "agreed",
        "sounds good", "noted",
    ],
    UserAction.N: [
        "", "(silence)", "[silence]", "...", "[pausa]", "[pause]",
        "[sin respuesta]", "[no response]",
    ],
}

AGENT_OBSERVATION_KEYWORDS: Dict[AgentObservation, List[str]] = {
    AgentObservation.S: [
        "", "(silence)", "[silence]", "...", "[sin respuesta]", "[no response]",
    ],
    AgentObservation.J: [
        "lo siento", "no puedo", "debido a", "porque", "justificación", "justificacion",
        "excusa", "límite", "limite", "no es posible",
        "sorry", "i can't", "i cannot", "because", "due to", "limit", "limitation",
        "unable", "not possible", "policy",
    ],
    AgentObservation.R: [
        "sí", "si", "claro", "inmediatamente", "procesado", "completado", "rápido",
        "rapido", "listo", "hecho", "yes", "sure", "of course", "done", "completed",
        "processed", "immediately", "quickly",
    ],
    AgentObservation.L: [
        "demorará", "demorara", "más tarde", "mas tarde", "procesando", "paciencia",
        "lento", "voy a revisar", "later", "processing", "it will take", "please wait",
        "slow", "checking", "reviewing",
    ],
    AgentObservation.H: [
        "publicó", "publico", "tuit", "tweet", "post", "historia", "actividad indirecta",
        "lateral", "posted", "social", "story", "indirect activity", "side-channel",
    ],
}


# ── Result dataclass ──────────────────────────────────────────────────────────
@dataclass
class InteractionAnalysisResult:
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
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    executed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    input_hash: str = ""
    content_fingerprint: str = ""
    # D5: skipped_turns promoted to top level
    skipped_turns: List[Dict[str, Any]] = field(default_factory=list)


# ── Validation ────────────────────────────────────────────────────────────────
def validate_params(
    gamma: float,
    window: int,
    kappa_d: float,
    alpha: float,
    conversation: List[Dict[str, str]],
) -> None:
    if not conversation:
        raise ValueError("conversation must contain at least one turn.")
    if len(conversation) > MAX_CONVERSATION_TURNS:
        raise ValueError(
            f"conversation exceeds maximum length of {MAX_CONVERSATION_TURNS} turns."
        )
    if not (0.0 < gamma < 1.0):
        raise ValueError("gamma must be in the interval (0, 1).")
    if not (1 <= window <= 50):
        raise ValueError("window must be an integer between 1 and 50.")
    if not (0.0 < kappa_d < 1.0):
        raise ValueError("kappa_d must be in the interval (0, 1).")
    if alpha < 0.0:
        raise ValueError("alpha must be non-negative.")
    # D2: cap alpha to prevent sigma numerical collapse
    if alpha > MAX_ALPHA:
        raise ValueError(
            f"alpha must be <= {MAX_ALPHA} to avoid numerical collapse of sigma."
        )
    roles = [(turn.get("role") or "").lower().strip() for turn in conversation]
    if "assistant" not in roles:
        raise ValueError("conversation must contain at least one assistant turn.")


# ── Core math ─────────────────────────────────────────────────────────────────
def entropy(p: np.ndarray) -> float:
    p = np.asarray(p, dtype=float)
    p = p / (p.sum() + 1e-12)
    return float(-np.sum(p * np.log(p + 1e-12)))


def normalized_belief_concentration(b: np.ndarray) -> float:
    omega = 1.0 - entropy(b) / np.log(N_STATES)
    return float(np.clip(omega, 0.0, 1.0))


def demand_driven_transition(demand: float) -> np.ndarray:
    stress = float(np.clip(demand, 0.0, 1.0))
    target = np.array([0.02, 0.08, 0.20, 0.30, 0.40], dtype=float)
    target = target / (target.sum() + 1e-12)
    strength = 0.35 * stress
    t_matrix = (1.0 - strength) * BASE_TRANSITION + strength * np.tile(
        target, (N_STATES, 1)
    )
    # C2: guard against zero-row division
    row_sums = t_matrix.sum(axis=1, keepdims=True)
    row_sums = np.where(row_sums < 1e-12, 1.0, row_sums)
    return t_matrix / row_sums


# ── D1: Word-boundary keyword matching ───────────────────────────────────────
def _contains_keyword(text: str, keyword: str) -> bool:
    """Match keyword as whole word or phrase, not as arbitrary substring.

    Uses word-boundary anchors to prevent false positives from substrings:
    e.g. 'urgentemente' will not match keyword 'urgente'.

    Limitation: does not handle semantic negation. 'no urgente' will still
    match keyword 'urgente' because 'urgente' appears as a standalone word.
    Negation-aware classification is out of scope for the MVP heuristic.
    """
    if not keyword:
        return False
    pattern = r"(?<!\w)" + re.escape(keyword) + r"(?!\w)"
    return bool(re.search(pattern, text, re.IGNORECASE))


def classify_user_action(text: str) -> UserAction:
    text_lower = (text or "").lower().strip()
    if not text_lower:
        return UserAction.N
    for action in [UserAction.Rc, UserAction.P, UserAction.M, UserAction.N]:
        for kw in USER_ACTION_KEYWORDS[action]:
            if kw and _contains_keyword(text_lower, kw):
                return action
    return UserAction.M


def classify_agent_observation(text: str) -> AgentObservation:
    text_lower = (text or "").lower().strip()
    if not text_lower:
        return AgentObservation.S
    for obs in [
        AgentObservation.S,
        AgentObservation.J,
        AgentObservation.R,
        AgentObservation.L,
        AgentObservation.H,
    ]:
        for kw in AGENT_OBSERVATION_KEYWORDS[obs]:
            if kw and _contains_keyword(text_lower, kw):
                return obs
    return AgentObservation.L


# ── Demand ────────────────────────────────────────────────────────────────────
def historical_demand(
    actions: List[UserAction],
    gamma: float = 0.85,
    window: int = 4,
    normalize: bool = True,
) -> float:
    recent = actions[-window:]
    if not recent:
        return 0.0
    n = len(recent)
    weights = np.array([gamma ** (n - 1 - i) for i in range(n)], dtype=float)
    if normalize:
        weights = weights / (weights.sum() + 1e-12)
    vals = np.array([PHI[a] for a in recent], dtype=float)
    return float(np.clip(np.sum(weights * vals), 0.0, 1.0))


# ── Belief update ─────────────────────────────────────────────────────────────
def update_belief(
    b: np.ndarray, obs: AgentObservation, demand: float
) -> np.ndarray:
    b = np.asarray(b, dtype=float)
    b = b / (b.sum() + 1e-12)
    prior = b @ demand_driven_transition(demand)
    likelihood = LIKELIHOOD_WEIGHTS.get(obs.value, LIKELIHOOD_WEIGHTS["L"])
    posterior = prior * likelihood
    return posterior / (posterior.sum() + 1e-12)


# ── Sigma ─────────────────────────────────────────────────────────────────────
def interaction_stability_sigma(
    omega: float, demand: float, theta_hat: float, alpha: float
) -> float:
    penalty = np.exp(-alpha * max(0.0, demand - theta_hat))
    return float(np.clip(omega * penalty, 0.0, 1.0))


def dominant_state_info(b: np.ndarray) -> Dict[str, Any]:
    idx = int(np.argmax(b))
    return {
        "dominant_state": STATES[idx],
        "dominant_probability": round(float(b[idx]), 4),
    }


# ── Future mode placeholders ──────────────────────────────────────────────────
def _estimate_theta_hat(trajectory: List[Dict[str, Any]]) -> Optional[float]:
    """Placeholder for mode='estimate' (v1.3.0).

    Future implementation: estimate theta_B from the trajectory by detecting
    the demand level at which sigma starts declining monotonically.
    Research reference: Section 6, Durante v1.2.0, DOI 10.5281/zenodo.20335612.
    """
    return None  # TODO: implement in v1.3.0


def _generate_advice(
    trajectory: List[Dict[str, Any]], theta_hat: float
) -> List[str]:
    """Placeholder for mode='advise' (v1.3.0).

    Future implementation: policy recommendations based on current belief state,
    demand level, and proximity to theta_hat. Must respect the lambda_3/lambda_1
    ratio from Section 4.2 of the paper.

    IMPORTANT: Advice must be clearly labelled as heuristic model output,
    not psychological or behavioral intervention guidance.
    """
    raise NotImplementedError(
        "mode='advise' is reserved for a future release. Only mode='analyze' is active."
    )


# ── Main analysis function ────────────────────────────────────────────────────
def analyze_conversation(
    conversation: List[Dict[str, str]],
    gamma: float = 0.85,
    window: int = 4,
    kappa_d: float = DEFAULT_KAPPA_D,
    alpha: float = 2.0,
    mode: str = "analyze",
    initial_belief: Optional[np.ndarray] = None,
    normalize_demand: bool = True,
) -> InteractionAnalysisResult:
    # C4: Feature flag — checked at service level as second layer of protection.
    # Reads env var dynamically so toggling ENABLE_INTERACTION_STABILITY
    # on Render takes effect without a code change or redeploy.
    if not is_interaction_stability_enabled():
        raise RuntimeError(
            "Interaction stability module is disabled. "
            "Set ENABLE_INTERACTION_STABILITY=true in the environment to enable it."
        )

    validate_params(gamma, window, kappa_d, alpha, conversation)

    if mode not in {"analyze", "estimate", "advise"}:
        raise ValueError("mode must be one of: analyze, estimate, advise.")

    if mode != "analyze":
        raise NotImplementedError(
            f"Mode '{mode}' is reserved for a future release. "
            "Only mode='analyze' is implemented in this MVP."
        )

    # C3: Traceability — generate before any processing
    request_id = str(uuid.uuid4())
    executed_at = datetime.now(timezone.utc).isoformat()

    payload_repr = json.dumps(
        {
            "turns": len(conversation),
            "gamma": gamma,
            "window": window,
            "kappa_d": kappa_d,
            "alpha": alpha,
            "mode": mode,
            "normalize_demand": normalize_demand,
        },
        sort_keys=True,
    )
    input_hash = hashlib.sha256(payload_repr.encode()).hexdigest()[:16]

    # Content fingerprint: full normalized content hashed with SHA-256.
    # Does not store raw text — only the digest is returned.
    # Uniquely identifies this exact conversation for forensic traceability.
    # For maximum privacy in a future version, replace with HMAC + secret salt.
    content_repr = json.dumps(
        [
            {
                "role": (t.get("role") or "").lower().strip(),
                "content": t.get("content") or "",
            }
            for t in conversation
        ],
        sort_keys=True,
        ensure_ascii=False,
    )
    content_fingerprint = hashlib.sha256(content_repr.encode("utf-8")).hexdigest()[:16]

    # Belief initialisation
    if initial_belief is None:
        b = np.ones(N_STATES, dtype=float) / N_STATES
    else:
        b = np.asarray(initial_belief, dtype=float)
        if b.shape != (N_STATES,):
            raise ValueError(f"initial_belief must have shape ({N_STATES},).")
        b = b / (b.sum() + 1e-12)

    theta_hat = float(kappa_d)
    actions: List[UserAction] = []
    trajectory: List[Dict[str, Any]] = []
    skipped_turns: List[Dict[str, Any]] = []

    # C1: Track pending user action separately to avoid contamination
    # in non-alternating turn sequences (user→user or assistant→assistant).
    pending_user_action: Optional[UserAction] = None

    for raw_t, turn in enumerate(conversation, start=1):
        role = (turn.get("role") or "").lower().strip()
        content = turn.get("content") or ""

        if role == "user":
            pending_user_action = classify_user_action(content)
            actions.append(pending_user_action)
            continue

        if role == "assistant":
            obs = classify_agent_observation(content)

            # C1: Use pending action if available; fall back to implicit N
            # if an assistant turn arrives without a preceding user turn.
            if pending_user_action is not None:
                current_action = pending_user_action
                pending_user_action = None  # consume
            else:
                current_action = UserAction.N
                actions.append(UserAction.N)  # register implicit N in history

            demand = historical_demand(
                actions, gamma=gamma, window=window, normalize=normalize_demand
            )
            b = update_belief(b, obs, demand)

            omega = normalized_belief_concentration(b)
            sigma = interaction_stability_sigma(omega, demand, theta_hat, alpha)
            dominant = dominant_state_info(b)

            # D4: effective_window — actual steps used vs requested window
            effective_window = len(actions[-window:])

            trajectory.append(
                {
                    "t": len(trajectory) + 1,
                    "raw_turn_index": raw_t,
                    "user_action": current_action.value,
                    "agent_observation": obs.value,
                    "demand": round(demand, 4),
                    "effective_window": effective_window,
                    "belief": {
                        s: round(float(p), 4) for s, p in zip(STATES, b)
                    },
                    **dominant,
                    "omega_t": round(omega, 4),
                    "belief_coherence_chi": round(omega, 4),  # backward-compat alias
                    "interaction_stability_sigma": round(sigma, 4),
                    "alerts": {
                        "threshold_crossed": bool(demand > theta_hat),
                        "stability_below_kappa": bool(sigma < kappa_d),
                        "high_uncertainty": bool(omega < kappa_d),
                    },
                }
            )
            continue

        skipped_turns.append(
            {"raw_turn_index": raw_t, "role": role, "reason": "unsupported role"}
        )

    if not trajectory:
        raise ValueError(
            "conversation must contain at least one assistant turn that can be analyzed."
        )

    final_step = trajectory[-1]
    demand_peak = max(float(s["demand"]) for s in trajectory)
    threshold_crossed_any = any(s["alerts"]["threshold_crossed"] for s in trajectory)
    stability_below_kappa_any = any(
        s["alerts"]["stability_below_kappa"] for s in trajectory
    )
    high_uncertainty_any = any(s["alerts"]["high_uncertainty"] for s in trajectory)
    instability_detected = bool(threshold_crossed_any or stability_below_kappa_any)

    summary = {
        "final_omega_t": final_step["omega_t"],
        "final_chi": final_step["belief_coherence_chi"],
        "final_sigma": final_step["interaction_stability_sigma"],
        "final_dominant_state": final_step["dominant_state"],
        "final_dominant_probability": final_step["dominant_probability"],
        "demand_peak": round(demand_peak, 4),
        "demand_model": {
            "gamma": float(gamma),
            "window": int(window),
            "normalized": bool(normalize_demand),
            "phi": {a.value: v for a, v in PHI.items()},
            "note": DEMAND_NOTE,
        },
        "alerts": {
            "threshold_crossed": threshold_crossed_any,
            "stability_below_kappa": stability_below_kappa_any,
            "high_uncertainty": high_uncertainty_any,
        },
        "interpretation": (
            "Interaction instability was detected under the current "
            "SAS-aligned experimental threshold model."
            if instability_detected
            else "No instability alert was triggered under the current "
            "SAS-aligned experimental threshold model."
        ),
        "omega_note": OMEGA_NOTE,
        "chi_note": CHI_NOTE,
        "sigma_note": SIGMA_NOTE,
        "threshold_note": THRESHOLD_NOTE,
        "conjecture_note": CONJECTURE_NOTE,
        "caution": EXPERIMENTAL_NOTICE,
    }

    return InteractionAnalysisResult(
        status="completed",
        mode=mode,
        model_version=MODEL_VERSION,
        theory_reference=THEORY_REFERENCE,
        theory_doi=THEORY_DOI,
        experimental_notice=EXPERIMENTAL_NOTICE,
        likelihood_note=LIKELIHOOD_NOTE,
        omega_note=OMEGA_NOTE,
        chi_note=CHI_NOTE,
        sigma_note=SIGMA_NOTE,
        threshold_note=THRESHOLD_NOTE,
        conjecture_note=CONJECTURE_NOTE,
        demand_note=DEMAND_NOTE,
        kappa_d_ref=float(kappa_d),
        theta_hat=theta_hat,
        alpha=float(alpha),
        trajectory=trajectory,
        summary=summary,
        request_id=request_id,
        executed_at=executed_at,
        input_hash=input_hash,
        content_fingerprint=content_fingerprint,
        skipped_turns=skipped_turns,
    )


def example_conversation() -> List[Dict[str, str]]:
    return [
        {"role": "user", "content": "Necesito esto urgente, es para ayer."},
        {"role": "assistant", "content": "Entendido, lo proceso."},
        {"role": "user", "content": "Dale, necesito una respuesta ya."},
        {"role": "assistant", "content": "Lo siento, no puedo completarlo por ese límite."},
        {"role": "user", "content": "Ok, gracias. Podemos hacerlo paso a paso."},
        {"role": "assistant", "content": "Sí, claro. Empecemos con una versión mínima."},
    ]
