# SAS API Documentation

This document summarizes the public and authenticated HTTP API for **SAS — Symbiotic Autoprotection System**.

Hosted API:

```text
https://sas-api.onrender.com
```

Interactive FastAPI docs:

```text
https://sas-api.onrender.com/docs
```

---

## 1. Authentication

Authenticated endpoints require:

```text
X-API-Key: sas_xxxxxxxxxxxxxxxxxxxxx
```

Example:

```bash
curl https://sas-api.onrender.com/v1/whoami \
  -H "X-API-Key: sas_xxxxxxxxxxxxxxxxxxxxx"
```

The official CLI reads keys from:

```text
SAS_API_KEY
SAS_KEY
```

---

## 2. Official CLI

Install:

```bash
pip install sas-client
```

Request a Free key:

```bash
sas request-key --email you@example.com --name "Your Name"
```

Set key:

```bash
export SAS_API_KEY="sas_xxxxxxxxxxxxxxxxxxxxx"
```

PowerShell:

```powershell
$env:SAS_API_KEY="sas_xxxxxxxxxxxxxxxxxxxxx"
```

Check identity:

```bash
sas whoami
```

Run diff:

```bash
sas diff "source text" "response text"
```

---

## 3. Public endpoints

### `GET /health`

Basic liveness check.

```bash
curl https://sas-api.onrender.com/health
```

Example response:

```json
{
  "status": "ok",
  "kappa_d": 0.56
}
```

---

### `GET /readyz`

Readiness check for routers and service configuration.

```bash
curl https://sas-api.onrender.com/readyz
```

Example response:

```json
{
  "status": "ready",
  "service": "SAS - Symbiotic Autoprotection System",
  "version": "1.1.0",
  "kappa_d": 0.56,
  "routers": {
    "health": true,
    "audit": true,
    "diff": true,
    "public_demo": true,
    "public_request_key": true,
    "whoami": true
  }
}
```

Recommended future addition:

```json
{
  "databases": {
    "auth_db": true,
    "metrics_db": true
  }
}
```

---

### `GET /robots.txt`

Crawler guidance.

```bash
curl https://sas-api.onrender.com/robots.txt
```

Expected:

```text
User-agent: *
Allow: /
Disallow: /admin
Disallow: /v1
Disallow: /billing
Disallow: /public/request-key
```

---

### `HEAD /`

Uptime monitor endpoint. Returns `200 OK` with no body.

```bash
curl -I https://sas-api.onrender.com/
```

---

### `GET /public/stats`

Public aggregate metrics. No raw IPs, API keys, API key hashes, or request IDs are exposed.

```bash
curl https://sas-api.onrender.com/public/stats
```

---

### `GET /public/activity?limit=10`

Public anonymized activity feed.

```bash
curl "https://sas-api.onrender.com/public/activity?limit=10"
```

---

### `POST /public/demo/audit`

Runs a public no-key demo audit.

Request:

```bash
curl -X POST https://sas-api.onrender.com/public/demo/audit \
  -H "Content-Type: application/json" \
  -d '{
    "source": "The Eiffel Tower is located in Paris, France.",
    "response": "The Eiffel Tower is located in Berlin, Germany."
  }'
```

CLI:

```bash
sas demo-audit \
  "The Eiffel Tower is located in Paris, France." \
  "The Eiffel Tower is located in Berlin, Germany."
```

Response fields:

```json
{
  "status": "ok",
  "isi": 0.6,
  "kappa_d": 0.56,
  "verdict": "MINOR_DRIFT",
  "manipulation_alert": {
    "triggered": false,
    "sources": []
  }
}
```

The public demo may return a simplified response compared with `/v1/diff`.

---

### `POST /public/request-key`

Requests a Free API key by email.

```bash
curl -X POST https://sas-api.onrender.com/public/request-key \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com", "name": "Your Name"}'
```

CLI:

```bash
sas request-key --email you@example.com --name "Your Name"
```

Example success:

```json
{
  "status": "ok",
  "message": "API key sent by email.",
  "plan": "free",
  "email_delivery": {
    "sent": true,
    "provider": "smtp"
  }
}
```

Notes:

- This endpoint is public.
- It should be rate limited by IP and email hash.
- It is disallowed in `robots.txt`.
- It should not expose raw API keys in public metrics.

---

## 4. Authenticated endpoints

### `GET /v1/whoami`

Shows key identity, plan, and quota.

```bash
curl https://sas-api.onrender.com/v1/whoami \
  -H "X-API-Key: sas_xxxxxxxxxxxxxxxxxxxxx"
```

CLI:

```bash
sas whoami
```

Example response:

```json
{
  "status": "ok",
  "plan": "pro",
  "active": true,
  "email": "co***@hotmail.com",
  "email_hash": "c1fd8e...",
  "daily_limit": null,
  "monthly_limit": 10000,
  "daily_used": 2,
  "monthly_used": 32,
  "quota_allowed": true,
  "quota_reason": null
}
```

---

### `POST /v1/diff`

Primary forensic endpoint.

Compares source against generated response.

Request:

```bash
curl -X POST https://sas-api.onrender.com/v1/diff \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sas_xxxxxxxxxxxxxxxxxxxxx" \
  -d '{
    "text_a": "The Eiffel Tower is located in Paris, France. It was built in 1889.",
    "text_b": "The Eiffel Tower is located in Berlin, Germany. It was built in 1950.",
    "experimental": true
  }'
```

CLI:

```bash
sas diff \
  "The Eiffel Tower is located in Paris, France. It was built in 1889." \
  "The Eiffel Tower is located in Berlin, Germany. It was built in 1950."
```

Important response fields:

```json
{
  "manifold_score": 0.25,
  "isi": 0.25,
  "verdict": "MANIFOLD_RUPTURE",
  "manipulation_alert": {
    "triggered": true,
    "sources": ["SourceTargetGuard"]
  },
  "confidence": 0.85,
  "evidence": {
    "isi_final": 0.25,
    "kappa_d": 0.56,
    "fired_modules": []
  }
}
```

---

### `POST /v1/audit`

Audits one text. Useful for single-output checks where a source/response pair is not available.

```bash
curl -X POST https://sas-api.onrender.com/v1/audit \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sas_xxxxxxxxxxxxxxxxxxxxx" \
  -d '{
    "text": "The Eiffel Tower is located in Berlin, Germany.",
    "experimental": true
  }'
```

CLI:

```bash
sas audit "The Eiffel Tower is located in Berlin, Germany."
```

For source-grounded use cases, prefer `/v1/diff`.

---

### `POST /v1/chat`

Chat endpoint for hosted SAS interactions.

```bash
curl -X POST https://sas-api.onrender.com/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sas_xxxxxxxxxxxxxxxxxxxxx" \
  -d '{"message": "Explain κD = 0.56 in one paragraph."}'
```

CLI:

```bash
sas chat "Explain κD = 0.56 in one paragraph."
```

---

## 5. Billing endpoints

Billing endpoints are used by hosted checkout and webhooks.

Typical public checkout endpoints:

```text
POST /billing/polar/checkout
POST /billing/mercadopago/checkout
```

Webhook endpoints:

```text
POST /billing/polar/webhook
POST /billing/mercadopago/webhook
```

See [`billing.md`](billing.md).

---

## 6. Error responses

### 401

Missing or invalid API key.

Example CLI message:

```text
SAS API error 401: Missing API key. Set SAS_API_KEY, SAS_KEY, or pass api_key=...
```

### 422

Validation error. The API returns sanitized details and examples.

Example:

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
  "request_id": "868f98a3-29c9-4d5f-be43-b532ae3434d1",
  "examples": {
    "request_key": {
      "method": "POST",
      "path": "/public/request-key",
      "json": {
        "email": "you@example.com",
        "name": "Your Name"
      }
    }
  }
}
```

### 429

Rate limit or quota exceeded.

Example cases:

- Free daily quota exceeded.
- Legacy shared key exceeded 5 requests/day.
- Too many key requests from the same IP/email.

### 500

Unexpected server error. Should include `request_id` but no internal traceback.

---

## 7. Recommended client behavior

For production integrations:

1. Use `/v1/diff` for source-response auditing.
2. Store `request_id`, `isi`, `verdict`, and `evidence.fired_modules`.
3. Treat `MANIFOLD_RUPTURE` as a flag for retry, escalation, or human review.
4. Treat `MINOR_DRIFT` as acceptable or reviewable depending on domain.
5. Implement retry with backoff for transient 5xx.
6. Do not retry 401/422 without fixing the input/key.
7. Monitor 429 and upgrade plan or reduce request rate.

---

## 8. Future endpoint: `/v1/batch`

Planned endpoint for batch auditing.

Draft request:

```json
{
  "pairs": [
    {
      "text_a": "source 1",
      "text_b": "response 1"
    },
    {
      "text_a": "source 2",
      "text_b": "response 2"
    }
  ],
  "experimental": true
}
```

Suggested limits:

| Plan | Max pairs per batch |
|---|---:|
| Free | 5 |
| Pro | 100 |
| Enterprise | Custom |
