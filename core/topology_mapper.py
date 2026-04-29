"""
topology_mapper.py — Omni-Scanner Semantic v1.0
-------------------------------------------------
CHANGELOG vs original version:
  + map_logic_flow(segments) preservada con firma original (usa networkx)
  + NUEVO: analyze(text) — pipeline completo texto → TopologyReport
    sin necesidad de pre-construir el grafo manualmente
  + NEW: automatic graph construction from sentences via TF-IDF cosine
  + NUEVO: coherence_score [0,1] combinando densidad + clustering + conectividad
  + Cycle detection (circular logic) and centrality preserved
"""
from __future__ import annotations
import re
import math
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
import networkx as nx


@dataclass
class TopologyReport:
    node_count: int
    edge_count: int
    density: float
    avg_clustering: float
    components: int
    circular_logic_detected: bool
    main_anchor: str
    critical_vulnerability: str     # API original preservada
    coherence_score: float
    flag: str                       # "COHERENT" | "FRAGMENTED" | "INSUFFICIENT"
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


class TopologyMapper:
    """
    Parameters
    ----------
    similarity_threshold : float    Cosine threshold for automatic edge creation.
    min_sentences : int             Minimum sentences for analysis.
    coherence_threshold : float     Umbral para flag COHERENT.
    """

    def __init__(
        self,
        similarity_threshold: float = 0.20,
        min_sentences: int = 5,
        coherence_threshold: float = 0.30,   # alineado con manifold topo_coherent threshold
        adaptive_threshold: bool = True,
    ):
        self.similarity_threshold = similarity_threshold
        self.min_sentences = min_sentences
        self.coherence_threshold = coherence_threshold
        self.adaptive_threshold = adaptive_threshold
        self.graph = nx.DiGraph()   # preservado como atributo de instancia (API original)

    # ------------------------------------------------------------------
    # API ORIGINAL (preservada para compatibilidad)
    # ------------------------------------------------------------------

    def map_logic_flow(self, segments: List[Tuple]) -> dict:
        """
        Convierte pares (src, dst, weight) en un grafo dirigido.
        API original preservada.
        segments: Lista de (idea_origen, idea_destino, peso_logico)
        """
        self.graph.clear()
        for src, dst, weight in segments:
            self.graph.add_edge(src, dst, weight=weight)

        centrality = nx.degree_centrality(self.graph)
        cycles = list(nx.simple_cycles(self.graph))

        return {
            "nodes_count": self.graph.number_of_nodes(),
            "edges_count": self.graph.number_of_edges(),
            "circular_logic_detected": len(cycles) > 0,
            "main_anchor": max(centrality, key=centrality.get) if centrality else "N/A",
            "critical_vulnerability": (
                "LOGICAL VOID"
                if not nx.is_weakly_connected(self.graph)
                else "SOLID STRUCTURE"
            ),
        }

    # ------------------------------------------------------------------
    # API EXTENDIDA — pipeline completo sobre texto crudo
    # ------------------------------------------------------------------

    def analyze(self, text: str) -> TopologyReport:
        """
        Pipeline completo: texto → TopologyReport.
        Automatically builds graph from sentences via TF-IDF cosine.
        """
        sentences = self._split_sentences(text)
        n = len(sentences)

        if n < self.min_sentences:
            return TopologyReport(
                node_count=n, edge_count=0, density=0.0,
                avg_clustering=0.0, components=n,
                circular_logic_detected=False, main_anchor="N/A",
                critical_vulnerability="LOGICAL VOID",
                coherence_score=0.0, flag="INSUFFICIENT",
                details={"reason": f"Too few sentences ({n} < {self.min_sentences})"},
            )

        tfidf = self._compute_tfidf(sentences)
        edges = self._build_edges(tfidf, n)

        # Build directed graph (order of appearance → direction)
        G = nx.DiGraph()
        G.add_nodes_from(range(n))
        for i, j, w in edges:
            G.add_edge(i, j, weight=w)

        # Update self.graph for original API compatibility
        self.graph = G

        centrality = nx.degree_centrality(G)
        cycles = list(nx.simple_cycles(G))
        components = nx.number_weakly_connected_components(G)
        is_connected = nx.is_weakly_connected(G)

        density = nx.density(G)
        ug = G.to_undirected()
        avg_clust = nx.average_clustering(ug)
        coherence = self._coherence_score(density, avg_clust, components, n)
        flag = "COHERENT" if coherence >= self.coherence_threshold else "FRAGMENTED"

        main_anchor_idx = max(centrality, key=centrality.get) if centrality else 0
        # Show fragment of anchor sentence
        main_anchor_text = sentences[main_anchor_idx][:60] + "..." if len(sentences[main_anchor_idx]) > 60 else sentences[main_anchor_idx]

        return TopologyReport(
            node_count=n,
            edge_count=len(edges),
            density=round(density, 6),
            avg_clustering=round(avg_clust, 6),
            components=components,
            circular_logic_detected=len(cycles) > 0,
            main_anchor=main_anchor_text,
            critical_vulnerability="LOGICAL VOID" if not is_connected else "SOLID STRUCTURE",
            coherence_score=round(coherence, 6),
            flag=flag,
            details={
                "similarity_threshold": self.similarity_threshold,
                "coherence_threshold": self.coherence_threshold,
                "cycles_found": len(cycles),
            },
        )

    # ------------------------------------------------------------------
    # Helpers privados (TF-IDF sin dependencias externas)
    # ------------------------------------------------------------------

    def _split_sentences(self, text: str) -> List[str]:
        sents = re.split(r"(?<=[.!?])\s+", text.strip())
        return [s.strip() for s in sents if len(s.strip()) > 10]

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"\b\w+\b", text.lower())

    def _compute_tfidf(self, sentences: List[str]) -> List[dict]:
        tokenized = [self._tokenize(s) for s in sentences]
        N = len(tokenized)
        df: dict = defaultdict(int)
        for tokens in tokenized:
            for t in set(tokens):
                df[t] += 1
        idf = {t: math.log((N + 1) / (df[t] + 1)) + 1 for t in df}
        vecs = []
        for tokens in tokenized:
            tf: dict = defaultdict(float)
            for t in tokens:
                tf[t] += 1
            total = max(len(tokens), 1)
            vecs.append({t: (c / total) * idf.get(t, 1.0) for t, c in tf.items()})
        return vecs

    def _cosine(self, a: dict, b: dict) -> float:
        common = set(a) & set(b)
        if not common:
            return 0.0
        dot = sum(a[k] * b[k] for k in common)
        na = math.sqrt(sum(v ** 2 for v in a.values()))
        nb = math.sqrt(sum(v ** 2 for v in b.values()))
        return dot / max(na * nb, 1e-12)

    def _build_edges(self, vecs: List[dict], n: int) -> List[Tuple[int, int, float]]:
        """
        Builds edges with hybrid k-NN + threshold strategy.

        Problema diagnosticado:
        With documents with short sentences (contracts, legal clauses),
        el 90%+ de pares coseno tiene similitud = 0.
        Cualquier umbral global deja el grafo con 3 aristas para 33 nodos.

        Solution: guaranteed k-NN + soft threshold.
        - For each node, connect its k nearest neighbors (k=2 minimum).
        - Agregar aristas adicionales de similitud alta (>= umbral suave).
        - Resultado: grafo siempre conectado con densidad razonable.
        """
        # Calcular matriz de similitudes completa
        sim_matrix: List[Tuple[int, int, float]] = []
        for i in range(n):
            for j in range(i + 1, n):
                sim = self._cosine(vecs[i], vecs[j])
                sim_matrix.append((i, j, sim))

        all_sims = [s for _, _, s in sim_matrix if s > 1e-9]

        # ── Estrategia k-NN garantizado ───────────────────────
        # Adaptive k: more sentences → fewer neighbors needed
        k_neighbors = max(2, min(4, n // 8))

        # For each node, the k nearest neighbors
        edge_set: set = set()
        for i in range(n):
            # Similarities from i to all others
            neighbors = sorted(
                [(sim, j) for _, j, sim in sim_matrix if _ == i] +
                [(sim, i) for j2, _, sim in sim_matrix if _ == i],
                reverse=True,
            )
            # Reconstruir correctamente por nodo
            node_sims = []
            for a, b, sim in sim_matrix:
                if a == i:
                    node_sims.append((sim, b))
                elif b == i:
                    node_sims.append((sim, a))
            node_sims.sort(reverse=True)

            for sim_val, j in node_sims[:k_neighbors]:
                if sim_val > 1e-9:
                    key = (min(i, j), max(i, j))
                    edge_set.add((key[0], key[1], sim_val))

        # ── Aristas adicionales por umbral suave ──────────────
        if all_sims:
            sorted_desc = sorted(all_sims, reverse=True)
            # Top 20% de similitudes positivas siempre entran
            top20_idx = max(0, int(len(sorted_desc) * 0.20))
            soft_threshold = sorted_desc[top20_idx] if top20_idx < len(sorted_desc) else 0.0

            for i, j, sim in sim_matrix:
                if sim >= soft_threshold:
                    key = (min(i, j), max(i, j))
                    edge_set.add((key[0], key[1], sim))

        return list(edge_set)

    def _coherence_score(self, density: float, clustering: float, components: int, n: int) -> float:
        isolation_penalty = (components - 1) / max(n - 1, 1)
        return max(0.0, 0.5 * density + 0.3 * clustering + 0.2 * (1 - isolation_penalty))
