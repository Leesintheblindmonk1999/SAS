"""
E9 — Logical Contradiction Thermometer.

Detects explicit intra-response polarity inversions using conservative symbolic
rules. Optional NLI models can be added later without changing the public API.

Design: high precision over recall. The module only triggers when two sentences
are lexically near-equivalent after removing negation markers and have opposite
polarity.

Author/standard origin: Gonzalo Emir Durante.
License: GPL-3.0 + Durante Invariance License v1.0.
"""
from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Iterable

from .module_result import ModuleResult

NEGATION_RE = re.compile(
    r"\b(no|not|never|nunca|jam[aá]s|cannot|can't|cant|won't|wont|don't|dont|"
    r"doesn't|doesnt|didn't|didnt|isn't|isnt|aren't|arent|wasn't|wasnt|"
    r"weren't|werent|without|sin|false|falso|incorrect|incorrecto|impossible|imposible)\b",
    re.IGNORECASE,
)
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")
TOKEN_RE = re.compile(r"[a-záéíóúñü0-9]+", re.IGNORECASE)

STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "to", "of", "and", "or", "in", "on", "at", "for", "with", "as", "by",
    "el", "la", "los", "las", "un", "una", "es", "son", "fue", "era", "de",
    "del", "y", "o", "en", "con", "por", "para", "como", "que",
}


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in SENTENCE_RE.split(text.strip()) if s.strip()]


def _tokens_without_negation(sentence: str) -> list[str]:
    cleaned = NEGATION_RE.sub(" ", sentence.lower())
    return [t for t in TOKEN_RE.findall(cleaned) if t not in STOPWORDS and len(t) > 1]


def _has_negation(sentence: str) -> bool:
    return bool(NEGATION_RE.search(sentence))


def _similarity(a_tokens: Iterable[str], b_tokens: Iterable[str]) -> float:
    a = list(a_tokens)
    b = list(b_tokens)
    if not a or not b:
        return 0.0
    set_a, set_b = set(a), set(b)
    jaccard = len(set_a & set_b) / max(1, len(set_a | set_b))
    seq = SequenceMatcher(None, " ".join(a), " ".join(b)).ratio()
    return max(jaccard, seq)


def detect(sentences: list[str] | str, penalty: float = 0.5) -> ModuleResult:
    if isinstance(sentences, str):
        sentences = split_sentences(sentences)

    if len(sentences) < 2:
        return ModuleResult(
            code="E9",
            name="Logical Contradiction",
            reason="fewer than two sentences",
        )

    analyzed = []
    for sentence in sentences:
        analyzed.append({
            "sentence": sentence,
            "negated": _has_negation(sentence),
            "tokens": _tokens_without_negation(sentence),
        })

    for i in range(len(analyzed)):
        for j in range(i + 1, len(analyzed)):
            left = analyzed[i]
            right = analyzed[j]
            if left["negated"] == right["negated"]:
                continue
            sim = _similarity(left["tokens"], right["tokens"])
            if sim >= 0.65 and len(set(left["tokens"]) & set(right["tokens"])) >= 2:
                return ModuleResult(
                    code="E9",
                    name="Logical Contradiction",
                    triggered=True,
                    penalty=penalty,
                    reason="opposite polarity on near-equivalent proposition",
                    evidence={
                        "sentence_i": left["sentence"],
                        "sentence_j": right["sentence"],
                        "similarity": round(sim, 4),
                    },
                )

    return ModuleResult(
        code="E9",
        name="Logical Contradiction",
        reason="no high-confidence polarity inversion detected",
    )


# Compatibility alias used by tests and detector.
def run(text: str) -> ModuleResult:
    return detect(text)
