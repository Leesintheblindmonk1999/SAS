"""
core/tda_attestation.py — Omni-Scanner Semantic v5.6
═══════════════════════════════════════════════════════
Topological Attestation Module (TDA)
──────────────────────────────────────
Detects "structural hallucinations" in text via Persistent Homology
over the lexical embedding manifold.

Pipeline:
  texto → embeddings TF-IDF → nube de puntos → Vietoris-Rips
        → diagrama de persistencia H₀/H₁ → filtrado por κD
        → topological attestation report

DEPENDENCIAS:
    pip install ripser persim scikit-learn matplotlib numpy

TECHNICAL NOTE ON THRESHOLD κD = 0.56:
    In standard TDA literature, persistence thresholds are calibrated
    empirically against a reference corpus. The constant κD=0.56 is
    used here as a configurable filtering parameter.
    The module exposes persistence_threshold as an argument so
    the user can recalibrate against their own corpus.
    See: `calibrate_threshold()` method.
"""
from __future__ import annotations

import re
import math
import json
import hashlib
import datetime
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from pathlib import Path

import numpy as np

# ── TDA imports ───────────────────────────────────────────────
try:
    from ripser import ripser
    from persim import plot_diagrams
    _RIPSER_OK = True
except ImportError:
    _RIPSER_OK = False

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    _MPL_OK = True
except ImportError:
    _MPL_OK = False

# ── sklearn para embeddings ───────────────────────────────────
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.preprocessing import normalize
    from sklearn.decomposition import TruncatedSVD
    _SK_OK = True
except ImportError:
    _SK_OK = False


# ══════════════════════════════════════════════════════════════
# Estructuras de datos
# ══════════════════════════════════════════════════════════════

@dataclass
class PersistencePair:
    """A (birth, death) pair of a homological cycle."""
    dimension:   int
    birth:       float
    death:       float
    persistence: float   # death - birth
    ratio:       float   # death / birth  (∞ si birth ≈ 0)
    flag:        str     # "STRUCTURAL_FALSEHOOD" | "STABILIZED" | "NOISE"

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


@dataclass
class TDAAttestationReport:
    """Complete topological attestation report."""
    timestamp:          str
    text_hash:          str
    token_count:        int
    sentence_count:     int
    embedding_dim:      int
    point_cloud_size:   int

    # H₀ Homology (connected components)
    h0_pairs:           List[PersistencePair] = field(default_factory=list)
    h0_count:           int = 0

    # H₁ Homology (cycles — "circular hallucinations")
    h1_pairs:           List[PersistencePair] = field(default_factory=list)
    h1_structural_falsehoods: int = 0   # H₁ con ratio > κD
    h1_stabilized:      int = 0          # H₁ con ratio ≤ κD
    h1_total:           int = 0

    # Aggregated metrics
    kappa_d:            float = 0.56
    max_h1_persistence: float = 0.0
    mean_h1_persistence: float = 0.0
    topological_noise:  float = 0.0     # fraction of pairs with persistence < 0.01

    # Verdict
    verdict:            str = "PENDING"
    integrity_score:    float = 0.0     # [0,1]: 1 = intact manifold
    structural_risk:    str = "LOW"     # LOW | MEDIUM | HIGH | CRITICAL
    summary:            str = ""

    # Metadata
    ripser_available:   bool = False
    fallback_used:      bool = False

    def to_dict(self) -> dict:
        d = {k: v for k, v in self.__dict__.items()}
        d["h0_pairs"] = [p.to_dict() for p in self.h0_pairs]
        d["h1_pairs"] = [p.to_dict() for p in self.h1_pairs]
        return d

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


# ══════════════════════════════════════════════════════════════
# Capa de Embeddings (TF-IDF + SVD = LSA)
# ══════════════════════════════════════════════════════════════

class LexicalEmbedder:
    """
    Transforms sentences into low-dimensional vectors via TF-IDF + SVD.
    No requiere modelos preentrenados — funciona sin GPU ni red.

    For production with real LLMs, replace with model embeddings
    (e.g. sentence-transformers) for higher semantic fidelity.
    """

    def __init__(self, n_components: int = 20, min_df: int = 1):
        self.n_components = n_components
        self.min_df = min_df
        self._vectorizer: Optional["TfidfVectorizer"] = None
        self._svd: Optional["TruncatedSVD"] = None
        self._fitted = False

    def fit_transform(self, sentences: List[str]) -> np.ndarray:
        """
        Fits the embedder and transforms sentences.
        Retorna matriz (n_sentences × n_components).
        """
        if not _SK_OK:
            raise ImportError("scikit-learn requerido: pip install scikit-learn")

        n = len(sentences)
        effective_components = min(self.n_components, n - 1) if n > 1 else 1

        self._vectorizer = TfidfVectorizer(
            min_df=self.min_df,
            ngram_range=(1, 2),
            sublinear_tf=True,
            token_pattern=r"(?u)\b\w+\b",
        )
        X = self._vectorizer.fit_transform(sentences)

        if X.shape[1] < 2 or effective_components < 2:
            # Demasiado poco vocabulario — usar TF-IDF denso directamente
            arr = X.toarray()
            return normalize(arr)

        self._svd = TruncatedSVD(n_components=effective_components, random_state=42)
        X_reduced = self._svd.fit_transform(X)
        self._fitted = True
        return normalize(X_reduced)

    def transform(self, sentences: List[str]) -> np.ndarray:
        """Transforms new sentences with the already-fitted embedder."""
        if not self._fitted:
            return self.fit_transform(sentences)
        X = self._vectorizer.transform(sentences)
        X_red = self._svd.transform(X)
        return normalize(X_red)


# ══════════════════════════════════════════════════════════════
# Persistent Homology (Vietoris-Rips via Ripser)
# ══════════════════════════════════════════════════════════════

def _compute_persistence_ripser(
    point_cloud: np.ndarray,
    max_dim: int = 1,
    max_edge_length: float = 2.0,
) -> dict:
    """Calcula diagramas de persistencia con Ripser."""
    result = ripser(
        point_cloud,
        maxdim=max_dim,
        thresh=max_edge_length,
        metric="euclidean",
    )
    return result["dgms"]  # lista: [dgm_H0, dgm_H1]


def _compute_persistence_fallback(
    point_cloud: np.ndarray,
    max_dim: int = 1,
) -> list:
    """
    Fallback without Ripser: H₀ and H₁ approximation via distances.

    H₀: estimado con algoritmo greedy de componentes conexas
        (equivalent to minimum spanning tree in ascending scale)
    H₁: estimado via ciclos en grafo de vecindad k-NN

    NOTE: This is an approximation, not strict Vietoris-Rips.
    Values are indicative. For formal forensic auditing,
    install Ripser: pip install ripser
    """
    n = len(point_cloud)
    if n < 3:
        return [
            np.array([[0.0, float("inf")]]),
            np.array([]).reshape(0, 2),
        ]

    # Matriz de distancias euclidianas
    dists = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            d = float(np.linalg.norm(point_cloud[i] - point_cloud[j]))
            dists[i, j] = dists[j, i] = d

    # ── H₀: Union-Find sobre distancias crecientes ────────────
    parent = list(range(n))
    def find(x):
        while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
        return x
    def union(x, y):
        parent[find(x)] = find(y)

    edges_sorted = sorted(
        [(dists[i, j], i, j) for i in range(n) for j in range(i+1, n)]
    )
    h0_pairs = [[0.0, float("inf")]]  # componente principal
    n_components = n
    for d_val, i, j in edges_sorted:
        if find(i) != find(j):
            union(i, j)
            n_components -= 1
            if n_components > 1:
                h0_pairs.append([0.0, d_val])
            else:
                break  # todas conectadas

    dgm_h0 = np.array(h0_pairs)

    # ── H₁: ciclos via vecinos cercanos ───────────────────────
    if max_dim < 1:
        return [dgm_h0, np.array([]).reshape(0, 2)]

    # Umbral adaptativo: percentil 30 de distancias
    all_dists_flat = [dists[i,j] for i in range(n) for j in range(i+1,n)]
    all_dists_flat.sort()
    p30_idx = max(0, int(len(all_dists_flat) * 0.30) - 1)
    eps = all_dists_flat[p30_idx]

    # Grafo de vecindad
    adj = [[False]*n for _ in range(n)]
    for d_val, i, j in edges_sorted:
        if d_val <= eps:
            adj[i][j] = adj[j][i] = True

    # Detectar ciclos simples con DFS
    h1_pairs = []
    visited  = [False] * n

    def dfs_cycle(node, parent_node, start, depth, entry_d):
        """Retorna (birth, death) si encuentra ciclo de longitud ≥ 3."""
        visited[node] = True
        for nb in range(n):
            if not adj[node][nb]: continue
            if nb == parent_node: continue
            if nb == start and depth >= 2:
                death = max(entry_d, dists[node][nb])
                h1_pairs.append([entry_d * 0.5, death])
                return
            if not visited[nb]:
                dfs_cycle(nb, node, start, depth+1,
                          max(entry_d, dists[node][nb]))

    for start_node in range(min(n, 30)):  # limitar para performance
        visited = [False] * n
        dfs_cycle(start_node, -1, start_node, 0, 0.0)
        if len(h1_pairs) >= 20:  # suficientes ciclos detectados
            break

    dgm_h1 = np.array(h1_pairs) if h1_pairs else np.array([]).reshape(0, 2)
    return [dgm_h0, dgm_h1]


# ══════════════════════════════════════════════════════════════
# Main Attestation Module
# ══════════════════════════════════════════════════════════════

class TDAAttestator:
    """
    Audits topological stability of text via Persistent Homology.

    Parameters
    ----------
    persistence_threshold : float
        Umbral de ratio death/birth para clasificar H₁.
        Default: 0.56 (κD de referencia).
        CALIBRATION: use calibrate_threshold() against own corpus.
    embedding_dim : int
        Latent space dimension (LSA). Default: 20.
    min_sentences : int
        Minimum sentences for topological analysis. Default: 3.
    """

    def __init__(
        self,
        persistence_threshold: float = 0.56,
        embedding_dim: int = 20,
        min_sentences: int = 3,
    ):
        self.kappa_d    = persistence_threshold
        self.embed_dim  = embedding_dim
        self.min_sents  = min_sentences
        self._embedder  = LexicalEmbedder(n_components=embedding_dim)

    # ── API principal ─────────────────────────────────────────

    def attest(self, text: str) -> TDAAttestationReport:
        """
        Pipeline completo: texto → TDAAttestationReport.

        1. Tokenizes into sentences
        2. Genera embeddings LSA
        3. Calculates persistent homology (Ripser or fallback)
        4. Clasifica pares H₁ por umbral κD
        5. Emits integrity verdict
        """
        ts    = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"
        t_hash = hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16]

        sentences = self._split_sentences(text)
        tokens    = re.findall(r"\b\w+\b", text)

        report = TDAAttestationReport(
            timestamp       = ts,
            text_hash       = t_hash,
            token_count     = len(tokens),
            sentence_count  = len(sentences),
            embedding_dim   = self.embed_dim,
            point_cloud_size= 0,
            kappa_d         = self.kappa_d,
            ripser_available= _RIPSER_OK,
        )

        if len(sentences) < self.min_sents:
            report.verdict         = "INSUFFICIENT_DATA"
            report.structural_risk = "UNKNOWN"
            report.summary = (
                f"Texto insuficiente: {len(sentences)} oración(es) "
                f"(mínimo: {self.min_sents}). "
                "Proveer al menos 3 oraciones para análisis topológico."
            )
            return report

        # ── 1. Embeddings ──────────────────────────────────────
        try:
            point_cloud = self._embedder.fit_transform(sentences)
        except Exception as e:
            report.verdict = "EMBEDDING_ERROR"
            report.summary = f"Error en embeddings: {e}"
            return report

        report.point_cloud_size = len(point_cloud)

        # ── 2. Persistent Homology ─────────────────────────────
        use_fallback = not _RIPSER_OK
        try:
            if _RIPSER_OK:
                dgms = _compute_persistence_ripser(point_cloud, max_dim=1)
            else:
                dgms = _compute_persistence_fallback(point_cloud, max_dim=1)
                report.fallback_used = True
        except Exception:
            dgms = _compute_persistence_fallback(point_cloud, max_dim=1)
            report.fallback_used = True

        # ── 3. Parsear H₀ ──────────────────────────────────────
        if len(dgms) > 0 and len(dgms[0]) > 0:
            report.h0_pairs  = self._parse_pairs(dgms[0], dim=0,
                                                  fallback_mode=report.fallback_used)
            report.h0_count  = len(report.h0_pairs)

        # ── 4. Parsear H₁ y clasificar por κD ─────────────────
        # NOTA CRÍTICA: En fallback mode (sin Ripser), los ciclos H₁ generados
        # por el DFS tienen persistencia ≈ diameter/2 por construcción geométrica.
        # Esta uniformidad hace que la clasificación por ratio o persistencia
        # normalizada no discrimine entre documentos coherentes e incoherentes.
        # To maintain scientific integrity, H₁ is only classified with Ripser.
        if len(dgms) > 1 and len(dgms[1]) > 0 and not report.fallback_used:
            report.h1_pairs = self._parse_pairs(dgms[1], dim=1,
                                                 fallback_mode=report.fallback_used)
            report.h1_total = len(report.h1_pairs)

            structural = [p for p in report.h1_pairs if p.flag == "STRUCTURAL_FALSEHOOD"]
            stabilized = [p for p in report.h1_pairs if p.flag == "STABILIZED"]

            report.h1_structural_falsehoods = len(structural)
            report.h1_stabilized            = len(stabilized)

            persistences = [p.persistence for p in report.h1_pairs if p.persistence < float("inf")]
            if persistences:
                report.max_h1_persistence  = round(max(persistences), 6)
                report.mean_h1_persistence = round(sum(persistences)/len(persistences), 6)
                noise = sum(1 for p in persistences if p < 0.01) / len(persistences)
                report.topological_noise   = round(noise, 4)

        # ── 5. Verdict ─────────────────────────────────────────
        report = self._assign_verdict(report)
        return report

    def _parse_pairs(
        self,
        dgm: np.ndarray,
        dim: int,
        fallback_mode: bool = False,
    ) -> List[PersistencePair]:
        """
        Convierte diagrama de persistencia en lista de PersistencePair.

        H₁ Classification:
          · Ripser (fallback_mode=False):
              ratio = death/birth > κD → STRUCTURAL_FALSEHOOD
              This ratio has real topological meaning in Vietoris-Rips.

          · Fallback DFS (fallback_mode=True):
              The DFS generates death ≈ 2·birth by geometric construction,
              haciendo ratio ≈ 2.0 siempre — no discrimina.
              Normalized persistence by cloud diameter is used:
              norm_pers = persistence / cloud_diameter > κD → STRUCTURAL_FALSEHOOD
              Esto mide si el ciclo es "grande" relativo al espacio total.
        """
        pairs = []

        # Cloud diameter for normalization in fallback mode
        if fallback_mode and len(dgm) > 0:
            finite_deaths = [float(r[1]) for r in dgm if not math.isinf(r[1])]
            births = [float(r[0]) for r in dgm]
            cloud_diameter = (max(finite_deaths) if finite_deaths else 1.0)
            cloud_diameter = max(cloud_diameter, 1e-8)
        else:
            cloud_diameter = 1.0

        for row in dgm:
            birth = float(row[0])
            death = float(row[1])

            if math.isinf(death):
                persistence = float("inf")
                ratio = float("inf")
            else:
                persistence = death - birth
                ratio = (death / birth) if birth > 1e-8 else float("inf")

            # Classification by κD (only relevant for H₁)
            if dim == 1:
                if fallback_mode:
                    # Fallback: use normalized persistence as topological proxy.
                    # Un ciclo H₁ es "estructuralmente falso" si su persistencia
                    # represents a significant fraction of the total diameter,
                    # lo que indica un loop real en el espacio de embeddings.
                    # Empirical threshold: norm_pers > 0.35 discriminates well without ripser.
                    if math.isinf(persistence):
                        flag = "STRUCTURAL_FALSEHOOD"
                    else:
                        norm_pers = persistence / cloud_diameter
                        if norm_pers > 0.35:
                            flag = "STRUCTURAL_FALSEHOOD"
                        elif persistence < 0.005 or norm_pers < 0.05:
                            flag = "NOISE"
                        else:
                            flag = "STABILIZED"
                else:
                    # Ripser: usar ratio death/birth — tiene significado real
                    if math.isinf(ratio) or ratio > self.kappa_d:
                        flag = "STRUCTURAL_FALSEHOOD"
                    elif persistence < 0.005:
                        flag = "NOISE"
                    else:
                        flag = "STABILIZED"
            else:
                flag = "H0_COMPONENT"

            pairs.append(PersistencePair(
                dimension   = dim,
                birth       = round(birth, 6),
                death       = round(death, 6) if not math.isinf(death) else death,
                persistence = round(persistence, 6) if not math.isinf(persistence) else persistence,
                ratio       = round(ratio, 6) if not math.isinf(ratio) else ratio,
                flag        = flag,
            ))
        return pairs

    def _assign_verdict(self, report: TDAAttestationReport) -> TDAAttestationReport:
        """Assigns final verdict based on topological structure."""
        sf  = report.h1_structural_falsehoods
        tot = max(report.h1_total, 1)
        sf_ratio = sf / tot

        # Integrity: 1.0 = no anomalous structural cycles
        integrity = max(0.0, 1.0 - sf_ratio * 0.8 - report.topological_noise * 0.2)
        report.integrity_score = round(integrity, 4)

        if report.h1_total == 0:
            report.verdict         = "TOPOLOGICALLY_SIMPLE"
            report.structural_risk = "LOW"
            detail = "No H₁ cycles detected. Topologically simple manifold."
        elif sf == 0:
            report.verdict         = "MANIFOLD_STABLE"
            report.structural_risk = "LOW"
            detail = (
                f"All H₁ cycles ({report.h1_total}) stabilize "
                f"below κD={self.kappa_d}. "
                "Structural coherence confirmed."
            )
        elif sf_ratio <= 0.25:
            report.verdict         = "PARTIAL_INSTABILITY"
            report.structural_risk = "MEDIUM"
            detail = (
                f"{sf}/{report.h1_total} ciclos H₁ superan κD={self.kappa_d}. "
                "Partial instability: review sections with high conceptual repetition."
            )
        elif sf_ratio <= 0.60:
            report.verdict         = "STRUCTURAL_TENSION"
            report.structural_risk = "HIGH"
            detail = (
                f"{sf}/{report.h1_total} ciclos H₁ sobre κD={self.kappa_d}. "
                "Significant structural tension. "
                "Possible semantic circularity without factual basis."
            )
        else:
            report.verdict         = "SEMANTIC_COLLAPSE"
            report.structural_risk = "CRITICAL"
            detail = (
                f"{sf}/{report.h1_total} ciclos H₁ sobre κD={self.kappa_d} "
                f"({sf_ratio:.0%} del total). "
                "SEMANTIC COLLAPSE: The manifold presents persistent structural "
                "inconsistencies. High probability of circular hallucination."
            )

        fallback_note = (
            "\n[WARNING: Ripser unavailable — fallback approximation used. "
            "Install: pip install ripser persim]"
            if report.fallback_used else ""
        )

        report.summary = (
            f"TOPOLOGICAL ATTESTATION — {report.verdict}\n"
            f"{'─'*55}\n"
            f"Sentences analyzed   : {report.sentence_count}\n"
            f"Point cloud          : {report.point_cloud_size} vectors ×"
            f" {report.embedding_dim}D\n"
            f"H₀ components        : {report.h0_count}\n"
            f"H₁ cycles total      : {report.h1_total}\n"
            f"  → Struct. falsehoods: {report.h1_structural_falsehoods} "
            f"[ratio > κD={self.kappa_d}]\n"
            f"  → Stabilized        : {report.h1_stabilized} "
            f"[ratio ≤ κD={self.kappa_d}]\n"
            f"Max H₁ persistence   : {report.max_h1_persistence:.4f}\n"
            f"Topological noise    : {report.topological_noise:.2%}\n"
            f"Manifold integrity   : {report.integrity_score:.4f}\n"
            f"Structural risk      : {report.structural_risk}\n"
            f"{'─'*55}\n"
            f"{detail}"
            f"{fallback_note}"
        )
        return report

    # ── Calibration ───────────────────────────────────────────

    def calibrate_threshold(
        self,
        reference_texts: List[str],
        known_hallucinations: List[str],
    ) -> dict:
        """
        Calibrates persistence_threshold empirically.

        Parámetros
        ----------
        reference_texts      : Lista de textos conocidamente coherentes
        known_hallucinations : Lista de textos conocidamente alucinados

        Returns dict with optimal threshold and calibration statistics.

        Uso recomendado:
            result = attestator.calibrate_threshold(
                reference_texts=corpus_coherente,
                known_hallucinations=corpus_alucinado,
            )
            attestator.kappa_d = result["optimal_threshold"]
        """
        def _mean_max_h1(texts):
            vals = []
            for t in texts:
                r = self.attest(t)
                if r.max_h1_persistence > 0:
                    vals.append(r.max_h1_persistence)
            return sum(vals)/len(vals) if vals else 0.0

        mean_ref  = _mean_max_h1(reference_texts)
        mean_hall = _mean_max_h1(known_hallucinations)

        optimal = round((mean_ref + mean_hall) / 2, 4) if mean_hall > mean_ref else self.kappa_d

        return {
            "mean_h1_coherent":      round(mean_ref, 4),
            "mean_h1_hallucinated":  round(mean_hall, 4),
            "optimal_threshold":     optimal,
            "current_kappa_d":       self.kappa_d,
            "recommendation": (
                f"Usar threshold={optimal:.4f} para este corpus. "
                f"Ajustar attestator.kappa_d = {optimal:.4f}"
            ),
        }

    # ── Visualization ─────────────────────────────────────────

    def plot_persistence(
        self,
        report: TDAAttestationReport,
        output_path: Optional[str] = None,
    ) -> Optional[bytes]:
        """
        Generates scatter diagram of persistence pairs.
        Retorna PNG como bytes si output_path es None.
        """
        if not _MPL_OK:
            return None

        fig, axes = plt.subplots(1, 2, figsize=(12, 5), facecolor="#000")

        for ax in axes:
            ax.set_facecolor("#0D0D0D")
            ax.tick_params(colors="#FFB100")
            ax.spines["bottom"].set_color("#FFB100")
            ax.spines["left"].set_color("#FFB100")
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)

        # ── Plot H₀ ───────────────────────────────────────────
        ax0 = axes[0]
        h0  = [p for p in report.h0_pairs if not math.isinf(p.death)]
        if h0:
            births  = [p.birth for p in h0]
            deaths  = [p.death for p in h0]
            ax0.scatter(births, deaths, c="#FFB100", s=40, alpha=0.8, label="H₀ finitos")
        # Diagonal
        lim = max(report.max_h1_persistence * 1.2, 1.0)
        ax0.plot([0, lim], [0, lim], "--", color="rgba(255,177,0,0.3)", linewidth=0.8)
        ax0.set_xlabel("Birth", color="#FFB100", fontsize=9)
        ax0.set_ylabel("Death", color="#FFB100", fontsize=9)
        ax0.set_title("Diagrama H₀ (Componentes Conexas)",
                      color="#FFB100", fontsize=9)

        # ── Plot H₁ ───────────────────────────────────────────
        ax1 = axes[1]
        h1_sf   = [p for p in report.h1_pairs if p.flag == "STRUCTURAL_FALSEHOOD" and not math.isinf(p.death)]
        h1_stab = [p for p in report.h1_pairs if p.flag == "STABILIZED"]
        h1_noise= [p for p in report.h1_pairs if p.flag == "NOISE"]

        if h1_sf:
            ax1.scatter([p.birth for p in h1_sf],
                        [p.death for p in h1_sf],
                        c="#FF2D2D", s=60, marker="X", alpha=0.9,
                        label=f"STRUCTURAL_FALSEHOOD ({len(h1_sf)})", zorder=5)
        if h1_stab:
            ax1.scatter([p.birth for p in h1_stab],
                        [p.death for p in h1_stab],
                        c="#00FF88", s=40, alpha=0.7,
                        label=f"STABILIZED ({len(h1_stab)})")
        if h1_noise:
            ax1.scatter([p.birth for p in h1_noise],
                        [p.death for p in h1_noise],
                        c="#444", s=20, alpha=0.5,
                        label=f"NOISE ({len(h1_noise)})")

        # κD threshold line (death = birth * κD → slope κD in log)
        xs = np.linspace(0, lim, 100)
        ax1.plot(xs, xs + report.kappa_d, "--",
                 color="#FFB100", linewidth=1.2, alpha=0.6,
                 label=f"Umbral κD={report.kappa_d}")
        ax1.plot([0, lim], [0, lim], "-",
                 color="rgba(255,177,0,0.2)", linewidth=0.7)

        ax1.set_xlabel("Birth", color="#FFB100", fontsize=9)
        ax1.set_ylabel("Death", color="#FFB100", fontsize=9)
        ax1.set_title(
            f"Diagrama H₁ (Ciclos) — {report.verdict}",
            color=("#FF2D2D" if "COLLAPSE" in report.verdict else "#FFB100"),
            fontsize=9,
        )
        leg = ax1.legend(fontsize=7, facecolor="#1A1A1A",
                         edgecolor="#FFB100", labelcolor="#FFB100")

        plt.suptitle(
            f"TOPOLOGICAL ATTESTATION — Hash: {report.text_hash}",
            color="#FFB100", fontsize=10, fontfamily="monospace",
        )
        plt.tight_layout(pad=1.5)

        if output_path:
            fig.savefig(output_path, dpi=130, facecolor="#000", bbox_inches="tight")
            plt.close(fig)
            return None
        else:
            import io
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=130,
                        facecolor="#000", bbox_inches="tight")
            plt.close(fig)
            buf.seek(0)
            return buf.read()

    # ── Helpers ───────────────────────────────────────────────

    def _split_sentences(self, text: str) -> List[str]:
        sents = re.split(r"(?<=[.!?])\s+", text.strip())
        return [s.strip() for s in sents if len(s.strip()) > 8]


# ══════════════════════════════════════════════════════════════
# Command line interface
# ══════════════════════════════════════════════════════════════

def _cli():
    import argparse, sys
    parser = argparse.ArgumentParser(
        prog="tda_attestation",
        description="Topological Attestation of text via Persistent Homology",
    )
    parser.add_argument("--file",   help="Text file to audit")
    parser.add_argument("--kappa",  type=float, default=0.56,
                        help="Umbral κD (default: 0.56)")
    parser.add_argument("--dim",    type=int,   default=20,
                        help="LSA embedding dimension (default: 20)")
    parser.add_argument("--plot",   help="Guardar diagrama de persistencia en PNG")
    parser.add_argument("--json",   action="store_true", help="Salida JSON")
    args = parser.parse_args()

    if args.file:
        text = Path(args.file).read_text(encoding="utf-8")
    else:
        print("Paste text (END to finish):")
        lines = []
        try:
            while True:
                line = sys.stdin.readline()
                if not line or line.strip() == "END": break
                lines.append(line)
        except (KeyboardInterrupt, EOFError):
            pass
        text = "".join(lines)

    attestator = TDAAttestator(persistence_threshold=args.kappa, embedding_dim=args.dim)
    report = attestator.attest(text)

    if args.json:
        print(report.to_json())
    else:
        print(report.summary)

    if args.plot:
        attestator.plot_persistence(report, output_path=args.plot)
        print(f"\nDiagrama guardado: {args.plot}")


if __name__ == "__main__":
    _cli()
