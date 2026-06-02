# SAS - Symbiotic Autoprotection System

> Extended bilingual documentation hub / Centro de documentación bilingüe extendido.
>
> Main repository README: [../README.md](../README.md) · API reference: [api.md](api.md) · Privacy: [../PRIVACY.md](../PRIVACY.md)


[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19702379.svg)](https://doi.org/10.5281/zenodo.19702379)
[![Landing Page](https://img.shields.io/badge/🌐-Landing_Page-0a0e17?style=flat&logo=github)](https://leesintheblindmonk1999.github.io/sas-landing/)
[![API Online](https://img.shields.io/badge/API-online-brightgreen)](https://sas-api.onrender.com)
[![PyPI](https://img.shields.io/pypi/v/sas-client?label=sas-client&color=blue)](https://pypi.org/project/sas-client/)
[![License](https://img.shields.io/badge/license-GPL--3.0%20%2B%20Durante%20Invariance-blue)](../LICENSE.md)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](../requirements.txt)
[![API](https://img.shields.io/badge/API-FastAPI-009688)](https://sas-api.onrender.com/docs)
[![Status](https://img.shields.io/badge/status-research%20alpha-orange)](#es-alcance-y-limitaciones)
[![Benchmark](https://img.shields.io/badge/benchmark-98.8%25%20accuracy-brightgreen)](benchmark_complete_20260429_172647.json)
[![OTS Proof](https://img.shields.io/badge/OpenTimestamps-proof-blueviolet)](benchmark_complete_20260429_172647.json.ots)
[![Security](https://img.shields.io/badge/security-policy-lightgrey)](../SECURITY.md)
[![Contributing](https://img.shields.io/badge/contributions-welcome-brightgreen)](../CONTRIBUTING.md)
[![Smoke Test](https://github.com/Leesintheblindmonk1999/SAS/actions/workflows/smoke_test.yml/badge.svg)](https://github.com/Leesintheblindmonk1999/SAS/actions/workflows/smoke_test.yml)

<!-- SAS-LIVE-METRICS:START -->
## Live Operational Snapshot / Estado Operativo Vivo

_Last automated update / Última actualización automática:_ `2026-05-12T19:41:56+00:00`

> ⚠️ This block is updated by an automated workflow and may lag behind current activity. For the live state, use `/readyz`, `/public/stats`, `/public/activity`, and `/public/interaction/stats`.
>
> ⚠️ Este bloque se actualiza mediante un workflow automatizado y puede quedar retrasado respecto de la actividad actual. Para el estado vivo, usar `/readyz`, `/public/stats`, `/public/activity` y `/public/interaction/stats`.

### English

| Signal | Value |
|---|---:|
| API product requests, last 24h | `18` |
| Successful requests, last 24h | `17` |
| 4xx errors, last 24h | `1` |
| 5xx errors, last 24h | `0` |
| Unique anonymized users, last 24h | `4` |
| API product requests, last 7d | `18` |
| Detected country buckets | `AR=14, US=3, unknown=1` |
| Monitoring signal | `normal_public_activity` |
| Repository clones | `unavailable` |
| Unique cloners | `unavailable` |

### Español

| Señal | Valor |
|---|---:|
| Requests de producto, últimas 24h | `18` |
| Requests exitosas, últimas 24h | `17` |
| Errores 4xx, últimas 24h | `1` |
| Errores 5xx, últimas 24h | `0` |
| Usuarios anonimizados únicos, últimas 24h | `4` |
| Requests de producto, últimos 7d | `18` |
| Países detectados | `AR=14, US=3, unknown=1` |
| Señal de monitoreo | `normal_public_activity` |
| Clones del repositorio | `unavailable` |
| Clonadores únicos | `unavailable` |

> Public note / Nota pública: generated from aggregated public API metrics and GitHub traffic data. No raw IPs, raw API keys, API key hashes, or request IDs are published.
<!-- SAS-LIVE-METRICS:END -->

## Language / Idioma

- [Español](#es)
- [English](#en)
  
---

<a id="es"></a>

# Español

**SAS - Symbiotic Autoprotection System** es un framework API open source para detectar alucinaciones estructurales en salidas de IA generativa.

SAS evalúa si una respuesta generada preserva estructura semántica, consistencia lógica, integridad numérica y señales de coherencia factual respecto de un texto fuente o prompt. Combina análisis topológico de datos, invariancia numérica y módulos especializados de detección dentro de una API basada en FastAPI.

El sistema fue creado por **Gonzalo Emir Durante** y se publica como candidato a estándar técnico abierto para auditoría estructural de coherencia en sistemas de IA.

---

<a id="es-api-publica"></a>

## API pública en vivo

La API pública oficial de referencia ya está en funcionamiento:

**[https://sas-api.onrender.com](https://sas-api.onrender.com)**

Health check:

```bash
curl https://sas-api.onrender.com/health
```

Documentación interactiva de FastAPI:

```text
https://sas-api.onrender.com/docs
```

El autoalojamiento sigue siendo completamente posible bajo los términos de la licencia del proyecto.

---

<a id="es-estado-operativo-actual"></a>

## Estado operativo actual

SAS ya no es solo un prototipo de detección: actualmente opera como una API pública con autenticación, cuotas, rate limiting, observabilidad, smoke tests y stores persistentes.

Estado validado recientemente:

```text
/health                               -> ok
/readyz                               -> ready
/public/stats                         -> ok
/public/activity                      -> ok
/public/interaction/stats             -> ok
/v1/diff                              -> activo
/v1/audit                             -> activo
/v1/batch                             -> activo
/v1/interaction/stability             -> activo detrás de flag + API key
```

Bases verificadas por `/readyz`:

| Store | Estado | Uso |
|---|---|---|
| `auth.db` | activo | usuarios, API keys, cuotas |
| `metrics.db` | activo | métricas de requests y funnel |
| `audit.db` | activo | audit trail y validation errors |
| `rate_limit.db` | activo | eventos de rate limiting |
| `interaction.db` | activo | observabilidad agregada de interaction stability |

Routers relevantes activos:

```text
public_demo
public_request_key
public_activity
public_interaction_stats
whoami
diff
audit
batch
interaction_stability
billing_polar
billing_mercadopago
notarization
```

Superficies actuales:

| Línea | Endpoints |
|---|---|
| Structural Coherence Auditing | `/v1/diff`, `/v1/audit`, `/v1/batch`, `/public/demo/audit` |
| Temporal Interaction Auditing | `/v1/interaction/stability`, `/v1/interaction/stability/example`, `/public/interaction/stats` |
| Onboarding | `/public/request-key`, `/v1/whoami` |
| Observabilidad pública | `/public/stats`, `/public/activity`, `/public/interaction/stats` |
| Sistema | `/health`, `/readyz`, `/integrity`, `/robots.txt` |
| Billing alojado | Polar + Mercado Pago checkout/webhooks |

---

<a id="es-python-client"></a>

## Cliente Python oficial

SAS está disponible como cliente Python y CLI instalable desde PyPI:

```bash
pip install sas-client
```

Repositorio del cliente:

```text
https://github.com/Leesintheblindmonk1999/sas-client
```

PyPI:

```text
https://pypi.org/project/sas-client/
```

### Uso desde Python

```python
from sas_client import SASClient

client = SASClient(api_key="YOUR_API_KEY")

result = client.diff(
    text_a="Python is a programming language.",
    text_b="A python is a snake."
)

print(result["isi"])
print(result["verdict"])
print(result.get("evidence", {}).get("fired_modules"))
```

### Uso CLI

```bash
sas health
sas public-stats
sas public-activity --limit 10
sas --api-key YOUR_API_KEY diff "Python is a programming language." "A python is a snake."
```

En Windows PowerShell:

```powershell
$env:SAS_API_KEY="YOUR_API_KEY"
sas diff "Python is a programming language." "A python is a snake."
```

---

<a id="es-documentacion"></a>

## Documentación

| Documento | Descripción |
|---|---|
| [README principal](../README.md) | Vista rápida del proyecto, API pública, capacidades y roadmap |
| [Privacy and Observability](../PRIVACY.md) | Manejo de datos, hashes, fingerprints y stats públicas |
| [API Reference](api.md) | Endpoints, auth, ejemplos, errores y recomendaciones de cliente |
| [Architecture Overview](architecture.md) | Diseño de alto nivel, pipeline de detección, módulos y flujo de datos |
| [Manifold Model](manifold.md) | ISI, κD, TDA, NIG, SourceTargetGuard y módulos E9-E12 |
| [Benchmark](benchmark.md) | Metodología, limitaciones y guía de replicación |
| [Billing](billing.md) | Free/Pro flow, Polar, Mercado Pago, cuotas y webhooks |
| [Security Notes](security.md) | API keys, rate limits, validación, privacidad y seguridad operativa |
| [Benchmark JSON](benchmark_complete_20260429_172647.json) | Resultado completo del benchmark |
| [Benchmark OTS Proof](benchmark_complete_20260429_172647.json.ots) | Prueba OpenTimestamps del benchmark |
| [Security Policy](../SECURITY.md) | Reporte de vulnerabilidades, notas de seguridad y divulgación responsable |
| [Contributing Guide](../CONTRIBUTING.md) | Setup de desarrollo, pull requests, testing y reglas de contribución |
| [Code of Conduct](../CODE_OF_CONDUCT.md) | Estándares comunitarios y política de convivencia |
| [Bug Report Template](../.github/ISSUE_TEMPLATE/bug_report.md) | Template de GitHub Issues para bugs |
| [Feature Request Template](../.github/ISSUE_TEMPLATE/feature_request.md) | Template de GitHub Issues para mejoras |
| [License](../LICENSE.md) | GPL-3.0 + Durante Invariance License |

---

## 🌐 Manifesto Público / Estándar SAS

**Landing page oficial:** [sas-landing](https://leesintheblindmonk1999.github.io/sas-landing/)

Benchmark, declaración de neutralidad geopolítica, registro TAD, DOI y anclaje OpenTimestamps.

---

<a id="es-problema"></a>

## Problema que resuelve

Los sistemas de IA generativa pueden producir respuestas fluidas pero estructuralmente inconsistentes, lógicamente invertidas, numéricamente erróneas o desconectadas semánticamente del input.

Las métricas tradicionales de similitud suelen fallar en estos casos, porque una alucinación puede conservar fluidez superficial mientras rompe coherencia profunda.

SAS aborda este problema tratando la detección de alucinaciones como una tarea de **auditoría estructural de coherencia**.

SAS está diseñado para detectar:

- ruptura de manifold semántico;
- contradicción lógica;
- inconsistencia numérica;
- anomalías de referencia o grounding;
- cambios abruptos de tema;
- divergencia estructural entre fuente y respuesta.

SAS no es un oráculo factual universal. Produce evidencia técnica para auditoría de coherencia estructural y señales de alucinación.

---

<a id="es-kappa"></a>

## Concepto central: κD = 0.56

SAS utiliza la constante:

```text
κD = 0.56
```

κD, también llamada **Durante Constant**, funciona como umbral crítico de coherencia dentro del pipeline SAS.

Interpretación operacional:

```text
ISI >= κD  -> estructuralmente coherente
ISI <  κD  -> posible ruptura de manifold / señal de alucinación
```

La constante se utiliza junto con el **Invariant Similarity Index (ISI)** y módulos adicionales de detección.

---

<a id="es-lineas-tecnicas"></a>

## Líneas técnicas actuales

### 1. Structural Coherence Auditing

Endpoints:

```text
POST /public/demo/audit
POST /v1/diff
POST /v1/audit
POST /v1/batch
```

Propósito:

- comparar texto fuente contra respuesta generada;
- detectar ruptura semántica estructural;
- detectar mutaciones de fechas, lugares, entidades, cantidades o afirmaciones críticas;
- producir `isi`, `verdict`, `fired_modules` y `manipulation_alert`.

### 2. Temporal Interaction Auditing

Endpoints experimentales:

```text
GET  /v1/interaction/stability/example
POST /v1/interaction/stability
GET  /public/interaction/stats
```

Este módulo está basado en la línea de investigación:

```text
A Control-Theoretic Model for Stochastic Interaction under Hidden-State
Uncertainty and Demand-Sensitive Response Degradation
DOI: 10.5281/zenodo.20335612
```

Estados ocultos modelados:

```text
Open · Ambivalent · Saturated · Avoidant · Defensive
```

Campos principales:

| Campo | Significado |
|---|---|
| `omega_t` | Concentración normalizada del belief state |
| `belief_coherence_chi` | Alias retrocompatible de `omega_t` |
| `dominant_state` | Estado oculto más probable bajo el modelo |
| `dominant_probability` | Probabilidad del estado dominante |
| `interaction_stability_sigma` | Concentración penalizada por demanda histórica |
| `demand_peak` | Pico estimado de demanda histórica |
| `request_id` | ID de trazabilidad |
| `input_hash` | Hash operacional |
| `content_fingerprint` | Fingerprint para reproducibilidad sin almacenar texto crudo |
| `skipped_turns` | Turnos no soportados omitidos por el analizador |

Advertencia interpretativa:

```text
omega_t mide concentración del belief state, no salud, bondad ni deseabilidad.
Un omega alto con dominant_state=Defensive puede indicar degradación confiada.
```

---

<a id="es-estructura"></a>

## Estructura del proyecto

```text
SAS/
├── app/
│   ├── main.py                      # FastAPI app, middleware, startup, readiness
│   ├── routers/                     # audit, diff, batch, interaction, public, billing, auth
│   ├── services/                    # detector, stores, auth, metrics, audit, interaction observability
│   ├── db/                          # SQLite: auth, usage, payments
│   └── middleware/                  # security headers, auth, rate limiting, validation logging
├── core/                            # scientific core: semantic_diff, TDA, NIG
├── docs/                            # architecture, API, benchmark, OTS proof, manifold model
├── scripts/                         # funnel_report.py and operational tooling
├── tests/                           # tests and benchmark runner
├── .github/workflows/               # smoke tests and CI
├── Dockerfile
├── docker-compose.yml
├── PRIVACY.md
├── README.md
└── requirements.txt
```

---

<a id="es-arquitectura"></a>

## Arquitectura

```text
SAS/
├── app/                          # Código principal de la API
│   ├── main.py                   # FastAPI app
│   ├── routers/                  # audit, diff, batch, interaction, public, billing
│   ├── services/                 # detector, stores, auth, metrics, audit, interaction observability
│   ├── db/                       # SQLite: auth, usage, payments
│   └── middleware/               # auth, validation, rate limiting, security headers
├── core/                         # scientific core: semantic_diff, TDA, NIG
├── scripts/                      # funnel_report.py and operational tooling
├── tests/benchmark_runner.py
├── docker-compose.yml
├── Dockerfile
├── PRIVACY.md
└── requirements.txt
```

### Componentes principales

| Componente | Función |
|---|---|
| TDA | Topological Data Analysis para comparación estructural semántica |
| ISI | Invariant Similarity Index |
| NIG | Numerical Invariance Guard |
| E9 | Detección de contradicción lógica |
| E10 | Grounding factual / detección de inventiva narrativa |
| E11 | Detección de inconsistencia temporal |
| E12 | Detección de cambio abrupto de tema |
| FastAPI | Capa API para audit, diff, chat, health y administración |

Para una explicación técnica más profunda, ver [docs/architecture.md](architecture.md).

---

<a id="es-benchmark"></a>

## Benchmark

Artefacto principal:

```text
docs/benchmark_complete_20260429_172647.json
```

Prueba OpenTimestamps:

```text
docs/benchmark_complete_20260429_172647.json.ots
```

Hash SHA-256 para trazabilidad:

```text
0713acbbf50e1a0054f545e5eb68078744f9c5a09d4bc370b5224bb81183a6fe
```

| Métrica | Resultado |
|---|---:|
| Pares evaluados | 2,000 |
| Pares con alucinación | 1,000 |
| Pares limpios | 1,000 |
| Accuracy | 98.80% |
| Precision | 100.00% |
| Recall | 97.60% |
| F1 score | 98.79% |
| κD | 0.56 |
| ISI promedio en alucinaciones | 0.072993 |
| ISI promedio en textos limpios | 1.000000 |

> Resultados específicos del dataset. Ver [benchmark.md](benchmark.md) para alcance, metodología y detalles de replicación.

### Matriz de confusión

|  | Alucinación real | Texto limpio real |
|---|---:|---:|
| Predicción: alucinación | TP = 976 | FP = 0 |
| Predicción: limpio | FN = 24 | TN = 1000 |

Para ejecutar el benchmark:

```bash
python tests/benchmark_runner.py
```

---

<a id="es-planes"></a>

## Planes y precios

SAS es open source bajo **GPL-3.0 + Durante Invariance License**.

Los planes siguientes corresponden al **servicio API alojado**, no a una modificación ni relajación de la licencia del código fuente.

Cualquier persona puede autoalojar su propia instancia de SAS bajo los términos de GPL-3.0 + Durante Invariance License.

| Plan | Uso / Características | Precio |
| :--- | :--- | :--- |
| **SAS Free** | 50 requests/día. API Key automática. Ideal para pruebas, desarrollo individual y evaluación técnica inicial. | **Gratis** |
| **SAS Developer / Pro** | 10.000 requests/mes. API Key. Acceso a la API pública alojada. Soporte básico por email. | **99 USD/mes** |
| **SAS Team** | 50.000 requests/mes. API Key. Acceso alojado para equipos. Soporte prioritario. | **299 USD/mes** |
| **SAS Enterprise Cloud** | Volumen alto o paquete personalizado. Soporte directo. Integración privada. SLA según acuerdo comercial. | **Desde 1.500 USD/mes** |
| **SAS On-Premise License** | Despliegue privado en infraestructura del cliente. Licencia comercial. Integración interna y soporte de implementación. | **Desde 15.000 USD/año** |
| **Piloto técnico** | Auditoría inicial, integración guiada, informe técnico y validación sobre casos de uso del cliente. | **1.500–3.000 USD, pago único** |

> **Nota de licencia:** el código sigue publicado bajo **GPL-3.0 + Durante Invariance License**. Los planes anteriores corresponden al uso del servicio alojado, soporte comercial, integración privada o licenciamiento empresarial.

📧 **Consultas Enterprise, On-Premise o pilots:** duranteg2@gmail.com

---

<a id="es-inicio-rapido"></a>

## Inicio rápido

### API pública alojada

**[https://sas-api.onrender.com](https://sas-api.onrender.com)**

Health check:

```bash
curl https://sas-api.onrender.com/health
```

### Demo pública — sin API key

Probá el motor real sin registrarte:

```bash
curl -X POST https://sas-api.onrender.com/public/demo/audit \
  -H "Content-Type: application/json" \
  -d '{
    "source": "The Eiffel Tower is located in Paris, France.",
    "response": "The Eiffel Tower is located in Berlin, Germany."
  }'
```

O desde la landing interactiva: [sas-landing/#demo](https://leesintheblindmonk1999.github.io/sas-landing/#demo)

### Opción 1: Docker / autoalojamiento

```bash
git clone https://github.com/Leesintheblindmonk1999/SAS.git
cd SAS
docker compose up --build
```

### Opción 2: instalación local con Python

```bash
git clone https://github.com/Leesintheblindmonk1999/SAS.git
cd SAS
python -m venv .venv
source .venv/bin/activate  # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

<a id="es-configuracion"></a>

## Configuración

Crear un archivo local `.env`:

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

No subir archivos `.env` a repositorios públicos.

---

<a id="es-auth"></a>

## Autenticación API y obtención de keys

### API key Free — automática

Solicitá tu API key gratuita directamente desde el endpoint público:

```bash
curl -X POST https://sas-api.onrender.com/public/request-key \
  -H "Content-Type: application/json" \
  -d '{"email": "your@email.com", "name": "Tu nombre"}'
```

Recibirás tu API key por email de forma automática. Sin intervención manual.

Límite: 1 key Free por email por día.

### Plan Pro — pago automático

Suscripción Pro disponible vía:

- **Polar:** [https://polar.sh](https://polar.sh) (tarjetas internacionales)
- **Mercado Pago:** disponible para LATAM

Al confirmar el pago, tu API key Pro se genera y envía automáticamente por email.

### Autoalojamiento

Si estás ejecutando tu propia instancia, generá una API key vía admin:

```bash
curl -X POST http://localhost:8000/admin/generate-key \
  -H "X-Admin-Secret: change-this-admin-secret"
```

### Uso de la API key

```bash
curl -X POST https://sas-api.onrender.com/v1/diff \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sas_xxxxxxxxxxxxxxxxxxxxx" \
  -d '{
    "text_a": "Python is a programming language.",
    "text_b": "A python is a snake.",
    "experimental": true
  }'
```

### Verificar tu plan

```bash
curl https://sas-api.onrender.com/v1/whoami \
  -H "X-API-Key: sas_xxxxxxxxxxxxxxxxxxxxx"
```

```json
{
  "plan": "free",
  "active": true,
  "daily_limit": 50,
  "email": "yo***@gmail.com"
}
```

---

<a id="es-ejemplos-api"></a>

## Ejemplos de API

### Health check

```bash
curl https://sas-api.onrender.com/health
```

### Auditar una respuesta generada

```bash
curl -X POST https://sas-api.onrender.com/v1/audit \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sas_xxxxxxxxxxxxxxxxxxxxx" \
  -d '{
    "text": "The Eiffel Tower is located in Berlin, Germany.",
    "experimental": true
  }'
```

### Comparar dos textos (endpoint forense principal)

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

### Chat endpoint

```bash
curl -X POST https://sas-api.onrender.com/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sas_xxxxxxxxxxxxxxxxxxxxx" \
  -d '{"message": "Explain what κD means in SAS."}'
```


### Batch audit

```bash
curl -X POST https://sas-api.onrender.com/v1/batch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sas_xxxxxxxxxxxxxxxxxxxxx" \
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

### Interaction stability experimental

```bash
curl -X POST https://sas-api.onrender.com/v1/interaction/stability \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sas_xxxxxxxxxxxxxxxxxxxxx" \
  -d '{
    "conversation": [
      {"role":"user","content":"Necesito esto urgente, es para ayer."},
      {"role":"assistant","content":"Entendido, lo proceso."}
    ]
  }'
```

Campos esperados:

```text
status
trajectory
summary
request_id
executed_at
input_hash
content_fingerprint
skipped_turns
```

### Stats públicas de interaction stability

```bash
curl "https://sas-api.onrender.com/public/interaction/stats?days=7"
```

Estas stats son agregadas. No publican texto crudo, API keys, hashes de API keys, request IDs, input hashes ni fingerprints.

### Endpoints públicos (sin key)

```bash
curl https://sas-api.onrender.com/public/stats
curl https://sas-api.onrender.com/public/activity?limit=10
curl "https://sas-api.onrender.com/public/interaction/stats?days=7"
curl https://sas-api.onrender.com/readyz
```

---

<a id="es-modulos"></a>

## Control de módulos

```env
MODULES_ENABLED=E9,E10,E11,E12
```

| Módulo | Nombre | Función |
|---|---|---|
| E9 | Logical Contradiction | Detecta inversión lógica o contradicción interna |
| E10 | Fact Grounding | Detecta claims no soportados cuando hay grounding local disponible |
| E11 | Temporal Inconsistency | Detecta secuencias temporales incompatibles |
| E12 | Topic Shift | Detecta cambios abruptos de tema sin señales de transición |

---


---

<a id="es-privacidad-observabilidad"></a>

## Privacidad y observabilidad

SAS almacena metadata operativa para confiabilidad, prevención de abuso, reproducibilidad e investigación agregada.

Para `/v1/interaction/stability`, SAS puede almacenar:

- `request_id`;
- timestamp;
- hash corto de API key;
- bucket de usuario/plan;
- cantidad de turnos;
- cantidad de turnos del asistente;
- estado dominante final;
- `omega_t` final;
- `sigma` final;
- pico de demanda;
- flags de umbral/incertidumbre;
- `input_hash`;
- `content_fingerprint`;
- latencia.

SAS **no almacena texto crudo de conversación** en el store de observabilidad de interacción.

Las stats públicas solo exponen agregados. No exponen:

- texto crudo;
- API keys;
- hashes de API keys;
- request IDs;
- input hashes;
- content fingerprints;
- filas por usuario.

Ver: [Privacy and Observability](../PRIVACY.md)

<a id="es-zenodo"></a>

## Zenodo y registro

- **Zenodo DOI principal SAS:** [10.5281/zenodo.19702379](https://doi.org/10.5281/zenodo.19702379)
- **Zenodo DOI interaction stability:** `10.5281/zenodo.20335612`
- **Registro TAD:** `EX-2026-18792778`
- **Autor:** Gonzalo Emir Durante
- **Licencia:** [GPL-3.0 + Durante Invariance License](../LICENSE.md)
- **API alojada:** [https://sas-api.onrender.com](https://sas-api.onrender.com)
- **Cliente PyPI:** [https://pypi.org/project/sas-client/](https://pypi.org/project/sas-client/)

---

<a id="es-citacion"></a>

## Citación

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

<a id="es-licencia"></a>

## Licencia

```text
GPL-3.0 + Durante Invariance License
```

Ver [LICENSE.md](../LICENSE.md) para el texto completo.

---

<a id="es-desarrollo"></a>

## Desarrollo

```bash
pytest
python tests/benchmark_runner.py
uvicorn app.main:app --reload
```

---

<a id="es-seguridad"></a>

## Notas de seguridad

- No subir archivos `.env`.
- Rotar `ADMIN_SECRET` antes de despliegue.
- Usar HTTPS en producción.
- Restringir CORS en producción.
- Mantener API keys privadas.

Para reportes de vulnerabilidad, ver [SECURITY.md](../SECURITY.md).

---

<a id="es-alcance-y-limitaciones"></a>

## Alcance y limitaciones

SAS está diseñado para auditoría estructural de coherencia y detección de señales de alucinación. No garantiza verificación factual universal.

Limitaciones conocidas:

- El grounding factual depende de fuentes locales disponibles.
- La detección de cambio de tema es conservadora para reducir falsos positivos.
- Los resultados deben interpretarse como evidencia técnica, no como certificación legal.
- El rendimiento puede variar en dominios, idiomas y datasets no representados en el benchmark actual.
- Interaction stability produce constructos de modelo, no diagnósticos psicológicos ni determinaciones legales.
- `omega_t` mide concentración del belief state, no bondad ni salud del estado.
- Las stats públicas son agregadas y no deben interpretarse como identificación de usuarios.

---


---

<a id="es-roadmap"></a>

## Roadmap

### Corto plazo

- Mantener smoke tests verdes.
- Monitorear `funnel_report.py`.
- Mantener `/public/interaction/stats` estable.
- Mejorar documentación API y ejemplos de integración.

### Producto

- Node.js / TypeScript SDK.
- Dashboard mínimo basado en métricas públicas agregadas.
- CLI batch por archivo.
- Reportes exportables con hash, timestamp y request ID.

### Científico

- Snapshot empírico de interaction stability al alcanzar volumen suficiente.
- Calibración de parámetros de interaction stability.
- Benchmark v2 con corpus narrativo y multilingüe.
- Paquete de replicación externa.

<a id="es-autor"></a>

## Autor

**Gonzalo Emir Durante**

- Repositorio: https://github.com/Leesintheblindmonk1999/SAS
- API: https://sas-api.onrender.com
- DOI: https://doi.org/10.5281/zenodo.19702379
- Contacto comercial: duranteg2@gmail.com

---

<a id="en"></a>

# English

**SAS - Symbiotic Autoprotection System** is an open-source API framework for detecting structural hallucinations in generative AI outputs.

SAS evaluates whether a generated response preserves semantic structure, logical consistency, numerical integrity, and factual-coherence signals relative to a source text or prompt. It combines topological data analysis, numerical invariance checks, and modular hallucination probes into a FastAPI-based audit system.

The system is authored by **Gonzalo Emir Durante** and published as an open technical standard candidate for structural coherence auditing in AI systems.

---

<a id="en-live-api"></a>

## Live Public API

**[https://sas-api.onrender.com](https://sas-api.onrender.com)**

```bash
curl https://sas-api.onrender.com/health
```

FastAPI interactive documentation: https://sas-api.onrender.com/docs

---

<a id="en-current-operational-state"></a>

## Current Operational State

SAS currently operates as a public API with authentication, quotas, persistent rate limiting, observability, smoke tests, and SQLite-backed operational stores.

Recently validated surfaces:

```text
/health                               -> ok
/readyz                               -> ready
/public/stats                         -> ok
/public/activity                      -> ok
/public/interaction/stats             -> ok
/v1/diff                              -> active
/v1/audit                             -> active
/v1/batch                             -> active
/v1/interaction/stability             -> active behind feature flag + API key
```

Databases checked by `/readyz`:

| Store | Status | Use |
|---|---|---|
| `auth.db` | active | users, API keys, quotas |
| `metrics.db` | active | request metrics and funnel reporting |
| `audit.db` | active | audit trail and validation errors |
| `rate_limit.db` | active | persistent rate-limit events |
| `interaction.db` | active | aggregate interaction-stability observability |

Main active surfaces:

| Line | Endpoints |
|---|---|
| Structural Coherence Auditing | `/v1/diff`, `/v1/audit`, `/v1/batch`, `/public/demo/audit` |
| Temporal Interaction Auditing | `/v1/interaction/stability`, `/v1/interaction/stability/example`, `/public/interaction/stats` |
| Onboarding | `/public/request-key`, `/v1/whoami` |
| Public observability | `/public/stats`, `/public/activity`, `/public/interaction/stats` |
| System | `/health`, `/readyz`, `/integrity`, `/robots.txt` |
| Hosted billing | Polar + Mercado Pago checkout/webhooks |

---

<a id="en-python-client"></a>

## Official Python Client

```bash
pip install sas-client
```

```python
from sas_client import SASClient

client = SASClient(api_key="YOUR_API_KEY")

result = client.diff(
    text_a="Python is a programming language.",
    text_b="A python is a snake."
)

print(result["isi"])
print(result["verdict"])
```

CLI:

```bash
sas health
sas public-stats
sas --api-key YOUR_API_KEY diff "Python is a programming language." "A python is a snake."
```

---

<a id="en-documentation"></a>

## Documentation

| Document | Description |
|---|---|
| [Main README](../README.md) | Project overview, public API, capabilities and roadmap |
| [Privacy and Observability](../PRIVACY.md) | Data handling, hashes, fingerprints and public stats |
| [API Reference](api.md) | Endpoints, auth, examples, errors and client guidance |
| [Architecture Overview](architecture.md) | High-level design, detection pipeline and data flow |
| [Manifold Model](manifold.md) | ISI, κD, TDA, NIG, SourceTargetGuard and E9-E12 |
| [Benchmark](benchmark.md) | Methodology, limitations and replication guidance |
| [Billing](billing.md) | Free/Pro flow, Polar, Mercado Pago, quotas and webhooks |
| [Security Notes](security.md) | API keys, rate limits, validation, privacy and operational security |
| [Benchmark JSON](benchmark_complete_20260429_172647.json) | Full benchmark output |
| [Benchmark OTS Proof](benchmark_complete_20260429_172647.json.ots) | OpenTimestamps proof |
| [Security Policy](../SECURITY.md) | Vulnerability reporting and responsible disclosure |
| [Contributing Guide](../CONTRIBUTING.md) | Development setup, pull requests and contribution rules |
| [Code of Conduct](../CODE_OF_CONDUCT.md) | Community standards |
| [License](../LICENSE.md) | GPL-3.0 + Durante Invariance License |

---

## 🌐 Public Manifesto / SAS Standard

**Official Landing Page:** [sas-landing](https://leesintheblindmonk1999.github.io/sas-landing/)

---

<a id="en-problem"></a>

## Problem

Generative AI systems can produce fluent outputs that are structurally inconsistent, logically inverted, numerically wrong, or semantically disconnected from the input. Traditional similarity metrics often fail to detect these cases.

SAS addresses this by treating hallucination detection as a **structural coherence audit** problem.

---

<a id="en-kappa"></a>

## Core Concept: κD = 0.56

```text
ISI >= κD  ->  structurally coherent
ISI <  κD  ->  potential manifold rupture / hallucination signal
```

κD = 0.56, the **Durante Constant**, is the critical coherence threshold in the SAS pipeline.

---

<a id="en-technical-lines"></a>

## Current technical lines

### 1. Structural Coherence Auditing

Endpoints:

```text
POST /public/demo/audit
POST /v1/diff
POST /v1/audit
POST /v1/batch
```

Purpose:

- compare source text against generated response;
- detect structural semantic rupture;
- detect mutations of dates, locations, entities, quantities or critical claims;
- produce `isi`, `verdict`, `fired_modules` and `manipulation_alert`.

### 2. Temporal Interaction Auditing

Experimental endpoints:

```text
GET  /v1/interaction/stability/example
POST /v1/interaction/stability
GET  /public/interaction/stats
```

Research line:

```text
A Control-Theoretic Model for Stochastic Interaction under Hidden-State
Uncertainty and Demand-Sensitive Response Degradation
DOI: 10.5281/zenodo.20335612
```

Hidden-state model constructs:

```text
Open · Ambivalent · Saturated · Avoidant · Defensive
```

Key fields:

| Field | Meaning |
|---|---|
| `omega_t` | Normalized belief-state concentration |
| `belief_coherence_chi` | Backward-compatible alias of `omega_t` |
| `dominant_state` | Most probable hidden-state construct |
| `dominant_probability` | Probability of dominant state |
| `interaction_stability_sigma` | Belief concentration penalized by historical demand |
| `demand_peak` | Peak historical demand estimate |
| `request_id` | Traceability ID |
| `input_hash` | Operational hash |
| `content_fingerprint` | Reproducibility fingerprint without storing raw text |
| `skipped_turns` | Unsupported turns skipped by the analyzer |

Interpretation warning:

```text
omega_t measures belief-state concentration, not desirability.
High omega_t with dominant_state=Defensive can mean confident degradation.
```

---

<a id="en-benchmark"></a>

## Benchmark Results

| Metric | Result |
|---|---:|
| Evaluated pairs | 2,000 |
| Accuracy | 98.80% |
| Precision | 100.00% |
| Recall | 97.60% |
| F1 score | 98.79% |
| False Positives | 0 |
| κD | 0.56 |

> Results are dataset-specific. See [benchmark.md](benchmark.md) for scope and replication details.

SHA-256: `0713acbbf50e1a0054f545e5eb68078744f9c5a09d4bc370b5224bb81183a6fe`

---

<a id="en-pricing"></a>

## Plans and Pricing

SAS is open source under **GPL-3.0 + Durante Invariance License**. The plans below refer to the **hosted API service**.

| Plan | Usage / Features | Price |
| :--- | :--- | :--- |
| **SAS Free** | 50 requests/day. Automatic API Key. Ideal for testing and evaluation. | **Free** |
| **SAS Developer / Pro** | 10,000 requests/month. API Key. Hosted API access. Basic email support. | **USD 99/month** |
| **SAS Team** | 50,000 requests/month. Hosted API access for teams. Priority support. | **USD 299/month** |
| **SAS Enterprise Cloud** | High-volume or custom package. Direct support. Private integration. SLA by agreement. | **From USD 1,500/month** |
| **SAS On-Premise License** | Private deployment on customer infrastructure. Commercial license. | **From USD 15,000/year** |
| **Technical Pilot** | Initial audit, guided integration, technical report, and use-case validation. | **USD 1,500–3,000 one-time** |

📧 **Enterprise, On-Premise, or pilot inquiries:** duranteg2@gmail.com

---

<a id="en-quick-start"></a>

## Quick Start

### Public demo — no API key required

```bash
curl -X POST https://sas-api.onrender.com/public/demo/audit \
  -H "Content-Type: application/json" \
  -d '{
    "source": "The Eiffel Tower is located in Paris, France.",
    "response": "The Eiffel Tower is located in Berlin, Germany."
  }'
```

Or try the interactive demo: [sas-landing/#demo](https://leesintheblindmonk1999.github.io/sas-landing/#demo)

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
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---


---

<a id="en-configuration"></a>

## Configuration

Example `.env`:

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

Enable interaction stability:

```env
ENABLE_INTERACTION_STABILITY=true
```

Do not commit `.env` files.

<a id="en-auth"></a>

## API Authentication and Key Acquisition

### Free API key — automatic

Request your free API key directly:

```bash
curl -X POST https://sas-api.onrender.com/public/request-key \
  -H "Content-Type: application/json" \
  -d '{"email": "your@email.com", "name": "Your Name"}'
```

Your API key will be delivered automatically by email. No manual intervention required.

Limit: 1 Free key per email per day.

### Pro plan — automatic payment

Pro subscriptions available via:

- **Polar:** [https://polar.sh](https://polar.sh) (international cards)
- **Mercado Pago:** available for LATAM

Your Pro API key is generated and delivered by email automatically upon payment confirmation.

### Self-hosting

```bash
curl -X POST http://localhost:8000/admin/generate-key \
  -H "X-Admin-Secret: change-this-admin-secret"
```

### Using your API key

```bash
curl -X POST https://sas-api.onrender.com/v1/diff \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sas_xxxxxxxxxxxxxxxxxxxxx" \
  -d '{
    "text_a": "Python is a programming language.",
    "text_b": "A python is a snake.",
    "experimental": true
  }'
```

### Check your plan

```bash
curl https://sas-api.onrender.com/v1/whoami \
  -H "X-API-Key: sas_xxxxxxxxxxxxxxxxxxxxx"
```

```json
{
  "plan": "free",
  "active": true,
  "daily_limit": 50,
  "email": "yo***@gmail.com"
}
```

---

<a id="en-api-examples"></a>

## API Examples

### Health check

```bash
curl https://sas-api.onrender.com/health
```

### Audit a generated response

```bash
curl -X POST https://sas-api.onrender.com/v1/audit \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sas_xxxxxxxxxxxxxxxxxxxxx" \
  -d '{"text": "The Eiffel Tower is located in Berlin, Germany.", "experimental": true}'
```

### Compare two texts (primary forensic endpoint)

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


### Batch audit

```bash
curl -X POST https://sas-api.onrender.com/v1/batch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sas_xxxxxxxxxxxxxxxxxxxxx" \
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

### Experimental interaction stability

```bash
curl -X POST https://sas-api.onrender.com/v1/interaction/stability \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sas_xxxxxxxxxxxxxxxxxxxxx" \
  -d '{
    "conversation": [
      {"role":"user","content":"Necesito esto urgente, es para ayer."},
      {"role":"assistant","content":"Entendido, lo proceso."}
    ]
  }'
```

Expected fields:

```text
status
trajectory
summary
request_id
executed_at
input_hash
content_fingerprint
skipped_turns
```

### Public interaction stats

```bash
curl "https://sas-api.onrender.com/public/interaction/stats?days=7"
```

These stats are aggregate-only. They do not publish raw text, API keys, API-key hashes, request IDs, input hashes or fingerprints.

### Public endpoints (no key required)

```bash
curl https://sas-api.onrender.com/public/stats
curl "https://sas-api.onrender.com/public/activity?limit=10"
curl "https://sas-api.onrender.com/public/interaction/stats?days=7"
curl https://sas-api.onrender.com/readyz
```

---

<a id="en-modules"></a>

## Module Controls

```env
MODULES_ENABLED=E9,E10,E11,E12
```

| Module | Name | Function |
|---|---|---|
| E9 | Logical Contradiction | Detects internal logical inversion or contradiction |
| E10 | Fact Grounding | Detects unsupported claims when local grounding is available |
| E11 | Temporal Inconsistency | Detects incompatible temporal sequences |
| E12 | Topic Shift | Detects abrupt topic changes without transition signals |

---


---

<a id="en-privacy-observability"></a>

## Privacy and observability

SAS stores operational metadata for reliability, abuse prevention, reproducibility and aggregate research.

For `/v1/interaction/stability`, SAS may store:

- `request_id`;
- timestamp;
- short hashed API-key identifier;
- user/plan bucket;
- turn counts;
- final dominant state;
- final `omega_t`;
- final `sigma`;
- demand peak;
- threshold/uncertainty flags;
- `input_hash`;
- `content_fingerprint`;
- latency.

SAS does **not** store raw conversation text in the interaction observability store.

Public stats expose aggregate data only. They do not expose:

- raw text;
- API keys;
- API-key hashes;
- request IDs;
- input hashes;
- content fingerprints;
- per-user rows.

See: [Privacy and Observability](../PRIVACY.md)

<a id="en-zenodo"></a>

## Zenodo and Registration

- **Main SAS DOI:** [10.5281/zenodo.19702379](https://doi.org/10.5281/zenodo.19702379)
- **Interaction stability DOI:** `10.5281/zenodo.20335612`
- **TAD Registry:** `EX-2026-18792778`
- **Author:** Gonzalo Emir Durante
- **License:** [GPL-3.0 + Durante Invariance License](../LICENSE.md)
- **Hosted API:** [https://sas-api.onrender.com](https://sas-api.onrender.com)
- **PyPI Client:** [https://pypi.org/project/sas-client/](https://pypi.org/project/sas-client/)

---

<a id="en-citation"></a>

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

<a id="en-license"></a>

## License

```text
GPL-3.0 + Durante Invariance License
```

See [LICENSE.md](../LICENSE.md) for the full text.

---

<a id="en-development"></a>

## Development

```bash
pytest
python tests/benchmark_runner.py
uvicorn app.main:app --reload
```

---


---

<a id="en-operations"></a>

## Operations and reporting

```bash
python scripts/funnel_report.py --hours 24 --show-recent
```

Or:

```bash
python scripts/funnel_report.py --days 3 --show-recent --json
```

The report separates infrastructure, discovery, trial, conversion, authenticated usage, validation errors, audit events, rate-limit events and interaction-stability usage.

<a id="en-security"></a>

## Security Notes

- Do not commit `.env` files.
- Rotate `ADMIN_SECRET` before deployment.
- Use HTTPS in production.
- Restrict CORS origins in production.
- Keep API keys private.

For vulnerability reports, see [SECURITY.md](../SECURITY.md).

---

<a id="en-scope-and-limitations"></a>

## Scope and Limitations

SAS is designed for structural coherence auditing and hallucination signal detection. It does not guarantee universal factual verification.

Known limitations:

- Factual grounding depends on available local knowledge sources.
- Topic-shift detection is conservative to reduce false positives.
- Results should be interpreted as technical evidence, not as legal certification.
- Benchmark performance may vary across domains and languages not represented in the current evaluation.
- Interaction stability outputs are model constructs, not psychological diagnoses or legal determinations.
- `omega_t` measures belief-state concentration, not state desirability.
- Public stats are aggregate and must not be interpreted as user identification.

---


---

<a id="en-roadmap"></a>

## Roadmap

### Short term

- Keep smoke tests green.
- Monitor `funnel_report.py`.
- Keep `/public/interaction/stats` stable.
- Improve API documentation and developer examples.

### Product

- Node.js / TypeScript SDK.
- Minimal dashboard based on public aggregate metrics.
- CLI batch by file.
- Exportable reports with hash, timestamp and request ID.

### Scientific

- Empirical interaction-stability snapshot after enough real analyses.
- Calibration of interaction-stability parameters.
- Benchmark v2 with narrative and multilingual corpora.
- External replication package.

<a id="en-author"></a>

## Author

**Gonzalo Emir Durante**

- Repository: https://github.com/Leesintheblindmonk1999/SAS
- API: https://sas-api.onrender.com
- DOI: https://doi.org/10.5281/zenodo.19702379
- Commercial contact: duranteg2@gmail.com
