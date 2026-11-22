#!/usr/bin/env python3
"""Конвертер: Markdown-выгрузка SQL-запросов Grafana -> YAML-описания конструктора (queries/<раздел>.yaml).

Замены макросов Grafana (значения всегда передаются как параметры ?):
  $__timeFilter(X)           -> X >= :date_from AND X < DATEADD(day, 1, :date_to)
  $__timeGroupAlias(X,1d)    -> CAST(X AS date) AS [Дата]
  $__timeGroup(X,1d)         -> CAST(X AS date)
  N${имя:sqlstring}          -> :имя
  $имя / ${имя}              -> :имя   (для переменных дашборда)
Запуск (только чтение исходников): см. docs/CONVERTER.md
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

H_DASH = re.compile(r"^### (\d+)\. (.+?)\s*$")
UID = re.compile(r"uid: `([^`]+)`")
VAR = re.compile(r"^\*\*Переменная `\$(\w+)` \(«([^»]+)»\)")
GROUP = re.compile(r"^#### Раздел: (.+?)\s*$")
Q_HEAD = re.compile(r"^\*\*(\d+)\.(\d+)\. (.+?)\*\* \(([^)]*)\) \*\*\[R\]\*\*\s*$")
BULLET = re.compile(r"^- (Что показывает|Как считается|Примечание): (.*)$")


class Lit(str):
    """Строка, которая выводится в YAML блоком '|'."""


yaml.add_representer(Lit, lambda d, v: d.represent_scalar("tag:yaml.org,2002:str", v, style="|"), Dumper=yaml.SafeDumper)


def norm_sql(sql: str) -> Lit:
    lines = [ln.rstrip().replace("\t", "  ") for ln in sql.strip("\n").split("\n")]
    return Lit("\n".join(lines) + "\n")


def clean_title(t: str) -> str:
    return re.sub(r"\s+", " ", t.replace(" $zone", "").replace("$zone", "")).strip()


def convert_sql(sql: str, var_names: set[str], warn) -> tuple[str, bool]:
    uses_time = False

    def tf(m):
        nonlocal uses_time
        uses_time = True
        x = m.group(1).strip()
        return f"{x} >= :date_from AND {x} < DATEADD(day, 1, :date_to)"

    sql = re.sub(r"\$__timeFilter\(([^()]+)\)", tf, sql)

    def tg(alias: bool):
        def f(m):
            if m.group(2).strip().lower() != "1d":
                warn(f"интервал {m.group(2)} не поддержан: {m.group(0)}")
                return m.group(0)
            x = m.group(1).strip()
            return f"CAST({x} AS date) AS [Дата]" if alias else f"CAST({x} AS date)"
        return f

    sql = re.sub(r"\$__timeGroupAlias\(([^,()]+),([^()]+)\)", tg(True), sql)
    sql = re.sub(r"\$__timeGroup\(([^,()]+),([^()]+)\)", tg(False), sql)
    sql = re.sub(r"N?\$\{(\w+):sqlstring\}", lambda m: f":{m.group(1)}", sql)
    for name in var_names:
        sql = re.sub(r"\$\{" + name + r"\}|\$" + name + r"\b", f":{name}", sql)
    rest = re.findall(r"\$[A-Za-z_{][\w:}]*", sql)
    if rest:
        warn("остались неразобранные макросы: " + ", ".join(sorted(set(rest))))
    return sql, uses_time


def period_days(dash_dir: Path | None, uid: str) -> int:
    if dash_dir:
        for p in dash_dir.glob("*.json"):
            try:
                d = json.loads(p.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if d.get("uid") == uid:
                m = re.fullmatch(r"now-(\d+)([dhwm])", str(d.get("time", {}).get("from", "")))
                if m:
                    n, u = int(m.group(1)), m.group(2)
                    return max(1, n if u == "d" else 1 if u == "h" else n * 7 if u == "w" else n * 30)
    return 30


def parse(md: str, dash_dir: Path | None, warnings: list[str]) -> list[dict]:
    sections: list[dict] = []
    sec = None
    pending = None  # ('var', name) | ('query', dict)
    group = ""
    lines = md.split("\n")
    i = 0
    while i < len(lines):
        ln = lines[i]
        m = H_DASH.match(ln)
        if m:
            title = re.sub(r"\s*\(LV_MERIDIAN\)\s*$", "", m.group(2))
            sec = {"num": m.group(1), "title": title, "uid": "", "variables": {}, "queries": [], "uses_time": False}
            sections.append(sec)
            group, pending = "", None
        elif sec is not None:
            mu = UID.search(ln)
            if mu and not sec["uid"] and ln.startswith("- uid:"):
                sec["uid"] = mu.group(1)
            mv = VAR.match(ln)
            if mv:
                name, label = mv.group(1), mv.group(2)
                if "запрос списка значений" in ln:
                    sec["variables"][name] = {"label": label, "type": "multiselect"}
                    pending = ("var", name)
                else:
                    sec["variables"][name] = {"label": label, "type": "text"}
            mg = GROUP.match(ln)
            if mg:
                group = clean_title(mg.group(1))
            mq = Q_HEAD.match(ln)
            if mq:
                q = {"id": f"{mq.group(1)}-{mq.group(2)}", "title": clean_title(mq.group(3)), "group": group,
                     "kind": mq.group(4), "desc": []}
                sec["queries"].append(q)
                pending = ("query", q)
            mb = BULLET.match(ln)
            if mb and pending and pending[0] == "query":
                pending[1]["desc"].append(f"{mb.group(1)}: {mb.group(2).strip()}")
            if ln.startswith("```sql"):
                j = i + 1
                body = []
                while j < len(lines) and not lines[j].startswith("```"):
                    body.append(lines[j])
                    j += 1
                sql = "\n".join(body)
                i = j
                if pending is None:
                    warnings.append(f"{sec['uid']}: SQL-блок без заголовка (строка {i})")
                elif pending[0] == "var":
                    sec["variables"][pending[1]]["options_sql"] = sql
                    pending = None
                else:
                    pending[1]["raw_sql"] = sql
                    pending = None
        i += 1
    for s in sections:
        s["period_days"] = period_days(dash_dir, s["uid"])
    return sections


def build_yaml(sec: dict, warnings: list[str]) -> dict:
    key = sec["uid"].removeprefix("wms-")
    var_names = set(sec["variables"])
    variables: dict = {}
    for name, v in sec["variables"].items():
        item = {"label": v["label"], "type": v["type"]}
        if v.get("options_sql"):
            item["options_sql"] = norm_sql(v["options_sql"])
        variables[name] = item
    queries = []
    for q in sec["queries"]:
        if "raw_sql" not in q:
            warnings.append(f"{sec['uid']} {q['id']}: нет SQL-блока")
            continue

        def warn(msg, _id=q["id"]):
            warnings.append(f"{sec['uid']} {_id}: {msg}")

        sql, uses_time = convert_sql(q["raw_sql"], var_names, warn)
        sec["uses_time"] = sec["uses_time"] or uses_time or "date_from" in sql
        queries.append({
            "id": f"{key}.{q['id']}",
            "title": q["title"],
            "group": q["group"],
            "kind": q["kind"],
            "description": Lit("\n".join(q["desc"]) + "\n") if q["desc"] else "",
            "sql": norm_sql(sql),
        })
    if sec["uses_time"]:
        variables["date_from"] = {"label": "С даты", "type": "date", "default": f"-{sec['period_days']}d"}
        variables["date_to"] = {"label": "По дату", "type": "date"}
    return {"section": key, "title": sec["title"], "source_dashboard": sec["uid"], "variables": variables, "queries": queries}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", required=True, help="Markdown-файл с запросами")
    ap.add_argument("--dashboards", help="папка с JSON дашбордов (для периода по умолчанию), только чтение")
    ap.add_argument("--out", default="queries", help="куда писать YAML")
    a = ap.parse_args()

    warnings: list[str] = []
    sections = parse(Path(a.md).read_text(encoding="utf-8"), Path(a.dashboards) if a.dashboards else None, warnings)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    total_q = total_opts = 0
    for sec in sections:
        if not sec["uid"]:
            warnings.append(f"дашборд {sec['num']} {sec['title']}: нет uid, пропущен")
            continue
        doc = build_yaml(sec, warnings)
        (out / f"{doc['section']}.yaml").write_text(
            yaml.dump(doc, Dumper=yaml.SafeDumper, allow_unicode=True, sort_keys=False, width=1000), encoding="utf-8")
        total_q += len(doc["queries"])
        total_opts += sum(1 for v in doc["variables"].values() if v.get("options_sql"))
        print(f"{doc['section']:28} запросов: {len(doc['queries']):2}  переменных: {list(doc['variables'])}")
    print(f"\nИтого: разделов {len(sections)}, запросов {total_q}, запросов списков значений {total_opts} (всего SQL: {total_q + total_opts})")
    for w in warnings:
        print("ПРЕДУПРЕЖДЕНИЕ:", w)
    return 0


if __name__ == "__main__":
    sys.exit(main())
