# SAS — Symbiotic Autoprotection System

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19702379.svg)](https://doi.org/10.5281/zenodo.19702379)
[![Landing Page](https://img.shields.io/badge/🌐-Landing_Page-0a0e17?style=flat&logo=github)](https://leesintheblindmonk1999.github.io/sas-landing/)
[![API Online](https://img.shields.io/badge/API-online-brightgreen)](https://sas-api.onrender.com)
[![PyPI](https://img.shields.io/pypi/v/sas-client?label=sas-client&color=blue)](https://pypi.org/project/sas-client/)
[![API Docs](https://img.shields.io/badge/API-FastAPI-009688)](https://sas-api.onrender.com/docs)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](requirements.txt)
[![License](https://img.shields.io/badge/license-GPL--3.0%20%2B%20Durante%20Invariance-blue)](LICENSE.md)
[![Status](https://img.shields.io/badge/status-research%20alpha-orange)](#scope-and-limitations)
[![Benchmark](https://img.shields.io/badge/benchmark-98.8%25%20accuracy-brightgreen)](docs/benchmark_complete_20260429_172647.json)
[![OTS Proof](https://img.shields.io/badge/OpenTimestamps-proof-blueviolet)](docs/benchmark_complete_20260429_172647.json.ots)
[![Smoke Test](https://github.com/Leesintheblindmonk1999/SAS/actions/workflows/smoke_test.yml/badge.svg)](https://github.com/Leesintheblindmonk1999/SAS/actions/workflows/smoke_test.yml)

**SAS — Symbiotic Autoprotection System** is an open-source defensive AI auditing system.

It provides an API and research framework for auditing:

- structural coherence in generated text;
- source/response semantic rupture;
- hallucination-risk signals;
- batch comparison workflows;
- experimental temporal interaction stability;
- operational traceability without storing raw submitted content.

The core structural signal is the **Invariant Similarity Index (ISI)** compared against **κD = 0.56** — the Durante Constant.

```text
ISI >= 0.56  →  structurally coherent
ISI <  0.56  →  MANIFOLD_RUPTURE — potential structural hallucination signal
```

> SAS is not a universal factual oracle. It is a defensive audit layer for generating reproducible evidence about structural coherence, semantic divergence, and interaction stability.

---

## Public API

Hosted API:

```text
https://sas-api.onrender.com
```

Interactive docs:

```text
https://sas-api.onrender.com/docs
```

Landing page:

```text
https://leesintheblindmonk1999.github.io/sas-landing/
```

---

## Try it in 30 seconds

No API key, no registration:

```bash
curl -X POST https://sas-api.onrender.com/public/demo/audit \
  -H "Content-Type: application/json" \
  -d '{
    "source": "The Eiffel Tower is in Paris, France. It was built in 1889.",
    "response": "The Eiffel Tower is in Berlin, Germany. It was built in 1950."
  }'
```

Expected shape:

```json
{
  "status": "ok",
  "isi": 0.041,
  "kappa_d": 0.56,
  "verdict": "MANIFOLD_RUPTURE",
  "fired_modules": ["NIG", "SourceTargetGuard"],
  "demo": true
}
```

Or from the CLI:

```bash
pip install sas-client

sas demo-audit \
  "The Eiffel Tower is in Paris, France. It was built in 1889." \
  "The Eiffel Tower is in Berlin, Germany. It was built in 1950."
```

---

## Get a Free API key

```bash
sas request-key --email you@example.com --name "Your Name"
```

Free keys are delivered by email automatically.

Then:

```bash
export SAS_API_KEY="sas_xxxxxxxxxxxxxxxxxxxxx"

sas whoami

sas diff "The contract is governed by Argentine law." \
         "The contract is NOT governed by Argentine law."
```

Hosted Free plan: **50 requests/day**, no credit card.

---

## Main capabilities

### Structural Coherence Auditing

SAS compares source text against generated text and checks whether the response preserves structural coherence.

Primary endpoints:

```text
POST /v1/diff
POST /v1/audit
POST /v1/batch
```

Core components:

| Component | Function |
|---|---|
| **TDA** | Topological Data Analysis — persistent homology H₀ + H₁, Wasserstein distance |
| **NIG** | Numerical Invariance Guard — detects year, quantity, and measurement mutations |
| **SourceTargetGuard** | Detects critical source-response mutations: locations, entities, dates |
| **E9** | Logical contradiction detection |
| **E10** | Fact grounding — unsupported claims vs. source |
| **E11** | Temporal inconsistency detection |
| **E12** | Abrupt topic-shift detection |

Pipeline:

```text
Source text A + Response text B
        │
        ▼
[Layer 0]  Lexical Overlap Guard
[Layer 1]  TDA: Persistent Homology H₀ + H₁  →  ISI_TDA
[Layer 2]  NIG: Numerical Invariance Guard    →  ISI_NIG
[Core]     ISI_HARD = min(ISI_TDA, ISI_NIG)
[SAS]      E9-E12 + SourceTargetGuard         →  module penalties
        │
        ├── ISI_FINAL >= 0.56  →  COHERENT
        └── ISI_FINAL <  0.56  →  MANIFOLD_RUPTURE
```

No GPU. No external LLM API required for the core detector.

---

## Batch auditing

`POST /v1/batch` audits multiple source/response pairs in a single authenticated request.

Example:

```bash
curl -X POST https://sas-api.onrender.com/v1/batch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $SAS_API_KEY" \
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

The endpoint is API-key protected, payload-limited, audited, and covered by smoke tests.

---

## Experimental Interaction Stability Auditing

SAS includes an experimental temporal-interaction module:

```text
GET  /v1/interaction/stability/example
POST /v1/interaction/stability
GET  /public/interaction/stats
```

This module is based on the research line:

**A Control-Theoretic Model for Stochastic Interaction under Hidden-State Uncertainty and Demand-Sensitive Response Degradation**  
DOI: `10.5281/zenodo.20335612`

It estimates a heuristic trajectory over hidden-state model constructs:

```text
Open · Ambivalent · Saturated · Avoidant · Defensive
```

It computes:

| Field | Meaning |
|---|---|
| `omega_t` | Normalized belief-state concentration: `1 - H(b_t) / ln(|S|)` |
| `belief_coherence_chi` | Backward-compatible alias of `omega_t` |
| `dominant_state` | Most probable hidden-state construct under the model |
| `dominant_probability` | Probability of the dominant state |
| `interaction_stability_sigma` | Belief concentration penalized by historical demand above threshold |
| `demand_peak` | Peak historical demand estimate |
| `content_fingerprint` | Hash/fingerprint for traceability without storing raw text |

Important limitation:

> `omega_t` / `belief_coherence_chi` measures belief concentration, not whether the dominant state is desirable. High concentration on a defensive state may indicate confident degradation, not healthy stability.

Example:

```bash
curl -X POST https://sas-api.onrender.com/v1/interaction/stability \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $SAS_API_KEY" \
  -d '{
    "conversation": [
      {"role": "user", "content": "Necesito esto urgente, es para ayer."},
      {"role": "assistant", "content": "Entendido, lo proceso."},
      {"role": "user", "content": "Ok, gracias. Podemos hacerlo paso a paso."},
      {"role": "assistant", "content": "Sí, claro. Empecemos con una versión mínima."}
    ]
  }'
```

The endpoint is experimental, API-key protected, feature-flagged, payload-limited, persistently rate-limited, and instrumented through an observability store.

---

## Operational hardening

SAS is designed to fail safely and remain observable.

| Layer | Purpose |
|---|---|
| API-key authentication | Protects `/v1/*` endpoints and hosted usage |
| Payload limits | Rejects oversized requests before expensive logic runs |
| Persistent rate limiting | SQLite-backed rate-limit events that survive restarts |
| `audit.db` | Persistent API audit trail without raw IPs or request bodies |
| `metrics.db` | Aggregate request metrics, status buckets, latency, plan buckets |
| `rate_limit.db` | Allowed/blocked rate-limit events |
| `interaction.db` | Experimental interaction-stability observability metadata |
| `request_id` | Traceability across logs, metrics, audit, and responses |
| `content_fingerprint` | Reproducibility without storing raw conversation text |
| GitHub Actions smoke tests | Production checks for health, readiness, demo, auth, batch, and interaction stability |
| `/readyz` | Granular readiness for routers and databases |
| `funnel_report.py` | Operational report separating infrastructure traffic from product traffic |

---

## Privacy and observability

SAS stores operational metadata for reliability, abuse prevention, reproducibility, and aggregate research.

For the interaction-stability endpoint, SAS may store:

- request ID;
- timestamp;
- short hashed API-key identifier;
- user/plan bucket;
- turn counts;
- final dominant state;
- final `omega_t`;
- final `sigma`;
- demand peak;
- alert flags;
- input hash;
- content fingerprint;
- latency.

SAS does **not** store raw conversation text in the interaction observability store.

Public stats expose only aggregate data. They do not expose raw text, API keys, API-key hashes, input hashes, content fingerprints, request IDs, or per-user rows.

See: [PRIVACY.md](PRIVACY.md)

---

## Live operational snapshot

Public aggregate metrics:

```bash
curl https://sas-api.onrender.com/public/stats
curl "https://sas-api.onrender.com/public/activity?limit=10"
curl "https://sas-api.onrender.com/public/interaction/stats"
```

Public endpoints expose only aggregate and anonymized activity. No raw IPs, API keys, emails, or request bodies are published.

---

## API endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/health` | None | Health check |
| `GET` | `/readyz` | None | Granular router/database readiness |
| `GET` | `/integrity` | None | Legal and technical provenance certificate |
| `POST` | `/public/demo/audit` | None | Public demo — forensic pipeline |
| `GET` | `/public/stats` | None | Aggregate usage metrics |
| `GET` | `/public/activity` | None | Recent anonymized activity |
| `GET` | `/public/interaction/stats` | None | Aggregate interaction-stability stats |
| `GET` | `/public/request-key` | None | Free key onboarding instructions |
| `POST` | `/public/request-key` | None | Free API key by email |
| `GET` | `/v1/whoami` | API Key | Plan, quota, and key status |
| `POST` | `/v1/diff` | API Key | Forensic source/response diff |
| `POST` | `/v1/audit` | API Key | Single-text structural audit |
| `POST` | `/v1/batch` | API Key | Batch structural audit |
| `POST` | `/v1/chat` | API Key | Honest chat with κD filter |
| `GET` | `/v1/interaction/stability/example` | None | Experimental example payload, feature-flag controlled |
| `POST` | `/v1/interaction/stability` | API Key | Experimental interaction-stability analysis |
| `GET` | `/robots.txt` | None | Crawler guidance |

Full documentation:

```text
https://sas-api.onrender.com/docs
docs/api.md
```

---

## Benchmark — 2,000 pairs, reproducible, Bitcoin-anchored

| Metric | Result |
|---|---:|
| Evaluated pairs | 2,000 |
| Hallucination pairs | 1,000 |
| Clean pairs | 1,000 |
| **Accuracy** | **98.80%** |
| **Precision** | **100.00%** |
| **Recall** | **97.60%** |
| **F1 score** | **98.79%** |
| **False positives** | **0** |
| κD threshold | 0.56 |
| Avg ISI (hallucination) | 0.072993 |
| Avg ISI (clean) | 1.000000 |

Confusion matrix:

|  | Actual hallucination | Actual clean |
|---|---:|---:|
| Predicted hallucination | TP = 976 | FP = **0** |
| Predicted clean | FN = 24 | TN = 1,000 |

Traceability:

- Benchmark file: `docs/benchmark_complete_20260429_172647.json`
- OTS proof: `docs/benchmark_complete_20260429_172647.json.ots`
- SHA-256: `0713acbbf50e1a0054f545e5eb68078744f9c5a09d4bc370b5224bb81183a6fe`
- DOI: [10.5281/zenodo.19702379](https://doi.org/10.5281/zenodo.19702379)
- TAD Registry: `EX-2026-18792778`

> Benchmark results are dataset-specific. See the DOI and benchmark artifact for methodology and replication details.

Run it yourself:

```bash
python tests/benchmark_runner.py --suite regression --api-url https://sas-api.onrender.com
```

---

## Plans and pricing

SAS is open source under **GPL-3.0 + Durante Invariance License**. Self-hosting is fully supported.

Hosted API plans:

| Plan | Usage | Price |
|---|---|---:|
| **SAS Free** | 50 requests/day · automatic API key | **Free** |
| **SAS Developer / Pro** | 10,000 requests/month · basic email support | **USD 99/month** |
| **SAS Team** | 50,000 requests/month · priority support | **USD 299/month** |
| **SAS Enterprise Cloud** | High volume · private integration · SLA | **From USD 1,500/month** |
| **SAS On-Premise License** | Private deployment · commercial license | **From USD 15,000/year** |
| **Technical Pilot** | Guided integration · technical report | **USD 1,500–3,000 one-time** |

Payment automation:

- Free key: `POST /public/request-key` → email delivery.
- Polar: international cards → webhook → Pro key by email.
- Mercado Pago: LATAM → webhook → Pro key by email.

Commercial contact:

```text
duranteg2@gmail.com
```

---

## Architecture

```text
SAS/
├── app/
│   ├── main.py                      # FastAPI app, middleware, startup, readiness
│   ├── routers/                     # audit, diff, batch, interaction, public, billing, auth
│   ├── services/                    # detector, stores, auth, metrics, audit, interaction observability
│   ├── db/                          # SQLite: auth, usage, payments
│   └── middleware/                  # security headers, auth, rate limiting, validation logging
├── core/                            # scientific core: semantic_diff, TDA, NIG
├── docs/                            # architecture, benchmark, OTS proof, manifold model
├── scripts/                         # funnel_report.py and operational tooling
├── tests/                           # tests and benchmark runner
├── .github/workflows/               # smoke tests and CI
├── Dockerfile
├── docker-compose.yml
├── PRIVACY.md
└── requirements.txt
```

Operational SQLite stores:

| Store | Purpose |
|---|---|
| `auth.db` | Users, API keys, quota tracking |
| `metrics.db` | Request metrics and funnel reporting |
| `audit.db` | Persistent sovereign API audit trail |
| `rate_limit.db` | Persistent rate-limit events |
| `interaction.db` | Interaction-stability observability metadata |

---

## Self-hosting

### Docker

```bash
git clone https://github.com/Leesintheblindmonk1999/SAS.git
cd SAS
docker compose up --build
```

### Local Python

```bash
git clone https://github.com/Leesintheblindmonk1999/SAS.git
cd SAS
python -m venv .venv
source .venv/bin/activate       # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Minimal `.env`:

```env
ADMIN_SECRET=change-this-admin-secret
FREE_REQUESTS_PER_DAY=50
MODULES_ENABLED=E9,E10,E11,E12
CORS_ALLOW_ORIGINS=*
AUTH_DB_PATH=/app/data/auth.db
METRICS_DB_PATH=/app/data/metrics.db
AUDIT_DB_PATH=/app/data/audit.db
RATE_LIMIT_DB_PATH=/app/data/rate_limit.db
INTERACTION_DB_PATH=/app/data/interaction.db
AUDIT_SALT_SECRET=change-this-long-random-secret
RATE_LIMIT_HASH_PEPPER=change-this-long-random-secret
INTERACTION_HASH_PEPPER=change-this-long-random-secret
ENABLE_INTERACTION_STABILITY=false
```

To enable the experimental interaction-stability endpoint:

```env
ENABLE_INTERACTION_STABILITY=true
```

---

## Documentation

| Document | Description |
|---|---|
| [Privacy and Observability](PRIVACY.md) | Data handling, hashes, fingerprints, public stats |
| [Manifold Model](docs/manifold.md) | ISI, κD, TDA, NIG, SourceTargetGuard, E9-E12 |
| [API Reference](docs/api.md) | Endpoints, CLI, auth, errors, and examples |
| [Billing](docs/billing.md) | Free/Pro flow, Polar, Mercado Pago, quotas |
| [Benchmark](docs/benchmark.md) | Methodology, limitations, replication guidance |
| [Security Notes](docs/security.md) | API keys, privacy, validation, rate limits, billing security |
| [Architecture](docs/architecture.md) | Detection pipeline, modules, and data flow |
| [Security Policy](SECURITY.md) | Vulnerability reporting and responsible disclosure |
| [Contributing Guide](CONTRIBUTING.md) | Development setup and pull requests |
| [Code of Conduct](CODE_OF_CONDUCT.md) | Community standards |
| [License](LICENSE.md) | GPL-3.0 + Durante Invariance License |

---

## Scope and limitations

- SAS measures structural coherence, not factual truth.
- A structurally coherent response can still be factually wrong.
- SourceTargetGuard detects source-response slot mutations; it does not replace an external knowledge base.
- Interaction-stability outputs are model constructs, not psychological diagnoses or legal determinations.
- `omega_t` measures belief-state concentration, not state desirability.
- Benchmark results are dataset-specific.
- Results are technical evidence, not automatic legal certification.
- Very short texts provide limited structural signal.
- Experimental endpoints may change as the research framework evolves.

---

## Roadmap

### Stabilization and observability

- Interaction observability store and public aggregate stats.
- `funnel_report.py` improvements for interaction usage.
- Continued privacy documentation and operational hardening.
- Monitoring rate-limit events and 4xx/5xx patterns.

### Product expansion

- Minimal usage dashboard.
- Node.js / TypeScript SDK.
- CLI support for batch files and interaction-stability calls.
- Signed PDF audit report with timestamp, hash, and provenance.

### Scientific

- Benchmark v2.0 with narrative and multilingual corpora.
- Empirical calibration of interaction-stability parameters.
- External replication by independent researchers.
- Formal investigation of the conjectural bridge between `omega_t` and ISI.

---

## Ecosystem

| Repository | Role |
|---|---|
| [`SAS`](https://github.com/Leesintheblindmonk1999/SAS) | Main API, core engine, benchmark, docs, self-hosting |
| [`sas-landing`](https://github.com/Leesintheblindmonk1999/sas-landing) | Public legitimacy layer: benchmark, API status, demo, activity feed |
| [`sas-client`](https://github.com/Leesintheblindmonk1999/sas-client) | Official Python client and CLI |

---

## Citation

```text
Durante, G. E. (2026). SAS - Symbiotic Autoprotection System.
Zenodo. https://doi.org/10.5281/zenodo.19702379
```

```bibtex
@software{durante_2026_sas,
  author    = {Durante, Gonzalo Emir},
  title     = {SAS - Symbiotic Autoprotection System},
  year      = {2026},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.19702379},
  url       = {https://doi.org/10.5281/zenodo.19702379}
}
```

---

## Author

**Gonzalo Emir Durante**

- GitHub: [Leesintheblindmonk1999](https://github.com/Leesintheblindmonk1999)
- API: [https://sas-api.onrender.com](https://sas-api.onrender.com)
- Landing: [https://leesintheblindmonk1999.github.io/sas-landing/](https://leesintheblindmonk1999.github.io/sas-landing/)
- DOI: [10.5281/zenodo.19702379](https://doi.org/10.5281/zenodo.19702379)
- Contact: duranteg2@gmail.com
