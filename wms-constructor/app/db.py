"""Подключение к MS SQL (только чтение, учётная запись constructor_ro) и выполнение запроса."""
from __future__ import annotations

import datetime as dt
import decimal
import time
from dataclasses import dataclass

import pyodbc

from .config import Settings
from .queries import QueryError


def _esc(value: str) -> str:
    return "{" + value.replace("}", "}}") + "}"


def connect(s: Settings, database: str | None = None) -> pyodbc.Connection:
    if not (s.host and s.user and s.password):
        raise QueryError("не заданы MSSQL_HOST / MSSQL_USER / MSSQL_PASSWORD")
    cs = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={s.host},{s.port};DATABASE={database or s.database};"
        f"UID={_esc(s.user)};PWD={_esc(s.password)};"
        f"Encrypt=yes;TrustServerCertificate={'yes' if s.trust_cert else 'no'};"
        "APP=wms-constructor;"
    )
    conn = pyodbc.connect(cs, timeout=10, autocommit=True)
    conn.timeout = s.query_timeout  # таймаут выполнения запроса, секунды
    return conn


@dataclass
class Result:
    columns: list[str]
    rows: list[tuple]
    truncated: bool
    elapsed_ms: int


def run(s: Settings, sql: str, args: list, limit: int) -> Result:
    t0 = time.perf_counter()
    conn = connect(s)
    try:
        cur = conn.cursor()
        cur.execute(sql, args) if args else cur.execute(sql)
        if cur.description is None:
            raise QueryError("запрос не вернул набор строк")
        columns = [(d[0] or f"Столбец {i + 1}") for i, d in enumerate(cur.description)]
        rows = cur.fetchmany(limit + 1)
        truncated = len(rows) > limit
        rows = [tuple(r) for r in rows[:limit]]
    finally:
        conn.close()
    return Result(columns, rows, truncated, int((time.perf_counter() - t0) * 1000))


def to_json_value(v):
    """Значение ячейки для JSON (экран). Двоичные данные не передаются."""
    if v is None or isinstance(v, (bool, int, float, str)):
        return v
    if isinstance(v, decimal.Decimal):
        return format(v, "f")
    if isinstance(v, dt.datetime):
        return v.isoformat(sep=" ", timespec="seconds")
    if isinstance(v, (dt.date, dt.time)):
        return v.isoformat()
    if isinstance(v, (bytes, bytearray, memoryview)):
        return "<двоичные данные>"
    return str(v)
