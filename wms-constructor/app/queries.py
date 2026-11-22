"""Описания запросов (YAML), проверка SQL и подстановка параметров.

Правила безопасности:
* выполняются только запросы из каталога queries/ (произвольный SQL от пользователя не принимается);
* SQL должен начинаться с SELECT или WITH, без второго оператора и без изменяющих ключевых слов;
* значения параметров передаются только как параметры ODBC (?), в текст SQL не подставляются.
"""
from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml


class QueryError(ValueError):
    """Ошибка описания запроса или параметров."""


# Строковые литералы, [идентификаторы] и комментарии. При split() чётные элементы - код, нечётные - всё остальное.
_TOKEN = re.compile(r"('(?:[^']|'')*'|\[[^\]]*\]|--[^\n]*|/\*.*?\*/)", re.S)
_PLACEHOLDER = re.compile(r"(?<![:\w]):([A-Za-z_]\w*)")
_FORBIDDEN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|MERGE|DROP|ALTER|CREATE|TRUNCATE|EXEC|EXECUTE|GRANT|REVOKE|DENY|"
    r"BACKUP|RESTORE|SHUTDOWN|RECONFIGURE|OPENROWSET|OPENQUERY|OPENDATASOURCE|BULK|INTO|WAITFOR|KILL|DBCC)\b",
    re.I,
)
_SYSPROC = re.compile(r"\b(xp|sp)_\w*", re.I)

BUILTIN_DATE_VARS = {"date_from": "С даты", "date_to": "По дату"}
MAX_TEXT_LEN = 200
MAX_LIST_ITEMS = 500


def _code_only(sql: str) -> str:
    parts = _TOKEN.split(sql)
    return " ".join(p for i, p in enumerate(parts) if i % 2 == 0)


def validate_sql(sql: str) -> None:
    """Бросает QueryError, если SQL не является одиночным читающим запросом."""
    code = _code_only(sql).strip().rstrip(";").strip()
    if not re.match(r"(SELECT|WITH)\b", code, re.I):
        raise QueryError("SQL должен начинаться с SELECT или WITH")
    if ";" in code:
        raise QueryError("допускается только один оператор (найдена ';')")
    m = _FORBIDDEN.search(code)
    if m:
        raise QueryError(f"запрещённое ключевое слово: {m.group(1).upper()}")
    if _SYSPROC.search(code):
        raise QueryError("системные процедуры (xp_/sp_) запрещены")


def placeholders(sql: str) -> list[str]:
    """Имена :параметров в порядке первого появления (только в коде, не в литералах и комментариях)."""
    seen: list[str] = []
    parts = _TOKEN.split(sql)
    for i in range(0, len(parts), 2):
        for m in _PLACEHOLDER.finditer(parts[i]):
            if m.group(1) not in seen:
                seen.append(m.group(1))
    return seen


@dataclass
class Variable:
    name: str
    label: str
    type: str = "text"  # text | multiselect | date
    options_sql: str | None = None
    options: list[dict] | None = None
    default: object | None = None


@dataclass
class Query:
    id: str
    section: str
    title: str
    group: str
    kind: str
    description: str
    sql: str
    params: list[str]


@dataclass
class Section:
    key: str
    title: str
    source_dashboard: str
    variables: dict[str, Variable]
    queries: list[Query] = field(default_factory=list)


@dataclass
class Registry:
    sections: list[Section]
    queries: dict[str, Query]

    def section_of(self, q: Query) -> Section:
        return next(s for s in self.sections if s.key == q.section)

    def menu(self) -> list[dict]:
        out = []
        for s in self.sections:
            groups: dict[str, list[dict]] = {}
            for q in s.queries:
                groups.setdefault(q.group or "Прочее", []).append(
                    {"id": q.id, "title": q.title, "kind": q.kind}
                )
            out.append(
                {
                    "key": s.key,
                    "title": s.title,
                    "groups": [{"title": g, "queries": qs} for g, qs in groups.items()],
                }
            )
        return out


def _parse_variable(name: str, raw: dict) -> Variable:
    vtype = raw.get("type", "text")
    if vtype not in ("text", "multiselect", "date"):
        raise QueryError(f"переменная {name}: неизвестный тип {vtype!r}")
    if raw.get("options_sql"):
        validate_sql(raw["options_sql"])
    return Variable(
        name=name,
        label=raw.get("label", name),
        type=vtype,
        options_sql=raw.get("options_sql"),
        options=raw.get("options"),
        default=raw.get("default"),
    )


def load_registry(directory: str | Path) -> Registry:
    base = Path(directory)
    errors: list[str] = []
    sections: list[Section] = []
    queries: dict[str, Query] = {}

    for path in sorted(base.glob("*.yaml")):
        try:
            doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            key = doc["section"]
            variables = {n: _parse_variable(n, v or {}) for n, v in (doc.get("variables") or {}).items()}
            section = Section(key, doc.get("title", key), doc.get("source_dashboard", ""), variables)
            for item in doc.get("queries") or []:
                qid = item["id"]
                try:
                    sql = item["sql"]
                    validate_sql(sql)
                    used = placeholders(sql)
                    for name in used:
                        if name in variables:
                            continue
                        if name in BUILTIN_DATE_VARS:
                            variables[name] = Variable(name, BUILTIN_DATE_VARS[name], "date")
                        else:
                            raise QueryError(f"параметр :{name} не описан в variables")
                    declared = item.get("params")
                    if declared is not None and set(declared) != set(used):
                        raise QueryError(f"params {sorted(declared)} не совпадают с используемыми {sorted(used)}")
                    if qid in queries:
                        raise QueryError("повторяющийся id")
                    q = Query(
                        id=qid,
                        section=key,
                        title=item["title"],
                        group=item.get("group", ""),
                        kind=item.get("kind", ""),
                        description=(item.get("description") or "").strip(),
                        sql=sql,
                        params=used,
                    )
                    section.queries.append(q)
                    queries[qid] = q
                except (QueryError, KeyError) as exc:
                    errors.append(f"{path.name}: запрос {qid}: {exc}")
            sections.append(section)
        except (QueryError, KeyError, yaml.YAMLError) as exc:
            errors.append(f"{path.name}: {exc}")

    if errors:
        raise QueryError("Ошибки в описаниях запросов:\n" + "\n".join(errors))
    return Registry(sections, queries)


def _coerce(var: Variable, value):
    if var.type == "text":
        s = "" if value is None else str(value).strip()
        if len(s) > MAX_TEXT_LEN:
            raise QueryError(f"{var.label}: слишком длинное значение (максимум {MAX_TEXT_LEN})")
        return s
    if var.type == "date":
        if value in (None, ""):
            value = var.default
        if value in (None, ""):
            today = dt.date.today()
            return today if var.name == "date_to" else today - dt.timedelta(days=30)
        try:
            return dt.date.fromisoformat(str(value))
        except ValueError:
            raise QueryError(f"{var.label}: ожидается дата ГГГГ-ММ-ДД")
    # multiselect
    if value is None:
        return []
    if not isinstance(value, list):
        raise QueryError(f"{var.label}: ожидается список значений")
    if len(value) > MAX_LIST_ITEMS:
        raise QueryError(f"{var.label}: слишком много значений (максимум {MAX_LIST_ITEMS})")
    return [str(v) for v in value]


def bind(query: Query, variables: dict[str, Variable], raw: dict) -> tuple[str, list]:
    """Возвращает (SQL с ?, список значений) в порядке появления параметров."""
    args: list = []
    parts = _TOKEN.split(query.sql)

    def repl(m: re.Match) -> str:
        var = variables[m.group(1)]
        val = _coerce(var, raw.get(var.name))
        if var.type == "multiselect":
            if not val:
                return "NULL"  # пустой выбор: IN (NULL) ничего не вернёт
            args.extend(val)
            return ",".join("?" * len(val))
        args.append(val)
        return "?"

    for i in range(0, len(parts), 2):
        parts[i] = _PLACEHOLDER.sub(repl, parts[i])
    if len(args) > 2000:
        raise QueryError("слишком много параметров для одного запроса")
    return "".join(parts), args
