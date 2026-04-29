# SAS Architecture Overview

This document describes the high-level architecture of **SAS - Symbiotic Autoprotection System**.

SAS is an API-based framework for structural coherence auditing and hallucination signal detection in generative AI outputs.

---

## High-Level Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│ Client                                                      │
│ curl, Python, JavaScript, internal AI systems               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ FastAPI Gateway                                              │
│                                                             │
│  /health     /v1/audit     /v1/diff     /v1/chat            │
│                                                             │
│ Middleware: Auth → Rate Limit → CORS → Security Headers     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ Core Detection Engine                                        │
│                                                             │
│  quick_diff / detector pipeline                              │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ TDA / ISI    │  │ NIG          │  │ E9-E12 Modules     │  │
│  │ Homology     │  │ Numerical    │  │ Contradiction,     │  │
│  │ Structure    │  │ Integrity    │  │ Temporal, Topic    │  │
│  └──────────────┘  └──────────────┘  └───────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ Response                                                     │
│ { isi, verdict, confidence, evidence, fired_modules }        │
└─────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. TDA - Topological Data Analysis

TDA is used to compare the semantic structure of two texts.

The core pipeline uses persistent homology to measure structural similarity and produce the **Invariant Similarity Index (ISI)**.

Primary responsibilities:

- Compare semantic manifolds
- Detect structural rupture
- Produce a bounded ISI score
- Support the `κD = 0.56` threshold

### 2. ISI - Invariant Similarity Index

The ISI is the main structural coherence score used by SAS.

Operational interpretation:

```text
ISI >= κD  → structurally coherent
ISI <  κD  → potential manifold rupture
```

### 3. κD = 0.56

`κD = 0.56` is the semantic invariance threshold used by SAS.

It acts as the operational decision boundary for structural coherence.

### 4. NIG - Numerical Invariance Guard

NIG validates numerical claims and detects numerical inconsistencies.

Examples:

- Incorrect arithmetic
- Impossible numerical relationships
- Contradictions involving quantities

Typical penalty range:

```text
×0.3 to ×0.7
```

### 5. E9-E12 Thermal Modules

These modules are optional high-precision detectors that act as independent penalty factors.

| Module | Detection Target | Penalty |
|--------|------------------|---------|
| E9 | Logical contradiction | ×0.5 |
| E10 | Fact grounding violation | ×0.3 |
| E11 | Temporal inconsistency | ×0.4 |
| E12 | Abrupt topic shift | ×0.6 |

Modules are applied only when they detect a clear signal.

---

## Data Flow

1. Input validation
2. Text preparation and splitting
3. Embedding generation
4. TDA computation
5. ISI calculation
6. NIG validation
7. E9-E12 execution, if enabled
8. Penalty cascade
9. Verdict assignment
10. Evidence packaging

---

## Penalty Cascade

Each module returns:

```text
triggered: true | false
penalty: value in (0, 1]
evidence: explanation
```

If a module is not triggered, no penalty is applied.

If triggered:

```text
isi_final = isi_hard × penalty_1 × penalty_2 × ...
```

This preserves the core ISI calculation while allowing high-precision signals to reduce the final score.

---

## Verdict Assignment

Typical verdicts include:

| Verdict | Meaning |
|---------|---------|
| `EQUILIBRIUM` | Structural coherence preserved |
| `MANIFOLD_RUPTURE` | Structural coherence rupture detected |
| `IDENTICAL` | Texts are identical or near-identical |
| `ERROR` | Internal processing issue or invalid input |

---

## Key Constants

```python
KAPPA_D = 0.56          # Semantic invariance threshold
MIN_TEXT_LENGTH = 30    # Minimum characters for analysis
TIMEOUT_SECONDS = 15    # Maximum scan time
```

---

## Database Schema

### users / API keys

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| api_key_hash | TEXT | SHA-256 hashed key |
| is_premium | BOOLEAN | 0 = free, 1 = pro |
| created_at | TIMESTAMP | Key generation date |
| last_used | TIMESTAMP | Last access |

### rate limit logs

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| api_key_hash | TEXT | SHA-256 hashed key |
| request_date | TEXT | Request date |
| endpoint | TEXT | API endpoint |

The rate limit is calculated using request counts per API key per day.

---

## Deployment Options

| Option | Command |
|--------|---------|
| Local development | `uvicorn src.api.main:app --reload` |
| Docker | `docker compose up --build` |
| Production | `gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.api.main:app` |

---

## Environment Variables

```ini
ADMIN_SECRET=change-me
FREE_REQUESTS_PER_DAY=50
MODULES_ENABLED=E9,E10,E11,E12
CORS_ALLOW_ORIGINS=*
```

For production, restrict `CORS_ALLOW_ORIGINS` to trusted domains.

---

## Performance Metrics

| Operation | Average Latency |
|-----------|-----------------|
| `/health` | <5 ms |
| `/v1/audit` short text | ~1 s |
| `/v1/audit` long text | ~2-3 s |
| `/v1/diff` | ~2 s |
| `/v1/chat` | ~3-5 s, depending on LLM backend |

---

## Security Layers

SAS includes the following security layers:

- API key authentication
- SHA-256 hashed key storage
- Rate limiting per API key
- Input validation
- Timeout protection
- Configurable CORS
- Recommended HTTPS deployment
- Admin secret for key generation

---

## Scope

SAS is designed for structural coherence auditing and hallucination signal detection.

It is not a universal factual verification system and should not be presented as legal certification.