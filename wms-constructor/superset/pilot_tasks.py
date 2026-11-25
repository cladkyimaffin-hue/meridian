#!/usr/bin/env python3
"""Проба Superset: дашборд «Задачи склада» из queries/tasks.yaml (наборы данных, диаграммы, дашборд с CSS и баннерами).
Секреты читаются из /opt/wms-constructor-secrets/*.env (значения не выводятся). Запуск: SUPERSET_URL=http://<адрес>:8088 python3 pilot_tasks.py [--rebuild]"""
import json, math, os, re, sys, yaml
from sscli import SS, clean, B

HERE = os.path.dirname(os.path.abspath(__file__))
s = SS()
REBUILD = "--rebuild" in sys.argv
st, r = s.call("GET", "/api/v1/database/")
DB_ID = next(d["id"] for d in r["result"] if d["database_name"] == "LV_MERIDIAN (WMS)")
doc = yaml.safe_load(open(os.path.join(HERE, "..", "queries", "tasks.yaml"), encoding="utf-8"))
Q = {q["id"]: q for q in doc["queries"]}
m = re.fullmatch(r"-(\d+)d", str(doc["variables"]["date_from"].get("default", "")))
DAYS = int(m.group(1)) if m else 30
C1, C2 = "#6C3FB0", "#B08EE3"   # цвета темы «Задачи»
DATE_RE = re.compile(r"([\w\.]+) >= :date_from AND \1 < DATEADD\(day, 1, :date_to\)")


def strip_order(sql):
    """Убирает последний ORDER BY верхнего уровня (в подзапросе SQL Server он запрещён без TOP)."""
    if " TOP " in sql[:80].upper(): return sql
    depth, last, i, instr = 0, -1, 0, False
    up = sql.upper()
    while i < len(sql):
        ch = sql[i]
        if ch == "'": instr = not instr
        elif not instr:
            if ch == "(": depth += 1
            elif ch == ")": depth -= 1
            elif depth == 0 and up.startswith("ORDER BY", i) and (i == 0 or not up[i - 1].isalnum()): last = i
        i += 1
    return sql[:last].rstrip() if last >= 0 else sql


def to_sql(sql):
    sql = " ".join(sql.strip().lstrip(";").rstrip(";").split())
    sql = DATE_RE.sub(lambda m: f"{m.group(1)} >= DATEADD(day, -{DAYS}, CAST(GETDATE() AS date)) AND {m.group(1)} < DATEADD(day, 1, CAST(GETDATE() AS date))", sql)
    return strip_order(sql)


daily = (f"SELECT CAST(tsk_CreateTime AS date) AS [Дата], N'Создано' AS [Показатель], COUNT(*) AS [Задач] FROM dbo.LV_Task "
         f"WHERE tsk_CreateTime >= DATEADD(day, -{DAYS}, CAST(GETDATE() AS date)) GROUP BY CAST(tsk_CreateTime AS date) UNION ALL "
         f"SELECT CAST(tsk_ActualTime AS date), N'Выполнено', COUNT(*) FROM dbo.LV_Task WHERE tsk_ActualTime IS NOT NULL AND "
         f"tsk_ActualTime >= DATEADD(day, -{DAYS}, CAST(GETDATE() AS date)) GROUP BY CAST(tsk_ActualTime AS date)")
DATASETS = {"summary": ("Задачи: сводка", to_sql(Q["tasks.9-1"]["sql"])),
            "types": ("Задачи: по типам и статусам", to_sql(Q["tasks.9-2"]["sql"])),
            "open": ("Задачи: незавершённые и зависшие", to_sql(Q["tasks.9-4"]["sql"])),
            "daily": ("Задачи: создано и выполнено по дням", daily)}

# ---------- очистка при пересборке (дашборды -> диаграммы -> наборы данных)
TITLE = "Задачи склада (проба Superset)"
if REBUILD:
    st, r = s.call("GET", "/api/v1/dashboard/?q=" + json.dumps({"page_size": 100}))
    for d in r.get("result", []):
        if d["dashboard_title"] == TITLE: print("удаляю дашборд", d["id"], s.call("DELETE", f"/api/v1/dashboard/{d['id']}")[0])
    names = {v[0] for v in DATASETS.values()}
    st, r = s.call("GET", "/api/v1/chart/?q=" + json.dumps({"page_size": 200}))
    for c in r.get("result", []):
        if (c.get("datasource_name_text") or "") in names or True:
            if c.get("slice_name"): s.call("DELETE", f"/api/v1/chart/{c['id']}")
st, r = s.call("GET", "/api/v1/dataset/?q=" + json.dumps({"page_size": 200}))
have = {d["table_name"]: d["id"] for d in r.get("result", [])}
ds = {}
for key, (name, sql) in DATASETS.items():
    if name in have and REBUILD:
        s.call("DELETE", f"/api/v1/dataset/{have[name]}"); have.pop(name)
    if name in have:
        ds[key] = have[name]; continue
    st, r = s.call("POST", "/api/v1/dataset/", {"database": DB_ID, "schema": "dbo", "table_name": name, "sql": sql, "owners": [1]})
    print(f"набор «{name}»: HTTP {st}", "" if st < 300 else clean(r)[:300])
    if st < 300: ds[key] = r["id"]
if len(ds) < 4: sys.exit("не все наборы созданы")


def columns(dsid):
    st, r = s.call("GET", f"/api/v1/dataset/{dsid}")
    return [(c["column_name"], str(c.get("type") or "")) for c in r["result"]["columns"]]


# значения сводки (для шкал тахометров)
st, r = s.call("POST", "/api/v1/sqllab/execute/", {"database_id": DB_ID, "sql": DATASETS["summary"][1], "runAsync": False, "schema": "dbo"})
srow = r["data"][0] if st == 200 and r.get("data") else {}
print("сводка:", {k: v for k, v in srow.items()})

BAD = ("ошиб", "зависш", "отрицат", "проблем", "просроч", "застр", "сбой", "ждут", "отклон", "брак", "блокир", "в ожидании", "незаверш", "пуст")
GOOD = ("выполнен", "заверш", "принят", "успеш", "готов", "закрыт")


def nice_max(v):
    t = max(abs(v or 0) * 1.3, 10); mag = 10 ** math.floor(math.log10(t))
    for k in (1, 2, 2.5, 5, 10):
        if k * mag >= t: return int(k * mag)
    return int(10 * mag)


# ---------- дашборд
CSS = """
.dashboard-component-chart-holder{border-radius:16px;box-shadow:0 2px 10px rgba(108,63,176,.18);border:1px solid #E4D9F5;background:#fff}
.dashboard table thead th{background:linear-gradient(90deg,#6C3FB0,#B08EE3)!important;color:#fff!important;font-weight:700}
.dashboard table tbody tr:nth-of-type(even) td{background:#F4EEFC!important}
.dashboard table tbody tr:nth-of-type(odd) td{background:#FFFFFF!important}
.dashboard table tbody tr:hover td{background:#E2D2F7!important}
.dashboard-header-container{background:linear-gradient(90deg,#EFE7FB,#FFFFFF)}
body,.dashboard{background:#F6F2FC}
"""
st, r = s.call("POST", "/api/v1/dashboard/", {"dashboard_title": TITLE, "slug": "tasks-pilot", "published": True, "css": CSS, "owners": [1]})
if st >= 300: sys.exit("дашборд: " + clean(r)[:300])
DASH = r["id"]; print("дашборд создан, id", DASH)


def chart(name, viz, dsid, params):
    params = dict(params); params.update({"viz_type": viz, "datasource": f"{dsid}__table"})
    st, r = s.call("POST", "/api/v1/chart/", {"slice_name": name, "viz_type": viz, "datasource_id": dsid, "datasource_type": "table",
                                               "params": json.dumps(params, ensure_ascii=False), "dashboards": [DASH], "owners": [1]})
    print(f"  диаграмма «{name}» ({viz}): HTTP {st}", "" if st < 300 else clean(r)[:240])
    return r["id"] if st < 300 else None


def metric(col, fn="MAX"):
    return {"expressionType": "SQL", "sqlExpression": f"{fn}([{col}])", "label": col, "hasCustomLabel": True}


gauges = []
for col, typ in columns(ds["summary"]):
    if not any(t in typ.upper() for t in ("INT", "NUM", "DEC", "FLOAT")): continue
    v = srow.get(col) or 0; mx = nice_max(v); a, b = round(mx / 3), round(mx * 2 / 3)
    n = col.lower()
    scheme = "svetofor" if any(w in n for w in BAD) else "svetofor_rev" if any(w in n for w in GOOD) else "t_zadachi"
    cid = chart(col, "gauge_chart", ds["summary"], {
        "metric": metric(col), "groupby": [], "adhoc_filters": [], "row_limit": 10, "min_val": 0, "max_val": mx,
        "start_angle": 225, "end_angle": -45, "color_scheme": scheme, "font_size": 16, "number_format": "SMART_NUMBER",
        "value_formatter": "{value}", "show_pointer": True, "animation": True, "show_axis_tick": False, "show_split_line": False,
        "split_number": 3, "show_progress": True, "overlap": True, "intervals": f"{a},{b},{mx}", "interval_color_indices": "1,2,3"})
    if cid: gauges.append(cid)

tcols = [c for c, _ in columns(ds["types"])]
bar_metrics = [metric(c) for c in tcols[1:3]]
bar = chart("Задачи по типам", "echarts_timeseries_bar", ds["types"], {
    "x_axis": tcols[0], "metrics": bar_metrics, "groupby": [], "adhoc_filters": [], "row_limit": 100, "color_scheme": "t_zadachi",
    "orientation": "vertical", "show_legend": True, "legendType": "scroll", "legendOrientation": "top", "show_value": True,
    "x_axis_sort_asc": True, "xAxisLabelRotation": 0})
line = chart("Создано и выполнено по дням", "echarts_timeseries_line", ds["daily"], {
    "x_axis": "Дата", "metrics": [metric("Задач", "SUM")], "groupby": ["Показатель"], "adhoc_filters": [], "row_limit": 10000,
    "color_scheme": "t_zadachi", "show_legend": True, "legendOrientation": "top", "markerEnabled": True, "markerSize": 6,
    "area": True, "opacity": 0.25, "x_axis_time_format": "smart_date", "time_grain_sqla": "P1D"})
cf = [{"column": c, "operator": ">", "targetValue": 0, "colorScheme": "#DCCBF4"} for c in tcols[2:4]]
tab1 = chart("Задачи по типам и статусам", "table", ds["types"], {
    "query_mode": "raw", "all_columns": tcols, "adhoc_filters": [], "row_limit": 1000, "order_desc": True, "include_search": True,
    "page_length": 10, "show_cell_bars": True, "color_pn": False, "align_pn": False, "conditional_formatting": cf})
ocols = [c for c, _ in columns(ds["open"])]
tab2 = chart("Незавершённые и зависшие задачи", "table", ds["open"], {
    "query_mode": "raw", "all_columns": ocols, "adhoc_filters": [], "row_limit": 1000, "include_search": True, "page_length": 10,
    "show_cell_bars": False, "conditional_formatting": []})

# ---------- раскладка
def banner(text, c1=C1, c2=C2, size=26):
    return ('<div style="background:linear-gradient(90deg,%s,%s);color:#fff;text-align:center;font-size:%dpx;font-weight:700;'
            'letter-spacing:1px;padding:12px 8px;border-radius:14px;box-shadow:0 2px 8px rgba(0,0,0,.15)">%s</div>' % (c1, c2, size, text))

pos = {"DASHBOARD_VERSION_KEY": "v2", "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID", "children": ["GRID_ID"]},
       "GRID_ID": {"type": "GRID", "id": "GRID_ID", "children": [], "parents": ["ROOT_ID"]},
       "HEADER_ID": {"id": "HEADER_ID", "type": "HEADER", "meta": {"text": TITLE}}}
rows = []


def add_row(children):
    rid = f"ROW-{len(rows) + 1}"; rows.append(rid)
    pos[rid] = {"type": "ROW", "id": rid, "children": [c[0] for c in children], "parents": ["ROOT_ID", "GRID_ID"], "meta": {"background": "BACKGROUND_TRANSPARENT"}}
    for cid, typ, meta in children:
        pos[cid] = {"type": typ, "id": cid, "children": [], "parents": ["ROOT_ID", "GRID_ID", rid], "meta": meta}


def md(i, text, size=26, c1=C1, c2=C2, h=9):
    return (f"MARKDOWN-{i}", "MARKDOWN", {"width": 12, "height": h, "code": banner(text, c1, c2, size)})


def ch(cid, name, w, h):
    return (f"CHART-{cid}", "CHART", {"chartId": cid, "width": w, "height": h, "sliceName": name})


add_row([md(1, "Обзор задач", 30, "#4B2A85", "#8A5FD0", 10)])
for i in range(0, len(gauges), 6):
    add_row([ch(c, "Показатель", 2, 34) for c in gauges[i:i + 6]])
add_row([md(2, "Структура и динамика", 24, "#6C3FB0", "#B08EE3", 8)])
add_row([ch(c, n, 6, 48) for c, n in ((bar, "Задачи по типам"), (line, "Создано и выполнено по дням")) if c])
add_row([md(3, "Подробные таблицы", 24, "#6C3FB0", "#B08EE3", 8)])
add_row([ch(c, n, 12, 56) for c, n in ((tab1, "Задачи по типам и статусам"), (tab2, "Незавершённые и зависшие задачи")) if c])
pos["GRID_ID"]["children"] = rows
for cid in [c for c in gauges + [bar, line, tab1, tab2] if c]:
    s.call("PUT", f"/api/v1/chart/{cid}", {"dashboards": [DASH]})
st, rel = s.call("GET", "/api/v1/dashboard/related/roles")
pub = next((o["value"] for o in rel.get("result", []) if o["text"] == "Public"), None)
body = {"position_json": json.dumps(pos, ensure_ascii=False), "published": True,
        "json_metadata": json.dumps({"color_scheme": "t_zadachi", "refresh_frequency": 0, "label_colors": {}})}
if pub: body["roles"] = [pub]
st, r = s.call("PUT", f"/api/v1/dashboard/{DASH}", body)
print("раскладка и роль Public: HTTP", st, "" if st < 300 else clean(r)[:300], "| роль Public id:", pub)
print(f"\nГОТОВО: дашборд {B}/superset/dashboard/{DASH}/  (тахометров {len(gauges)})")
