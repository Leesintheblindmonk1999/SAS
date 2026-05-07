from __future__ import annotations

import json
import os
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


README_PATH = Path("README.md")

SAS_API_URL = os.getenv("SAS_API_URL", "https://sas-api.onrender.com").rstrip("/")
GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY", "Leesintheblindmonk1999/SAS")
GH_TRAFFIC_TOKEN = os.getenv("GH_TRAFFIC_TOKEN") or os.getenv("GITHUB_TOKEN", "")

START = "<!-- SAS-LIVE-METRICS:START -->"
END = "<!-- SAS-LIVE-METRICS:END -->"


def http_json(url: str, headers: dict[str, str] | None = None) -> dict:
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_public_stats() -> dict:
    try:
        return http_json(f"{SAS_API_URL}/public/stats")
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def fetch_clones() -> dict:
    if not GH_TRAFFIC_TOKEN:
        return {"available": False, "reason": "GitHub token not configured"}

    url = f"https://api.github.com/repos/{GITHUB_REPOSITORY}/traffic/clones"

    try:
        return http_json(
            url,
            headers={
                "Authorization": f"Bearer {GH_TRAFFIC_TOKEN}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
    except Exception as exc:
        return {"available": False, "reason": str(exc)}


def render_block(stats: dict, clones: dict) -> str:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    w24 = stats.get("window_24h", {})
    w7 = stats.get("window_7d", {})
    signal = stats.get("monitoring_signal", {})

    countries = w24.get("countries", [])
    countries_text = ", ".join(
        f"{c.get('country', 'unknown')}={c.get('total_requests', 0)}"
        for c in countries[:6]
    ) or "n/a"

    clone_count = clones.get("count", "unavailable")
    unique_cloners = clones.get("uniques", "unavailable")

    total24 = w24.get("total_requests", "n/a")
    ok24 = w24.get("successful_requests", "n/a")
    err4 = w24.get("client_errors_4xx", "n/a")
    err5 = w24.get("server_errors_5xx", "n/a")
    unique = w24.get("unique_users", "n/a")
    total7 = w7.get("total_requests", "n/a")
    monitoring = signal.get("signal", "unknown")

    return f"""{START}
## Live Operational Snapshot / Estado Operativo Vivo

_Last automated update / Última actualización automática:_ `{now}`

### English

| Signal | Value |
|---|---:|
| API product requests, last 24h | `{total24}` |
| Successful requests, last 24h | `{ok24}` |
| 4xx errors, last 24h | `{err4}` |
| 5xx errors, last 24h | `{err5}` |
| Unique anonymized users, last 24h | `{unique}` |
| API product requests, last 7d | `{total7}` |
| Detected country buckets | `{countries_text}` |
| Monitoring signal | `{monitoring}` |
| Repository clones | `{clone_count}` |
| Unique cloners | `{unique_cloners}` |

### Español

| Señal | Valor |
|---|---:|
| Requests de producto, últimas 24h | `{total24}` |
| Requests exitosas, últimas 24h | `{ok24}` |
| Errores 4xx, últimas 24h | `{err4}` |
| Errores 5xx, últimas 24h | `{err5}` |
| Usuarios anonimizados únicos, últimas 24h | `{unique}` |
| Requests de producto, últimos 7d | `{total7}` |
| Países detectados | `{countries_text}` |
| Señal de monitoreo | `{monitoring}` |
| Clones del repositorio | `{clone_count}` |
| Clonadores únicos | `{unique_cloners}` |

> Public note / Nota pública: generated from aggregated public API metrics and GitHub traffic data. No raw IPs, raw API keys, API key hashes, or request IDs are published.
{END}"""


def update_readme(block: str) -> bool:
    if not README_PATH.exists():
        print("README.md not found")
        return False

    text = README_PATH.read_text(encoding="utf-8")

    if START not in text or END not in text:
        print("README markers not found")
        return False

    before = text.split(START)[0]
    after = text.split(END)[1]
    new_text = before + block + after

    if new_text == text:
        return False

    README_PATH.write_text(new_text, encoding="utf-8")
    return True


def main() -> int:
    stats = fetch_public_stats()
    clones = fetch_clones()
    block = render_block(stats, clones)

    changed = update_readme(block)
    print("README changed:", changed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
