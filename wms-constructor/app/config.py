"""Настройки приложения. Читаются из переменных окружения (секреты - только из app.env вне репозитория)."""
from __future__ import annotations

import os
from dataclasses import dataclass, field


def _int(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    return int(raw) if raw else default


@dataclass(frozen=True)
class Settings:
    host: str = ""
    port: int = 1433
    user: str = ""
    password: str = field(default="", repr=False)  # пароль не попадает в repr/логи
    database: str = "LV_MERIDIAN"
    exchange_db: str = "MRDN_Exchange"
    trust_cert: bool = True
    row_limit_ui: int = 5000
    row_limit_xlsx: int = 100000
    query_timeout: int = 60
    queries_dir: str = "/app/queries"


def load_settings() -> Settings:
    return Settings(
        host=os.environ.get("MSSQL_HOST", "").strip(),
        port=_int("MSSQL_PORT", 1433),
        user=os.environ.get("MSSQL_USER", "").strip(),
        password=os.environ.get("MSSQL_PASSWORD", ""),
        database=os.environ.get("MSSQL_DB", "LV_MERIDIAN").strip(),
        exchange_db=os.environ.get("MSSQL_EXCHANGE_DB", "MRDN_Exchange").strip(),
        trust_cert=os.environ.get("MSSQL_TRUST_CERT", "yes").strip().lower() in ("1", "yes", "true"),
        row_limit_ui=_int("ROW_LIMIT_UI", 5000),
        row_limit_xlsx=min(_int("ROW_LIMIT_XLSX", 100000), 1_000_000),
        query_timeout=_int("QUERY_TIMEOUT", 60),
        queries_dir=os.environ.get("QUERIES_DIR", "/app/queries"),
    )
