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

PowerShell:

```powershell
$env:SAS_API_KEY="sas_xxxxxxxxxxxxxxxxxxxxx"
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

Check identity:

```bash
sas whoami
```

Run a source/response diff:

```bash
sas diff "source text" "response text"
```

Run the public demo without a key:

```bash
sas demo-audit \
  "The Eiffel Tower is located in Paris, France." \
  "The Eiffel Tower is located in Berlin, Germany."
```

---

## 3. Public system endpoints

### `GET /health`

Basic liveness check.

```bash
curl https://sas-api.onrender.com/health
```

Example:

```json
{
  "status": "ok",
  "kappa_d": 0.56
}
```

---

### `GET /readyz`

Granular readiness check for routers and databases.

```bash
curl https://sas-api.onrender.com/readyz
```

Current response shape:

```json
{
  "status": "ready",
  "service": "SAS - Symbiotic Autoprotection System",
  "version": "1.1.0",
  "kappa_d": 0.56,
  "databases": {
    "auth_db": true,
    "metrics_db": true,
    "audit_db": true,
    "rate_limit_db": true,
    "interaction_db": true
  },
  "routers": {
    "health": true,
    "audit": true,
    "diff": true,
    "admin": true,
    "metrics": true,
    "public_activity": true,
    "public_interaction_stats": true,
    "public_demo": true,
    "public_request_key": true,
    "whoami": true,
    "billing_polar": true,
    "billing_mercadopago": true,
    "chat": true,
    "audit_conversation": true,
    "status": true,
    "external_audit": false,
    "batch": true,
    "notarization": true,
    "interaction_stability": true
  }
}
```

Notes:

- `interaction_stability` depends on `ENABLE_INTERACTION_STABILITY=true`.
- `interaction_db` is an observability store; core SAS detection can remain operational even if observability is degraded.
- `/readyz` does not expose DB paths, credentials, table contents, raw errors, or secrets.

---

### `GET /robots.txt`

Crawler guidance. This is not a security boundary.

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

### `GET /integrity`

Technical and legal provenance certificate.

```bash
curl https://sas-api.onrender.com/integrity
```

Typical fields:

```json
{
  "status": "operational",
  "kappa_d": 0.56,
  "author": "Gonzalo Emir Durante",
  "protocol": "SAS v1.1.0 - Omni-Scanner ...",
  "registry": "TAD EX-2026-18792778",
  "license": "GPL-3.0 + Durante Invariance License v1.0"
}
```

---

## 4. Public product endpoints

### `GET /public/stats`

Public aggregate metrics. No raw IPs, raw API keys, API key hashes, emails, request IDs, or request bodies are exposed.

```bash
curl https://sas-api.onrender.com/public/stats
```

Use this endpoint for public transparency, landing status, and aggregate product activity.

---

### `GET /public/activity?limit=10`

Public anonymized activity feed.

```bash
curl "https://sas-api.onrender.com/public/activity?limit=10"
```

Notes:

- Activity is anonymized.
- Raw IPs and raw API keys are not exposed.
- This endpoint is intended for public operational transparency.

---

### `GET /public/interaction/stats?days=7`

Public aggregate stats for the experimental interaction-stability endpoint.

```bash
curl "https://sas-api.onrender.com/public/interaction/stats?days=7"
```

Example response:

```json
{
  "status": "ok",
  "period": "last_7_days",
  "total_analyses": 2,
  "avg_conversation_turns": 4.0,
  "avg_assistant_turns": 2.0,
  "avg_final_sigma": 0.0703,
  "avg_final_omega_t": 0.1079,
  "avg_demand_peak": 1.0,
  "threshold_crossed_pct": 1.0,
  "stability_below_kappa_pct": 1.0,
  "high_uncertainty_pct": 1.0,
  "avg_latency_ms": 6.41,
  "dominant_states_distribution": {
    "Ambivalent": 2
  },
  "plan_distribution": {
    "free": 1,
    "pro": 1
  },
  "sigma_buckets": {
    "0.00-0.24": 2
  },
  "demand_peak_buckets": {
    "0.75-1.00": 2
  },
  "privacy": {
    "raw_text_stored": false,
    "raw_api_keys_stored": false,
    "public_stats_are_aggregated": true
  }
}
```

Privacy guarantees:

- No raw submitted text.
- No request IDs.
- No raw API keys.
- No API key hashes.
- No input hashes.
- No content fingerprints.
- No per-user rows.

`days` range:

```text
1 <= days <= 90
```

---

### `GET /public/demo/audit`

Onboarding/help endpoint for the public demo.

```bash
curl https://sas-api.onrender.com/public/demo/audit
```

Returns recommended request shape and CLI usage.

---

### `POST /public/demo/audit`

Runs a public no-key demo audit.

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

Example response shape:

```json
{
  "status": "ok",
  "isi": 0.5,
  "kappa_d": 0.56,
  "verdict": "MANIFOLD_RUPTURE",
  "fired_modules": [
    "SourceTargetGuard: anchored entity/location shift..."
  ],
  "manipulation_alert": {
    "triggered": true,
    "sources": ["SourceTargetGuard"]
  },
  "demo": true
}
```

Notes:

- This endpoint is public.
- It is payload-limited and rate-limited.
- For authenticated production use, prefer `/v1/diff` or `/v1/batch`.

---

### `GET /public/request-key`

Onboarding/help endpoint for Free API key generation.

```bash
curl https://sas-api.onrender.com/public/request-key
```

Returns CLI and HTTP examples for requesting a key.

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

Validation guidance:

- Send JSON body.
- `email` is required.
- `name` is optional.
- Do not send email as a query parameter.
- The endpoint is disallowed in `robots.txt`.

Common validation response:

```json
{
  "error": "Validation error",
  "detail": "Missing required fields: email",
  "reason": "missing_email",
  "missing_fields": ["email"],
  "required_format": {
    "email": "string, valid email address, required",
    "name": "optional string, max 120 characters"
  }
}
```

---

## 5. Authenticated endpoints

### `GET /v1/whoami`

Shows key identity, plan, status, and quota.

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
  "plan": "free",
  "active": true,
  "email": "co***@example.com",
  "email_hash": "89b58b...",
  "daily_limit": 50,
  "monthly_limit": null,
  "daily_used": 1,
  "monthly_used": 1,
  "quota_allowed": true,
  "quota_reason": null
}
```

---

### `POST /v1/diff`

Primary forensic source/response endpoint.

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
  "isi": 0.25,
  "kappa_d": 0.56,
  "verdict": "MANIFOLD_RUPTURE",
  "fired_modules": [
    "SourceTargetGuard: year mismatch: 1889 -> 1950..."
  ],
  "manipulation_alert": {
    "triggered": true,
    "sources": ["SourceTargetGuard"]
  },
  "evidence": {
    "isi_final": 0.25,
    "kappa_d": 0.56,
    "fired_modules": []
  }
}
```

Recommended production use:

- Store `request_id` when present.
- Store `isi`, `verdict`, and `manipulation_alert`.
- Treat `MANIFOLD_RUPTURE` as a signal for retry, escalation, or human review.
- Do not treat SAS as a universal factual verifier.

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

### `POST /v1/batch`

Audits multiple source/response pairs in a single authenticated request.

```bash
curl -X POST https://sas-api.onrender.com/v1/batch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sas_xxxxxxxxxxxxxxxxxxxxx" \
  -d '{
    "experimental": true,
    "domain": "generic",
    "pairs": [
      {
        "source": "The Eiffel Tower is located in Paris, France, and was built in 1889.",
        "response": "The Eiffel Tower is located in Berlin, Germany, and was built in 1950."
      },
      {
        "source": "Water boils at 100 degrees Celsius at sea level.",
        "response": "Water boils at 100 degrees Celsius at sea level."
      }
    ]
  }'
```

Example response shape:

```json
{
  "status": "ok",
  "count": 2,
  "results": [
    {
      "index": 0,
      "status": "ok",
      "isi": 0.25,
      "kappa_d": 0.56,
      "verdict": "MANIFOLD_RUPTURE",
      "fired_modules": ["SourceTargetGuard"],
      "manipulation_alert": {
        "triggered": true,
        "sources": ["SourceTargetGuard"]
      },
      "error": null
    },
    {
      "index": 1,
      "status": "ok",
      "isi": 1.0,
      "kappa_d": 0.56,
      "verdict": "PERFECT_EQUILIBRIUM",
      "fired_modules": [],
      "manipulation_alert": {
        "triggered": false,
        "sources": []
      },
      "error": null
    }
  ],
  "batch": true,
  "latency_ms": 2.75
}
```

Notes:

- Protected by API key.
- Payload-limited.
- Covered by smoke tests.
- Individual item failures should not necessarily fail the full batch.

---

### `POST /v1/chat`

Hosted SAS chat endpoint.

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

## 6. Experimental interaction endpoints

### `GET /v1/interaction/stability/example`

Returns a ready-to-use demo payload for the interaction-stability endpoint.

```bash
curl https://sas-api.onrender.com/v1/interaction/stability/example
```

Typical fields:

```json
{
  "experimental_notice": "...",
  "likelihood_note": "...",
  "omega_note": "...",
  "sigma_note": "...",
  "threshold_note": "...",
  "conjecture_note": "...",
  "demand_note": "...",
  "theory_doi": "10.5281/zenodo.20335612",
  "conversation": [
    {"role": "user", "content": "Necesito esto urgente, es para ayer."},
    {"role": "assistant", "content": "Entendido, lo proceso."}
  ],
  "gamma": 0.85,
  "window": 4,
  "kappa_d": 0.56,
  "alpha": 2.0,
  "mode": "analyze",
  "normalize_demand": true
}
```

Notes:

- Public, no API key required.
- Feature-flag controlled.
- Persistently rate-limited.

---

### `POST /v1/interaction/stability`

Experimental heuristic endpoint for interaction stability research.

```bash
curl -X POST https://sas-api.onrender.com/v1/interaction/stability \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sas_xxxxxxxxxxxxxxxxxxxxx" \
  -d '{
    "conversation": [
      {"role": "user", "content": "Necesito esto urgente, es para ayer."},
      {"role": "assistant", "content": "Entendido, lo proceso."},
      {"role": "user", "content": "Ok, gracias. Podemos hacerlo paso a paso."},
      {"role": "assistant", "content": "Sí, claro. Empecemos con una versión mínima."}
    ],
    "gamma": 0.85,
    "window": 4,
    "kappa_d": 0.56,
    "alpha": 2.0,
    "mode": "analyze",
    "normalize_demand": true
  }'
```

PowerShell:

```powershell
$body = @{
  conversation = @(
    @{ role = "user"; content = "Necesito esto urgente, es para ayer." },
    @{ role = "assistant"; content = "Entendido, lo proceso." }
  )
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Method Post `
  -Uri "https://sas-api.onrender.com/v1/interaction/stability" `
  -Headers @{ "X-API-Key" = $env:SAS_API_KEY.Trim() } `
  -ContentType "application/json" `
  -Body $body | ConvertTo-Json -Depth 10
```

Example response shape:

```json
{
  "status": "completed",
  "mode": "analyze",
  "model_version": "interaction-stability-v1.2.1-mvp",
  "theory_reference": "stochastic_interaction_v1.2.0",
  "theory_doi": "10.5281/zenodo.20335612",
  "kappa_d_ref": 0.56,
  "theta_hat": 0.56,
  "alpha": 2.0,
  "trajectory": [
    {
      "t": 1,
      "raw_turn_index": 2,
      "user_action": "Rc",
      "agent_observation": "L",
      "demand": 1.0,
      "effective_window": 1,
      "belief": {
        "Open": 0.1029,
        "Ambivalent": 0.3561,
        "Saturated": 0.263,
        "Avoidant": 0.1766,
        "Defensive": 0.1014
      },
      "dominant_state": "Ambivalent",
      "dominant_probability": 0.3561,
      "omega_t": 0.0734,
      "belief_coherence_chi": 0.0734,
      "interaction_stability_sigma": 0.0305,
      "alerts": {
        "threshold_crossed": true,
        "stability_below_kappa": true,
        "high_uncertainty": true
      }
    }
  ],
  "summary": {
    "final_omega_t": 0.0734,
    "final_chi": 0.0734,
    "final_sigma": 0.0305,
    "final_dominant_state": "Ambivalent",
    "final_dominant_probability": 0.3561,
    "demand_peak": 1.0,
    "alerts": {
      "threshold_crossed": true,
      "stability_below_kappa": true,
      "high_uncertainty": true
    }
  },
  "request_id": "7bec74ea-300b-46db-b009-57a1c3c50e4f",
  "executed_at": "2026-06-01T18:55:05.078188+00:00",
  "input_hash": "1cce5708ce56cffd",
  "content_fingerprint": "fa710b9bf8f0a151",
  "skipped_turns": []
}
```

Interpretation cautions:

- Outputs are heuristic model constructs, not empirical measurements.
- Hidden states are model states, not psychological facts.
- `omega_t` measures belief concentration, not desirability.
- `theta_hat=0.56` is an SAS-aligned experimental default, not an observed `theta_B`.
- Do not use this endpoint for psychological assessment, legal proceedings, or behavioral intervention.

Limits and validation:

| Field | Constraint |
|---|---|
| `conversation` | Required, 1–100 turns |
| `role` | Max 50 characters |
| `content` | Max 4000 characters per turn |
| `gamma` | `(0, 1)` |
| `window` | `1–50` |
| `kappa_d` | `(0, 1)` |
| `alpha` | `0–20` |
| `mode` | `analyze` only for MVP |
| `normalize_demand` | Boolean |

Observability:

- Successful analyses are recorded in `interaction.db`.
- Raw conversation text is not stored in the interaction observability store.
- Public aggregate stats are exposed through `/public/interaction/stats`.

---

## 7. Billing endpoints

Billing endpoints are used by hosted checkout and webhooks.

Checkout endpoints:

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

## 8. Error responses

### 400

Bad request or explicit guidance error.

Example: email sent in query string for `/public/request-key`.

```json
{
  "error": "Validation error",
  "reason": "email_in_query",
  "message": "Use POST with JSON body."
}
```

---

### 401

Missing or invalid API key.

Example:

```json
{
  "detail": "Invalid API key"
}
```

CLI behavior:

```text
SAS API error 401: Missing API key. Set SAS_API_KEY, SAS_KEY, or pass api_key=...
```

---

### 422

Validation error. The API returns sanitized details and examples.

Example:

```json
{
  "error": "Validation error",
  "message": "Invalid request body or parameters.",
  "details": [
    {
      "loc": ["header", "X-API-Key"],
      "msg": "Field required",
      "type": "missing"
    }
  ],
  "request_id": "868f98a3-29c9-4d5f-be43-b532ae3434d1"
}
```

For `/public/request-key`, validation errors include stronger onboarding guidance:

```json
{
  "error": "Validation error",
  "detail": "Missing required fields: email",
  "reason": "missing_email",
  "missing_fields": ["email"],
  "required_format": {
    "email": "string, valid email address, required",
    "name": "optional string, max 120 characters"
  }
}
```

---

### 429

Rate limit or quota exceeded.

Possible causes:

- public demo rate limit;
- request-key abuse protection;
- interaction-stability rate limit;
- Free daily quota exceeded;
- plan quota exceeded.

Typical response shape:

```json
{
  "detail": {
    "error": "Persistent rate limit exceeded",
    "message": "Too many requests for this endpoint. Please wait and retry.",
    "scope": "interaction_stability_post",
    "limit": 10,
    "window_seconds": 600,
    "current_count": 10,
    "retry_after_seconds": 471
  }
}
```

Client behavior:

- respect `Retry-After` when present;
- use exponential backoff for transient pressure;
- do not loop aggressively.

---

### 503

Feature disabled or temporarily unavailable.

Interaction stability may return `503` if disabled by feature flag:

```json
{
  "detail": {
    "error": "endpoint_disabled",
    "message": "The interaction stability endpoint is currently disabled."
  }
}
```

---

### 500

Unexpected server error. Should include `request_id` but no internal traceback.

```json
{
  "error": "Internal server error",
  "message": "The SAS API encountered an unexpected error.",
  "kappa_d": 0.56,
  "request_id": "..."
}
```

---

## 9. Rate limits and payload limits

Current operational hardening includes:

| Surface | Protection |
|---|---|
| `/public/request-key` | Persistent rate limit + validation logging |
| `/public/demo/audit` | Persistent rate limit + payload limit |
| `/v1/interaction/stability/example` | Persistent public GET limit |
| `/v1/interaction/stability` | Persistent authenticated POST limit |
| `/v1/diff` | Payload limit |
| `/v1/audit` | Payload limit |
| `/v1/batch` | Schema limits + API-key auth |
| `/v1/chat` | Payload limit |

Interaction-specific persistent limits:

| Method | Path | Limit |
|---|---|---:|
| `GET` | `/v1/interaction/stability/example` | 30 requests / 600 seconds / IP |
| `POST` | `/v1/interaction/stability` | 10 requests / 600 seconds / IP |

---

## 10. Recommended client behavior

For production integrations:

1. Use `/v1/diff` for source-response auditing.
2. Use `/v1/batch` for multiple source-response pairs.
3. Store `request_id`, `isi`, `verdict`, `manipulation_alert`, and `fired_modules`.
4. Treat `MANIFOLD_RUPTURE` as a flag for retry, escalation, or human review.
5. Use `/v1/interaction/stability` only as an experimental interaction-stability signal.
6. Store `request_id`, `input_hash`, and `content_fingerprint` when using interaction stability.
7. Implement retry with backoff for transient `5xx`.
8. Respect `Retry-After` on `429`.
9. Do not retry `401` or `422` without fixing the key or payload.
10. Do not treat SAS as an automatic legal or factual certification layer.

---

## 11. Privacy model

See [`../PRIVACY.md`](../PRIVACY.md).

Summary:

- SAS does not publish raw IPs.
- SAS does not publish raw API keys.
- SAS does not publish request bodies.
- Interaction observability does not store raw conversation text.
- Public interaction stats expose aggregate metrics only.
- Hashes and fingerprints are used for reproducibility, diagnostics, and abuse prevention.

---

## 12. Operational reporting

Run on the server:

```bash
python scripts/funnel_report.py --hours 24 --show-recent
```

Or:

```bash
python scripts/funnel_report.py --days 3 --show-recent --json
```

The report separates:

- infrastructure traffic;
- discovery;
- trial;
- conversion;
- authenticated usage;
- validation errors;
- audit DB events;
- rate-limit events;
- interaction-stability usage.

---

## 13. OpenAPI / interactive docs

FastAPI docs:

```text
https://sas-api.onrender.com/docs
```

For automated clients, prefer stable fields documented here over undocumented internal fields.

Experimental endpoints may evolve as the research framework is calibrated.
