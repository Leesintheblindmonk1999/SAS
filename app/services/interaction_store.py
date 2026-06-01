"""
app/services/interaction_store.py - SAS Interaction Observability Store

Persistent, non-blocking observability for /v1/interaction/stability.

Design goals:
- Store operational metadata and aggregate model outputs only.
- Never store raw submitted conversation text.
- Never store raw API keys.
- Never block the user-facing endpoint if observability fails.
- Use SQLite + in-memory queue + background writer thread, following audit_store.py.
- Provide safe aggregate stats for /public/interaction/stats and funnel_report.py.
"""

from __future__ import annotations

import hashlib
import logging
import os
import queue
import sqlite3
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, NamedTuple

logger = logging.getLogger("sas.interaction_store")

INTERACTION_DB_PATH: str = os.getenv("INTERACTION_DB_PATH", "/app/data/interaction.db")
INTERACTION_HASH_PEPPER: str = os.getenv(
    "INTERACTION_HASH_PEPPER",
    os.getenv("AUDIT_SALT_SECRET", "sas-interaction-observability-dev-pepper"),
)

QUEUE_MAXSIZE = int(os.getenv("INTERACTION_QUEUE_MAXSIZE", "10000"))
BATCH_SIZE = int(os.getenv("INTERACTION_BATCH_SIZE", "50"))
FLUSH_INTERVAL_SECONDS = float(os.getenv("INTERACTION_FLUSH_INTERVAL_SECONDS", "2.0"))

_QUEUE: queue.Queue = queue.Queue(maxsize=QUEUE_MAXSIZE)
_WRITER_THREAD: threading.Thread | None = None
_SHUTDOWN = threading.Event()


class InteractionEvent(NamedTuple):
    ts_utc: str
    request_id: str
    executed_at: str
    api_key_hash: str
    user_id: str
    plan: str
    conversation_turns: int
    assistant_turns: int
    final_dominant_state: str
    final_dominant_probability: float
    final_omega_t: float
    final_sigma: float
    demand_peak: float
    threshold_crossed: int
    stability_below_kappa: int
    high_uncertainty: int
    input_hash: str
    content_fingerprint: str
    latency_ms: float


def hash_api_key_for_observability(api_key: str | None) -> str:
    """Return a short opaque hash for an API key. Raw API keys are never stored."""
    if not api_key:
        return "anonymous"
    material = f"{INTERACTION_HASH_PEPPER}:api_key:{api_key.strip()}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:12]


def _safe_str(value: Any, default: str = "unknown", max_len: int = 128) -> str:
    if value is None:
        return default
    text = str(value)
    if not text:
        return default
    return text[:max_len]


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _safe_bool_int(value: Any) -> int:
    return 1 if bool(value) else 0


def _connect(db_path: str = INTERACTION_DB_PATH) -> sqlite3.Connection:
    db = Path(db_path)
    db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db), timeout=5)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def init_interaction_db(path: str = INTERACTION_DB_PATH) -> None:
    """Initialize interaction observability database and start writer thread."""
    conn = _connect(path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS interaction_events (
                id                           INTEGER PRIMARY KEY AUTOINCREMENT,
                ts_utc                       TEXT NOT NULL,
                request_id                   TEXT,
                executed_at                  TEXT,
                api_key_hash                 TEXT,
                user_id                      TEXT,
                plan                         TEXT,
                conversation_turns           INTEGER,
                assistant_turns              INTEGER,
                final_dominant_state         TEXT,
                final_dominant_probability   REAL,
                final_omega_t                REAL,
                final_sigma                  REAL,
                demand_peak                  REAL,
                threshold_crossed            INTEGER,
                stability_below_kappa        INTEGER,
                high_uncertainty             INTEGER,
                input_hash                   TEXT,
                content_fingerprint          TEXT,
                latency_ms                   REAL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_interaction_ts ON interaction_events (ts_utc)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_interaction_request_id ON interaction_events (request_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_interaction_api_key_hash ON interaction_events (api_key_hash)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_interaction_plan ON interaction_events (plan)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_interaction_state ON interaction_events (final_dominant_state)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_interaction_alerts ON interaction_events (threshold_crossed, stability_below_kappa, high_uncertainty)")
        conn.commit()
        logger.info("interaction_db_initialized path=%s", str(path))
    finally:
        conn.close()
    _start_writer(str(path))


def interaction_db_stats(db_path: str = INTERACTION_DB_PATH) -> dict[str, Any]:
    """Lightweight readiness/statistics check. Startup owns initialization."""
    try:
        conn = _connect(db_path)
        row = conn.execute(
            "SELECT COUNT(*) AS total, MIN(ts_utc) AS oldest, MAX(ts_utc) AS newest FROM interaction_events"
        ).fetchone()
        conn.close()
        return {
            "ok": True,
            "total_events": int(row["total"] or 0),
            "oldest": row["oldest"],
            "newest": row["newest"],
            "queue_size": safe_queue_size(),
            "writer_alive": bool(_WRITER_THREAD and _WRITER_THREAD.is_alive()),
        }
    except Exception as exc:
        return {
            "ok": False,
            "error": str(exc),
            "queue_size": safe_queue_size(),
            "writer_alive": bool(_WRITER_THREAD and _WRITER_THREAD.is_alive()),
        }


def enqueue_interaction_event(event: InteractionEvent) -> None:
    """Non-blocking enqueue. Never raises."""
    try:
        _QUEUE.put_nowait(event)
    except queue.Full:
        logger.warning(
            "interaction_queue_full dropping_new_event request_id=%s queue_size=%s",
            getattr(event, "request_id", "unknown"),
            safe_queue_size(),
        )
    except Exception as exc:
        logger.warning("interaction_enqueue_failed error=%s", exc)


def record_interaction_event(
    *,
    request_id: str,
    executed_at: str,
    api_key: str | None,
    user_id: Any,
    plan: str | None,
    conversation_turns: int,
    assistant_turns: int,
    summary: dict[str, Any],
    input_hash: str,
    content_fingerprint: str,
    latency_ms: float,
) -> None:
    """Build and enqueue an InteractionEvent from a successful analysis."""
    try:
        alerts = summary.get("alerts", {}) if isinstance(summary, dict) else {}
        event = InteractionEvent(
            ts_utc=datetime.now(timezone.utc).isoformat(),
            request_id=_safe_str(request_id),
            executed_at=_safe_str(executed_at),
            api_key_hash=hash_api_key_for_observability(api_key),
            user_id=_safe_str(user_id, default="unknown", max_len=64),
            plan=_safe_str(plan, default="unknown", max_len=32),
            conversation_turns=int(conversation_turns),
            assistant_turns=int(assistant_turns),
            final_dominant_state=_safe_str(summary.get("final_dominant_state"), max_len=64),
            final_dominant_probability=_safe_float(summary.get("final_dominant_probability")),
            final_omega_t=_safe_float(summary.get("final_omega_t", summary.get("final_chi"))),
            final_sigma=_safe_float(summary.get("final_sigma")),
            demand_peak=_safe_float(summary.get("demand_peak")),
            threshold_crossed=_safe_bool_int(alerts.get("threshold_crossed")),
            stability_below_kappa=_safe_bool_int(alerts.get("stability_below_kappa")),
            high_uncertainty=_safe_bool_int(alerts.get("high_uncertainty")),
            input_hash=_safe_str(input_hash, default="", max_len=64),
            content_fingerprint=_safe_str(content_fingerprint, default="", max_len=64),
            latency_ms=round(_safe_float(latency_ms), 2),
        )
        enqueue_interaction_event(event)
    except Exception as exc:
        logger.warning("interaction_record_failed_open request_id=%s error=%s", request_id, exc)


_INSERT_SQL = """
    INSERT INTO interaction_events (
        ts_utc, request_id, executed_at, api_key_hash, user_id, plan,
        conversation_turns, assistant_turns, final_dominant_state,
        final_dominant_probability, final_omega_t, final_sigma, demand_peak,
        threshold_crossed, stability_below_kappa, high_uncertainty,
        input_hash, content_fingerprint, latency_ms
    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
"""


def _flush_batch(conn: sqlite3.Connection | None, db_path: str, batch: list[InteractionEvent]) -> sqlite3.Connection | None:
    if not batch:
        return conn
    if conn is None:
        conn = _connect(db_path)
    conn.executemany(_INSERT_SQL, batch)
    conn.commit()
    return conn


def _drain_queue_into(batch: list[InteractionEvent], limit: int | None = None) -> None:
    while limit is None or len(batch) < limit:
        try:
            batch.append(_QUEUE.get_nowait())
        except queue.Empty:
            break


def _writer_loop(db_path: str) -> None:
    conn: sqlite3.Connection | None = None
    batch: list[InteractionEvent] = []
    last_flush = time.monotonic()
    while not _SHUTDOWN.is_set():
        try:
            timeout = max(0.1, FLUSH_INTERVAL_SECONDS - (time.monotonic() - last_flush))
            event = _QUEUE.get(timeout=timeout)
            batch.append(event)
            _drain_queue_into(batch, BATCH_SIZE)
        except queue.Empty:
            pass
        should_flush = bool(batch) and (
            len(batch) >= BATCH_SIZE or (time.monotonic() - last_flush >= FLUSH_INTERVAL_SECONDS)
        )
        if should_flush:
            try:
                conn = _flush_batch(conn, db_path, batch)
                batch.clear()
                last_flush = time.monotonic()
            except Exception as exc:
                logger.error("interaction_writer_failed error=%s", exc)
                try:
                    if conn:
                        conn.close()
                except Exception:
                    pass
                conn = None
    try:
        _drain_queue_into(batch, None)
        if batch:
            conn = _flush_batch(conn, db_path, batch)
            batch.clear()
    except Exception as exc:
        logger.error("interaction_shutdown_flush_failed error=%s remaining_events=%d", exc, len(batch))
    finally:
        try:
            if conn:
                conn.close()
        except Exception:
            pass


def _start_writer(db_path: str) -> None:
    global _WRITER_THREAD
    if _WRITER_THREAD and _WRITER_THREAD.is_alive():
        return
    _SHUTDOWN.clear()
    _WRITER_THREAD = threading.Thread(
        target=_writer_loop,
        args=(db_path,),
        name="sas-interaction-writer",
        daemon=True,
    )
    _WRITER_THREAD.start()
    logger.info("interaction_writer_started db=%s", db_path)


def stop_interaction_writer() -> None:
    """Stop writer and flush remaining queued events."""
    _SHUTDOWN.set()
    if _WRITER_THREAD:
        _WRITER_THREAD.join(timeout=5)
        if _WRITER_THREAD.is_alive():
            logger.warning("interaction_writer_stop_timeout queue_size=%s", safe_queue_size())
    logger.info("interaction_writer_stopped queue_size=%s", safe_queue_size())


def safe_queue_size() -> int:
    try:
        return _QUEUE.qsize()
    except Exception:
        return -1


def _bucket(value: float) -> str:
    if value < 0.25:
        return "0.00-0.24"
    if value < 0.50:
        return "0.25-0.49"
    if value < 0.75:
        return "0.50-0.74"
    return "0.75-1.00"


def get_interaction_stats(*, days: int = 7, db_path: str = INTERACTION_DB_PATH) -> dict[str, Any]:
    """Return public-safe aggregate stats. No per-user rows or hashes are exposed."""
    days = max(1, min(int(days), 90))
    start = datetime.now(timezone.utc) - timedelta(days=days)
    start_iso = start.isoformat()
    try:
        conn = _connect(db_path)
        total_row = conn.execute("SELECT COUNT(*) AS c FROM interaction_events WHERE ts_utc >= ?", (start_iso,)).fetchone()
        total = int(total_row["c"] or 0)
        if total == 0:
            conn.close()
            return {
                "status": "ok",
                "period": f"last_{days}_days",
                "total_analyses": 0,
                "message": "No interaction stability analyses recorded in this period.",
                "privacy": {
                    "raw_text_stored": False,
                    "raw_api_keys_stored": False,
                    "public_stats_are_aggregated": True,
                },
            }

        avg_row = conn.execute(
            """
            SELECT
                AVG(conversation_turns) AS avg_conversation_turns,
                AVG(assistant_turns) AS avg_assistant_turns,
                AVG(final_sigma) AS avg_final_sigma,
                AVG(final_omega_t) AS avg_final_omega_t,
                AVG(demand_peak) AS avg_demand_peak,
                AVG(threshold_crossed) AS threshold_crossed_pct,
                AVG(stability_below_kappa) AS stability_below_kappa_pct,
                AVG(high_uncertainty) AS high_uncertainty_pct,
                AVG(latency_ms) AS avg_latency_ms
            FROM interaction_events
            WHERE ts_utc >= ?
            """,
            (start_iso,),
        ).fetchone()
        states = conn.execute(
            """
            SELECT final_dominant_state AS state, COUNT(*) AS count
            FROM interaction_events
            WHERE ts_utc >= ?
            GROUP BY final_dominant_state
            ORDER BY count DESC
            """,
            (start_iso,),
        ).fetchall()
        plans = conn.execute(
            """
            SELECT plan, COUNT(*) AS count
            FROM interaction_events
            WHERE ts_utc >= ?
            GROUP BY plan
            ORDER BY count DESC
            """,
            (start_iso,),
        ).fetchall()
        rows_for_buckets = conn.execute("SELECT final_sigma, demand_peak FROM interaction_events WHERE ts_utc >= ?", (start_iso,)).fetchall()
        conn.close()

        sigma_buckets: dict[str, int] = {}
        demand_buckets: dict[str, int] = {}
        for r in rows_for_buckets:
            sigma_buckets[_bucket(float(r["final_sigma"] or 0.0))] = sigma_buckets.get(_bucket(float(r["final_sigma"] or 0.0)), 0) + 1
            demand_buckets[_bucket(float(r["demand_peak"] or 0.0))] = demand_buckets.get(_bucket(float(r["demand_peak"] or 0.0)), 0) + 1

        def pct(v: Any) -> float:
            return round(float(v or 0.0), 4)

        return {
            "status": "ok",
            "period": f"last_{days}_days",
            "total_analyses": total,
            "avg_conversation_turns": round(float(avg_row["avg_conversation_turns"] or 0.0), 2),
            "avg_assistant_turns": round(float(avg_row["avg_assistant_turns"] or 0.0), 2),
            "avg_final_sigma": round(float(avg_row["avg_final_sigma"] or 0.0), 4),
            "avg_final_omega_t": round(float(avg_row["avg_final_omega_t"] or 0.0), 4),
            "avg_demand_peak": round(float(avg_row["avg_demand_peak"] or 0.0), 4),
            "threshold_crossed_pct": pct(avg_row["threshold_crossed_pct"]),
            "stability_below_kappa_pct": pct(avg_row["stability_below_kappa_pct"]),
            "high_uncertainty_pct": pct(avg_row["high_uncertainty_pct"]),
            "avg_latency_ms": round(float(avg_row["avg_latency_ms"] or 0.0), 2),
            "dominant_states_distribution": {str(r["state"] or "unknown"): int(r["count"] or 0) for r in states},
            "plan_distribution": {str(r["plan"] or "unknown"): int(r["count"] or 0) for r in plans},
            "sigma_buckets": sigma_buckets,
            "demand_peak_buckets": demand_buckets,
            "privacy": {
                "raw_text_stored": False,
                "raw_api_keys_stored": False,
                "public_stats_are_aggregated": True,
            },
        }
    except Exception as exc:
        logger.warning("interaction_stats_failed error=%s", exc)
        return {
            "status": "degraded",
            "period": f"last_{days}_days",
            "error": "interaction stats unavailable",
            "privacy": {
                "raw_text_stored": False,
                "raw_api_keys_stored": False,
                "public_stats_are_aggregated": True,
            },
        }
