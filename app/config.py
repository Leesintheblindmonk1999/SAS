"""
app/config.py — Omni-Scanner API v1.0 + SAS
Autor: Gonzalo Emir Durante — TAD EX-2026-18792778
"""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ========================================================================
    # API Security
    # ========================================================================
    admin_secret: str = "sas_admin_dev_2026_durante"

    # ========================================================================
    # Core Detection
    # ========================================================================
    kappa_d: float = 0.56
    scan_timeout_seconds: int = 30
    min_text_length: int = 30

    # ========================================================================
    # Database paths (relative to app/ folder)
    # ========================================================================
    auth_db_path: str = "data/auth.db"
    rate_limit_db_path: str = "data/rate_limit.db"

    # ========================================================================
    # Rate Limiting
    # ========================================================================
    free_requests_per_day: int = 100

    # ========================================================================
    # Ollama (local LLM for /v1/chat)
    # ========================================================================
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:14b-instruct-q4_K_M"
    ollama_timeout: int = 60

    # ========================================================================
    # Extended Modules E9-E12
    # ========================================================================
    modules_enabled: str = "E9,E11,E12"
    sas_fact_kb_path: str = ""
    sas_fact_kb_flag_unknown: bool = False
    sas_topic_shift_use_st: bool = False
    sas_topic_shift_model: str = "all-MiniLM-L6-v2"

    # ========================================================================
    # CORS
    # ========================================================================
    cors_allow_origins: str = "*"

    # ========================================================================
    # Logging
    # ========================================================================
    log_level: str = "INFO"

    # ========================================================================
    # SAS Identity
    # ========================================================================
    sas_version: str = "1.1.0-beta"
    registry: str = "TAD EX-2026-18792778"
    zenodo_doi: str = "10.5281/zenodo.19543972"

    # ========================================================================
    # Legacy / compatibility fields (no romper si están en .env)
    # ========================================================================
    enable_external_audit: bool = False
    ollama_url: str = ""  # se usa solo si ollama_host no está definido
    ollama_models_url: str = "http://localhost:11434/api/tags"
    database_url: str = "sqlite:///./omni_scanner.db"  # legacy

    # ========================================================================
    # Pydantic configuration
    # ========================================================================
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",  # <- clave: ignora variables del .env no definidas aquí
    )

    # ========================================================================
    # Properties (helpers)
    # ========================================================================
    @property
    def enabled_modules(self) -> list[str]:
        if not self.modules_enabled.strip():
            return []
        return [m.strip().upper() for m in self.modules_enabled.split(",") if m.strip()]

    @property
    def cors_origins(self) -> list[str]:
        if self.cors_allow_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]

    @property
    def ollama_api_url(self) -> str:
        """Compatibilidad: usa ollama_host + endpoint fijo"""
        if self.ollama_host:
            # Si no tiene /api/chat al final, lo agregamos
            base = self.ollama_host.rstrip('/')
            if not base.endswith('/api/chat'):
                base = f"{base}/api/chat"
            return base
        return self.ollama_url or "http://localhost:11434/api/chat"


settings = Settings()