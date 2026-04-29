"""
entropy_analyzer.py — Omni-Scanner Semantic v1.0
--------------------------------------------------
CHANGELOG vs original version:
  + Mantiene calculate_shannon_entropy() con firma original (compatibilidad)
  + detect_gaslighting_patterns() now uses regex for Spanish (accents, variants)
  + NUEVO: word_entropy(), conditional_entropy()
  + NUEVO: analyze() — pipeline completo texto → EntropyReport con flag NOISE/OK
  + NEW: gap H_observed / H_expected(fractal) as detection criterion
"""
from __future__ import annotations
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class EntropyReport:
    char_entropy: float
    word_entropy: float
    conditional_entropy: float
    expected_entropy: Optional[float]
    ratio: Optional[float]          # H_observed / H_expected
    gap: Optional[float]            # |ratio - 1.0|
    flag: str                       # "OK" | "NOISE" | "INSUFFICIENT_DATA"
    gaslighting: dict               # resultado de detect_gaslighting_patterns
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


class EntropyAnalyzer:
    """
    Parameters
    ----------
    ngram_size : int        Character n-gram size.
    base : float            Logarithmic base (2 = bits).
    noise_gap_threshold : float   Maximum tolerated relative gap.
    smoothing : float       Suavizado de Laplace.
    min_tokens : int        Minimum tokens for reliable analysis.
    """

    def __init__(
        self,
        ngram_size: int = 3,
        base: float = 2.0,
        noise_gap_threshold: float = 0.15,
        smoothing: float = 0.01,
        min_tokens: int = 50,
    ):
        self.ngram_size = ngram_size
        self.base = base
        self.noise_gap_threshold = noise_gap_threshold
        self.smoothing = smoothing
        self.min_tokens = min_tokens

    # ------------------------------------------------------------------
    # API ORIGINAL (preservada para compatibilidad)
    # ------------------------------------------------------------------

    def calculate_shannon_entropy(self, text: str) -> float:
        """Shannon entropy over characters. Original API preserved."""
        if not text:
            return 0.0
        prob = [n_c / len(text) for n_c in Counter(text).values()]
        return -sum(p * math.log2(p) for p in prob if p > 0)

    def detect_gaslighting_patterns(
        self, text: str, patterns: Optional[List[str]] = None
    ) -> dict:
        """
        Scans text for social engineering patterns.
        API original extendida: si no se pasa patterns, usa diccionario interno.
        patterns: list of 'Bad Faith' terms/regex.
        """
        if patterns is None:
            patterns = _DEFAULT_MANIPULATION_PATTERNS

        detected = []
        for p in patterns:
            try:
                if re.search(p, text, re.IGNORECASE):
                    detected.append(p)
            except re.error:
                # If not valid regex, literal search (v0 compatibility)
                if p.lower() in text.lower():
                    detected.append(p)

        risk_level = len(detected) / len(patterns) if patterns else 0.0
        return {
            "risk_level": round(risk_level, 4),
            "detected_triggers": detected,
            "integrity": "COMPROMISED" if risk_level > 0.4 else "OPTIMAL",
        }

    # ------------------------------------------------------------------
    # API EXTENDIDA — pipeline completo
    # ------------------------------------------------------------------

    def analyze(self, text: str, expected_entropy: Optional[float] = None) -> EntropyReport:
        """Pipeline completo: texto → EntropyReport con flag NOISE/OK/INSUFFICIENT."""
        tokens = self._tokenize(text)
        char_h = self.calculate_shannon_entropy(text)
        word_h = self._word_entropy(tokens)
        cond_h = self._conditional_entropy(tokens)
        gaslighting = self.detect_gaslighting_patterns(text)

        ratio = gap = None
        flag = "INSUFFICIENT_DATA"

        if len(tokens) >= self.min_tokens:
            if expected_entropy and expected_entropy > 0:
                ratio = word_h / expected_entropy
                gap = abs(ratio - 1.0)

                # Ajuste para texto técnico denso:
                # TTR alto indica vocabulario variado legítimo, no ruido.
                # Subimos el umbral efectivo proporcionalmente al TTR.
                ttr = len(set(tokens)) / max(len(tokens), 1)
                effective_threshold = self.noise_gap_threshold * (1 + ttr * 2.0)
                # Ejemplo: TTR=0.60 → threshold = 0.15 * 2.2 = 0.33
                #          TTR=0.80 → threshold = 0.15 * 2.6 = 0.39

                flag = "NOISE" if gap > effective_threshold else "OK"
            else:
                flag = "OK"

        return EntropyReport(
            char_entropy=round(char_h, 6),
            word_entropy=round(word_h, 6),
            conditional_entropy=round(cond_h, 6),
            expected_entropy=expected_entropy,
            ratio=round(ratio, 6) if ratio is not None else None,
            gap=round(gap, 6) if gap is not None else None,
            flag=flag,
            gaslighting=gaslighting,
            details={
                "token_count": len(tokens),
                "unique_tokens": len(set(tokens)),
                "ngram_size": self.ngram_size,
                "noise_gap_threshold": self.noise_gap_threshold,
            },
        )

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    def _tokenize(self, text: str) -> list[str]:
        return re.findall(r"\b\w+\b", text.lower())

    def _shannon(self, counts: Counter, total: int) -> float:
        vocab = len(counts)
        h = 0.0
        for c in counts.values():
            p = (c + self.smoothing) / (total + self.smoothing * vocab)
            h -= p * math.log(p, self.base)
        return h

    def _word_entropy(self, tokens: list[str]) -> float:
        return self._shannon(Counter(tokens), len(tokens)) if tokens else 0.0

    def _conditional_entropy(self, tokens: list[str]) -> float:
        """H(w_t | w_{t-1}): mide predictibilidad secuencial."""
        if len(tokens) < 2:
            return 0.0
        bigrams = Counter(zip(tokens[:-1], tokens[1:]))
        unigrams = Counter(tokens[:-1])
        total = sum(bigrams.values())
        h = 0.0
        for (w1, _), count in bigrams.items():
            p_bi = (count + self.smoothing) / (total + self.smoothing * len(bigrams))
            p_uni = (unigrams[w1] + self.smoothing) / (len(tokens) + self.smoothing * len(unigrams))
            h -= p_bi * math.log(max(p_bi / p_uni, 1e-12), self.base)
        return h


# ------------------------------------------------------------------
# Internal pattern dictionary (Spanish, regex-compatible)
# ------------------------------------------------------------------
_DEFAULT_MANIPULATION_PATTERNS = [
    # Contractual trap clauses
    r"renunci[ao]\s+(irrevocablemente|expresamente)",
    r"cede?\s+(todos\s+los\s+derechos|la\s+totalidad)",
    r"sin\s+derecho\s+a\s+compensaci[oó]n",
    r"de\s+forma\s+exclusiva\s+y\s+(permanente|perpetua)",
    r"propiedad\s+intelectual.{0,40}cede?",
    # Coercion
    r"no\s+(tienes?|tiene)\s+opci[oó]n",
    r"nos\s+veremos\s+obligados",
    r"sin\s+previo\s+aviso",
    r"terminaci[oó]n\s+unilateral",
    r"modificar\s+unilateralmente",
    # Gaslighting discursivo
    r"te\s+lo\s+est[aá]s\s+imaginando",
    r"siempre\s+exageras",
    r"est[aá]s\s+(loco|siendo\s+irracional)",
    r"nadie\s+m[aá]s\s+lo\s+ve\s+as[ií]",
    # Strategic vagueness
    r"a\s+criterio\s+de",
    r"seg[uú]n\s+corresponda",
    r"a\s+discreci[oó]n",
    r"en\s+los\s+t[eé]rminos\s+que\s+(se\s+)?determine",
]
