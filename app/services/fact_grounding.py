"""
E10 — Narrative Inventiveness / Fact Grounding Thermometer.

This module is intentionally disabled unless a local knowledge base is provided.
It never calls external services. With a configured SQLite KB, it can flag a
small set of high-confidence factual anomalies while preserving SAS's distinction
between structural coherence and universal factual verification.

Expected KB schema options:
  1. entities(name TEXT PRIMARY KEY, birth_year INTEGER, death_year INTEGER)
  2. entity_aliases(alias TEXT, name TEXT)

Author/standard origin: Gonzalo Emir Durante.
License: GPL-3.0 + Durante Invariance License v1.0.
"""
from __future__ import annotations

import os
import re
import sqlite3
from pathlib import Path
from typing import Any

from .module_result import ModuleResult

ENTITY_RE = re.compile(r"\b([A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñ'-]+(?:\s+[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñ'-]+){0,3})\b")
YEAR_RE = re.compile(r"\b(1[5-9]\d{2}|20\d{2}|21\d{2})\b")
BORN_RE = re.compile(r"\b(born|naci[oó]|nacido|nacida|birth)\b", re.IGNORECASE)
DIED_RE = re.compile(r"\b(died|death|mur[ií]o|falleci[oó]|fallecido|fallecida|muere|murió)\b", re.IGNORECASE)


def _kb_path() -> str | None:
    value = os.getenv("SAS_FACT_KB_PATH", "").strip()
    return value or None


def _flag_unknown_entities() -> bool:
    return os.getenv("SAS_FACT_KB_FLAG_UNKNOWN", "false").strip().lower() in {"1", "true", "yes", "on"}


def _extract_entities(text: str) -> list[str]:
    """Extrae entidades del texto usando regex conservador."""
    try:
        import spacy  # type: ignore
        model_name = os.getenv("SAS_SPACY_MODEL", "en_core_web_sm")
        nlp = spacy.load(model_name)
        return sorted({ent.text.strip() for ent in nlp(text).ents if ent.label_ in {"PERSON", "ORG", "GPE", "LOC"}})
    except Exception:
        candidates = [m.group(1).strip() for m in ENTITY_RE.finditer(text)]
        filtered = [c for c in candidates if len(c) > 2 and c.lower() not in {"The", "This", "That"}]
        return sorted(set(filtered))[:20]


def _fetch_entity(conn: sqlite3.Connection, name: str) -> dict[str, Any] | None:
    """Busca entidad por nombre o alias."""
    try:
        row = conn.execute(
            "SELECT name, birth_year, death_year FROM entities WHERE lower(name)=lower(?) LIMIT 1",
            (name,),
        ).fetchone()
        if row:
            return {"name": row[0], "birth_year": row[1], "death_year": row[2]}
    except sqlite3.Error:
        return None

    try:
        row = conn.execute(
            """
            SELECT e.name, e.birth_year, e.death_year
            FROM entity_aliases a JOIN entities e ON lower(a.name)=lower(e.name)
            WHERE lower(a.alias)=lower(?) LIMIT 1
            """,
            (name,),
        ).fetchone()
        if row:
            return {"name": row[0], "birth_year": row[1], "death_year": row[2]}
    except sqlite3.Error:
        return None
    return None


def _extract_claim_years(sentence: str) -> dict[str, list[int]]:
    """Extrae años relacionados con nacimiento o muerte dentro de una oración específica."""
    years = [int(y) for y in YEAR_RE.findall(sentence)]
    return {
        "born": years if BORN_RE.search(sentence) else [],
        "died": years if DIED_RE.search(sentence) else [],
    }


def detect(text: str, penalty: float = 0.3) -> ModuleResult:
    """Detecta desalineamientos fácticos contra una base de conocimiento local."""
    path = _kb_path()
    if not path or not Path(path).exists():
        return ModuleResult(
            code="E10",
            name="Fact Grounding",
            enabled=False,
            skipped=True,
            reason="local knowledge base not configured; no penalty applied",
        )

    # Dividir el texto en oraciones para análisis por afirmación
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
    
    if not sentences:
        return ModuleResult(code="E10", name="Fact Grounding", reason="no sentences detected")

    contradictions = []
    unknown_entities = set()
    all_entities = set()

    try:
        with sqlite3.connect(path) as conn:
            for sentence in sentences:
                entities = _extract_entities(sentence)
                if not entities:
                    continue
                
                claim_years = _extract_claim_years(sentence)
                has_birth_claim = bool(claim_years["born"])
                has_death_claim = bool(claim_years["died"])
                
                for ent in entities:
                    all_entities.add(ent)
                    record = _fetch_entity(conn, ent)
                    
                    if record is None:
                        unknown_entities.add(ent)
                        continue
                    
                    # Verificar años de nacimiento
                    if has_birth_claim and record.get("birth_year"):
                        for year in claim_years["born"]:
                            if abs(int(record["birth_year"]) - year) > 1:
                                contradictions.append({
                                    "entity": ent,
                                    "claim": "birth_year",
                                    "sentence": sentence[:100],
                                    "text_year": year,
                                    "kb_year": record["birth_year"]
                                })
                    
                    # Verificar años de muerte
                    if has_death_claim and record.get("death_year"):
                        for year in claim_years["died"]:
                            if abs(int(record["death_year"]) - year) > 1:
                                contradictions.append({
                                    "entity": ent,
                                    "claim": "death_year",
                                    "sentence": sentence[:100],
                                    "text_year": year,
                                    "kb_year": record["death_year"]
                                })
    
    except sqlite3.Error as exc:
        return ModuleResult(
            code="E10",
            name="Fact Grounding",
            enabled=False,
            skipped=True,
            reason=f"knowledge base unavailable: {exc}",
        )

    # Determinar si se dispara el módulo
    has_contradiction = len(contradictions) > 0
    has_unknown = len(unknown_entities) > 0 and _flag_unknown_entities()
    
    # IMPORTANTE: Solo triggered si HAY contradicciones O (unknown Y flag_unknown)
    # Evita falsos positivos cuando no hay claims fácticos
    if has_contradiction or has_unknown:
        return ModuleResult(
            code="E10",
            name="Fact Grounding",
            triggered=True,
            penalty=penalty,
            reason="local KB mismatch detected" if has_contradiction else "unknown entity detected",
            evidence={
                "contradictions": contradictions[:5],
                "unknown_entities": list(unknown_entities)[:10] if has_unknown else [],
                "checked_entities": len(all_entities)
            },
        )

    return ModuleResult(
        code="E10",
        name="Fact Grounding",
        reason="no high-confidence KB mismatch detected",
        evidence={
            "checked_entities": len(all_entities),
            "unknown_entities": list(unknown_entities)[:10]
        },
    )


def run(text: str) -> ModuleResult:
    return detect(text)