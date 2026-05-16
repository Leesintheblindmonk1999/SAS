"""
app/db/auth_store.py - SAS users, API keys, usage and billing SQLite layer.

Design goals:
- SQLite only, no ORM.
- API keys are hashed before storage.
- Prompt/body text is never stored.
- Usage logs store only metadata.
- Compatible with the existing SAS app/db package.
"""

from __future__ import annotations

import hashlib
import json
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import settings


class RateLimitError(Exception):
    """Raised when a public key request exceeds the allowed frequency."""


class AuthStoreError(Exception):
    """Raised for unexpected auth-store errors."""


# ==============================================================================
# TIME + HASH HELPERS
# ==============================================================================


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def utc_day() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def utc_month() -> str:
    now = datetime.now(timezone.utc)
    return f"{now.year:04d}-{now.month:02d}"


def normalize_email(email: str) -> str:
    return email.strip().lower()


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _pepper() -> str:
    return getattr(settings, "api_key_hash_pepper", "sas-dev-pepper-change-me")


def hash_email(email: str) -> str:
    return sha256_hex(normalize_email(email) + ":" + _pepper())


def hash_api_key(api_key: str) -> str:
    return sha256_hex(api_key.strip() + ":" + _pepper())


def generate_api_key(plan: str = "free") -> str:
    prefix = {
        "free": "sas_free_",
        "pro": "sas_pro_",
        "developer": "sas_pro_",
        "team": "sas_team_",
        "enterprise": "sas_ent_",
        "legacy": "sas_legacy_",
    }.get((plan or "free").lower(), "sas_key_")

    token = secrets.token_urlsafe(32).replace("-", "").replace("_", "")
    return f"{prefix}{token}"


def plan_limits(plan: str) -> dict[str, int | None]:
    plan = (plan or "free").lower()

    if plan == "free":
        return {
            "daily_limit": int(getattr(settings, "free_requests_per_day", 50)),
            "monthly_limit": None,
        }

    if plan in {"pro", "developer"}:
        return {
            "daily_limit": None,
            "monthly_limit": int(getattr(settings, "pro_requests_per_month", 10000)),
        }

    if plan == "team":
        return {
            "daily_limit": None,
            "monthly_limit": int(getattr(settings, "team_requests_per_month", 50000)),
        }

    if plan == "enterprise":
        return {
            "daily_limit": None,
            "monthly_limit": None,
        }

    if plan == "legacy":
        return {
            "daily_limit": int(getattr(settings, "legacy_requests_per_day", 5)),
            "monthly_limit": None,
        }

    return {
        "daily_limit": int(getattr(settings, "free_requests_per_day", 50)),
        "monthly_limit": None,
    }


# ==============================================================================
# CONNECTION + TABLES
# ==============================================================================


def _db_path() -> Path:
    return Path(getattr(settings, "auth_db_path", "data/auth.db"))


def connect() -> sqlite3.Connection:
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(path), timeout=20)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return dict(row)


def init_auth_db() -> None:
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                email_hash TEXT NOT NULL UNIQUE,
                name TEXT,
                api_key_hash TEXT UNIQUE,
                plan TEXT NOT NULL DEFAULT 'free',
                status TEXT NOT NULL DEFAULT 'active',
                daily_limit INTEGER,
                monthly_limit INTEGER,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                last_key_issued_at TEXT,
                polar_customer_id TEXT,
                polar_subscription_id TEXT
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS api_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                email_hash TEXT,
                plan TEXT,
                method TEXT,
                path TEXT,
                status_code INTEGER,
                request_id TEXT,
                day TEXT NOT NULL,
                month TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS request_key_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email_hash TEXT NOT NULL,
                ip_hash TEXT NOT NULL,
                day TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )


        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS request_key_failed_attempts (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at    TEXT NOT NULL,
                ip_hash       TEXT,
                reason        TEXT,
                email_present INTEGER DEFAULT 0,
                name_present  INTEGER DEFAULT 0,
                status        TEXT DEFAULT 'failed_validation'
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider TEXT NOT NULL,
                event_type TEXT,
                external_id TEXT,
                email TEXT,
                email_hash TEXT,
                user_id INTEGER,
                plan TEXT,
                status TEXT,
                raw_json TEXT,
                created_at TEXT NOT NULL,
                processed_at TEXT,
                UNIQUE(provider, external_id),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )

        conn.execute("CREATE INDEX IF NOT EXISTS idx_users_key ON users(api_key_hash)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_usage_user_day ON api_usage(user_id, day)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_usage_user_month ON api_usage(user_id, month)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_attempt_email_day ON request_key_attempts(email_hash, day)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_attempt_ip_day ON request_key_attempts(ip_hash, day)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_failed_attempt_ip ON request_key_failed_attempts(ip_hash)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_failed_attempt_created ON request_key_failed_attempts(created_at)")

        _ensure_legacy_key(conn)


def _ensure_legacy_key(conn: sqlite3.Connection) -> None:
    """
    Preserve compatibility with the existing sas_test_key_2026 workflow.

    The legacy key is kept only as a shared compatibility/demo key.
    It is limited by settings.legacy_requests_per_day and should not be used
    as a normal production API key.
    """
    legacy_key = getattr(settings, "legacy_bootstrap_api_key", "sas_test_key_2026").strip()
    if not legacy_key:
        return

    key_hash = hash_api_key(legacy_key)
    limits = plan_limits("legacy")

    row = conn.execute(
        "SELECT id FROM users WHERE api_key_hash = ?",
        (key_hash,),
    ).fetchone()

    if row:
        conn.execute(
            """
            UPDATE users
            SET plan = 'legacy',
                status = 'active',
                daily_limit = ?,
                monthly_limit = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                limits["daily_limit"],
                limits["monthly_limit"],
                utc_now(),
                row["id"],
            ),
        )
        return

    email = "legacy@sas.local"
    email_h = hash_email(email)
    now = utc_now()

    existing = conn.execute(
        "SELECT id FROM users WHERE email = ?",
        (email,),
    ).fetchone()

    if existing:
        conn.execute(
            """
            UPDATE users
            SET api_key_hash = ?,
                plan = 'legacy',
                status = 'active',
                daily_limit = ?,
                monthly_limit = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                key_hash,
                limits["daily_limit"],
                limits["monthly_limit"],
                now,
                existing["id"],
            ),
        )
        return

    conn.execute(
        """
        INSERT INTO users(
            email,
            email_hash,
            name,
            api_key_hash,
            plan,
            status,
            daily_limit,
            monthly_limit,
            created_at,
            updated_at,
            last_key_issued_at
        )
        VALUES (?, ?, 'Legacy SAS Key', ?, 'legacy', 'active', ?, ?, ?, ?, ?)
        """,
        (
            email,
            email_h,
            key_hash,
            limits["daily_limit"],
            limits["monthly_limit"],
            now,
            now,
            now,
        ),
    )


# ==============================================================================
# USERS + KEYS
# ==============================================================================


def get_user_by_email(email: str) -> dict[str, Any] | None:
    email = normalize_email(email)
    with connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    return row_to_dict(row)


def get_user_by_id(user_id: int) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return row_to_dict(row)


def get_user_by_api_key(api_key: str) -> dict[str, Any] | None:
    if not api_key or not api_key.strip():
        return None

    key_hash = hash_api_key(api_key)
    with connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE api_key_hash = ?", (key_hash,)).fetchone()
    return row_to_dict(row)


def ensure_user(email: str, name: str | None = None) -> dict[str, Any]:
    email = normalize_email(email)
    email_h = hash_email(email)
    now = utc_now()
    limits = plan_limits("free")

    with connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if row:
            if name and not row["name"]:
                conn.execute(
                    "UPDATE users SET name = ?, updated_at = ? WHERE id = ?",
                    (name, now, row["id"]),
                )
            return get_user_by_email(email) or dict(row)

        conn.execute(
            """
            INSERT INTO users(
                email, email_hash, name, plan, status,
                daily_limit, monthly_limit, created_at, updated_at
            )
            VALUES (?, ?, ?, 'free', 'active', ?, ?, ?, ?)
            """,
            (
                email,
                email_h,
                name,
                limits["daily_limit"],
                limits["monthly_limit"],
                now,
                now,
            ),
        )

    user = get_user_by_email(email)
    if not user:
        raise AuthStoreError("Failed to create user")
    return user


def count_key_attempts(email_hash: str, ip_hash: str, day: str) -> dict[str, int]:
    with connect() as conn:
        email_count = conn.execute(
            """
            SELECT COUNT(*) AS c
            FROM request_key_attempts
            WHERE email_hash = ? AND day = ?
            """,
            (email_hash, day),
        ).fetchone()["c"]

        ip_count = conn.execute(
            """
            SELECT COUNT(*) AS c
            FROM request_key_attempts
            WHERE ip_hash = ? AND day = ?
            """,
            (ip_hash, day),
        ).fetchone()["c"]

    return {"email": int(email_count), "ip": int(ip_count)}


def record_key_attempt(email_hash: str, ip_hash: str, day: str) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO request_key_attempts(email_hash, ip_hash, day, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (email_hash, ip_hash, day, utc_now()),
        )


def create_or_rotate_key_for_email(email: str, name: str | None, ip_hash: str) -> dict[str, Any]:
    """
    Create or rotate a key for a public user.

    Guardrails:
    - 1 public request per email per UTC day.
    - 1 public request per IP hash per UTC day.
    - If an existing user has a paid plan, the plan is preserved.
    - Raw API key is returned only once from this function.
    """
    email = normalize_email(email)
    email_h = hash_email(email)
    day = utc_day()

    attempts = count_key_attempts(email_h, ip_hash, day)
    if attempts["email"] >= 1:
        raise RateLimitError("Only one API key request per email per day is allowed.")
    if attempts["ip"] >= 1:
        raise RateLimitError("Only one API key request per IP per day is allowed.")

    record_key_attempt(email_h, ip_hash, day)

    existing = get_user_by_email(email)
    plan = (existing or {}).get("plan", "free")
    status = (existing or {}).get("status", "active")

    if plan not in {"free", "pro", "developer", "team", "enterprise", "legacy"}:
        plan = "free"

    raw_key = generate_api_key(plan)
    key_hash = hash_api_key(raw_key)
    limits = plan_limits(plan)
    now = utc_now()

    with connect() as conn:
        if existing:
            conn.execute(
                """
                UPDATE users
                SET name = COALESCE(?, name),
                    api_key_hash = ?,
                    plan = ?,
                    status = ?,
                    daily_limit = ?,
                    monthly_limit = ?,
                    updated_at = ?,
                    last_key_issued_at = ?
                WHERE id = ?
                """,
                (
                    name,
                    key_hash,
                    plan,
                    status,
                    limits["daily_limit"],
                    limits["monthly_limit"],
                    now,
                    now,
                    existing["id"],
                ),
            )
            user_id = existing["id"]
        else:
            conn.execute(
                """
                INSERT INTO users(
                    email, email_hash, name, api_key_hash, plan, status,
                    daily_limit, monthly_limit, created_at, updated_at, last_key_issued_at
                )
                VALUES (?, ?, ?, ?, 'free', 'active', ?, ?, ?, ?, ?)
                """,
                (
                    email,
                    email_h,
                    name,
                    key_hash,
                    limits["daily_limit"],
                    limits["monthly_limit"],
                    now,
                    now,
                    now,
                ),
            )
            user_id = conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]

    user = get_user_by_id(int(user_id))
    if not user:
        raise AuthStoreError("Failed to fetch user after key creation")

    return {"user": user, "api_key": raw_key}


def _table_names(conn: sqlite3.Connection) -> set[str]:
    return {
        str(r["name"])
        for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    }


def _table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    try:
        rows = conn.execute(f'PRAGMA table_info("{table}")').fetchall()
        return {str(r["name"]) if "name" in r.keys() else str(r[1]) for r in rows}
    except Exception:
        return set()


def register_failed_attempt(
    ip_hash: str,
    reason: str,
    email_present: bool,
    name_present: bool,
) -> None:
    """
    Register failed /public/request-key validation attempts.

    Stores no raw email and no request body.
    Safe for funnel analysis.

    Attempts to write into request_key_attempts when compatible.
    Falls back to request_key_failed_attempts if the existing schema differs.
    """
    now = utc_now()

    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS request_key_failed_attempts (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at    TEXT NOT NULL,
                ip_hash       TEXT,
                reason        TEXT,
                email_present INTEGER DEFAULT 0,
                name_present  INTEGER DEFAULT 0,
                status        TEXT DEFAULT 'failed_validation'
            )
            """
        )

        table_names = _table_names(conn)
        columns_set = _table_columns(conn, "request_key_attempts")

        candidate = {
            "created_at": now,
            "ts_utc": now,
            "ip_hash": ip_hash,
            "reason": reason,
            "error_reason": reason,
            "email_present": 1 if email_present else 0,
            "name_present": 1 if name_present else 0,
            "status": "failed_validation",
            "success": 0,
            "day": utc_day(),
        }

        insertable = [col for col in candidate.keys() if col in columns_set]

        # Use request_key_attempts only if there are enough compatible columns.
        # Current production schema requires email_hash NOT NULL, so fallback is
        # expected unless the table has been expanded later.
        if "request_key_attempts" in table_names and len(insertable) >= 3 and "email_hash" not in columns_set:
            placeholders = ", ".join(["?"] * len(insertable))
            col_sql = ", ".join(f'"{c}"' for c in insertable)
            values = [candidate[c] for c in insertable]
            conn.execute(
                f'INSERT INTO request_key_attempts ({col_sql}) VALUES ({placeholders})',
                values,
            )
        else:
            conn.execute(
                """
                INSERT INTO request_key_failed_attempts (
                    created_at,
                    ip_hash,
                    reason,
                    email_present,
                    name_present,
                    status
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    now,
                    ip_hash,
                    reason,
                    1 if email_present else 0,
                    1 if name_present else 0,
                    "failed_validation",
                ),
            )


def create_admin_key(is_premium: bool = False) -> str:
    """Compatibility helper for /admin/generate-key."""
    plan = "pro" if is_premium else "free"
    raw_key = generate_api_key(plan)
    key_hash = hash_api_key(raw_key)
    now = utc_now()
    limits = plan_limits(plan)
    synthetic_email = f"admin-{secrets.token_hex(8)}@sas.local"

    with connect() as conn:
        conn.execute(
            """
            INSERT INTO users(
                email, email_hash, name, api_key_hash, plan, status,
                daily_limit, monthly_limit, created_at, updated_at, last_key_issued_at
            )
            VALUES (?, ?, ?, ?, ?, 'active', ?, ?, ?, ?, ?)
            """,
            (
                synthetic_email,
                hash_email(synthetic_email),
                "Admin generated key",
                key_hash,
                plan,
                limits["daily_limit"],
                limits["monthly_limit"],
                now,
                now,
                now,
            ),
        )

    return raw_key


# ==============================================================================
# QUOTA + USAGE
# ==============================================================================


def usage_counts(user_id: int) -> dict[str, int]:
    with connect() as conn:
        daily = conn.execute(
            "SELECT COUNT(*) AS c FROM api_usage WHERE user_id = ? AND day = ?",
            (user_id, utc_day()),
        ).fetchone()["c"]

        monthly = conn.execute(
            "SELECT COUNT(*) AS c FROM api_usage WHERE user_id = ? AND month = ?",
            (user_id, utc_month()),
        ).fetchone()["c"]

    return {"daily": int(daily), "monthly": int(monthly)}


def quota_state(user: dict[str, Any]) -> dict[str, Any]:
    if not user or not user.get("id"):
        return {
            "allowed": True,
            "daily_used": 0,
            "monthly_used": 0,
            "daily_limit": None,
            "monthly_limit": None,
            "reason": None,
        }

    counts = usage_counts(int(user["id"]))
    daily_limit = user.get("daily_limit")
    monthly_limit = user.get("monthly_limit")

    if daily_limit is not None and counts["daily"] >= int(daily_limit):
        return {
            "allowed": False,
            "daily_used": counts["daily"],
            "monthly_used": counts["monthly"],
            "daily_limit": daily_limit,
            "monthly_limit": monthly_limit,
            "reason": "daily_limit_exceeded",
        }

    if monthly_limit is not None and counts["monthly"] >= int(monthly_limit):
        return {
            "allowed": False,
            "daily_used": counts["daily"],
            "monthly_used": counts["monthly"],
            "daily_limit": daily_limit,
            "monthly_limit": monthly_limit,
            "reason": "monthly_limit_exceeded",
        }

    return {
        "allowed": True,
        "daily_used": counts["daily"],
        "monthly_used": counts["monthly"],
        "daily_limit": daily_limit,
        "monthly_limit": monthly_limit,
        "reason": None,
    }


def record_api_usage(
    user: dict[str, Any],
    method: str,
    path: str,
    status_code: int,
    request_id: str | None = None,
) -> None:
    if not user or not user.get("id"):
        return

    with connect() as conn:
        conn.execute(
            """
            INSERT INTO api_usage(
                user_id, email_hash, plan, method, path, status_code,
                request_id, day, month, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(user["id"]),
                user.get("email_hash"),
                user.get("plan"),
                method,
                path,
                int(status_code),
                request_id,
                utc_day(),
                utc_month(),
                utc_now(),
            ),
        )


# ==============================================================================
# BILLING
# ==============================================================================


def upsert_paid_user(
    email: str,
    plan: str = "pro",
    name: str | None = None,
    polar_customer_id: str | None = None,
    polar_subscription_id: str | None = None,
) -> dict[str, Any]:
    email = normalize_email(email)
    user = get_user_by_email(email)
    limits = plan_limits(plan)
    now = utc_now()

    raw_key: str | None = None
    key_hash: str | None = None

    if not user or not user.get("api_key_hash"):
        raw_key = generate_api_key(plan)
        key_hash = hash_api_key(raw_key)

    with connect() as conn:
        if user:
            conn.execute(
                """
                UPDATE users
                SET name = COALESCE(?, name),
                    api_key_hash = COALESCE(?, api_key_hash),
                    plan = ?,
                    status = 'active',
                    daily_limit = ?,
                    monthly_limit = ?,
                    updated_at = ?,
                    polar_customer_id = COALESCE(?, polar_customer_id),
                    polar_subscription_id = COALESCE(?, polar_subscription_id)
                WHERE id = ?
                """,
                (
                    name,
                    key_hash,
                    plan,
                    limits["daily_limit"],
                    limits["monthly_limit"],
                    now,
                    polar_customer_id,
                    polar_subscription_id,
                    user["id"],
                ),
            )
            user_id = user["id"]
        else:
            conn.execute(
                """
                INSERT INTO users(
                    email, email_hash, name, api_key_hash, plan, status,
                    daily_limit, monthly_limit, created_at, updated_at,
                    last_key_issued_at, polar_customer_id, polar_subscription_id
                )
                VALUES (?, ?, ?, ?, ?, 'active', ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    email,
                    hash_email(email),
                    name,
                    key_hash,
                    plan,
                    limits["daily_limit"],
                    limits["monthly_limit"],
                    now,
                    now,
                    now if raw_key else None,
                    polar_customer_id,
                    polar_subscription_id,
                ),
            )
            user_id = conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]

    updated = get_user_by_id(int(user_id))
    if not updated:
        raise AuthStoreError("Failed to fetch paid user")

    return {"user": updated, "api_key": raw_key}


def record_payment_event(
    provider: str,
    event_type: str,
    external_id: str,
    email: str | None,
    plan: str | None,
    status: str,
    raw_payload: dict[str, Any],
    user_id: int | None = None,
) -> bool:
    email_norm = normalize_email(email) if email else None
    email_h = hash_email(email_norm) if email_norm else None
    raw_json = json.dumps(raw_payload, ensure_ascii=False, sort_keys=True)
    now = utc_now()

    with connect() as conn:
        cur = conn.execute(
            """
            INSERT OR IGNORE INTO payments(
                provider, event_type, external_id, email, email_hash,
                user_id, plan, status, raw_json, created_at, processed_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                provider,
                event_type,
                external_id,
                email_norm,
                email_h,
                user_id,
                plan,
                status,
                raw_json,
                now,
                now,
            ),
        )

    return cur.rowcount > 0
