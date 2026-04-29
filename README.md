# SAS - Symbiotic Autoprotection System

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19689077.svg)](https://doi.org/10.5281/zenodo.19689077)
[![License](https://img.shields.io/badge/license-GPL--3.0%20%2B%20Durante%20Invariance-blue)](LICENSE.md)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](requirements.txt)
[![API](https://img.shields.io/badge/API-FastAPI-009688)](#api-examples)
[![Status](https://img.shields.io/badge/status-research%20alpha-orange)](#scope-and-limitations)
[![Benchmark](https://img.shields.io/badge/benchmark-98.8%25%20accuracy-brightgreen)](docs/benchmark_results.json)
[![Security](https://img.shields.io/badge/security-policy-lightgrey)](SECURITY.md)
[![Contributing](https://img.shields.io/badge/contributions-welcome-brightgreen)](CONTRIBUTING.md)

**SAS - Symbiotic Autoprotection System** is an open-source API framework for detecting structural hallucinations in generative AI outputs.

SAS evaluates whether a generated response preserves semantic structure, logical consistency, numerical integrity, temporal consistency, and factual-coherence signals relative to a source text or prompt. It combines topological data analysis, numerical invariance checks, and modular hallucination probes into a FastAPI-based audit system.

The project is authored by **Gonzalo Emir Durante** and published as an open technical standard candidate for structural coherence auditing in AI systems.

---

## Documentation

| Document | Purpose |
|---|---|
| [Security Policy](SECURITY.md) | Vulnerability reporting, deployment security, and responsible disclosure |
| [Contributing Guide](CONTRIBUTING.md) | Development setup, pull requests, tests, and contribution rules |
| [Code of Conduct](CODE_OF_CONDUCT.md) | Community standards and enforcement process |
| [Architecture Overview](docs/architecture.md) | System design, core components, data flow, and deployment model |
| [Benchmark Results](docs/benchmark_results.json) | Full benchmark output used for the current metrics |
| [Benchmark OTS Proof](docs/benchmark_results.json.ots) | OpenTimestamps proof for benchmark traceability, if included in the repository |
| [Bug Report Template](.github/ISSUE_TEMPLATE/bug_report.md) | GitHub issue template for bug reports |
| [Feature Request Template](.github/ISSUE_TEMPLATE/feature_request.md) | GitHub issue template for feature proposals |
| [License](LICENSE.md) | GPL-3.0 + Durante Invariance License |

---

## Problem

Generative AI systems can produce fluent outputs that are structurally inconsistent, logically inverted, numerically wrong, temporally incoherent, or semantically disconnected from the input.

Traditional similarity metrics often fail to detect these cases because hallucinations may preserve surface fluency while breaking deeper coherence.

SAS addresses this by treating hallucination detection as a **structural coherence audit** problem.

It is designed to detect:

- semantic manifold rupture;
- logical contradiction;
- numerical inconsistency;
- temporal inconsistency;
- reference or grounding anomalies;
- abrupt topic shifts;
- structural divergence between source and response.

SAS is not a universal factual oracle. It provides technical evidence for structural hallucination detection and coherence auditing.

---

## Core concept: kappa_D = 0.56

SAS uses the constant:

```text
kappa_D = 0.56
```

`kappa_D`, also referred to as the **Durante Constant**, is used as a critical coherence threshold in the SAS pipeline.

Within the framework, `kappa_D = 0.56` represents the operational point at which semantic structure is treated as preserved or ruptured.

Operational interpretation:

```text
ISI >= kappa_D  -> structurally coherent
ISI <  kappa_D  -> potential manifold rupture / hallucination signal
```

The constant is used in combination with the **Invariant Similarity Index (ISI)** and additional detection modules.

---

## Architecture

```text
SAS/
├── .gitignore
├── LICENSE.md
├── README.md
├── SECURITY.md
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
├── .github/
│   └── ISSUE_TEMPLATE/
│       ├── bug_report.md
│       └── feature_request.md
├── docs/
│   ├── architecture.md
│   └── benchmark_results.json
├── src/
│   ├── sas/
│   │   └── detector.py
│   └── api/
│       └── main.py
├── tests/
├── docker-compose.yml
└── requirements.txt
```

### Core components

| Component | Purpose |
|---|---|
| TDA | Topological Data Analysis for semantic structure comparison |
| ISI | Invariant Similarity Index |
| NIG | Numerical Invariance Guard |
| E9 | Logical contradiction detection |
| E10 | Fact grounding / narrative inventiveness check |
| E11 | Temporal inconsistency detection |
| E12 | Abrupt topic shift detection |
| FastAPI | API layer for audit, diff, chat, health, and admin functions |

---

## Current benchmark results

The current benchmark evaluates **2,000 total pairs**:

- 1,000 hallucination pairs
- 1,000 clean pairs

Benchmark timestamp:

```text
2026-04-29T17:26:47.459936
```

Benchmark SHA-256 hash:

```text
0713acbbf50e1a0054f545e5eb68078744f9c5a09d4bc370b5224bb81183a6fe
```

### Confusion matrix

|                      | Actual hallucination | Actual clean |
|---|---:|---:|
| Predicted hallucination | 976 | 0 |
| Predicted clean | 24 | 1000 |

### Metrics

| Metric | Result |
|---|---:|
| Total evaluated pairs | 2,000 |
| Hallucination pairs | 1,000 |
| Clean pairs | 1,000 |
| True positives | 976 |
| False negatives | 24 |
| True negatives | 1,000 |
| False positives | 0 |
| Accuracy | 98.80% |
| Precision | 100.00% |
| Recall | 97.60% |
| F1 score | 98.79% |
| False positive rate | 0.00% |
| Clean specificity | 100.00% |
| Average ISI, hallucination pairs | 0.072993 |
| Average ISI, clean pairs | 1.000000 |

### Benchmark interpretation

The benchmark shows that SAS detected 976 out of 1,000 hallucination cases while producing 0 false positives on 1,000 clean examples.

This supports the current positioning of SAS as a high-precision structural hallucination audit layer. The benchmark should be interpreted within its evaluated dataset and configuration.

To reproduce the benchmark:

```bash
python tests/benchmark_runner.py
```

---

## Quick start

### Option 1: Docker

```bash
git clone https://github.com/Leesintheblindmonk1999/SAS.git
cd SAS

docker compose up --build
```

The API should be available at:

```text
http://localhost:8000
```

Health check:

```bash
curl http://localhost:8000/health
```

---

### Option 2: Local Python install

```bash
git clone https://github.com/Leesintheblindmonk1999/SAS.git
cd SAS

python -m venv .venv
```

Activate the environment:

```bash
# Linux/macOS
source .venv/bin/activate
```

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the API:

```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Configuration

Create a local `.env` file:

```env
ADMIN_SECRET=change-this-admin-secret
FREE_REQUESTS_PER_DAY=5
MODULES_ENABLED=E9,E10,E11,E12
CORS_ALLOW_ORIGINS=*
```

Do not commit `.env` files to public repositories.

For production, restrict CORS:

```env
CORS_ALLOW_ORIGINS=https://yourdomain.com
```

---

## API authentication

Most API endpoints require an API key.

Generate an API key using the admin endpoint:

```bash
curl -X POST http://localhost:8000/admin/generate-key \
  -H "X-Admin-Secret: change-this-admin-secret"
```

Example response:

```json
{
  "api_key": "sas_xxxxxxxxxxxxxxxxxxxxx",
  "created_at": "2026-04-29T00:00:00Z"
}
```

Use the returned key in API requests:

```bash
-H "X-API-Key: sas_xxxxxxxxxxxxxxxxxxxxx"
```

---

## API examples

### Health check

```bash
curl http://localhost:8000/health
```

Example response:

```json
{
  "status": "ok",
  "service": "SAS",
  "version": "1.0"
}
```

---

### Audit a generated response

```bash
curl -X POST http://localhost:8000/v1/audit \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sas_xxxxxxxxxxxxxxxxxxxxx" \
  -d '{
    "source": "The Eiffel Tower is located in Paris, France.",
    "response": "The Eiffel Tower is located in Berlin, Germany.",
    "experimental": true
  }'
```

Example response:

```json
{
  "isi": 0.0,
  "kappa_d": 0.56,
  "detected_hallucination": true,
  "verdict": "MANIFOLD_RUPTURE",
  "fired_modules": [
    "E9 Logical Contradiction",
    "E10 Fact Grounding"
  ]
}
```

---

### Compare two texts

```bash
curl -X POST http://localhost:8000/v1/diff \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sas_xxxxxxxxxxxxxxxxxxxxx" \
  -d '{
    "text_a": "Python is commonly used for automation and data analysis.",
    "text_b": "Python is mainly a type of tropical snake used in weather forecasting.",
    "experimental": true
  }'
```

Example response:

```json
{
  "isi": 0.0,
  "kappa_d": 0.56,
  "verdict": "MANIFOLD_RUPTURE",
  "detected_hallucination": true
}
```

---

### Chat endpoint

```bash
curl -X POST http://localhost:8000/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sas_xxxxxxxxxxxxxxxxxxxxx" \
  -d '{
    "message": "Explain what kappa_D means in SAS."
  }'
```

---

## Module controls

Experimental modules can be enabled through environment configuration:

```env
MODULES_ENABLED=E9,E10,E11,E12
```

Or selectively disabled:

```env
MODULES_ENABLED=E9,E11
```

### Module overview

| Module | Name | Function |
|---|---|---|
| E9 | Logical Contradiction | Detects internal logical inversion or contradiction |
| E10 | Fact Grounding | Detects unsupported or implausible factual claims when local grounding is available |
| E11 | Temporal Inconsistency | Detects incompatible temporal sequences |
| E12 | Topic Shift | Detects abrupt topic changes without transition signals |

Modules are used as independent penalty factors and do not replace the core ISI/TDA calculation.

---

## Zenodo and registration

- **Zenodo DOI:** [10.5281/zenodo.19689077](https://doi.org/10.5281/zenodo.19689077)
- **TAD Registry:** `EX-2026-18792778`
- **Author:** Gonzalo Emir Durante
- **License:** GPL-3.0 + Durante Invariance License
- **Benchmark SHA-256:** `0713acbbf50e1a0054f545e5eb68078744f9c5a09d4bc370b5224bb81183a6fe`

---

## Citation

If you use SAS, cite the project as:

```text
Durante, G. E. (2026). SAS - Symbiotic Autoprotection System:
A structural coherence audit framework for hallucination detection
in generative AI systems. Zenodo.
https://doi.org/10.5281/zenodo.19689077
```

### BibTeX

```bibtex
@software{durante_2026_sas,
  author       = {Durante, Gonzalo Emir},
  title        = {SAS - Symbiotic Autoprotection System},
  year         = {2026},
  publisher    = {Zenodo},
  doi          = {10.5281/zenodo.19689077},
  url          = {https://doi.org/10.5281/zenodo.19689077}
}
```

---

## License

This project is licensed under:

```text
GPL-3.0 + Durante Invariance License
```

The additional Durante Invariance clause requires attribution for use, implementation, or distribution of the `kappa_D = 0.56` constant for semantic invariance detection, hallucination detection, or similar purposes.

See [LICENSE.md](LICENSE.md) for the full license text.

---

## Development

Run tests:

```bash
pytest
```

Run benchmark:

```bash
python tests/benchmark_runner.py
```

Run API locally:

```bash
uvicorn src.api.main:app --reload
```

---

## Security notes

- Do not commit `.env` files.
- Rotate `ADMIN_SECRET` before deployment.
- Use HTTPS in production.
- Restrict CORS origins in production.
- Keep API keys private.
- The `/admin/generate-key` endpoint must be protected by a strong admin secret.
- Report vulnerabilities privately according to [SECURITY.md](SECURITY.md).

---

## Scope and limitations

SAS is designed for structural coherence auditing and hallucination signal detection. It does not guarantee universal factual verification.

Known limitations:

- Factual grounding depends on available local knowledge sources.
- Topic-shift detection is conservative to reduce false positives.
- Results should be interpreted as technical evidence, not as legal certification.
- Benchmark results should be interpreted within the evaluated dataset and configuration.

---

## Author

**Gonzalo Emir Durante**

Author of SAS, Omni-Scanner API, and `kappa_D = 0.56`.

Repository:

```text
https://github.com/Leesintheblindmonk1999/SAS
```

DOI:

```text
https://doi.org/10.5281/zenodo.19689077
```
