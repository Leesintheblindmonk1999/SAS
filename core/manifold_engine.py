"""
manifold_engine.py — Omni-Scanner Semantic v1.0
-------------------------------------------------
CHANGELOG vs original version:
  + Mantiene K_DURANTE = 0.56 y precision_threshold = 0.15
  + calculate_invariance(semantic_vector) preservada con firma original
  + detect_plagiarism_signature(a, b) preservada con firma original
  + FIX: calculate_invariance now accepts both numeric vector and text
  + NUEVO: analyze(text) — pipeline completo texto → ManifoldResult
  + NEW: combined ManifoldScore (entropy + fractal) instead of norm-only
  + NUEVO: veredictos EQUILIBRIUM / TENSION / ANOMALY con confianza
"""
from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Optional, Union
import numpy as np

from .entropy_analyzer import EntropyAnalyzer, EntropyReport
from .multifractal_processor import MultifractalProcessor, FractalReport


@dataclass
class ManifoldResult:
    manifold_score: float           # [0, 1]: convergencia al equilibrio
    stability_index: float          # original index (saturated norm)
    gap: float                      # |stability_index - K_DURANTE|
    is_stable: bool
    status: str                     # "CONVERGENTE" | "DISTORSIONADO" (API original)
    verdict: str                    # "EQUILIBRIUM" | "TENSION" | "ANOMALY" | "INSUFFICIENT"
    confidence: float
    entropy_report: EntropyReport
    fractal_report: FractalReport
    summary: str

    def to_dict(self) -> dict:
        d = {k: v for k, v in self.__dict__.items()}
        d["entropy_report"] = self.entropy_report.to_dict()
        d["fractal_report"] = self.fractal_report.__dict__
        return d


class ManifoldEngine:
    """
    Parameters
    ----------
    K_DURANTE : float           Stability threshold (hyperparameter, default 0.56).
    precision_threshold : float Tolerance margin for bad-faith detection (default 0.15).
    tension_tolerance : float   Extra tolerance for TENSION vs ANOMALY verdict.
    """

    def __init__(
        self,
        K_DURANTE: float = 0.56,
        precision_threshold: float = 0.15,
        tension_tolerance: float = 0.10,
    ):
        self.K_DURANTE = K_DURANTE
        self.precision_threshold = precision_threshold
        self.tension_tolerance = tension_tolerance
        self._entropy = EntropyAnalyzer(noise_gap_threshold=precision_threshold)
        self._fractal = MultifractalProcessor(stability_threshold=K_DURANTE)

    # ------------------------------------------------------------------
    # API ORIGINAL (preservada para compatibilidad)
    # ------------------------------------------------------------------

    def calculate_invariance(self, semantic_vector: Union[np.ndarray, list, str]) -> dict:
        """
        Calculates the manifold stability index.
        EXTENDED: accepts numeric vector (original API) OR raw text.
        """
        if isinstance(semantic_vector, str):
            # Convierte texto a vector de longitudes de palabras normalizadas
            import re
            tokens = re.findall(r"\b\w+\b", semantic_vector.lower())
            if not tokens:
                semantic_vector = np.array([0.0])
            else:
                max_len = max(len(t) for t in tokens)
                semantic_vector = np.array([len(t) / max_len for t in tokens])
        else:
            semantic_vector = np.asarray(semantic_vector, dtype=float)

        norm_vector = np.linalg.norm(semantic_vector)
        stability_index = norm_vector / (1 + norm_vector)  # original saturation function
        gap = abs(stability_index - self.K_DURANTE)
        is_stable = gap < self.precision_threshold

        return {
            "index": round(float(stability_index), 4),
            "gap": round(float(gap), 4),
            "is_stable": is_stable,
            "status": "CONVERGENTE" if is_stable else "DISTORSIONADO",
        }

    def detect_plagiarism_signature(
        self,
        input_logic: Union[np.ndarray, list],
        prior_art_logic: Union[np.ndarray, list],
    ) -> bool:
        """
        Compares the logical fingerprint of input against Prior Art.
        Returns True if correlation > 0.85 (original API preserved).
        FIX: handles arrays of different sizes by truncating to minimum.
        """
        a = np.asarray(input_logic, dtype=float)
        b = np.asarray(prior_art_logic, dtype=float)
        min_len = min(len(a), len(b))
        if min_len < 2:
            return False
        correlation = np.corrcoef(a[:min_len], b[:min_len])[0, 1]
        return bool(correlation > 0.85)

    # ------------------------------------------------------------------
    # API EXTENDIDA — pipeline completo sobre texto crudo
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Adaptive weights based on data availability
    # ------------------------------------------------------------------

    @staticmethod
    def _adaptive_weights(token_count: int, sentence_count: int) -> tuple[float, float, float]:
        """
        Returns (w_topology, w_entropy, w_fractal) adapted to text size.

        Rationale:
        - Topology requires ≥ 4 sentences for graphs with significant edges.
          Bajo ese umbral, su score colapsa a 0 o a ruido → se reduce su peso.
        - Fractalidad (Higuchi) necesita ≥ 20 puntos de serie para ser confiable.
          Con textos cortos la varianza es enorme → se reduce su peso.
        - Entropy is the most stable: works from ~30 tokens.
          In short texts, it receives more weight as the most robust metric.

        Rangos documentados:
          Texto muy corto  (<50 tokens,  <3 sent):  E=0.60  T=0.15  F=0.25
          Texto corto      (<150 tokens, <6 sent):  E=0.45  T=0.25  F=0.30
          Texto medio      (<400 tokens, <15 sent): E=0.35  T=0.40  F=0.25  ← target
          Texto largo      (≥400 tokens, ≥15 sent): E=0.35  T=0.40  F=0.25
        """
        if token_count < 50 or sentence_count < 3:
            return 0.15, 0.60, 0.25
        if token_count < 150 or sentence_count < 6:
            return 0.25, 0.45, 0.30
        # Medium and long → target weighting
        return 0.40, 0.35, 0.25

    def analyze(self, text: str, topology_coherence: float | None = None) -> ManifoldResult:
        """
        Complete pipeline: text → ManifoldResult with verdict and confidence.

        Parameters
        ----------
        text               : texto crudo a analizar
        topology_coherence : if caller already computed topological coherence
                             (FullDiagnostic la pasa desde TopologyMapper),
                             se usa directamente. Si es None, se omite la
                             topological dimension of the score.
        """
        import re as _re
        f_report = self._fractal.analyze(text)
        expected_h = (
            f_report.expected_entropy
            if not math.isnan(f_report.expected_entropy) else None
        )
        e_report = self._entropy.analyze(text, expected_entropy=expected_h)
        inv = self.calculate_invariance(text)

        # Sentence count for adaptive weights
        sentence_count = max(1, len(_re.split(r"[.!?]+", text.strip())))
        token_count    = e_report.details.get("token_count", 0)

        if e_report.flag == "INSUFFICIENT_DATA" or f_report.flag == "INSUFFICIENT":
            # ── PARTIAL mode: short text but technically dense ──────
            # Condition: between 10 and 50 tokens with high TTR (rich vocabulary)
            token_count_raw = e_report.details.get("token_count", 0)
            import re as _re2
            words = _re2.findall(r"\b\w+\b", text.lower())
            ttr   = len(set(words)) / max(len(words), 1)
            avg_word_len = sum(len(w) for w in words) / max(len(words), 1)

            # Technical density indicators
            is_technically_dense = (
                ttr >= 0.70 and          # vocabulario muy variado
                avg_word_len >= 5.5 and  # long words (technical)
                token_count_raw >= 10    # absolute minimum
            )

            if is_technically_dense and token_count_raw < 100:
                # PARTIAL: only entropy is reliable — weight 60%
                entropy_score_partial = max(0.0, 1.0 - (e_report.gap or 0.5))
                # Fractalidad como referencial — estimada desde TTR
                fractal_est = min(ttr * 0.8, 0.8)
                partial_score = round(0.60 * entropy_score_partial + 0.40 * fractal_est, 6)
                confidence_partial = round(token_count_raw / 100 * 0.6, 4)

                dev = 1.0 - partial_score
                verdict_p = (
                    "EQUILIBRIUM" if dev <= self.tension_tolerance else
                    "TENSION"     if dev <= self.tension_tolerance * 3 else
                    "ANOMALY"
                )
                summary_p = (
                    f"PARTIAL_VALIDATION MODE — Short text with high technical density\n"
                    f"TTR={ttr:.3f} | avg_word_len={avg_word_len:.1f} | tokens={token_count_raw}\n"
                    f"Partial score: {partial_score:.4f} (60% entropy + 40% reference fractal)\n"
                    f"Verdict: {verdict_p} | Reduced confidence: {confidence_partial:.2%}"
                )
                return ManifoldResult(
                    manifold_score=partial_score,
                    stability_index=inv["index"],
                    gap=inv["gap"],
                    is_stable=inv["is_stable"],
                    status="PARTIAL_VALIDATION",
                    verdict=verdict_p,
                    confidence=confidence_partial,
                    entropy_report=e_report,
                    fractal_report=f_report,
                    summary=summary_p,
                )

            return ManifoldResult(
                manifold_score=float("nan"),
                stability_index=inv["index"],
                gap=inv["gap"],
                is_stable=inv["is_stable"],
                status=inv["status"],
                verdict="INSUFFICIENT",
                confidence=0.0,
                entropy_report=e_report,
                fractal_report=f_report,
                summary="Insufficient text for reliable analysis.",
            )

        # ── Scores individuales ────────────────────────────────────────
        fractal_score  = max(0.0, 1.0 - f_report.stability_delta / max(self.K_DURANTE, 1e-6))
        entropy_score  = max(0.0, 1.0 - (e_report.gap or 0.0))

        # Lexical density multiplier
        # High TTR + long words → technical text → slightly boosts score
        import re as _re3
        words_all = _re3.findall(r"\b\w+\b", text.lower())
        ttr_main  = len(set(words_all)) / max(len(words_all), 1)
        avg_wl    = sum(len(w) for w in words_all) / max(len(words_all), 1)
        # Multiplier in [0.90, 1.05]: fine adjustment only, no distortion
        lex_mult  = min(1.05, max(0.90, 0.90 + ttr_main * 0.10 + (avg_wl - 4) * 0.01))

        # Topology: if provided by caller use it; otherwise exclude from computation
        topo_available = topology_coherence is not None and not math.isnan(topology_coherence)
        topo_score     = max(0.0, float(topology_coherence)) if topo_available else None

        # ── Pesos adaptativos ──────────────────────────────────────────
        w_topo, w_entr, w_frac = self._adaptive_weights(token_count, sentence_count)

        if topo_score is None:
            # Redistribute topology weight between entropy and fractal
            total = w_entr + w_frac
            w_entr = w_entr / total
            w_frac = w_frac / total
            w_topo = 0.0
            topo_score = 0.0

        manifold_score = round(
            min(1.0, (w_topo * topo_score + w_entr * entropy_score + w_frac * fractal_score) * lex_mult),
            6,
        )

        # ── Confianza ──────────────────────────────────────────────────
        # Penaliza textos cortos donde los pesos se redistribuyeron
        base_conf   = min(1.0, token_count / 500)
        topo_conf   = 1.0 if topo_available else 0.75
        confidence  = round(base_conf * topo_conf, 4)

        # ── Verdict with σ-bands ───────────────────────────────────────
        # deviation = distancia al equilibrio perfecto (score=1.0)
        deviation = 1.0 - manifold_score
        sigma_band = self.tension_tolerance   # σ base (configurable)

        # If topology has reasonable coherence, do not escalate to ANOMALY.
        # Threshold 0.30 (was 0.40): technical paper with 33 sentences gives ~0.37,
        # que es coherencia real — el grafo tiene estructura, no es ruido.
        topo_coherent = (
            topo_available and
            topo_score is not None and
            topo_score >= 0.30
        )

        if deviation <= sigma_band:
            verdict = "EQUILIBRIUM"
        elif deviation <= sigma_band * 3:
            verdict = "TENSION"
        elif topo_coherent:
            # Low score but coherent logical structure → TENSION, not ANOMALY
            verdict = "TENSION"
        else:
            verdict = "ANOMALY"

        # ── Diagnostic summary ──────────────────────────────────────────
        w_str = (f"Pesos adaptativos: T={w_topo:.2f} E={w_entr:.2f} F={w_frac:.2f} "
                 f"[tokens={token_count}, sents={sentence_count}]")
        summary = (
            f"Verdict: {verdict} | ManifoldScore: {manifold_score:.4f} | "
            f"Confianza: {confidence:.2%}\n"
            f"{w_str}\n"
            f"Scores → Topology: {topo_score:.4f} | "
            f"Entropy: {entropy_score:.4f} | Fractal: {fractal_score:.4f}\n"
            f"Observed entropy: {e_report.word_entropy:.4f} bits"
            f" | Esperada: {e_report.expected_entropy or 'N/A'}\n"
            f"Entropy gap: {e_report.gap or 'N/A'} | FLAG: {e_report.flag}\n"
            f"Higuchi Dimension: {f_report.higuchi_dim:.4f} | "
            f"Δ estabilidad: {f_report.stability_delta:.4f}"
        )

        return ManifoldResult(
            manifold_score=manifold_score,
            stability_index=inv["index"],
            gap=inv["gap"],
            is_stable=inv["is_stable"],
            status=inv["status"],
            verdict=verdict,
            confidence=confidence,
            entropy_report=e_report,
            fractal_report=f_report,
            summary=summary,
        )
