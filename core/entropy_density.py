"""
core/entropy_density.py — Entropy Density Mapping v1.1
═══════════════════════════════════════════════════════════════════════════════
Detects artificial uniformity in generated text via sliding-window entropy.

Target domain: simplification / truthfulqa narratives (recall 0.7% → target >20%)

Methodology:
  1. Tokenise text into words (lowercased, alphabetic only).
  2. Discard texts below MIN_TOKENS (200) — too short for reliable analysis.
  3. Split into overlapping windows (size=100 tokens, step=50).
  4. Compute Shannon word entropy per window.
  5. Compute variance of window entropies.
  6. Apply an ADAPTIVE threshold: variance < mean_entropy * VARIANCE_RATIO
     flags the text as artificially uniform.
     (Fix from v1.0: fixed threshold 0.05 was too low for technical/legal texts
     which have naturally low variance but are not AI-generated.)
  7. Apply a mild penalty (UNIFORMITY_PENALTY) when artificial uniformity
     is detected.

Correction from v1.0:
  - Fixed threshold 0.05 → adaptive threshold (mean_entropy * VARIANCE_RATIO)
  - Added MIN_TOKENS guard (200 tokens) for short texts
  - Removed numpy dependency (replaced with pure Python statistics)
  - Entropy computed on words only (not characters) for stability

Known limitations:
  - Window-based analysis requires sufficient text length.
  - Highly specialised vocabulary (e.g., legal boilerplate) may trigger
    false positives even with the adaptive threshold.
  - The penalty is mild (0.85) because this is a supporting signal,
    not a primary detection mechanism.
  - Does not distinguish between uniform-due-to-style and uniform-due-to-AI.

Registry: EX-2026-18792778
Author: Gonzalo Emir Durante — Project Manifold 0.56
License: Durante Invariance License v1.0
"""

from __future__ import annotations

import re
import math
from dataclasses import dataclass, field
from typing import List, Optional

# ── Constants ──────────────────────────────────────────────────────────────────
KAPPA_D: float = 0.56

UNIFORMITY_PENALTY: float = 0.85   # mild — entropy density is a soft signal
MIN_TOKENS: int = 200               # below this, analysis is unreliable
MIN_WINDOWS: int = 3                # minimum windows for meaningful variance

WINDOW_SIZE: int = 100              # tokens per window
WINDOW_STEP: int = 50               # step between windows (50% overlap)

# Adaptive threshold: flag as artificial if variance < mean_entropy * ratio.
# 0.10 means variance must be at least 10% of mean entropy to be considered
# natural. This is more lenient than a fixed value for low-entropy domains.
VARIANCE_RATIO: float = 0.10


# ── Tokeniser ──────────────────────────────────────────────────────────────────

def _tokenise(text: str) -> List[str]:
    """
    Extract lowercase word tokens from text.
    Only alphabetic characters — strips numbers and punctuation — to ensure
    that purely numeric texts (e.g., financial tables) don't inflate entropy.
    """
    return re.findall(r'\b[a-z]{2,}\b', text.lower())


# ── Shannon entropy ─────────────────────────────────────────────────────────────

def _shannon_entropy(tokens: List[str]) -> float:
    """
    Compute Shannon word entropy in bits over a token list.
    Returns 0.0 for empty inputs.
    """
    if not tokens:
        return 0.0
    freq: dict[str, int] = {}
    for t in tokens:
        freq[t] = freq.get(t, 0) + 1
    total = len(tokens)
    h = 0.0
    for c in freq.values():
        p = c / total
        if p > 0:
            h -= p * math.log2(p)
    return h


# ── Pure-Python statistics (no numpy required) ──────────────────────────────────

def _mean(values: List[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _variance(values: List[float]) -> float:
    """Population variance."""
    if len(values) < 2:
        return 0.0
    mu = _mean(values)
    return sum((v - mu) ** 2 for v in values) / len(values)


# ── Result dataclass ────────────────────────────────────────────────────────────

@dataclass
class EntropyDensityResult:
    """Result of entropy density analysis."""
    window_entropies:  List[float]
    mean_entropy:      float
    variance:          float
    adaptive_threshold: float          # = mean_entropy * VARIANCE_RATIO
    is_artificial:     bool
    penalty:           float
    details:           str = ""

    def to_dict(self) -> dict:
        return {
            "window_count":      len(self.window_entropies),
            "mean_entropy":      round(self.mean_entropy, 4),
            "variance":          round(self.variance, 6),
            "adaptive_threshold": round(self.adaptive_threshold, 6),
            "is_artificial":     self.is_artificial,
            "penalty":           round(self.penalty, 6),
            "details":           self.details,
        }


# ── Main analyser ───────────────────────────────────────────────────────────────

def compute_entropy_density(
    text: str,
    window_size: int = WINDOW_SIZE,
    window_step: int = WINDOW_STEP,
) -> EntropyDensityResult:
    """
    Compute sliding-window Shannon entropy and flag artificial uniformity.

    The adaptive threshold (mean_entropy * VARIANCE_RATIO) adjusts the
    detection sensitivity based on the baseline entropy of the text:
      - High-entropy creative text → higher threshold → harder to flag
      - Low-entropy technical text → lower threshold → proportionally adjusted
    This avoids the fixed-threshold false positives of v1.0.

    Returns an EntropyDensityResult with penalty = 1.0 if no anomaly found.
    """
    tokens = _tokenise(text)

    # ── Short text guard ──────────────────────────────────────
    if len(tokens) < MIN_TOKENS:
        return EntropyDensityResult(
            window_entropies=[],
            mean_entropy=0.0,
            variance=0.0,
            adaptive_threshold=0.0,
            is_artificial=False,
            penalty=1.0,
            details=f"Text too short ({len(tokens)} tokens < {MIN_TOKENS} minimum)",
        )

    # ── Window entropy computation ────────────────────────────
    entropies: List[float] = []
    pos = 0
    while pos + window_size <= len(tokens):
        window = tokens[pos: pos + window_size]
        h = _shannon_entropy(window)
        entropies.append(h)
        pos += window_step

    if len(entropies) < MIN_WINDOWS:
        return EntropyDensityResult(
            window_entropies=[round(h, 4) for h in entropies],
            mean_entropy=_mean(entropies),
            variance=0.0,
            adaptive_threshold=0.0,
            is_artificial=False,
            penalty=1.0,
            details=f"Only {len(entropies)} windows; need at least {MIN_WINDOWS}",
        )

    mean_h   = _mean(entropies)
    variance = _variance(entropies)

    # ── Adaptive threshold ─────────────────────────────────────
    # Minimum floor of 0.01 to avoid division-by-zero on degenerate texts
    adaptive_thr = max(0.01, mean_h * VARIANCE_RATIO)
    is_artificial = variance < adaptive_thr and mean_h > 0.5  # mean > 0.5 to exclude near-empty texts

    if is_artificial:
        penalty = UNIFORMITY_PENALTY
        details = (
            f"Artificial uniformity: variance={variance:.4f} < "
            f"adaptive_threshold={adaptive_thr:.4f} "
            f"(mean_entropy={mean_h:.4f}, ratio={VARIANCE_RATIO})"
        )
    else:
        penalty = 1.0
        details = (
            f"Natural entropy variance: {variance:.4f} ≥ "
            f"adaptive_threshold={adaptive_thr:.4f} "
            f"(mean_entropy={mean_h:.4f})"
        )

    return EntropyDensityResult(
        window_entropies=[round(h, 4) for h in entropies],
        mean_entropy=round(mean_h, 6),
        variance=round(variance, 6),
        adaptive_threshold=round(adaptive_thr, 6),
        is_artificial=is_artificial,
        penalty=round(penalty, 6),
        details=details,
    )


def integrate_entropy_penalty(
    isi_current: float,
    ed_result: EntropyDensityResult,
) -> float:
    """Apply the entropy density penalty to the current ISI value."""
    if ed_result.penalty >= 1.0:
        return isi_current
    return round(max(0.0, isi_current * ed_result.penalty), 6)
