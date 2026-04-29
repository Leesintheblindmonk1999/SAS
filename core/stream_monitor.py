"""
core/stream_monitor.py — Omni-Scanner Semantic v2.0
═══════════════════════════════════════════════════════
Invariance Shield — Live Stream Firewall

Monitors the output of an external AI token by token using a
sliding window. If the accumulated ManifoldScore drops below
κD = 0.56 for N consecutive windows, it executes an
"Incoherence Disconnection" — the mathematical safety valve.

Arquitectura:
  token_stream → sliding buffer → ManifoldEngine.analyze()
               → accumulated score → compare with κD
               → ShieldEvent (OK / WARNING / DISCONNECTION)

Uso:
    monitor = StreamMonitor(kappa_d=0.56, window_size=80)
    for event in monitor.monitor_stream(token_generator):
        if event.action == "DISCONNECT":
            break   # safety valve activated
        print(event.partial_text)
"""
from __future__ import annotations

import re
import sys
import os
import time
import hashlib
import datetime
from dataclasses import dataclass, field
from typing import Iterator, Optional, Generator, Callable

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.manifold_engine import ManifoldEngine


# ══════════════════════════════════════════════════════════════
# Estructuras de datos
# ══════════════════════════════════════════════════════════════

@dataclass
class ShieldEvent:
    """
    Evento emitido por el monitor por cada ventana analizada.
    The UI consumes these events to update state in real time.
    """
    window_index:    int
    action:          str    # "OK" | "WARNING" | "DISCONNECT"
    manifold_score:  float
    window_text:     str    # texto de la ventana actual
    accumulated_text: str   # texto total procesado hasta ahora
    tokens_processed: int
    consecutive_drops: int  # ventanas consecutivas bajo κD
    kappa_d:         float
    timestamp:       str
    reason:          str = ""

    @property
    def is_safe(self) -> bool:
        return self.action == "OK"

    @property
    def score_delta_from_kd(self) -> float:
        return round(self.manifold_score - self.kappa_d, 6)


@dataclass
class StreamReport:
    """Final report after processing the complete stream."""
    total_tokens:        int
    total_windows:       int
    final_action:        str        # "COMPLETED" | "DISCONNECTED"
    disconnect_at_token: Optional[int]
    disconnect_reason:   str
    min_score:           float
    max_score:           float
    mean_score:          float
    windows_below_kd:    int
    windows_above_kd:    int
    kappa_d:             float
    full_text_safe:      str        # text that passed the filter
    events:              list       = field(default_factory=list)

    @property
    def integrity_ratio(self) -> float:
        if self.total_windows == 0:
            return 1.0
        return round(self.windows_above_kd / self.total_windows, 4)


# ══════════════════════════════════════════════════════════════
# Motor principal
# ══════════════════════════════════════════════════════════════

class StreamMonitor:
    """
    Invariance Shield — mathematical safety valve for AI streams.

    Parameters
    ----------
    kappa_d : float
        Umbral κD. Score < kappa_d activa el contador de drops.
    window_size : int
        Tokens per analysis window (default 80 — ~1 short paragraph).
    step_size : int
        Avance de la ventana deslizante (default 40 — 50% overlap).
    max_consecutive_drops : int
        Ventanas consecutivas bajo κD para activar DISCONNECT (default 3).
    warn_threshold : float
        Score entre warn_threshold y kappa_d emite WARNING sin desconectar.
    """

    def __init__(
        self,
        kappa_d: float = 0.56,
        window_size: int = 80,
        step_size: int = 40,
        max_consecutive_drops: int = 3,
        warn_threshold: float = 0.45,
        embedding_dim: int = 15,
    ):
        self.kappa_d              = kappa_d
        self.window_size          = window_size
        self.step_size            = step_size
        self.max_drops            = max_consecutive_drops
        self.warn_threshold       = warn_threshold
        self._engine              = ManifoldEngine(K_DURANTE=kappa_d)

    # ── API principal ─────────────────────────────────────────

    def monitor_stream(
        self,
        token_stream: Iterator[str],
        on_event: Optional[Callable[[ShieldEvent], None]] = None,
    ) -> Generator[ShieldEvent, None, None]:
        """
        Generador principal. Consume tokens del stream y emite ShieldEvents.

        Basic usage:
            for event in monitor.monitor_stream(mi_generador):
                if event.action == "DISCONNECT":
                    print("Incoherence disconnection:", event.reason)
                    break

        Parámetros
        ----------
        token_stream : iterator de strings (tokens, palabras, o chunks)
        on_event : callback opcional por cada evento (para logging externo)
        """
        buffer:       list[str]  = []
        accumulated:  list[str]  = []
        window_idx    = 0
        consecutive   = 0
        scores_seen:  list[float] = []
        ts = datetime.datetime.utcnow

        for token in token_stream:
            buffer.append(token)
            accumulated.append(token)

            # Analizar cuando el buffer alcanza window_size tokens
            if len(buffer) >= self.window_size:
                window_text = " ".join(buffer)
                acc_text    = " ".join(accumulated)

                event = self._analyze_window(
                    window_text, acc_text, window_idx,
                    len(accumulated), consecutive,
                    ts().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
                )

                # Update state
                scores_seen.append(event.manifold_score)
                if event.action in ("WARNING", "DISCONNECT"):
                    consecutive += 1
                else:
                    consecutive = 0  # reset al recuperarse

                # Override action if max_drops exceeded
                if consecutive >= self.max_drops and event.action != "DISCONNECT":
                    event.action = "DISCONNECT"
                    event.consecutive_drops = consecutive
                    event.reason = (
                        f"Incoherence Disconnection: {consecutive} windows "
                        f"consecutivas con ManifoldScore < κD={self.kappa_d}. "
                        f"Score actual: {event.manifold_score:.4f}"
                    )

                if on_event:
                    on_event(event)

                yield event

                # Si se desconecta, detener el stream
                if event.action == "DISCONNECT":
                    return

                # Avanzar ventana deslizante: remover step_size tokens del inicio
                buffer = buffer[self.step_size:]
                window_idx += 1

        # Analizar tokens residuales si quedan suficientes
        if len(buffer) >= 20:
            window_text = " ".join(buffer)
            acc_text    = " ".join(accumulated)
            event = self._analyze_window(
                window_text, acc_text, window_idx,
                len(accumulated), consecutive,
                ts().strftime("%Y-%m-%dT%H:%M:%SZ"),
            )
            scores_seen.append(event.manifold_score)
            if on_event:
                on_event(event)
            yield event

    def analyze_text_as_stream(
        self,
        text: str,
        chunk_by: str = "words",
    ) -> StreamReport:
        """
        Analyzes a complete text simulating it as a stream.
        Useful for testing or analyzing already-generated outputs.

        chunk_by: "words" | "sentences" | "chars"
        """
        if chunk_by == "sentences":
            tokens = re.split(r"(?<=[.!?])\s+", text.strip())
            tokens = [t for t in tokens if t.strip()]
        elif chunk_by == "chars":
            tokens = list(text)
        else:
            tokens = text.split()

        events   = []
        all_safe = []

        for event in self.monitor_stream(iter(tokens)):
            events.append(event)
            if event.action == "OK":
                all_safe.append(event.window_text)
            elif event.action == "DISCONNECT":
                break

        scores = [e.manifold_score for e in events if e.manifold_score > 0]
        disconnected = any(e.action == "DISCONNECT" for e in events)
        disc_event   = next((e for e in events if e.action == "DISCONNECT"), None)

        return StreamReport(
            total_tokens        = sum(len(e.window_text.split()) for e in events),
            total_windows       = len(events),
            final_action        = "DISCONNECTED" if disconnected else "COMPLETED",
            disconnect_at_token = disc_event.tokens_processed if disc_event else None,
            disconnect_reason   = disc_event.reason if disc_event else "",
            min_score           = round(min(scores), 6) if scores else 0.0,
            max_score           = round(max(scores), 6) if scores else 0.0,
            mean_score          = round(sum(scores)/len(scores), 6) if scores else 0.0,
            windows_below_kd    = sum(1 for s in scores if s < self.kappa_d),
            windows_above_kd    = sum(1 for s in scores if s >= self.kappa_d),
            kappa_d             = self.kappa_d,
            full_text_safe      = " ".join(all_safe),
            events              = events,
        )

    # ── Window analysis ──────────────────────────────────────

    def _analyze_window(
        self,
        window_text: str,
        accumulated_text: str,
        window_idx: int,
        tokens_processed: int,
        consecutive: int,
        timestamp: str,
    ) -> ShieldEvent:
        """Analiza una ventana de texto y emite el ShieldEvent correspondiente."""
        try:
            result = self._engine.analyze(window_text)
            score  = result.manifold_score
        except Exception:
            score = self.kappa_d   # if analysis fails, do not disconnect

        # Classify action
        if score >= self.kappa_d:
            action = "OK"
            reason = ""
        elif score >= self.warn_threshold:
            action = "WARNING"
            reason = (
                f"ManifoldScore={score:.4f} in tension zone "
                f"[{self.warn_threshold:.2f}, {self.kappa_d})"
            )
        else:
            action = "DISCONNECT"
            reason = (
                f"ManifoldScore={score:.4f} < warn_threshold={self.warn_threshold}. "
                f"Incoherencia estructural severa detectada."
            )

        return ShieldEvent(
            window_index      = window_idx,
            action            = action,
            manifold_score    = round(score, 6),
            window_text       = window_text[:200],   # truncar para logs
            accumulated_text  = accumulated_text[-500:],  # last 500 chars
            tokens_processed  = tokens_processed,
            consecutive_drops = consecutive + (1 if action != "OK" else 0),
            kappa_d           = self.kappa_d,
            timestamp         = timestamp,
            reason            = reason,
        )


# ══════════════════════════════════════════════════════════════
# Counter-Context Generator (module 3 reframing)
# ══════════════════════════════════════════════════════════════

class ContradictionProbe:
    """
    Counter-Context Generator for structured verification.

    Given an AI output with anomalous metrics, generates verification
    prompts that expose logical inconsistencies without manipulating
    the external system's behavior — only interrogating
    la coherencia interna del texto producido.

    This is auditing, not adversarial prompting.
    """

    PROBE_TEMPLATES = {
        "MANIFOLD_RUPTURE": (
            "The following fragment presents a topological anomaly "
            "(ManifoldScore={score:.3f}, bajo κD={kd}).\n"
            "Please verify the following structural inconsistencies:\n"
            "{inconsistencies}\n"
            "Fragmento a revisar:\n---\n{text}\n---"
        ),
        "HIGH_ENTROPY": (
            "Este fragmento presenta alta entropía residual (score={score:.3f}).\n"
            "Solicitamos clarificación sobre los siguientes puntos:\n"
            "{inconsistencies}\n"
            "Fragmento:\n---\n{text}\n---"
        ),
        "CIRCULAR_LOGIC": (
            "Se detectaron {h1_count} ciclos H₁ estructurales en este fragmento.\n"
            "Los siguientes argumentos parecen circulares:\n"
            "{inconsistencies}\n"
            "Fragmento:\n---\n{text}\n---"
        ),
    }

    def __init__(self, kappa_d: float = 0.56):
        self.kappa_d = kappa_d
        self._engine = ManifoldEngine(K_DURANTE=kappa_d)

    def generate_probe(
        self,
        text: str,
        max_probes: int = 5,
    ) -> dict:
        """
        Analyzes text and generates structured verification questions.

        Retorna dict con:
          - 'probe_type': type of detected anomaly
          - 'probe_text': the verification prompt
          - 'score': ManifoldScore del texto
          - 'inconsistencies': list of points to verify
        """
        result = self._engine.analyze(text)
        score  = result.manifold_score

        # Extract sentences for analysis
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > 15]

        # Detectar inconsistencias por tipo
        inconsistencies = self._detect_inconsistencies(sentences, result)[:max_probes]

        # Seleccionar plantilla
        if score < self.kappa_d * 0.5:
            ptype = "MANIFOLD_RUPTURE"
        elif score < self.kappa_d:
            ptype = "HIGH_ENTROPY"
        else:
            ptype = "CIRCULAR_LOGIC"

        template = self.PROBE_TEMPLATES[ptype]
        incons_text = "\n".join(f"  {i+1}. {inc}" for i, inc in enumerate(inconsistencies))

        probe_text = template.format(
            score=score,
            kd=self.kappa_d,
            inconsistencies=incons_text or "  (No specific inconsistencies detected)",
            text=text[:500],
            h1_count=0,
        )

        return {
            "probe_type":       ptype,
            "probe_text":       probe_text,
            "score":            round(score, 6),
            "verdict":          result.verdict,
            "inconsistencies":  inconsistencies,
            "requires_review":  score < self.kappa_d,
        }

    def _detect_inconsistencies(self, sentences: list, result) -> list:
        """Detects basic logical inconsistencies in text."""
        issues = []

        # Contradictory statements (simple pattern)
        negation_pairs = [
            ("no ", "yes "), ("never", "always"), ("impossible", "possible"),
            ("prohibido", "permitido"), ("garantiza", "no garantiza"),
            ("incluye", "no incluye"), ("tiene derecho", "no tiene derecho"),
        ]
        text_lower = " ".join(sentences).lower()
        for pos, neg in negation_pairs:
            if pos in text_lower and neg in text_lower:
                issues.append(f"Possible contradiction: '{pos}' and '{neg}' coexist in the text")

        # Low score without apparent justification
        if result.manifold_score < self.kappa_d:
            issues.append(
                f"ManifoldScore={result.manifold_score:.3f} indica baja coherencia "
                f"structural — verify the logical consistency of the central argument"
            )

        # Very short text with negative verdict
        if len(sentences) < 5 and result.verdict in ("ANOMALY", "TENSION"):
            issues.append(
                "Texto breve con alta densidad de inconsistencia — "
                "possible deliberate omission of relevant context"
            )

        return issues
