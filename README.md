# SAS - Symbiotic Autoprotection System

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19689077.svg)](https://doi.org/10.5281/zenodo.19689077)
[![Landing Page](https://img.shields.io/badge/🌐-Landing_Page-0a0e17?style=flat&logo=github)](https://leesintheblindmonk1999.github.io/sas-landing/)
[![API Online](https://img.shields.io/badge/API-online-brightgreen)](https://sas-api.onrender.com)
[![License](https://img.shields.io/badge/license-GPL--3.0%20%2B%20Durante%20Invariance-blue)](LICENSE.md)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](requirements.txt)
[![API](https://img.shields.io/badge/API-FastAPI-009688)](https://sas-api.onrender.com/docs)
[![Status](https://img.shields.io/badge/status-research%20alpha-orange)](#es-alcance-y-limitaciones)
[![Benchmark](https://img.shields.io/badge/benchmark-98.8%25%20accuracy-brightgreen)](docs/benchmark_complete_20260429_172647.json)
[![OTS Proof](https://img.shields.io/badge/OpenTimestamps-proof-blueviolet)](docs/benchmark_complete_20260429_172647.json.ots)
[![Security](https://img.shields.io/badge/security-policy-lightgrey)](SECURITY.md)
[![Contributing](https://img.shields.io/badge/contributions-welcome-brightgreen)](CONTRIBUTING.md)
[![Smoke Test](https://github.com/Leesintheblindmonk1999/SAS/actions/workflows/smoke_test.yml/badge.svg)](https://github.com/Leesintheblindmonk1999/SAS/actions/workflows/smoke_test.yml)


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

Dentro del framework, κD representa el punto operativo donde el ruido semántico cae por debajo de la coherencia estructural y el significado se vuelve suficientemente estable como para considerarse preservado.

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
├── app/                   # Código principal de la API
│   ├── main.py            # FastAPI app: /v1/audit, /v1/diff, /v1/chat, /health
│   └── services/          # Motor core: TDA + NIG + módulos E9-E12
├── tests/benchmark_runner.py # Script de benchmark
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

### Nota sobre el benchmark

Este benchmark incluye ejemplos con alucinación y ejemplos limpios. Las métricas de accuracy, precision, recall y F1 se derivan de la matriz de confusión anterior.

El resultado actual muestra **0 falsos positivos** en el subconjunto limpio evaluado y recall alto sobre el subconjunto con alucinaciones. Esto posiciona a SAS como un detector estructural orientado a precisión.

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
| **SAS Free** | 50 requests/día. Autenticación por API Key. Ideal para desarrollo, pruebas y evaluación. | **Gratis** |
| **SAS Pro** | 10,000 requests/mes. Sin límite de concurrencia. Soporte prioritario por email. | **49 USD/mes** o **490 USD/año** |
| **SAS Enterprise** | Requests ilimitadas o paquete personalizado. SLA garantizado 99.9%. Licencia On-Premise opcional. Soporte 24/7. | **Cotización** — desde **499 USD/mes** |

📧 **¿Interesado en una licencia Enterprise o necesitas un plan a medida?** Contacto: **duranteg2@gmail.com**

### Posicionamiento comercial

SAS está diseñado para auditoría de alucinaciones orientada a precisión. En el benchmark actual, SAS reporta **98.8% de accuracy**, **100% de precision** y **97.6% de recall** sobre 2,000 pares evaluados.

No pagas por una similitud vaga. Pagas por detección estructural auditable, métricas claras, artefactos trazables y evidencia reproducible.

---

<a id="es-inicio-rapido"></a>

## Inicio rápido

### API pública alojada

La API pública de referencia ya está en funcionamiento:

**[https://sas-api.onrender.com](https://sas-api.onrender.com)**

Health check:

```bash
curl https://sas-api.onrender.com/health
```

### Opción 1: Docker / autoalojamiento

```bash
git clone https://github.com/Leesintheblindmonk1999/SAS.git
cd SAS

docker compose up --build
```

La API local debería estar disponible en:

```text
http://localhost:8000
```

Health check local:

```bash
curl http://localhost:8000/health
```

---

### Opción 2: instalación local con Python

```bash
git clone https://github.com/Leesintheblindmonk1999/SAS.git
cd SAS

python -m venv .venv
```

Activar entorno:

```bash
# Linux/macOS
source .venv/bin/activate
```

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

Instalar dependencias:

```bash
pip install -r requirements.txt
```

Ejecutar API:

```bash
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

Para producción:

```env
CORS_ALLOW_ORIGINS=https://yourdomain.com
ADMIN_SECRET=use-a-strong-random-secret
FREE_REQUESTS_PER_DAY=50
```

---

<a id="es-auth"></a>

## Autenticación API

La mayoría de endpoints requieren una API key.

### API pública alojada

Para el servicio alojado, las API keys son emitidas por el operador del servicio.

Contacto:

```text
duranteg2@gmail.com
```

### Autoalojamiento

Si estás ejecutando tu propia instancia, puedes generar una API key usando el endpoint admin:

```bash
curl -X POST http://localhost:8000/admin/generate-key \
  -H "X-Admin-Secret: change-this-admin-secret"
```

Ejemplo de respuesta:

```json
{
  "api_key": "sas_xxxxxxxxxxxxxxxxxxxxx",
  "created_at": "2026-04-29T00:00:00Z"
}
```

Usar la API key en requests:

```bash
-H "X-API-Key: sas_xxxxxxxxxxxxxxxxxxxxx"
```

---

<a id="es-ejemplos-api"></a>

## Ejemplos de API

Los ejemplos siguientes usan la API pública alojada:

```text
https://sas-api.onrender.com
```

Para autoalojamiento local, reemplazar por:

```text
http://localhost:8000
```

---

### Health check

```bash
curl https://sas-api.onrender.com/health
```

Ejemplo:

```json
{
  "status": "ok",
  "service": "SAS",
  "version": "1.0"
}
```

---

### Auditar una respuesta generada

```bash
curl -X POST https://sas-api.onrender.com/v1/audit \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sas_xxxxxxxxxxxxxxxxxxxxx" \
  -d '{
    "source": "The Eiffel Tower is located in Paris, France.",
    "response": "The Eiffel Tower is located in Berlin, Germany.",
    "experimental": true
  }'
```

Ejemplo de respuesta:

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

### Comparar dos textos

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

Ejemplo:

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
curl -X POST https://sas-api.onrender.com/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sas_xxxxxxxxxxxxxxxxxxxxx" \
  -d '{
    "message": "Explain what κD means in SAS."
  }'
```

---

<a id="es-modulos"></a>

## Control de módulos

Los módulos experimentales pueden activarse mediante variables de entorno:

```env
MODULES_ENABLED=E9,E10,E11,E12
```

O activarse selectivamente:

```env
MODULES_ENABLED=E9,E11
```

| Módulo | Nombre | Función |
|---|---|---|
| E9 | Logical Contradiction | Detecta inversión lógica o contradicción interna |
| E10 | Fact Grounding | Detecta claims no soportados cuando hay grounding local disponible |
| E11 | Temporal Inconsistency | Detecta secuencias temporales incompatibles |
| E12 | Topic Shift | Detecta cambios abruptos de tema sin señales de transición |

Los módulos actúan como factores de penalización independientes y no reemplazan el cálculo core ISI/TDA.

---

<a id="es-zenodo"></a>

## Zenodo y registro

- **Zenodo DOI:** [10.5281/zenodo.19689077](https://doi.org/10.5281/zenodo.19689077)
- **Registro TAD:** `EX-2026-18792778`
- **Autor:** Gonzalo Emir Durante
- **Licencia:** [GPL-3.0 + Durante Invariance License](LICENSE.md)
- **API alojada:** [https://sas-api.onrender.com](https://sas-api.onrender.com)

---

<a id="es-citacion"></a>

## Citación

Si usas SAS, cita el proyecto como:

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

<a id="es-licencia"></a>

## Licencia

Este proyecto se publica bajo:

```text
GPL-3.0 + Durante Invariance License
```

La cláusula adicional Durante Invariance requiere atribución por el uso, implementación o distribución de la constante `κD = 0.56` para detección de invariancia semántica, detección de alucinaciones o propósitos similares.

Ver [LICENSE.md](LICENSE.md) para el texto completo.

### Servicio alojado vs licencia del código

Los planes **SAS Free**, **SAS Pro** y **SAS Enterprise** corresponden al servicio API alojado.

El código fuente sigue bajo **GPL-3.0 + Durante Invariance License**. Puedes autoalojar tu propia instancia bajo esos términos.

---

<a id="es-desarrollo"></a>

## Desarrollo

Ejecutar tests:

```bash
pytest
```

Ejecutar benchmark:

```bash
python tests/benchmark_runner.py
```

Ejecutar API local:

```bash
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
- Proteger `/admin/generate-key` con un admin secret fuerte.

Para reportes de vulnerabilidad, ver [SECURITY.md](SECURITY.md).

---

<a id="es-alcance-y-limitaciones"></a>

## Alcance y limitaciones

SAS está diseñado para auditoría estructural de coherencia y detección de señales de alucinación. No garantiza verificación factual universal.

Limitaciones conocidas:

- El grounding factual depende de fuentes locales disponibles.
- La detección de cambio de tema es conservadora para reducir falsos positivos.
- Los resultados deben interpretarse como evidencia técnica, no como certificación legal.
- Los despliegues productivos requieren hardening de seguridad estándar.
- El rendimiento puede variar en dominios, idiomas y datasets no representados en el benchmark actual.

---

<a id="es-autor"></a>

## Autor

**Gonzalo Emir Durante**

Autor de SAS, Omni-Scanner API y `κD = 0.56`.

Repositorio:

```text
https://github.com/Leesintheblindmonk1999/SAS
```

API alojada:

```text
https://sas-api.onrender.com
```

DOI:

```text
https://doi.org/10.5281/zenodo.19689077
```

Contacto:

```text
duranteg2@gmail.com
```

---

<a id="en"></a>

# English

**SAS - Symbiotic Autoprotection System** is an open-source API framework for detecting structural hallucinations in generative AI outputs.

SAS evaluates whether a generated response preserves semantic structure, logical consistency, numerical integrity, and factual-coherence signals relative to a source text or prompt. It combines topological data analysis, numerical invariance checks, and modular hallucination probes into a FastAPI-based audit system.

The system is authored by **Gonzalo Emir Durante** and published as an open technical standard candidate for structural coherence auditing in AI systems.

---

<a id="en-live-api"></a>

## Live Public API

The official hosted reference API is available at:

**[https://sas-api.onrender.com](https://sas-api.onrender.com)**

Health check:

```bash
curl https://sas-api.onrender.com/health
```

FastAPI interactive documentation:

```text
https://sas-api.onrender.com/docs
```

Self-hosting remains fully supported under the project license.

---

<a id="en-documentation"></a>

## Documentation

| Document | Description |
|---|---|
| [Security Policy](SECURITY.md) | Vulnerability reporting, deployment security notes, and responsible disclosure |
| [Contributing Guide](CONTRIBUTING.md) | Development setup, pull request process, testing, and contribution rules |
| [Code of Conduct](CODE_OF_CONDUCT.md) | Community standards and enforcement policy |
| [Architecture Overview](docs/architecture.md) | High-level system design, detection pipeline, modules, and data flow |
| [Benchmark JSON](docs/benchmark_complete_20260429_172647.json) | Full benchmark output |
| [Benchmark OTS Proof](docs/benchmark_complete_20260429_172647.json.ots) | OpenTimestamps proof for the benchmark |
| [Bug Report Template](.github/ISSUE_TEMPLATE/bug_report.md) | GitHub issue template for bugs |
| [Feature Request Template](.github/ISSUE_TEMPLATE/feature_request.md) | GitHub issue template for enhancement proposals |
| [License](LICENSE.md) | GPL-3.0 + Durante Invariance License |

---

## 🌐 Public Manifesto / SAS Standard

**Official Landing Page:** [sas-landing](https://leesintheblindmonk1999.github.io/sas-landing/)

Benchmark, Declaration of Geopolitical Neutrality, TAD Registration, DOI, and OpenTimestamps Anchoring.

---

<a id="en-problem"></a>

## Problem

Generative AI systems can produce fluent outputs that are structurally inconsistent, logically inverted, numerically wrong, or semantically disconnected from the input.

Traditional similarity metrics often fail to detect these cases because hallucinations may preserve surface fluency while breaking deeper coherence.

SAS addresses this by treating hallucination detection as a **structural coherence audit** problem.

SAS is designed to detect:

- semantic manifold rupture;
- logical contradiction;
- numerical inconsistency;
- reference or grounding anomalies;
- abrupt topic shifts;
- structural divergence between source and response.

SAS is not a universal factual oracle. It provides technical evidence for structural hallucination detection and coherence auditing.

---

<a id="en-kappa"></a>

## Core Concept: κD = 0.56

SAS uses the constant:

```text
κD = 0.56
```

κD, also referred to as the **Durante Constant**, is used as a critical coherence threshold in the SAS pipeline.

Within the framework, κD represents the operational point where semantic noise collapses below structural coherence and meaning becomes stable enough to be treated as preserved.

Operational interpretation:

```text
ISI >= κD  -> structurally coherent
ISI <  κD  -> potential manifold rupture / hallucination signal
```

The constant is used in combination with the **Invariant Similarity Index (ISI)** and additional detection modules.

---

<a id="en-project-structure"></a>

## Project Structure

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

<a id="en-architecture"></a>

## Architecture

```text
SAS/
├── app/                   # Main API code
│   ├── main.py            # FastAPI app: /v1/audit, /v1/diff, /v1/chat, /health
│   └── services/          # Core engine: TDA + NIG + E9-E12 modules
├── tests/benchmark_runner.py # Benchmark execution script
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

### Core Components

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

For a deeper technical view, see [docs/architecture.md](docs/architecture.md).

---

<a id="en-benchmark"></a>

## Benchmark Results

Main artifact:

```text
docs/benchmark_complete_20260429_172647.json
```

OpenTimestamps proof:

```text
docs/benchmark_complete_20260429_172647.json.ots
```

SHA-256 traceability hash:

```text
0713acbbf50e1a0054f545e5eb68078744f9c5a09d4bc370b5224bb81183a6fe
```

| Metric | Result |
|---|---:|
| Evaluated pairs | 2,000 |
| Hallucination pairs | 1,000 |
| Clean pairs | 1,000 |
| Accuracy | 98.80% |
| Precision | 100.00% |
| Recall | 97.60% |
| F1 score | 98.79% |
| κD | 0.56 |
| Hallucination average ISI | 0.072993 |
| Clean average ISI | 1.000000 |

### Confusion Matrix

|  | Actual hallucination | Actual clean |
|---|---:|---:|
| Predicted hallucination | TP = 976 | FP = 0 |
| Predicted clean | FN = 24 | TN = 1000 |

### Benchmark Note

This benchmark includes both hallucination and clean examples. The reported accuracy, precision, recall, and F1 score are derived from the confusion matrix above.

The current benchmark shows **zero false positives** on the evaluated clean subset and high recall on the hallucination subset. This supports SAS as a precision-oriented structural hallucination detector.

To reproduce the benchmark:

```bash
python tests/benchmark_runner.py
```

---

<a id="en-pricing"></a>

## Plans and Pricing

SAS is open source under **GPL-3.0 + Durante Invariance License**.

The plans below refer to the **hosted SAS API service**, not to a modification or relaxation of the source-code license.

Anyone may self-host their own SAS instance under the terms of GPL-3.0 + Durante Invariance License.

| Plan | Usage / Features | Price |
| :--- | :--- | :--- |
| **SAS Free** | 50 requests/day. API key authentication. Ideal for development, testing, and evaluation. | **Free** |
| **SAS Pro** | 10,000 requests/month. No concurrency limit. Priority email support. | **$49 USD/month** or **$490 USD/year** |
| **SAS Enterprise** | Unlimited requests or custom package. Guaranteed SLA 99.9%. Optional On-Premise license. 24/7 support. | **Custom quote** — starting at **$499/month** |

📧 **Interested in an Enterprise license or need a custom plan?** Contact: **duranteg2@gmail.com**

### Commercial Positioning

SAS is designed for precision-oriented hallucination auditing. In the current benchmark, SAS reports **98.8% accuracy**, **100% precision**, and **97.6% recall** across 2,000 evaluated pairs.

You are not paying for vague similarity scoring. You are paying for auditable structural detection with clear metrics, traceable benchmark artifacts, and reproducible evidence.

---

<a id="en-quick-start"></a>

## Quick Start

### Public Hosted API

The public reference API is already running:

**[https://sas-api.onrender.com](https://sas-api.onrender.com)**

Health check:

```bash
curl https://sas-api.onrender.com/health
```

### Option 1: Docker Self-Hosting

```bash
git clone https://github.com/Leesintheblindmonk1999/SAS.git
cd SAS

docker compose up --build
```

The local API should be available at:

```text
http://localhost:8000
```

Local health check:

```bash
curl http://localhost:8000/health
```

---

### Option 2: Local Python Install

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
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

<a id="en-configuration"></a>

## Configuration

Create a local `.env` file:

```env
ADMIN_SECRET=change-this-admin-secret
FREE_REQUESTS_PER_DAY=50
MODULES_ENABLED=E9,E10,E11,E12
CORS_ALLOW_ORIGINS=*
```

Do not commit `.env` files to public repositories.

For production deployments:

```env
CORS_ALLOW_ORIGINS=https://yourdomain.com
ADMIN_SECRET=use-a-strong-random-secret
FREE_REQUESTS_PER_DAY=50
```

---

<a id="en-auth"></a>

## API Authentication

Most API endpoints require an API key.

### Hosted Public API

For the hosted service, API keys are issued by the service operator.

Contact:

```text
duranteg2@gmail.com
```

### Self-hosting

If you are running your own instance, you can generate an API key using the admin endpoint:

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

<a id="en-api-examples"></a>

## API Examples

The examples below use the hosted public API:

```text
https://sas-api.onrender.com
```

For local self-hosting, replace it with:

```text
http://localhost:8000
```

---

### Health Check

```bash
curl https://sas-api.onrender.com/health
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

### Audit a Generated Response

```bash
curl -X POST https://sas-api.onrender.com/v1/audit \
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

### Compare Two Texts

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

### Chat Endpoint

```bash
curl -X POST https://sas-api.onrender.com/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sas_xxxxxxxxxxxxxxxxxxxxx" \
  -d '{
    "message": "Explain what κD means in SAS."
  }'
```

---

<a id="en-modules"></a>

## Module Controls

Experimental modules can be enabled through environment configuration:

```env
MODULES_ENABLED=E9,E10,E11,E12
```

Or selectively disabled:

```env
MODULES_ENABLED=E9,E11
```

| Module | Name | Function |
|---|---|---|
| E9 | Logical Contradiction | Detects internal logical inversion or contradiction |
| E10 | Fact Grounding | Detects unsupported claims when local grounding is available |
| E11 | Temporal Inconsistency | Detects incompatible temporal sequences |
| E12 | Topic Shift | Detects abrupt topic changes without transition signals |

Modules are used as independent penalty factors and do not replace the core ISI/TDA calculation.

---

<a id="en-zenodo"></a>

## Zenodo and Registration

- **Zenodo DOI:** [10.5281/zenodo.19689077](https://doi.org/10.5281/zenodo.19689077)
- **TAD Registry:** `EX-2026-18792778`
- **Author:** Gonzalo Emir Durante
- **License:** [GPL-3.0 + Durante Invariance License](LICENSE.md)
- **Hosted API:** [https://sas-api.onrender.com](https://sas-api.onrender.com)

---

<a id="en-citation"></a>

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

<a id="en-license"></a>

## License

This project is licensed under:

```text
GPL-3.0 + Durante Invariance License
```

The additional Durante Invariance clause requires attribution for use, implementation, or distribution of the `κD = 0.56` constant for semantic invariance detection, hallucination detection, or similar purposes.

See [LICENSE.md](LICENSE.md) for the full license text.

### Hosted Service vs Source Code License

The **SAS Free**, **SAS Pro**, and **SAS Enterprise** plans refer to the hosted SAS API service.

The source code remains licensed under **GPL-3.0 + Durante Invariance License**. You may self-host your own instance under those license terms.

---

<a id="en-development"></a>

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
- The `/admin/generate-key` endpoint must be protected by a strong admin secret.

For vulnerability reports, see [SECURITY.md](SECURITY.md).

---

<a id="en-scope-and-limitations"></a>

## Scope and Limitations

SAS is designed for structural coherence auditing and hallucination signal detection. It does not guarantee universal factual verification.

Known limitations:

- Factual grounding depends on available local knowledge sources.
- Topic-shift detection is conservative to reduce false positives.
- Results should be interpreted as technical evidence, not as legal certification.
- Production deployments require standard security hardening.
- Benchmark performance may vary across domains, languages, and datasets not represented in the current evaluation.

---

<a id="en-author"></a>

## Author

**Gonzalo Emir Durante**

Author of SAS, Omni-Scanner API, and `κD = 0.56`.

Repository:

```text
https://github.com/Leesintheblindmonk1999/SAS
```

Hosted API:

```text
https://sas-api.onrender.com
```

DOI:

```text
https://doi.org/10.5281/zenodo.19689077
```

Contact:

```text
duranteg2@gmail.com
```
