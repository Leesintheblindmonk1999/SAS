#!/usr/bin/env python3
"""
scripts/funnel_report.py

SAS operational funnel report.

Usage:
  python scripts/funnel_report.py
  python scripts/funnel_report.py --hours 24 --show-recent
  python scripts/funnel_report.py --days 7 --json > funnel_report.json

This version handles both numeric status codes (200/422/500) and bucket
strings (2xx/4xx/5xx), so recent 4xx/5xx sections work correctly.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


DEFAULT_METRICS_DB = "/app/data/metrics.db"
DEFAULT_AUTH_DB = "/app/data/auth.db"
DEFAULT_AUDIT_DB = "/app/data/audit.db"

INFRA_PATHS = {"/health", "/readyz", "/robots.txt"}
DISCOVERY_PATHS = {"/", "/docs", "/openapi.json", "/integrity", "/public/stats", "/public/activity"}
TRIAL_PATHS = {"/public/demo/audit"}
CONVERSION_PATHS = {"/public/request-key", "/billing/polar/checkout", "/billing/mercadopago/checkout"}
AUTH_PATHS = {"/v1/whoami", "/v1/diff", "/v1/audit", "/v1/chat"}


def connect(path: str) -> sqlite3.Connection | None:
    if not Path(path).exists():
        print(f"[WARN] DB not found: {path}")
        return None
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone()
    return row is not None


def columns(conn: sqlite3.Connection, table: str) -> set[str]:
    if not table_exists(conn, table):
        return set()
    return {r["name"] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def rows(conn: sqlite3.Connection, query: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
    try:
        return conn.execute(query, params).fetchall()
    except Exception as exc:
        print(f"[WARN] query failed: {exc}")
        print(query)
        return []


def detect_ts_column(conn: sqlite3.Connection, table: str) -> str | None:
    cols = columns(conn, table)
    for name in ("ts_utc", "created_at", "timestamp", "time_bucket_utc", "processed_at"):
        if name in cols:
            return name
    return None


def normalize_status(value: Any) -> tuple[str, int | None]:
    if value is None:
        return "unknown", None

    raw = str(value).strip().lower()
    if raw in {"2xx", "3xx", "4xx", "5xx"}:
        return raw, None

    try:
        code = int(float(raw))
    except Exception:
        return "unknown", None

    if 200 <= code <= 299:
        return "2xx", code
    if 300 <= code <= 399:
        return "3xx", code
    if 400 <= code <= 499:
        return "4xx", code
    if 500 <= code <= 599:
        return "5xx", code
    return "other", code


def is_error(value: Any) -> bool:
    bucket, code = normalize_status(value)
    return bucket in {"4xx", "5xx"} or (code is not None and code >= 400)


def status_value(row: dict[str, Any]) -> Any:
    if row.get("status_code") is not None:
        return row.get("status_code")
    return row.get("status_bucket")


def classify(method: str, path: str) -> str:
    method = (method or "").upper()
    path = path or ""

    if path in INFRA_PATHS or (method == "HEAD" and path == "/"):
        return "infrastructure"
    if path in DISCOVERY_PATHS:
        return "discovery"
    if path in TRIAL_PATHS:
        return "trial"
    if path in CONVERSION_PATHS:
        return "conversion"
    if path in AUTH_PATHS or path.startswith("/v1/"):
        return "authenticated_usage"
    if path.startswith("/billing/"):
        return "billing_other"
    if path.startswith("/admin"):
        return "admin"
    if path.startswith("/public/"):
        return "public_other"
    return "other"


def mask_email(email: Any) -> str:
    if not email:
        return ""
    email = str(email)
    if "@" not in email:
        return email[:2] + "***" if len(email) > 2 else "***"
    local, domain = email.split("@", 1)
    return (local[:2] if len(local) > 2 else local[:1]) + "***@" + domain


def short(value: Any, n: int = 12) -> str:
    if value is None:
        return ""
    return str(value)[:n]


def print_section(title: str) -> None:
    print("\n" + "=" * 92)
    print(title)
    print("=" * 92)


def print_table(data: list[dict[str, Any]], cols: list[str], limit: int | None = None) -> None:
    if limit is not None:
        data = data[:limit]
    if not data:
        print("(no rows)")
        return

    widths = {c: max(len(c), *(len(str(r.get(c, ""))) for r in data)) for c in cols}
    header = "  ".join(c.ljust(widths[c]) for c in cols)
    print(header)
    print("-" * len(header))
    for r in data:
        print("  ".join(str(r.get(c, "")).ljust(widths[c]) for c in cols))


def load_metrics(conn: sqlite3.Connection, start_iso: str) -> list[dict[str, Any]]:
    table = "api_request_metrics"
    if not table_exists(conn, table):
        print("[WARN] api_request_metrics table not found")
        return []

    cols = columns(conn, table)
    ts_col = detect_ts_column(conn, table)

    def c(name: str, default: str) -> str:
        return name if name in cols else f"{default} AS {name}"

    selected = [
        c("id", "NULL"),
        c("method", "NULL"),
        c("path", "NULL"),
        c("status_code", "NULL"),
        c("status_bucket", "NULL"),
        c("country", "'unknown'"),
        c("ip_hash", "NULL"),
        c("api_key_hash", "NULL"),
        c("plan", "NULL"),
        c("latency_ms", "NULL"),
        c("request_id", "NULL"),
    ]

    if ts_col:
        selected.append(f"{ts_col} AS ts")
        where = f"{ts_col} >= ?"
        params = (start_iso,)
        order = ts_col
    else:
        selected.append("NULL AS ts")
        where = "1=1"
        params = ()
        order = "id" if "id" in cols else "rowid"

    q = f"SELECT {', '.join(selected)} FROM {table} WHERE {where} ORDER BY {order} ASC"
    return [dict(r) for r in rows(conn, q, params)]


def summarize_metrics(metric_rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_category = Counter()
    by_country = Counter()
    by_plan = Counter()
    by_path = Counter()
    by_ip_country = Counter()
    by_key_plan = Counter()

    unique_ips = set()
    unique_keys = set()
    product_rows = []
    error_rows = []

    for r in metric_rows:
        method = str(r.get("method") or "")
        path = str(r.get("path") or "")
        country = str(r.get("country") or "unknown")
        plan = str(r.get("plan") or "anonymous")
        ip_hash = r.get("ip_hash")
        key_hash = r.get("api_key_hash")
        stat = status_value(r)
        bucket, code = normalize_status(stat)
        category = classify(method, path)

        by_category[category] += 1
        by_country[country] += 1
        by_plan[plan] += 1
        by_path[(path, method, bucket)] += 1

        if ip_hash:
            unique_ips.add(str(ip_hash))
            by_ip_country[(short(ip_hash), country)] += 1
        if key_hash:
            unique_keys.add(str(key_hash))
            by_key_plan[(short(key_hash), plan)] += 1

        clean = {
            "ts": r.get("ts"),
            "country": country,
            "method": method,
            "path": path,
            "status": code if code is not None else bucket,
            "status_bucket": bucket,
            "category": category,
            "plan": plan,
            "ip_hash": short(ip_hash),
            "api_key_hash": short(key_hash),
            "latency_ms": r.get("latency_ms"),
            "request_id": short(r.get("request_id"), 8),
        }

        if category != "infrastructure":
            product_rows.append(clean)
        if is_error(stat):
            error_rows.append(clean)

    return {
        "total_requests": len(metric_rows),
        "unique_ip_hashes": len(unique_ips),
        "unique_api_key_hashes": len(unique_keys),
        "by_category": dict(by_category.most_common()),
        "by_country": dict(by_country.most_common()),
        "by_plan": dict(by_plan.most_common()),
        "by_path": [
            {"path": p, "method": m, "status": s, "count": n}
            for (p, m, s), n in by_path.most_common()
        ],
        "by_ip_country": [
            {"ip_hash": ip, "country": country, "count": n}
            for (ip, country), n in by_ip_country.most_common(50)
        ],
        "by_key_plan": [
            {"api_key_hash": key, "plan": plan, "count": n}
            for (key, plan), n in by_key_plan.most_common(50)
        ],
        "product_rows": product_rows,
        "error_rows": error_rows,
    }


def print_metrics(summary: dict[str, Any], show_recent: bool, recent_limit: int) -> None:
    print_section("METRICS SUMMARY")
    print(f"Total requests:          {summary['total_requests']}")
    print(f"Unique ip_hashes:        {summary['unique_ip_hashes']}")
    print(f"Unique api_key_hashes:   {summary['unique_api_key_hashes']}")

    print_section("TRAFFIC BY CATEGORY")
    print_table([{"category": k, "count": v} for k, v in summary["by_category"].items()], ["category", "count"])

    print_section("COUNTRIES")
    print_table([{"country": k, "count": v} for k, v in summary["by_country"].items()], ["country", "count"], 30)

    print_section("PLANS")
    print_table([{"plan": k, "count": v} for k, v in summary["by_plan"].items()], ["plan", "count"], 30)

    print_section("PATH / METHOD / STATUS")
    print_table(summary["by_path"], ["path", "method", "status", "count"], 100)

    print_section("PRODUCT FUNNEL")
    ordered = [
        "/", "/docs", "/openapi.json", "/public/stats", "/public/activity",
        "/public/demo/audit", "/public/request-key", "/v1/whoami", "/v1/diff",
        "/v1/audit", "/v1/chat", "/billing/polar/checkout",
        "/billing/mercadopago/checkout", "/billing/polar/webhook",
        "/billing/mercadopago/webhook",
    ]
    items = []
    for path in ordered:
        for bucket in ("2xx", "3xx", "4xx", "5xx", "unknown"):
            count = sum(x["count"] for x in summary["by_path"] if x["path"] == path and x["status"] == bucket)
            if count:
                items.append({"path": path, "status": bucket, "count": count})
    print_table(items, ["path", "status", "count"])

    print_section("TOP IP HASH / COUNTRY BUCKETS")
    print_table(summary["by_ip_country"], ["ip_hash", "country", "count"], 30)

    print_section("API KEY HASH / PLAN BUCKETS")
    print_table(summary["by_key_plan"], ["api_key_hash", "plan", "count"], 30)

    print_section("RECENT 4xx/5xx")
    print_table(
        summary["error_rows"][-recent_limit:],
        ["ts", "country", "method", "path", "status", "status_bucket", "category", "plan", "ip_hash", "api_key_hash"],
        recent_limit,
    )

    if show_recent:
        print_section("RECENT PRODUCT ACTIVITY")
        print_table(
            summary["product_rows"][-recent_limit:],
            ["ts", "country", "method", "path", "status", "status_bucket", "category", "plan", "ip_hash", "api_key_hash"],
            recent_limit,
        )


def print_users(conn: sqlite3.Connection | None, start_iso: str) -> list[dict[str, Any]]:
    print_section("AUTH / USERS")
    if conn is None or not table_exists(conn, "users"):
        print("[WARN] users table not found")
        return []

    cols = columns(conn, "users")
    ts_col = "created_at" if "created_at" in cols else None
    where = f"{ts_col} >= ?" if ts_col else "1=1"
    params = (start_iso,) if ts_col else ()

    wanted = ["id", "email", "name", "plan", "status", "daily_limit", "monthly_limit", "created_at", "last_key_issued_at"]
    select_cols = [x for x in wanted if x in cols]
    q = f"SELECT {', '.join(select_cols)} FROM users WHERE {where} ORDER BY id DESC LIMIT 100"
    data = []
    for r in rows(conn, q, params):
        d = dict(r)
        data.append({
            "id": d.get("id"),
            "email": mask_email(d.get("email")),
            "name": d.get("name"),
            "plan": d.get("plan"),
            "status": d.get("status"),
            "daily": d.get("daily_limit"),
            "monthly": d.get("monthly_limit"),
            "created_at": d.get("created_at"),
            "last_key": d.get("last_key_issued_at"),
        })
    print_table(data, ["id", "email", "name", "plan", "status", "daily", "monthly", "created_at", "last_key"], 100)
    return data


def print_request_key_attempts(conn: sqlite3.Connection | None, start_iso: str) -> list[dict[str, Any]]:
    print_section("REQUEST KEY ATTEMPTS")
    if conn is None or not table_exists(conn, "request_key_attempts"):
        print("[WARN] request_key_attempts table not found")
        return []

    cols = columns(conn, "request_key_attempts")
    ts_col = "created_at" if "created_at" in cols else detect_ts_column(conn, "request_key_attempts")
    where = f"{ts_col} >= ?" if ts_col else "1=1"
    params = (start_iso,) if ts_col else ()

    preferred = ["id", "email", "email_hash", "ip_hash", "status", "created_at", "sent", "provider", "error"]
    select_cols = [x for x in preferred if x in cols] or list(cols)
    order_col = ts_col or ("id" if "id" in cols else "rowid")

    q = f"SELECT {', '.join(select_cols)} FROM request_key_attempts WHERE {where} ORDER BY {order_col} DESC LIMIT 100"
    data = []
    for r in rows(conn, q, params):
        d = dict(r)
        if "email" in d:
            d["email"] = mask_email(d.get("email"))
        if "email_hash" in d:
            d["email_hash"] = short(d.get("email_hash"))
        if "ip_hash" in d:
            d["ip_hash"] = short(d.get("ip_hash"))
        data.append(d)

    print_table(data, list(data[0].keys()) if data else ["id"], 100)
    return data


def print_api_usage(conn: sqlite3.Connection | None, start_iso: str) -> list[dict[str, Any]]:
    print_section("API USAGE")
    if conn is None or not table_exists(conn, "api_usage"):
        print("[WARN] api_usage table not found")
        return []

    cols = columns(conn, "api_usage")
    ts_col = "created_at" if "created_at" in cols else detect_ts_column(conn, "api_usage")
    where = f"{ts_col} >= ?" if ts_col else "1=1"
    params = (start_iso,) if ts_col else ()

    group_cols = [x for x in ("user_id", "endpoint", "day", "month") if x in cols]
    if group_cols:
        q = f"SELECT {', '.join(group_cols)}, COUNT(*) AS count FROM api_usage WHERE {where} GROUP BY {', '.join(group_cols)} ORDER BY count DESC LIMIT 100"
    else:
        q = f"SELECT COUNT(*) AS count FROM api_usage WHERE {where}"

    data = [dict(r) for r in rows(conn, q, params)]
    print_table(data, list(data[0].keys()) if data else ["count"], 100)
    return data


def print_payments(conn: sqlite3.Connection | None, start_iso: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    print_section("BILLING / PAYMENTS")
    if conn is None or not table_exists(conn, "payments"):
        print("[WARN] payments table not found")
        return [], []

    cols = columns(conn, "payments")
    ts_col = "created_at" if "created_at" in cols else detect_ts_column(conn, "payments")
    where = f"{ts_col} >= ?" if ts_col else "1=1"
    params = (start_iso,) if ts_col else ()

    preferred = ["provider", "event_type", "external_id", "email", "plan", "status", "created_at", "processed_at"]
    select_cols = [x for x in preferred if x in cols]
    order_col = ts_col or ("id" if "id" in cols else "rowid")

    q = f"SELECT {', '.join(select_cols)} FROM payments WHERE {where} ORDER BY {order_col} DESC LIMIT 100"
    payments = []
    for r in rows(conn, q, params):
        d = dict(r)
        if "email" in d:
            d["email"] = mask_email(d.get("email"))
        if d.get("external_id"):
            d["external_id"] = short(d.get("external_id")) + "..."
        payments.append(d)

    print_table(payments, list(payments[0].keys()) if payments else preferred, 100)

    print_section("PAYMENT STATUS SUMMARY")
    summary = []
    if {"provider", "event_type", "status"}.issubset(cols):
        q2 = f"SELECT provider, event_type, status, COUNT(*) AS count FROM payments WHERE {where} GROUP BY provider, event_type, status ORDER BY count DESC LIMIT 100"
        summary = [dict(r) for r in rows(conn, q2, params)]

    print_table(summary, ["provider", "event_type", "status", "count"], 100)
    return payments, summary



def load_audit_summary(conn: sqlite3.Connection | None, start_iso: str) -> dict[str, Any]:
    if conn is None or not table_exists(conn, "audit_events"):
        return {"available": False, "reason": "audit_events table not found"}

    data: dict[str, Any] = {"available": True}

    total = rows(conn, "SELECT COUNT(*) AS count FROM audit_events WHERE ts_utc >= ?", (start_iso,))
    data["total_events"] = int(total[0]["count"] if total else 0)

    by_status = rows(conn, """
        SELECT status_class, COUNT(*) AS count
        FROM audit_events
        WHERE ts_utc >= ?
        GROUP BY status_class
        ORDER BY count DESC
    """, (start_iso,))
    data["by_status_class"] = [dict(r) for r in by_status]

    by_country = rows(conn, """
        SELECT country, COUNT(*) AS count
        FROM audit_events
        WHERE ts_utc >= ?
        GROUP BY country
        ORDER BY count DESC
        LIMIT 30
    """, (start_iso,))
    data["by_country"] = [dict(r) for r in by_country]

    by_prefix = rows(conn, """
        SELECT path_prefix, status_class, COUNT(*) AS count
        FROM audit_events
        WHERE ts_utc >= ?
        GROUP BY path_prefix, status_class
        ORDER BY count DESC
        LIMIT 50
    """, (start_iso,))
    data["by_path_prefix"] = [dict(r) for r in by_prefix]

    recent_errors = rows(conn, """
        SELECT ts_utc, country, method, path, status_code, status_class, request_id
        FROM audit_events
        WHERE ts_utc >= ? AND status_code >= 400
        ORDER BY ts_utc DESC
        LIMIT 50
    """, (start_iso,))
    data["recent_errors"] = [dict(r) for r in recent_errors]

    return data


def print_audit_summary(summary: dict[str, Any], recent_limit: int) -> None:
    print_section("PERSISTENT AUDIT DB")
    if not summary.get("available"):
        print(f"(not available: {summary.get('reason', 'unknown')})")
        return

    print(f"Total audit events:     {summary.get('total_events', 0)}")

    print("\nSTATUS CLASS")
    print_table(summary.get("by_status_class", []), ["status_class", "count"], 20)

    print("\nCOUNTRIES")
    print_table(summary.get("by_country", []), ["country", "count"], 30)

    print("\nPATH PREFIX / STATUS")
    print_table(summary.get("by_path_prefix", []), ["path_prefix", "status_class", "count"], 50)

    print("\nRECENT AUDIT ERRORS")
    print_table(
        summary.get("recent_errors", [])[:recent_limit],
        ["ts_utc", "country", "method", "path", "status_code", "status_class", "request_id"],
        recent_limit,
    )


def load_validation_errors_summary(conn: sqlite3.Connection | None, start_iso: str) -> dict[str, Any]:
    if conn is None or not table_exists(conn, "validation_errors"):
        return {"available": False, "reason": "validation_errors table not found"}

    data: dict[str, Any] = {"available": True}

    total = rows(conn, "SELECT COUNT(*) AS count FROM validation_errors WHERE ts_utc >= ?", (start_iso,))
    data["total"] = int(total[0]["count"] if total else 0)

    by_path = rows(conn, """
        SELECT path, method, status, COUNT(*) AS count
        FROM validation_errors
        WHERE ts_utc >= ?
        GROUP BY path, method, status
        ORDER BY count DESC
        LIMIT 50
    """, (start_iso,))
    data["by_path_method"] = [dict(r) for r in by_path]

    field_shape = rows(conn, """
        SELECT
            json_valid,
            email_present,
            email_valid,
            name_present,
            COUNT(*) AS count
        FROM validation_errors
        WHERE ts_utc >= ? AND path = '/public/request-key'
        GROUP BY json_valid, email_present, email_valid, name_present
        ORDER BY count DESC
    """, (start_iso,))
    data["request_key_field_shape"] = [dict(r) for r in field_shape]

    by_types = rows(conn, """
        SELECT validation_error_types, COUNT(*) AS count
        FROM validation_errors
        WHERE ts_utc >= ?
        GROUP BY validation_error_types
        ORDER BY count DESC
        LIMIT 50
    """, (start_iso,))
    data["by_validation_error_types"] = [dict(r) for r in by_types]

    recent = rows(conn, """
        SELECT
            ts_utc,
            country,
            method,
            path,
            status,
            content_type,
            content_length,
            json_valid,
            email_present,
            email_valid,
            name_present,
            validation_error_types,
            ip_hash
        FROM validation_errors
        WHERE ts_utc >= ?
        ORDER BY id DESC
        LIMIT 50
    """, (start_iso,))
    data["recent"] = [dict(r) for r in recent]

    return data


def print_validation_errors_summary(summary: dict[str, Any], recent_limit: int) -> None:
    print_section("VALIDATION ERRORS (422)")

    if not summary.get("available"):
        print(f"(not available: {summary.get('reason', 'unknown')})")
        return

    print(f"Total validation errors: {summary.get('total', 0)}")

    print("\nBY PATH / METHOD / STATUS")
    print_table(summary.get("by_path_method", []), ["path", "method", "status", "count"], 50)

    print("\nREQUEST-KEY FIELD SHAPE")
    print_table(
        summary.get("request_key_field_shape", []),
        ["json_valid", "email_present", "email_valid", "name_present", "count"],
        50,
    )

    print("\nBY VALIDATION ERROR TYPES")
    print_table(summary.get("by_validation_error_types", []), ["validation_error_types", "count"], 50)

    print("\nRECENT VALIDATION ERRORS")
    print_table(
        summary.get("recent", [])[:recent_limit],
        [
            "ts_utc",
            "country",
            "method",
            "path",
            "status",
            "content_type",
            "content_length",
            "json_valid",
            "email_present",
            "email_valid",
            "name_present",
            "validation_error_types",
            "ip_hash",
        ],
        recent_limit,
    )


def interpretation(metrics: dict[str, Any], users: list[dict[str, Any]], attempts: list[dict[str, Any]]) -> list[str]:
    lines = []
    total = metrics.get("total_requests", 0) or 0
    cats = metrics.get("by_category", {})
    countries = metrics.get("by_country", {})

    infra = cats.get("infrastructure", 0)
    if total:
        lines.append(f"Infrastructure traffic is {infra / total * 100:.1f}% of total traffic. Do not treat it as product demand.")

    if cats.get("discovery", 0):
        lines.append(f"Discovery traffic exists: {cats['discovery']} requests around root/docs/openapi/stats/activity.")
    if cats.get("trial", 0):
        lines.append(f"Trial traffic exists: {cats['trial']} public demo requests.")
    if cats.get("conversion", 0):
        lines.append(f"Conversion-surface traffic exists: {cats['conversion']} request-key or checkout requests.")
    if cats.get("authenticated_usage", 0):
        lines.append(f"Authenticated API usage exists: {cats['authenticated_usage']} whoami/diff/audit/chat requests.")

    external = [c for c in countries if c not in {"AR", "unknown"}]
    if external:
        lines.append(f"External country buckets observed: {', '.join(external[:12])}.")

    if attempts:
        lines.append("Request-key attempts exist in this window. Verify whether they are owner tests or external users.")
    else:
        lines.append("No request-key attempts in this window. Discovery has not converted into Free key creation yet.")

    if users:
        lines.append("Users were created/updated in this window. Check whether they are test users or external users.")
    else:
        lines.append("No new users in this window.")

    lines.append("Investigate repeated 4xx/5xx on request-key, demo, whoami, diff or checkout before broad public launches.")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description="SAS operational funnel report")
    parser.add_argument("--metrics-db", default=DEFAULT_METRICS_DB)
    parser.add_argument("--auth-db", default=DEFAULT_AUTH_DB)
    parser.add_argument("--audit-db", default=DEFAULT_AUDIT_DB)
    parser.add_argument("--hours", type=int, default=24)
    parser.add_argument("--days", type=int, default=None)
    parser.add_argument("--show-recent", action="store_true")
    parser.add_argument("--recent-limit", type=int, default=50)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    now = datetime.now(timezone.utc)
    if args.days is not None:
        start = now - timedelta(days=args.days)
        window = f"last {args.days}d"
    else:
        start = now - timedelta(hours=args.hours)
        window = f"last {args.hours}h"
    start_iso = start.isoformat()

    print_section("SAS FUNNEL REPORT")
    print(f"Window:       {window}")
    print(f"Start UTC:    {start_iso}")
    print(f"Metrics DB:   {args.metrics_db}")
    print(f"Auth DB:      {args.auth_db}")
    print(f"Audit DB:     {args.audit_db}")

    metrics_conn = connect(args.metrics_db)
    auth_conn = connect(args.auth_db)
    audit_conn = connect(args.audit_db)

    metrics_summary = {}
    if metrics_conn:
        metric_rows = load_metrics(metrics_conn, start_iso)
        metrics_summary = summarize_metrics(metric_rows)
        print_metrics(metrics_summary, args.show_recent, args.recent_limit)

    users = print_users(auth_conn, start_iso)
    attempts = print_request_key_attempts(auth_conn, start_iso)
    usage = print_api_usage(auth_conn, start_iso)
    payments, payment_summary = print_payments(auth_conn, start_iso)
    audit_summary = load_audit_summary(audit_conn, start_iso)
    print_audit_summary(audit_summary, args.recent_limit)

    validation_summary = load_validation_errors_summary(audit_conn, start_iso)
    print_validation_errors_summary(validation_summary, args.recent_limit)

    print_section("RECOMMENDED INTERPRETATION")
    notes = interpretation(metrics_summary, users, attempts)
    for line in notes:
        print(f"- {line}")

    output = {
        "window": window,
        "start_utc": start_iso,
        "metrics": {k: v for k, v in metrics_summary.items() if k not in {"product_rows", "error_rows"}},
        "recent_errors": metrics_summary.get("error_rows", [])[-args.recent_limit:],
        "recent_product_activity": metrics_summary.get("product_rows", [])[-args.recent_limit:] if args.show_recent else [],
        "users": users,
        "request_key_attempts": attempts,
        "api_usage": usage,
        "payments": payments,
        "payment_summary": payment_summary,
        "audit": audit_summary,
        "validation_errors": validation_summary,
        "interpretation": notes,
    }

    if metrics_conn:
        metrics_conn.close()
    if auth_conn:
        auth_conn.close()
    if audit_conn:
        audit_conn.close()

    if args.json:
        print_section("JSON SUMMARY")
        print(json.dumps(output, indent=2, ensure_ascii=False, default=str))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
