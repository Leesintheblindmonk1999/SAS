# SAS Privacy and Observability Notes

SAS is designed as a defensive audit system. Its operational logging supports
reliability, abuse prevention, reproducibility, and aggregate research without
storing raw submitted content.

## Interaction Stability Observability

For the experimental `/v1/interaction/stability` endpoint, SAS may store
operational metadata and aggregate model outputs, including request ID,
timestamp, short hashed API-key identifier, user/plan bucket, turn counts,
final dominant state, final omega/sigma values, demand peak, alert flags,
input hash, content fingerprint, and latency.

SAS does **not** store raw conversation text in the interaction observability
store.

## Hashes and fingerprints

SAS may store hashes or fingerprints for reproducibility, deduplication,
diagnostics, abuse prevention, and operational debugging. These values are not
intended to expose raw submitted content or raw API keys.

## Rate limiting and security logs

SAS rate limiting stores hashed identifiers and path/method metadata. It does
not store raw API keys and is designed to avoid storing raw IP addresses.

## Public statistics

Public stats endpoints expose only aggregate metrics. They do not expose raw
submitted text, request IDs, API keys, API key hashes, input hashes, content
fingerprints, or per-user rows.

## Experimental-status note

Interaction stability outputs are model constructs from an experimental research
framework. They are not psychological diagnoses, legal determinations, or
behavioral intervention guidance.
