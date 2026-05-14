# SAS Billing and Plans

This document explains the hosted SAS billing model, plan logic, payment providers, and operational safeguards.

SAS remains open source under **GPL-3.0 + Durante Invariance License**. Billing applies to the hosted API service, support, integration, private deployment, or commercial licensing.

---

## 1. Hosted API plans

| Plan | Limit | Use case | Price |
|---|---:|---|---:|
| Free | 50 requests/day | Evaluation, individual development, testing | Free |
| Pro | 10,000 requests/month | Hosted API usage and basic email support | USD 99/month |
| Enterprise Cloud | Custom | High-volume usage, direct support, private integration | From USD 1,500/month |
| On-Premise License | Custom | Private deployment on customer infrastructure | From USD 15,000/year |
| Technical Pilot | Scoped | Integration guidance and use-case validation | USD 1,500-3,000 one-time |

---

## 2. Free API key flow

Users can request a Free key from the CLI:

```bash
pip install sas-client
sas request-key --email you@example.com --name "Your Name"
```

Or by HTTP:

```bash
curl -X POST https://sas-api.onrender.com/public/request-key \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com", "name": "Your Name"}'
```

Expected behavior:

1. Request is validated.
2. Email is normalized.
3. Rate limits are checked.
4. User is created or updated.
5. Free key is generated.
6. Key is sent automatically by email.
7. Public response does not expose the raw key.

Recommended safeguards:

- Rate limit by IP hash.
- Rate limit by email hash.
- Do not expose raw API keys in metrics.
- Do not expose raw IPs.
- Do not expose raw emails in public metrics.
- Disallow `/public/request-key` in `robots.txt`.

---

## 3. Pro payment flow

SAS supports hosted Pro checkout through:

- Polar;
- Mercado Pago.

High-level flow:

```text
User selects Pro
-> hosted checkout
-> payment provider confirms event
-> webhook validates event
-> user is created/updated as Pro
-> Pro API key is issued
-> key is sent by email
```

Expected Pro limit:

```text
10,000 requests/month
```

---

## 4. Polar

Typical endpoints:

```text
POST /billing/polar/checkout
POST /billing/polar/webhook
```

Event handling should be idempotent.

Recommended event handling:

| Event | Recommended action |
|---|---|
| `checkout.created` | Store/ignore as non-activating event |
| `order.created` | Store/ignore unless explicitly used |
| `subscription.created` | Activate Pro plan |
| `subscription.updated` | Update status/plan if needed |
| `subscription.canceled` | Deactivate or downgrade at period end |
| unknown event | Store as ignored event |

Important:

```text
Only payment-confirming events should activate Pro access.
```

---

## 5. Mercado Pago

Typical endpoints:

```text
POST /billing/mercadopago/checkout
POST /billing/mercadopago/webhook
```

Recommended behavior:

- validate provider signature when available;
- fetch payment details from provider API if needed;
- only activate paid plans after confirmed payment;
- store provider event IDs;
- make webhook processing idempotent;
- return clear 4xx for invalid payloads;
- return clear 5xx/502 for provider failures without exposing secrets.

---

## 6. Idempotency

Billing webhooks can be delivered multiple times.

Store:

```text
provider
event_type
external_id
email
plan
status
created_at
processed_at
```

Do not process the same provider/external ID twice.

Recommended statuses:

```text
processed
ignored_event_type
duplicate
invalid_signature
invalid_payload
provider_error
```

---

## 7. Checkout error handling

Checkout endpoints should avoid generic 500s for user or configuration problems.

Recommended mapping:

| Problem | Status |
|---|---:|
| Invalid plan | 400 |
| Missing email | 422 |
| Invalid email | 422 |
| Billing disabled/misconfigured | 503 |
| Provider API error | 502 |
| Unexpected internal error | 500 |

Every error should include:

```json
{
  "error": "Provider error",
  "message": "Could not create checkout session.",
  "request_id": "..."
}
```

Do not expose provider secrets, tokens, raw headers, or internal tracebacks.

---

## 8. Quota model

Current hosted quotas:

| Plan | Daily limit | Monthly limit |
|---|---:|---:|
| Free | 50 | null |
| Legacy | 5 | null |
| Pro | null | 10000 |

`/v1/whoami` should expose safe quota information:

```json
{
  "status": "ok",
  "plan": "pro",
  "active": true,
  "daily_limit": null,
  "monthly_limit": 10000,
  "daily_used": 2,
  "monthly_used": 32,
  "quota_allowed": true
}
```

---

## 9. Legacy shared key

The public legacy test key should not act as an unlimited bypass.

Recommended current behavior:

```text
email: legacy@sas.local
plan: legacy
daily_limit: 5
monthly_limit: null
```

After quota exhaustion, endpoints should return:

```text
429 Too Many Requests
```

The response should encourage users to request a personal Free key.

---

## 10. Upgrade nudges

Future conversion flow:

- when Free usage reaches 80% daily limit, send one soft email;
- when Free quota is exhausted, return 429 with upgrade/request-key message;
- avoid aggressive spam;
- do not send repeated emails every day without user intent.

Example 429 body:

```json
{
  "error": "Quota exceeded",
  "message": "Daily Free quota exceeded. Upgrade to Pro or wait for reset.",
  "plan": "free",
  "daily_limit": 50
}
```

---

## 11. Security checklist

Billing implementation should ensure:

- webhook secret validation;
- idempotent processing;
- no raw provider secrets in logs;
- no raw API keys in logs;
- no raw payment metadata in public metrics;
- clear 4xx/5xx mapping;
- retries are safe;
- user emails are masked in public/admin-safe outputs;
- all checkout and webhook events are timestamped.

---

## 12. Operations

Recommended daily check:

```bash
python scripts/funnel_report.py
```

Expected billing metrics:

```text
checkout_started
checkout_200
checkout_4xx
checkout_5xx
webhook_received
webhook_processed
webhook_ignored
pro_users_created
```
