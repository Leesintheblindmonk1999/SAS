"""
core/threshold_calibrator.py — Omni-Scanner Semantic v2.0
═══════════════════════════════════════════════════════════
Threshold Calibration Engine — κD Threshold Sovereignty

Allows the auditor to adjust κD in real time without re-scanning
the full text. Only recalculates H₁ cycle classification and the
final verdict — embeddings and persistent homology are already
computed and cached.

Mechanics:
  1. The main scan runs once and caches the complete ManifoldResult
     and TDAAttestationReport.
  2. The κD slider calls recalibrate(new_kd) → instant result.
  3. The UI updates the Durante Thermometer in <100ms.

Golden zone [0.40, 0.80]:
  · κD < 0.40: probabilistic noise zone (too permissive)
  · κD = 0.56: Durante Equilibrium Point
  · κD > 0.80: over-restriction zone (rejects coherent texts)
"""
from __future__ import annotations

import os
import sys
import math
from dataclasses import dataclass
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.manifold_engine import ManifoldEngine, ManifoldResult
from core.tda_attestation import TDAAttestator, TDAAttestationReport


# ══════════════════════════════════════════════════════════════
# Calibration result
# ══════════════════════════════════════════════════════════════

@dataclass
class CalibrationResult:
    """Resultado de aplicar un nuevo κD al texto ya analizado."""
    kappa_d:                  float
    manifold_score:           float
    manifold_verdict:         str
    topology_verdict:         str
    h1_structural_falsehoods: int
    h1_stabilized:            int
    h1_total:                 int
    integrity_score:          float
    structural_risk:          str
    isi_self:                 float   # ISI del doc consigo mismo bajo nuevo κD
    zone:                     str     # "RUIDO" | "OPTIMA" | "SOBRERESTRICCION"
    zone_warning:             str
    overall_verdict:          str     # CLEAR | REVIEW | HIGH_RISK

    @property
    def passes_kd(self) -> bool:
        return self.manifold_score >= self.kappa_d

    @property
    def is_golden_zone(self) -> bool:
        return 0.40 <= self.kappa_d <= 0.80


# ══════════════════════════════════════════════════════════════
# Calibration engine
# ══════════════════════════════════════════════════════════════

class ThresholdCalibrator:
    """
    κD Threshold Calibration Engine.

    Flujo de uso:
      1. calibrator.load_text(raw_text)   → runs full analysis
      2. calibrator.recalibrate(0.60)     → recalculates classification only
      3. Repeat (2) for each slider position

    El costo computacional de (2) es ~10ms vs ~2s de (1).
    """

    KAPPA_DURANTE = 0.56   # Punto de Equilibrio original
    SLIDER_MIN    = 0.20
    SLIDER_MAX    = 0.95
    SLIDER_STEP   = 0.01

    # Optimal zone defined by empirical calibration
    GOLDEN_MIN = 0.40
    GOLDEN_MAX = 0.80

    def __init__(self, embedding_dim: int = 20):
        self._engine     = ManifoldEngine(K_DURANTE=self.KAPPA_DURANTE)
        self._attestator = TDAAttestator(
            persistence_threshold=self.KAPPA_DURANTE,
            embedding_dim=embedding_dim,
        )
        self._manifold_result:  Optional[ManifoldResult]        = None
        self._tda_report:       Optional[TDAAttestationReport]  = None
        self._raw_text:         str = ""
        self._loaded:           bool = False

    # ── Carga inicial ─────────────────────────────────────────

    def load_text(self, raw_text: str) -> CalibrationResult:
        """
        Runs the complete analysis and caches results.
        Llamar una vez antes de usar recalibrate().
        """
        self._raw_text = raw_text
        self._manifold_result = self._engine.analyze(raw_text)
        self._tda_report      = self._attestator.attest(raw_text)
        self._loaded          = True
        return self.recalibrate(self.KAPPA_DURANTE)

    # ── Instant recalibration ─────────────────────────────────

    def recalibrate(self, new_kd: float) -> CalibrationResult:
        """
        Recalculates verdict applying a new κD to the already-cached analysis.
        Fast operation (<50ms) — does not re-run embeddings or homology.

        Parámetros
        ----------
        new_kd : float
            Nuevo umbral κD ∈ [SLIDER_MIN, SLIDER_MAX].
        """
        if not self._loaded:
            raise RuntimeError("Llamar load_text() antes de recalibrate()")

        kd = max(self.SLIDER_MIN, min(self.SLIDER_MAX, new_kd))

        # ── Re-clasificar ciclos H₁ con nuevo κD ──────────────
        h1_sf = 0
        h1_st = 0

        if self._tda_report:
            for pair in self._tda_report.h1_pairs:
                if pair.flag == "NOISE":
                    continue
                if math.isinf(pair.ratio) or pair.ratio > kd:
                    h1_sf += 1
                else:
                    h1_st += 1

            h1_total = self._tda_report.h1_total
        else:
            h1_total = 0

        # ── Re-calcular integridad TDA con nuevo κD ────────────
        if h1_total > 0:
            sf_ratio  = h1_sf / h1_total
            noise     = self._tda_report.topological_noise if self._tda_report else 0.0
            integrity = max(0.0, 1.0 - sf_ratio * 0.8 - noise * 0.2)
        else:
            integrity = 1.0
            sf_ratio  = 0.0

        # ── TDA Verdict ────────────────────────────────────────
        if h1_total == 0:
            tda_v = "TOPOLOGICALLY_SIMPLE"
            strisk = "LOW"
        elif h1_sf == 0:
            tda_v = "MANIFOLD_STABLE"
            strisk = "LOW"
        elif sf_ratio <= 0.25:
            tda_v = "PARTIAL_INSTABILITY"
            strisk = "MEDIUM"
        elif sf_ratio <= 0.60:
            tda_v = "STRUCTURAL_TENSION"
            strisk = "HIGH"
        else:
            tda_v = "SEMANTIC_COLLAPSE"
            strisk = "CRITICAL"

        # ── Global verdict with new κD ─────────────────────────
        ms = self._manifold_result.manifold_score if self._manifold_result else 0.5
        manifold_verdict = "EQUILIBRIUM" if ms >= kd else (
            "TENSION" if ms >= kd * 0.8 else "ANOMALY"
        )

        if ms >= kd and h1_sf == 0:
            overall = "CLEAR"
        elif ms < kd * 0.7 or h1_sf >= 3:
            overall = "HIGH_RISK"
        else:
            overall = "REVIEW"

        # ── ISI self: similitud del doc consigo mismo bajo κD ──
        # If κD is very high, more cycles classified as FALSEHOOD → ISI drops
        isi_self = max(0.0, min(1.0, 1.0 - (h1_sf / max(h1_total, 1)) * (kd / self.KAPPA_DURANTE)))

        # ── Zona del slider ────────────────────────────────────
        zone, warning = self._classify_zone(kd)

        return CalibrationResult(
            kappa_d                  = round(kd, 4),
            manifold_score           = round(ms, 6),
            manifold_verdict         = manifold_verdict,
            topology_verdict         = tda_v,
            h1_structural_falsehoods = h1_sf,
            h1_stabilized            = h1_st,
            h1_total                 = h1_total,
            integrity_score          = round(integrity, 6),
            structural_risk          = strisk,
            isi_self                 = round(isi_self, 6),
            zone                     = zone,
            zone_warning             = warning,
            overall_verdict          = overall,
        )

    def _classify_zone(self, kd: float) -> tuple[str, str]:
        """Clasifica la zona del umbral y genera advertencia si corresponde."""
        if kd < self.GOLDEN_MIN:
            return (
                "RUIDO",
                f"⚠ κD={kd:.2f} is in probabilistic noise zone "
                f"(< {self.GOLDEN_MIN}). El scanner acepta documentos con alta "
                f"structural entropy. Risk of false negatives."
            )
        elif kd > self.GOLDEN_MAX:
            return (
                "OVER-RESTRICTION",
                f"⚠ κD={kd:.2f} is in over-restriction zone "
                f"(> {self.GOLDEN_MAX}). El scanner rechaza documentos coherentes. "
                f"Riesgo de falsos positivos."
            )
        else:
            delta = abs(kd - self.KAPPA_DURANTE)
            if delta < 0.02:
                return (
                    "ÓPTIMA",
                    f"✓ κD={kd:.2f} — Punto de Equilibrio de Durante "
                    f"(±{delta:.2f} del valor calibrado {self.KAPPA_DURANTE})."
                )
            else:
                return (
                    "ÓPTIMA",
                    f"κD={kd:.2f} dentro de la zona válida "
                    f"[{self.GOLDEN_MIN}, {self.GOLDEN_MAX}]. "
                    f"Δ={delta:+.2f} respecto al Punto de Equilibrio ({self.KAPPA_DURANTE})."
                )

    # ── Barrer el rango completo ──────────────────────────────

    def sweep(self, n_steps: int = 40) -> list[CalibrationResult]:
        """
        Barre el rango completo de κD y retorna la curva de sensibilidad.
        Useful for plotting how verdicts change as a function of threshold.
        """
        if not self._loaded:
            raise RuntimeError("Llamar load_text() antes de sweep()")

        import numpy as np
        kd_values = np.linspace(self.SLIDER_MIN, self.SLIDER_MAX, n_steps)
        return [self.recalibrate(float(kd)) for kd in kd_values]

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def cached_text_preview(self) -> str:
        return self._raw_text[:80] + "..." if len(self._raw_text) > 80 else self._raw_text
