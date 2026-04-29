"""
multifractal_processor.py — Omni-Scanner Semantic v1.0
--------------------------------------------------------
CHANGELOG vs original version:
  + estimate_hausdorff_dimension(text_vector) preservada con firma original
  + analyze_rugosity(hausdorff_dim) preservada con firma original
  + FIX: bins=int(len/s) could generate 0 bins → now bins=max(2, int(...))
  + FIX: np.histogram con bins=0 lanzaba ValueError — corregido
  + NEW: _higuchi_fd() — Higuchi method (more robust than box-counting for short series)
  + NUEVO: analyze(text) — pipeline completo texto → FractalReport
  + NEW: theoretical expected_entropy to pass to EntropyAnalyzer
"""
from __future__ import annotations
import math
import re
from dataclasses import dataclass
from typing import Optional
import numpy as np


@dataclass
class FractalReport:
    higuchi_dim: float
    hausdorff_dim: float            # box-counting original
    expected_entropy: float
    series_length: int
    kmax: int
    stability_delta: float
    flag: str                       # "STABLE" | "UNSTABLE" | "INSUFFICIENT"
    rugosity: dict                  # resultado de analyze_rugosity (API original)
    details: dict


class MultifractalProcessor:
    """
    Parameters
    ----------
    reference_fractal_dim : float   Ideal reference dimension (original API, default 1.58).
    kmax : int                      Maximum k parameter for Higuchi.
    stability_threshold : float     Umbral de equilibrio (default 0.56).
    stability_tolerance : float     Tolerancia para flag STABLE.
    min_series_len : int            Minimum series length.
    """

    def __init__(
        self,
        reference_fractal_dim: float = 1.58,
        kmax: int = 10,
        stability_threshold: float = 0.56,
        stability_tolerance: float = 0.15,   # wider tolerance (was 0.05)
        min_series_len: int = 20,             # bajado de 100 a 20
    ):
        self.reference_fractal_dim = reference_fractal_dim
        self.kmax = kmax
        self.stability_threshold = stability_threshold
        self.stability_tolerance = stability_tolerance
        self.min_series_len = min_series_len

    # ------------------------------------------------------------------
    # API ORIGINAL (preservada para compatibilidad)
    # ------------------------------------------------------------------

    def estimate_hausdorff_dimension(self, text_vector: np.ndarray) -> float:
        """
        Box-counting simplificado. API original preservada.
        FIX: minimum 2 bins to avoid ValueError from np.histogram.
        """
        arr = np.asarray(text_vector, dtype=float)
        if len(arr) < 2:
            return 0.0

        scales = np.logspace(0.1, 1, num=10)
        counts = []
        for s in scales:
            n_bins = max(2, int(len(arr) / s))          # FIX: minimum 2 bins
            bins = np.histogram(arr, bins=n_bins)[0]
            counts.append(np.count_nonzero(bins))

        # Evitar log(0)
        valid = [(math.log(1 / s), math.log(max(c, 1))) for s, c in zip(scales, counts)]
        if len(valid) < 2:
            return 0.0

        xs = np.array([v[0] for v in valid])
        ys = np.array([v[1] for v in valid])
        coeffs = np.polyfit(xs, ys, 1)
        return round(abs(float(coeffs[0])), 4)

    def analyze_rugosity(self, hausdorff_dim: float) -> dict:
        """
        Determina si el texto es 'liso' o 'rugoso'. API original preservada.
        """
        deviation = abs(hausdorff_dim - self.reference_fractal_dim)
        status = "NATURAL" if deviation < 0.2 else "ARTIFICIAL/FRAGMENTADO"
        return {
            "dimension": hausdorff_dim,
            "deviation": round(deviation, 4),
            "topology_status": status,
        }

    # ------------------------------------------------------------------
    # API EXTENDIDA — pipeline completo sobre texto crudo
    # ------------------------------------------------------------------

    def analyze(self, text: str) -> FractalReport:
        """Pipeline completo: texto → FractalReport."""
        series = self._text_to_series(text)
        n = len(series)

        if n < self.min_series_len:
            return FractalReport(
                higuchi_dim=float("nan"),
                hausdorff_dim=float("nan"),
                expected_entropy=float("nan"),
                series_length=n,
                kmax=self.kmax,
                stability_delta=float("nan"),
                flag="INSUFFICIENT",
                rugosity={"topology_status": "INSUFFICIENT"},
                details={"reason": f"Serie demasiado corta ({n} < {self.min_series_len})"},
            )

        arr = np.array(series, dtype=float)
        higuchi = self._higuchi_fd(arr)
        hausdorff = self.estimate_hausdorff_dimension(arr)
        rugosity = self.analyze_rugosity(hausdorff)

        vocab = len(set(self._tokenize(text)))
        n_tokens = len(self._tokenize(text))
        # Expected entropy per Zipf + correction for lexical density (TTR).
        # Legal/technical text has high TTR → H_expected structurally higher.
        # Un factor fijo subestima H_expected → gap inflado → FLAG:NOISE falso.
        ttr = vocab / max(n_tokens, 1)
        if n_tokens < 50:
            base_factor = 0.82
        elif n_tokens < 200:
            base_factor = 0.74
        else:
            base_factor = 0.65
        # TTR correction: up to +0.15 for very technical text (TTR > 0.6)
        ttr_correction = min(0.15, max(0.0, (ttr - 0.30) * 0.43))
        zipf_factor = base_factor + ttr_correction
        expected_h = math.log2(max(vocab, 2)) * zipf_factor
        # stability_delta: distancia a la dimensión fractal de referencia (1.58)
        # normalizada al rango [0,1]. Antes usaba K_D como referencia lo cual
        # producía deltas >1.0 porque Higuchi vive en [1.0, 2.0], no en [0, 0.56].
        delta = abs(higuchi - self.reference_fractal_dim) / self.reference_fractal_dim
        flag = "STABLE" if delta <= self.stability_tolerance else "UNSTABLE"

        return FractalReport(
            higuchi_dim=round(higuchi, 6),
            hausdorff_dim=hausdorff,
            expected_entropy=round(expected_h, 6),
            series_length=n,
            kmax=self.kmax,
            stability_delta=round(delta, 6),
            flag=flag,
            rugosity=rugosity,
            details={
                "stability_threshold": self.stability_threshold,
                "reference_fractal_dim": self.reference_fractal_dim,
                "vocab_size": vocab,
            },
        )

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    def _tokenize(self, text: str) -> list[str]:
        return re.findall(r"\b\w+\b", text.lower())

    def _text_to_series(self, text: str) -> list[float]:
        tokens = self._tokenize(text)
        if not tokens:
            return []
        max_len = max(len(t) for t in tokens)
        return [len(t) / max_len for t in tokens]

    def _higuchi_fd(self, x: np.ndarray) -> float:
        """Higuchi algorithm — more robust than box-counting for short series."""
        N = len(x)
        L = []
        for k in range(1, self.kmax + 1):
            Lk = []
            for m in range(1, k + 1):
                indices = np.arange(m - 1, N, k)
                x_m = x[indices]
                n_m = len(x_m) - 1
                if n_m < 1:
                    continue
                norm = (N - 1) / (n_m * k)
                lm = norm * np.sum(np.abs(np.diff(x_m))) / k
                Lk.append(lm)
            if Lk:
                L.append((math.log(k), math.log(max(float(np.mean(Lk)), 1e-12))))

        if len(L) < 2:
            return 1.0
        xs = np.array([p[0] for p in L])
        ys = np.array([p[1] for p in L])
        coeffs = np.polyfit(xs, ys, 1)
        return abs(float(coeffs[0]))
