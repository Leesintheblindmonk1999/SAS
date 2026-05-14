# SAS — Symbiotic Autoprotection System

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19702379.svg)](https://doi.org/10.5281/zenodo.19702379)
[![Landing Page](https://img.shields.io/badge/Landing_Page-0a0e17?style=flat&logo=github)](https://leesintheblindmonk1999.github.io/sas-landing/)
[![API Online](https://img.shields.io/badge/API-online-brightgreen)](https://sas-api.onrender.com)
[![PyPI](https://img.shields.io/pypi/v/sas-client?label=sas-client&color=blue)](https://pypi.org/project/sas-client/)
[![API Docs](https://img.shields.io/badge/API-FastAPI-009688)](https://sas-api.onrender.com/docs)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](requirements.txt)
[![License](https://img.shields.io/badge/license-GPL--3.0%20%2B%20Durante%20Invariance-blue)](LICENSE.md)
[![Status](https://img.shields.io/badge/status-research%20alpha-orange)](#scope-and-limitations)
[![Benchmark](https://img.shields.io/badge/benchmark-documented-brightgreen)](docs/benchmark_complete_20260429_172647.json)
[![OTS Proof](https://img.shields.io/badge/OpenTimestamps-proof-blueviolet)](docs/benchmark_complete_20260429_172647.json.ots)
[![Security](https://img.shields.io/badge/security-policy-lightgrey)](SECURITY.md)
[![Contributing](https://img.shields.io/badge/contributions-welcome-brightgreen)](CONTRIBUTING.md)
[![Smoke Test](https://github.com/Leesintheblindmonk1999/SAS/actions/workflows/smoke_test.yml/badge.svg)](https://github.com/Leesintheblindmonk1999/SAS/actions/workflows/smoke_test.yml)

**SAS — Symbiotic Autoprotection System** is an open-source structural coherence auditing API for generative AI outputs.

SAS compares a source and a generated response to detect semantic drift, structural hallucination, numerical inconsistency, logical contradiction, and source-response factual slot mutations.

It is built around:

- **κD = 0.56** — the Durante Constant, used as the operational coherence threshold.
- **ISI** — Invariant Similarity Index.
- **TDA** — topological structural comparison.
- **NIG** — Numerical Invariance Guard.
- **SourceTargetGuard** — source-response invariance guard for years, numbers, locations, and anchored entities.
- **E9-E12 modules** — logical contradiction, fact grounding, temporal inconsistency, and topic shift.

> SAS is not a universal factual oracle. It provides technical evidence for structural coherence auditing.

---

## Live API

Hosted reference API:

```text
https://sas-api.onrender.com
```

Interactive FastAPI docs:

```text
https://sas-api.onrender.com/docs
```

Health check:

```bash
curl https://sas-api.onrender.com/health
```

Readiness check:

```bash
curl https://sas-api.onrender.com/readyz
```

---

## Fastest start: terminal onboarding

Install the official Python client and CLI:

```bash
pip install sas-client
```

Request a Free API key from the terminal:

```bash
sas request-key --email you@example.com --name "Your Name"
```

After receiving the key by email:

```bash
export SAS_API_KEY="sas_xxxxxxxxxxxxxxxxxxxxx"
sas whoami
```

Windows PowerShell:

```powershell
$env:SAS_API_KEY="sas_xxxxxxxxxxxxxxxxxxxxx"
sas whoami
```

Run a forensic diff:

```bash
sas diff \
  "The Eiffel Tower is located in Paris, France. It was built in 1889. It is one of the most recognized landmarks in France." \
  "The Eiffel Tower is located in Berlin, Germany. It was built in 1950. It is one of the most recognized landmarks in Germany."
```

Expected behavior for that mutation:

```json
{
  "isi": 0.25,
  "verdict": "MANIFOLD_RUPTURE",
  "manipulation_alert": {
    "triggered": true,
    "sources": ["SourceTargetGuard"]
  }
}
```

---

## Public demo — no API key required

```bash
sas demo-audit \
  "The Eiffel Tower is located in Paris, France, and was built in 1889." \
  "The Eiffel Tower is located in Berlin, Germany, and was built in 1950."
```

Or with curl:

```bash
curl -X POST https://sas-api.onrender.com/public/demo/audit \
  -H "Content-Type: application/json" \
  -d '{
    "source": "The Eiffel Tower is located in Paris, France.",
    "response": "The Eiffel Tower is located in Berlin, Germany."
  }'
```

Interactive landing demo:

```text
https://leesintheblindmonk1999.github.io/sas-landing/#demo
```

---

## Official Python client

Repository:

```text
https://github.com/Leesintheblindmonk1999/sas-client
```

PyPI:

```text
https://pypi.org/project/sas-client/
```

Install:

```bash
pip install sas-client
```

### Python usage

```python
from sas_client import SASClient

client = SASClient(api_key="YOUR_API_KEY")

result = client.diff(
    text_a="Python is a programming language.",
    text_b="A python is a snake.",
    experimental=True,
)

print(result["isi"])
print(result["verdict"])
print(result.get("evidence", {}).get("fired_modules"))
```

### CLI commands in `sas-client` v0.2.0+

| Command | API key required | Purpose |
|---|---:|---|
| `sas health` | No | Check `/health` |
| `sas readyz` | No | Check `/readyz` and router readiness |
| `sas public-stats` | No | Show aggregated public metrics |
| `sas public-activity --limit 10` | No | Show anonymized public activity |
| `sas plans` | No | Show hosted Free / Pro plan information |
| `sas request-key --email you@example.com --name "Name"` | No | Request a Free API key by email |
| `sas demo-audit "source" "response"` | No | Run the public no-key demo |
| `sas whoami` | Yes | Show current API key identity, plan, and quota |
| `sas audit "text"` | Yes | Audit one text |
| `sas diff "source" "response"` | Yes | Compare source against response |
| `sas chat "message"` | Yes | Use the chat endpoint |

Environment variables:

```bash
export SAS_API_KEY="YOUR_API_KEY"
# or
export SAS_KEY="YOUR_API_KEY"
```

Windows PowerShell:

```powershell
$env:SAS_API_KEY="YOUR_API_KEY"
# or
$env:SAS_KEY="YOUR_API_KEY"
```

Self-hosted instance:

```bash
sas --base-url http://localhost:8000 health
```

---

## API authentication and key acquisition

### Free API key

Request from CLI:

```bash
sas request-key --email you@example.com --name "Your Name"
```

Or with curl:

```bash
curl -X POST https://sas-api.onrender.com/public/request-key \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com", "name": "Your Name"}'
```

Your Free API key is generated and delivered automatically by email.

Current hosted Free plan:

```text
50 requests/day
```

### Check current plan and quota

```bash
sas whoami
```

Or with curl:

```bash
curl https://sas-api.onrender.com/v1/whoami \
  -H "X-API-Key: sas_xxxxxxxxxxxxxxxxxxxxx"
```

Example:

```json
{
  "status": "ok",
  "plan": "free",
  "active": true,
  "daily_limit": 50,
  "daily_used": 3,
  "quota_allowed": true
}
```

### Pro plan

Hosted Pro currently provides:

```text
10,000 requests/month
```

Available through hosted checkout flows:

- Polar — international cards.
- Mercado Pago — LATAM.

---

## Core API examples

### `/v1/diff` — primary forensic endpoint

```bash
curl -X POST https://sas-api.onrender.com/v1/diff \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sas_xxxxxxxxxxxxxxxxxxxxx" \
  -d '{
    "text_a": "Python is commonly used for automation and data analysis.",
    "text_b": "Python is mainly a type of tropical snake used in weather forecasting.",
    "experimental": true
  }'
```

### `/v1/audit`

```bash
curl -X POST https://sas-api.onrender.com/v1/audit \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sas_xxxxxxxxxxxxxxxxxxxxx" \
  -d '{
    "text": "The Eiffel Tower is located in Berlin, Germany.",
    "experimental": true
  }'
```

### `/v1/chat`

```bash
curl -X POST https://sas-api.onrender.com/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sas_xxxxxxxxxxxxxxxxxxxxx" \
  -d '{"message": "Explain what κD means in SAS."}'
```

### Public endpoints

```bash
curl https://sas-api.onrender.com/public/stats
curl "https://sas-api.onrender.com/public/activity?limit=10"
curl https://sas-api.onrender.com/readyz
curl https://sas-api.onrender.com/robots.txt
```

---

## Architecture

```text
SAS/
├── app/
│   ├── main.py                   # FastAPI app, middleware, readiness, system endpoints
│   ├── routers/                  # audit, diff, chat, public demo, keys, billing
│   ├── services/                 # detector, TDA/NIG wrappers, SourceTargetGuard, E9-E12
│   ├── db/                       # SQLite auth, usage, payments, metrics
│   └── middleware/               # security headers, auth/rate-limit middleware
├── core/                         # semantic diff / low-level core components
├── docs/                         # architecture, benchmark, OTS proof
├── tests/                        # test suite and benchmark runner
├── .github/workflows/            # smoke tests and automation
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

### Main components

| Component | Function |
|---|---|
| TDA | Topological Data Analysis for structural semantic comparison |
| ISI | Invariant Similarity Index |
| κD | Critical coherence threshold, currently `0.56` |
| NIG | Numerical Invariance Guard |
| SourceTargetGuard | Detects critical source-response mutations in years, numbers, locations, and anchored entities |
| E9 | Logical contradiction detection |
| E10 | Fact grounding when local grounding sources are available |
| E11 | Temporal inconsistency detection |
| E12 | Abrupt topic shift detection |
| FastAPI | Hosted API layer |
| SQLite | Auth, usage, key issuance, billing events, and public metrics |

---

## SourceTargetGuard

SourceTargetGuard was added to prevent cases where two texts preserve the same superficial structure but mutate critical factual slots.

Example:

```text
Source:   The Eiffel Tower is located in Paris, France. It was built in 1889.
Response: The Eiffel Tower is located in Berlin, Germany. It was built in 1950.
```

Expected SAS signal:

```text
ISI: 0.25
Verdict: MANIFOLD_RUPTURE
Alert source: SourceTargetGuard
Reason: year mismatch + anchored location/entity shift
```

This guard does **not** claim external truth. It checks whether the generated response preserved critical invariants from the provided source.

---

## Plans and pricing for hosted API

SAS is open source under **GPL-3.0 + Durante Invariance License**.

The following plans refer to the hosted API service, support, integration, or private licensing. They do not remove or relax the open-source license of the public code.

| Plan | Usage / Features | Price |
|---|---|---:|
| SAS Free | 50 requests/day. Automatic API key. Technical evaluation and individual development. | Free |
| SAS Developer / Pro | 10,000 requests/month. Hosted API access. Basic email support. | USD 99/month |
| SAS Enterprise Cloud | High volume or custom package. Direct support. Private integration. SLA by agreement. | From USD 1,500/month |
| SAS On-Premise License | Private deployment on customer infrastructure. Commercial license and implementation support. | From USD 15,000/year |
| Technical Pilot | Initial audit, guided integration, technical report, and use-case validation. | USD 1,500-3,000 one-time |

Commercial contact:

```text
duranteg2@gmail.com
```

---

## Benchmark

Main benchmark artifact:

```text
docs/benchmark_complete_20260429_172647.json
```

OpenTimestamps proof:

```text
docs/benchmark_complete_20260429_172647.json.ots
```

SHA-256:

```text
0713acbbf50e1a0054f545e5eb68078744f9c5a09d4bc370b5224bb81183a6fe
```

Documented benchmark summary:

| Metric | Result |
|---|---:|
| Evaluated pairs | 2,000 |
| Hallucination pairs | 1,000 |
| Clean pairs | 1,000 |
| Accuracy | 98.80% |
| Precision | 100.00% |
| Recall | 97.60% |
| F1 score | 98.79% |
| False positives | 0 |
| κD | 0.56 |

> Benchmark results are dataset-specific. See the benchmark artifact, methodology, and DOI for replication context.

Run benchmark:

```bash
python tests/benchmark_runner.py
```

---

## Documentation

| Document | Description |
|---|---|
| [Security Policy](SECURITY.md) | Vulnerability reporting and responsible disclosure |
| [Contributing Guide](CONTRIBUTING.md) | Development setup, pull requests, testing, contribution rules |
| [Code of Conduct](CODE_OF_CONDUCT.md) | Community standards |
| [Architecture Overview](docs/architecture.md) | Detection pipeline, modules, and data flow |
| [Benchmark JSON](docs/benchmark_complete_20260429_172647.json) | Full benchmark output |
| [Benchmark OTS Proof](docs/benchmark_complete_20260429_172647.json.ots) | OpenTimestamps proof |
| [License](LICENSE.md) | GPL-3.0 + Durante Invariance License |

Recommended next technical doc:

```text
docs/manifold.md
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
source .venv/bin/activate  # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Local health check:

```bash
curl http://localhost:8000/health
```

---

## Configuration

Create a local `.env`:

```env
ADMIN_SECRET=change-this-admin-secret
FREE_REQUESTS_PER_DAY=50
LEGACY_REQUESTS_PER_DAY=5
MODULES_ENABLED=E9,E10,E11,E12
CORS_ALLOW_ORIGINS=*
AUTH_DB_PATH=/app/data/auth.db
METRICS_DB_PATH=/app/data/metrics.db
```

Do not commit `.env` files.

---

## Security notes

- Do not commit `.env` files.
- Rotate `ADMIN_SECRET` before deployment.
- Use HTTPS in production.
- Restrict CORS origins in production.
- Keep API keys private.
- Keep billing webhook secrets private.
- `robots.txt` is crawler guidance, not a security boundary.
- Admin and debug endpoints must remain protected.

For vulnerability reports, see [SECURITY.md](SECURITY.md).

---

## Scope and limitations

SAS is designed for structural coherence auditing and hallucination signal detection. It does not guarantee universal factual verification.

Known limitations:

- Factual grounding depends on available local knowledge sources.
- SourceTargetGuard checks preservation of source-response invariants; it does not replace an external fact database.
- Topic-shift detection is conservative to reduce false positives.
- Results should be interpreted as technical evidence, not automatic legal certification.
- Benchmark performance may vary across domains, languages, and datasets not represented in the current evaluation.
- Very short texts may provide limited structural signal.

---

## Roadmap

### Before broad public launch

- GitHub Release `v1.1.0` with changelog.
- End-to-end user flow test: demo -> request key -> email -> whoami -> diff.
- `/readyz` database checks for auth and metrics SQLite.
- Funnel report script separating infrastructure traffic from product traffic.
- Tests for `robots.txt`, `HEAD /`, validation errors, auth failures, SourceTargetGuard, and legacy quota.

### Near-term

- SQLite-backed persistent rate limiting.
- Payload size limits by plan.
- Better webhook idempotency and failure handling.
- `docs/manifold.md`.
- Mini benchmark suite for v1.1.x/v1.2.x.

### Product expansion

- `/v1/batch` endpoint for multiple source-response pairs.
- `sas batch --file pairs.json` in the CLI.
- Node.js / TypeScript SDK.
- LangChain integration.
- Minimal usage dashboard.
- Signed PDF audit report with timestamp, hash, and provenance.

### Scientific credibility

- Benchmark v2.0 with broader narrative and multilingual corpora.
- Independent replication by external researchers.
- Updated Zenodo release for major API/client milestones.

---

## Zenodo and registry

- **Zenodo DOI:** [10.5281/zenodo.19702379](https://doi.org/10.5281/zenodo.19702379)
- **TAD Registry:** `EX-2026-18792778`
- **Author:** Gonzalo Emir Durante
- **Hosted API:** [https://sas-api.onrender.com](https://sas-api.onrender.com)
- **Landing:** [https://leesintheblindmonk1999.github.io/sas-landing/](https://leesintheblindmonk1999.github.io/sas-landing/)
- **PyPI Client:** [https://pypi.org/project/sas-client/](https://pypi.org/project/sas-client/)

---

## Citation

```text
Durante, G. E. (2026). SAS - Symbiotic Autoprotection System:
A structural coherence audit framework for hallucination detection
in generative AI systems. Zenodo.
https://doi.org/10.5281/zenodo.19702379
```

```bibtex
@software{durante_2026_sas,
  author       = {Durante, Gonzalo Emir},
  title        = {SAS - Symbiotic Autoprotection System},
  year         = {2026},
  publisher    = {Zenodo},
  doi          = {10.5281/zenodo.19702379},
  url          = {https://doi.org/10.5281/zenodo.19702379}
}
```

---

## License

```text
GPL-3.0 + Durante Invariance License
```

See [LICENSE.md](LICENSE.md).

---

## Author

**Gonzalo Emir Durante**

- GitHub: [Leesintheblindmonk1999](https://github.com/Leesintheblindmonk1999)
- Repository: [SAS](https://github.com/Leesintheblindmonk1999/SAS)
- API: [https://sas-api.onrender.com](https://sas-api.onrender.com)
- Landing: [https://leesintheblindmonk1999.github.io/sas-landing/](https://leesintheblindmonk1999.github.io/sas-landing/)
- PyPI: [sas-client](https://pypi.org/project/sas-client/)
- DOI: [10.5281/zenodo.19702379](https://doi.org/10.5281/zenodo.19702379)
- Commercial contact: duranteg2@gmail.com
