#!/usr/bin/env python3
"""Шапка-навигация в каждом отчёте: баннер с названием и кнопкой «← Главная».

Зачем отдельный скрипт: дашборды собираются своими построителями, и каждый
раз вставлять баннер в трёх местах — лишний риск. Здесь это делается один раз
для всех отчётов сразу и идемпотентно.

Что делает для каждого отчёта из MAP:
  1. ставит в раскладку первую строку с Markdown-баннером:
     название отчёта + кнопка «← Главная» (ведёт на портал);
  2. применяет CSS темы — он же скрывает верхнее меню Superset и служебную
     шапку дашборда, чтобы у пользователя не было других путей, кроме
     портала и ссылок внутри отчёта.

Повторный запуск обновляет баннер и CSS, а не добавляет второй.

Запуск на wmssql-analytics:
    docker cp sdesign.py apply_portal_chrome.py superset:/tmp/
    docker exec superset python /tmp/apply_portal_chrome.py
или снаружи: SUPERSET_URL=http://<адрес>:8088 python3 apply_portal_chrome.py
"""

import json
import sys

from sscli import SS, clean, B
import sdesign as D

# slug отчёта -> тема оформления
MAP = {
    "wms-stock-parallel": "Остатки",
    "wms-receipts": "Приходы",
    "wms-orders": "Расход и заказы",
    "tasks-pilot": "Задачи",
    "wms-movement": "Движение",
    "wms-exchange": "Обмен с 1С",
}

BANNER_ID = "MARKDOWN-NAVBAR"
BANNER_ROW = "ROW-NAVBAR"

s = SS()

st, r = s.call("GET", "/api/v1/dashboard/?q=" + json.dumps({"page_size": 100}))
if st >= 300:
    sys.exit("список дашбордов: " + clean(r)[:300])
by_slug = {d["slug"]: d for d in r.get("result", []) if d.get("slug")}


def put_banner(slug, theme):
    dash = by_slug.get(slug)
    if dash is None:
        print(f"  {slug}: дашборда нет, пропускаю")
        return False

    st, full = s.call("GET", f"/api/v1/dashboard/{dash['id']}")
    if st >= 300:
        print(f"  {slug}: не прочитался ({st})")
        return False
    # API отдаёт объект в обёртке {"result": {...}}
    full = full.get("result") or {}

    pos = json.loads(full.get("position_json") or "{}")
    if not pos:
        print(f"  {slug}: пустая раскладка, пропускаю")
        return False

    title = full.get("dashboard_title") or theme
    colors = D.THEMES[theme]

    pos[BANNER_ID] = {
        "type": "MARKDOWN",
        "id": BANNER_ID,
        "children": [],
        "parents": ["ROOT_ID", "GRID_ID", BANNER_ROW],
        "meta": {"width": 12, "height": 8, "code": D.banner(title, colors, back=True, size=26)},
    }
    pos[BANNER_ROW] = {
        "type": "ROW",
        "id": BANNER_ROW,
        "children": [BANNER_ID],
        "parents": ["ROOT_ID", "GRID_ID"],
        "meta": {"background": "BACKGROUND_TRANSPARENT"},
    }

    grid = pos.get("GRID_ID") or {}
    children = [c for c in (grid.get("children") or []) if c != BANNER_ROW]
    grid["children"] = [BANNER_ROW] + children
    pos["GRID_ID"] = grid

    body = {
        "position_json": json.dumps(pos, ensure_ascii=False),
        "css": D.dashboard_css(theme),
    }
    st, res = s.call("PUT", f"/api/v1/dashboard/{dash['id']}", body)
    ok = st < 300
    print(f"  {slug}: {'баннер и оформление обновлены' if ok else 'ОШИБКА ' + clean(res)[:200]}")
    return ok


print("шапка с кнопкой «← Главная»:")
done = 0
for slug, theme in MAP.items():
    if put_banner(slug, theme):
        done += 1

print()
print(f"обновлено отчётов: {done} из {len(MAP)}")
print(f"портал: {B}/superset/dashboard/home/?standalone=2")
