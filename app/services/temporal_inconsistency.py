"""
E11 — Temporal Inconsistency Thermometer.

Uses local regex/date parsing rules to catch high-confidence impossibilities
such as birth after graduation or death before birth. The optional dateparser
package can be installed later; regex is the safe default.

Author/standard origin: Gonzalo Emir Durante.
License: GPL-3.0 + Durante Invariance License v1.0.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .module_result import ModuleResult

SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")
YEAR_RE = re.compile(r"\b(1[5-9]\d{2}|20\d{2}|21\d{2})\b")
BIRTH_RE = re.compile(r"\b(born|naci[oó]|nacido|nacida|birth)\b", re.IGNORECASE)
GRAD_RE = re.compile(r"\b(graduated|graduate|gradu[oó]|graduado|graduada|graduation)\b", re.IGNORECASE)
DEATH_RE = re.compile(r"\b(died|death|mur[ií]o|falleci[oó]|fallecido|fallecida)\b", re.IGNORECASE)
FOUNDED_RE = re.compile(r"\b(founded|founded in|fund[oó]|fundada|fundado)\b", re.IGNORECASE)


@dataclass
class TemporalFacts:
    birth_years: list[int]
    graduation_years: list[int]
    death_years: list[int]
    founded_years: list[int]


def _years(sentence: str) -> list[int]:
    return [int(y) for y in YEAR_RE.findall(sentence)]


def _extract(text: str) -> TemporalFacts:
    facts = TemporalFacts([], [], [], [])
    for sentence in [s.strip() for s in SENTENCE_RE.split(text.strip()) if s.strip()] or [text]:
        years = _years(sentence)
        if not years:
            continue
        if BIRTH_RE.search(sentence):
            facts.birth_years.extend(years)
        if GRAD_RE.search(sentence):
            facts.graduation_years.extend(years)
        if DEATH_RE.search(sentence):
            facts.death_years.extend(years)
        if FOUNDED_RE.search(sentence):
            facts.founded_years.extend(years)
    return facts


def detect(text: str, penalty: float = 0.4) -> ModuleResult:
    facts = _extract(text)
    inconsistencies: list[str] = []

    for birth in facts.birth_years:
        for grad in facts.graduation_years:
            if birth > grad:
                inconsistencies.append(f"birth year {birth} occurs after graduation year {grad}")
            elif grad - birth < 10:
                inconsistencies.append(f"graduation year {grad} implies age under 10 for birth year {birth}")
        for death in facts.death_years:
            if death < birth:
                inconsistencies.append(f"death year {death} occurs before birth year {birth}")
            elif death - birth > 130:
                inconsistencies.append(f"lifespan {death - birth} years exceeds conservative bound")

    # Conservative cycle-style check for organizations/founding after closure can be
    # added later. Current version focuses on high-confidence biographical inversions.
    if inconsistencies:
        return ModuleResult(
            code="E11",
            name="Temporal Inconsistency",
            triggered=True,
            penalty=penalty,
            reason="high-confidence temporal ordering violation",
            evidence={"inconsistencies": inconsistencies[:5]},
        )

    return ModuleResult(
        code="E11",
        name="Temporal Inconsistency",
        reason="no high-confidence temporal contradiction detected",
        evidence={
            "birth_years": facts.birth_years,
            "graduation_years": facts.graduation_years,
            "death_years": facts.death_years,
        },
    )


def run(text: str) -> ModuleResult:
    return detect(text)
