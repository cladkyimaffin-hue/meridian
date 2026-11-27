#!/usr/bin/env python3
"""Стартовая страница Superset: карточки тем с ссылками на дашборды (slug «home»).

Оформление — прежнее, принятое владельцем: баннер «Склад АО «Меридиан»: отчёты»,
строка-подсказка и карточки по три в ряд, внутри карточки — кнопки-ссылки на
отчёты темы. Недоступные отчёты показываются серыми с пометкой «(скоро)».

Готовность отчёта определяется по факту: скрипт спрашивает у Superset список
дашбордов и делает ссылкой только те адреса, что существуют и опубликованы.
Поэтому «скоро» снимается само, как только отчёт собран.

Запуск на wmssql-analytics:
    docker cp sdesign.py build_home.py superset:/tmp/
    docker exec superset python /tmp/build_home.py
или снаружи: SUPERSET_URL=http://<адрес>:8088 python3 build_home.py
"""
import json, sys

from sscli import SS, clean, B
import sdesign as D

s = SS()
TITLE, SLUG = "Главная: склад LV_MERIDIAN", "home"
LINK = lambda slug: f"/superset/dashboard/{slug}/?standalone=2"

# тема -> (описание, [(название отчёта, slug дашборда)])
CARDS = [
    ("Остатки", "Остатки по товарам и зонам, проблемные остатки, места хранения, инвентаризация ячеек.",
     [("Остатки по товарам", "wms-stock-parallel"), ("Остатки: проблемные", "wms-stock-issues"),
      ("Места хранения", "wms-places"), ("Инвентаризация ячеек", "wms-inventory")]),
    ("Приходы", "Приходы на склад, приёмка, сверка приходов с 1С.",
     [("Приходы", "wms-receipts"), ("Сверка приходов с 1С", "wms-reconcile-receipts")]),
    ("Расход и заказы", "Заказы и расходные партии.",
     [("Расход: заказы и партии", "wms-orders")]),
    ("Задачи", "Задачи склада и нагрузка по исполнителям.",
     [("Задачи склада", "tasks-pilot"), ("Нагрузка по исполнителям", "wms-staff-workload")]),
    ("Движение", "Движение товара: операции, ячейки, история по товару.",
     [("Движение товара", "wms-movement"), ("Движение по товару", "wms-product-movement")]),
    ("Обмен с 1С", "Очереди и ошибки обмена, сверка расхода с 1С, маркировка КМ (только счётчики и статусы).",
     [("Обмен с 1С: очереди и ошибки", "wms-exchange"), ("Сверка расхода с 1С", "wms-reconcile-orders"),
      ("Маркировка КМ", "wms-km")]),
]

# какие адреса отчётов реально существуют (спрашиваем Superset, а не верим списку)
st, r = s.call("GET", "/api/v1/dashboard/?q=" + json.dumps({"page_size": 100}))
if st >= 300:
    sys.exit("список дашбордов: " + clean(r)[:300])
dash = {d["slug"]: d for d in r.get("result", []) if d.get("slug")}


def url_for(slug):
    """Ссылка на отчёт, если дашборд существует и опубликован; иначе None."""
    if not slug:
        return None
    d = dash.get(slug)
    return LINK(slug) if d and d.get("published") else None


for d in dash.values():
    if d["dashboard_title"] == TITLE:
        print("удаляю свой прежний дашборд", d["id"], s.call("DELETE", f"/api/v1/dashboard/{d['id']}")[0])

st, r = s.call("POST", "/api/v1/dashboard/", {"dashboard_title": TITLE, "slug": SLUG,
                                             "published": True, "css": D.home_css(), "owners": [1]})
if st >= 300:
    sys.exit("дашборд: " + clean(r)[:300])
DASH = r["id"]

pos = {"DASHBOARD_VERSION_KEY": "v2", "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID", "children": ["GRID_ID"]},
       "GRID_ID": {"type": "GRID", "id": "GRID_ID", "children": [], "parents": ["ROOT_ID"]},
       "HEADER_ID": {"id": "HEADER_ID", "type": "HEADER", "meta": {"text": TITLE}}}
rows = []


def add_row(children):
    rid = f"ROW-{len(rows) + 1}"
    rows.append(rid)
    pos[rid] = {"type": "ROW", "id": rid, "children": [c[0] for c in children],
                "parents": ["ROOT_ID", "GRID_ID"], "meta": {"background": "BACKGROUND_TRANSPARENT"}}
    for cid, typ, meta in children:
        pos[cid] = {"type": typ, "id": cid, "children": [],
                    "parents": ["ROOT_ID", "GRID_ID", rid], "meta": meta}


def md(i, html, w, h):
    return (f"MARKDOWN-{i}", "MARKDOWN", {"width": w, "height": h, "code": html})


def card_html(theme, desc, items):
    """Карточка темы; отчёт без ссылки показывается серым «(скоро)»."""
    prepared = [(title, url_for(slug)) for title, slug in items]
    return D.theme_card(theme, desc, prepared)


add_row([md(1, D.banner("Склад АО «Меридиан»: отчёты", D.NAVY, back=False, size=32), 12, 10)])
add_row([md(2, '<div style="text-align:center;color:#5B6676;font-size:15px;padding:2px 0">'
               'Выберите отчёт. Данные берутся из системы WMS при каждом открытии.</div>', 12, 5)])
for i in range(0, len(CARDS), 3):
    add_row([md(10 + i + j, card_html(t, desc, items), 4, 46)
             for j, (t, desc, items) in enumerate(CARDS[i:i + 3])])

pos["GRID_ID"]["children"] = rows

st, rel = s.call("GET", "/api/v1/dashboard/related/roles")
pub = next((o["value"] for o in rel.get("result", []) if o["text"] == "Public"), None)
body = {"position_json": json.dumps(pos, ensure_ascii=False), "published": True,
        "css": D.home_css(), "json_metadata": json.dumps({"refresh_frequency": 0})}
if pub:
    body["roles"] = [pub]
st, r = s.call("PUT", f"/api/v1/dashboard/{DASH}", body)
print("главная: HTTP", st, "" if st < 300 else clean(r)[:300])

print()
for theme, _desc, items in CARDS:
    for title, slug in items:
        state = "ссылка" if url_for(slug) else "скоро"
        print(f"  {title:<32} {state}")
print(f"\nГОТОВО: {B}/superset/dashboard/{SLUG}/?standalone=2")
