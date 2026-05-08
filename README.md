# SAS - Symbiotic Autoprotection System

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19702379.svg)](https://doi.org/10.5281/zenodo.19702379)
[![Landing Page](https://img.shields.io/badge/Landing_Page-online-0a0e17?style=flat&logo=github)](https://leesintheblindmonk1999.github.io/sas-landing/)
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
Live metrics will be updated automatically.
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

## API pública en vivo

La API pública oficial de referencia está en funcionamiento:

**[https://sas-api.onrender.com](https://sas-api.onrender.com)**

```bash
curl https://sas-api.onrender.com/health
```

Documentación interactiva:

```text
https://sas-api.onrender.com/docs
```

---

## Cliente Python oficial

SAS está disponible como cliente Python y CLI instalable desde PyPI:

```bash
pip install sas-client
```

Repositorio:

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

---

## Documentación

| Documento | Descripción |
|---|---|
| [Security Policy](SECURITY.md) | Reporte de vulnerabilidades, seguridad y divulgación responsable |
| [Contributing Guide](CONTRIBUTING.md) | Setup, pull requests, testing y contribuciones |
| [Code of Conduct](CODE_OF_CONDUCT.md) | Estándares comunitarios |
| [Architecture Overview](docs/architecture.md) | Arquitectura, pipeline y módulos |
| [Benchmark JSON](docs/benchmark_complete_20260429_172647.json) | Resultado completo del benchmark |
| [Benchmark OTS Proof](docs/benchmark_complete_20260429_172647.json.ots) | Prueba OpenTimestamps |
| [License](LICENSE.md) | GPL-3.0 + Durante Invariance License |

---

## Manifesto público / Estándar SAS

**Landing page oficial:** [sas-landing](https://leesintheblindmonk1999.github.io/sas-landing/)

La landing pública presenta benchmark, neutralidad geopolítica, registro TAD, DOI, anclaje OpenTimestamps, API pública, pricing, actividad pública anonimizada y contacto comercial.

---

## Problema que resuelve

Los sistemas de IA generativa pueden producir respuestas fluidas pero estructuralmente inconsistentes, lógicamente invertidas, numéricamente erróneas o desconectadas semánticamente del input.

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

## Concepto central: κD = 0.56

```text
κD = 0.56
```

κD, también llamada **Durante Constant**, funciona como umbral crítico de coherencia dentro del pipeline SAS.

```text
ISI >= κD  -> estructuralmente coherente
ISI <  κD  -> posible ruptura de manifold / señal de alucinación
```

---

## Arquitectura

```text
SAS/
├── app/                       # Código principal de la API
│   ├── main.py                # FastAPI app
│   ├── routers/               # /v1/audit, /v1/diff, /v1/chat, admin, metrics
│   └── services/              # Motor core, auth, metrics y servicios auxiliares
├── docs/
│   ├── architecture.md
│   ├── benchmark_complete_20260429_172647.json
│   └── benchmark_complete_20260429_172647.json.ots
├── tests/
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

| Componente | Función |
|---|---|
| TDA | Topological Data Analysis para comparación estructural semántica |
| ISI | Invariant Similarity Index |
| NIG | Numerical Invariance Guard |
| E9 | Detección de contradicción lógica |
| E10 | Grounding factual / detección de inventiva narrativa |
| E11 | Detección de inconsistencia temporal |
| E12 | Detección de cambio abrupto de tema |
| FastAPI | API para audit, diff, chat, health, admin, métricas y actividad pública |

---

## Benchmark

Artefacto principal:

```text
docs/benchmark_complete_20260429_172647.json
```

Prueba OpenTimestamps:

```text
docs/benchmark_complete_20260429_172647.json.ots
```

Hash SHA-256:

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

## Planes y precios

SAS es open source bajo **GPL-3.0 + Durante Invariance License**.

Los planes siguientes corresponden al **servicio API alojado**, soporte comercial, integración privada o licenciamiento empresarial.

| Plan | Uso / Características | Precio |
| :--- | :--- | :--- |
| **SAS Free** | 50 requests/día. API Key incluida. Ideal para pruebas, desarrollo individual y evaluación técnica inicial. | **Gratis** |
| **SAS Developer / Pro** | 10.000 requests/mes. API Key. Acceso a la API pública alojada. Soporte básico por email. | **99 USD/mes** |
| **SAS Team** | 50.000 requests/mes. Uso para equipos. Soporte prioritario. Adecuado para startups RAG, equipos ML y validación interna. | **299 USD/mes** |
| **SAS Enterprise Cloud** | Volumen alto o paquete personalizado. Soporte directo. Integración privada. SLA según acuerdo comercial. | **Desde 1.500 USD/mes** |
| **SAS On-Premise License** | Despliegue privado en infraestructura del cliente. Licencia comercial. Integración interna y soporte de implementación. | **Desde 15.000 USD/año** |
| **Piloto técnico** | Auditoría inicial, integración guiada, informe técnico y validación sobre casos de uso del cliente. | **1.500–3.000 USD, pago único** |

📧 **Consultas comerciales, licencias Enterprise u On-Premise:** duranteg2@gmail.com

---

## Inicio rápido

### Cliente Python

```bash
pip install sas-client
```

```python
from sas_client import SASClient

client = SASClient(api_key="YOUR_API_KEY")
print(client.health())
```

### API pública alojada

```bash
curl https://sas-api.onrender.com/health
```

### Docker / autoalojamiento

```bash
git clone https://github.com/Leesintheblindmonk1999/SAS.git
cd SAS
docker compose up --build
```

### Instalación local con Python

```bash
git clone https://github.com/Leesintheblindmonk1999/SAS.git
cd SAS
python -m venv .venv
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

---

## Configuración

```env
ADMIN_SECRET=change-this-admin-secret
FREE_REQUESTS_PER_DAY=50
MODULES_ENABLED=E9,E10,E11,E12
CORS_ALLOW_ORIGINS=*
```

No subir archivos `.env` a repositorios públicos.

---

## Autenticación API

La mayoría de endpoints requieren una API key.

Para el servicio alojado, las API keys son emitidas por el operador del servicio.

Contacto:

```text
duranteg2@gmail.com
```

Para autoalojamiento:

```bash
curl -X POST http://localhost:8000/admin/generate-key   -H "X-Admin-Secret: change-this-admin-secret"
```

Usar la API key:

```bash
-H "X-API-Key: sas_xxxxxxxxxxxxxxxxxxxxx"
```

---

## Ejemplos de API

### Health check

```bash
curl https://sas-api.onrender.com/health
```

### Auditar una respuesta

```bash
curl -X POST https://sas-api.onrender.com/v1/audit   -H "Content-Type: application/json"   -H "X-API-Key: sas_xxxxxxxxxxxxxxxxxxxxx"   -d '{
    "source": "The Eiffel Tower is located in Paris, France.",
    "response": "The Eiffel Tower is located in Berlin, Germany.",
    "experimental": true
  }'
```

### Comparar dos textos

```bash
curl -X POST https://sas-api.onrender.com/v1/diff   -H "Content-Type: application/json"   -H "X-API-Key: sas_xxxxxxxxxxxxxxxxxxxxx"   -d '{
    "text_a": "Python is commonly used for automation and data analysis.",
    "text_b": "Python is mainly a type of tropical snake used in weather forecasting.",
    "experimental": true
  }'
```

---

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

## Métricas públicas anonimizadas

```text
https://sas-api.onrender.com/public/stats
https://sas-api.onrender.com/public/activity?limit=100
```

Estos endpoints alimentan la landing pública y el README vivo.

---

## Zenodo y registro

- **Zenodo DOI:** [10.5281/zenodo.19702379](https://doi.org/10.5281/zenodo.19702379)
- **Registro TAD:** `EX-2026-18792778`
- **Autor:** Gonzalo Emir Durante
- **Licencia:** [GPL-3.0 + Durante Invariance License](LICENSE.md)
- **API alojada:** [https://sas-api.onrender.com](https://sas-api.onrender.com)
- **Cliente PyPI:** [https://pypi.org/project/sas-client/](https://pypi.org/project/sas-client/)

---

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

## Licencia

```text
GPL-3.0 + Durante Invariance License
```

Ver [LICENSE.md](LICENSE.md) para el texto completo.

---

## Desarrollo

```bash
pytest
python tests/benchmark_runner.py
uvicorn app.main:app --reload
```

---

## Notas de seguridad

- No subir archivos `.env`.
- Rotar `ADMIN_SECRET` antes de despliegue.
- Usar HTTPS en producción.
- Restringir CORS en producción.
- Mantener API keys privadas.
- Proteger `/admin/generate-key` con un admin secret fuerte.
- No exponer secretos SMTP, tokens PyPI, API keys ni admin secrets.

Para reportes de vulnerabilidad, ver [SECURITY.md](SECURITY.md).

---

## Alcance y limitaciones

SAS está diseñado para auditoría estructural de coherencia y detección de señales de alucinación. No garantiza verificación factual universal.

Limitaciones conocidas:

- El grounding factual depende de fuentes locales disponibles.
- La detección de cambio de tema es conservadora para reducir falsos positivos.
- Los resultados deben interpretarse como evidencia técnica, no como certificación legal.
- Los despliegues productivos requieren hardening de seguridad estándar.
- El rendimiento puede variar en dominios, idiomas y datasets no representados en el benchmark actual.

---

## Autor

**Gonzalo Emir Durante**

Autor de SAS, Omni-Scanner API y `κD = 0.56`.

- Repositorio: <https://github.com/Leesintheblindmonk1999/SAS>
- Cliente Python: <https://github.com/Leesintheblindmonk1999/sas-client>
- API alojada: <https://sas-api.onrender.com>
- DOI: <https://doi.org/10.5281/zenodo.19702379>
- Contacto: duranteg2@gmail.com

---

<a id="en"></a>

# English

**SAS - Symbiotic Autoprotection System** is an open-source API framework for detecting structural hallucinations in generative AI outputs.

SAS evaluates whether a generated response preserves semantic structure, logical consistency, numerical integrity, and factual-coherence signals relative to a source text or prompt. It combines topological data analysis, numerical invariance checks, and modular hallucination probes into a FastAPI-based audit system.

The system is authored by **Gonzalo Emir Durante** and published as an open technical standard candidate for structural coherence auditing in AI systems.

---

## Live Public API

The official hosted reference API is available at:

**[https://sas-api.onrender.com](https://sas-api.onrender.com)**

```bash
curl https://sas-api.onrender.com/health
```

Interactive documentation:

```text
https://sas-api.onrender.com/docs
```

---

## Official Python Client

SAS is available as an installable Python client and CLI from PyPI:

```bash
pip install sas-client
```

Repository:

```text
https://github.com/Leesintheblindmonk1999/sas-client
```

PyPI:

```text
https://pypi.org/project/sas-client/
```

### Python usage

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

### CLI usage

```bash
sas health
sas public-stats
sas public-activity --limit 10
sas --api-key YOUR_API_KEY diff "Python is a programming language." "A python is a snake."
```

---

## Documentation

| Document | Description |
|---|---|
| [Security Policy](SECURITY.md) | Vulnerability reporting, security notes, and responsible disclosure |
| [Contributing Guide](CONTRIBUTING.md) | Setup, pull requests, testing, and contribution rules |
| [Code of Conduct](CODE_OF_CONDUCT.md) | Community standards |
| [Architecture Overview](docs/architecture.md) | Architecture, pipeline, and modules |
| [Benchmark JSON](docs/benchmark_complete_20260429_172647.json) | Full benchmark output |
| [Benchmark OTS Proof](docs/benchmark_complete_20260429_172647.json.ots) | OpenTimestamps proof |
| [License](LICENSE.md) | GPL-3.0 + Durante Invariance License |

---

## Public Manifesto / SAS Standard

**Official Landing Page:** [sas-landing](https://leesintheblindmonk1999.github.io/sas-landing/)

The public landing page presents benchmark evidence, geopolitical neutrality statement, TAD registry, DOI, OpenTimestamps anchoring, public API, pricing, anonymized public activity, and commercial contact.

---

## Problem

Generative AI systems can produce fluent outputs that are structurally inconsistent, logically inverted, numerically wrong, or semantically disconnected from the input.

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

## Core Concept: κD = 0.56

```text
κD = 0.56
```

κD, also referred to as the **Durante Constant**, is used as a critical coherence threshold in the SAS pipeline.

```text
ISI >= κD  -> structurally coherent
ISI <  κD  -> potential manifold rupture / hallucination signal
```

---

## Architecture

```text
SAS/
├── app/                       # Main API code
│   ├── main.py                # FastAPI app
│   ├── routers/               # /v1/audit, /v1/diff, /v1/chat, admin, metrics
│   └── services/              # Core engine, auth, metrics, auxiliary services
├── docs/
│   ├── architecture.md
│   ├── benchmark_complete_20260429_172647.json
│   └── benchmark_complete_20260429_172647.json.ots
├── tests/
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

| Component | Purpose |
|---|---|
| TDA | Topological Data Analysis for semantic structure comparison |
| ISI | Invariant Similarity Index |
| NIG | Numerical Invariance Guard |
| E9 | Logical contradiction detection |
| E10 | Fact grounding / narrative inventiveness check |
| E11 | Temporal inconsistency detection |
| E12 | Abrupt topic shift detection |
| FastAPI | API for audit, diff, chat, health, admin, metrics, and public activity |

---

## Benchmark Results

Main artifact:

```text
docs/benchmark_complete_20260429_172647.json
```

OpenTimestamps proof:

```text
docs/benchmark_complete_20260429_172647.json.ots
```

SHA-256 hash:

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

To reproduce the benchmark:

```bash
python tests/benchmark_runner.py
```

---

## Plans and Pricing

SAS is open source under **GPL-3.0 + Durante Invariance License**.

The plans below refer to the **hosted SAS API service**, commercial support, private integration, or enterprise licensing.

| Plan | Usage / Features | Price |
| :--- | :--- | :--- |
| **SAS Free** | 50 requests/day. API Key included. Ideal for testing, individual development, and initial technical evaluation. | **Free** |
| **SAS Developer / Pro** | 10,000 requests/month. API Key. Access to the hosted public API. Basic email support. | **USD 99/month** |
| **SAS Team** | 50,000 requests/month. Team usage. Priority support. Suitable for RAG startups, ML teams, and internal validation. | **USD 299/month** |
| **SAS Enterprise Cloud** | High-volume usage or custom request package. Direct support. Private integration. SLA according to commercial agreement. | **From USD 1,500/month** |
| **SAS On-Premise License** | Private deployment on customer infrastructure. Commercial license. Internal integration and implementation support. | **From USD 15,000/year** |
| **Technical Pilot** | Initial audit, guided integration, technical report, and validation on customer-specific use cases. | **USD 1,500–3,000 one-time payment** |

📧 **Commercial inquiries, Enterprise licensing, or On-Premise deployment:** duranteg2@gmail.com

---

## Quick Start

### Python client

```bash
pip install sas-client
```

```python
from sas_client import SASClient

client = SASClient(api_key="YOUR_API_KEY")
print(client.health())
```

### Public hosted API

```bash
curl https://sas-api.onrender.com/health
```

### Docker self-hosting

```bash
git clone https://github.com/Leesintheblindmonk1999/SAS.git
cd SAS
docker compose up --build
```

### Local Python install

```bash
git clone https://github.com/Leesintheblindmonk1999/SAS.git
cd SAS
python -m venv .venv
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

---

## Configuration

```env
ADMIN_SECRET=change-this-admin-secret
FREE_REQUESTS_PER_DAY=50
MODULES_ENABLED=E9,E10,E11,E12
CORS_ALLOW_ORIGINS=*
```

Do not commit `.env` files to public repositories.

---

## API Authentication

Most API endpoints require an API key.

For the hosted service, API keys are issued by the service operator.

Contact:

```text
duranteg2@gmail.com
```

For self-hosting:

```bash
curl -X POST http://localhost:8000/admin/generate-key   -H "X-Admin-Secret: change-this-admin-secret"
```

Use the API key:

```bash
-H "X-API-Key: sas_xxxxxxxxxxxxxxxxxxxxx"
```

---

## API Examples

### Health Check

```bash
curl https://sas-api.onrender.com/health
```

### Audit a generated response

```bash
curl -X POST https://sas-api.onrender.com/v1/audit   -H "Content-Type: application/json"   -H "X-API-Key: sas_xxxxxxxxxxxxxxxxxxxxx"   -d '{
    "source": "The Eiffel Tower is located in Paris, France.",
    "response": "The Eiffel Tower is located in Berlin, Germany.",
    "experimental": true
  }'
```

### Compare two texts

```bash
curl -X POST https://sas-api.onrender.com/v1/diff   -H "Content-Type: application/json"   -H "X-API-Key: sas_xxxxxxxxxxxxxxxxxxxxx"   -d '{
    "text_a": "Python is commonly used for automation and data analysis.",
    "text_b": "Python is mainly a type of tropical snake used in weather forecasting.",
    "experimental": true
  }'
```

---

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

## Public Anonymized Metrics

```text
https://sas-api.onrender.com/public/stats
https://sas-api.onrender.com/public/activity?limit=100
```

These endpoints feed the public landing page and the live README section.

---

## Zenodo and Registration

- **Zenodo DOI:** [10.5281/zenodo.19702379](https://doi.org/10.5281/zenodo.19702379)
- **TAD Registry:** `EX-2026-18792778`
- **Author:** Gonzalo Emir Durante
- **License:** [GPL-3.0 + Durante Invariance License](LICENSE.md)
- **Hosted API:** [https://sas-api.onrender.com](https://sas-api.onrender.com)
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

See [LICENSE.md](LICENSE.md) for the full license text.

---

## Development

```bash
pytest
python tests/benchmark_runner.py
uvicorn app.main:app --reload
```

---

## Security Notes

- Do not commit `.env` files.
- Rotate `ADMIN_SECRET` before deployment.
- Use HTTPS in production.
- Restrict CORS origins in production.
- Keep API keys private.
- Protect `/admin/generate-key` with a strong admin secret.
- Do not expose SMTP secrets, PyPI tokens, API keys, or admin secrets.

For vulnerability reports, see [SECURITY.md](SECURITY.md).

---

## Scope and Limitations

SAS is designed for structural coherence auditing and hallucination signal detection. It does not guarantee universal factual verification.

Known limitations:

- Factual grounding depends on available local knowledge sources.
- Topic-shift detection is conservative to reduce false positives.
- Results should be interpreted as technical evidence, not as legal certification.
- Production deployments require standard security hardening.
- Benchmark performance may vary across domains, languages, and datasets not represented in the current evaluation.

---

## Author

**Gonzalo Emir Durante**

Author of SAS, Omni-Scanner API, and `κD = 0.56`.

- Repository: <https://github.com/Leesintheblindmonk1999/SAS>
- Python client: <https://github.com/Leesintheblindmonk1999/sas-client>
- Hosted API: <https://sas-api.onrender.com>
- DOI: <https://doi.org/10.5281/zenodo.19702379>
- Contact: duranteg2@gmail.com
