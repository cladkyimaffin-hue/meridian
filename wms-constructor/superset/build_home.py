#!/usr/bin/env python3
"""Стартовая страница Superset: карточки тем с ссылками на дашборды (slug «home»). Доступные отчёты - ссылки, остальные серые «скоро».
Запуск: SUPERSET_URL=http://<адрес>:8088 python3 build_home.py"""
import json, sys
from sscli import SS, clean, B
import sdesign as D

s = SS()
TITLE, SLUG = "Главная: склад LV_MERIDIAN", "home"
LINK = lambda slug: f"/superset/dashboard/{slug}/?standalone=2"
CARDS = [
    ("Остатки", "Остатки по товарам и зонам, проблемные остатки, места хранения, инвентаризация ячеек.",
     [("Остатки по товарам", None), ("Остатки: проблемные", None), ("Места хранения", None), ("Инвентаризация ячеек", None)]),
    ("Приходы", "Приходы на склад, приёмка, сверка приходов с 1С.", [("Приходы", None), ("Сверка приходов с 1С", None)]),
    ("Расход и заказы", "Заказы и расходные партии.", [("Расход: заказы и партии", None)]),
    ("Задачи", "Задачи склада и нагрузка по исполнителям.", [("Задачи склада", LINK("tasks-pilot")), ("Нагрузка по исполнителям", None)]),
    ("Движение", "Движение товара: операции, ячейки, история по товару.", [("Движение товара", None), ("Движение по товару", None)]),
    ("Обмен с 1С", "Очереди и ошибки обмена, сверка расхода с 1С, маркировка КМ (только счётчики и статусы).",
     [("Обмен с 1С: очереди и ошибки", None), ("Сверка расхода с 1С", None), ("Маркировка КМ", None)]),
]
st, r = s.call("GET", "/api/v1/dashboard/?q=" + json.dumps({"page_size": 100}))
for d in r.get("result", []):
    if d["dashboard_title"] == TITLE: print("удаляю свой прежний дашборд", d["id"], s.call("DELETE", f"/api/v1/dashboard/{d['id']}")[0])
st, r = s.call("POST", "/api/v1/dashboard/", {"dashboard_title": TITLE, "slug": SLUG, "published": True, "css": D.home_css(), "owners": [1]})
if st >= 300: sys.exit("дашборд: " + clean(r)[:300])
DASH = r["id"]
pos = {"DASHBOARD_VERSION_KEY": "v2", "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID", "children": ["GRID_ID"]},
       "GRID_ID": {"type": "GRID", "id": "GRID_ID", "children": [], "parents": ["ROOT_ID"]},
       "HEADER_ID": {"id": "HEADER_ID", "type": "HEADER", "meta": {"text": TITLE}}}
rows = []


def add_row(children):
    rid = f"ROW-{len(rows) + 1}"; rows.append(rid)
    pos[rid] = {"type": "ROW", "id": rid, "children": [c[0] for c in children], "parents": ["ROOT_ID", "GRID_ID"], "meta": {"background": "BACKGROUND_TRANSPARENT"}}
    for cid, typ, meta in children: pos[cid] = {"type": typ, "id": cid, "children": [], "parents": ["ROOT_ID", "GRID_ID", rid], "meta": meta}


def md(i, html, w, h):
    return (f"MARKDOWN-{i}", "MARKDOWN", {"width": w, "height": h, "code": html})


add_row([md(1, D.banner("Склад АО «Меридиан»: отчёты", D.NAVY, back=False, size=32), 12, 10)])
add_row([md(2, '<div style="text-align:center;color:#5B6676;font-size:15px;padding:2px 0">Выберите отчёт. Данные берутся из системы WMS при каждом открытии.</div>', 12, 5)])
for i in range(0, len(CARDS), 3):
    add_row([md(10 + i + j, D.theme_card(t, desc, items), 4, 46) for j, (t, desc, items) in enumerate(CARDS[i:i + 3])])
pos["GRID_ID"]["children"] = rows
st, rel = s.call("GET", "/api/v1/dashboard/related/roles")
pub = next((o["value"] for o in rel.get("result", []) if o["text"] == "Public"), None)
body = {"position_json": json.dumps(pos, ensure_ascii=False), "published": True, "css": D.home_css(), "json_metadata": json.dumps({"refresh_frequency": 0})}
if pub: body["roles"] = [pub]
st, r = s.call("PUT", f"/api/v1/dashboard/{DASH}", body)
print("главная: HTTP", st, "" if st < 300 else clean(r)[:300])
print(f"ГОТОВО: {B}/superset/dashboard/{SLUG}/?standalone=2")
