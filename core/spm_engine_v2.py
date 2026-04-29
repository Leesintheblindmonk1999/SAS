"""
core/spm_engine_v2.py — SPM: Semantic Perturbation Module v2.0 (FULL)
═══════════════════════════════════════════════════════════════════════════════

Módulo unificado que contiene:
  - Motor SPM (perturbaciones, embeddings, análisis)
  - Adapter para integración con Manifold Bootstrap
  - Benchmark utilities
  - Funciones de conveniencia

MEJORAS v2.0 (Abril 2026):
  1. Voice change generalizado (no solo 4 patrones)
  2. Reordenación completa de oraciones (sin preservar primera/última)
  3. Pesos iguales (0.25 cada uno) + flag experimental
  4. Integración con el Manifold Bootstrap via SPMAdapter
  5. Benchmark sobre biographies_corpus

LÍMITES DOCUMENTADOS:
  - Un modelo que evade consistentemente ("no sé" de formas variadas) puede pasar SPM como STABLE.
  - Un modelo que alucina consistentemente (misma mentira siempre) también pasa SPM.
  - SPM detecta INESTABILIDAD GENERATIVA, no falsedad factual.
  - Combinar con TDA+NIG para cobertura complementaria.

Registry: EX-2026-18792778 (TAD, Argentina)
Author: Gonzalo Emir Durante — Project Manifold 0.56
License: Durante Invariance License v1.0
"""
from __future__ import annotations

import re
import json
import random
import logging
import datetime
from dataclasses import dataclass, field
from typing import List, Optional, Callable, Dict, Any, Tuple

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity as sklearn_cosine

logger = logging.getLogger(__name__)

# ── Constantes ────────────────────────────────────────────────────────────────

KAPPA_D: float = 0.56

PTYPE_SYNONYM    = "synonym_substitution"
PTYPE_REORDER    = "clause_reordering"
PTYPE_VOICE      = "voice_change"
PTYPE_NOISE      = "semantic_noise"

MIN_WORDS_FOR_PERTURBATION: int = 5

# v2.0: Pesos iguales (experimental, sujeto a calibración empírica)
PERTURBATION_WEIGHTS: Dict[str, float] = {
    PTYPE_SYNONYM:  0.25,
    PTYPE_REORDER:  0.25,
    PTYPE_VOICE:    0.25,
    PTYPE_NOISE:    0.25,
}

# ── Tabla de sinónimos (expandida v2.0) ──────────────────────────────────────

SYNONYM_TABLE: Dict[str, List[str]] = {
    # Verbos de solicitud
    "tell":      ["inform", "describe", "explain", "give"],
    "give":      ["provide", "share", "offer", "present"],
    "provide":   ["give", "supply", "offer", "present"],
    "describe":  ["explain", "outline", "summarize", "detail"],
    "explain":   ["describe", "clarify", "elaborate on", "detail"],
    "show":      ["demonstrate", "present", "reveal", "display"],
    "find":      ["locate", "identify", "discover", "search for"],
    "write":     ["compose", "draft", "produce", "create"],
    "generate":  ["create", "produce", "compose", "write"],
    "list":      ["enumerate", "outline", "itemize", "name"],
    "summarize": ["recap", "outline", "condense", "review"],
    "ask":       ["inquire", "request", "query", "pose"],
    "answer":    ["respond", "reply", "address", "resolve"],

    # Sustantivos comunes
    "bio":          ["biography", "profile", "background", "life story"],
    "biography":    ["bio", "profile", "life story", "background"],
    "profile":      ["biography", "bio", "overview", "background"],
    "information":  ["details", "facts", "data", "knowledge"],
    "details":      ["information", "facts", "specifics", "particulars"],
    "facts":        ["information", "details", "data", "specifics"],
    "overview":     ["summary", "outline", "profile", "introduction"],
    "summary":      ["overview", "recap", "outline", "synopsis"],
    "history":      ["background", "past", "story", "record"],
    "background":   ["history", "past", "context", "story"],
    "story":        ["history", "narrative", "account", "background"],
    "account":      ["description", "report", "narrative", "record"],
    "report":       ["account", "description", "summary", "overview"],
    "life":         ["career", "story", "journey", "existence"],
    "career":       ["professional life", "work history", "trajectory"],
    "work":         ["career", "profession", "field", "expertise"],
    "achievements": ["accomplishments", "contributions", "milestones"],
    "contributions":["achievements", "work", "impact", "additions"],

    # Preposiciones / frases
    "about":    ["regarding", "concerning", "on", "related to"],
    "regarding":["about", "concerning", "on", "related to"],
    "of":       ["about", "on", "regarding", "concerning"],
    "born in":  ["from", "native of", "originating in"],
    "known for":["recognized for", "famous for", "noted for"],
    "famous for":["known for", "recognized for", "celebrated for"],
    "noted for":["known for", "recognized for", "distinguished by"],

    # Adjetivos
    "notable":    ["prominent", "significant", "renowned", "distinguished"],
    "prominent":  ["notable", "significant", "well-known", "distinguished"],
    "renowned":   ["famous", "notable", "celebrated", "well-known"],
    "significant":["important", "notable", "major", "substantial"],
    "important":  ["significant", "notable", "key", "major"],
    "famous":     ["renowned", "well-known", "celebrated", "noted"],
    "well-known": ["famous", "renowned", "recognized", "notable"],
    "recent":     ["latest", "current", "contemporary", "modern"],
    "early":      ["initial", "original", "first", "formative"],
    "main":       ["primary", "chief", "principal", "key"],
    "major":      ["significant", "important", "key", "primary"],
}

NOISE_MARKERS: List[str] = [
    "notably,",
    "it is worth mentioning that",
    "as it happens,",
    "interestingly,",
    "for context,",
    "worth noting,",
    "as a matter of fact,",
    "by the way,",
    "incidentally,",
    "to be precise,",
    "in particular,",
    "specifically,",
    "it should be noted that",
    "as is well known,",
]


# ── Perturbaciones mejoradas v2.0 ────────────────────────────────────────────

def synonym_substitution(
    text: str,
    substitution_rate: float = 0.30,
    seed: int = 42,
) -> str:
    """Sustituye tokens por sinónimos (preserva nombres propios)."""
    if not text or len(text.split()) < MIN_WORDS_FOR_PERTURBATION:
        return text

    rng = random.Random(seed)
    words = text.split()
    result = []

    for i, word in enumerate(words):
        clean = word.lower().strip(".,!?;:\"'()")
        punct = word[len(clean.rstrip(".,!?;:\"'()")):]

        is_sentence_start = (i == 0 or words[i-1][-1:] in ".!?")
        is_proper_noun = word[0].isupper() and not is_sentence_start

        if (not is_proper_noun
                and clean in SYNONYM_TABLE
                and rng.random() < substitution_rate):
            synonym = rng.choice(SYNONYM_TABLE[clean])
            if is_sentence_start:
                synonym = synonym[0].upper() + synonym[1:]
            result.append(synonym + punct)
        else:
            result.append(word)

    return " ".join(result)


def _split_sentences(text: str) -> List[str]:
    """Divide texto en oraciones."""
    sents = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in sents if s.strip()]


def clause_reordering(text: str, seed: int = 42, preserve_first_last: bool = False) -> str:
    """
    Reordena oraciones. v2.0: opción de permutación completa.
    
    Args:
        text: Texto original.
        seed: Semilla.
        preserve_first_last: Si True, mantiene primera y última oración fijas.
                             Si False (default), permutación completa.
    """
    if not text or len(text.split()) < MIN_WORDS_FOR_PERTURBATION:
        return text

    rng = random.Random(seed)
    sentences = _split_sentences(text)

    if len(sentences) <= 1:
        # Texto de una sola oración: reordenar cláusulas por coma
        clauses = [c.strip() for c in text.split(",") if c.strip()]
        if len(clauses) >= 3:
            first = clauses[0]
            rest = clauses[1:]
            rng.shuffle(rest)
            return first + ", " + ", ".join(rest)
        return text

    if preserve_first_last and len(sentences) >= 3:
        # Modo conservador (v1.0)
        middle = sentences[1:-1]
        rng.shuffle(middle)
        return " ".join([sentences[0]] + middle + [sentences[-1]])
    else:
        # v2.0: permutación completa
        rng.shuffle(sentences)
        return " ".join(sentences)


def voice_change(text: str) -> str:
    """
    v2.0: Transformación de voz generalizada.
    
    Estrategia: No intentamos parsear la gramática completa.
    En su lugar, aplicamos transformaciones superficiales que
    cambian la forma sintáctica sin alterar el significado:
    
    1. Interrogación de prompts imperativos
    2. Reformulación de "X is/was Y" a "Y characterizes X"
    3. Inversión de sujeto-objeto en frases simples
    4. Fallback: añadir prefijo modal
    """
    if not text or len(text.split()) < MIN_WORDS_FOR_PERTURBATION:
        return text

    t = text.strip()

    # Caso 1: Prompt imperativo → interrogativo
    # "Tell me about X" → "What can you tell me about X?"
    imperative_patterns = [
        (r"^(tell me|give me|provide|describe|explain|write|list|show me)\s+(.+)$",
         lambda m: f"What can you {m.group(1)} {m.group(2)}?"),
        (r"^(tell|give|provide|describe|explain)\s+(.+)$",
         lambda m: f"Could you {m.group(1)} {m.group(2)}?"),
    ]
    
    for pattern, transform in imperative_patterns:
        m = re.match(pattern, t, re.IGNORECASE)
        if m:
            return transform(m)

    # Caso 2: "X was born in Y" → "Y is the birthplace of X"
    m = re.match(r"^(.+?)\s+was born in\s+(.+?)([.,].*)?$", t, re.IGNORECASE)
    if m:
        subject = m.group(1).strip()
        place = m.group(2).strip()
        rest = m.group(3) or ""
        return f"{place} is the birthplace of {subject}{rest}"

    # Caso 3: "X is known for Y" → "Y is associated with X"
    m = re.match(r"^(.+?)\s+is (?:known|recognized|famous|noted)\s+for\s+(.+?)([.,].*)?$",
                 t, re.IGNORECASE)
    if m:
        subject = m.group(1).strip()
        reason = m.group(2).strip()
        rest = m.group(3) or ""
        return f"{reason} is what {subject} is known for{rest}"

    # Caso 4: "X worked at Y" → "Y employed X"
    m = re.match(r"^(.+?)\s+worked (?:at|for|with)\s+(.+?)([.,].*)?$", t, re.IGNORECASE)
    if m:
        subject = m.group(1).strip()
        org = m.group(2).strip()
        rest = m.group(3) or ""
        return f"{org} employed {subject}{rest}"

    # Caso 5: Fallback universal: añadir prefijo modal
    if t[0].isupper() and not t.endswith("?"):
        return "Please explain: " + t[0].lower() + t[1:]

    return t


def insert_semantic_noise(
    text: str,
    noise_rate: float = 0.20,
    seed: int = 42,
) -> str:
    """Inserta marcadores discursivos neutros."""
    if not text or len(text.split()) < MIN_WORDS_FOR_PERTURBATION:
        return text

    rng = random.Random(seed)
    sentences = _split_sentences(text)

    result = []
    for i, sent in enumerate(sentences):
        if i > 0 and rng.random() < noise_rate:
            marker = rng.choice(NOISE_MARKERS)
            if sent[0].isupper():
                sent_lower = sent[0].lower() + sent[1:]
            else:
                sent_lower = sent
            result.append(f"{marker.capitalize()} {sent_lower}")
        else:
            result.append(sent)

    return " ".join(result)


# ── Embeddings (sin cambios, funciona) ───────────────────────────────────────

def _get_sentence_transformer():
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer("all-MiniLM-L6-v2")
    except ImportError:
        return None

_ST_MODEL = None
_ST_LOADED = False


def get_embedding(texts: List[str]) -> np.ndarray:
    global _ST_MODEL, _ST_LOADED

    if not _ST_LOADED:
        _ST_MODEL = _get_sentence_transformer()
        _ST_LOADED = True

    if _ST_MODEL is not None:
        try:
            return _ST_MODEL.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        except Exception as e:
            logger.warning(f"SPM: sentence-transformers error: {e}")

    # Fallback TF-IDF
    try:
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True, max_features=5000)
        return vectorizer.fit_transform(texts).toarray()
    except Exception as e:
        logger.error(f"SPM: TF-IDF fallback error: {e}")
        return np.random.rand(len(texts), 50)


def cosine_distance(emb_a: np.ndarray, emb_b: np.ndarray) -> float:
    sim = float(sklearn_cosine(emb_a.reshape(1, -1), emb_b.reshape(1, -1))[0][0])
    return round(max(0.0, min(1.0, 1.0 - sim)), 6)


# ── Estructuras de datos ──────────────────────────────────────────────────────

@dataclass
class PerturbationResult:
    perturbation_type:   str
    perturbed_text:      str
    original_response:   str
    perturbed_response:  str
    distance:            float
    weight:              float
    weighted_distance:   float


@dataclass
class SPMResult:
    stability_score:    float
    verdict:            str       # STABLE | UNSTABLE | INSUFFICIENT_DATA | EXPERIMENTAL_STABLE | EXPERIMENTAL_UNSTABLE
    is_unstable:        bool
    perturbations:      List[PerturbationResult] = field(default_factory=list)
    mean_distance:      float = 0.0
    max_distance:       float = 0.0
    min_distance:       float = 0.0
    most_destabilizing: str = ""
    original_text:      str = ""
    embedding_method:   str = ""
    kappa_threshold:    float = KAPPA_D
    n_perturbations:    int = 0
    experimental:       bool = False
    timestamp:          str = field(default_factory=lambda: datetime.datetime.utcnow().isoformat() + "Z")
    author:             str = "Gonzalo Emir Durante"
    registry:           str = "EX-2026-18792778"

    def to_dict(self) -> dict:
        return {
            "original_text":      self.original_text[:200],
            "stability_score":    round(self.stability_score, 4),
            "verdict":            self.verdict,
            "is_unstable":        self.is_unstable,
            "mean_distance":      round(self.mean_distance, 4),
            "max_distance":       round(self.max_distance, 4),
            "min_distance":       round(self.min_distance, 4),
            "most_destabilizing": self.most_destabilizing,
            "kappa_threshold":    self.kappa_threshold,
            "n_perturbations":    self.n_perturbations,
            "embedding_method":   self.embedding_method,
            "experimental":       self.experimental,
            "perturbations":      [{"type": p.perturbation_type, "distance": p.distance} for p in self.perturbations],
            "timestamp":          self.timestamp,
            "author":             self.author,
            "registry":           self.registry,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


# ── Motor SPM v2.0 ───────────────────────────────────────────────────────────

class SPMEngine:
    def __init__(
        self,
        kappa_d:            float = KAPPA_D,
        perturbation_types: Optional[List[str]] = None,
        synonym_rate:       float = 0.30,
        noise_rate:         float = 0.20,
        seed:               int = 42,
        experimental:       bool = True,
    ):
        self.kappa_d = kappa_d
        self.perturbation_types = perturbation_types or [PTYPE_SYNONYM, PTYPE_REORDER, PTYPE_VOICE, PTYPE_NOISE]
        self.synonym_rate = synonym_rate
        self.noise_rate = noise_rate
        self.seed = seed
        self.experimental = experimental

        global _ST_MODEL, _ST_LOADED
        if not _ST_LOADED:
            _ST_MODEL = _get_sentence_transformer()
            _ST_LOADED = True
        self._embedding_method = "sentence-transformers" if _ST_MODEL else "tfidf"
        
        logger.info(f"SPM v2.0 | embedding={self._embedding_method} | experimental={experimental}")

    def generate_perturbations(self, text: str) -> List[Dict[str, str]]:
        perturbations = []

        if PTYPE_SYNONYM in self.perturbation_types:
            perturbations.append({"type": PTYPE_SYNONYM, "text": synonym_substitution(text, self.synonym_rate, self.seed)})

        if PTYPE_REORDER in self.perturbation_types:
            perturbations.append({"type": PTYPE_REORDER, "text": clause_reordering(text, self.seed, preserve_first_last=False)})

        if PTYPE_VOICE in self.perturbation_types:
            perturbations.append({"type": PTYPE_VOICE, "text": voice_change(text)})

        if PTYPE_NOISE in self.perturbation_types:
            perturbations.append({"type": PTYPE_NOISE, "text": insert_semantic_noise(text, self.noise_rate, self.seed)})

        return perturbations

    def analyze(self, original_text: str, model_function: Callable[[str], str]) -> SPMResult:
        if not original_text or len(original_text.split()) < 2:
            return SPMResult(stability_score=1.0, verdict="INSUFFICIENT_DATA", is_unstable=False, original_text=original_text, experimental=self.experimental)

        try:
            original_response = model_function(original_text)
        except Exception as e:
            logger.error(f"SPM: model error: {e}")
            return SPMResult(stability_score=1.0, verdict="INSUFFICIENT_DATA", is_unstable=False, original_text=original_text, experimental=self.experimental)

        if not original_response or len(original_response.split()) < 3:
            return SPMResult(stability_score=1.0, verdict="INSUFFICIENT_DATA", is_unstable=False, original_text=original_text, experimental=self.experimental)

        perturbation_specs = self.generate_perturbations(original_text)
        responses: List[Tuple[str, str, str]] = []

        for spec in perturbation_specs:
            try:
                p_response = model_function(spec["text"])
                if p_response and len(p_response.split()) >= 3:
                    responses.append((spec["type"], spec["text"], p_response))
            except Exception as e:
                logger.warning(f"SPM: error en {spec['type']}: {e}")

        if not responses:
            return SPMResult(stability_score=1.0, verdict="INSUFFICIENT_DATA", is_unstable=False, original_text=original_text, experimental=self.experimental)

        all_texts = [original_response] + [r[2] for r in responses]
        embeddings = get_embedding(all_texts)
        emb_original = embeddings[0]

        perturbation_results = []
        for i, (ptype, ptext, p_response) in enumerate(responses):
            dist = cosine_distance(emb_original, embeddings[i + 1])
            weight = PERTURBATION_WEIGHTS.get(ptype, 0.25)
            perturbation_results.append(PerturbationResult(
                perturbation_type=ptype,
                perturbed_text=ptext,
                original_response=original_response,
                perturbed_response=p_response,
                distance=dist,
                weight=weight,
                weighted_distance=dist * weight,
            ))

        total_weight = sum(p.weight for p in perturbation_results)
        weighted_mean_dist = sum(p.weighted_distance for p in perturbation_results) / total_weight
        stability_score = round(max(0.0, min(1.0, 1.0 - weighted_mean_dist)), 6)

        distances = [p.distance for p in perturbation_results]
        base_verdict = "STABLE" if stability_score >= self.kappa_d else "UNSTABLE"
        
        if self.experimental:
            verdict = f"EXPERIMENTAL_{base_verdict}"
        else:
            verdict = base_verdict

        return SPMResult(
            stability_score=stability_score,
            verdict=verdict,
            is_unstable=(stability_score < self.kappa_d),
            perturbations=perturbation_results,
            mean_distance=round(float(np.mean(distances)), 6),
            max_distance=round(float(np.max(distances)), 6),
            min_distance=round(float(np.min(distances)), 6),
            most_destabilizing=max(perturbation_results, key=lambda p: p.distance).perturbation_type,
            original_text=original_text,
            embedding_method=self._embedding_method,
            kappa_threshold=self.kappa_d,
            n_perturbations=len(perturbation_results),
            experimental=self.experimental,
        )


# ── SPMAdapter (integración con Manifold Bootstrap) ──────────────────────────

class SPMAdapter:
    """
    Adaptador de SPM para el Manifold Bootstrap v5.3.
    
    Modos de operación:
      - modo="warning_only": SPM no modifica ISI, solo agrega advertencia
      - modo="integrated": SPM contribuye a ISI_FINAL
      - modo="experimental": SPM corre pero no afecta veredicto (default)
    """
    
    def __init__(
        self,
        mode: str = "experimental",
        kappa_d: float = KAPPA_D,
        spm_weight: float = 0.30,
    ):
        self.mode = mode
        self.kappa_d = kappa_d
        self.spm_weight = spm_weight
        self.engine = SPMEngine(kappa_d=kappa_d, experimental=(mode == "experimental"))
        
        logger.info(f"SPMAdapter initialized | mode={mode} | weight={spm_weight}")
    
    def run(
        self,
        text: str,
        model_function: Callable[[str], str],
        isi_hard: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Ejecuta SPM y opcionalmente combina con ISI_HARD.
        
        Args:
            text: Prompt original
            model_function: Función LLM
            isi_hard: Valor de ISI_HARD (TDA + NIG) si está disponible
        
        Returns:
            Dict con resultados y veredicto integrado
        """
        spm_result = self.engine.analyze(text, model_function)
        
        output = {
            "spm": spm_result.to_dict(),
            "mode": self.mode,
            "integrated_verdict": None,
            "recommendation": None,
        }
        
        # Interpretación
        if "UNSTABLE" in spm_result.verdict:
            output["recommendation"] = (
                "SPM detecta inestabilidad generativa. "
                "La respuesta del modelo varía significativamente ante perturbaciones menores del prompt. "
                "Esto puede indicar alucinación narrativa, falta de anclaje factual, o ambigüedad del prompt. "
                "Se recomienda verificación externa."
            )
        elif "STABLE" in spm_result.verdict:
            output["recommendation"] = (
                "SPM detecta estabilidad generativa. "
                "El modelo responde de manera consistente ante variaciones del prompt. "
                "Esto NO garantiza veracidad factual — solo indica consistencia en la generación."
            )
        else:
            output["recommendation"] = "SPM no pudo completar el análisis (datos insuficientes)."
        
        # Integración con ISI_HARD
        if self.mode == "integrated" and isi_hard is not None:
            instability_signal = 1 - spm_result.stability_score
            isi_spm = max(isi_hard, instability_signal)
            output["integrated_verdict"] = "RUPTURE" if isi_spm < self.kappa_d else "COHERENT"
            output["isi_hard_input"] = isi_hard
            output["instability_signal"] = instability_signal
            output["isi_integrated"] = isi_spm
        
        return output


# ── Funciones de conveniencia ─────────────────────────────────────────────────

def detect_with_spm(
    text: str,
    model_function: Callable[[str], str],
    kappa_d: float = KAPPA_D,
    experimental: bool = True
) -> dict:
    """Función rápida para análisis SPM standalone."""
    engine = SPMEngine(kappa_d=kappa_d, experimental=experimental)
    result = engine.analyze(text, model_function)
    return result.to_dict()


def quick_spm_check(text: str, model_function: Callable[[str], str]) -> Dict[str, Any]:
    """Chequeo SPM con adapter en modo experimental."""
    adapter = SPMAdapter(mode="experimental")
    return adapter.run(text, model_function)


# ── Benchmark utilities ───────────────────────────────────────────────────────

@dataclass
class BenchmarkResult:
    name: str
    is_invented: bool
    spm_verdict: str
    spm_score: float
    spm_correct: bool
    decm_known_result: str


def run_benchmark(
    corpus_path: str,
    model_function: Callable[[str], str],
    experimental: bool = False
) -> Tuple[List[BenchmarkResult], Dict]:
    """
    Ejecuta benchmark de SPM sobre el corpus de biografías.
    
    Args:
        corpus_path: Ruta al JSON con estructura:
            [{"name": "...", "is_invented": true/false, "decm_verdict": "THERMAL_COLLAPSE/STABLE"}]
        model_function: Función LLM que responde a "Tell me a bio of {name}"
        experimental: Si True, usa modo experimental (verdict con prefijo)
    
    Returns:
        Tuple con (resultados, estadísticas)
    """
    with open(corpus_path, "r", encoding="utf-8") as f:
        corpus = json.load(f)
    
    results = []
    
    for i, item in enumerate(corpus):
        name = item["name"]
        is_invented = item.get("is_invented", False)
        decm_result = item.get("decm_verdict", "UNKNOWN")
        
        prompt = f"Tell me a bio of {name}"
        spm_output = detect_with_spm(prompt, model_function, experimental=experimental)
        
        spm_verdict = spm_output["verdict"]
        # Limpiar prefijo EXPERIMENTAL_ para la evaluación
        clean_verdict = spm_verdict.replace("EXPERIMENTAL_", "")
        spm_score = spm_output["stability_score"]
        
        # Correcto si: inventado → UNSTABLE, real → STABLE
        spm_correct = (is_invented and clean_verdict == "UNSTABLE") or (not is_invented and clean_verdict == "STABLE")
        
        results.append(BenchmarkResult(
            name=name,
            is_invented=is_invented,
            spm_verdict=spm_verdict,
            spm_score=spm_score,
            spm_correct=spm_correct,
            decm_known_result=decm_result,
        ))
        
        if (i + 1) % 20 == 0:
            logger.info(f"Benchmark progress: {i+1}/{len(corpus)}")
    
    # Estadísticas
    total = len(results)
    invented = [r for r in results if r.is_invented]
    real = [r for r in results if not r.is_invented]
    
    stats = {
        "total": total,
        "invented_count": len(invented),
        "real_count": len(real),
        "spm_accuracy_overall": sum(1 for r in results if r.spm_correct) / total * 100 if total else 0,
        "spm_accuracy_invented": sum(1 for r in invented if r.spm_correct) / len(invented) * 100 if invented else 0,
        "spm_accuracy_real": sum(1 for r in real if r.spm_correct) / len(real) * 100 if real else 0,
        "spm_detection_rate_invented": sum(1 for r in invented if "UNSTABLE" in r.spm_verdict) / len(invented) * 100 if invented else 0,
        "spm_false_positive_rate": sum(1 for r in real if "UNSTABLE" in r.spm_verdict) / len(real) * 100 if real else 0,
    }
    
    return results, stats


def print_benchmark_report(results: List[BenchmarkResult], stats: Dict):
    """Imprime reporte formateado del benchmark."""
    print("\n" + "=" * 70)
    print("SPM BENCHMARK REPORT — biographies_corpus")
    print("=" * 70)
    print(f"Total samples: {stats['total']}")
    print(f"Invented names: {stats['invented_count']}")
    print(f"Real names: {stats['real_count']}")
    print()
    print("--- SPM Performance ---")
    print(f"Overall accuracy: {stats['spm_accuracy_overall']:.1f}%")
    print(f"Accuracy on invented (should be UNSTABLE): {stats['spm_accuracy_invented']:.1f}%")
    print(f"Accuracy on real (should be STABLE): {stats['spm_accuracy_real']:.1f}%")
    print(f"Detection rate (invented → UNSTABLE): {stats['spm_detection_rate_invented']:.1f}%")
    print(f"False positive rate (real → UNSTABLE): {stats['spm_false_positive_rate']:.1f}%")
    print()
    print("--- Comparison with DECM (original benchmark) ---")
    print("DECM: 100% precision, 10% recall on evasiones")
    print(f"SPM: {stats['spm_detection_rate_invented']:.1f}% detection rate, {stats['spm_false_positive_rate']:.1f}% false positive rate")
    
    # Mostrar falsos positivos si los hay
    false_positives = [r for r in results if not r.is_invented and "UNSTABLE" in r.spm_verdict]
    if false_positives:
        print(f"\n⚠️ False positives ({len(false_positives)}):")
        for fp in false_positives[:10]:
            print(f"  - {fp.name} (score={fp.spm_score:.4f})")
    
    # Mostrar no detectados
    missed = [r for r in results if r.is_invented and "STABLE" in r.spm_verdict]
    if missed:
        print(f"\n⚠️ Missed detections ({len(missed)}):")
        for m in missed[:10]:
            print(f"  - {m.name} (score={m.spm_score:.4f}, verdict={m.spm_verdict})")


# ── Demo ──────────────────────────────────────────────────────────────────────

def _demo_with_mock_model():
    """Demostración con modelo simulado."""
    def stable_model(prompt: str) -> str:
        return ("Marie Curie was a pioneering physicist and chemist born in Warsaw in 1867. "
                "She conducted groundbreaking research on radioactivity and was the first woman "
                "to win a Nobel Prize, receiving awards in both Physics (1903) and Chemistry (1911).")
    
    def unstable_model(prompt: str) -> str:
        responses = [
            "I don't have information about Harry Cave.",
            "Harry Cave could refer to several different individuals.",
            "I cannot provide specific biographical information about this person.",
        ]
        r = random.Random(hash(prompt) % 1000)
        return r.choice(responses)
    
    print("=" * 70)
    print("SPM v2.0 DEMO")
    print("=" * 70)
    
    # Caso estable
    result = detect_with_spm("Tell me a bio of Marie Curie", stable_model, experimental=True)
    print(f"\nMarie Curie (real): {result['verdict']} | score={result['stability_score']:.4f}")
    
    # Caso inestable
    result = detect_with_spm("Tell me a bio of Harry Cave", unstable_model, experimental=True)
    print(f"Harry Cave (inventado): {result['verdict']} | score={result['stability_score']:.4f}")
    
    # Usar adapter
    adapter = SPMAdapter(mode="experimental")
    output = adapter.run("Tell me a bio of Harry Cave", unstable_model)
    print(f"\nAdapter output: {output['recommendation']}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    _demo_with_mock_model()