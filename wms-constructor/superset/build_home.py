"""Стартовая страница-портал Superset (slug «home»).

Единственная точка входа для пользователя: с неё открываются все отчёты, из
отчётов ведёт только кнопка «← Главная». Редакторы и настройки закрыты
прокси `Caddyfile.viewer` (порт 8090) и правами роли Public.

Что создаётся: дашборд «Главная: склад LV_MERIDIAN» из блоков Markdown
(герой, карточки тем, подсказка, подвал). Диаграмм на нём нет — поэтому он
открывается мгновенно и не тратит запросы к WMS.

Готовность отчёта определяется по факту: скрипт спрашивает у Superset список
дашбордов и показывает ссылку только на те, что существуют и опубликованы.
Поэтому «скоро» снимается само, как только отчёт собран.

Запуск на wmssql-analytics:
    docker cp sdesign.py build_home.py superset:/tmp/
    docker exec superset python /tmp/build_home.py
или снаружи: SUPERSET_URL=http://<адрес>:8088 python3 build_home.py
"""

import json
import sys

from sscli import SS, clean, B
import sdesign as D

s = SS()

TITLE = "Главная: склад LV_MERIDIAN"
SLUG = "home"

# (тема, slug отчёта, описание, что внутри)
REPORTS = [
    ("Остатки", "wms-stock-parallel",
     "Сколько чего лежит на складе: по товарам, зонам и местам хранения, с делением на свободный остаток и резерв.",
     "Остатки · зоны · резерв"),
    ("Приходы", "wms-receipts",
     "Приёмка на склад: документы, поставщики, статусы приёмки и расхождение план/факт по строкам.",
     "Документы · поставщики · статусы"),
    ("Расход и заказы", "wms-orders",
     "Отгрузка: заказы клиентам, типы расхода, статусы отбора и что фактически ушло со склада.",
     "Заказы · клиенты · строки"),
    ("Задачи", "tasks-pilot",
     "Работа склада в задачах: сколько выполнено, что зависло и как давно, нагрузка по типам.",
     "Статусы · зависшие · динамика"),
    ("Движение", "wms-movement",
     "Журнал операций: что и куда двигали, кто из сотрудников и в каких зонах.",
     "Операции · зоны · сотрудники"),
]

# (тема, описание) — отчёта ещё нет, карточка серая
SOON = [
    ("Обмен с 1С",
     "Очереди и ошибки обмена с 1С, сверка расхода, счётчики маркировки КМ."),
]

# какие адреса отчётов реально существуют (спрашиваем Superset, а не верим списку)
st, r = s.call("GET", "/api/v1/dashboard/?q=" + json.dumps({"page_size": 100}))
if st >= 300:
    sys.exit("не удалось получить список дашбордов: " + clean(r)[:300])
dash = {d["slug"]: d for d in r.get("result", []) if d.get("slug")}

# пересоздаём только свой дашборд
for d in dash.values():
    if d["dashboard_title"] == TITLE:
        print("удаляю прежнюю главную:", d["id"], s.call("DELETE", f"/api/v1/dashboard/{d['id']}")[0])

ready = []
missing = []
for theme, slug, desc, chips in REPORTS:
    if slug in dash and dash[slug].get("published"):
        ready.append((theme, slug, desc, chips))
    else:
        missing.append(theme)

st, r = s.call("POST", "/api/v1/dashboard/", {
    "dashboard_title": TITLE, "slug": SLUG, "published": True,
    "css": D.portal_css(), "owners": [1],
})
if st >= 300:
    sys.exit("дашборд: " + clean(r)[:300])
DASH = r["id"]

pos = {"DASHBOARD_VERSION_KEY": "v2",
       "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID", "children": ["GRID_ID"]},
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


# --- герой
add_row([md(1, D.hero(
    "Отчёты склада",
    "Пять готовых отчётов по остаткам, приёмке, отгрузке, задачам и движению товара. "
    "Каждый график и таблица живые: нажмите на строку таблицы или на столбец диаграммы — "
    "остальные блоки пересчитаются под выбранное значение.",
), 12, 34)])

# --- карточки: по две в ряд (крупные, читаемые названия)
cards = []
idx = 10
for theme, slug, desc, _chips in ready:
    idx += 1
    cards.append(md(idx, D.portal_card(theme, desc, url=D.DASH(slug)), 6, 34))
for theme, desc in SOON:
    idx += 1
    cards.append(md(idx, D.portal_card(theme, desc, url=None), 6, 34))
for i in range(0, len(cards), 2):
    add_row(cards[i:i + 2])

# --- подсказка
add_row([md(90, D.hint_block(
    "Как читать отчёты: <b>клик по строке таблицы</b> или по столбцу диаграммы фильтрует "
    "остальные блоки этого отчёта; повторный клик по тому же значению снимает фильтр. "
    "Вернуться на эту страницу — кнопка <b>«← Главная»</b> в шапке отчёта. "
    "Количества сравнимы только внутри одной единицы измерения (штука, пара, метр, комплект) — "
    "поэтому на графиках они разделены по единицам."
), 12, 22)])

# --- подвал
add_row([md(99, D.footer_note(
    "Источник: <b>LV_MERIDIAN</b> (WMS) · отчёты строятся на витринах dm_stock, "
    "dm_receipts, dm_orders, dm_movement",
    "Superset 6.1 · просмотр без входа",
), 12, 8)])

pos["GRID_ID"]["children"] = rows

st, rel = s.call("GET", "/api/v1/dashboard/related/roles")
pub = next((o["value"] for o in rel.get("result", []) if o["text"] == "Public"), None)
body = {
    "position_json": json.dumps(pos, ensure_ascii=False),
    "published": True,
    "css": D.portal_css(),
    "json_metadata": json.dumps({"refresh_frequency": 0}),
}
if pub:
    body["roles"] = [pub]
st, r = s.call("PUT", f"/api/v1/dashboard/{DASH}", body)
print("главная: HTTP", st, "" if st < 300 else clean(r)[:300])

print()
print(f"отчётов на портале: {len(ready)}")
for theme, slug, _desc, _chips in ready:
    print(f"  {theme:<18} /superset/dashboard/{slug}/")
for theme in missing:
    print(f"  {theme:<18} НЕ НАЙДЕН дашборд — карточка показана серой")
for theme, _desc in SOON:
    print(f"  {theme:<18} в разработке (карточка «скоро»)")

print()
print(f"ГОТОВО: {B}/superset/dashboard/{SLUG}/?standalone=2")