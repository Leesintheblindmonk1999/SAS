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

**SAS** is an open-source structural coherence auditing API for generative AI outputs.

It compares a source text against a generated response and measures whether the response preserves **structural coherence** using topological data analysis, numerical invariance, and specialized detection modules.

The core signal is the **Invariant Similarity Index (ISI)** compared against **κD = 0.56** — the Durante Constant.

```text
ISI >= 0.56  →  structurally coherent
ISI <  0.56  →  MANIFOLD_RUPTURE — potential hallucination signal
```

> SAS is not a universal factual oracle. It is a structural evidence layer for auditing LLM outputs.

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

Expected result:

```json
{
  "isi": 0.041,
  "kappa_d": 0.56,
  "verdict": "MANIFOLD_RUPTURE",
  "fired_modules": ["NIG: numerical violation", "SourceTargetGuard: location+year mutation"],
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

Interactive landing demo: [sas-landing/#demo](https://leesintheblindmonk1999.github.io/sas-landing/#demo)

---

## Get a Free API key — automatic, no manual step

```bash
sas request-key --email you@example.com --name "Your Name"
```

Your key arrives by email in seconds. 50 requests/day, no credit card.

Then:

```bash
export SAS_API_KEY="sas_xxxxxxxxxxxxxxxxxxxxx"
sas whoami
sas diff "The contract is governed by Argentine law." \
         "The contract is NOT governed by Argentine law."
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

**Traceability:**
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

## What SAS detects

SAS uses a layered pipeline:

| Component | Function |
|---|---|
| **TDA** | Topological Data Analysis — persistent homology H₀ + H₁, Wasserstein distance |
| **NIG** | Numerical Invariance Guard — detects year, quantity, and measurement mutations |
| **SourceTargetGuard** | Detects critical source-response slot mutations: locations, entities, dates |
| **E9** | Logical contradiction detection |
| **E10** | Fact grounding — unsupported claims vs. source |
| **E11** | Temporal inconsistency detection |
| **E12** | Abrupt topic shift detection |

Detection pipeline:

```text
Source text A  +  Response text B
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

No GPU. No external API calls. Runs locally or hosted.

---

## Live operational snapshot

SAS exposes public aggregate metrics for transparency:

```bash
curl https://sas-api.onrender.com/public/stats
curl "https://sas-api.onrender.com/public/activity?limit=10"
```

Public endpoints expose only aggregate and anonymized activity. No raw IPs, API keys, emails, or request bodies are ever published.

---

## API endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/health` | None | Health check |
| `GET` | `/readyz` | None | Granular router readiness |
| `GET` | `/integrity` | None | Legal provenance certificate |
| `POST` | `/public/demo/audit` | **None** | **Public demo — full forensic pipeline** |
| `GET` | `/public/stats` | None | Aggregate usage metrics |
| `GET` | `/public/activity` | None | Last N anonymized requests |
| `POST` | `/public/request-key` | None | Free API key by email |
| `POST` | `/v1/diff` | API Key | Forensic diff — primary endpoint |
| `POST` | `/v1/audit` | API Key | Single-text structural audit |
| `POST` | `/v1/chat` | API Key | Honest chat with κD filter |
| `GET` | `/v1/whoami` | API Key | Plan, quota, and key status |
| `GET` | `/robots.txt` | None | Crawler guidance |

Full documentation: [docs/api.md](docs/api.md) · [sas-api.onrender.com/docs](https://sas-api.onrender.com/docs)

---

## Plans and pricing

SAS is open source under **GPL-3.0 + Durante Invariance License**. Self-hosting is fully supported.

The following plans refer to the **hosted API service**:

| Plan | Usage | Price |
|---|---|---:|
| **SAS Free** | 50 requests/day · automatic API key | **Free** |
| **SAS Developer / Pro** | 10,000 requests/month · basic email support | **USD 99/month** |
| **SAS Team** | 50,000 requests/month · priority support | **USD 299/month** |
| **SAS Enterprise Cloud** | High volume · private integration · SLA | **From USD 1,500/month** |
| **SAS On-Premise License** | Private deployment · commercial license | **From USD 15,000/year** |
| **Technical Pilot** | Guided integration · technical report | **USD 1,500–3,000 one-time** |

Payment automation:
- **Free key** — `POST /public/request-key` → email delivery → no manual step.
- **Polar** — international cards → webhook → Pro key by email automatically.
- **Mercado Pago** — LATAM → webhook → Pro key by email automatically.

Commercial contact: duranteg2@gmail.com

---

## Architecture

```text
SAS/
├── app/
│   ├── main.py                   # FastAPI app, middleware, startup, system endpoints
│   ├── routers/                  # audit, diff, chat, public demo, keys, billing, whoami
│   ├── services/                 # detector, TDA/NIG wrappers, SourceTargetGuard, E9-E12
│   ├── db/                       # SQLite: auth, usage, payments, metrics
│   └── middleware/               # security headers, auth, rate limiting
├── core/                         # scientific core: semantic_diff, TDA, NIG
├── docs/                         # architecture, benchmark, OTS proof, manifold model
├── scripts/                      # funnel_report.py and operational tooling
├── tests/                        # test suite and benchmark runner
├── .github/workflows/            # smoke tests and CI
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

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
```

Full configuration reference: [docs/api.md](docs/api.md)

---

## Documentation

| Document | Description |
|---|---|
| [Manifold Model](docs/manifold.md) | ISI, κD, TDA, NIG, SourceTargetGuard, E9-E12 and interpretation |
| [API Reference](docs/api.md) | All endpoints, CLI, auth, errors, and examples |
| [Billing](docs/billing.md) | Free/Pro flow, Polar, Mercado Pago, quotas |
| [Benchmark](docs/benchmark.md) | Methodology, limitations, replication guidance |
| [Security Notes](docs/security.md) | API keys, privacy, validation, rate limits, billing security |
| [Architecture](docs/architecture.md) | Detection pipeline, modules, and data flow |
| [Security Policy](SECURITY.md) | Vulnerability reporting and responsible disclosure |
| [Contributing Guide](CONTRIBUTING.md) | Development setup, pull requests, and contribution rules |
| [Code of Conduct](CODE_OF_CONDUCT.md) | Community standards |
| [License](LICENSE.md) | GPL-3.0 + Durante Invariance License |

---

## Scope and limitations

- SAS measures **structural coherence**, not factual truth. A structurally coherent response can still be factually wrong.
- SourceTargetGuard detects source-response slot mutations — it does not replace an external knowledge base.
- Topic-shift detection is conservative to reduce false positives.
- Benchmark results are dataset-specific. Narrative and open-ended domains show lower recall.
- Results are technical evidence, not automatic legal certification.
- Very short texts provide limited structural signal.

---

## Roadmap

**Before broad launch:**
- `/readyz` database health checks for auth and metrics SQLite
- End-to-end flow test: demo → key → whoami → diff
- `funnel_report.py` for separating infrastructure from product traffic

**Near-term:**
- SQLite-backed persistent rate limiting
- `/v1/batch` for multiple source-response pairs
- `sas batch --file pairs.json` in CLI

**Product expansion:**
- Node.js / TypeScript SDK
- LangChain integration
- Minimal usage dashboard
- Signed PDF audit report with timestamp, hash, and provenance

**Scientific:**
- Benchmark v2.0 with narrative and multilingual corpora
- Independent replication by external researchers

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
