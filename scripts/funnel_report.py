#!/usr/bin/env python3
"""
scripts/funnel_report.py

Operational funnel report for SAS.

Purpose:
- Separate infrastructure traffic from product traffic.
- Inspect product funnel: docs -> demo -> request-key -> whoami/diff -> checkout.
- Summarize users, key attempts, billing events, plans, countries, errors and API usage.
- Avoid exposing raw API keys or raw IPs.

Designed for Render shell:

    python scripts/funnel_report.py

Optional:

    python scripts/funnel_report.py --hours 24
    python scripts/funnel_report.py --days 7
    python scripts/funnel_report.py --metrics-db /app/data/metrics.db --auth-db /app/data/auth.db
    python scripts/funnel_report.py --show-recent
    python scripts/funnel_report.py --json

Assumptions:
- metrics DB table: api_request_metrics
- auth DB tables: users, api_usage, request_key_attempts, payments

The script is defensive: if a table or column is missing, it prints a warning and continues.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable


DEFAULT_METRICS_DB = "/app/data/metrics.db"
DEFAULT_AUTH_DB = "/app/data/auth.db"

INFRA_PATHS = {
    "/health",
    "/readyz",
    "/robots.txt",
}

DISCOVERY_PATHS = {
    "/",
    "/docs",
    "/openapi.json",
    "/integrity",
    "/public/stats",
    "/public/activity",
}

TRIAL_PATHS = {
    "/public/demo/audit",
}

CONVERSION_PATHS = {
    "/public/request-key",
    "/billing/polar/checkout",
    "/billing/mercadopago/checkout",
}

AUTH_USAGE_PATHS = {
    "/v1/whoami",
    "/v1/diff",
    "/v1/audit",
    "/v1/chat",
}


def connect(path: str) -> sqlite3.Connection | None:
    if not Path(path).exists():
        print(f"[WARN] DB not found: {path}")
        return None
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone()
    return row is not None


def columns(conn: sqlite3.Connection, table: str) -> set[str]:
    if not table_exists(conn, table):
        return set()
    return {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def safe_count(conn: sqlite3.Connection, table: str, where: str = "", params: Iterable[Any] = ()) -> int:
    if not table_exists(conn, table):
        return 0
    query = f"SELECT COUNT(*) AS c FROM {table}"
    if where:
        query += f" WHERE {where}"
    try:
        return int(conn.execute(query, tuple(params)).fetchone()["c"])
    except Exception as exc:
        print(f"[WARN] count failed for {table}: {exc}")
        return 0


def rows(conn: sqlite3.Connection, query: str, params: Iterable[Any] = ()) -> list[sqlite3.Row]:
    try:
        return conn.execute(query, tuple(params)).fetchall()
    except Exception as exc:
        print(f"[WARN] query failed: {exc}\n{query}")
        return []


def dt_window(hours: int | None, days: int | None) -> tuple[str, datetime]:
    now = datetime.now(timezone.utc)
    if hours is not None:
        start = now - timedelta(hours=hours)
        label = f"last {hours}h"
    else:
        days = days if days is not None else 1
        start = now - timedelta(days=days)
        label = f"last {days}d"
    return label, start


def detect_ts_column(conn: sqlite3.Connection, table: str) -> str | None:
    cols = columns(conn, table)
    for candidate in ("ts_utc", "created_at", "timestamp", "time_bucket_utc", "processed_at"):
        if candidate in cols:
            return candidate
    return None


def status_bucket(code: Any) -> str:
    try:
        c = int(code)
    except Exception:
        return "unknown"
    if 200 <= c <= 299:
        return "2xx"
    if 300 <= c <= 399:
        return "3xx"
    if 400 <= c <= 499:
        return "4xx"
    if 500 <= c <= 599:
        return "5xx"
    return "other"


def print_section(title: str) -> None:
    print("\n" + "=" * 88)
    print(title)
    print("=" * 88)


def print_table(items: list[dict[str, Any]], columns_: list[str], limit: int | None = None) -> None:
    if limit is not None:
        items = items[:limit]
    if not items:
        print("(no rows)")
        return

    widths = {c: max(len(c), *(len(str(row.get(c, ""))) for row in items)) for c in columns_}
    header = "  ".join(c.ljust(widths[c]) for c in columns_)
    print(header)
    print("-" * len(header))
    for row in items:
        print("  ".join(str(row.get(c, "")).ljust(widths[c]) for c in columns_))


def classify_request(method: str, path: str) -> str:
    if path in INFRA_PATHS or (method == "HEAD" and path == "/"):
        return "infrastructure"
    if path in DISCOVERY_PATHS:
        return "discovery"
    if path in TRIAL_PATHS:
        return "trial"
    if path in CONVERSION_PATHS:
        return "conversion"
    if path in AUTH_USAGE_PATHS:
        return "authenticated_usage"
    if path.startswith("/billing/"):
        return "billing_other"
    if path.startswith("/admin"):
        return "admin"
    if path.startswith("/v1/"):
        return "authenticated_usage"
    if path.startswith("/public/"):
        return "public_other"
    return "other"


def metrics_report(conn: sqlite3.Connection | None, start_iso: str, show_recent: bool) -> dict[str, Any]:
    report: dict[str, Any] = {}
    if conn is None or not table_exists(conn, "api_request_metrics"):
        print("[WARN] metrics table api_request_metrics not found")
        return report

    cols = columns(conn, "api_request_metrics")
    ts_col = detect_ts_column(conn, "api_request_metrics")

    if ts_col is None:
        print("[WARN] no timestamp column found in api_request_metrics; report will use all rows")
        where = "1=1"
        params: tuple[Any, ...] = ()
    else:
        where = f"{ts_col} >= ?"
        params = (start_iso,)

    select_cols = {
        "method": "method" if "method" in cols else "NULL AS method",
        "path": "path" if "path" in cols else "NULL AS path",
        "status_code": "status_code" if "status_code" in cols else "NULL AS status_code",
        "country": "country" if "country" in cols else "'unknown' AS country",
        "ip_hash": "ip_hash" if "ip_hash" in cols else "NULL AS ip_hash",
        "api_key_hash": "api_key_hash" if "api_key_hash" in cols else "NULL AS api_key_hash",
        "plan": "plan" if "plan" in cols else "NULL AS plan",
        "latency_ms": "latency_ms" if "latency_ms" in cols else "NULL AS latency_ms",
        "ts": ts_col if ts_col else "NULL AS ts",
    }

    all_rows = rows(
        conn,
        f"""
        SELECT
          {select_cols['method']},
          {select_cols['path']},
          {select_cols['status_code']},
          {select_cols['country']},
          {select_cols['ip_hash']},
          {select_cols['api_key_hash']},
          {select_cols['plan']},
          {select_cols['latency_ms']},
          {select_cols['ts']}
        FROM api_request_metrics
        WHERE {where}
        ORDER BY {ts_col or 'id'} ASC
        """,
        params,
    )

    by_category: dict[str, int] = defaultdict(int)
    by_path_status: dict[tuple[str, str, str], int] = defaultdict(int)
    by_country: dict[str, int] = defaultdict(int)
    by_plan: dict[str, int] = defaultdict(int)
    errors: list[dict[str, Any]] = []

    unique_ips = set()
    unique_keys = set()

    for r in all_rows:
        method = r["method"] or ""
        path = r["path"] or ""
        status_code = r["status_code"]
        country = r["country"] or "unknown"
        plan = r["plan"] or "none"
        bucket = status_bucket(status_code)
        category = classify_request(method, path)

        by_category[category] += 1
        by_path_status[(path, method, bucket)] += 1
        by_country[country] += 1
        by_plan[plan] += 1

        if r["ip_hash"]:
            unique_ips.add(r["ip_hash"])
        if r["api_key_hash"]:
            unique_keys.add(r["api_key_hash"])

        try:
            code_int = int(status_code)
            if code_int >= 400:
                errors.append(
                    {
                        "ts": r["ts"],
                        "country": country,
                        "method": method,
                        "path": path,
                        "status": status_code,
                        "plan": plan,
                        "ip_hash": (r["ip_hash"] or "")[:12],
                        "api_key_hash": (r["api_key_hash"] or "")[:12],
                    }
                )
        except Exception:
            pass

    report["total_requests"] = len(all_rows)
    report["unique_ip_hashes"] = len(unique_ips)
    report["unique_api_key_hashes"] = len(unique_keys)
    report["by_category"] = dict(sorted(by_category.items(), key=lambda x: x[1], reverse=True))
    report["by_country"] = dict(sorted(by_country.items(), key=lambda x: x[1], reverse=True))
    report["by_plan"] = dict(sorted(by_plan.items(), key=lambda x: x[1], reverse=True))

    path_status_items = [
        {"path": k[0], "method": k[1], "status": k[2], "count": v}
        for k, v in sorted(by_path_status.items(), key=lambda x: x[1], reverse=True)
    ]
    report["by_path_status"] = path_status_items
    report["recent_errors"] = errors[-50:]

    print_section("METRICS SUMMARY")
    print(f"Total requests:          {report['total_requests']}")
    print(f"Unique ip_hashes:        {report['unique_ip_hashes']}")
    print(f"Unique api_key_hashes:   {report['unique_api_key_hashes']}")

    print_section("TRAFFIC BY CATEGORY")
    print_table(
        [{"category": k, "count": v} for k, v in report["by_category"].items()],
        ["category", "count"],
    )

    print_section("COUNTRIES")
    print_table(
        [{"country": k, "count": v} for k, v in report["by_country"].items()],
        ["country", "count"],
        limit=20,
    )

    print_section("PLANS")
    print_table(
        [{"plan": k, "count": v} for k, v in report["by_plan"].items()],
        ["plan", "count"],
        limit=20,
    )

    print_section("PATH / METHOD / STATUS")
    print_table(path_status_items, ["path", "method", "status", "count"], limit=80)

    print_section("PRODUCT FUNNEL")
    funnel_paths = [
        "/docs",
        "/openapi.json",
        "/public/demo/audit",
        "/public/request-key",
        "/v1/whoami",
        "/v1/diff",
        "/v1/audit",
        "/v1/chat",
        "/billing/polar/checkout",
        "/billing/mercadopago/checkout",
    ]
    funnel_rows = []
    for p in funnel_paths:
        for bucket in ("2xx", "4xx", "5xx"):
            count = sum(v for (path, _method, b), v in by_path_status.items() if path == p and b == bucket)
            if count:
                funnel_rows.append({"path": p, "status": bucket, "count": count})
    print_table(funnel_rows, ["path", "status", "count"])

    print_section("RECENT 4xx/5xx")
    print_table(report["recent_errors"], ["ts", "country", "method", "path", "status", "plan", "ip_hash", "api_key_hash"], limit=50)

    if show_recent:
        print_section("RECENT PRODUCT ACTIVITY")
        recent = []
        for r in all_rows[-100:]:
            method = r["method"] or ""
            path = r["path"] or ""
            category = classify_request(method, path)
            if category != "infrastructure":
                recent.append(
                    {
                        "ts": r["ts"],
                        "country": r["country"],
                        "method": method,
                        "path": path,
                        "status": r["status_code"],
                        "plan": r["plan"],
                        "ip_hash": (r["ip_hash"] or "")[:12],
                        "api_key_hash": (r["api_key_hash"] or "")[:12],
                    }
                )
        print_table(recent[-50:], ["ts", "country", "method", "path", "status", "plan", "ip_hash", "api_key_hash"], limit=50)

    return report


def auth_report(conn: sqlite3.Connection | None, start_iso: str) -> dict[str, Any]:
    report: dict[str, Any] = {}
    if conn is None:
        return report

    print_section("AUTH / USERS")

    if table_exists(conn, "users"):
        cols = columns(conn, "users")
        created_col = "created_at" if "created_at" in cols else None
        where = f"{created_col} >= ?" if created_col else "1=1"
        params = (start_iso,) if created_col else ()

        users = rows(
            conn,
            f"""
            SELECT
              id,
              email,
              name,
              plan,
              status,
              daily_limit,
              monthly_limit,
              created_at,
              last_key_issued_at
            FROM users
            WHERE {where}
            ORDER BY id DESC
            LIMIT 50
            """,
            params,
        )
        safe_users = []
        for u in users:
            email = u["email"] or ""
            masked = mask_email(email)
            safe_users.append(
                {
                    "id": u["id"],
                    "email": masked,
                    "name": u["name"],
                    "plan": u["plan"],
                    "status": u["status"],
                    "daily": u["daily_limit"],
                    "monthly": u["monthly_limit"],
                    "created_at": u["created_at"],
                    "last_key": u["last_key_issued_at"],
                }
            )
        report["users"] = safe_users
        print_table(safe_users, ["id", "email", "name", "plan", "status", "daily", "monthly", "created_at", "last_key"], limit=50)
    else:
        print("[WARN] users table not found")

    print_section("REQUEST KEY ATTEMPTS")
    if table_exists(conn, "request_key_attempts"):
        cols = columns(conn, "request_key_attempts")
        order_col = "created_at" if "created_at" in cols else "id"
        select = ", ".join([c for c in ("id", "email", "email_hash", "ip_hash", "status", "created_at", "sent", "provider") if c in cols])
        if not select:
            select = "*"
        attempts = rows(
            conn,
            f"SELECT {select} FROM request_key_attempts ORDER BY {order_col} DESC LIMIT 50",
        )
        safe_attempts = []
        for a in attempts:
            d = dict(a)
            if "email" in d:
                d["email"] = mask_email(d.get("email") or "")
            if "email_hash" in d and d["email_hash"]:
                d["email_hash"] = str(d["email_hash"])[:12]
            if "ip_hash" in d and d["ip_hash"]:
                d["ip_hash"] = str(d["ip_hash"])[:12]
            safe_attempts.append(d)
        report["request_key_attempts"] = safe_attempts
        if safe_attempts:
            print_table(safe_attempts, list(safe_attempts[0].keys()), limit=50)
        else:
            print("(no rows)")
    else:
        print("[WARN] request_key_attempts table not found")

    print_section("API USAGE")
    if table_exists(conn, "api_usage"):
        cols = columns(conn, "api_usage")
        select_cols = [c for c in ("id", "user_id", "endpoint", "created_at", "day", "month") if c in cols]
        if select_cols:
            usage_rows = rows(
                conn,
                f"""
                SELECT {', '.join(select_cols)}, COUNT(*) AS count
                FROM api_usage
                GROUP BY {', '.join(select_cols)}
                ORDER BY count DESC
                LIMIT 50
                """,
            )
            usage = [dict(r) for r in usage_rows]
            report["api_usage"] = usage
            if usage:
                print_table(usage, list(usage[0].keys()), limit=50)
            else:
                print("(no rows)")
        else:
            print("[WARN] api_usage columns not recognized")
    else:
        print("[WARN] api_usage table not found")

    return report


def payments_report(conn: sqlite3.Connection | None) -> dict[str, Any]:
    report: dict[str, Any] = {}
    print_section("BILLING / PAYMENTS")
    if conn is None or not table_exists(conn, "payments"):
        print("[WARN] payments table not found")
        return report

    payment_rows = rows(
        conn,
        """
        SELECT
          provider,
          event_type,
          external_id,
          email,
          plan,
          status,
          created_at,
          processed_at
        FROM payments
        ORDER BY id DESC
        LIMIT 50
        """,
    )

    safe = []
    for p in payment_rows:
        d = dict(p)
        d["email"] = mask_email(d.get("email") or "")
        if d.get("external_id"):
            d["external_id"] = str(d["external_id"])[:12] + "..."
        safe.append(d)

    report["payments"] = safe
    if safe:
        print_table(safe, ["provider", "event_type", "external_id", "email", "plan", "status", "created_at", "processed_at"], limit=50)
    else:
        print("(no rows)")

    print_section("PAYMENT STATUS SUMMARY")
    summary_rows = rows(
        conn,
        """
        SELECT provider, event_type, status, COUNT(*) AS count
        FROM payments
        GROUP BY provider, event_type, status
        ORDER BY count DESC
        LIMIT 50
        """,
    )
    summary = [dict(r) for r in summary_rows]
    report["payment_summary"] = summary
    print_table(summary, ["provider", "event_type", "status", "count"], limit=50)

    return report


def mask_email(email: str) -> str:
    if not email or "@" not in email:
        return email or ""
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        return local[:1] + "***@" + domain
    return local[:2] + "***@" + domain


def main() -> int:
    parser = argparse.ArgumentParser(description="SAS operational funnel report")
    parser.add_argument("--metrics-db", default=DEFAULT_METRICS_DB)
    parser.add_argument("--auth-db", default=DEFAULT_AUTH_DB)
    parser.add_argument("--hours", type=int, default=24, help="Window in hours. Default: 24")
    parser.add_argument("--days", type=int, default=None, help="Window in days. Overrides --hours if set")
    parser.add_argument("--show-recent", action="store_true", help="Show recent non-infrastructure activity")
    parser.add_argument("--json", action="store_true", help="Print final machine-readable JSON summary")
    args = parser.parse_args()

    if args.days is not None:
        label, start = dt_window(hours=None, days=args.days)
    else:
        label, start = dt_window(hours=args.hours, days=None)

    start_iso = start.isoformat()

    print_section("SAS FUNNEL REPORT")
    print(f"Window:       {label}")
    print(f"Start UTC:    {start_iso}")
    print(f"Metrics DB:   {args.metrics_db}")
    print(f"Auth DB:      {args.auth_db}")

    metrics_conn = connect(args.metrics_db)
    auth_conn = connect(args.auth_db)

    output: dict[str, Any] = {
        "window": label,
        "start_utc": start_iso,
        "metrics_db": args.metrics_db,
        "auth_db": args.auth_db,
    }

    output["metrics"] = metrics_report(metrics_conn, start_iso, show_recent=args.show_recent)
    output["auth"] = auth_report(auth_conn, start_iso)
    output["payments"] = payments_report(auth_conn)

    if metrics_conn:
        metrics_conn.close()
    if auth_conn:
        auth_conn.close()

    print_section("RECOMMENDED INTERPRETATION")
    print(
        "\n".join(
            [
                "- Treat /health, /readyz, HEAD / and /robots.txt as infrastructure, not product demand.",
                "- Product interest starts around /docs, /openapi.json, /public/demo/audit and /public/stats.",
                "- Conversion starts at /public/request-key, /v1/whoami, /v1/diff and checkout endpoints.",
                "- External validation requires request-key success from non-owner traffic and authenticated usage after that.",
                "- Investigate any 5xx on checkout, request-key, demo, whoami or diff before broad public launches.",
            ]
        )
    )

    if args.json:
        print_section("JSON SUMMARY")
        print(json.dumps(output, indent=2, ensure_ascii=False, default=str))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
