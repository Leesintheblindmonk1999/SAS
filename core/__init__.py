"""
core/__init__.py — Omni-Scanner v5.3 Core Modules
═══════════════════════════════════════════════════════════════════════════════
Exports all core detection engines for Omni-Scanner Semantic v5.3.

Modules:
  · tda_attestation        – Persistent homology (H₀, H₁)
  · nig_engine_v1          – Numerical Invariance Guard (core)
  · flow_coherence         – Entropy spikes (experimental)
  · cre_engine_v1          – Legacy CRE (Ricci Monitor experimental)
  · msc_engine_v5          – Multi‑sample consistency (experimental)
  · thermic_invariance_v5  – DECM evasion detection (experimental)
  · semantic_diff          – Main orchestrator
"""

from .tda_attestation import TDAAttestator, TDAAttestationReport
from .nig_engine_v1 import run_nig, NIGResult
from .semantic_diff import SemanticDiff, SemanticDiffReport, ManifoldDelta, quick_diff, detect_domain, DOMAIN_KAPPA, KAPPA_D

# Experimental modules (optional)
_EXPERIMENTAL_EXPORTS = []

try:
    from .flow_coherence import run_flow_coherence, apply_flow_penalty, FlowCoherenceResult
    _EXPERIMENTAL_EXPORTS += ["run_flow_coherence", "apply_flow_penalty", "FlowCoherenceResult"]
except ImportError:
    pass

try:
    from .ricci_enhanced_cre import run_cre_ricci, RicciEnhancedResult, RicciMonitor
    _EXPERIMENTAL_EXPORTS += ["run_cre_ricci", "RicciEnhancedResult", "RicciMonitor"]
except ImportError:
    pass

try:
    from .msc_engine_v5 import MSCEngineV5, MSCEngineResult, msc_v5_quick, msc_v5_from_texts
    _EXPERIMENTAL_EXPORTS += ["MSCEngineV5", "MSCEngineResult", "msc_v5_quick", "msc_v5_from_texts"]
except ImportError:
    pass

try:
    from .thermic_invariance_v5 import ThermicInvarianceDetector, DECMResult, integrate_decm_into_pipeline
    _EXPERIMENTAL_EXPORTS += ["ThermicInvarianceDetector", "DECMResult", "integrate_decm_into_pipeline"]
except ImportError:
    pass

__all__ = [
    # Core
    "TDAAttestator", "TDAAttestationReport",
    "run_nig", "NIGResult",
    "SemanticDiff", "SemanticDiffReport", "ManifoldDelta", "quick_diff",
    "detect_domain", "DOMAIN_KAPPA", "KAPPA_D",
] + _EXPERIMENTAL_EXPORTS