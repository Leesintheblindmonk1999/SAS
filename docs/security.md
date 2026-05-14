# SAS Security Notes

This document summarizes security assumptions, current safeguards, and recommended hardening for the SAS hosted API and self-hosted deployments.

For vulnerability reports, also see:

```text
SECURITY.md
```

---

## 1. Security principles

SAS should follow these principles:

- no raw API keys in logs;
- no raw IPs in public metrics;
- no raw API key hashes in public metrics;
- no full request headers exposed;
- no internal traceback in API responses;
- explicit auth on protected endpoints;
- rate limits on public and authenticated endpoints;
- safe billing webhooks;
- secure defaults for self-hosting.

---

## 2. API keys

API keys should be treated as secrets.

Rules:

- never commit API keys;
- never print raw API keys in logs;
- never expose raw API keys in `/public/stats` or `/public/activity`;
- hash keys for metrics and usage correlation;
- allow users to rotate keys in future admin/dashboard flow.

Recommended headers:

```text
X-API-Key: sas_xxxxxxxxxxxxxxxxxxxxx
```

CLI environment variables:

```text
SAS_API_KEY
SAS_KEY
```

---

## 3. IP privacy

SAS metrics should store and expose only hashed IPs internally, and should not expose IP hashes publicly.

Recommended:

```text
raw IP       -> never in public metrics
ip_hash      -> internal only
country      -> public aggregate ok
request_id   -> internal/debug only, not public activity
```

Current monitoring uses anonymized country/path/status buckets for public activity.

---

## 4. Public endpoints

Public endpoints:

```text
GET  /health
GET  /readyz
GET  /robots.txt
HEAD /
GET  /public/stats
GET  /public/activity
POST /public/demo/audit
POST /public/request-key
```

Security posture:

| Endpoint | Risk | Controls |
|---|---|---|
| `/health` | low | no sensitive output |
| `/readyz` | medium | avoid secrets, show only readiness |
| `/public/stats` | medium | aggregate only |
| `/public/activity` | medium | anonymized only |
| `/public/demo/audit` | medium | payload limits, rate limits |
| `/public/request-key` | high | rate limit, email normalization, no key in response |
| `/robots.txt` | low | crawler guidance only |
| `HEAD /` | low | no body |

---

## 5. robots.txt

Recommended:

```text
User-agent: *
Allow: /
Disallow: /admin
Disallow: /v1
Disallow: /billing
Disallow: /public/request-key
```

Important:

```text
robots.txt is not a security boundary.
It is crawler guidance only.
```

---

## 6. Request validation

Validation errors should be useful but not leak payloads.

Recommended 422 body:

```json
{
  "error": "Validation error",
  "message": "Invalid request body or parameters.",
  "details": [
    {
      "loc": ["body", "email"],
      "msg": "Field required",
      "type": "missing"
    }
  ],
  "request_id": "..."
}
```

Do not include raw invalid inputs in validation responses or logs.

---

## 7. Rate limiting

Current required rate-limit classes:

| Surface | Suggested limit |
|---|---|
| `/public/request-key` | strict by IP + email hash |
| `/public/demo/audit` | strict by IP |
| `/v1/diff` Free | 50/day by key |
| `/v1/diff` Legacy | 5/day by key |
| `/v1/diff` Pro | 10,000/month by key |
| `/billing/*/checkout` | moderate by IP |
| `/billing/*/webhook` | provider-authenticated, idempotent |

Important improvement:

```text
Move in-memory rate limit buckets to SQLite-backed persistent rate limits.
```

Reason:

```text
In-memory buckets reset on Render restarts.
```

---

## 8. Payload size limits

Recommended before broad public launch:

| Endpoint | Suggested limit |
|---|---:|
| `/public/demo/audit` | 5 KB/request |
| `/public/request-key` | 2 KB/request |
| `/v1/diff` Free | 10 KB/request |
| `/v1/diff` Pro | 100 KB/request |
| `/v1/audit` Free | 10 KB/request |
| `/v1/chat` Free | 10 KB/request |

Reject oversized requests with:

```text
413 Payload Too Large
```

---

## 9. Billing security

Billing endpoints must validate provider authenticity.

Required:

- webhook signature validation;
- idempotency by provider event ID;
- no raw secrets in logs;
- no raw payment metadata in public metrics;
- 4xx for invalid payload/signature;
- 502 for provider failure;
- no duplicate plan activation.

See [`billing.md`](billing.md).

---

## 10. Admin and debug endpoints

Admin/debug endpoints must require:

```text
X-Admin-Secret
```

Debug endpoint behavior:

- disabled unless `ENABLE_DEBUG_ENDPOINTS=true`;
- returns 404 when disabled;
- returns 403 for invalid admin secret;
- returns only safe header snapshot;
- never exposes all headers;
- never exposes API keys.

---

## 11. CORS

Development may use:

```text
CORS_ALLOW_ORIGINS=*
```

Production should restrict CORS to known origins:

```text
https://leesintheblindmonk1999.github.io
https://your-production-domain.example
```

Allowed methods should include:

```text
GET
POST
HEAD
OPTIONS
```

---

## 12. Security headers

Recommended headers:

```text
X-Content-Type-Options: nosniff
X-Frame-Options: DENY or SAMEORIGIN
Referrer-Policy: no-referrer
Permissions-Policy: geolocation=(), microphone=(), camera=()
```

If Swagger `/docs` requires looser framing or script rules, configure carefully.

---

## 13. Logging

Log:

- request ID;
- country;
- hashed IP;
- method;
- path;
- status code;
- latency;
- hashed API key if needed internally;
- plan.

Do not log:

- raw API key;
- raw authorization headers;
- raw email in public metrics;
- full request body;
- billing secrets;
- SMTP credentials;
- provider tokens.

---

## 14. Error handling

Recommended mapping:

| Error | Status |
|---|---:|
| Missing API key | 401 |
| Invalid API key | 401 |
| Quota exceeded | 429 |
| Invalid JSON/body | 422 |
| Payload too large | 413 |
| Invalid checkout request | 400/422 |
| Provider failure | 502 |
| Unexpected internal failure | 500 |

All 500s should include:

```json
{
  "error": "Internal server error",
  "message": "The SAS API encountered an unexpected error.",
  "request_id": "..."
}
```

No traceback should be returned to clients.

---

## 15. Pre-launch checklist

Before broad public traffic:

- [ ] `GET /health` returns 200.
- [ ] `GET /readyz` returns 200.
- [ ] `GET /robots.txt` returns 200.
- [ ] `HEAD /` returns 200.
- [ ] invalid `/public/request-key` returns safe 422.
- [ ] missing API key returns 401.
- [ ] invalid API key returns 401.
- [ ] legacy quota returns 429 after limit.
- [ ] SourceTargetGuard regression returns MANIFOLD_RUPTURE.
- [ ] no raw keys in logs.
- [ ] no raw IPs in public metrics.
- [ ] checkout 500s are eliminated or controlled.
- [ ] smoke test workflow passes.

---

## 16. Vulnerability disclosure

Recommended public policy:

```text
Please report vulnerabilities privately to duranteg2@gmail.com.
Do not disclose vulnerabilities publicly before coordinated review.
Include reproduction steps, affected endpoint, expected impact, and suggested fix if available.
```

---

## 17. Security roadmap

Near-term:

- SQLite-backed persistent rate limits.
- Payload size limits.
- DB checks in `/readyz`.
- Funnel report script.
- Better webhook idempotency.
- API-key rotation endpoint.
- Optional user dashboard.

Mid-term:

- signed audit reports;
- per-user usage dashboard;
- audit log export;
- enterprise private deployment guide;
- external security review.
