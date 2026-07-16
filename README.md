# SAS — Symbiotic Autoprotection System

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19702379.svg)](https://doi.org/10.5281/zenodo.19702379)
[![R0 Audit](https://img.shields.io/badge/R0%20Audit-Zenodo%2020647532-blueviolet)](https://zenodo.org/records/20647532)
[![R1-D](https://img.shields.io/badge/R1--D-Zenodo%2021282332-blueviolet)](https://zenodo.org/records/21282332)
[![R2.1](https://img.shields.io/badge/R2.1-Zenodo%2021365707-blueviolet)](https://doi.org/10.5281/zenodo.21365707)
[![Landing Page](https://img.shields.io/badge/🌐-Landing_Page-0a0e17?style=flat&logo=github)](https://leesintheblindmonk1999.github.io/sas-landing/)
[![API Online](https://img.shields.io/badge/API-online-brightgreen)](https://sas-api.onrender.com)
[![PyPI](https://img.shields.io/pypi/v/sas-client?label=sas-client&color=blue)](https://pypi.org/project/sas-client/)
[![npm](https://img.shields.io/npm/v/sas-audit-client?label=sas-audit-client&color=red)](https://www.npmjs.com/package/sas-audit-client)
[![API Docs](https://img.shields.io/badge/API-FastAPI-009688)](https://sas-api.onrender.com/docs)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](requirements.txt)
[![License](https://img.shields.io/badge/license-GPL--3.0%20%2B%20Durante%20Invariance-blue)](LICENSE.md)
[![Status](https://img.shields.io/badge/status-research%20alpha-orange)](#scope-and-limitations)
[![Benchmark](https://img.shields.io/badge/benchmark-98.8%25%20accuracy-brightgreen)](docs/benchmark_complete_20260429_172647.json)
[![R0 Baseline](https://img.shields.io/badge/R0%20baseline-12k%20stratified-success)](#r0-infrastructure-and-baseline-stability-audit)
[![OTS Proof](https://img.shields.io/badge/OpenTimestamps-proof-blueviolet)](docs/benchmark_complete_20260429_172647.json.ots)
[![Smoke Test](https://github.com/Leesintheblindmonk1999/SAS/actions/workflows/smoke_test.yml/badge.svg)](https://github.com/Leesintheblindmonk1999/SAS/actions/workflows/smoke_test.yml)

**SAS — Symbiotic Autoprotection System** is an open-source defensive AI auditing system.

It provides an API and research framework for auditing:

- structural coherence in generated text;
- source/response semantic rupture;
- hallucination-risk signals;
- batch comparison workflows;
- experimental temporal interaction stability;
- JavaScript / TypeScript integration through the published Node SDK `sas-audit-client`;
- operational traceability without storing raw submitted content;
- reproducible R0/R1 research workflows for module-correlation, baseline stability, and future multimetric tribunal evaluation.

The core structural signal is the **Invariant Similarity Index (ISI)** compared against **κD = 0.56** — the Durante Constant.

```text
ISI >= 0.56  →  structurally coherent
ISI <  0.56  →  MANIFOLD_RUPTURE — potential structural hallucination signal
```

> SAS is not a universal factual oracle. It is a defensive audit layer for generating reproducible evidence about structural coherence, semantic divergence, and interaction stability.

---

## Latest research release — R0 Baseline Stability Audit

A new R0 technical report and curated artifact package were released on Zenodo:

```text
R0 Infrastructure and Baseline Stability Audit for SAS/κD-0.56:
A Stratified Clean-Self Control Study over 152,525 Hallucination Pairs
```

Zenodo record:

```text
https://zenodo.org/records/20647532
```

Public curated artifact:

```text
public_r0_baseline_audit_20260611_clean.zip
```

Artifact SHA-256:

```text
b1c4b2eddc7b887f8721f3f193b5d1263e4822f13efd08f8b20ae95389dd36fe
```

This release validates the **R0 infrastructure and baseline stability** of the SAS research pipeline under a `clean_strategy=self` control condition.

It demonstrates:

- large-scale local corpus conversion;
- stratified sampling by corpus/category;
- frozen train/test splits;
- isolated module execution;
- module-correlation analysis;
- minimal baseline tribunal selection;
- held-out test validation;
- confusion matrix export;
- category-level error analysis;
- public artifact curation without raw benchmark text redistribution.

It does **not** claim final production-grade SAS validation or R1 tribunal validation. The reported runs use clean-self controls, where clean records are generated as:

```text
source = A_clean
response = A_clean
```

This can inflate performance for dissimilarity-based modules. The release should be interpreted as R0 infrastructure, reproducibility, stratified sampling, module-correlation, and baseline-stability evidence.

---

## Related Research Releases — R1-D and R2.1

Two further research milestones have been published since the R0 audit above, in the companion research repository [`Project_Manifold_056`](https://github.com/Leesintheblindmonk1999/Project_Manifold_056). They are documented here as **research findings that inform the SAS roadmap**, not as claims about what is currently deployed in the live production API — see the note below each summary.

### R1-D — Structural Evaluation over Declarative Corpus (halueval_qa)

```text
Flow + CRE + Negation composite: test F1 = 0.8571, precision = 0.9513,
recall = 0.7798, accuracy = 0.8699 — a +22.4% improvement over the
R0.5D lexical baseline (AUC 0.749).
```

Zenodo record: https://doi.org/10.5281/zenodo.21282332

### R2.1 — Structural Code Hallucination Detection via AST Fingerprinting

First extension of the κD structural-evaluation line into the code domain. AST structural comparison against a reference implementation (binary vetoes removed) reached AUC 0.9141 (raw) / 0.9421 (length-confound-controlled) on a 1,596-row execution-verified corpus. An internal-coherence TDA adaptation was tested and produced a documented negative result (AUC 0.40–0.45), confirmed by two independent implementations.

Zenodo record: https://doi.org/10.5281/zenodo.21365707

> **Production status note:** the `Flow + CRE + Negation` composite (R1-D) and the vetoless AST structural comparison (R2.1, `code_diff_isi`) are research results validated against offline corpora. Whether and how they have been integrated into the live modules behind `/v1/diff`, `/v1/audit`, and `/v1/batch` should be confirmed against the current `core/` implementation and changelog before being cited as a description of live production behavior. The R0 → R1 transition plan below tracks this integration work explicitly.

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

## Official clients and SDKs

SAS currently has two public developer clients:

| Client | Package | Runtime | Status |
|---|---|---|---|
| Python CLI / client | [`sas-client`](https://pypi.org/project/sas-client/) | Python 3.10+ | Published on PyPI |
| Node.js / TypeScript SDK | [`sas-audit-client`](https://www.npmjs.com/package/sas-audit-client) | Node.js 18+ | Published on npm as `0.1.0` |

### Node.js / TypeScript SDK

Install:

```bash
npm install sas-audit-client
```

Minimal usage:

```js
import { SASClient } from "sas-audit-client";

const client = new SASClient();

console.log(await client.health());
```

Authenticated usage:

```js
import { SASClient } from "sas-audit-client";

const client = new SASClient({
  apiKey: process.env.SAS_API_KEY
});

const result = await client.diff({
  textA: "The Eiffel Tower is located in Paris, France, and was completed in 1889.",
  textB: "The Eiffel Tower is located in Berlin, Germany, and was completed in 1950.",
  experimental: true
});

console.log(result.verdict);
console.log(result.isi);
```

SDK repository:

```text
https://github.com/Leesintheblindmonk1999/sas-js
```

npm package:

```text
https://www.npmjs.com/package/sas-audit-client
```

The SDK is TypeScript-first, JavaScript-compatible, ESM/CJS packaged, uses native `fetch`, supports Node.js 18+, and does not store API keys.

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

Or from Node.js / TypeScript:

```bash
npm install sas-audit-client
```

```js
import { SASClient } from "sas-audit-client";

const client = new SASClient();

const result = await client.demoAudit({
  source: "The Eiffel Tower is located in Paris, France, and was completed in 1889.",
  response: "The Eiffel Tower is located in Berlin, Germany, and was completed in 1950."
});

console.log(result.verdict);
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

Node.js / TypeScript:

```js
import { SASClient } from "sas-audit-client";

const client = new SASClient({
  apiKey: process.env.SAS_API_KEY
});

console.log(await client.whoami());
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

## R0 Infrastructure and Baseline Stability Audit

The R0 audit validates the research pipeline around SAS rather than claiming final production validation.

### Corpus scale

A local benchmark scan identified:

| Corpus/category | Complete pairs |
|---|---:|
| `halogen/biographies` | 9,362 |
| `halogen/code` | 15,190 |
| `halogen/historical_events` | 21,008 |
| `halogen/numerical_falsepresupposition` | 15,168 |
| `halogen/rationalization_binary` | 21,000 |
| `halogen/rationalization_numerical` | 14,274 |
| `halogen/references` | 24,918 |
| `halueval_dialogue/direct` | 10,000 |
| `halueval_general/direct` | 815 |
| `halueval_qa/direct` | 10,000 |
| `halueval_summarization/direct` | 10,000 |
| `truthfulqa/direct` | 790 |

Total:

```text
152,525 complete A/B hallucination pairs
305,050 generated clean-self records
12 corpus/category strata
```

### Stratified R0 runs

| Run | Records | Pairs/category | Train/Test | Minimal module | Minimal F1 | Full F1 | Gap |
|---|---:|---:|---:|---|---:|---:|---:|
| `sample_strat_2400` | 2,400 | 100 | 1,800 / 600 | `lexical_drift` | 0.9983 | 1.0000 | 0.0017 |
| `sample_strat_6000` | 6,000 | 250 | 4,500 / 1,500 | `lexical_drift` | 0.9987 | 1.0000 | 0.0013 |
| `sample_strat_12000` | 12,000 | 500 | 9,000 / 3,000 | `entity_drift` | 0.9993 | 1.0000 | 0.0007 |

Across increasing sample sizes, the baseline pipeline executed without runtime failures, maintained a stable module-correlation structure, and produced consistently low gaps between the selected minimal baseline tribunal and the full baseline pipeline.

### Stable correlation structure

Across the stratified runs, the correlation audit repeatedly found:

```text
Low-correlation pairs (< 0.60): 6
High-correlation pairs (> 0.85): 3
```

This indicates that some baseline modules are highly redundant under the clean-self condition, especially lexical/entity drift signals, while other modules may retain specialized signal even if they do not dominate global F1.

### R0 baseline modules

The R0 baseline audit used simple interpretable modules to validate the research infrastructure:

| Module | Purpose | Current status |
|---|---|---|
| `density_delta` | Character/token-density divergence | Baseline audit module |
| `entity_drift` | Entity-level source/response drift | Baseline audit module |
| `length_delta` | Length-shift signal | Baseline audit module |
| `lexical_drift` | Lexical divergence signal | Baseline audit module |
| `negation_shift` | Negation-presence shift | Baseline audit module |
| `numeric_invariant_loss` | Number/date/quantity mutation proxy | Baseline audit module |

These modules are not the full SAS production detector. They are R0 baseline modules used to validate the pipeline and generate reproducible module-correlation evidence.

### Error analysis

The 12,000-record run produced:

```text
Precision: 1.0000
Recall:    0.9987
F1:        0.9993
FP:        0
FN:        2
```

The two false negatives were localized in:

```text
halueval_general/direct
```

### Methodological boundary

These results are intentionally reported as:

```text
R0 infrastructure and baseline-stability evidence
```

not as:

```text
final SAS production validation
```

The main limitation is `clean_strategy=self`, where clean controls are generated as:

```text
source = A_clean
response = A_clean
```

This may inflate performance for dissimilarity-based modules. Future R1-oriented validation requires:

1. connecting real SAS modules to the R0 pipeline;
2. repeating the stratified protocol with SAS modules;
3. using independent clean negatives through `clean_strategy=external`;
4. evaluating the R1 multimetric tribunal under stronger ground-truth conditions.

Public record:

```text
https://zenodo.org/records/20647532
```

---

## Research modules and planned R0/R1 expansion

The next research phase is to connect the production SAS detector and planned R1 modules to the R0 research pipeline.

### Planned / in-progress research modules

| Module / layer | Purpose | Planned use |
|---|---|---|
| `sas_tda_score` | TDA / persistent homology structural score | R0 rerun with real SAS signal |
| `sas_nig_score` | Numerical Invariance Guard score | R0 rerun with real SAS signal |
| `source_target_guard_score` | Entity/location/date mutation guard | R0/R1 tribunal |
| `e9_contradiction_score` | Logical contradiction signal | R1 multimetric tribunal |
| `e10_grounding_score` | Unsupported claim / source-grounding signal | R1 multimetric tribunal |
| `e11_temporal_score` | Temporal inconsistency signal | R1 multimetric tribunal |
| `e12_topic_shift_score` | Abrupt topic-shift signal | R1 multimetric tribunal |
| `flow_cre_negation_composite` | Structural composite validated in R1-D (test F1=0.8571 on declarative QA) | Candidate for R1 multimetric tribunal; production-integration status to be confirmed against `core/` |
| `code_diff_isi` (vetoless) | AST structural comparison validated in R2.1 (AUC 0.9141-0.9421, reference required) | Candidate for a code-domain audit endpoint; requires a reference implementation at call time, not a drop-in replacement for `/v1/diff` on arbitrary text |
| `kappa_equivalence_scan` | κD semantic-equivalence and threshold-shield scanner | API-SHIELD / integrity layer |
| `module_observability` | `debug_modules=true`, per-module trace outputs | API-OBS |
| `evidence_bundle` | Hashes, module outputs, request metadata, reproducibility bundle | API-CERT |
| `certify_endpoint` | `/v1/certify`, signed audit certificate / evidence bundle | API-CERT |
| `multimetric_auditor` | Experimental R1 tribunal combining SAS modules | `/v2/audit` candidate |
| `temporal_consistency_score` | Multi-turn temporal consistency and drift analysis | R3 research line |
| `interaction_isi_bridge` | Bridge between interaction stability and structural ISI | R2 research line |
| `category_conditioned_tribunal` | Category-specific module weighting and failure analysis | R1/R2 research |

### Planned API/research layers

| Layer | Description |
|---|---|
| **API-OBS** | Module-level observability, `debug_modules=true`, internal score traces |
| **API-SHIELD** | κD equivalence scanner and semantic threshold integrity checks |
| **API-CERT** | Evidence bundles, SHA-256 traceability, `/v1/certify` candidate |
| **API-R1** | Multimetric tribunal and `/v2/audit` experimental route |
| **API-R2** | Interaction stability / ISI bridge and demand-sensitive degradation analysis |
| **API-R3** | Temporal consistency and multi-turn structural coherence checks |
| **API-HIST** | Historical Project Manifold integration and prior-art traceability |

The objective is not to replace the existing SAS production endpoints prematurely. The objective is to use the validated R0 infrastructure to compare, calibrate, and justify which SAS modules belong in a future R1 multimetric tribunal.

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

The Node SDK v0.1.0 intentionally omits the optional `domain` field from `diff()`, `audit()`, and `batch()` request types until domain-specific routing is a stable public contract.

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

Published developer packages:

```text
PyPI: sas-client
npm:  sas-audit-client@0.1.0
```

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

Planned experimental endpoints:

| Method | Endpoint | Status | Description |
|---|---|---|---|
| `GET/POST` | `/v1/certify` | Planned | Evidence bundle, hash, module trace, signed audit artifact |
| `POST` | `/v2/audit` | Planned experimental | R1 multimetric tribunal with real SAS modules |
| `POST` | `/v1/temporal/consistency` | Planned experimental | Multi-turn temporal consistency audit |
| `GET/POST` | `/v1/kappa/equivalence` | Planned internal/public split | κD semantic-equivalence and threshold-shield scanner |

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

> Results are dataset-specific. See [benchmark methodology](docs/benchmark.md) for scope and replication details.

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

## R0 research artifact — 152,525-pair corpus scan

| Item | Value |
|---|---:|
| Complete A/B pairs discovered | 152,525 |
| Clean-self records generated locally | 305,050 |
| Public stratified runs | 2,400 · 6,000 · 12,000 records |
| Corpus/category strata | 12 |
| Best 12k minimal baseline F1 | 0.9993 |
| 12k full baseline F1 | 1.0000 |
| 12k minimal/full gap | 0.0007 |
| 12k false positives | 0 |
| 12k false negatives | 2 |
| Public artifact SHA-256 | `b1c4b2eddc7b887f8721f3f193b5d1263e4822f13efd08f8b20ae95389dd36fe` |
| Zenodo record | `https://zenodo.org/records/20647532` |

> This R0 artifact is an infrastructure and baseline-stability audit under clean-self control. It is not a final production-grade validation.

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

Planned research package structure:

```text
research/
├── R0_correlation_audit/
│   ├── scripts/
│   │   ├── benchmark_corpus_to_jsonl.py
│   │   ├── stratified_sample_jsonl.py
│   │   ├── 00_create_split.py
│   │   ├── 01_run_isolated.py
│   │   ├── 02_correlation_matrix.py
│   │   ├── 03_marginal_contribution.py
│   │   ├── 04_validate_test.py
│   │   ├── 05_error_analysis.py
│   │   └── module_registry.py
│   ├── docs/
│   └── results/
├── R1_tribunal_multimetrico/
├── R2_theta_kappa_bridge/
├── R3_temporal_consistency/
└── experimental/
    └── kappa_equivalence/
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
| [Node SDK Plan](docs/sdk_node_plan.md) | Technical specification and implementation record for the Node.js / TypeScript SDK |
| [Billing](docs/billing.md) | Free/Pro flow, Polar, Mercado Pago, quotas |
| [Benchmark](docs/benchmark.md) | Methodology, limitations, replication guidance |
| [Security Notes](docs/security.md) | API keys, privacy, validation, rate limits, billing security |
| [Architecture](docs/architecture.md) | Detection pipeline, modules, and data flow |
| [Security Policy](SECURITY.md) | Vulnerability reporting and responsible disclosure |
| [Contributing Guide](CONTRIBUTING.md) | Development setup and pull requests |
| [Code of Conduct](CODE_OF_CONDUCT.md) | Community standards |
| [License](LICENSE.md) | GPL-3.0 + Durante Invariance License |

Recommended new documentation:

| Planned document | Purpose |
|---|---|
| `docs/r0_baseline_stability_audit.md` | Summary of the 2026-06-11 R0 audit and Zenodo record |
| `docs/r1_multimetric_tribunal_plan.md` | Plan for connecting SAS modules to the R1 tribunal |
| `docs/kappa_equivalence_shield.md` | κD semantic-equivalence and threshold-shield scanner |
| `docs/certify_endpoint_plan.md` | Evidence bundle and `/v1/certify` design |
| `docs/temporal_consistency_plan.md` | R3 temporal consistency research module |
| `docs/research_module_registry.md` | Mapping between production modules and research pipeline modules |

---

## Scope and limitations

- SAS measures structural coherence, not factual truth.
- A structurally coherent response can still be factually wrong.
- SourceTargetGuard detects source-response slot mutations; it does not replace an external knowledge base.
- Interaction-stability outputs are model constructs, not psychological diagnoses or legal determinations.
- `omega_t` measures belief-state concentration, not state desirability.
- Benchmark results are dataset-specific.
- R0 clean-self results may inflate performance for dissimilarity-based modules.
- R0 baseline modules are not the complete SAS production detector.
- Final R1 validation requires independent clean negatives and real SAS module integration.
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
- API-OBS: module-level traces through `debug_modules=true`.
- Research pipeline artifact hashing and reproducibility reports.

### Product expansion

- Minimal usage dashboard.
- Node.js / TypeScript SDK — completed as [`sas-audit-client@0.1.0`](https://www.npmjs.com/package/sas-audit-client); future work continues with examples, integrations, and ecosystem documentation.
- CLI support for batch files and interaction-stability calls.
- Signed PDF audit report with timestamp, hash, and provenance.
- API-CERT: evidence bundle and `/v1/certify` candidate endpoint.
- API-SHIELD: κD equivalence scanner for semantic threshold integrity.

### Scientific

- R0 rerun with real SAS modules connected to `module_registry.py`.
- Independent clean negatives through `clean_strategy=external`.
- R1 multimetric tribunal evaluation.
- Category-conditioned tribunal analysis.
- Benchmark v2.0 with narrative and multilingual corpora.
- Empirical calibration of interaction-stability parameters.
- R2 interaction stability / ISI bridge.
- R3 temporal consistency and multi-turn coherence auditing.
- External replication by independent researchers.
- Formal investigation of the conjectural bridge between `omega_t` and ISI.

### R0 → R1 transition plan

| Step | Goal | Status |
|---|---|---|
| R0-A | Validate infrastructure on small smoke tests | Completed |
| R0-B | Convert full local benchmark and create stratified samples | Completed |
| R0-C | Run 2.4k / 6k / 12k baseline stability audits | Completed |
| R0-D | Publish curated public artifact and technical report | Completed |
| R0-E | Connect real SAS modules to research registry | Next |
| R0-F | Repeat stratified audit with real SAS modules | Planned |
| R1-A | Add independent clean negatives | Planned |
| R1-B | Evaluate multimetric tribunal | Planned |
| R1-C | Publish R1 validation report | Planned |

---

## Ecosystem

| Repository | Role |
|---|---|
| [`SAS`](https://github.com/Leesintheblindmonk1999/SAS) | Main API, core engine, benchmark, docs, self-hosting |
| [`Project_Manifold_056`](https://github.com/Leesintheblindmonk1999/Project_Manifold_056) | Historical κD prior-art snapshot; R0/R0-bis/R0.5 external-clean tracks; R1/R1-D structural evaluations; R2.1 code-domain extension |
| [`sas-landing`](https://github.com/Leesintheblindmonk1999/sas-landing) | Public legitimacy layer: benchmark, API status, demo, activity feed |
| [`sas-client`](https://github.com/Leesintheblindmonk1999/sas-client) | Official Python client and CLI |
| [`sas-js`](https://github.com/Leesintheblindmonk1999/sas-js) | Official Node.js / TypeScript SDK, published on npm as [`sas-audit-client`](https://www.npmjs.com/package/sas-audit-client) |

---

## Citation

Primary SAS software record:

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

R0 infrastructure and baseline stability audit:

```text
Durante, G. E. (2026). R0 Infrastructure and Baseline Stability Audit for SAS/κD-0.56:
A Stratified Clean-Self Control Study over 152,525 Hallucination Pairs.
Zenodo. https://zenodo.org/records/20647532
```

```bibtex
@misc{durante_2026_sas_r0_baseline_audit,
  author       = {Durante, Gonzalo Emir},
  title        = {R0 Infrastructure and Baseline Stability Audit for SAS/κD-0.56:
                  A Stratified Clean-Self Control Study over 152,525 Hallucination Pairs},
  year         = {2026},
  publisher    = {Zenodo},
  url          = {https://zenodo.org/records/20647532},
  note         = {R0 infrastructure and baseline-stability audit under clean-self control}
}
```

R1-D structural evaluation over declarative corpus R0.5D:

```text
Durante, G. E. (2026). SAS / κD=0.56 — R1-D: Structural Evaluation over Declarative
Corpus R0.5D (halueval_qa). Zenodo. https://doi.org/10.5281/zenodo.21282332
```

R2.1 structural code hallucination detection:

```text
Durante, G. E. (2026). SAS / κD=0.56 — R2.1: Structural Code Hallucination Detection
via AST Fingerprinting, Validated on a Functional Corpus. Zenodo.
https://doi.org/10.5281/zenodo.21365707
```

---

## Author

**Gonzalo Emir Durante**

- GitHub: [Leesintheblindmonk1999](https://github.com/Leesintheblindmonk1999)
- API: [https://sas-api.onrender.com](https://sas-api.onrender.com)
- Landing: [https://leesintheblindmonk1999.github.io/sas-landing/](https://leesintheblindmonk1999.github.io/sas-landing/)
- SAS DOI: [10.5281/zenodo.19702379](https://doi.org/10.5281/zenodo.19702379)
- R0 Audit: [https://zenodo.org/records/20647532](https://zenodo.org/records/20647532)
- Contact: duranteg2@gmail.com
