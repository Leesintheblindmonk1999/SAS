"""
core/msc_engine_v5.py — Omni-Scanner Semantic v5.0
═══════════════════════════════════════════════════════════════════════════════
Multi-Sample Consistency Engine v5.0 — "Oído Absoluto Semántico"

PRINCIPIO TEÓRICO:
  La Constante de Durante κD = 0.56 emerge de cinco convergencias matemáticas
  independientes (Termodinámica Estadística, Teoría de Percolación, Rate-Distortion,
  Estabilidad de Lyapunov, Razón Áurea). Es el umbral termodinámico donde el ruido
  semántico supera la capacidad de reconstrucción estructural fiel.

  El MSC Engine opera como un "nivel de burbuja" sobre esta constante:
  si un texto alucinado es sometido a presión térmica variable (T ∈ {0.3→1.1}),
  las regiones de inestabilidad semántica "florecen" de forma diferente en cada
  muestra. Un hecho estructural real permanece invariante. Una alucinación diverge.

ARQUITECTURA v5.0:
  Layer 0.5  → Domain Classifier (TDM — Terminología Agnóstica)
  Layer 1    → Thermal Injector (5 prompts adaptativos por temperatura)
  Layer 2    → Pairwise ISI Matrix con pesos W_ij = W_Ti · W_Tj
  Layer 3    → σ_MSC Ponderado (desviación estándar ponderada)
  Layer 4    → Adaptive Threshold por dominio (0.10 / 0.15 / 0.18)
  Layer 5    → Fallback Logic (OPACIDAD_BACKEND si n < 3)
  Layer 6    → Integration con ISI_TDA (ISI_FINAL = min(ISI_TDA, ISI_MSC))

REGISTRO Y AUTORÍA:
  Author   : Gonzalo Emir Durante — Project Manifold 0.56 / Protocol ANEXA Ultra
  Registry : EX-2026-18792778 (TAD, Argentina)
  CONICET  : Ticket #2026032610006187
  DOI      : https://doi.org/10.5281/zenodo.19052627
  OTS      : Bitcoin blockchain — anclaje 10 marzo 2026
  License  : Durante Invariance License v1.0 (GPL-3.0 + atribución obligatoria)
  LinkedIn : https://www.linkedin.com/in/gonzalo-emir-durante-8178b6277/
"""
from __future__ import annotations

import os
import re
import sys
import json
import time
import math
import hashlib
import datetime
import itertools
from collections import Counter
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple

import numpy as np
import requests

# ── Import interno — semantic_diff v4.2 ───────────────────────────────────────
# Si el módulo no está disponible (testing aislado), se usa un stub.
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from core.semantic_diff import quick_diff, DOMAIN_KAPPA
    _TDA_AVAILABLE = True
except ImportError:
    _TDA_AVAILABLE = False
    DOMAIN_KAPPA: Dict[str, float] = {
        "legal": 0.54, "medical": 0.58, "code": 0.54,
        "financial": 0.56, "discourse": 0.54, "scientific": 0.55,
        "academic": 0.58, "regulatory": 0.56, "literature": 0.52,
        "generic": 0.56,
    }

    def quick_diff(text_a: str, text_b: str, domain: str = "generic") -> Any:  # type: ignore
        """Stub para testing sin semantic_diff instalado."""
        raise RuntimeError(
            "semantic_diff v4.2 no disponible. "
            "Instalar el paquete Omni-Scanner completo o proveer ISI externamente."
        )


# ══════════════════════════════════════════════════════════════════════════════
# SELLO DE INTEGRIDAD SHA-256
# Reemplazar "PENDING_SEAL" con el hash real tras el primer release sellado.
# Verificación: sha256sum core/msc_engine_v5.py
# ══════════════════════════════════════════════════════════════════════════════

_MODULE_REFERENCE_HASH: str = "PENDING_SEAL"


def verify_module_integrity(warn: bool = True) -> Tuple[bool, str]:
    """
    Calcula SHA-256 del propio archivo y lo compara con _MODULE_REFERENCE_HASH.
    Retorna (ok: bool, current_hash: str).
    ok = True si el hash coincide o si el sellado está pendiente.
    """
    try:
        with open(os.path.abspath(__file__), "rb") as fh:
            current_hash = hashlib.sha256(fh.read()).hexdigest()
    except Exception as exc:
        if warn:
            print(f"[MSC v5 INTEGRITY] No se pudo leer el archivo fuente: {exc}")
        return False, ""

    if _MODULE_REFERENCE_HASH == "PENDING_SEAL":
        return True, current_hash  # sellado pendiente

    ok = current_hash == _MODULE_REFERENCE_HASH
    if not ok and warn:
        print(
            f"\n[MSC v5 INTEGRITY] ⚠ Hash no coincide.\n"
            f"  Esperado : {_MODULE_REFERENCE_HASH}\n"
            f"  Actual   : {current_hash}\n"
            f"  Verificar contra TAD EX-2026-18792778.\n"
        )
    return ok, current_hash


# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTES GLOBALES
# ══════════════════════════════════════════════════════════════════════════════

# κD = 0.56 — La Constante de Durante. No configurable externamente.
# Converge desde 5 caminos independientes (ver paper v2).
KAPPA_D: float = 0.56

# Temperaturas del Inyector Térmico
DEFAULT_TEMPERATURES: List[float] = [0.3, 0.7, 1.1, 1.5, 2.0]

# Pesos térmicos W_Ti — favorecen determinismo (T baja = más confiable)
THERMAL_WEIGHTS: Dict[str, float] = {
    "low":    1.5,   # T ≤ 0.5  — zona determinista
    "mid":    1.0,   # 0.5 < T ≤ 0.9 — zona estándar
    "high":   0.5,   # T > 0.9  — zona de estrés / exploración
}

# Umbrales σ_MSC adaptativos por tipo de dominio
SIGMA_THRESHOLDS: Dict[str, float] = {
    "rigid":    0.12,   # Legal, Médico — tolerancia mínima
    "standard": 0.15,   # Académico, Científico — κD base
    "flexible": 0.18,   # Creativo, Discurso — mayor varianza permitida
}

# Normalización σ para cálculo ISI_MSC
SIGMA_NORM: float = 0.30

# Muestras mínimas para análisis válido
MIN_SAMPLES_VALID: int = 3

# Longitud mínima de tokens por muestra
MIN_TOKEN_LENGTH: int = 50

# Estados de veredicto
STATUS_RUPTURE   = "ESTADO: RUPTURA_DE_MANIFOLD"
STATUS_COHERENT  = "ESTADO: COHERENTE"
STATUS_RISK      = "ESTADO: RIESGO_SEMANTICO"
STATUS_OPAQUE    = "ESTADO: OPACIDAD_BACKEND"
STATUS_CRITICAL  = "ESTADO: RUPTURA_CRITICA_DE_MANIFOLD"


# ══════════════════════════════════════════════════════════════════════════════
# LAYER 0.5 — DOMAIN CLASSIFIER (TDM — Terminología Agnóstica)
# ══════════════════════════════════════════════════════════════════════════════

class DomainClassifier:
    """
    Clasifica el dominio de un texto sin depender de listas léxicas fijas.
    Usa "Densidad de Tokens de Baja Frecuencia" (DTBF) como proxy de rigidez
    terminológica — independiente del idioma.

    Lógica:
      - Textos rígidos (legal/médico) tienen alta concentración de tokens raros,
        frases cortas y alta precisión sintáctica.
      - Textos flexibles (creativos/discurso) tienen alta entropía léxica,
        oraciones largas y uso frecuente de adjetivos/metáforas.
      - Default académico/científico = estándar.

    El clasificador retorna: "rigid" | "standard" | "flexible"
    y el σ_threshold correspondiente.
    """

    # Tokens de alta frecuencia universal (stop words multilingüe simplificado)
    _UNIVERSAL_HIGH_FREQ = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "have",
        "has", "had", "do", "does", "did", "will", "would", "could", "should",
        "may", "might", "shall", "de", "la", "el", "en", "que", "los", "las",
        "un", "una", "por", "con", "del", "al", "se", "no", "si", "su", "es",
        "y", "o", "e", "but", "and", "or", "not", "this", "that", "it", "of",
        "to", "in", "for", "on", "with", "at", "by", "from", "as", "into",
    }

    def classify(self, text: str) -> Tuple[str, float]:
        """
        Analiza el texto y retorna (domain_type, sigma_threshold).

        domain_type: "rigid" | "standard" | "flexible"
        sigma_threshold: valor numérico correspondiente
        """
        sentences = [s.strip() for s in re.split(r'[.!?;\n]+', text) if len(s.strip()) > 5]
        if not sentences:
            return "standard", SIGMA_THRESHOLDS["standard"]

        tokens_raw = re.findall(r"\b\w+\b", text.lower())
        if not tokens_raw:
            return "standard", SIGMA_THRESHOLDS["standard"]

        # ── Métrica 1: Densidad de Tokens de Baja Frecuencia (DTBF) ──────────
        # Tokens que NO son stop words y tienen longitud ≥ 6 (terminología técnica)
        technical_tokens = [
            t for t in tokens_raw
            if t not in self._UNIVERSAL_HIGH_FREQ and len(t) >= 6
        ]
        dtbf = len(technical_tokens) / max(len(tokens_raw), 1)

        # ── Métrica 2: Longitud media de oración ─────────────────────────────
        sentence_lengths = [
            len(re.findall(r"\b\w+\b", s)) for s in sentences
        ]
        mean_sentence_len = np.mean(sentence_lengths) if sentence_lengths else 0

        # ── Métrica 3: Entropía léxica (variedad de vocabulario) ─────────────
        freq = Counter(tokens_raw)
        total = sum(freq.values())
        entropy = -sum(
            (c / total) * math.log2(c / total)
            for c in freq.values() if c > 0
        )
        max_entropy = math.log2(len(freq)) if len(freq) > 1 else 1.0
        normalized_entropy = entropy / max_entropy

        # ── Métrica 4: Ratio de números y unidades ───────────────────────────
        # Alta presencia de números → dominio técnico/médico/legal
        numeric_tokens = re.findall(r'\b\d+[\.,]?\d*\s*(?:mg|kg|ml|%|°|§|art\.?)?\b', text, re.IGNORECASE)
        numeric_ratio = len(numeric_tokens) / max(len(sentences), 1)

        # ── Clasificación por puntuación compuesta ────────────────────────────
        # Score rígido: alta DTBF, oraciones cortas, baja entropía, alta presencia numérica
        rigidity_score = (
            dtbf * 0.40
            + (1.0 - min(mean_sentence_len / 30.0, 1.0)) * 0.25
            + (1.0 - normalized_entropy) * 0.20
            + min(numeric_ratio / 3.0, 1.0) * 0.15
        )

        # Score flexible: baja DTBF, oraciones largas, alta entropía
        flexibility_score = (
            (1.0 - dtbf) * 0.35
            + min(mean_sentence_len / 25.0, 1.0) * 0.35
            + normalized_entropy * 0.30
        )

        if rigidity_score > 0.55:
            return "rigid", SIGMA_THRESHOLDS["rigid"]
        elif flexibility_score > 0.60:
            return "flexible", SIGMA_THRESHOLDS["flexible"]
        else:
            return "standard", SIGMA_THRESHOLDS["standard"]

    def get_kappa_for_domain(self, domain_name: Optional[str]) -> float:
        """Retorna κD adaptivo para el dominio dado, o el global si es None."""
        if domain_name and domain_name in DOMAIN_KAPPA:
            return DOMAIN_KAPPA[domain_name]
        return KAPPA_D


# ══════════════════════════════════════════════════════════════════════════════
# LAYER 1 — THERMAL INJECTOR (Muestreo de Entropía Controlada)
# ══════════════════════════════════════════════════════════════════════════════

class ThermalInjector:
    """
    Genera 5 variantes de prompt por temperatura, cada una diseñada para
    inducir un nivel diferente de exploración semántica sin perder el
    marco de referencia del input original.

    Si un dato es una verdad estructural:
      → Las 5 respuestas dirán lo mismo con distintas palabras → σ bajo
    Si es una alucinación sembrada:
      → A T=0.3 dirá "A", a T=1.1 dirá "B" o "X" → σ alto → RUPTURA

    Los modificadores son intencionalmente genéricos para operar en
    cualquier idioma y dominio sin requerir personalización.
    """

    # Modificadores por zona térmica
    _MODIFIERS: Dict[float, str] = {
        0.3: (
            "Provide the exact technical answer. Prioritize brevity and rigor. "
            "Do not elaborate beyond what is strictly necessary."
        ),
        0.5: (
            "Explain the resolution by following the causal logic step by step. "
            "Be precise and structured."
        ),
        0.7: (
            "Respond in a standard way, maintaining natural fluency. "
            "Balance completeness and conciseness."
        ),
        0.9: (
            "Provide a detailed response, exploring possible technical nuances "
            "and edge cases relevant to the topic."
        ),
        1.1: (
            "Generate a creative and expansive response on the topic. "
            "Explore connections, implications, and broader context freely."
        ),
    }

    def build_prompt(self, original_input: str, temperature: float) -> str:
        """
        Construye el prompt inyectado para una temperatura dada.

        Estructura:
          [CONTEXT] + [MODIFIER] + [INPUT]

        El modificador ajusta el modo de generación sin alterar el contenido
        solicitado — solo la profundidad y el estilo de exploración.
        """
        # Buscar el modificador más cercano a la temperatura solicitada
        closest_temp = min(self._MODIFIERS.keys(), key=lambda t: abs(t - temperature))
        modifier = self._MODIFIERS[closest_temp]

        return (
            f"[INSTRUCTION: {modifier}]\n\n"
            f"{original_input}"
        )

    def build_all_prompts(
        self,
        original_input: str,
        temperatures: List[float]
    ) -> List[Tuple[float, str]]:
        """
        Genera todos los prompts inyectados para la lista de temperaturas.
        Retorna lista de (temperatura, prompt_inyectado).
        """
        return [(t, self.build_prompt(original_input, t)) for t in temperatures]


# ══════════════════════════════════════════════════════════════════════════════
# BACKENDS LLM — Ollama y OpenRouter con retry + backoff
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class SampleResult:
    """Resultado de una generación individual."""
    temperature: float
    text:        str
    success:     bool
    error:       Optional[str] = None
    latency_ms:  float         = 0.0


class OllamaBackend:
    """Backend Ollama para generación local."""

    def __init__(
        self,
        model:      str   = "llama3.2",
        base_url:   str   = "http://localhost:11434",
        max_retries: int  = 3,
        timeout:    int   = 60,
    ):
        self.model       = model
        self.base_url    = base_url.rstrip("/")
        self.max_retries = max_retries
        self.timeout     = timeout

    def generate(self, prompt: str, temperature: float) -> SampleResult:
        """Genera una respuesta con retry exponencial."""
        url = f"{self.base_url}/api/generate"

        for attempt in range(self.max_retries):
            t0 = time.time()
            try:
                resp = requests.post(
                    url,
                    json={
                        "model":       self.model,
                        "prompt":      prompt,
                        "temperature": temperature,
                        "stream":      False,
                        "options":     {"num_predict": 512},
                    },
                    timeout=self.timeout,
                )
                resp.raise_for_status()
                data = resp.json()
                text = data.get("response", "").strip()
                latency = (time.time() - t0) * 1000

                if not text:
                    raise ValueError("Respuesta vacía del backend")

                return SampleResult(
                    temperature=temperature,
                    text=text,
                    success=True,
                    latency_ms=latency,
                )

            except requests.exceptions.Timeout:
                error = f"Timeout en intento {attempt + 1}"
            except requests.exceptions.HTTPError as e:
                error = f"HTTP {e.response.status_code}: {e}"
            except Exception as e:
                error = str(e)

            if attempt < self.max_retries - 1:
                wait = 2 ** attempt  # backoff exponencial: 1s, 2s, 4s
                time.sleep(wait)

        return SampleResult(
            temperature=temperature,
            text="",
            success=False,
            error=error,
        )


class OpenRouterBackend:
    """Backend OpenRouter para modelos en la nube."""

    def __init__(
        self,
        model:       str  = "mistralai/mistral-7b-instruct",
        api_key:     str  = "",
        max_retries: int  = 3,
        timeout:     int  = 90,
    ):
        self.model       = model
        self.api_key     = api_key or os.environ.get("OPENROUTER_API_KEY", "")
        self.max_retries = max_retries
        self.timeout     = timeout
        self._url        = "https://openrouter.ai/api/v1/chat/completions"

    def generate(self, prompt: str, temperature: float) -> SampleResult:
        """Genera con retry. Clampea temperatura a [0.0, 1.0] si la API no acepta > 1.0."""
        # Algunos endpoints no aceptan T > 1.0 — fallback a 1.0 con warning
        api_temp = temperature
        clamped  = False
        if temperature > 1.0:
            api_temp = 1.0
            clamped  = True

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type":  "application/json",
        }

        for attempt in range(self.max_retries):
            t0 = time.time()
            try:
                resp = requests.post(
                    self._url,
                    headers=headers,
                    json={
                        "model":       self.model,
                        "messages":    [{"role": "user", "content": prompt}],
                        "temperature": api_temp,
                        "max_tokens":  512,
                    },
                    timeout=self.timeout,
                )
                resp.raise_for_status()
                data  = resp.json()
                text  = data["choices"][0]["message"]["content"].strip()
                latency = (time.time() - t0) * 1000

                if not text:
                    raise ValueError("Respuesta vacía del backend")

                result = SampleResult(
                    temperature=temperature,
                    text=text,
                    success=True,
                    latency_ms=latency,
                )
                if clamped:
                    result.error = f"[WARN] Temperatura {temperature} clampeada a 1.0 por el backend"
                return result

            except requests.exceptions.Timeout:
                error = f"Timeout en intento {attempt + 1}"
            except requests.exceptions.HTTPError as e:
                status = e.response.status_code if e.response else "?"
                # 422 = temperatura inválida para este modelo
                if status == 422:
                    error = f"HTTP 422: temperatura {temperature} rechazada"
                    break  # no reintentar, es un error de parámetro
                error = f"HTTP {status}: {e}"
            except Exception as e:
                error = str(e)

            if attempt < self.max_retries - 1:
                time.sleep(2 ** attempt)

        return SampleResult(
            temperature=temperature,
            text="",
            success=False,
            error=error,
        )


# ══════════════════════════════════════════════════════════════════════════════
# LAYER 2-3 — MATRIZ PAIRWISE ISI + σ PONDERADO
# ══════════════════════════════════════════════════════════════════════════════

def _thermal_weight(temperature: float) -> float:
    """
    Retorna W_Ti según la zona térmica.
    T ≤ 0.5  → 1.5 (alta confianza, zona determinista)
    0.5 < T ≤ 0.9 → 1.0 (confianza estándar)
    T > 0.9  → 0.5 (baja confianza, zona de estrés)
    """
    if temperature <= 0.5:
        return THERMAL_WEIGHTS["low"]
    elif temperature <= 0.9:
        return THERMAL_WEIGHTS["mid"]
    else:
        return THERMAL_WEIGHTS["high"]


def _compute_isi_between(text_a: str, text_b: str, domain: Optional[str] = None) -> float:
    """
    Calcula ISI entre dos textos usando quick_diff de semantic_diff v4.2.
    Si TDA no está disponible, usa similitud coseno bag-of-words como fallback.

    Retorna ISI ∈ [0, 1].
    """
    if _TDA_AVAILABLE:
        try:
            report = quick_diff(text_a, text_b, domain=domain or "generic")
            return float(getattr(report, "isi", 0.5))
        except Exception:
            pass

    # ── Fallback: similitud coseno BoW ────────────────────────────────────────
    def _tokenize(t: str) -> Counter:
        return Counter(re.findall(r"\b\w+\b", t.lower()))

    freq_a = _tokenize(text_a)
    freq_b = _tokenize(text_b)
    vocab  = set(freq_a) | set(freq_b)

    if not vocab:
        return 0.0

    dot   = sum(freq_a.get(w, 0) * freq_b.get(w, 0) for w in vocab)
    mag_a = math.sqrt(sum(v ** 2 for v in freq_a.values()))
    mag_b = math.sqrt(sum(v ** 2 for v in freq_b.values()))

    if mag_a == 0 or mag_b == 0:
        return 0.0

    return round(dot / (mag_a * mag_b), 6)


@dataclass
class PairwiseResult:
    """Resultado de un par (i, j) en la matriz ISI."""
    temp_i:  float
    temp_j:  float
    isi:     float
    weight:  float   # W_ij = W_Ti * W_Tj


def compute_pairwise_matrix(
    samples:      List[SampleResult],
    domain:       Optional[str] = None,
) -> List[PairwiseResult]:
    """
    Construye la Matriz de Similitud Invariante (MSI) pairwise.

    Para cada par (i, j) con i < j:
      1. Calcula ISI(R_i, R_j) via semantic_diff v4.2
      2. Aplica peso W_ij = W_Ti · W_Tj

    Retorna lista de PairwiseResult (C(n,2) entradas para n samples).
    """
    valid = [s for s in samples if s.success and len(s.text.split()) >= MIN_TOKEN_LENGTH]
    results: List[PairwiseResult] = []

    for i, j in itertools.combinations(range(len(valid)), 2):
        s_i = valid[i]
        s_j = valid[j]

        isi = _compute_isi_between(s_i.text, s_j.text, domain=domain)
        w_i = _thermal_weight(s_i.temperature)
        w_j = _thermal_weight(s_j.temperature)
        w_ij = w_i * w_j

        results.append(PairwiseResult(
            temp_i=s_i.temperature,
            temp_j=s_j.temperature,
            isi=isi,
            weight=w_ij,
        ))

    return results


def compute_weighted_sigma(pairs: List[PairwiseResult]) -> Tuple[float, float]:
    """
    Calcula σ_MSC ponderado y ISI medio ponderado.

    Fórmula:
      ISI_mean = Σ(W_ij · ISI_ij) / Σ(W_ij)
      σ_MSC   = sqrt( Σ(W_ij · (ISI_ij - ISI_mean)²) / Σ(W_ij) )

    Retorna (sigma_msc, isi_mean_weighted).

    La convergencia de κD = 0.56 implica que un σ_MSC > threshold
    indica que el espacio de probabilidad del modelo no es estable
    en torno a la afirmación evaluada — señal de incoherencia estructural.
    """
    if not pairs:
        return 0.0, 0.0

    total_weight = sum(p.weight for p in pairs)
    if total_weight == 0:
        return 0.0, 0.0

    isi_mean = sum(p.weight * p.isi for p in pairs) / total_weight
    variance = sum(p.weight * (p.isi - isi_mean) ** 2 for p in pairs) / total_weight
    sigma    = math.sqrt(variance)

    return round(sigma, 6), round(isi_mean, 6)


# ══════════════════════════════════════════════════════════════════════════════
# RESULTADO ESTRUCTURADO
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class MSCEngineResult:
    """
    Objeto de salida del MSC Engine v5.0.
    Todos los campos son serializables a JSON para auditoría forense.
    """
    # Métricas principales
    isi_final:       float
    weighted_sigma:  float
    isi_msc:         float
    isi_mean:        float
    samples_count:   int
    valid_count:     int
    status_string:   str

    # Contexto de análisis
    domain_type:     str           # "rigid" | "standard" | "flexible"
    sigma_threshold: float
    kappa_d:         float
    temperatures:    List[float]

    # Integración TDA
    isi_tda:         Optional[float] = None

    # Detalle pairwise
    pairwise:        List[Dict[str, Any]] = field(default_factory=list)

    # Metadatos forenses
    timestamp:       str = field(default_factory=lambda: datetime.datetime.utcnow().isoformat() + "Z")
    prompt_hash:     str = ""
    report_hash:     str = ""
    author:          str = "Gonzalo Emir Durante"
    registry:        str = "EX-2026-18792778 (TAD, Argentina)"
    doi:             str = "https://doi.org/10.5281/zenodo.19052627"
    license:         str = "Durante Invariance License v1.0"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "isi_final":       self.isi_final,
            "weighted_sigma":  self.weighted_sigma,
            "isi_msc":         self.isi_msc,
            "isi_mean":        self.isi_mean,
            "samples_count":   self.samples_count,
            "valid_count":     self.valid_count,
            "status_string":   self.status_string,
            "domain_type":     self.domain_type,
            "sigma_threshold": self.sigma_threshold,
            "kappa_d":         self.kappa_d,
            "temperatures":    self.temperatures,
            "isi_tda":         self.isi_tda,
            "pairwise":        self.pairwise,
            "timestamp":       self.timestamp,
            "prompt_hash":     self.prompt_hash,
            "report_hash":     self.report_hash,
            "author":          self.author,
            "registry":        self.registry,
            "doi":             self.doi,
            "license":         self.license,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    @property
    def is_rupture(self) -> bool:
        return self.isi_final < self.kappa_d


# ══════════════════════════════════════════════════════════════════════════════
# MSC ENGINE v5.0 — MOTOR PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

class MSCEngineV5:
    """
    Motor de Consistencia Multi-Sample v5.0.

    Orquesta el pipeline completo:
      DomainClassifier → ThermalInjector → Backend(s) → PairwiseMatrix
      → WeightedSigma → AdaptiveThreshold → FallbackLogic → MSCEngineResult

    Uso básico:
      engine = MSCEngineV5(backend=OllamaBackend(model="llama3.2"))
      result = engine.analyze(prompt="Cuál es la masa del electrón?", isi_tda=0.72)
      print(result.to_json())

    Uso avanzado (samples pre-generados):
      result = engine.analyze_from_samples(samples, temperatures, isi_tda=0.68)
    """

    def __init__(
        self,
        backend:      Optional[Any]        = None,
        temperatures: List[float]          = None,
        domain:       Optional[str]        = None,
        kappa_d:      float                = KAPPA_D,
    ):
        self.backend      = backend
        self.temperatures = temperatures or DEFAULT_TEMPERATURES
        self.domain       = domain
        self.kappa_d      = kappa_d

        self._injector   = ThermalInjector()
        self._classifier = DomainClassifier()

    # ── Generación de samples ─────────────────────────────────────────────────

    def _generate_samples(self, prompt: str) -> List[SampleResult]:
        """
        Inyecta prompts térmicos y genera muestras via backend.
        Maneja fallback si el backend rechaza temperaturas altas.
        """
        if self.backend is None:
            raise RuntimeError(
                "Backend LLM no configurado. "
                "Usar analyze_from_samples() para samples pre-generados."
            )

        injected = self._injector.build_all_prompts(prompt, self.temperatures)
        samples: List[SampleResult] = []

        for temp, injected_prompt in injected:
            result = self.backend.generate(injected_prompt, temp)
            samples.append(result)

        return samples

    # ── Pipeline de análisis ─────────────────────────────────────────────────

    def analyze_from_samples(
        self,
        samples:      List[SampleResult],
        temperatures: Optional[List[float]] = None,
        isi_tda:      Optional[float]       = None,
        prompt:       str                   = "",
    ) -> MSCEngineResult:
        """
        Analiza consistency a partir de samples pre-generados.

        Args:
            samples:      Lista de SampleResult (generados externamente o via _generate_samples)
            temperatures: Temperaturas usadas (opcional, para metadatos)
            isi_tda:      ISI de la capa TDA (semantic_diff v4.2). Si se provee,
                          ISI_FINAL = min(ISI_TDA, ISI_MSC).
            prompt:       Prompt original (para hash forense).

        Returns:
            MSCEngineResult con todos los campos poblados.
        """
        temps = temperatures or self.temperatures
        ts    = datetime.datetime.utcnow().isoformat() + "Z"

        # Hash del prompt original (privacidad + trazabilidad)
        prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16] if prompt else ""

        # ── LAYER 0.5: Domain Classification ─────────────────────────────────
        # Usar el texto más largo disponible para mejor clasificación
        reference_text = max(
            (s.text for s in samples if s.success),
            key=len,
            default="",
        )
        if reference_text:
            domain_type, sigma_threshold = self._classifier.classify(reference_text)
        else:
            domain_type, sigma_threshold = "standard", SIGMA_THRESHOLDS["standard"]

        # Si el dominio fue forzado en el constructor, aplicar κD adaptivo
        effective_kappa = self._classifier.get_kappa_for_domain(self.domain) \
            if self.domain else self.kappa_d

        # ── Filtrar samples válidos ───────────────────────────────────────────
        valid_samples = [
            s for s in samples
            if s.success and len(s.text.split()) >= MIN_TOKEN_LENGTH
        ]
        n_valid = len(valid_samples)
        n_total = len(samples)

        # ── LAYER 5: Fallback Logic ───────────────────────────────────────────
        if n_valid < MIN_SAMPLES_VALID:
            # OPACIDAD_BACKEND — no hay suficientes muestras para análisis
            isi_final = isi_tda if isi_tda is not None else 0.5
            return MSCEngineResult(
                isi_final=round(isi_final, 6),
                weighted_sigma=0.0,
                isi_msc=0.5,
                isi_mean=0.0,
                samples_count=n_total,
                valid_count=n_valid,
                status_string=STATUS_OPAQUE,
                domain_type=domain_type,
                sigma_threshold=sigma_threshold,
                kappa_d=effective_kappa,
                temperatures=temps,
                isi_tda=isi_tda,
                timestamp=ts,
                prompt_hash=prompt_hash,
            )

        # ── LAYER 2: Pairwise ISI Matrix ──────────────────────────────────────
        pairs = compute_pairwise_matrix(valid_samples, domain=self.domain)

        # ── LAYER 3: σ_MSC Ponderado ──────────────────────────────────────────
        weighted_sigma, isi_mean = compute_weighted_sigma(pairs)

        # ── ISI_MSC desde σ_MSC ───────────────────────────────────────────────
        # Si σ > threshold → incoherente → ISI_MSC = 0.0
        # Si no → ISI_MSC = 1 - (σ / SIGMA_NORM), clampeado a [0, 1]
        if weighted_sigma > sigma_threshold:
            isi_msc = 0.0
        else:
            isi_msc = max(0.0, min(1.0, 1.0 - (weighted_sigma / SIGMA_NORM)))

        # ── LAYER 6: Integration con ISI_TDA ─────────────────────────────────
        if isi_tda is not None:
            isi_final = min(float(isi_tda), isi_msc)
        else:
            isi_final = isi_msc

        # ── Status String ─────────────────────────────────────────────────────
        if isi_final < effective_kappa:
            if weighted_sigma > sigma_threshold * 1.5:
                status = STATUS_CRITICAL
            else:
                status = STATUS_RUPTURE
        elif isi_final < effective_kappa * 1.10:
            status = STATUS_RISK
        else:
            status = STATUS_COHERENT

        # ── Serializar pairwise para auditoría ───────────────────────────────
        pairwise_dicts = [
            {
                "temp_i":  p.temp_i,
                "temp_j":  p.temp_j,
                "isi":     round(p.isi, 6),
                "weight":  round(p.weight, 4),
            }
            for p in pairs
        ]

        result = MSCEngineResult(
            isi_final=round(isi_final, 6),
            weighted_sigma=round(weighted_sigma, 6),
            isi_msc=round(isi_msc, 6),
            isi_mean=round(isi_mean, 6),
            samples_count=n_total,
            valid_count=n_valid,
            status_string=status,
            domain_type=domain_type,
            sigma_threshold=sigma_threshold,
            kappa_d=effective_kappa,
            temperatures=temps,
            isi_tda=round(isi_tda, 6) if isi_tda is not None else None,
            pairwise=pairwise_dicts,
            timestamp=ts,
            prompt_hash=prompt_hash,
        )

        # Hash forense del reporte completo
        report_dict = result.to_dict()
        report_dict.pop("report_hash", None)
        raw = json.dumps(report_dict, default=str, sort_keys=True, ensure_ascii=False)
        result.report_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()

        return result

    def analyze(
        self,
        prompt:  str,
        isi_tda: Optional[float] = None,
    ) -> MSCEngineResult:
        """
        Pipeline completo: genera samples via backend y analiza consistency.

        Args:
            prompt:  Texto / pregunta a evaluar.
            isi_tda: ISI de la capa TDA (si disponible).

        Returns:
            MSCEngineResult
        """
        samples = self._generate_samples(prompt)
        return self.analyze_from_samples(
            samples,
            temperatures=self.temperatures,
            isi_tda=isi_tda,
            prompt=prompt,
        )


# ══════════════════════════════════════════════════════════════════════════════
# ONE-LINERS DE CONVENIENCIA
# ══════════════════════════════════════════════════════════════════════════════

def msc_v5_quick(
    prompt:      str,
    isi_tda:     Optional[float] = None,
    backend:     Optional[Any]   = None,
    model:       str             = "llama3.2",
    domain:      Optional[str]   = None,
    temperatures: Optional[List[float]] = None,
) -> MSCEngineResult:
    """
    One-liner: pipeline completo con Ollama.

    >>> result = msc_v5_quick("What is the mass of the electron?", isi_tda=0.72)
    >>> print(result.status_string)
    """
    if backend is None:
        backend = OllamaBackend(model=model)
    engine = MSCEngineV5(
        backend=backend,
        domain=domain,
        temperatures=temperatures,
    )
    return engine.analyze(prompt, isi_tda=isi_tda)


def msc_v5_from_texts(
    texts:        List[str],
    temperatures: Optional[List[float]] = None,
    isi_tda:      Optional[float]       = None,
    domain:       Optional[str]         = None,
) -> MSCEngineResult:
    """
    One-liner: analiza textos pre-generados (sin backend LLM).
    Útil para benchmarking y testing.

    >>> texts = ["El electrón tiene masa 9.1e-31 kg.", "La masa es 9.1e-31 kg.", ...]
    >>> result = msc_v5_from_texts(texts, isi_tda=0.65)
    """
    temps = temperatures or DEFAULT_TEMPERATURES[:len(texts)]
    samples = [
        SampleResult(temperature=t, text=txt, success=True)
        for t, txt in zip(temps, texts)
    ]
    engine = MSCEngineV5(domain=domain)
    return engine.analyze_from_samples(samples, temperatures=temps, isi_tda=isi_tda)


# ══════════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════════

def _cli():
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(
        prog="msc_engine_v5",
        description=(
            "Omni-Scanner MSC Engine v5.0 — Oído Absoluto Semántico\n"
            "κD = 0.56 — The Truth Layer Is Operational\n"
            "Registry: EX-2026-18792778 (TAD, Argentina)\n"
            "DOI: https://doi.org/10.5281/zenodo.19052627"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--verify-integrity", action="store_true",
                        help="Verificar SHA-256 del módulo y salir")

    sub = parser.add_subparsers(dest="command")

    # ── analyze (samples pre-generados) ──────────────────────────────────────
    cmd_a = sub.add_parser("analyze", help="Analizar textos pre-generados")
    cmd_a.add_argument("--samples", nargs="+", required=True,
                       help="Paths a archivos .txt (uno por muestra)")
    cmd_a.add_argument("--temps", nargs="+", type=float,
                       default=DEFAULT_TEMPERATURES)
    cmd_a.add_argument("--isi-tda", type=float, default=None)
    cmd_a.add_argument("--domain", type=str, default=None)
    cmd_a.add_argument("--output", type=str, default=None,
                       help="Path para guardar el JSON de auditoría")

    # ── generate (requiere backend) ───────────────────────────────────────────
    cmd_g = sub.add_parser("generate", help="Generar samples y analizar via Ollama")
    cmd_g.add_argument("--prompt", type=str, required=True)
    cmd_g.add_argument("--model", type=str, default="llama3.2")
    cmd_g.add_argument("--isi-tda", type=float, default=None)
    cmd_g.add_argument("--domain", type=str, default=None)
    cmd_g.add_argument("--output", type=str, default=None)

    args = parser.parse_args()

    # ── Verificación de integridad ────────────────────────────────────────────
    if args.verify_integrity:
        ok, current = verify_module_integrity(warn=True)
        print(f"Hash actual: {current}")
        print(f"Estado: {'✅ OK' if ok else '❌ NO COINCIDE'}")
        return

    if args.command == "analyze":
        texts = []
        for path in args.samples:
            p = Path(path)
            if not p.exists():
                print(f"[ERROR] Archivo no encontrado: {path}")
                return
            texts.append(p.read_text(encoding="utf-8"))

        result = msc_v5_from_texts(
            texts,
            temperatures=args.temps,
            isi_tda=args.isi_tda,
            domain=args.domain,
        )

    elif args.command == "generate":
        result = msc_v5_quick(
            prompt=args.prompt,
            isi_tda=args.isi_tda,
            model=args.model,
            domain=args.domain,
        )

    else:
        parser.print_help()
        return

    print(result.to_json())

    if args.output:
        Path(args.output).write_text(result.to_json(), encoding="utf-8")
        print(f"\n[MSC v5] Auditoría guardada en: {args.output}")


if __name__ == "__main__":
    _cli()
