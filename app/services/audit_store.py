"""
app/services/audit_store.py — SAS Persistent Audit Store
═══════════════════════════════════════════════════════════

Persistent, sovereign audit log for SAS API traffic.

Design decisions:
- In-memory queue + background writer thread: low latency impact on API.
- WAL mode: concurrent reads while writing.
- Batched SQLite inserts: lower write overhead under moderate traffic.
- Daily salted IP hash: improves unlinkability across days.
- Path normalization: reduces cardinality for historical analysis.
- Graceful degradation: audit failures never affect API responses.

Important behavior:
- If the queue is full, new events are dropped (not the oldest).
- The API response path is never blocked by SQLite writes.
- The middleware reads request.state.request_id if available; it does not create
  a second request_id that would diverge from metrics.db.

Registry: TAD EX-2026-18792778
Author: Gonzalo Emir Durante
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import queue
import sqlite3
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, NamedTuple

from fastapi import Request

logger = logging.getLogger("sas.audit_store")

# ==============================================================================
# CONFIG
# ==============================================================================

AUDIT_DB_PATH: str = os.getenv("AUDIT_DB_PATH", "/app/data/audit.db")

QUEUE_MAXSIZE = int(os.getenv("AUDIT_QUEUE_MAXSIZE", "10000"))
BATCH_SIZE = int(os.getenv("AUDIT_BATCH_SIZE", "50"))
FLUSH_INTERVAL_SECONDS = float(os.getenv("AUDIT_FLUSH_INTERVAL_SECONDS", "2.0"))

# Daily salt rotates at UTC midnight. This improves unlinkability across days.
_SALT_DATE: str = ""
_SALT_VALUE: str = ""

# In-memory queue. Events are written by a background thread, not the event loop.
# If the queue is full, new events are dropped (not the oldest).
_QUEUE: queue.Queue = queue.Queue(maxsize=QUEUE_MAXSIZE)

_WRITER_THREAD: threading.Thread | None = None
_SHUTDOWN = threading.Event()

# Paths that carry little analytical product value.
_INFRA_PATHS = frozenset(
    {
        "/health",
        "/readyz",
        "/robots.txt",
        "/favicon.ico",
        "/",
    }
)


# ==============================================================================
# EVENT MODEL
# ==============================================================================


class AuditEvent(NamedTuple):
    ts_utc: str
    ip_hash: str
    country: str
    method: str
    path: str
    path_prefix: str
    status_code: int
    status_class: str
    latency_ms: float
    request_id: str
    is_infra: int


# ==============================================================================
# IP HASHING
# ==============================================================================


def _daily_salt() -> str:
    """
    Return a daily salt derived from the UTC date.

    AUDIT_SALT_SECRET should be configured in production. If it is missing,
    a development fallback is used and a warning is emitted.

    Daily salt makes IP hashes non-linkable across different UTC days unless
    the operator has the original IP and the salt secret.
    """
    global _SALT_DATE, _SALT_VALUE

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if today != _SALT_DATE:
        _SALT_DATE = today

        secret = os.getenv("AUDIT_SALT_SECRET")
        if not secret:
            logger.warning(
                "AUDIT_SALT_SECRET is not set; using development fallback salt. "
                "Set AUDIT_SALT_SECRET in production."
            )
            secret = "sas-audit-salt-v1"

        _SALT_VALUE = hashlib.sha256(f"{secret}:{today}".encode("utf-8")).hexdigest()[:16]

    return _SALT_VALUE


def hash_ip_daily(ip: str) -> str:
    """
    Hash an IP with the current UTC daily salt.

    Returns a short pseudonymous hash. The raw IP is never stored.
    """
    salt = _daily_salt()
    normalized_ip = (ip or "unknown").strip()
    return hashlib.sha256(f"{salt}:{normalized_ip}".encode("utf-8")).hexdigest()[:16]


# ==============================================================================
# SCHEMA
# ==============================================================================


def init_audit_db(path: str = AUDIT_DB_PATH) -> None:
    """
    Initialize audit.db with WAL mode and required schema.

    Safe to call multiple times.
    Also starts the background writer thread.
    """
    db_path = Path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path), timeout=5)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA busy_timeout=5000")

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_events (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                ts_utc       TEXT    NOT NULL,
                ip_hash      TEXT,
                country      TEXT,
                method       TEXT,
                path         TEXT,
                path_prefix  TEXT,
                status_code  INTEGER,
                status_class TEXT,
                latency_ms   REAL,
                request_id   TEXT,
                is_infra     INTEGER DEFAULT 0
            )
            """
        )

        conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_ts ON audit_events (ts_utc)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_country ON audit_events (country)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_prefix ON audit_events (path_prefix)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_status ON audit_events (status_code)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_status_class ON audit_events (status_class)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_infra_ts ON audit_events (is_infra, ts_utc)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_request_id ON audit_events (request_id)")

        conn.commit()
        logger.info("audit_db_initialized path=%s", str(db_path))
    finally:
        conn.close()

    _start_writer(str(db_path))


# ==============================================================================
# NORMALIZATION HELPERS
# ==============================================================================


def _normalize_path(path: str) -> str:
    """
    Return a normalized path prefix for grouping.

    Examples:
    - /v1/diff -> /v1/diff
    - /public/demo/audit -> /public/demo
    - /public/request-key -> /public/request-key
    - /billing/polar/webhook -> /billing/polar
    - /admin/generate-key -> /admin
    """
    clean = (path or "/").split("?")[0].rstrip("/") or "/"

    if clean in _INFRA_PATHS:
        return clean

    parts = clean.split("/")

    if len(parts) <= 2:
        return clean

    if parts[1] == "public":
        if len(parts) >= 4 and parts[2] == "demo":
            return "/public/demo"
        if len(parts) >= 3 and parts[2] == "request-key":
            return "/public/request-key"
        return "/".join(parts[:3]) or "/public"

    if parts[1] == "v1":
        return "/".join(parts[:3]) or "/v1"

    if parts[1] == "billing":
        return "/".join(parts[:3]) or "/billing"

    if parts[1] == "admin":
        return "/admin"

    return "/".join(parts[:3]) or clean


def _status_class(code: int) -> str:
    if code < 300:
        return "2xx"
    if code < 400:
        return "3xx"
    if code < 500:
        return "4xx"
    return "5xx"


def _client_ip_from_request(request: Request) -> str:
    """
    Extract client IP using common proxy headers.

    This intentionally stores only a derived hash later, never the raw IP.
    """
    headers = request.headers

    candidates = [
        headers.get("true-client-ip"),
        headers.get("cf-connecting-ip"),
        headers.get("x-real-ip"),
        headers.get("x-forwarded-for", "").split(",")[0].strip()
        if headers.get("x-forwarded-for")
        else None,
    ]

    for candidate in candidates:
        if candidate:
            return candidate.strip()

    if request.client and request.client.host:
        return request.client.host

    return "unknown"


def _country_from_request(request: Request) -> str:
    """
    Extract country bucket from common infrastructure headers.
    """
    return (
        request.headers.get("cf-ipcountry")
        or request.headers.get("x-vercel-ip-country")
        or request.headers.get("x-country")
        or "unknown"
    )


# ==============================================================================
# ENQUEUE
# ==============================================================================


def enqueue_audit_event(
    ip: str,
    country: str,
    method: str,
    path: str,
    status_code: int,
    latency_ms: float,
    request_id: str,
) -> None:
    """
    Non-blocking: enqueue an audit event for background writing.

    Never raises. Audit logging must not affect API responses.
    """
    try:
        event = AuditEvent(
            ts_utc=datetime.now(timezone.utc).isoformat(),
            ip_hash=hash_ip_daily(ip),
            country=(country or "unknown").upper(),
            method=(method or "GET").upper(),
            path=path or "/",
            path_prefix=_normalize_path(path or "/"),
            status_code=int(status_code),
            status_class=_status_class(int(status_code)),
            latency_ms=round(float(latency_ms), 2),
            request_id=request_id or "unknown",
            is_infra=1 if (path or "/") in _INFRA_PATHS else 0,
        )

        _QUEUE.put_nowait(event)

    except queue.Full:
        logger.warning(
            "audit_queue_full dropping_new_event method=%s path=%s status=%s",
            method,
            path,
            status_code,
        )
    except Exception as exc:
        logger.warning("audit_enqueue_failed error=%s", exc)


# ==============================================================================
# BACKGROUND WRITER
# ==============================================================================


_INSERT_SQL = """
    INSERT INTO audit_events (
        ts_utc, ip_hash, country, method, path, path_prefix,
        status_code, status_class, latency_ms, request_id, is_infra
    ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
"""


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, timeout=5)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def _flush_batch(
    conn: sqlite3.Connection | None,
    db_path: str,
    batch: list[AuditEvent],
) -> sqlite3.Connection | None:
    """
    Flush a batch to SQLite.

    If conn is None, creates a new connection. Returns the active connection.
    Keeps the caller responsible for clearing the batch only after success.
    """
    if not batch:
        return conn

    if conn is None:
        conn = _connect(db_path)

    conn.executemany(_INSERT_SQL, batch)
    conn.commit()
    return conn


def _drain_queue_into(batch: list[AuditEvent], limit: int | None = None) -> None:
    """
    Drain queued events into an existing batch without blocking.
    """
    while limit is None or len(batch) < limit:
        try:
            batch.append(_QUEUE.get_nowait())
        except queue.Empty:
            break


def _writer_loop(db_path: str) -> None:
    """
    Background thread: drains the queue and writes to SQLite in batches.
    """
    conn: sqlite3.Connection | None = None
    batch: list[AuditEvent] = []
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
            len(batch) >= BATCH_SIZE
            or (time.monotonic() - last_flush >= FLUSH_INTERVAL_SECONDS)
        )

        if should_flush:
            try:
                conn = _flush_batch(conn, db_path, batch)
                batch.clear()
                last_flush = time.monotonic()
            except Exception as exc:
                logger.error("audit_writer_failed error=%s", exc)
                try:
                    if conn:
                        conn.close()
                except Exception:
                    pass
                conn = None
                # Keep the batch for retry on the next loop.

    # Shutdown path:
    # 1. Drain remaining queued events.
    # 2. Flush even if conn is None by creating a new connection.
    try:
        _drain_queue_into(batch, None)

        if batch:
            conn = _flush_batch(conn, db_path, batch)
            batch.clear()

    except Exception as exc:
        logger.error("audit_shutdown_flush_failed error=%s remaining_events=%d", exc, len(batch))

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
        name="sas-audit-writer",
        daemon=True,
    )
    _WRITER_THREAD.start()

    logger.info("audit_writer_started db=%s", db_path)


def stop_writer() -> None:
    """
    Stop the writer thread and flush remaining queued/batched events.

    Call from FastAPI shutdown.
    """
    _SHUTDOWN.set()

    if _WRITER_THREAD:
        _WRITER_THREAD.join(timeout=5)

        if _WRITER_THREAD.is_alive():
            logger.warning("audit_writer_stop_timeout queue_size=%s", safe_queue_size())

    logger.info("audit_writer_stopped queue_size=%s", safe_queue_size())


def safe_queue_size() -> int:
    try:
        return _QUEUE.qsize()
    except Exception:
        return -1


# ==============================================================================
# FASTAPI MIDDLEWARE
# ==============================================================================


async def audit_middleware(request: Request, call_next: Any):
    """
    FastAPI middleware for persistent audit logging.

    Important:
    - Does not generate request_id.
    - Reads request.state.request_id if already assigned by request monitoring.
    - Uses enqueue_audit_event(), never SQLite directly.
    - Captures status_code even when downstream raises.
    - Never blocks the request path with database IO.
    """
    start = time.perf_counter()

    method = request.method
    path = request.url.path
    country = _country_from_request(request)
    client_ip = _client_ip_from_request(request)

    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code
        return response

    except Exception:
        status_code = 500
        raise

    finally:
        # Yield once to the event loop without blocking.
        await asyncio.sleep(0.0)

        latency_ms = (time.perf_counter() - start) * 1000
        request_id = getattr(request.state, "request_id", "unknown")

        enqueue_audit_event(
            ip=client_ip,
            country=country,
            method=method,
            path=path,
            status_code=status_code,
            latency_ms=latency_ms,
            request_id=request_id,
        )


# ==============================================================================
# GDPR / PRIVACY HELPERS
# ==============================================================================


def delete_audit_day(date_str: str, db_path: str = AUDIT_DB_PATH) -> int:
    """
    Conservatively delete all audit events for a UTC day (YYYY-MM-DD).

    Privacy note:
    The preferred precise erasure workflow is to recompute the daily hash for a
    known source IP + date range using AUDIT_SALT_SECRET, then delete only those
    matching hashes. Because raw IPs are not stored, this function provides a
    conservative fallback: delete an entire UTC day when a broad erasure action
    is required and precise hash reconstruction is not possible.

    Returns number of rows deleted.
    """
    conn = sqlite3.connect(db_path, timeout=5)
    try:
        cur = conn.execute(
            "DELETE FROM audit_events WHERE ts_utc LIKE ?",
            (f"{date_str}%",),
        )
        conn.commit()
        deleted = int(cur.rowcount or 0)
        logger.info("audit_day_erasure date=%s deleted=%d", date_str, deleted)
        return deleted
    finally:
        conn.close()


def delete_audit_ip_for_day(ip: str, date_str: str, db_path: str = AUDIT_DB_PATH) -> int:
    """
    Delete audit events for a known raw IP on a specific UTC day.

    This function temporarily reconstructs the daily salted hash without storing
    the raw IP. It requires AUDIT_SALT_SECRET to be the same secret used on that
    day.
    """
    secret = os.getenv("AUDIT_SALT_SECRET")
    if not secret:
        raise RuntimeError("AUDIT_SALT_SECRET is required for precise IP erasure.")

    salt = hashlib.sha256(f"{secret}:{date_str}".encode("utf-8")).hexdigest()[:16]
    ip_hash = hashlib.sha256(f"{salt}:{ip.strip()}".encode("utf-8")).hexdigest()[:16]

    conn = sqlite3.connect(db_path, timeout=5)
    try:
        cur = conn.execute(
            "DELETE FROM audit_events WHERE ts_utc LIKE ? AND ip_hash = ?",
            (f"{date_str}%", ip_hash),
        )
        conn.commit()
        deleted = int(cur.rowcount or 0)
        logger.info("audit_ip_day_erasure date=%s deleted=%d", date_str, deleted)
        return deleted
    finally:
        conn.close()


def audit_db_stats(db_path: str = AUDIT_DB_PATH) -> dict[str, Any]:
    """
    Return row count and date range.

    Useful for /readyz or admin endpoints.
    """
    try:
        conn = sqlite3.connect(db_path, timeout=2)
        conn.row_factory = sqlite3.Row

        row = conn.execute(
            "SELECT COUNT(*) AS total, MIN(ts_utc) AS oldest, MAX(ts_utc) AS newest FROM audit_events"
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
