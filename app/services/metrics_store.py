"""
app/services/metrics_store.py - SAS API metrics store

Admin-only operational metrics for SAS.

Design:
- SQLite local storage.
- No raw IP storage.
- No raw API key storage.
- Aggregated endpoint metrics for 24h / 7d / 30d.
- Public activity endpoints expose only anonymized aggregates.
"""

from __future__ import annotations

import hashlib
import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from app.config import settings


_DB_LOCK = threading.Lock()

NOISE_PATHS = (
    "/health",
    "/readyz",
    "/v1/metrics",
    "/favicon.ico",
    "/robots.txt",
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _db_path() -> Path:
    path = Path(getattr(settings, "metrics_db_path", "data/metrics.db"))
    if not path.is_absolute():
        path = Path.cwd() / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _auth_db_path() -> Path:
    path = Path(getattr(settings, "auth_db_path", "data/auth.db"))
    if not path.is_absolute():
        path = Path.cwd() / path
    return path


def _connect(path: Path | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path or _db_path()), timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def hash_api_key(api_key: str | None) -> str | None:
    if not api_key:
        return None
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def init_metrics_db() -> None:
    """Initialize metrics database. Safe to call on app startup."""
    with _DB_LOCK:
        conn = _connect()
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS api_request_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts_utc TEXT NOT NULL,
                    method TEXT NOT NULL,
                    path TEXT NOT NULL,
                    status_code INTEGER NOT NULL,
                    ok INTEGER NOT NULL,
                    ip_hash TEXT NOT NULL,
                    api_key_hash TEXT,
                    plan TEXT NOT NULL DEFAULT 'unknown',
                    latency_ms REAL,
                    request_id TEXT,
                    country TEXT
                )
                """
            )

            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_metrics_ts ON api_request_metrics(ts_utc)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_metrics_path_ts ON api_request_metrics(path, ts_utc)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_metrics_status_ts ON api_request_metrics(status_code, ts_utc)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_metrics_ip_ts ON api_request_metrics(ip_hash, ts_utc)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_metrics_plan_ts ON api_request_metrics(plan, ts_utc)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_metrics_key_ts ON api_request_metrics(api_key_hash, ts_utc)"
            )

            conn.commit()
        finally:
            conn.close()


def _resolve_plan(api_key_hash: str | None) -> str:
    """
    Resolve API key plan from auth.db when possible.

    Tolerates several possible schemas and fails safe as 'unknown'.
    """
    if not api_key_hash:
        return "anonymous"

    auth_path = _auth_db_path()
    if not auth_path.exists():
        return "unknown"

    try:
        conn = sqlite3.connect(str(auth_path), timeout=5)
        conn.row_factory = sqlite3.Row

        tables = [
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        ]

        candidate_tables = [
            table
            for table in tables
            if table.lower() in {"users", "api_keys", "keys", "auth_keys"}
        ]

        for table in candidate_tables:
            columns = {
                row["name"]
                for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
            }

            key_column = None
            for candidate in ("api_key_hash", "key_hash", "hash"):
                if candidate in columns:
                    key_column = candidate
                    break

            if not key_column:
                continue

            row = conn.execute(
                f"SELECT * FROM {table} WHERE {key_column} = ? LIMIT 1",
                (api_key_hash,),
            ).fetchone()

            if row is None:
                continue

            row_dict = dict(row)

            if "plan" in row_dict and row_dict["plan"]:
                return str(row_dict["plan"]).lower()

            if "tier" in row_dict and row_dict["tier"]:
                return str(row_dict["tier"]).lower()

            if "is_premium" in row_dict:
                return "pro" if int(row_dict["is_premium"]) == 1 else "free"

            if "premium" in row_dict:
                return "pro" if int(row_dict["premium"]) == 1 else "free"

            return "free"

        return "unknown"

    except Exception:
        return "unknown"
    finally:
        try:
            conn.close()
        except Exception:
            pass


def should_record_path(path: str) -> bool:
    """
    Decide whether to store this path in private admin metrics.

    Admin metrics keep /health because it helps detect uptime-check pressure.
    Public stats filter health/readiness later.
    """
    ignored_exact = {
        "/v1/metrics",
        "/favicon.ico",
    }

    if path in ignored_exact:
        return False

    ignored_prefixes = (
        "/static/",
        "/assets/",
    )

    return not path.startswith(ignored_prefixes)


def record_request_metric(
    *,
    method: str,
    path: str,
    status_code: int,
    ip_hash: str,
    api_key: str | None,
    latency_ms: float | None,
    request_id: str | None,
    country: str | None = None,
) -> None:
    """
    Store a single request metric.

    Important:
    - Stores api_key_hash only.
    - Stores ip_hash only.
    - Never stores raw IP.
    - Never stores raw API key.
    """
    if not should_record_path(path):
        return

    api_key_hash = hash_api_key(api_key)
    plan = _resolve_plan(api_key_hash)
    ok = 1 if 200 <= int(status_code) < 400 else 0

    with _DB_LOCK:
        conn = _connect()
        try:
            conn.execute(
                """
                INSERT INTO api_request_metrics (
                    ts_utc,
                    method,
                    path,
                    status_code,
                    ok,
                    ip_hash,
                    api_key_hash,
                    plan,
                    latency_ms,
                    request_id,
                    country
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    _utc_now().isoformat(),
                    method.upper(),
                    path,
                    int(status_code),
                    ok,
                    ip_hash,
                    api_key_hash,
                    plan,
                    latency_ms,
                    request_id,
                    country or "unknown",
                ),
            )
            conn.commit()
        finally:
            conn.close()


def _window_to_timedelta(window: str) -> timedelta:
    normalized = window.lower().strip()

    if normalized in {"24h", "1d"}:
        return timedelta(hours=24)
    if normalized == "7d":
        return timedelta(days=7)
    if normalized == "30d":
        return timedelta(days=30)

    raise ValueError("Invalid window. Use one of: 24h, 7d, 30d")


def get_metrics_summary(window: str = "24h") -> dict[str, Any]:
    delta = _window_to_timedelta(window)
    now = _utc_now()
    since = now - delta

    conn = _connect()
    try:
        params = (since.isoformat(),)

        totals = conn.execute(
            """
            SELECT
                COUNT(*) AS total_requests,
                SUM(CASE WHEN status_code BETWEEN 200 AND 399 THEN 1 ELSE 0 END) AS successful_requests,
                SUM(CASE WHEN status_code BETWEEN 400 AND 499 THEN 1 ELSE 0 END) AS client_errors_4xx,
                SUM(CASE WHEN status_code >= 500 THEN 1 ELSE 0 END) AS server_errors_5xx,
                COUNT(DISTINCT ip_hash) AS unique_ip_hashes,
                COUNT(DISTINCT api_key_hash) AS unique_api_keys,
                AVG(latency_ms) AS avg_latency_ms
            FROM api_request_metrics
            WHERE ts_utc >= ?
            """,
            params,
        ).fetchone()

        by_endpoint = conn.execute(
            """
            SELECT
                path,
                COUNT(*) AS total_requests,
                SUM(CASE WHEN status_code BETWEEN 200 AND 399 THEN 1 ELSE 0 END) AS successful_requests,
                SUM(CASE WHEN status_code BETWEEN 400 AND 499 THEN 1 ELSE 0 END) AS client_errors_4xx,
                SUM(CASE WHEN status_code >= 500 THEN 1 ELSE 0 END) AS server_errors_5xx,
                COUNT(DISTINCT ip_hash) AS unique_ip_hashes,
                AVG(latency_ms) AS avg_latency_ms
            FROM api_request_metrics
            WHERE ts_utc >= ?
            GROUP BY path
            ORDER BY total_requests DESC
            """,
            params,
        ).fetchall()

        by_plan = conn.execute(
            """
            SELECT
                plan,
                COUNT(*) AS total_requests,
                SUM(CASE WHEN status_code BETWEEN 200 AND 399 THEN 1 ELSE 0 END) AS successful_requests,
                SUM(CASE WHEN status_code BETWEEN 400 AND 499 THEN 1 ELSE 0 END) AS client_errors_4xx,
                SUM(CASE WHEN status_code >= 500 THEN 1 ELSE 0 END) AS server_errors_5xx,
                COUNT(DISTINCT ip_hash) AS unique_ip_hashes,
                COUNT(DISTINCT api_key_hash) AS unique_api_keys,
                AVG(latency_ms) AS avg_latency_ms
            FROM api_request_metrics
            WHERE ts_utc >= ?
            GROUP BY plan
            ORDER BY total_requests DESC
            """,
            params,
        ).fetchall()

        status_buckets = conn.execute(
            """
            SELECT
                CASE
                    WHEN status_code BETWEEN 200 AND 299 THEN '2xx'
                    WHEN status_code BETWEEN 300 AND 399 THEN '3xx'
                    WHEN status_code BETWEEN 400 AND 499 THEN '4xx'
                    WHEN status_code >= 500 THEN '5xx'
                    ELSE 'other'
                END AS bucket,
                COUNT(*) AS total
            FROM api_request_metrics
            WHERE ts_utc >= ?
            GROUP BY bucket
            ORDER BY bucket
            """,
            params,
        ).fetchall()

        top_countries = conn.execute(
            """
            SELECT
                country,
                COUNT(*) AS total_requests,
                COUNT(DISTINCT ip_hash) AS unique_ip_hashes
            FROM api_request_metrics
            WHERE ts_utc >= ?
            GROUP BY country
            ORDER BY total_requests DESC
            LIMIT 15
            """,
            params,
        ).fetchall()

        def row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
            result = dict(row)
            if result.get("avg_latency_ms") is not None:
                result["avg_latency_ms"] = round(float(result["avg_latency_ms"]), 2)
            return result

        total_dict = row_to_dict(totals)

        return {
            "status": "ok",
            "window": window,
            "since_utc": since.isoformat(),
            "until_utc": now.isoformat(),
            "totals": {
                "total_requests": int(total_dict.get("total_requests") or 0),
                "successful_requests": int(total_dict.get("successful_requests") or 0),
                "client_errors_4xx": int(total_dict.get("client_errors_4xx") or 0),
                "server_errors_5xx": int(total_dict.get("server_errors_5xx") or 0),
                "unique_ip_hashes": int(total_dict.get("unique_ip_hashes") or 0),
                "unique_api_keys": int(total_dict.get("unique_api_keys") or 0),
                "avg_latency_ms": total_dict.get("avg_latency_ms"),
            },
            "by_endpoint": [row_to_dict(row) for row in by_endpoint],
            "by_plan": [row_to_dict(row) for row in by_plan],
            "status_buckets": [row_to_dict(row) for row in status_buckets],
            "top_countries": [row_to_dict(row) for row in top_countries],
            "privacy": {
                "raw_ips_exposed": False,
                "raw_api_keys_exposed": False,
                "api_key_hashes_exposed": False,
                "only_aggregates_returned": True,
            },
        }
    finally:
        conn.close()


def purge_old_metrics() -> int:
    """
    Optional cleanup. Call manually or on startup.
    """
    retention_days = int(getattr(settings, "metrics_retention_days", 90))
    cutoff = _utc_now() - timedelta(days=retention_days)

    with _DB_LOCK:
        conn = _connect()
        try:
            cur = conn.execute(
                "DELETE FROM api_request_metrics WHERE ts_utc < ?",
                (cutoff.isoformat(),),
            )
            conn.commit()
            return int(cur.rowcount or 0)
        finally:
            conn.close()


def _noise_filter_clause() -> tuple[str, tuple[str, ...]]:
    placeholders = ",".join("?" for _ in NOISE_PATHS)
    return f"path NOT IN ({placeholders})", NOISE_PATHS


def _bucket_time(ts_utc: str) -> str:
    """
    Return approximate UTC timestamp rounded to 10-minute bucket.
    """
    try:
        dt = datetime.fromisoformat(ts_utc)
        minute_bucket = (dt.minute // 10) * 10
        bucketed = dt.replace(minute=minute_bucket, second=0, microsecond=0)
        return bucketed.isoformat()
    except Exception:
        return "unknown"


def get_public_activity(limit: int = 100) -> dict[str, Any]:
    """
    Public anonymized activity feed.

    Does not expose:
    - raw IPs
    - ip_hashes
    - API keys
    - API key hashes
    - request IDs
    """
    safe_limit = max(1, min(int(limit), 100))
    noise_clause, noise_params = _noise_filter_clause()

    conn = _connect()
    try:
        rows = conn.execute(
            f"""
            SELECT
                ts_utc,
                method,
                path,
                status_code,
                country
            FROM api_request_metrics
            WHERE {noise_clause}
            ORDER BY ts_utc DESC
            LIMIT ?
            """,
            (*noise_params, safe_limit),
        ).fetchall()

        events = []
        for row in rows:
            status_code = int(row["status_code"])
            if 200 <= status_code <= 299:
                status_bucket = "2xx"
            elif 300 <= status_code <= 399:
                status_bucket = "3xx"
            elif 400 <= status_code <= 499:
                status_bucket = "4xx"
            elif status_code >= 500:
                status_bucket = "5xx"
            else:
                status_bucket = "other"

            events.append(
                {
                    "time_bucket_utc": _bucket_time(row["ts_utc"]),
                    "method": row["method"],
                    "path": row["path"],
                    "status_bucket": status_bucket,
                    "country": row["country"] or "unknown",
                }
            )

        return {
            "status": "ok",
            "limit": safe_limit,
            "events": events,
            "privacy": {
                "raw_ips_exposed": False,
                "ip_hashes_exposed": False,
                "raw_api_keys_exposed": False,
                "api_key_hashes_exposed": False,
                "request_ids_exposed": False,
            },
        }
    finally:
        conn.close()


def get_public_stats() -> dict[str, Any]:
    """
    Public aggregate stats for landing page and README automation.

    Safe for browser fetch.
    """
    now = _utc_now()
    since_7d = now - timedelta(days=7)
    since_24h = now - timedelta(hours=24)
    noise_clause, noise_params = _noise_filter_clause()

    conn = _connect()
    try:
        totals_24h = conn.execute(
            f"""
            SELECT
                COUNT(*) AS total_requests,
                SUM(CASE WHEN status_code BETWEEN 200 AND 399 THEN 1 ELSE 0 END) AS successful_requests,
                SUM(CASE WHEN status_code BETWEEN 400 AND 499 THEN 1 ELSE 0 END) AS client_errors_4xx,
                SUM(CASE WHEN status_code >= 500 THEN 1 ELSE 0 END) AS server_errors_5xx,
                COUNT(DISTINCT ip_hash) AS unique_users
            FROM api_request_metrics
            WHERE ts_utc >= ? AND {noise_clause}
            """,
            (since_24h.isoformat(), *noise_params),
        ).fetchone()

        total_7d = conn.execute(
            f"""
            SELECT COUNT(*) AS total
            FROM api_request_metrics
            WHERE ts_utc >= ? AND {noise_clause}
            """,
            (since_7d.isoformat(), *noise_params),
        ).fetchone()["total"]

        countries = conn.execute(
            f"""
            SELECT country, COUNT(*) AS total
            FROM api_request_metrics
            WHERE ts_utc >= ? AND {noise_clause}
            GROUP BY country
            ORDER BY total DESC
            LIMIT 10
            """,
            (since_24h.isoformat(), *noise_params),
        ).fetchall()

        country_rows = []
        top_country = "unknown"
        top_country_total = 0

        for row in countries:
            country = row["country"] or "unknown"
            total = int(row["total"] or 0)

            country_rows.append(
                {
                    "country": country,
                    "total_requests": total,
                }
            )

            if total > top_country_total:
                top_country = country
                top_country_total = total

        anomaly_threshold = int(getattr(settings, "public_anomaly_threshold", 5000))

        anomaly = {
            "active": top_country_total >= anomaly_threshold,
            "signal": "traffic_anomaly_detected"
            if top_country_total >= anomaly_threshold
            else "normal_public_activity",
            "top_country": top_country,
            "top_country_requests_24h": top_country_total,
            "threshold": anomaly_threshold,
        }

        return {
            "status": "ok",
            "window_24h": {
                "total_requests": int(totals_24h["total_requests"] or 0),
                "successful_requests": int(totals_24h["successful_requests"] or 0),
                "client_errors_4xx": int(totals_24h["client_errors_4xx"] or 0),
                "server_errors_5xx": int(totals_24h["server_errors_5xx"] or 0),
                "unique_users": int(totals_24h["unique_users"] or 0),
                "countries": country_rows,
            },
            "window_7d": {
                "total_requests": int(total_7d or 0),
            },
            "monitoring_signal": anomaly,
            "privacy": {
                "only_aggregates": True,
                "raw_ips_exposed": False,
                "ip_hashes_exposed": False,
                "api_keys_exposed": False,
                "api_key_hashes_exposed": False,
            },
        }
    finally:
        conn.close()
