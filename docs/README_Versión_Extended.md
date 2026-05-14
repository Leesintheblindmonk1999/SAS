# SAS - Symbiotic Autoprotection System

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19702379.svg)](https://doi.org/10.5281/zenodo.19702379)
[![Landing Page](https://img.shields.io/badge/🌐-Landing_Page-0a0e17?style=flat&logo=github)](https://leesintheblindmonk1999.github.io/sas-landing/)
[![API Online](https://img.shields.io/badge/API-online-brightgreen)](https://sas-api.onrender.com)
[![PyPI](https://img.shields.io/pypi/v/sas-client?label=sas-client&color=blue)](https://pypi.org/project/sas-client/)
[![License](https://img.shields.io/badge/license-GPL--3.0%20%2B%20Durante%20Invariance-blue)](LICENSE.md)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](requirements.txt)
[![API](https://img.shields.io/badge/API-FastAPI-009688)](https://sas-api.onrender.com/docs)
[![Status](https://img.shields.io/badge/status-research%20alpha-orange)](#es-alcance-y-limitaciones)
[![Benchmark](https://img.shields.io/badge/benchmark-98.8%25%20accuracy-brightgreen)](docs/benchmark_complete_20260429_172647.json)
[![OTS Proof](https://img.shields.io/badge/OpenTimestamps-proof-blueviolet)](docs/benchmark_complete_20260429_172647.json.ots)
[![Security](https://img.shields.io/badge/security-policy-lightgrey)](SECURITY.md)
[![Contributing](https://img.shields.io/badge/contributions-welcome-brightgreen)](CONTRIBUTING.md)
[![Smoke Test](https://github.com/Leesintheblindmonk1999/SAS/actions/workflows/smoke_test.yml/badge.svg)](https://github.com/Leesintheblindmonk1999/SAS/actions/workflows/smoke_test.yml)

<!-- SAS-LIVE-METRICS:START -->
## Live Operational Snapshot / Estado Operativo Vivo

_Last automated update / Última actualización automática:_ `2026-05-12T19:41:56+00:00`

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
| [Security Policy](SECURITY.md) | Reporte de vulnerabilidades, notas de seguridad y divulgación responsable |
| [Contributing Guide](CONTRIBUTING.md) | Setup de desarrollo, pull requests, testing y reglas de contribución |
| [Code of Conduct](CODE_OF_CONDUCT.md) | Estándares comunitarios y política de convivencia |
| [Architecture Overview](docs/architecture.md) | Diseño de alto nivel, pipeline de detección, módulos y flujo de datos |
| [Benchmark JSON](docs/benchmark_complete_20260429_172647.json) | Resultado completo del benchmark |
| [Benchmark OTS Proof](docs/benchmark_complete_20260429_172647.json.ots) | Prueba OpenTimestamps del benchmark |
| [Bug Report Template](.github/ISSUE_TEMPLATE/bug_report.md) | Template de GitHub Issues para bugs |
| [Feature Request Template](.github/ISSUE_TEMPLATE/feature_request.md) | Template de GitHub Issues para mejoras |
| [License](LICENSE.md) | GPL-3.0 + Durante Invariance License |

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

<a id="es-estructura"></a>

## Estructura del proyecto

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
│   ├── benchmark_complete_20260429_172647.json
│   └── benchmark_complete_20260429_172647.json.ots
├── src/
├── tests/
├── docker-compose.yml
└── requirements.txt
```

---

<a id="es-arquitectura"></a>

## Arquitectura

```text
SAS/
├── app/                          # Código principal de la API
│   ├── main.py                   # FastAPI app
│   ├── routers/                  # Endpoints: audit, diff, chat, demo, billing
│   ├── services/                 # Motor core: TDA + NIG + módulos E9-E12
│   ├── db/                       # SQLite: auth_store, rate limit
│   └── middleware/               # Auth, rate limiting
├── tests/benchmark_runner.py
├── docker-compose.yml
├── Dockerfile
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

Para una explicación técnica más profunda, ver [docs/architecture.md](docs/architecture.md).

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

### Endpoints públicos (sin key)

```bash
curl https://sas-api.onrender.com/public/stats
curl https://sas-api.onrender.com/public/activity?limit=10
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

<a id="es-zenodo"></a>

## Zenodo y registro

- **Zenodo DOI:** [10.5281/zenodo.19702379](https://doi.org/10.5281/zenodo.19702379)
- **Registro TAD:** `EX-2026-18792778`
- **Autor:** Gonzalo Emir Durante
- **Licencia:** [GPL-3.0 + Durante Invariance License](LICENSE.md)
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

Ver [LICENSE.md](LICENSE.md) para el texto completo.

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

Para reportes de vulnerabilidad, ver [SECURITY.md](SECURITY.md).

---

<a id="es-alcance-y-limitaciones"></a>

## Alcance y limitaciones

SAS está diseñado para auditoría estructural de coherencia y detección de señales de alucinación. No garantiza verificación factual universal.

Limitaciones conocidas:

- El grounding factual depende de fuentes locales disponibles.
- La detección de cambio de tema es conservadora para reducir falsos positivos.
- Los resultados deben interpretarse como evidencia técnica, no como certificación legal.
- El rendimiento puede variar en dominios, idiomas y datasets no representados en el benchmark actual.

---

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
| [Security Policy](SECURITY.md) | Vulnerability reporting and responsible disclosure |
| [Contributing Guide](CONTRIBUTING.md) | Development setup, pull requests, and contribution rules |
| [Code of Conduct](CODE_OF_CONDUCT.md) | Community standards |
| [Architecture Overview](docs/architecture.md) | Detection pipeline, modules, and data flow |
| [Benchmark JSON](docs/benchmark_complete_20260429_172647.json) | Full benchmark output |
| [Benchmark OTS Proof](docs/benchmark_complete_20260429_172647.json.ots) | OpenTimestamps proof |
| [License](LICENSE.md) | GPL-3.0 + Durante Invariance License |

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

SHA-256: `0713acbbf50e1a0054f545e5eb68078744f9c5a09d4bc370b5224bb81183a6fe`

---

<a id="en-pricing"></a>

## Plans and Pricing

SAS is open source under **GPL-3.0 + Durante Invariance License**. The plans below refer to the **hosted API service**.

| Plan | Usage / Features | Price |
| :--- | :--- | :--- |
| **SAS Free** | 50 requests/day. Automatic API Key. Ideal for testing and evaluation. | **Free** |
| **SAS Developer / Pro** | 10,000 requests/month. API Key. Hosted API access. Basic email support. | **USD 99/month** |
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

### Public endpoints (no key required)

```bash
curl https://sas-api.onrender.com/public/stats
curl "https://sas-api.onrender.com/public/activity?limit=10"
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

<a id="en-zenodo"></a>

## Zenodo and Registration

- **Zenodo DOI:** [10.5281/zenodo.19702379](https://doi.org/10.5281/zenodo.19702379)
- **TAD Registry:** `EX-2026-18792778`
- **Author:** Gonzalo Emir Durante
- **License:** [GPL-3.0 + Durante Invariance License](LICENSE.md)
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

See [LICENSE.md](LICENSE.md) for the full text.

---

<a id="en-development"></a>

## Development

```bash
pytest
python tests/benchmark_runner.py
uvicorn app.main:app --reload
```

---

<a id="en-security"></a>

## Security Notes

- Do not commit `.env` files.
- Rotate `ADMIN_SECRET` before deployment.
- Use HTTPS in production.
- Restrict CORS origins in production.
- Keep API keys private.

For vulnerability reports, see [SECURITY.md](SECURITY.md).

---

<a id="en-scope-and-limitations"></a>

## Scope and Limitations

SAS is designed for structural coherence auditing and hallucination signal detection. It does not guarantee universal factual verification.

Known limitations:

- Factual grounding depends on available local knowledge sources.
- Topic-shift detection is conservative to reduce false positives.
- Results should be interpreted as technical evidence, not as legal certification.
- Benchmark performance may vary across domains and languages not represented in the current evaluation.

---

<a id="en-author"></a>

## Author

**Gonzalo Emir Durante**

- Repository: https://github.com/Leesintheblindmonk1999/SAS
- API: https://sas-api.onrender.com
- DOI: https://doi.org/10.5281/zenodo.19702379
- Commercial contact: duranteg2@gmail.com
