# SAS Benchmark Documentation

This document summarizes the current SAS benchmark artifact, interpretation, and recommended future benchmark work.

Current benchmark artifact:

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

Zenodo DOI:

```text
10.5281/zenodo.19702379
```

---

## 1. Current benchmark summary

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

Confusion matrix:

|  | Actual hallucination | Actual clean |
|---|---:|---:|
| Predicted hallucination | TP = 976 | FP = 0 |
| Predicted clean | FN = 24 | TN = 1000 |

---

## 2. Interpretation

The benchmark indicates strong performance on the evaluated dataset.

However, all benchmark claims should be stated with context:

```text
Benchmark results are dataset-specific.
They do not prove universal factual verification.
They show performance on the published benchmark configuration.
```

Recommended public wording:

```text
SAS achieved 98.8% accuracy on its documented 2,000-pair benchmark.
See the benchmark artifact and DOI for methodology and replication context.
```

Avoid wording like:

```text
SAS solves hallucinations.
SAS detects all hallucinations.
SAS is universally accurate.
```

---

## 3. How to run

From repository root:

```bash
python tests/benchmark_runner.py
```

Recommended output artifacts:

```text
docs/benchmark_complete_<timestamp>.json
docs/benchmark_complete_<timestamp>.json.ots
```

For each benchmark run, record:

- dataset version;
- SAS version;
- κD;
- enabled modules;
- timestamp;
- hash;
- environment;
- confusion matrix;
- per-case results.

---

## 4. Recommended benchmark JSON structure

```json
{
  "metadata": {
    "sas_version": "1.1.0",
    "kappa_d": 0.56,
    "dataset_name": "sas-benchmark",
    "dataset_version": "2026-04-29",
    "created_at": "2026-04-29T17:26:47Z"
  },
  "summary": {
    "total_pairs": 2000,
    "accuracy": 0.988,
    "precision": 1.0,
    "recall": 0.976,
    "f1": 0.9879
  },
  "confusion_matrix": {
    "tp": 976,
    "fp": 0,
    "fn": 24,
    "tn": 1000
  },
  "cases": []
}
```

---

## 5. Mini regression suite

Before every release, run a small deterministic suite.

Recommended cases:

| Case | Expected |
|---|---|
| Identical texts | `PERFECT_EQUILIBRIUM`, ISI = 1.0 |
| Faithful paraphrase | ISI >= κD |
| Eiffel Paris/1889 -> Berlin/1950 | `MANIFOLD_RUPTURE`, SourceTargetGuard |
| Python language -> python snake | `MANIFOLD_RUPTURE` or strong drift |
| 5 mg -> 50 mg | numerical mutation |
| consistent year paraphrase | no year mismatch |
| abrupt topic shift | E12 or low ISI if enough context |
| too-short input | controlled error, no 500 |
| missing key | 401 |
| invalid body | 422 with examples |

---

## 6. SourceTargetGuard regression case

This case should never regress:

```text
A:
The Eiffel Tower is located in Paris, France.
It was built in 1889.
It is one of the most recognized landmarks in France.

B:
The Eiffel Tower is located in Berlin, Germany.
It was built in 1950.
It is one of the most recognized landmarks in Germany.
```

Expected:

```json
{
  "isi": 0.25,
  "verdict": "MANIFOLD_RUPTURE",
  "confidence": 0.85,
  "manipulation_alert": {
    "triggered": true,
    "sources": ["SourceTargetGuard"]
  }
}
```

Required evidence:

```text
year mismatch: 1889 -> 1950
removed France, Paris
added Berlin, Germany
```

---

## 7. Known benchmark limitations

Current benchmark limitations:

- dataset-specific;
- likely stronger on structured factual mutations than open-ended narrative drift;
- factual grounding depends on local knowledge sources;
- multilingual coverage should be expanded;
- long-form narrative coherence requires additional evaluation;
- external replication is still needed.

---

## 8. Recommended v2 benchmark

A stronger benchmark should include:

### Domains

- RAG factual QA;
- biographies;
- historical claims;
- medicine-like safety claims;
- legal/compliance-like claims;
- arithmetic and finance;
- multilingual Spanish/English cases;
- long narrative summaries;
- opinion-like text with subtle unsupported claims.

### Mutation types

- entity swap;
- location swap;
- year/date shift;
- quantity change;
- negation flip;
- unsupported citation;
- invented source;
- topic drift;
- temporal contradiction;
- paraphrase with preserved meaning;
- faithful compression;
- faithful expansion.

### Required metrics

- accuracy;
- precision;
- recall;
- F1;
- false positive rate;
- false negative rate;
- per-domain performance;
- latency distribution;
- module firing frequency.

---

## 9. Replication package

For independent replication, publish:

```text
dataset.jsonl
benchmark_runner.py
requirements.txt
SAS version/tag
expected output hash
README with exact command
```

Example command:

```bash
python tests/benchmark_runner.py \
  --dataset docs/benchmark_dataset_v2.jsonl \
  --output docs/benchmark_results_v2.json
```

---

## 10. Zenodo release guidance

Publish a new Zenodo release when a major benchmark or API milestone lands.

Recommended next release contents:

- SAS source release tag;
- sas-client v0.2.0+;
- SourceTargetGuard description;
- benchmark output;
- OTS proof;
- README;
- docs/manifold.md;
- docs/benchmark.md.

---

## 11. Public communication guidance

Strong phrasing:

```text
SAS is an open-source structural coherence auditing API for generative AI outputs.
```

Defensible claim:

```text
SAS achieved 98.8% accuracy on its documented 2,000-pair benchmark.
```

Avoid overclaiming:

```text
SAS solves hallucinations.
SAS proves truth.
SAS detects all factual errors.
```
