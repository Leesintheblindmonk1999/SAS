# SAS Node SDK Technical Specification

Technical plan for the first Node.js / TypeScript SDK for **SAS — Symbiotic Autoprotection System**.

This document defines the intended behavior, scope, API surface, error model, security rules, and release strategy for the initial Node SDK implementation.

Target implementation phase:

```text
I0 -> specification
I1 -> implementation
```

---

## 1. Goal

The goal of the SAS Node SDK is to provide a small, typed, reliable client for integrating with the SAS hosted API or a self-hosted SAS deployment.

The SDK should make it easy for JavaScript and TypeScript developers to use SAS as a defensive audit layer for generative AI systems.

The SDK must support:

* public health and readiness checks;
* public demo auditing;
* authenticated identity checks;
* source/response structural diff auditing;
* single-text auditing;
* batch auditing;
* public aggregate stats;
* public anonymized activity;
* public interaction-stability stats;
* experimental interaction-stability analysis;
* interaction-stability example payload retrieval.

The SDK should be:

* TypeScript-first;
* usable from JavaScript;
* lightweight;
* secure by default;
* faithful to the public SAS API;
* explicit about errors and rate limits;
* configurable for hosted or self-hosted deployments.

The SDK should not hide SAS concepts. It should expose core fields such as:

* `isi`;
* `kappa_d`;
* `verdict`;
* `manipulation_alert`;
* `fired_modules`;
* `request_id`;
* `input_hash`;
* `content_fingerprint`;
* `interaction_stability_sigma`;
* `omega_t`;
* `dominant_state`.

The SDK is not intended to replace SAS documentation. It is a clean developer interface over the existing HTTP API.

---

## 2. Non-goals

The initial SDK version must remain small and focused.

The following are **not** goals for v0.1.0:

* billing endpoint support;
* admin endpoint support;
* chat endpoint support;
* dashboard UI;
* local storage of API keys;
* credential management;
* OAuth;
* automatic background polling;
* hidden telemetry;
* analytics;
* large dependency trees;
* retrying requests by default;
* implementing SAS detection logic locally;
* replacing the hosted API;
* modifying API contracts;
* inventing response fields that do not exist in the backend.

The SDK should be an interface to the API, not a separate product with different behavior.

The `chat` endpoint is intentionally excluded from v0.1.0 because it could confuse the positioning of the SDK. The initial SDK should focus on audit and observability surfaces.

Billing and admin endpoints are intentionally excluded because they are not part of the public developer integration surface.

The `domain` field is also excluded from v0.1.0 request types because the current production API does not require it for the initial SDK surface. Domain-specific routing or calibration can be added later if the backend exposes it as a stable contract.

---

## 3. Package name candidates

Final npm package availability must be checked before implementation and publication.

Candidate package names:

```text
@sas-audit/sdk
@sas-audit/client
sas-audit
sas-audit-client
sas-client-node
sas-sdk
symbiotic-autoprotection-system
```

Preferred candidate:

```text
@sas-audit/sdk
```

Reasoning:

* clearly communicates audit purpose;
* avoids confusion with chatbot SDKs;
* leaves room for future packages under the same namespace;
* reads naturally in import statements.

Example:

```ts
import { SASClient } from "@sas-audit/sdk";
```

Fallback candidate if scoped package is not available:

```text
sas-audit-client
```

Example:

```ts
import { SASClient } from "sas-audit-client";
```

Package name selection rules:

1. Prefer clarity over cleverness.
2. Avoid names that imply official standards-body status.
3. Avoid names that imply the SDK is a model.
4. Avoid names that imply the SDK is only for hallucination detection.
5. Prefer an audit-oriented name.

Before publication:

```bash
npm view @sas-audit/sdk
npm view sas-audit-client
npm view sas-audit
```

---

## 4. Runtime support

Minimum runtime:

```text
Node.js 18+
```

Reason:

* Node.js 18 includes native `fetch`;
* no default dependency on `axios` is required;
* modern TLS and `AbortController` support;
* aligns with current LTS expectations.

Language support:

```text
TypeScript-first
JavaScript-compatible
```

Build targets:

```text
ESM primary
CommonJS optional if simple to support
```

Recommended package output:

```text
dist/
├── index.js
├── index.d.ts
└── index.cjs   # optional
```

Recommended `package.json` fields:

```json
{
  "type": "module",
  "main": "./dist/index.cjs",
  "module": "./dist/index.js",
  "types": "./dist/index.d.ts",
  "exports": {
    ".": {
      "types": "./dist/index.d.ts",
      "import": "./dist/index.js",
      "require": "./dist/index.cjs"
    }
  },
  "engines": {
    "node": ">=18"
  }
}
```

Browser support:

The SDK should be Node-first for v0.1.0.

Browser usage may work for public endpoints if CORS allows the target API call, but authenticated browser usage is not recommended because it can expose API keys.

Documentation should state:

```text
This SDK is designed for Node.js 18+. Browser usage may work for public endpoints, but API-key-protected browser usage is not recommended because it can expose credentials.
```

Timeout implementation:

The SDK should implement request timeouts using `AbortController`, available in Node.js 18+.

---

## 5. Installation

Once published:

### npm

```bash
npm install @sas-audit/sdk
```

### yarn

```bash
yarn add @sas-audit/sdk
```

### pnpm

```bash
pnpm add @sas-audit/sdk
```

If the fallback package name is used:

```bash
npm install sas-audit-client
```

Development install from local source:

```bash
git clone https://github.com/Leesintheblindmonk1999/sas-js
cd sas-js
npm install
npm run build
```

---

## 6. Authentication

Authenticated SAS endpoints require:

```text
X-API-Key: sas_xxxxxxxxxxxxxxxxxxxxx
```

The SDK must support API key configuration through:

1. constructor parameter;
2. environment variable.

Constructor example:

```ts
const client = new SASClient({
  apiKey: "sas_xxxxxxxxxxxxxxxxxxxxx"
});
```

Environment variable example:

```bash
export SAS_API_KEY="sas_xxxxxxxxxxxxxxxxxxxxx"
```

```ts
const client = new SASClient();
```

The SDK should read:

```text
process.env.SAS_API_KEY
```

Optional alias support:

```text
process.env.SAS_KEY
```

Recommended precedence:

```text
constructor apiKey > SAS_API_KEY > SAS_KEY
```

Security requirements:

* the SDK must not store API keys on disk;
* the SDK must not write API keys into logs;
* the SDK must not expose API keys in thrown error messages;
* the SDK must not mutate `process.env`;
* the SDK must not persist credentials in localStorage, files, caches, or config folders;
* the SDK must only send the API key in the `X-API-Key` header for authenticated endpoints.

Public endpoints should not send `X-API-Key` unless explicitly required.

Authenticated methods should throw a clear local error if no API key is available.

Example error:

```text
Missing SAS API key. Pass apiKey to SASClient or set SAS_API_KEY.
```

---

## 7. Client initialization

Default hosted client:

```ts
import { SASClient } from "@sas-audit/sdk";

const client = new SASClient({
  apiKey: process.env.SAS_API_KEY
});
```

Self-hosted client:

```ts
const client = new SASClient({
  baseUrl: "http://localhost:8000",
  apiKey: process.env.SAS_API_KEY
});
```

Client options:

```ts
export interface SASClientOptions {
  baseUrl?: string;
  apiKey?: string;
  timeoutMs?: number;
  retry?: false | RetryOptions;
  headers?: Record<string, string>;
}
```

Defaults:

```ts
const DEFAULT_BASE_URL = "https://sas-api.onrender.com";
const DEFAULT_TIMEOUT_MS = 30_000;
const DEFAULT_RETRY = false;
```

Retry options:

```ts
export interface RetryOptions {
  attempts: number;
  backoffMs: number;
  respectRetryAfter?: boolean;
  retryOnStatuses?: number[];
}
```

Recommended retry defaults when enabled:

```ts
{
  attempts: 2,
  backoffMs: 500,
  respectRetryAfter: true,
  retryOnStatuses: [429, 500, 502, 503, 504]
}
```

The SDK should normalize `baseUrl` by removing trailing slashes.

Example:

```ts
new SASClient({
  baseUrl: "https://sas-api.onrender.com/"
});
```

should internally use:

```text
https://sas-api.onrender.com
```

---

## 8. Method list

The v0.1.0 SDK must expose exactly these 12 methods:

```text
1. health()
2. readyz()
3. demoAudit()
4. whoami()
5. diff()
6. audit()
7. batch()
8. publicStats()
9. publicActivity()
10. publicInteractionStats()
11. interactionStability()
12. interactionStabilityExample()
```

No billing, admin, or chat methods in v0.1.0.

---

### 8.1 `health()`

Endpoint:

```text
GET /health
```

Auth:

```text
No
```

Example:

```ts
const health = await client.health();
```

Purpose:

* basic liveness check;
* verify the API is reachable.

---

### 8.2 `readyz()`

Endpoint:

```text
GET /readyz
```

Auth:

```text
No
```

Example:

```ts
const readiness = await client.readyz();
```

Purpose:

* check router and database readiness;
* useful for monitoring and CI.

---

### 8.3 `demoAudit()`

Endpoint:

```text
POST /public/demo/audit
```

Auth:

```text
No
```

Example:

```ts
const result = await client.demoAudit({
  source: "The Eiffel Tower is located in Paris, France.",
  response: "The Eiffel Tower is located in Berlin, Germany."
});
```

Purpose:

* no-key onboarding;
* simple demonstration of SAS structural audit behavior.

---

### 8.4 `whoami()`

Endpoint:

```text
GET /v1/whoami
```

Auth:

```text
Yes
```

Example:

```ts
const me = await client.whoami();
```

Purpose:

* validate API key;
* inspect plan and quota.

---

### 8.5 `diff()`

Endpoint:

```text
POST /v1/diff
```

Auth:

```text
Yes
```

Example:

```ts
const result = await client.diff({
  textA: "Paris is in France.",
  textB: "Paris is in Germany.",
  experimental: true
});
```

Purpose:

* primary source/response forensic diff;
* detect structural rupture between two texts.

The SDK should map `textA` and `textB` to backend fields:

```json
{
  "text_a": "...",
  "text_b": "..."
}
```

`domain` is intentionally not part of the v0.1.0 request type.

---

### 8.6 `audit()`

Endpoint:

```text
POST /v1/audit
```

Auth:

```text
Yes
```

Example:

```ts
const result = await client.audit({
  text: "The Eiffel Tower is located in Berlin, Germany.",
  experimental: true
});
```

Purpose:

* single-text audit;
* useful when no explicit source/response pair is available.

For source-grounded auditing, developers should prefer `diff()`.

`domain` is intentionally not part of the v0.1.0 request type.

---

### 8.7 `batch()`

Endpoint:

```text
POST /v1/batch
```

Auth:

```text
Yes
```

Example:

```ts
const result = await client.batch({
  experimental: true,
  pairs: [
    {
      source: "The Eiffel Tower is located in Paris, France.",
      response: "The Eiffel Tower is located in Berlin, Germany."
    },
    {
      source: "Water boils at 100 degrees Celsius at sea level.",
      response: "Water boils at 100 degrees Celsius at sea level."
    }
  ]
});
```

Purpose:

* run multiple source/response audits in one request;
* useful for pipelines and CI.

`domain` is intentionally not part of the v0.1.0 request type.

---

### 8.8 `publicStats()`

Endpoint:

```text
GET /public/stats
```

Auth:

```text
No
```

Example:

```ts
const stats = await client.publicStats();
```

Purpose:

* public aggregate usage metrics;
* landing/dashboard support;
* monitoring.

---

### 8.9 `publicActivity()`

Endpoint:

```text
GET /public/activity?limit=...
```

Auth:

```text
No
```

Example:

```ts
const activity = await client.publicActivity({ limit: 10 });
```

Purpose:

* public anonymized activity feed;
* operational transparency.

---

### 8.10 `publicInteractionStats()`

Endpoint:

```text
GET /public/interaction/stats?days=...
```

Auth:

```text
No
```

Example:

```ts
const stats = await client.publicInteractionStats({ days: 7 });
```

Purpose:

* public aggregate stats for experimental interaction-stability usage;
* no raw text exposure;
* no per-user rows.

---

### 8.11 `interactionStability()`

Endpoint:

```text
POST /v1/interaction/stability
```

Auth:

```text
Yes
```

Example:

```ts
const result = await client.interactionStability({
  conversation: [
    { role: "user", content: "Necesito esto urgente, es para ayer." },
    { role: "assistant", content: "Entendido, lo proceso." }
  ],
  gamma: 0.85,
  window: 4,
  kappaD: 0.56,
  alpha: 2.0,
  mode: "analyze",
  normalizeDemand: true
});
```

Purpose:

* experimental temporal interaction audit;
* estimates belief-state concentration and demand-sensitive stability.

The SDK should map camelCase fields to backend snake_case where required:

```ts
kappaD -> kappa_d
normalizeDemand -> normalize_demand
```

Caution:

This method is experimental. It must not be described as psychological diagnosis, legal determination, or behavioral certification.

---

### 8.12 `interactionStabilityExample()`

Endpoint:

```text
GET /v1/interaction/stability/example
```

Auth:

```text
No
```

Example:

```ts
const example = await client.interactionStabilityExample();
```

Return type: `Promise<InteractionStabilityExampleResponse>`

* retrieve a valid example payload;
* improve onboarding for `interactionStability()`.

Note:

This endpoint is feature-flag controlled by the backend. If interaction stability is disabled, the API may return `503`.

---

## 9. TypeScript types

The SDK must export TypeScript types.

The implementation should avoid `any` in public interfaces.

Internal parsing may use `unknown`, but public responses should be typed.

---

### 9.1 Core client options

```ts
export interface SASClientOptions {
  baseUrl?: string;
  apiKey?: string;
  timeoutMs?: number;
  retry?: false | RetryOptions;
  headers?: Record<string, string>;
}

export interface RetryOptions {
  attempts: number;
  backoffMs: number;
  respectRetryAfter?: boolean;
  retryOnStatuses?: number[];
}
```

---

### 9.2 Common response fields

```ts
export interface SASBaseResponse {
  status?: string;
  request_id?: string;
  kappa_d?: number;
}
```

---

### 9.3 Health

```ts
export interface HealthResponse {
  status: string;
  kappa_d: number;
}
```

---

### 9.4 Readiness

```ts
export interface ReadyzResponse {
  status: "ready" | "degraded" | string;
  service: string;
  version: string;
  kappa_d: number;
  databases: {
    auth_db?: boolean;
    metrics_db?: boolean;
    audit_db?: boolean;
    rate_limit_db?: boolean;
    interaction_db?: boolean;
    [key: string]: boolean | undefined;
  };
  routers: {
    health?: boolean;
    audit?: boolean;
    diff?: boolean;
    admin?: boolean;
    metrics?: boolean;
    public_activity?: boolean;
    public_interaction_stats?: boolean;
    public_demo?: boolean;
    public_request_key?: boolean;
    whoami?: boolean;
    billing_polar?: boolean;
    billing_mercadopago?: boolean;
    chat?: boolean;
    audit_conversation?: boolean;
    status?: boolean;
    external_audit?: boolean;
    batch?: boolean;
    notarization?: boolean;
    interaction_stability?: boolean;
    [key: string]: boolean | undefined;
  };
}
```

---

### 9.5 Demo audit

```ts
export interface DemoAuditRequest {
  source: string;
  response: string;
}

export interface ManipulationAlert {
  triggered: boolean;
  sources?: string[];
}

export interface AuditEvidence {
  isi_final?: number;
  kappa_d?: number;
  fired_modules?: string[];
  [key: string]: unknown;
}

export interface DemoAuditResponse {
  status: string;
  isi: number;
  kappa_d: number;
  verdict: string;
  fired_modules?: string[];
  manipulation_alert?: ManipulationAlert;
  evidence?: AuditEvidence;
  demo?: boolean;
  latency_ms?: number;
  request_id?: string;
}
```

---

### 9.6 Whoami

```ts
export interface WhoamiResponse {
  status: string;
  plan: string;
  active?: boolean;
  email?: string;
  email_hash?: string;
  daily_limit?: number | null;
  monthly_limit?: number | null;
  daily_used?: number | null;
  monthly_used?: number | null;
  quota_allowed?: boolean;
  quota_reason?: string | null;
  [key: string]: unknown;
}
```

---

### 9.7 Diff

```ts
export interface DiffRequest {
  textA: string;
  textB: string;
  experimental?: boolean;
}

export interface DiffApiRequest {
  text_a: string;
  text_b: string;
  experimental?: boolean;
}

export interface DiffResponse {
  status?: string;
  isi: number;
  kappa_d: number;
  verdict: string;
  fired_modules?: string[];
  manipulation_alert?: ManipulationAlert;
  evidence?: AuditEvidence;
  request_id?: string;
  latency_ms?: number;
  [key: string]: unknown;
}
```

---

### 9.8 Audit

```ts
export interface AuditRequest {
  text: string;
  experimental?: boolean;
}

export interface AuditResponse {
  status?: string;
  isi: number;
  kappa_d?: number;
  verdict: string;
  fired_modules?: string[];
  manipulation_alert?: ManipulationAlert;
  evidence?: AuditEvidence;
  request_id?: string;
  latency_ms?: number;
  [key: string]: unknown;
}
```

---

### 9.9 Batch

```ts
export interface BatchPair {
  source: string;
  response: string;
}

export interface BatchRequest {
  pairs: BatchPair[];
  experimental?: boolean;
}

export interface BatchItemResult {
  index: number;
  status: string;
  isi?: number;
  kappa_d?: number;
  verdict?: string;
  fired_modules?: string[];
  manipulation_alert?: ManipulationAlert;
  error?: string | null;
  [key: string]: unknown;
}

export interface BatchResponse {
  status: string;
  count: number;
  results: BatchItemResult[];
  batch?: boolean;
  latency_ms?: number;
  request_id?: string;
}
```

---

### 9.10 Public stats

```ts
export interface PublicStatsResponse {
  status: string;
  period?: string;
  total_requests?: number;
  total_errors?: number;
  total_2xx?: number;
  total_4xx?: number;
  total_5xx?: number;
  avg_latency_ms?: number;
  countries?: Record<string, number>;
  paths?: Record<string, number>;
  plans?: Record<string, number>;
  [key: string]: unknown;
}
```

This type remains partially open with `[key: string]: unknown` because public metrics may evolve without breaking the SDK.

---

### 9.11 Public activity

```ts
export interface PublicActivityOptions {
  limit?: number;
}

export interface PublicActivityEvent {
  ts_utc?: string;
  time_bucket_utc?: string;
  method?: string;
  path?: string;
  status_bucket?: string;
  country?: string;
  plan?: string;
  [key: string]: unknown;
}

export interface PublicActivityResponse {
  status: string;
  activity?: PublicActivityEvent[];
  events?: PublicActivityEvent[];
  limit?: number;
  [key: string]: unknown;
}
```

Note: the canonical activity field in the current backend response is `activity`.
The `events` alias is kept for forward compatibility, but implementors should prefer
`activity` when both are present.

---

### 9.12 Public interaction stats

```ts
export interface PublicInteractionStatsOptions {
  days?: number;
}

export interface PublicInteractionStatsResponse {
  status: string;
  period: string;
  total_analyses: number;
  avg_conversation_turns?: number;
  avg_assistant_turns?: number;
  avg_final_sigma?: number;
  avg_final_omega_t?: number;
  avg_demand_peak?: number;
  threshold_crossed_pct?: number;
  stability_below_kappa_pct?: number;
  high_uncertainty_pct?: number;
  avg_latency_ms?: number;
  dominant_states_distribution?: Record<string, number>;
  plan_distribution?: Record<string, number>;
  sigma_buckets?: Record<string, number>;
  demand_peak_buckets?: Record<string, number>;
  privacy: {
    raw_text_stored: boolean;
    raw_api_keys_stored: boolean;
    public_stats_are_aggregated: boolean;
  };
}
```

---

### 9.13 Interaction stability

```ts
export type InteractionRole = "user" | "assistant" | "system" | string;

export interface InteractionTurn {
  role: InteractionRole;
  content: string;
}

export type InteractionMode = "analyze" | string;

export interface InteractionStabilityRequest {
  conversation: InteractionTurn[];
  gamma?: number;
  window?: number;
  kappaD?: number;
  alpha?: number;
  mode?: InteractionMode;
  normalizeDemand?: boolean;
}

export interface InteractionStabilityApiRequest {
  conversation: InteractionTurn[];
  gamma?: number;
  window?: number;
  kappa_d?: number;
  alpha?: number;
  mode?: InteractionMode;
  normalize_demand?: boolean;
}

export interface InteractionBeliefState {
  Open?: number;
  Ambivalent?: number;
  Saturated?: number;
  Avoidant?: number;
  Defensive?: number;
  [key: string]: number | undefined;
}

export interface InteractionTrajectoryPoint {
  t: number;
  raw_turn_index?: number;
  user_action?: string;
  agent_observation?: string;
  demand?: number;
  effective_window?: number;
  belief?: InteractionBeliefState;
  dominant_state?: string;
  dominant_probability?: number;
  omega_t?: number;
  belief_coherence_chi?: number;
  interaction_stability_sigma?: number;
  alerts?: {
    threshold_crossed?: boolean;
    stability_below_kappa?: boolean;
    high_uncertainty?: boolean;
    [key: string]: boolean | undefined;
  };
  [key: string]: unknown;
}

export interface InteractionSummary {
  final_omega_t?: number;
  final_chi?: number;
  final_sigma?: number;
  final_dominant_state?: string;
  final_dominant_probability?: number;
  demand_peak?: number;
  alerts?: {
    threshold_crossed?: boolean;
    stability_below_kappa?: boolean;
    high_uncertainty?: boolean;
    [key: string]: boolean | undefined;
  };
  [key: string]: unknown;
}

export interface InteractionStabilityResponse {
  status: string;
  mode: string;
  model_version?: string;
  theory_reference?: string;
  theory_doi?: string;
  kappa_d_ref?: number;
  theta_hat?: number;
  alpha?: number;
  trajectory: InteractionTrajectoryPoint[];
  summary: InteractionSummary;
  request_id?: string;
  executed_at?: string;
  input_hash?: string;
  content_fingerprint?: string;
  skipped_turns?: unknown[];
  [key: string]: unknown;
}
```

---

### 9.14 Interaction stability example

```ts
export interface InteractionStabilityExampleResponse {
  experimental_notice?: string;
  likelihood_note?: string;
  omega_note?: string;
  sigma_note?: string;
  threshold_note?: string;
  conjecture_note?: string;
  demand_note?: string;
  theory_doi?: string;
  conversation: InteractionTurn[];
  gamma?: number;
  window?: number;
  kappa_d?: number;
  alpha?: number;
  mode?: InteractionMode;
  normalize_demand?: boolean;
  [key: string]: unknown;
}
```

---

### 9.15 Rate-limit headers

The SDK should expose rate-limit-related headers when available.

```ts
export interface SASRateLimitHeaders {
  retryAfter?: string | number;
  limit?: string;
  remaining?: string;
  reset?: string;
}
```

Potential HTTP headers:

```text
Retry-After
X-RateLimit-Limit
X-RateLimit-Remaining
X-RateLimit-Reset
```

These headers may not always be present. The SDK must treat them as optional.

---

## 10. Error model

The SDK must expose a clear error model.

Recommended exported error classes:

```ts
export class SASError extends Error {
  readonly name = "SASError";
}

export class SASNetworkError extends SASError {
  readonly name = "SASNetworkError";
  cause?: unknown;
}

export class SASTimeoutError extends SASNetworkError {
  readonly name = "SASTimeoutError";
  timeoutMs: number;
}

export class SASAPIError extends SASError {
  readonly name = "SASAPIError";
  status: number;
  statusText: string;
  body: unknown;
  headers: Record<string, string>;
  requestId?: string;
  retryAfter?: string | number;
  rateLimit?: SASRateLimitHeaders;
}

export class SASAuthenticationError extends SASAPIError {
  readonly name = "SASAuthenticationError";
}

export class SASValidationError extends SASAPIError {
  readonly name = "SASValidationError";
}

export class SASRateLimitError extends SASAPIError {
  readonly name = "SASRateLimitError";
  // retryAfter and rateLimit are inherited from SASAPIError.
}

export class SASServerError extends SASAPIError {
  readonly name = "SASServerError";
}

export class SASConfigurationError extends SASError {
  readonly name = "SASConfigurationError";
}
```

Error mapping:

| Situation                                | Error class              |
| ---------------------------------------- | ------------------------ |
| missing API key for authenticated method | `SASConfigurationError`  |
| DNS/TLS/fetch failure                    | `SASNetworkError`        |
| timeout                                  | `SASTimeoutError`        |
| HTTP 400                                 | `SASAPIError`            |
| HTTP 401/403                             | `SASAuthenticationError` |
| HTTP 422                                 | `SASValidationError`     |
| HTTP 429                                 | `SASRateLimitError`      |
| HTTP 500–599                             | `SASServerError`         |

The SDK must preserve:

* HTTP status;
* parsed error body when available;
* headers;
* `request_id` if returned by the backend;
* `retry-after` if present;
* optional rate-limit headers if present.

The SDK must not include API keys in error messages.

Recommended behavior:

```ts
try {
  await client.diff({
    textA: "Paris is in France.",
    textB: "Paris is in Germany."
  });
} catch (err) {
  if (err instanceof SASRateLimitError) {
    console.log("Retry after:", err.retryAfter);
    console.log("Remaining:", err.rateLimit?.remaining);
  }
}
```

---

## 11. Rate-limit behavior

The SDK must detect HTTP 429.

When a response returns:

```text
HTTP 429 Too Many Requests
```

the SDK should throw:

```ts
SASRateLimitError
```

The error should expose:

```ts
error.status
error.body
error.headers
error.retryAfter
error.rateLimit
error.requestId
```

The SDK should read retry-after from:

```text
Retry-After
retry-after
```

The SDK may also expose optional rate-limit headers:

```text
X-RateLimit-Limit
X-RateLimit-Remaining
X-RateLimit-Reset
```

If the backend returns a structured JSON body such as:

```json
{
  "detail": {
    "error": "Persistent rate limit exceeded",
    "retry_after_seconds": 471
  }
}
```

the SDK should expose `retryAfter` from the header if available, and may also expose the raw JSON body for `retry_after_seconds`.

Recommended helper:

```ts
function getRateLimitInfo(headers: Headers, body: unknown): SASRateLimitHeaders
```

Behavior:

* do not retry 429 by default;
* expose retry information;
* if retries are enabled and `respectRetryAfter` is true, use `Retry-After` when practical;
* never retry indefinitely;
* never retry invalid requests.

---

## 12. Retry strategy

Retries must be disabled by default.

Default:

```ts
new SASClient({
  retry: false
});
```

Explicit retry:

```ts
const client = new SASClient({
  apiKey: process.env.SAS_API_KEY,
  retry: {
    attempts: 2,
    backoffMs: 500,
    respectRetryAfter: true,
    retryOnStatuses: [429, 500, 502, 503, 504]
  }
});
```

Retry rules:

1. Retries are opt-in.
2. Retry count must be finite.
3. Default should be `false`.
4. Respect `Retry-After` when configured.
5. Use simple exponential backoff or linear backoff.
6. Do not retry 400, 401, 403, or 422.
7. Do not retry if request construction failed locally.
8. Do not retry if the payload is invalid.
9. Do not hide final errors.

Recommended backoff calculation:

```ts
const delay = backoffMs * Math.pow(2, attemptIndex);
```

Retryable network errors:

* transient `fetch` failures;
* timeout, only if the caller explicitly configured retry;
* HTTP 429 when retry is enabled;
* HTTP 500, 502, 503, 504 when retry is enabled.

Non-retryable errors:

* `SASConfigurationError`;
* `SASAuthenticationError`;
* `SASValidationError`;
* malformed request;
* unsupported runtime.

---

## 13. Examples

### 13.1 Basic TypeScript usage

```ts
import { SASClient } from "@sas-audit/sdk";

const client = new SASClient({
  apiKey: process.env.SAS_API_KEY
});

const result = await client.diff({
  textA: "Paris is in France.",
  textB: "Paris is in Germany.",
  experimental: true
});

console.log(result.verdict);
console.log(result.isi);
console.log(result.manipulation_alert);
```

---

### 13.2 JavaScript usage

```js
import { SASClient } from "@sas-audit/sdk";

const client = new SASClient({
  apiKey: process.env.SAS_API_KEY
});

const result = await client.demoAudit({
  source: "The Eiffel Tower is located in Paris, France.",
  response: "The Eiffel Tower is located in Berlin, Germany."
});

console.log(result);
```

---

### 13.3 Self-hosted API

```ts
import { SASClient } from "@sas-audit/sdk";

const client = new SASClient({
  baseUrl: "http://localhost:8000",
  apiKey: process.env.SAS_API_KEY
});

const health = await client.health();

console.log(health.status);
```

---

### 13.4 Batch auditing

```ts
const batch = await client.batch({
  experimental: true,
  pairs: [
    {
      source: "The Eiffel Tower is located in Paris, France.",
      response: "The Eiffel Tower is located in Berlin, Germany."
    },
    {
      source: "Water boils at 100 degrees Celsius at sea level.",
      response: "Water boils at 100 degrees Celsius at sea level."
    }
  ]
});

for (const item of batch.results) {
  console.log(item.index, item.verdict, item.isi);
}
```

---

### 13.5 Public interaction stats

```ts
const stats = await client.publicInteractionStats({ days: 7 });

console.log("Total analyses:", stats.total_analyses);
console.log("Average latency:", stats.avg_latency_ms);
console.log("Raw text stored:", stats.privacy.raw_text_stored);
```

---

### 13.6 Experimental interaction stability

```ts
const result = await client.interactionStability({
  conversation: [
    {
      role: "user",
      content: "Necesito esto urgente, es para ayer."
    },
    {
      role: "assistant",
      content: "Entendido, lo proceso."
    },
    {
      role: "user",
      content: "Ok, gracias. Podemos hacerlo paso a paso."
    },
    {
      role: "assistant",
      content: "Sí, claro. Empecemos con una versión mínima."
    }
  ],
  gamma: 0.85,
  window: 4,
  kappaD: 0.56,
  alpha: 2.0,
  mode: "analyze",
  normalizeDemand: true
});

console.log(result.summary.final_dominant_state);
console.log(result.summary.final_sigma);
console.log(result.request_id);
```

---

### 13.7 Error handling

```ts
import {
  SASClient,
  SASRateLimitError,
  SASValidationError,
  SASAuthenticationError,
  SASAPIError
} from "@sas-audit/sdk";

const client = new SASClient({
  apiKey: process.env.SAS_API_KEY
});

try {
  const result = await client.diff({
    textA: "Paris is in France.",
    textB: "Paris is in Germany."
  });

  console.log(result.verdict);
} catch (err) {
  if (err instanceof SASRateLimitError) {
    console.error("Rate limited. Retry after:", err.retryAfter);
  } else if (err instanceof SASValidationError) {
    console.error("Validation error:", err.body);
  } else if (err instanceof SASAuthenticationError) {
    console.error("Invalid or missing API key.");
  } else if (err instanceof SASAPIError) {
    console.error("SAS API error:", err.status, err.body);
  } else {
    console.error("Unexpected error:", err);
  }
}
```

---

### 13.8 Retry opt-in

```ts
const client = new SASClient({
  apiKey: process.env.SAS_API_KEY,
  retry: {
    attempts: 2,
    backoffMs: 500,
    respectRetryAfter: true,
    retryOnStatuses: [429, 500, 502, 503, 504]
  }
});
```

---

## 14. Security notes

The SDK must follow these security rules:

1. Never store API keys on disk.
2. Never log API keys.
3. Never expose API keys in error messages.
4. Never mutate `process.env`.
5. Never send API keys to public endpoints unless required.
6. Never include API keys in query strings.
7. Use `X-API-Key` header for authenticated endpoints.
8. Do not implement hidden telemetry.
9. Do not send analytics from the SDK.
10. Do not persist request bodies.
11. Do not store raw text locally.
12. Do not automatically retry forever.
13. Do not automatically retry invalid requests.
14. Do not hide rate-limit responses.
15. Do not claim SAS is a factual oracle.

Recommended warning for browser use:

```text
Do not expose SAS API keys in browser-side code. Use the SDK from trusted server-side Node.js environments for authenticated endpoints.
```

Recommended logging pattern:

```ts
console.log({
  verdict: result.verdict,
  isi: result.isi,
  requestId: result.request_id
});
```

Avoid:

```ts
console.log(process.env.SAS_API_KEY);
console.log(client);
console.log(headers);
```

The SDK should be safe for server-side logs by default.

---

## 15. Test plan

The SDK implementation must include unit tests and integration tests.

### 15.1 Unit tests

Required unit tests:

* client initialization with defaults;
* base URL normalization;
* constructor API key precedence;
* `SAS_API_KEY` env fallback;
* `SAS_KEY` env fallback;
* missing API key error for authenticated methods;
* no API key required for public methods;
* `diff()` maps `textA` / `textB` to `text_a` / `text_b`;
* `interactionStability()` maps `kappaD` to `kappa_d`;
* `interactionStability()` maps `normalizeDemand` to `normalize_demand`;
* timeout handling using `AbortController`;
* network error handling;
* 400 error mapping;
* 401 error mapping;
* 422 error mapping;
* 429 error mapping;
* 5xx error mapping;
* retry disabled by default;
* retry opt-in behavior;
* `Retry-After` extraction;
* optional `X-RateLimit-*` header extraction;
* no API key included in thrown error message;
* no `domain` field sent by `diff()`, `audit()`, or `batch()` in v0.1.0.

### 15.2 Mocked HTTP tests

Use a mock fetch layer or HTTP interception library.

Mock scenarios:

* `/health` returns 200;
* `/readyz` returns 200;
* `/public/demo/audit` returns 200;
* `/v1/whoami` returns 401;
* `/v1/diff` returns 422;
* `/v1/diff` returns 429 with `Retry-After`;
* `/v1/batch` returns mixed item results;
* `/v1/interaction/stability` returns 503 when disabled;
* network failure;
* timeout.

### 15.3 Integration tests with real API

Integration tests should be opt-in and not run by default in CI unless a real key is configured.

Required environment variable:

```text
SAS_API_KEY
```

Optional:

```text
SAS_BASE_URL
```

Real API tests:

* `health()`;
* `readyz()`;
* `demoAudit()`;
* `whoami()`;
* `diff()`;
* `batch()`;
* `publicStats()`;
* `publicActivity()`;
* `publicInteractionStats()`;
* `interactionStabilityExample()`;
* `interactionStability()` if enabled.

Integration test command:

```bash
SAS_API_KEY=sas_xxxxxxxxxxxxxxxxxxxxx npm run test:integration
```

CI safety:

* no secrets printed;
* skip integration tests if `SAS_API_KEY` missing;
* sanitize responses before logs;
* do not use excessive request volume.

### 15.4 Manual smoke test

After build:

```bash
npm run build
npm test
node examples/health.mjs
node examples/diff.mjs
node examples/batch.mjs
```

---

## 16. Release plan

Initial release:

```text
v0.1.0
```

Release scope:

* TypeScript client;
* JavaScript-compatible build;
* 12 methods listed in this spec;
* typed request/response interfaces;
* error classes;
* optional retry support;
* examples;
* README;
* license;
* npm package.

Recommended repository:

```text
sas-js
```

or:

```text
sas-node-sdk
```

Recommended package:

```text
@sas-audit/sdk
```

subject to npm availability.

### 16.1 Pre-release checklist

Before publishing:

* [ ] Confirm package name availability.
* [ ] Confirm license.
* [ ] Confirm no secrets in repo.
* [ ] Confirm `npm test` passes.
* [ ] Confirm `npm run build` passes.
* [ ] Confirm type declarations generated.
* [ ] Confirm examples work.
* [ ] Confirm `SAS_API_KEY` is not logged.
* [ ] Confirm README includes installation and quick start.
* [ ] Confirm package exports work in TypeScript.
* [ ] Confirm package exports work in JavaScript.
* [ ] Confirm Node.js 18 compatibility.
* [ ] Confirm package tarball contents with `npm pack --dry-run`.

### 16.2 Publish

Dry run:

```bash
npm pack --dry-run
```

Publish public scoped package:

```bash
npm publish --access public
```

If unscoped package:

```bash
npm publish
```

### 16.3 Post-release validation

After release:

```bash
mkdir /tmp/sas-sdk-test
cd /tmp/sas-sdk-test
npm init -y
npm install @sas-audit/sdk
```

Create `test.mjs`:

```js
import { SASClient } from "@sas-audit/sdk";

const client = new SASClient();

console.log(await client.health());
```

Run:

```bash
node test.mjs
```

Authenticated validation:

```bash
SAS_API_KEY=sas_xxxxxxxxxxxxxxxxxxxxx node examples/diff.mjs
```

### 16.4 Version policy

Initial version:

```text
0.1.0
```

Rules:

* patch version for bug fixes;
* minor version for new methods;
* major version only for breaking API changes.

---

## 17. Future versions

Future versions may include:

### v0.2.0

Potential additions:

* `chat()` support, if positioning remains clear;
* stable `domain` support if backend contract supports it;
* stricter runtime validation;
* helper for request-key flow;
* richer examples;
* browser-safe public-only client;
* improved typed response narrowing by verdict.

### v0.3.0

Potential additions:

* streaming support if backend supports it;
* batch file helpers;
* CLI wrapper around the SDK;
* signed report helper if backend supports report generation;
* better RAG integration examples.

### v0.4.0+

Potential additions:

* LangChain integration;
* LlamaIndex integration;
* middleware for Express/Fastify;
* GitHub Action helper;
* CI audit helpers;
* structured PDF report support if available.

### Explicitly optional / later

* billing endpoints;
* admin endpoints;
* advanced dashboard helpers;
* enterprise-only private APIs.

These must not be included in v0.1.0.

The initial SDK should remain small, stable, auditable, and faithful to the existing SAS API.
