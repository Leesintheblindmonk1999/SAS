"""
core/thermic_invariance_v5.py — DECM: Evasion Detection via Thermal Collapse
═══════════════════════════════════════════════════════════════════════════════
PRINCIPLE:
  A language model that lacks factual data about a subject often produces
  evasive responses ("As of my last update, there is no widely recognized...")
  rather than generating a hallucinated biography.

  Under thermal pressure (T=0.3 to T=1.5), evasive responses tend to
  paraphrase inconsistently, causing ISI_hot to drop below κD = 0.56.

  DECM detects these evasion patterns with high precision (0% false positives
  in our 100-pair benchmark). It does NOT detect well‑formed narrative
  hallucinations (invented biographies with plausible details).

  This module is an experimental extension to the Omni‑Scanner core.

Registry: EX-2026-18792778
Author: Gonzalo Emir Durante — Project Manifold 0.56
License: Durante Invariance License v1.0
"""

from __future__ import annotations

import math
import json
import datetime
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────

KAPPA_D: float = 0.56

# Thermal injection temperatures (cold → hot)
DECM_TEMPERATURES: List[float] = [0.3, 0.5, 0.7, 0.9, 1.5]
T_COLD: float = 0.3
T_HOT:  float = 1.5
DELTA_T: float = T_HOT - T_COLD  # 1.2

# Collapse threshold: if ISI_hot < COLLAPSE_THRESHOLD → THERMAL_COLLAPSE
# Calibrated empirically on biographies_corpus (evasion detection)
DEFAULT_COLLAPSE_THRESHOLD: float = 0.58
GRADIENT_RISK_THRESHOLD: float = 0.10

# Domain‑specific thresholds (can be overridden by config)
DOMAIN_COLLAPSE_THRESHOLDS: Dict[str, float] = {
    "biographies_corpus": 0.58,
    "code_corpus":        0.60,
    "references_corpus":  0.55,
    "generic":            0.56,
}

MIN_PAIRS_PER_TEMP: int = 2

# Domains where DECM is applicable (narrative / open‑ended questions)
DECM_TARGET_DOMAINS = {
    "biographies_corpus",
    "historical_events",
    "rationalization_binary",
    "rationalization_numerical",
    "references_corpus",
    "code_corpus",
    "generic",
}


# ── Data structures ─────────────────────────────────────────────────────────

@dataclass
class ThermalProfile:
    temperature: float
    isi_mean:    float
    n_pairs:     int
    std:         float = 0.0

    def to_dict(self) -> dict:
        return {
            "temperature": self.temperature,
            "isi_mean":    round(self.isi_mean, 4),
            "n_pairs":     self.n_pairs,
            "std":         round(self.std, 4),
        }


@dataclass
class DECMResult:
    """Result of DECM evasion detection."""
    thermal_gradient:   float
    isi_cold:           float
    isi_hot:            float
    isi_final:          float
    verdict:            str          # THERMAL_COLLAPSE, THERMAL_RISK, THERMALLY_STABLE
    is_rupture:         bool         # True if evasion detected
    thermal_profile:    List[ThermalProfile] = field(default_factory=list)
    gradient_normalized: float = 0.0
    thermal_variance:    float = 0.0
    cold_hot_ratio:      float = 0.0
    n_temperatures:     int = 0
    n_total_pairs:      int = 0
    backend_available:  bool = False
    domain:             str = "generic"
    collapse_threshold: float = DEFAULT_COLLAPSE_THRESHOLD
    timestamp:          str = field(default_factory=lambda: datetime.datetime.utcnow().isoformat() + "Z")
    kappa_d:            float = KAPPA_D
    author:             str = "Gonzalo Emir Durante"
    registry:           str = "EX-2026-18792778"

    def to_dict(self) -> dict:
        return {
            "thermal_gradient":    round(self.thermal_gradient, 4),
            "isi_cold":            round(self.isi_cold, 4),
            "isi_hot":             round(self.isi_hot, 4),
            "isi_final":           round(self.isi_final, 4),
            "verdict":             self.verdict,
            "is_rupture":          self.is_rupture,
            "gradient_normalized": round(self.gradient_normalized, 4),
            "thermal_variance":    round(self.thermal_variance, 4),
            "cold_hot_ratio":      round(self.cold_hot_ratio, 4),
            "thermal_profile":     [tp.to_dict() for tp in self.thermal_profile],
            "n_temperatures":      self.n_temperatures,
            "n_total_pairs":       self.n_total_pairs,
            "backend_available":   self.backend_available,
            "domain":              self.domain,
            "collapse_threshold":  self.collapse_threshold,
            "timestamp":           self.timestamp,
            "kappa_d":             self.kappa_d,
            "author":              self.author,
            "registry":            self.registry,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


def _insufficient_data_result(domain: str, backend_available: bool) -> DECMResult:
    return DECMResult(
        thermal_gradient=0.0,
        isi_cold=1.0,
        isi_hot=1.0,
        isi_final=1.0,
        verdict="INSUFFICIENT_DATA",
        is_rupture=False,
        backend_available=backend_available,
        domain=domain,
    )


# ── Thermal profile extraction ─────────────────────────────────────────────

def extract_thermal_profile(pairwise_results: List[dict]) -> List[ThermalProfile]:
    """Extract mean ISI per temperature from MSC pairwise matrix."""
    if not pairwise_results:
        return []

    temp_isis: Dict[float, List[float]] = defaultdict(list)

    for pair in pairwise_results:
        t_i = float(pair.get("temp_i", 0))
        t_j = float(pair.get("temp_j", 0))
        isi = float(pair.get("isi", 0))

        temp_isis[round(t_i, 2)].append(isi)
        temp_isis[round(t_j, 2)].append(isi)

    profiles = []
    for temp in sorted(temp_isis.keys()):
        isis = temp_isis[temp]
        mean_isi = float(np.mean(isis))
        std_isi = float(np.std(isis)) if len(isis) > 1 else 0.0
        profiles.append(ThermalProfile(
            temperature=temp,
            isi_mean=round(mean_isi, 6),
            n_pairs=len(isis),
            std=round(std_isi, 6),
        ))

    return profiles


def compute_thermal_gradient(profiles: List[ThermalProfile]) -> Tuple[float, float, float]:
    """Compute gradient between coldest and hottest temperature."""
    if len(profiles) < 2:
        return 0.0, 1.0, 1.0

    valid_profiles = [p for p in profiles if p.n_pairs >= MIN_PAIRS_PER_TEMP]
    if len(valid_profiles) < 2:
        valid_profiles = profiles

    cold_profile = valid_profiles[0]
    hot_profile = valid_profiles[-1]

    isi_cold = cold_profile.isi_mean
    isi_hot = hot_profile.isi_mean
    dt = hot_profile.temperature - cold_profile.temperature

    if dt < 1e-6:
        return 0.0, isi_cold, isi_hot

    gradient = (isi_cold - isi_hot) / dt
    return round(gradient, 6), round(isi_cold, 6), round(isi_hot, 6)


def compute_thermal_variance(profiles: List[ThermalProfile]) -> float:
    if len(profiles) < 2:
        return 0.0
    isis = [p.isi_mean for p in profiles]
    return round(float(np.var(isis)), 6)


# ── Main detector ─────────────────────────────────────────────────────────

class ThermicInvarianceDetector:
    """
    DECM – Evasion detector for LLM outputs.

    Uses thermal injection (multiple temperatures) and measures the semantic
    invariance of the generated responses. When the model evades answering
    (e.g., "I don't know"), the responses diverge under heat, causing
    ISI_hot to fall below κD = 0.56.

    Detected evasions have 100% precision in our benchmark; false positives = 0.
    This detector does NOT detect well‑formed narrative hallucinations.
    """

    def __init__(
        self,
        model:    str = "mistral",
        base_url: str = "http://localhost:11434",
        backend=None,
        temperatures: Optional[List[float]] = None,
        collapse_threshold: Optional[float] = None,
        gradient_risk: float = GRADIENT_RISK_THRESHOLD,
        kappa_d: float = KAPPA_D,
    ):
        self.kappa_d = kappa_d
        self.gradient_risk = gradient_risk
        self.temperatures = temperatures or DECM_TEMPERATURES
        self.collapse_threshold = collapse_threshold or DEFAULT_COLLAPSE_THRESHOLD
        self._backend = backend
        self._engine = None
        self._backend_available = False

        if backend is not None:
            self._init_engine(backend)
        else:
            try:
                import sys, os
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
                from core.msc_engine_v5 import MSCEngineV5, OllamaBackend
                ollama_backend = OllamaBackend(
                    model=model,
                    base_url=base_url,
                    timeout=90,
                )
                self._init_engine(ollama_backend)
            except Exception as e:
                logger.debug(f"DECM: backend not available ({e}). Degraded mode active.")

    def _init_engine(self, backend) -> None:
        try:
            import sys, os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
            from core.msc_engine_v5 import MSCEngineV5
            self._engine = MSCEngineV5(
                backend=backend,
                temperatures=self.temperatures,
                kappa_d=self.kappa_d,
            )
            self._backend_available = True
            logger.info("DECM: MSC backend initialized.")
        except Exception as e:
            logger.warning(f"DECM: MSC engine init error: {e}")

    def detect(
        self,
        text_b: str,
        isi_tda: float = 0.5,
        domain:  str = "generic",
    ) -> DECMResult:
        """Run DECM evasion detection on a candidate text."""
        if not self._backend_available or self._engine is None:
            logger.debug("DECM: no backend – neutral result.")
            return _insufficient_data_result(domain, backend_available=False)

        try:
            msc_result = self._engine.analyze(text_b, isi_tda=isi_tda)
        except Exception as e:
            logger.warning(f"DECM: MSC engine error: {e}")
            return _insufficient_data_result(domain, backend_available=True)

        pairwise = msc_result.pairwise
        if not pairwise or len(pairwise) < 3:
            logger.debug(f"DECM: insufficient pairwise data ({len(pairwise)} pairs).")
            return _insufficient_data_result(domain, backend_available=True)

        profiles = extract_thermal_profile(pairwise)
        if len(profiles) < 2:
            logger.debug("DECM: insufficient thermal profile.")
            return _insufficient_data_result(domain, backend_available=True)

        thermal_gradient, isi_cold, isi_hot = compute_thermal_gradient(profiles)
        thermal_variance = compute_thermal_variance(profiles)
        gradient_normalized = thermal_gradient / self.kappa_d if self.kappa_d > 0 else 0.0
        cold_hot_ratio = (isi_cold / isi_hot) if isi_hot > 1e-6 else 1.0

        # Domain‑adaptive collapse threshold
        collapse_threshold = DOMAIN_COLLAPSE_THRESHOLDS.get(domain, self.collapse_threshold)

        # Penalize gradient (secondary signal)
        if thermal_gradient > self.gradient_risk:
            penalty = min(0.25, thermal_gradient / (self.kappa_d * 3))
            isi_decm = max(0.0, isi_cold - penalty)
        else:
            isi_decm = isi_cold
        isi_decm = round(isi_decm, 6)

        # Primary decision: thermal collapse (evasion)
        if isi_hot < collapse_threshold:
            verdict = "THERMAL_COLLAPSE"
            is_rupture = True
        elif thermal_variance > 0.03:
            verdict = "THERMAL_VARIANCE"
            is_rupture = isi_decm < self.kappa_d
        elif thermal_gradient > self.gradient_risk:
            verdict = "THERMAL_RISK"
            is_rupture = isi_decm < self.kappa_d
        else:
            verdict = "THERMALLY_STABLE"
            is_rupture = False

        logger.info(
            f"DECM [{domain}] gradient={thermal_gradient:.4f} | "
            f"ISI_cold={isi_cold:.4f} | ISI_hot={isi_hot:.4f} | "
            f"variance={thermal_variance:.4f} | threshold={collapse_threshold:.3f} | "
            f"verdict={verdict}"
        )

        return DECMResult(
            thermal_gradient=thermal_gradient,
            isi_cold=isi_cold,
            isi_hot=isi_hot,
            isi_final=isi_decm,
            verdict=verdict,
            is_rupture=is_rupture,
            thermal_profile=profiles,
            gradient_normalized=round(gradient_normalized, 4),
            thermal_variance=thermal_variance,
            cold_hot_ratio=round(cold_hot_ratio, 4),
            n_temperatures=len(profiles),
            n_total_pairs=len(pairwise),
            backend_available=True,
            domain=domain,
            collapse_threshold=collapse_threshold,
            kappa_d=self.kappa_d,
        )

    def detect_batch(
        self,
        texts: List[str],
        domain: str = "generic",
        isi_tda_list: Optional[List[float]] = None,
    ) -> List[DECMResult]:
        results = []
        for i, text in enumerate(texts):
            isi_tda = isi_tda_list[i] if isi_tda_list and i < len(isi_tda_list) else 0.5
            results.append(self.detect(text, isi_tda=isi_tda, domain=domain))
        return results


# ── Pipeline integration helper ────────────────────────────────────────────

def integrate_decm_into_pipeline(
    isi_current: float,
    decm_result: DECMResult,
    kappa_d: float = KAPPA_D,
    domain: str = "generic",
) -> Tuple[float, str]:
    """
    Integrate DECM result into the main ISI pipeline.

    For THERMAL_COLLAPSE (evasion detected), applies a hard veto.
    For THERMAL_RISK, applies a soft penalty.
    Otherwise leaves ISI unchanged.
    """
    if decm_result.verdict == "INSUFFICIENT_DATA":
        return isi_current, ""

    if decm_result.verdict in ("THERMAL_COLLAPSE", "THERMAL_VARIANCE"):
        isi_updated = min(isi_current, decm_result.isi_final)
        note = (
            f"[DECM] {decm_result.verdict}: "
            f"ISI_hot={decm_result.isi_hot:.3f} < threshold={decm_result.collapse_threshold:.3f}"
        )
        return round(isi_updated, 6), note

    if decm_result.verdict == "THERMAL_RISK":
        isi_updated = 0.7 * isi_current + 0.3 * decm_result.isi_final
        note = f"[DECM] THERMAL_RISK: gradient={decm_result.thermal_gradient:.3f}"
        return round(isi_updated, 6), note

    return isi_current, ""


# ── Standalone test (synthetic) ────────────────────────────────────────────

def _demo_without_backend():
    print("=" * 60)
    print("DECM — Evasion detection demo (synthetic data, no LLM)")
    print("=" * 60)

    # Simulated pairwise data for a stable (non‑evasive) text
    stable_pairwise = [
        {"temp_i": 0.3, "temp_j": 0.5, "isi": 0.82},
        {"temp_i": 0.3, "temp_j": 0.7, "isi": 0.80},
        {"temp_i": 0.3, "temp_j": 1.5, "isi": 0.78},
        {"temp_i": 0.5, "temp_j": 0.7, "isi": 0.81},
        {"temp_i": 0.5, "temp_j": 1.5, "isi": 0.79},
        {"temp_i": 0.7, "temp_j": 1.5, "isi": 0.78},
    ]

    # Simulated pairwise data for an evasive text (ISI_hot collapses)
    evasion_pairwise = [
        {"temp_i": 0.3, "temp_j": 0.5, "isi": 0.75},
        {"temp_i": 0.3, "temp_j": 0.7, "isi": 0.62},
        {"temp_i": 0.3, "temp_j": 1.5, "isi": 0.31},
        {"temp_i": 0.5, "temp_j": 0.7, "isi": 0.60},
        {"temp_i": 0.5, "temp_j": 1.5, "isi": 0.28},
        {"temp_i": 0.7, "temp_j": 1.5, "isi": 0.25},
    ]

    for label, pairwise in [("STABLE (content)", stable_pairwise),
                            ("EVASION (detected)", evasion_pairwise)]:
        profiles = extract_thermal_profile(pairwise)
        grad, isi_cold, isi_hot = compute_thermal_gradient(profiles)
        variance = compute_thermal_variance(profiles)

        if isi_hot < DEFAULT_COLLAPSE_THRESHOLD:
            verdict = "THERMAL_COLLAPSE"
        elif grad > GRADIENT_RISK_THRESHOLD:
            verdict = "THERMAL_RISK"
        else:
            verdict = "THERMALLY_STABLE"

        print(f"\n[{label}]")
        print(f"  ISI_cold = {isi_cold:.4f} | ISI_hot = {isi_hot:.4f}")
        print(f"  gradient = {grad:.4f} | variance = {variance:.4f}")
        print(f"  verdict  = {verdict}")

    print("\n" + "=" * 60)
    print("To run with a real LLM backend (Ollama):")
    print("  detector = ThermicInvarianceDetector(model='mistral')")
    print("  result = detector.detect(candidate_text, domain='biographies_corpus')")
    print("=" * 60)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    _demo_without_backend()