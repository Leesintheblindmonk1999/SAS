# SAS Manifold Model

This document explains the structural coherence model used by **SAS — Symbiotic Autoprotection System**.

SAS is not designed as a universal factual oracle. It is designed as an audit layer for generative AI outputs: it compares a source and a generated response and evaluates whether the response preserves structural, semantic, logical, numerical, and source-response invariants.

---

## 1. Core idea

Large language models can produce fluent text that looks plausible while silently changing important structure:

- dates;
- quantities;
- entities;
- locations;
- logical polarity;
- references;
- topic continuity;
- numerical relations.

SAS treats these failures as **structural coherence failures**.

The central question is:

```text
Did the response preserve the meaningful structure of the source?
```

---

## 2. κD — Durante Constant

SAS uses:

```text
κD = 0.56
```

Operational interpretation:

```text
ISI >= κD  -> structurally coherent / acceptable drift
ISI <  κD  -> manifold rupture / hallucination signal
```

κD is not presented as a universal law of nature. It is the operational threshold used by the SAS pipeline and benchmarked in the current release.

---

## 3. ISI — Invariant Similarity Index

**ISI** means **Invariant Similarity Index**.

It is the main score returned by SAS.

Typical range:

```text
0.00 -> complete rupture / strong mismatch
1.00 -> maximum structural invariance
```

Example:

```json
{
  "isi": 0.25,
  "verdict": "MANIFOLD_RUPTURE"
}
```

SAS interprets ISI relative to κD:

```text
0.80 - 1.00  strong structural preservation
0.56 - 0.80  acceptable or minor drift
0.00 - 0.56  rupture / hallucination signal
```

Exact behavior depends on modules, text length, detected domain, and enabled experimental checks.

---

## 4. TDA — Topological Data Analysis

SAS uses topological comparison to detect whether two texts preserve similar semantic structure.

The intuition:

```text
Two texts can use different words but preserve the same semantic shape.
Two texts can also use almost the same words while changing critical facts.
```

TDA is useful for structural comparison but is not sufficient alone. This is why SAS combines TDA with additional guards.

Known limitation:

```text
If a response preserves the same sentence shape but mutates facts, topology alone may still look similar.
```

Example:

```text
Source:   The Eiffel Tower is located in Paris, France. It was built in 1889.
Response: The Eiffel Tower is located in Berlin, Germany. It was built in 1950.
```

This has similar structure but different factual slots. SAS handles this using SourceTargetGuard.

---

## 5. NIG — Numerical Invariance Guard

NIG checks numerical consistency and numerical invariants.

It helps catch:

- changed quantities;
- incompatible numerical relations;
- suspicious arithmetic shifts;
- numeric claims that violate expected relations.

Example:

```text
Source:   The dose is 5 mg.
Response: The dose is 50 mg.
```

A numeric mutation like this can be safety-critical even when text overlap is high.

---

## 6. SourceTargetGuard

**SourceTargetGuard** is the source-response invariance guard added to prevent same-shape factual mutations from passing as coherent.

It compares critical anchors between source and response:

- years;
- numbers;
- capitalized entities;
- anchored entity/location shifts;
- removed and added named entities when a shared anchor remains.

Example:

```text
Source:
The Eiffel Tower is located in Paris, France.
It was built in 1889.
It is one of the most recognized landmarks in France.

Response:
The Eiffel Tower is located in Berlin, Germany.
It was built in 1950.
It is one of the most recognized landmarks in Germany.
```

Expected signal:

```json
{
  "isi": 0.25,
  "verdict": "MANIFOLD_RUPTURE",
  "manipulation_alert": {
    "triggered": true,
    "sources": ["SourceTargetGuard"]
  },
  "evidence": {
    "fired_modules": [
      "SourceTargetGuard: year mismatch: 1889 -> 1950; anchored entity/location shift: removed France, Paris; added Berlin, Germany (guard ISI=0.250)"
    ]
  }
}
```

Important:

```text
SourceTargetGuard does not claim that Paris or Berlin is externally true.
It only checks whether the response preserved the invariants supplied by the source.
```

---

## 7. E9-E12 modules

SAS includes optional experimental modules:

| Module | Name | Purpose |
|---|---|---|
| E9 | Logical Contradiction | Detects high-confidence logical contradiction or polarity inversion |
| E10 | Fact Grounding | Checks claims against local grounding sources when configured |
| E11 | Temporal Inconsistency | Detects incompatible temporal sequences |
| E12 | Topic Shift | Detects abrupt topic changes without transition signals |

These modules are conservative by design. They should reduce false positives rather than aggressively label every drift as hallucination.

---

## 8. Verdicts

Common verdicts include:

| Verdict | Meaning |
|---|---|
| `PERFECT_EQUILIBRIUM` | Texts are identical or maximally invariant |
| `MINOR_DRIFT` | The response has drift but remains above κD |
| `MANIFOLD_RUPTURE` | The response fell below κD or a critical guard fired |
| `ERROR` | Input or processing error |

A verdict should be interpreted with `isi`, `confidence`, and `evidence`.

---

## 9. Evidence object

SAS returns an evidence object to make results auditable.

Common fields:

```json
{
  "isi_final": 0.25,
  "kappa_d": 0.56,
  "isi_tda": 1.0,
  "isi_nig": 1.0,
  "isi_hard": 1.0,
  "lexical_overlap": 0.7,
  "fired_modules": [],
  "module_notes": [],
  "extended_modules": []
}
```

Interpretation:

- `isi_final`: final score after guards and modules.
- `isi_tda`: topological similarity score.
- `isi_nig`: numerical invariance signal.
- `fired_modules`: human-readable reasons for penalties.
- `module_notes`: skipped or disabled module explanations.
- `extended_modules`: structured module outputs.

---

## 10. Known limitations

SAS is useful for structural coherence auditing, but it has limits:

- It is not a universal truth database.
- E10 factual grounding depends on configured local knowledge sources.
- Very short texts provide weak structural signal.
- Some paraphrases can look distant lexically while still being faithful.
- Some hallucinations require external world knowledge.
- Results should be interpreted as technical evidence, not automatic legal certification.

---

## 11. Recommended use

SAS is best used as:

- a RAG output validator;
- an LLM response audit layer;
- a CI-style regression test for generated answers;
- a forensic comparison tool between source and response;
- a compliance evidence generator when paired with timestamping and signed reports.

Recommended production pattern:

```text
LLM output -> SAS /v1/diff -> inspect ISI/verdict/evidence -> accept, flag, retry, or escalate
```

---

## 12. Minimal example

```bash
sas diff \
  "The Eiffel Tower is located in Paris, France. It was built in 1889." \
  "The Eiffel Tower is located in Berlin, Germany. It was built in 1950."
```

Expected:

```text
MANIFOLD_RUPTURE
SourceTargetGuard
ISI below κD
```
