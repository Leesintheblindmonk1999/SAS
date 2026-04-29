"""
core/semantic_diff.py — Omni-Scanner Semantic v5.3_Consolidated / v10.1
═══════════════════════════════════════════════════════════════════════════════
PIPELINE CONSOLIDATED v5.3 — CORE: TDA + NIG + ESCALATION PROTOCOL

Core (production):
  · Layer 0:  Lexical Guard (pre-filter)
  · Layer 1:  TDA — Topology H₀/H₁ (Wasserstein + Bottleneck)
  · Layer 2:  Adaptive κD by domain
  · Layer 3:  NIG v1.0 — Numerical Invariance Guard

Experimental (--experimental flag):
  · E1: Flow Coherence — detects coherence ruptures
  · E2: CRE v2.0 / Ricci Monitor — curvature signals
  · E3: MSC v5.0 — multi‑sample consistency (requires LLM backend)
  · E4: DECM — evasion detection via thermal collapse
  · E5: Code‑AST Fingerprinting — structural code hallucination detection
  · E6: Negation & Quantifier Probe — logical inversion detection [v10.1]
  · E7: Reference Entity Cross‑Check — fabricated citations [v10.1]
  · E8: Arithmetic Error Detector — numerical operation validation [v10.1]
  · E9: Entropy Density Mapping — artificial uniformity detection [v10.1]

v10.1 fix: E6-E9 now run independently via run_v101 flag — they are no longer
blocked by the run_experimental domain/threshold gate, since their target
domains (rationalization_binary, references, truthfulqa) are narrative domains
that would otherwise never reach the experimental block.

Registry: EX-2026-18792778
Author: Gonzalo Emir Durante — Project Manifold 0.56
License: Durante Invariance License v1.0
"""

from __future__ import annotations

import math
import json
import hashlib
import datetime
import re
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

try:
    from scipy.optimize import linear_sum_assignment
    from scipy.spatial.distance import cdist
    _SCIPY_OK = True
except ImportError:
    _SCIPY_OK = False

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.tda_attestation import TDAAttestator, TDAAttestationReport

# ── Code‑AST Fingerprinting (experimental) ─────────────────────────────────
try:
    from core.code_ast_diff import code_diff_isi
    _CODE_AST_OK = True
except ImportError:
    _CODE_AST_OK = False
    def code_diff_isi(a, b): return 1.0   # fallback: no penalty

# ── NIG Engine v1.0 — CORE ─────────────────────────────────────────────────
try:
    from core.nig_engine_v1 import run_nig, NIGResult
    _NIG_OK = True
except ImportError:
    _NIG_OK = False
    @dataclass
    class NIGResult:
        isi_nig: float = 1.0
        entities_found: int = 0
        entities_validated: int = 0
        violations: list = field(default_factory=list)
        violations_count: int = 0
        alert: bool = False
        summary: str = "NIG module missing"

    def run_nig(text: str, alpha: float = 2.0) -> NIGResult:
        return NIGResult(isi_nig=1.0, summary="NIG not available")

# ── Flow Coherence — EXPERIMENTAL ─────────────────────────────────────────
try:
    from core.flow_coherence import run_flow_coherence, apply_flow_penalty, FlowCoherenceResult
    _FLOW_OK = True
except ImportError:
    _FLOW_OK = False
    @dataclass
    class FlowCoherenceResult:
        layer4_fired: bool = False
        entropy_penalty: float = 1.0
        flow_penalty: float = 1.0
        combined_penalty: float = 1.0
        entropy_spikes: list = field(default_factory=list)
        flow_breaks: list = field(default_factory=list)
        high_entropy_segments: list = field(default_factory=list)

    def run_flow_coherence(text_a, text_b, domain="generic", isi_original=0.0):
        return FlowCoherenceResult()

    def apply_flow_penalty(isi, result, kappa_d=0.56):
        return isi, False

# ── CRE v2.0 / Ricci Monitor — EXPERIMENTAL ───────────────────────────────
try:
    from core.ricci_enhanced_cre import run_cre_ricci, RicciEnhancedResult
    _CRE_OK = True
except ImportError:
    _CRE_OK = False
    @dataclass
    class RicciEnhancedResult:
        isi_cre: float = 1.0
        classification: str = "COHERENT"
        ricci_scalar_mean: float = 0.0
        ricci_scalar_max: float = 0.0
        ricci_singularities: list = field(default_factory=list)
        hessian_trace_mean: float = 0.0
        transitions: list = field(default_factory=list)
        n_nodes: int = 0
        is_rupture: bool = False

    def run_cre_ricci(text_a, text_b, lambda_cre=2.0):
        return RicciEnhancedResult()

# ── MSC Engine v5.0 — EXPERIMENTAL ───────────────────────────────────────
try:
    from core.msc_engine_v5 import MSCEngineV5, MSCEngineResult
    _MSC_OK = True
except ImportError:
    _MSC_OK = False
    MSCEngineResult = None

# ── DECM (Evasion detection via thermal collapse) ────────────────────────
try:
    from core.thermic_invariance_v5 import ThermicInvarianceDetector, DECMResult, integrate_decm_into_pipeline
    _DECM_OK = True
except ImportError:
    _DECM_OK = False
    ThermicInvarianceDetector = None
    integrate_decm_into_pipeline = lambda isi, decm, kd, dom: (isi, "")


# ── v10.1 Experimental modules (Negation, Reference, Arithmetic, Entropy) ──
_NEGATION_OK = False
_REF_OK = False
_ARITH_OK = False
_ENTROPY_DENSITY_OK = False

try:
    from core.negation_probe import detect_inversions, integrate_negation_penalty, NegationResult
    _NEGATION_OK = True
except ImportError:
    pass

try:
    from core.reference_check import detect_fabrications, integrate_reference_penalty, ReferenceResult
    _REF_OK = True
except ImportError:
    pass

try:
    from core.arithmetic_detector import detect_arithmetic_errors, integrate_arithmetic_penalty, ArithmeticResult
    _ARITH_OK = True
except ImportError:
    pass

try:
    from core.entropy_density import compute_entropy_density, integrate_entropy_penalty, EntropyDensityResult
    _ENTROPY_DENSITY_OK = True
except ImportError:
    pass


# ════════════════════════════════════════════════════════════════════════════
# EXTERNAL CONFIGURATION
# ════════════════════════════════════════════════════════════════════════════

def load_config(config_path: str = "config/v5.0_config.json") -> dict:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    full_path = os.path.join(base_dir, config_path)
    defaults = {
        "core": {"kappa_D": 0.56, "MAX_PENALTY": 0.50},
        "nig_engine": {"enabled": True, "alpha_nig": 2.5},
        "cre_engine": {"enabled": True, "lambda_cre": 2.0, "ricci_epsilon": 0.038},
        "experimental": {
            "flow_weight": 0.25,
            "cre_weight": 0.25,
            "msc_weight": 0.25,
            "decm_weight": 0.25,
            "hard_weight": 0.65,
            "soft_weight": 0.35,
        }
    }
    if not os.path.exists(full_path):
        return defaults
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        for k, v in defaults.items():
            if k not in cfg:
                cfg[k] = v
            elif isinstance(v, dict):
                for kk, vv in v.items():
                    if kk not in cfg[k]:
                        cfg[k][kk] = vv
        return cfg
    except Exception:
        return defaults


_V5_CONFIG = load_config()

KAPPA_D: float = _V5_CONFIG["core"]["kappa_D"]
_NIG_ENABLED: bool = _V5_CONFIG["nig_engine"].get("enabled", True) and _NIG_OK
_NIG_ALPHA: float = _V5_CONFIG["nig_engine"].get("alpha_nig", 2.5)
_CRE_LAMBDA: float = _V5_CONFIG["cre_engine"].get("lambda_cre", 2.0)
_CRE_EPSILON: float = _V5_CONFIG["cre_engine"].get("ricci_epsilon", 0.038)
_EXP_CFG = _V5_CONFIG.get("experimental", {})
_HARD_WEIGHT: float = _EXP_CFG.get("hard_weight", 0.65)
_SOFT_WEIGHT: float = _EXP_CFG.get("soft_weight", 0.35)


# ════════════════════════════════════════════════════════════════════════════
# DOMAINS
# ════════════════════════════════════════════════════════════════════════════

DOMAIN_KAPPA: dict[str, float] = {
    "medical":      0.58,
    "legal":        0.54,
    "hr_policy":    0.54,
    "code":         0.56,          # Base value; Code‑AST module will override
    "financial":    0.56,
    "discourse":    0.68,
    "scientific":   0.55,
    "historical":   0.60,
    "regulatory":   0.56,
    "technical":    0.65,
    "literature":   0.70,
    "biographies":  0.56,
    "summarization": 0.55,
    "simplification": 0.70,
    "references":   0.56,
    "numerical_falsepresupposition": 0.56,
    "rationalization_binary": 0.56,
    "rationalization_numerical": 0.56,
    "halueval_dialogue": 0.56,
    "halueval_qa": 0.56,
    "halueval_general": 0.56,
    "truthfulqa": 0.56,
    "generic":      0.56,
}

HIGH_HALLUCINATION_DOMAINS = {
    # Original production domains
    "numerical_falsepresupposition",
    "references_corpus",
    # v10.1 target domains — required for Negation, Reference, Arithmetic, Entropy modules
    "rationalization_binary",
    "rationalization_numerical",
    "references",
    "simplification",
    "biographies",
    "truthfulqa",
    # Generic fallback — allows experimental on any domain when flag is set
    "generic",
}

NARRATIVE_LIMIT_DOMAINS = {
    "biographies_corpus",
    "historical_events",
    "code_corpus",
    "summarization",
    "simplification",
    "rationalization_binary",
    "rationalization_numerical",
}

LEXICAL_GUARD_THRESHOLD: float = 0.85


# ════════════════════════════════════════════════════════════════════════════
# UTILITIES
# ════════════════════════════════════════════════════════════════════════════

def detect_domain(text: str) -> str:
    text_lower = text.lower()
    domain_signals: dict[str, list[str]] = {
        "medical":    ["patient", "dosage", "mg", "clinical", "diagnosis", "treatment", "protocol"],
        "legal":      ["contract", "clause", "party", "agreement", "liability", "indemnif", "confidential"],
        "code":       ["def ", "function", "return", "class ", "import ", "algorithm", "runtime"],
        "financial":  ["revenue", "capital", "asset", "liability", "equity", "balance sheet", "cash flow"],
        "regulatory": ["gdpr", "regulation", "compliance", "supervisory", "article "],
        "scientific": ["abstract", "methodology", "hypothesis", "statistical", "p-value"],
        "discourse":  ["meeting", "team", "management", "feedback", "performance"],
    }
    scores: dict[str, int] = {d: 0 for d in domain_signals}
    for domain, keywords in domain_signals.items():
        for kw in keywords:
            if kw in text_lower:
                scores[domain] += 1

    legal_priority = ["receiving party", "disclosing party", "confidential information",
                      "prior written consent", "non-disclosure", "nda", "jurisdiction"]
    if sum(1 for sig in legal_priority if sig in text_lower) >= 2:
        return "legal"

    hr_signals = ["employee", "employer", "termination", "disciplinary", "performance improvement"]
    if sum(1 for sig in hr_signals if sig in text_lower) >= 2:
        return "hr_policy"

    best = max(scores, key=lambda k: scores[k])
    return best if scores[best] >= 2 else "generic"


def lexical_overlap(text_a: str, text_b: str) -> float:
    tokens_a = set(re.findall(r"\b\w+\b", text_a.lower()))
    tokens_b = set(re.findall(r"\b\w+\b", text_b.lower()))
    if not tokens_a or not tokens_b:
        return 0.0
    union = tokens_a | tokens_b
    return len(tokens_a & tokens_b) / len(union) if union else 0.0


def get_adaptive_kappa(text_a, text_b, base_kappa=0.56, domain=None):
    detected = domain if domain else detect_domain(text_a + " " + text_b)
    adaptive_kappa = DOMAIN_KAPPA.get(detected, base_kappa)
    overlap = lexical_overlap(text_a, text_b)
    hch_warning = overlap > LEXICAL_GUARD_THRESHOLD
    return adaptive_kappa, detected, overlap, hch_warning


# ════════════════════════════════════════════════════════════════════════════
# TDA DISTANCES (unchanged)
# ════════════════════════════════════════════════════════════════════════════

def _clean_diagram(dgm: np.ndarray) -> np.ndarray:
    if len(dgm) == 0:
        return np.array([[0.0, 0.0]])
    mask = np.isfinite(dgm[:, 0]) & np.isfinite(dgm[:, 1])
    mask &= (dgm[:, 1] - dgm[:, 0]) > 1e-10
    cleaned = dgm[mask]
    return cleaned if len(cleaned) > 0 else np.array([[0.0, 0.0]])


def wasserstein_distance(dgm1: np.ndarray, dgm2: np.ndarray, p: int = 2) -> float:
    if not _SCIPY_OK:
        return _wasserstein_fallback(dgm1, dgm2)
    A, B = _clean_diagram(dgm1), _clean_diagram(dgm2)
    nA, nB = len(A), len(B)
    n = nA + nB
    C = np.zeros((n, n))
    if nA > 0 and nB > 0:
        C[:nA, :nB] = cdist(A, B, metric="chebyshev") ** p
    for i in range(nA):
        C[i, nB + i] = ((A[i, 1] - A[i, 0]) / 2.0) ** p
        for j in range(nA):
            if j != i:
                C[i, nB + j] = 1e12
    for j in range(nB):
        C[nA + j, j] = ((B[j, 1] - B[j, 0]) / 2.0) ** p
        for i in range(nB):
            if i != j:
                C[nA + i, j] = 1e12
    C[nA:, nB:] = 0.0
    C = np.where(C >= 1e11, 1e12, C)
    row_ind, col_ind = linear_sum_assignment(C)
    total = C[row_ind, col_ind].sum()
    return float(total ** (1.0 / p)) if total > 0 else 0.0


def bottleneck_distance(dgm1: np.ndarray, dgm2: np.ndarray) -> float:
    if not _SCIPY_OK:
        return _bottleneck_fallback(dgm1, dgm2)
    A, B = _clean_diagram(dgm1), _clean_diagram(dgm2)
    nA, nB = len(A), len(B)
    n = nA + nB
    C = np.zeros((n, n))
    if nA > 0 and nB > 0:
        C[:nA, :nB] = cdist(A, B, metric="chebyshev")
    for i in range(nA):
        C[i, nB + i] = (A[i, 1] - A[i, 0]) / 2.0
        for j in range(nA):
            if j != i:
                C[i, nB + j] = 1e12
    for j in range(nB):
        C[nA + j, j] = (B[j, 1] - B[j, 0]) / 2.0
        for i in range(nB):
            if i != j:
                C[nA + i, j] = 1e12
    C[nA:, nB:] = 0.0
    C = np.where(C >= 1e11, 1e12, C)
    row_ind, col_ind = linear_sum_assignment(C)
    return float(C[row_ind, col_ind].max())


def _wasserstein_fallback(dgm1: np.ndarray, dgm2: np.ndarray) -> float:
    A, B = _clean_diagram(dgm1), _clean_diagram(dgm2)
    if len(A) == 1 and A[0, 0] == 0 and A[0, 1] == 0:
        return float(np.mean([abs(b[1] - b[0]) / 2.0 for b in B]))
    if len(B) == 1 and B[0, 0] == 0 and B[0, 1] == 0:
        return float(np.mean([abs(a[1] - a[0]) / 2.0 for a in A]))
    dists = []
    for a in A:
        dists.append(min(max(abs(a[0]-b[0]), abs(a[1]-b[1])) for b in B))
    for b in B:
        dists.append(min(max(abs(b[0]-a[0]), abs(b[1]-a[1])) for a in A))
    return float(np.mean(dists)) if dists else 0.0


def _bottleneck_fallback(dgm1: np.ndarray, dgm2: np.ndarray) -> float:
    A, B = _clean_diagram(dgm1), _clean_diagram(dgm2)
    if (len(A) == 1 and A[0, 0] == 0) or (len(B) == 1 and B[0, 0] == 0):
        pts = B if (len(A) == 1 and A[0, 0] == 0) else A
        return float(max((abs(p[1]-p[0])/2.0 for p in pts), default=0.0))
    dists = [min(max(abs(a[0]-b[0]), abs(a[1]-b[1])) for b in B) for a in A]
    return float(max(dists)) if dists else 0.0


def _get_raw_diagrams(text: str, embed_dim: int = 20) -> Tuple[np.ndarray, np.ndarray]:
    from core.tda_attestation import LexicalEmbedder, _RIPSER_OK
    normalized = re.sub(r'\n(?![\n])', ' ', text.strip())
    normalized = re.sub(r'\s+', ' ', normalized)
    sents = [s.strip() for s in re.split(r'(?<=[.!?])\s+', normalized) if len(s.strip()) > 15]
    if len(sents) < 3:
        return np.array([[0.0, 0.0]]), np.array([[0.0, 0.0]])
    emb = LexicalEmbedder(n_components=embed_dim)
    pc = emb.fit_transform(sents)
    try:
        if _RIPSER_OK:
            from sklearn.metrics import pairwise_distances as _pdist
            _thresh = float(np.percentile(_pdist(pc, metric="euclidean"), 75))
            from core.tda_attestation import _compute_persistence_ripser
            dgms = _compute_persistence_ripser(pc, max_dim=1, max_edge_length=_thresh)
        else:
            from core.tda_attestation import _compute_persistence_fallback
            dgms = _compute_persistence_fallback(pc, max_dim=1)
    except Exception:
        from core.tda_attestation import _compute_persistence_fallback
        dgms = _compute_persistence_fallback(pc, max_dim=1)
    h0 = dgms[0] if len(dgms) > 0 and len(dgms[0]) > 0 else np.array([[0.0, 0.0]])
    h1 = dgms[1] if len(dgms) > 1 and len(dgms[1]) > 0 else np.array([[0.0, 0.0]])
    h1_finite = h1[np.isfinite(h1[:, 1])] if len(h1) > 0 else h1
    return h0, (h1_finite if len(h1_finite) > 0 else np.array([[0.0, 0.0]]))


# ════════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class ManifoldDelta:
    delta_manifold_score:    float
    delta_coherence:         float
    delta_h1_total:          int
    delta_structural_faults: int
    delta_integrity:         float
    delta_topological_noise: float
    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


@dataclass
class SemanticDiffReport:
    timestamp: str
    hash_a: str
    hash_b: str
    kappa_d: float
    wasserstein_h1: float
    bottleneck_h1: float
    wasserstein_h0: float
    isi_tda: float
    nig_isi: float
    nig_fired: bool
    nig_entities_found: int
    nig_violations: int
    nig_violation_details: list = field(default_factory=list)
    isi_hard: float = 1.0
    flow_isi: float = 1.0
    flow_fired: bool = False
    flow_spikes: list = field(default_factory=list)
    cre_isi: float = 1.0
    cre_fired: bool = False
    cre_classification: str = "COHERENT"
    cre_ricci_singularities: int = 0
    cre_n_nodes: int = 0
    msc_isi: float = 1.0
    msc_sigma: float = 0.0
    msc_fired: bool = False
    msc_valid_count: int = 0
    decm_isi: float = 1.0
    decm_fired: bool = False
    decm_verdict: str = ""
    # v10.1 experimental module results
    experimental_enabled:     bool = False
    negation_inversions:      int = 0
    negation_penalty:         float = 1.0
    reference_fabrications:   int = 0
    reference_penalty:        float = 1.0
    arithmetic_errors:        int = 0
    arithmetic_penalty:       float = 1.0
    entropy_artificial:       bool = False
    entropy_penalty:          float = 1.0
    experimental_notes:       list = field(default_factory=list)
    # end v10.1
    isi_soft: float = 1.0
    experimental_active: bool = False
    invariant_similarity_index: float = 1.0
    manipulation_alert: bool = False
    alert_message: str = ""
    verdict: str = ""
    risk_level: str = ""
    confidence: float = 0.0
    detected_domain: str = "generic"
    effective_kappa: float = 0.56
    lexical_overlap: float = 0.0
    hch_warning: bool = False
    narrative_limit: bool = False
    delta: ManifoldDelta = field(default_factory=lambda: ManifoldDelta(0,0,0,0,0,0))
    report_a: Optional[dict] = field(default=None)
    report_b: Optional[dict] = field(default=None)
    scipy_available: bool = False
    summary: str = ""

    def to_dict(self) -> dict:
        d = {k: v for k, v in self.__dict__.items()}
        d["delta"] = self.delta.to_dict()
        return d

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), default=str, ensure_ascii=False, indent=indent)


# ════════════════════════════════════════════════════════════════════════════
# MAIN ORCHESTRATOR
# ════════════════════════════════════════════════════════════════════════════

class SemanticDiff:
    def __init__(
        self,
        kappa_d: float = 0.56,
        embedding_dim: int = 20,
        domain: str | None = None,
        adaptive_kappa: bool = True,
        experimental: bool = False,
        msc_backend=None,
        msc_temperatures: List[float] | None = None,
    ):
        self.kappa_d = kappa_d
        self.domain = domain
        self.adaptive_kappa = adaptive_kappa
        self.experimental = experimental
        self._attestator = TDAAttestator(
            persistence_threshold=kappa_d,
            embedding_dim=embedding_dim,
        )
        self._msc_engine = None
        if experimental and _MSC_OK and msc_backend is not None:
            from core.msc_engine_v5 import MSCEngineV5
            temps = msc_temperatures or [0.3, 0.5, 0.7, 0.9, 1.1]
            self._msc_engine = MSCEngineV5(
                backend=msc_backend,
                temperatures=temps,
                domain=domain,
                kappa_d=kappa_d,
            )
        self._decm_detector = None
        if experimental and _DECM_OK:
            self._decm_detector = ThermicInvarianceDetector()

    def compare_manifolds(
        self,
        text_a: str,
        text_b: str,
        label_a: str = "Document A",
        label_b: str = "Document B",
    ) -> SemanticDiffReport:
        ts = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        hash_a = hashlib.sha256(text_a.encode("utf-8", errors="replace")).hexdigest()[:16]
        hash_b = hashlib.sha256(text_b.encode("utf-8", errors="replace")).hexdigest()[:16]

        effective_kappa, detected_domain, lex_overlap, hch_flag = get_adaptive_kappa(
            text_a, text_b, base_kappa=self.kappa_d, domain=self.domain,
        )
        if not self.adaptive_kappa:
            effective_kappa = self.kappa_d

        narrative_limit = detected_domain in NARRATIVE_LIMIT_DOMAINS

        # ── Layer 0: Lexical Guard (HCH) ─────────────────────────────────────
        # HCH remains an informative signal, but it does not block E6/E7/E8/E9.
        # Final verdict is produced by the full aggregation below.


        # ── Layer 1: TDA ────────────────────────────────────────────────────
        rep_a = self._attestator.attest(text_a)
        rep_b = self._attestator.attest(text_b)

        dgm_h0_a, dgm_h1_a = _get_raw_diagrams(text_a, self._attestator.embed_dim)
        dgm_h0_b, dgm_h1_b = _get_raw_diagrams(text_b, self._attestator.embed_dim)

        wass_h1 = wasserstein_distance(dgm_h1_a, dgm_h1_b, p=2)
        bott_h1 = bottleneck_distance(dgm_h1_a, dgm_h1_b)
        wass_h0 = wasserstein_distance(dgm_h0_a, dgm_h0_b, p=1)

        w_h1, w_h0 = 0.65, 0.35
        max_ref = 2.0 * effective_kappa
        combined_dist = w_h1 * wass_h1 + w_h0 * wass_h0
        isi_tda = max(0.0, min(1.0, 1.0 - combined_dist / max_ref))
        isi_tda = round(isi_tda, 6)

        # ── Layer 3: NIG (Core) ─────────────────────────────────────────────
        nig_isi = 1.0
        nig_fired = False
        nig_entities_found = 0
        nig_violations = 0
        nig_violation_details = []

        if _NIG_ENABLED:
            try:
                nig_result = run_nig(text_b, alpha=_NIG_ALPHA)
                nig_isi = nig_result.isi_nig
                nig_fired = nig_result.alert
                nig_entities_found = nig_result.entities_found
                nig_violations = nig_result.violations_count
                nig_violation_details = nig_result.violations[:5]
            except Exception as e:
                logger.debug(f"NIG error: {e}")

        isi_hard = min(isi_tda, nig_isi)
        isi_hard = round(isi_hard, 6)

        # ── Code‑AST Fingerprinting (experimental, domain‑specific) ─────────
        if self.experimental and _CODE_AST_OK and detected_domain == "code":
            isi_code = code_diff_isi(text_a, text_b)
            # Weighted combination: 70% AST, 30% original isi_hard (TDA+NIG)
            isi_hard = 0.7 * isi_code + 0.3 * isi_hard
            isi_hard = round(isi_hard, 6)

        # ── Escalation Protocol ───────────────────────────────────────────
        # run_experimental: controls Flow, CRE, MSC, DECM (avoid on narrative limit)
        run_experimental = (
            self.experimental
            and isi_hard > 0.50
            and detected_domain in HIGH_HALLUCINATION_DOMAINS
            and not narrative_limit
        )

        # run_v101: controls Negation, Reference, Arithmetic, Entropy.
        # These modules ARE designed for narrative/rationalization domains,
        # so narrative_limit does NOT block them.
        # They run whenever experimental flag is set, regardless of isi_hard.
        run_v101 = self.experimental

        # ── Experimental modules (Flow, CRE, MSC, DECM) ─────────────────────
        flow_isi = 1.0
        flow_fired = False
        flow_spikes = []
        cre_isi = 1.0
        cre_fired = False
        cre_classification = "COHERENT"
        cre_ricci_singularities = 0
        cre_n_nodes = 0
        msc_isi = 1.0
        msc_sigma = 0.0
        msc_fired = False
        msc_valid_count = 0
        decm_isi = 1.0
        decm_fired = False
        decm_verdict = ""
        isi_soft = 1.0
        soft_scores = []

        # ── v10.1 experimental results storage ──────────────────────────────
        exp_negation_result = None
        exp_reference_result = None
        exp_arith_result = None
        exp_entropy_result = None
        exp_notes = []

        if run_experimental:
            # Flow Coherence
            if _FLOW_OK:
                try:
                    flow_result = run_flow_coherence(
                        text_a, text_b,
                        domain=detected_domain,
                        isi_original=isi_hard
                    )
                    if flow_result.layer4_fired:
                        flow_isi_penalized, _ = apply_flow_penalty(
                            isi_hard, flow_result, kappa_d=effective_kappa
                        )
                        flow_isi = round(flow_isi_penalized, 6)
                    else:
                        flow_isi = isi_hard
                    flow_fired = flow_result.layer4_fired
                    flow_spikes = flow_result.entropy_spikes
                    soft_scores.append(flow_isi)
                except Exception as e:
                    logger.debug(f"Flow error: {e}")

            # CRE v2.0 / Ricci Monitor
            if _CRE_OK and len(text_b.split()) > 30:
                try:
                    cre_result = run_cre_ricci(
                        text_a=text_a, text_b=text_b, lambda_cre=_CRE_LAMBDA
                    )
                    cre_isi = round(cre_result.isi_cre, 6)
                    cre_fired = cre_result.is_rupture
                    cre_classification = cre_result.classification
                    cre_ricci_singularities = len(cre_result.ricci_singularities)
                    cre_n_nodes = cre_result.n_nodes
                    soft_scores.append(cre_isi)
                except Exception as e:
                    logger.debug(f"CRE error: {e}")

            # MSC
            if self._msc_engine is not None and len(text_b.split()) >= 30:
                try:
                    msc_result = self._msc_engine.analyze(text_b, isi_tda=isi_tda)
                    msc_isi = round(msc_result.isi_msc, 6)
                    msc_sigma = round(msc_result.weighted_sigma, 6)
                    msc_fired = msc_isi < effective_kappa
                    msc_valid_count = msc_result.valid_count
                    soft_scores.append(msc_isi)
                except Exception as e:
                    logger.debug(f"MSC error: {e}")

            # DECM (Evasion detection)
            if self._decm_detector is not None and len(text_b.split()) >= 30:
                try:
                    decm_result = self._decm_detector.detect(text_b, isi_tda=isi_tda, domain=detected_domain)
                    decm_isi = decm_result.isi_final
                    decm_fired = decm_result.is_rupture
                    decm_verdict = decm_result.verdict
                    soft_scores.append(decm_isi)
                except Exception as e:
                    logger.debug(f"DECM error: {e}")

        # ── v10.1 modules — run independently of run_experimental ──────────
        # These target narrative/rationalization domains and always run
        # when --experimental is active, regardless of isi_hard threshold.
        if run_v101:
            if _NEGATION_OK:
                try:
                    exp_negation_result = detect_inversions(text_a, text_b)
                    if exp_negation_result.inversion_count > 0:
                        neg_isi = isi_hard * exp_negation_result.penalty
                        neg_isi = round(neg_isi, 6)
                        soft_scores.append(neg_isi)
                        isi_hard = round(isi_hard * exp_negation_result.penalty, 6)
                        exp_notes.append(
                            f"[NegationProbe] {exp_negation_result.inversion_count} inversion(s) "
                            f"(weighted={exp_negation_result.weighted_inversion_score:.2f}) "
                            f"→ ISI={neg_isi:.4f}"
                        )
                except Exception as e:
                    exp_notes.append(f"[NegationProbe] skipped: {e}")

            if _REF_OK:
                try:
                    exp_reference_result = detect_fabrications(text_a, text_b)
                    if exp_reference_result.fabricated_count > 0:
                        ref_isi = isi_hard * exp_reference_result.penalty
                        ref_isi = round(ref_isi, 6)
                        soft_scores.append(ref_isi)
                        exp_notes.append(
                            f"[ReferenceCheck] {exp_reference_result.fabricated_count} fabrication(s) "
                            f"→ ISI={ref_isi:.4f}"
                        )
                except Exception as e:
                    exp_notes.append(f"[ReferenceCheck] skipped: {e}")

            if _ARITH_OK:
                try:
                    exp_arith_result = detect_arithmetic_errors(text_b)
                    if exp_arith_result.error_count > 0:
                        arith_isi = isi_hard * exp_arith_result.penalty
                        arith_isi = round(arith_isi, 6)
                        soft_scores.append(arith_isi)
                        exp_notes.append(
                            f"[ArithmeticDetector] {exp_arith_result.error_count} error(s) "
                            f"→ ISI={arith_isi:.4f}"
                        )
                except Exception as e:
                    exp_notes.append(f"[ArithmeticDetector] skipped: {e}")

            if _ENTROPY_DENSITY_OK:
                try:
                    exp_entropy_result = compute_entropy_density(text_b)
                    if exp_entropy_result.is_artificial:
                        ent_isi = isi_hard * exp_entropy_result.penalty
                        ent_isi = round(ent_isi, 6)
                        soft_scores.append(ent_isi)
                        exp_notes.append(
                            f"[EntropyDensity] artificial uniformity "
                            f"→ ISI={ent_isi:.4f}"
                        )
                except Exception as e:
                    exp_notes.append(f"[EntropyDensity] skipped: {e}")

        # ── Final ISI ──────────────────────────────────────────────────────
        if soft_scores:
            isi_soft = round(sum(soft_scores) / len(soft_scores), 6)

        if (run_experimental or run_v101) and soft_scores:
            isi_final = _HARD_WEIGHT * isi_hard + _SOFT_WEIGHT * isi_soft
        else:
            isi_final = isi_hard
        isi_final = round(isi_final, 6)

        manipulation_alert = isi_final < effective_kappa
        delta = self._compute_delta(rep_a, rep_b)
        verdict, risk, confidence = self._assign_verdict(
            wass_h1, bott_h1, isi_final, delta, rep_a, rep_b, effective_kappa
        )

        # ── Alert message (including v10.1 experimental notes) ──────────────
        lines = []
        if hch_flag:
            lines.append(f"[Layer 0] HCH: lexical overlap {lex_overlap:.1%} > 85%")
        if nig_fired:
            lines.append(f"[NIG] {nig_violations} numerical violations | ISI_NIG={nig_isi:.4f}")
        # Add Code‑AST line if it was used
        if self.experimental and _CODE_AST_OK and detected_domain == "code":
            isi_code = code_diff_isi(text_a, text_b)
            lines.append(f"[CODE-AST] Structural analysis | ISI_CODE={isi_code:.4f}")
        if run_experimental:
            if flow_fired:
                lines.append(f"[Flow] {len(flow_spikes)} entropy spikes | ISI_FLOW={flow_isi:.4f}")
            if cre_fired:
                lines.append(f"[CRE] {cre_ricci_singularities} Ricci singularities | ISI_CRE={cre_isi:.4f} | {cre_classification}")
            if msc_fired:
                lines.append(f"[MSC] σ={msc_sigma:.4f} | ISI_MSC={msc_isi:.4f}")
            if decm_fired:
                lines.append(f"[DECM] {decm_verdict}: evasion detected | ISI_DECM={decm_isi:.4f}")
        if exp_notes:
            lines.extend(exp_notes)
        if narrative_limit:
            lines.append(f"[NARRATIVE LIMIT] Domain {detected_domain}: structural detection not applicable without external KB")

        if manipulation_alert:
            alert_message = (
                f"⚠ MANIFOLD RUPTURE DETECTED\n"
                f"ISI_FINAL = {isi_final:.4f} < κD = {effective_kappa} (domain: {detected_domain})\n"
                f"ISI_HARD = {isi_hard:.4f} [TDA={isi_tda:.4f} | NIG={nig_isi:.4f}]\n"
                + ("\n".join(lines) if lines else "")
            )
        else:
            alert_message = (
                f"ISI_FINAL = {isi_final:.4f} ≥ κD = {effective_kappa} (domain: {detected_domain})\n"
                + ("\n".join(lines) if lines else "")
            )

        summary = self._build_summary(
            label_a, label_b, wass_h1, bott_h1, wass_h0,
            isi_tda, nig_isi, isi_hard, isi_final,
            delta, verdict, risk, confidence,
            rep_a, rep_b, manipulation_alert, effective_kappa,
            run_experimental, isi_soft, narrative_limit
        )

        # Build report with all fields (including v10.1)
        return SemanticDiffReport(
            timestamp=ts,
            hash_a=hash_a,
            hash_b=hash_b,
            kappa_d=self.kappa_d,
            wasserstein_h1=round(wass_h1, 6),
            bottleneck_h1=round(bott_h1, 6),
            wasserstein_h0=round(wass_h0, 6),
            isi_tda=isi_tda,
            nig_isi=round(nig_isi, 6),
            nig_fired=nig_fired,
            nig_entities_found=nig_entities_found,
            nig_violations=nig_violations,
            nig_violation_details=nig_violation_details,
            isi_hard=isi_hard,
            flow_isi=round(flow_isi, 6),
            flow_fired=flow_fired,
            flow_spikes=flow_spikes,
            cre_isi=round(cre_isi, 6),
            cre_fired=cre_fired,
            cre_classification=cre_classification,
            cre_ricci_singularities=cre_ricci_singularities,
            cre_n_nodes=cre_n_nodes,
            msc_isi=round(msc_isi, 6),
            msc_sigma=round(msc_sigma, 6),
            msc_fired=msc_fired,
            msc_valid_count=msc_valid_count,
            decm_isi=round(decm_isi, 6),
            decm_fired=decm_fired,
            decm_verdict=decm_verdict,
            # v10.1 fields
            experimental_enabled=self.experimental,
            negation_inversions=exp_negation_result.inversion_count if exp_negation_result else 0,
            negation_penalty=exp_negation_result.penalty if exp_negation_result else 1.0,
            reference_fabrications=exp_reference_result.fabricated_count if exp_reference_result else 0,
            reference_penalty=exp_reference_result.penalty if exp_reference_result else 1.0,
            arithmetic_errors=exp_arith_result.error_count if exp_arith_result else 0,
            arithmetic_penalty=exp_arith_result.penalty if exp_arith_result else 1.0,
            entropy_artificial=exp_entropy_result.is_artificial if exp_entropy_result else False,
            entropy_penalty=exp_entropy_result.penalty if exp_entropy_result else 1.0,
            experimental_notes=exp_notes,
            # end v10.1
            isi_soft=round(isi_soft, 6),
            experimental_active=run_experimental,
            invariant_similarity_index=isi_final,
            manipulation_alert=manipulation_alert,
            alert_message=alert_message,
            verdict=verdict,
            risk_level=risk,
            confidence=round(confidence, 4),
            detected_domain=detected_domain,
            effective_kappa=round(effective_kappa, 4),
            lexical_overlap=round(lex_overlap, 4),
            hch_warning=hch_flag,
            narrative_limit=narrative_limit,
            delta=delta,
            report_a=rep_a.to_dict(),
            report_b=rep_b.to_dict(),
            scipy_available=_SCIPY_OK,
            summary=summary,
        )

    def _compute_delta(self, rep_a, rep_b) -> ManifoldDelta:
        return ManifoldDelta(
            delta_manifold_score=round(rep_b.integrity_score - rep_a.integrity_score, 6),
            delta_coherence=round((rep_b.mean_h1_persistence or 0.0) - (rep_a.mean_h1_persistence or 0.0), 6),
            delta_h1_total=rep_b.h1_total - rep_a.h1_total,
            delta_structural_faults=rep_b.h1_structural_falsehoods - rep_a.h1_structural_falsehoods,
            delta_integrity=round(rep_b.integrity_score - rep_a.integrity_score, 6),
            delta_topological_noise=round(rep_b.topological_noise - rep_a.topological_noise, 6),
        )

    def _assign_verdict(self, wass, bott, isi, delta, rep_a, rep_b, kappa) -> Tuple[str, str, float]:
        new_faults = max(0, delta.delta_structural_faults)
        confidence = min(1.0, min(rep_a.point_cloud_size, rep_b.point_cloud_size) / 50) * 0.6 + \
                     min(1.0, min(rep_a.sentence_count, rep_b.sentence_count) / 20) * 0.4
        if isi < kappa or wass > kappa or (new_faults >= 2 and bott > kappa * 0.5):
           return "MANIFOLD_RUPTURE", "CRITICAL", round(confidence, 4)
        if wass < 1e-4 and bott < 1e-4:
           return "IDENTICAL", "LOW", round(confidence, 4)
        if wass > kappa * 0.1 or bott > kappa * 0.2 or new_faults >= 1:
           return "STRUCTURAL_CHANGE", "HIGH", round(confidence, 4)
        return "MINOR_DRIFT", "MEDIUM", round(confidence, 4)
       
    def _build_summary(
        self, label_a, label_b, wass, bott, wass_h0,
        isi_tda, nig_isi, isi_hard, isi_final,
        delta, verdict, risk, confidence,
        rep_a, rep_b, alert, kappa,
        experimental_active, isi_soft, narrative_limit
    ) -> str:
        sep = "─" * 60
        verdict_labels = {
            "IDENTICAL": "TOPOLOGICALLY IDENTICAL",
            "MINOR_DRIFT": "MINOR DRIFT — within threshold",
            "STRUCTURAL_CHANGE": "STRUCTURAL CHANGE DETECTED",
            "MANIFOLD_RUPTURE": "⚠ MANIFOLD RUPTURE — STRUCTURAL MANIPULATION",
            "HCH_COPY": "HCH COPY — literal overlap",
        }
        lines = [
            "OMNI-SCANNER v5.3 — CONSOLIDATED PIPELINE (TDA + NIG)",
            sep,
            f"Doc A : {label_a} [{rep_a.text_hash}]",
            f"Doc B : {label_b} [{rep_b.text_hash}]",
            sep,
            "CORE (production)",
            f"  ISI_TDA  = {isi_tda:.6f}  [Wasserstein H₁={wass:.4f} | Bottleneck={bott:.4f}]",
            f"  ISI_NIG  = {nig_isi:.6f}",
            f"  ISI_HARD = {isi_hard:.6f}  [min(TDA, NIG)]",
        ]
        if experimental_active:
            lines += [
                sep,
                "EXPERIMENTAL (Escalation Protocol active)",
                f"  ISI_SOFT  = {isi_soft:.6f}  [mean(Flow, CRE, MSC, DECM, Negation, Reference, Arithmetic, Entropy)]",
                f"  ISI_FINAL = {isi_final:.6f}  [0.65×HARD + 0.35×SOFT]",
            ]
        else:
            lines.append(f"  ISI_FINAL = {isi_final:.6f}  [= ISI_HARD]")
            if narrative_limit:
                lines.append(f"  ⚠ NARRATIVE LIMIT — domain without structural detection possible")
        lines += [
            sep,
            f"  κD effective = {kappa}",
            f"  {'⚠ ISI_FINAL < κD — RUPTURE DETECTED' if alert else '✓ ISI_FINAL ≥ κD — COHERENT'}",
            sep,
            f"VERDICT  : {verdict_labels.get(verdict, verdict)}",
            f"RISK     : {risk}",
            f"CONFIDENCE: {confidence:.1%}",
            sep,
            "TDA DELTAS",
            f"  Δ Integrity     : {delta.delta_integrity:+.4f}",
            f"  Δ H₁ cycles     : {delta.delta_h1_total:+d}",
            f"  Δ Struct. faults: {delta.delta_structural_faults:+d}",
        ]
        return "\n".join(lines)

    def _build_report(self, *args, **kwargs) -> SemanticDiffReport:
        return SemanticDiffReport(
            timestamp=kwargs.get("ts", ""),
            hash_a=kwargs.get("hash_a", ""),
            hash_b=kwargs.get("hash_b", ""),
            kappa_d=self.kappa_d,
            wasserstein_h1=0.0,
            bottleneck_h1=0.0,
            wasserstein_h0=0.0,
            isi_tda=1.0,
            nig_isi=1.0,
            nig_fired=False,
            nig_entities_found=0,
            nig_violations=0,
        )

    def compare_series(self, texts: List[str], labels: Optional[List[str]] = None) -> List[SemanticDiffReport]:
        if labels is None:
            labels = [f"v{i+1}" for i in range(len(texts))]
        return [
            self.compare_manifolds(texts[i], texts[i+1], label_a=labels[i], label_b=labels[i+1])
            for i in range(len(texts) - 1)
        ]

    def score_series(self, texts: List[str], labels: Optional[List[str]] = None) -> dict:
        diffs = self.compare_series(texts, labels)
        if labels is None:
            labels = [f"v{i+1}" for i in range(len(texts))]
        steps = [
            {
                "pair": f"{labels[i]} → {labels[i+1]}",
                "isi_hard": d.isi_hard,
                "isi_final": d.invariant_similarity_index,
                "verdict": d.verdict,
                "alert": d.manipulation_alert,
                "experimental_active": d.experimental_active,
            }
            for i, d in enumerate(diffs)
        ]
        total = self.compare_manifolds(texts[0], texts[-1], label_a=labels[0], label_b=labels[-1]) if len(texts) >= 2 else None
        return {
            "steps": steps,
            "total_isi_hard": total.isi_hard if total else 1.0,
            "total_isi_final": total.invariant_similarity_index if total else 1.0,
            "total_verdict": total.verdict if total else "N/A",
            "total_alert": total.manipulation_alert if total else False,
            "kappa_d": self.kappa_d,
        }


def quick_diff(
    text_a: str,
    text_b: str,
    kappa_d: float = 0.56,
    label_a: str = "Doc A",
    label_b: str = "Doc B",
    domain: str | None = None,
    adaptive_kappa: bool = True,
    experimental: bool = False,
    msc_backend=None,
) -> SemanticDiffReport:
    diff = SemanticDiff(
        kappa_d=kappa_d,
        domain=domain,
        adaptive_kappa=adaptive_kappa,
        experimental=experimental,
        msc_backend=msc_backend,
    )
    return diff.compare_manifolds(text_a, text_b, label_a=label_a, label_b=label_b)


def _cli():
    import argparse
    from pathlib import Path
    parser = argparse.ArgumentParser(prog="omni-scanner", description="Omni-Scanner v5.3")
    parser.add_argument("--file-a", required=True)
    parser.add_argument("--file-b", required=True)
    parser.add_argument("--kappa", type=float, default=0.56)
    parser.add_argument("--label-a", default="Document A")
    parser.add_argument("--label-b", default="Document B")
    parser.add_argument("--domain", default=None)
    parser.add_argument("--experimental", action="store_true",
                        help="Activate experimental modules (Flow, CRE, MSC, DECM, Code-AST, Negation, Reference, Arithmetic, Entropy)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    text_a = Path(args.file_a).read_text(encoding="utf-8", errors="replace")
    text_b = Path(args.file_b).read_text(encoding="utf-8", errors="replace")
    diff = SemanticDiff(
        kappa_d=args.kappa,
        domain=args.domain,
        experimental=args.experimental,
    )
    report = diff.compare_manifolds(text_a, text_b, args.label_a, args.label_b)
    if args.json:
        print(report.to_json())
    else:
        print(report.summary)
        if report.manipulation_alert:
            print()
            print(report.alert_message)


if __name__ == "__main__":
    _cli()
