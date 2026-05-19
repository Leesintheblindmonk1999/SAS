"""
app/services/rate_limit_store.py

Persistent SQLite-backed rate limiting for SAS.

E1 goals:
- Survive Render restarts.
- Never store raw IPs or raw API keys.
- Fail open if SQLite has an operational issue.
- Record allowed and blocked events for funnel/security observability.
- Keep database work off the event loop via asyncio.to_thread().
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("sas.rate_limit_store")

RATE_LIMIT_DB_PATH: str = os.getenv("RATE_LIMIT_DB_PATH", "/app/data/rate_limit.db")
RATE_LIMIT_HASH_PEPPER: str = os.getenv(
    "RATE_LIMIT_HASH_PEPPER",
    os.getenv("AUDIT_SALT_SECRET", "sas-rate-limit-dev-pepper"),
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def hash_rate_limit_key(key: str, scope: str) -> str:
    """
    Hash a rate-limit key for storage.

    The key may be a daily IP hash, an API key hash, or a synthetic bucket.
    Raw IPs/API keys should not be passed here.
    """
    clean_key = (key or "unknown").strip()
    clean_scope = (scope or "global").strip()
    material = f"{RATE_LIMIT_HASH_PEPPER}:{clean_scope}:{clean_key}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:24]


def _connect(path: str = RATE_LIMIT_DB_PATH) -> sqlite3.Connection:
    db_path = Path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path), timeout=5)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def init_rate_limit_db(path: str = RATE_LIMIT_DB_PATH) -> None:
    """Initialize persistent rate-limit database. Safe to call repeatedly."""
    conn = _connect(path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS rate_limit_events (
                id                    INTEGER PRIMARY KEY AUTOINCREMENT,
                ts_utc                TEXT NOT NULL,
                key                   TEXT NOT NULL,
                key_hash              TEXT NOT NULL,
                scope                 TEXT NOT NULL,
                path                  TEXT,
                method                TEXT,
                limit_count           INTEGER,
                window_seconds        INTEGER,
                current_count         INTEGER,
                allowed               INTEGER,
                retry_after_seconds   INTEGER,
                request_id            TEXT,
                country               TEXT
            )
            """
        )

        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_rate_limit_key_scope_ts "
            "ON rate_limit_events (key_hash, scope, ts_utc)"
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_rate_limit_ts ON rate_limit_events (ts_utc)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_rate_limit_allowed ON rate_limit_events (allowed)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_rate_limit_path ON rate_limit_events (path)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_rate_limit_scope ON rate_limit_events (scope)")
        conn.commit()
        logger.info("rate_limit_db_initialized path=%s", str(path))
    finally:
        conn.close()


def _check_persistent_rate_limit_sync(
    *,
    key: str,
    scope: str,
    limit: int,
    window_seconds: int,
    path: str | None = None,
    method: str | None = None,
    request_id: str | None = None,
    country: str | None = None,
    db_path: str = RATE_LIMIT_DB_PATH,
) -> dict[str, Any]:
    """
    Blocking implementation. Use check_persistent_rate_limit() from async code.
    """
    now = utc_now()
    now_iso = now.isoformat()
    window_start = (now - timedelta(seconds=int(window_seconds))).isoformat()

    safe_scope = scope or "global"
    safe_key_hash = hash_rate_limit_key(key, safe_scope)

    conn = _connect(db_path)
    try:
        # Count only allowed events. Blocked attempts should not inflate
        # the active window forever.
        row = conn.execute(
            """
            SELECT COUNT(*) AS c, MIN(ts_utc) AS oldest
            FROM rate_limit_events
            WHERE key_hash = ?
              AND scope = ?
              AND allowed = 1
              AND ts_utc >= ?
            """,
            (safe_key_hash, safe_scope, window_start),
        ).fetchone()

        current_count = int(row["c"] or 0)
        oldest = row["oldest"]

        allowed = current_count < int(limit)

        if allowed:
            count_after = current_count + 1
            retry_after = 0
        else:
            count_after = current_count
            retry_after = int(window_seconds)
            if oldest:
                try:
                    oldest_dt = datetime.fromisoformat(str(oldest))
                    reset_at = oldest_dt + timedelta(seconds=int(window_seconds))
                    retry_after = max(1, int((reset_at - now).total_seconds()))
                except Exception:
                    retry_after = int(window_seconds)

        conn.execute(
            """
            INSERT INTO rate_limit_events (
                ts_utc,
                key,
                key_hash,
                scope,
                path,
                method,
                limit_count,
                window_seconds,
                current_count,
                allowed,
                retry_after_seconds,
                request_id,
                country
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now_iso,
                "hashed",
                safe_key_hash,
                safe_scope,
                path,
                (method or "GET").upper(),
                int(limit),
                int(window_seconds),
                int(count_after),
                1 if allowed else 0,
                int(retry_after),
                request_id or "unknown",
                (country or "unknown").upper(),
            ),
        )
        conn.commit()

        return {
            "allowed": bool(allowed),
            "limit": int(limit),
            "window_seconds": int(window_seconds),
            "current_count": int(count_after),
            "retry_after_seconds": int(retry_after),
            "scope": safe_scope,
        }
    finally:
        conn.close()


async def check_persistent_rate_limit(
    key: str,
    scope: str,
    limit: int,
    window_seconds: int,
    path: str | None = None,
    method: str | None = None,
    request_id: str | None = None,
    country: str | None = None,
) -> dict[str, Any]:
    """
    Async fail-open persistent rate limit check.

    If rate_limit.db is unavailable, request is allowed and a warning is logged.
    This prevents hardening/observability failures from taking down the API.
    """
    try:
        return await asyncio.to_thread(
            _check_persistent_rate_limit_sync,
            key=key,
            scope=scope,
            limit=limit,
            window_seconds=window_seconds,
            path=path,
            method=method,
            request_id=request_id,
            country=country,
        )
    except Exception as exc:
        logger.warning(
            "rate_limit_store_failed_open scope=%s path=%s method=%s error=%s",
            scope,
            path,
            method,
            exc,
        )
        return {
            "allowed": True,
            "limit": int(limit),
            "window_seconds": int(window_seconds),
            "current_count": 0,
            "retry_after_seconds": 0,
            "scope": scope,
            "fail_open": True,
        }


def cleanup_old_rate_limit_events(
    retention_hours: int = 48,
    db_path: str = RATE_LIMIT_DB_PATH,
) -> int:
    """Delete old rate-limit events. Intended for startup maintenance."""
    cutoff = (utc_now() - timedelta(hours=int(retention_hours))).isoformat()

    conn = _connect(db_path)
    try:
        cur = conn.execute("DELETE FROM rate_limit_events WHERE ts_utc < ?", (cutoff,))
        conn.commit()
        deleted = int(cur.rowcount or 0)
        if deleted:
            logger.info("rate_limit_retention deleted_rows=%s", deleted)
        return deleted
    finally:
        conn.close()


def rate_limit_db_stats(db_path: str = RATE_LIMIT_DB_PATH) -> dict[str, Any]:
    """Lightweight readiness/statistics check. Does NOT call init — that is startup-only."""
    try:
        conn = _connect(db_path)
        row = conn.execute(
            """
            SELECT
                COUNT(*) AS total,
                MIN(ts_utc) AS oldest,
                MAX(ts_utc) AS newest,
                SUM(CASE WHEN allowed = 0 THEN 1 ELSE 0 END) AS blocked
            FROM rate_limit_events
            """
        ).fetchone()
        conn.close()

        return {
            "ok": True,
            "total_events": int(row["total"] or 0),
            "blocked_events": int(row["blocked"] or 0),
            "oldest": row["oldest"],
            "newest": row["newest"],
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
