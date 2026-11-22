"""Веб-приложение конструктора запросов LV_MERIDIAN (только чтение)."""
from __future__ import annotations

import datetime as dt
import logging
import urllib.parse
from pathlib import Path

import pyodbc
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import db
from .config import Settings, load_settings
from .excel import build_xlsx
from .queries import QueryError, Registry, bind, load_registry, resolve_default

log = logging.getLogger("wms-constructor")


class RunBody(BaseModel):
    params: dict = Field(default_factory=dict)


def create_app(settings: Settings | None = None) -> FastAPI:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    s = settings or load_settings()
    registry: Registry = load_registry(s.queries_dir)  # при ошибках в YAML приложение не стартует
    app = FastAPI(title="Конструктор запросов LV_MERIDIAN", docs_url=None, redoc_url=None, openapi_url=None)

    def get_query(qid: str):
        q = registry.queries.get(qid)
        if q is None:
            raise HTTPException(404, "Запрос не найден")
        return q, registry.section_of(q)

    def fail(exc: Exception, qid: str):
        if isinstance(exc, QueryError):
            return JSONResponse({"error": str(exc)}, status_code=400)
        if isinstance(exc, pyodbc.Error):
            state = exc.args[0] if exc.args else ""
            log.error("query=%s db_error=%s", qid, exc)
            if state == "HYT00":
                return JSONResponse({"error": "Превышено время ожидания запроса"}, status_code=504)
            return JSONResponse({"error": "Ошибка выполнения запроса (подробности в журнале сервера)"}, status_code=502)
        raise exc

    @app.get("/healthz")
    def healthz():
        return {"status": "ok", "queries": len(registry.queries)}

    @app.get("/api/menu")
    def menu():
        return registry.menu()

    @app.get("/api/queries/{qid}")
    def meta(qid: str):
        q, sec = get_query(qid)
        return {
            "id": q.id,
            "title": q.title,
            "section": sec.title,
            "group": q.group,
            "kind": q.kind,
            "description": q.description,
            "row_limit_ui": s.row_limit_ui,
            "variables": [
                {
                    "name": n,
                    "label": sec.variables[n].label,
                    "type": sec.variables[n].type,
                    "default": resolve_default(sec.variables[n]),
                    "has_options": bool(sec.variables[n].options_sql or sec.variables[n].options),
                }
                for n in q.params
            ],
        }

    @app.get("/api/queries/{qid}/options/{name}")
    def options(qid: str, name: str, request: Request):
        q, sec = get_query(qid)
        var = sec.variables.get(name)
        if var is None or name not in q.params:
            raise HTTPException(404, "Параметр не найден")
        if var.options is not None:
            return var.options
        if not var.options_sql:
            return []
        try:
            res = db.run(s, var.options_sql, [], 1000)
        except Exception as exc:  # noqa: BLE001
            return fail(exc, qid)
        return [
            {"value": db.to_json_value(r[0]), "label": db.to_json_value(r[1] if len(r) > 1 else r[0])}
            for r in res.rows
        ]

    @app.post("/api/queries/{qid}/run")
    def run_query(qid: str, body: RunBody, request: Request):
        q, sec = get_query(qid)
        try:
            sql, args = bind(q, sec.variables, body.params)
            res = db.run(s, sql, args, s.row_limit_ui)
        except Exception as exc:  # noqa: BLE001
            return fail(exc, qid)
        log.info("run query=%s ip=%s rows=%d ms=%d truncated=%s", qid, request.client.host if request.client else "-", len(res.rows), res.elapsed_ms, res.truncated)
        return {
            "columns": res.columns,
            "rows": [[db.to_json_value(v) for v in r] for r in res.rows],
            "truncated": res.truncated,
            "row_limit": s.row_limit_ui,
            "elapsed_ms": res.elapsed_ms,
        }

    @app.post("/api/queries/{qid}/export")
    def export(qid: str, body: RunBody, request: Request):
        q, sec = get_query(qid)
        try:
            sql, args = bind(q, sec.variables, body.params)
            res = db.run(s, sql, args, s.row_limit_xlsx)
        except Exception as exc:  # noqa: BLE001
            return fail(exc, qid)
        now = dt.datetime.now()
        info = [
            ("Запрос", q.title),
            ("Раздел", sec.title),
            ("Идентификатор", q.id),
            ("Выгружено", now.strftime("%Y-%m-%d %H:%M:%S")),
            ("Строк в файле", str(len(res.rows))),
            ("Обрезано по лимиту", f"да (лимит {s.row_limit_xlsx})" if res.truncated else "нет"),
        ]
        for n in q.params:
            v = body.params.get(n)
            info.append((f"Параметр: {sec.variables[n].label}", ", ".join(map(str, v)) if isinstance(v, list) else str(v if v is not None else "")))
        data = build_xlsx(q.title, res.columns, res.rows, info)
        log.info("export query=%s ip=%s rows=%d ms=%d", qid, request.client.host if request.client else "-", len(res.rows), res.elapsed_ms)
        fname = f"{q.title}_{now.strftime('%Y-%m-%d_%H%M')}.xlsx"
        headers = {"Content-Disposition": "attachment; filename=\"export.xlsx\"; filename*=UTF-8''" + urllib.parse.quote(fname)}
        return Response(data, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers=headers)

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        resp = await call_next(request)
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("Content-Security-Policy", "default-src 'self'; frame-ancestors 'none'")
        resp.headers.setdefault("Cache-Control", "no-store")
        return resp

    static_dir = Path(__file__).parent / "static"
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(static_dir / "index.html")

    return app
