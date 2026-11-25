#!/usr/bin/env python3
"""Строит в Metabase коллекции, модели, карточки и дашборды из queries/*.yaml.

Темы -> коллекции; раздел (бывший дашборд Grafana) -> дашборд; запрос -> карточка:
  сводка без параметров -> модель + числовые плитки (по одной на столбец);
  таблица -> модель (если её можно использовать как источник) или вопрос; 2 столбца (категория, число) -> столбики/кольцо;
  timeseries -> линейный график.
Параметры: период -> число «За сколько дней» (окно до сегодняшнего дня), зона и товар -> текстовые фильтры.
Ключ API: /opt/wms-constructor-secrets/metabase-api.env (значение не выводится).
Запуск: METABASE_URL=http://<адрес>:3001 python3 build_content.py [--rebuild]
--rebuild: переносит прежнюю корневую коллекцию в корзину Metabase (восстановимо) и строит заново.
"""
import argparse, base64, glob, json, math, os, re, sys, urllib.error, urllib.request, uuid
from xml.sax.saxutils import escape as xesc
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
QDIR = os.path.join(HERE, "..", "queries")
KEYFILE = "/opt/wms-constructor-secrets/metabase-api.env"
DB_NAME = "LV_MERIDIAN (WMS)"
ROOT = "LV_MERIDIAN: отчёты по складу"
THEMES = [
    ("Остатки", "Остатки по товарам и зонам, проблемные остатки, места хранения, инвентаризация ячеек.",
     ["stock-products", "stock-issues", "places", "inventory"]),
    ("Приходы", "Приходы на склад, приёмка, сверка приходов с 1С.", ["receipts", "reconcile-receipts"]),
    ("Расход и заказы", "Заказы и расходные партии.", ["orders"]),
    ("Задачи", "Задачи склада и нагрузка по исполнителям.", ["tasks", "staff-workload"]),
    ("Движение", "Движение товара: операции, ячейки, история по товару.", ["movement", "product-movement"]),
    ("Обмен с 1С", "Очереди и ошибки обмена, сверка расхода с 1С, маркировка КМ (только счётчики и статусы).",
     ["exchange", "reconcile-orders", "km"]),
]
NUM_TYPES = {"type/Integer", "type/BigInteger", "type/Decimal", "type/Float", "type/Number"}
DATE_RE = re.compile(r"([\w\.]+) >= :date_from AND \1 < DATEADD\(day, 1, :date_to\)")
ZONE_RE = re.compile(r"(ISNULL\(z\.zon_code, N'-'\)|z\.zon_code) IN \(:zone\)")
TOVAR_RE = re.compile(r"\(:tovar=N'' OR p\.prd_PrimaryCode LIKE N'%'\+:tovar\+N'%' OR pn\.d LIKE N'%'\+:tovar\+N'%'\)")
PARAM_NAMES = {"days": ("За сколько дней", "number"), "zone": ("Зона (код)", "text"), "tovar": ("Товар (код или часть названия)", "text")}


THEME_COLORS = {  # (тёмный, светлый) для градиентов баннеров, графиков и тахометров
    "Остатки": ("#2D6CB5", "#6FB1F0"), "Приходы": ("#2E8B3E", "#7CCB80"), "Расход и заказы": ("#D9730D", "#F7B05E"),
    "Задачи": ("#6C3FB0", "#B08EE3"), "Движение": ("#13867F", "#5CCBC2"), "Обмен с 1С": ("#B23A48", "#EE8497"),
}
BAD_WORDS = ("ошиб", "зависш", "отрицат", "непригод", "расхожд", "проблем", "просроч", "застр", "зацикл", "дубл", "сбой",
             "недостач", "нет в ", "без ", "не найден", "не сопостав", "ждут", "очеред", "отклон", "брак", "блокир", "пуст")
GOOD_WORDS = ("выполнен", "заверш", "принят", "отгруж", "обработан", "успеш", "сопостав", "подтвержд", "готов", "закрыт")


def blend(hexc, t):
    """Смешивает цвет с белым: t=0 исходный, t=1 белый."""
    h = hexc.lstrip("#"); r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return "#%02X%02X%02X" % tuple(round(c + (255 - c) * t) for c in (r, g, b))


def metric_kind(name):
    n = name.lower()
    if any(w in n for w in BAD_WORDS): return "bad"
    if any(w in n for w in GOOD_WORDS): return "good"
    return "neutral"


def nice_max(v):
    v = abs(v or 0); target = max(v * 1.3, 10)
    mag = 10 ** math.floor(math.log10(target))
    for m in (1, 2, 2.5, 5, 10):
        if m * mag >= target: return int(m * mag)
    return int(10 * mag)


def gauge_viz(value, name, theme):
    kind = metric_kind(name); c1, c2 = THEME_COLORS[theme]
    cols = {"good": ["#ED6E6E", "#F9CF48", "#84BB4C"], "bad": ["#84BB4C", "#F9CF48", "#ED6E6E"],
            "neutral": [blend(c2, 0.55), c2, c1]}[kind]
    mx = nice_max(value); a, b = round(mx / 3), round(mx * 2 / 3)
    segs = [{"min": 0, "max": a, "color": cols[0], "label": ""}, {"min": a, "max": b, "color": cols[1], "label": ""},
            {"min": b, "max": mx, "color": cols[2], "label": ""}]
    return {"gauge.segments": segs}


def banner_md(text, c1, c2, h=84, size=0.5, w=1200):
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" preserveAspectRatio="xMidYMid meet">'
           '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="%s"/><stop offset="1" stop-color="%s"/></linearGradient></defs>'
           '<rect width="%d" height="%d" rx="14" fill="url(#g)"/>'
           '<text x="%d" y="%d" font-family="Lato, Segoe UI, Arial, sans-serif" font-size="%d" font-weight="700" letter-spacing="1" text-anchor="middle" fill="#FFFFFF">%s</text></svg>'
           ) % (w, h, c1, c2, w, h, w // 2, round(h * 0.66), round(h * size), xesc(text))
    return "![](data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode() + ")"


ID_HINTS = ("код", "id", "номер", "№", "штрих", "uid", "guid", "sscc", "партия")
STATUS_HINTS = ("статус", "состояни", "результат", "причина", "ошибк")


def table_viz(cols, rows, theme):
    """Цветные шкалы в числовых столбцах и подсветка проблемных статусов (зебры в Metabase нет)."""
    c1, c2 = THEME_COLORS[theme]; rules = []; rid = 0
    for i, c in enumerate(cols):
        nm = c["name"].lower()
        if len(cols) > 14: break
        if c.get("base_type") in NUM_TYPES and not any(h in nm for h in ID_HINTS):
            vals = [r[i] for r in rows if r[i] is not None]
            if vals and max(vals) != min(vals):
                rid += 1
                rules.append({"id": rid, "columns": [c["name"]], "type": "range", "colors": ["#FFFFFF", blend(c2, 0.35)],
                              "min_type": None, "max_type": None, "min_value": 0, "max_value": 100})
        elif c.get("base_type") == "type/Text" and any(h in nm for h in STATUS_HINTS):
            for word, color in (("ошиб", "#F8C9C9"), ("зависш", "#F8C9C9"), ("не найден", "#F8C9C9"), ("заверш", "#CDEBD0"), ("выполнен", "#CDEBD0"), ("успеш", "#CDEBD0")):
                rid += 1
                rules.append({"id": rid, "columns": [c["name"]], "type": "single", "operator": "contains", "value": word,
                              "color": color, "highlight_row": False})
    return {"table.column_formatting": rules} if rules else {}


def series_color_viz(base, metrics, theme):
    c1, c2 = THEME_COLORS[theme]
    base = dict(base)
    base["series_settings"] = {m: {"color": (c1 if i % 2 == 0 else c2)} for i, m in enumerate(metrics)}
    return base


def convert(sql):
    sql = sql.strip().lstrip(";").strip().rstrip(";")
    sql = DATE_RE.sub(lambda m: m.group(1) + " >= DATEADD(day, -{{days}}, CAST(GETDATE() AS date)) AND " + m.group(1)
                      + " < DATEADD(day, 1, CAST(GETDATE() AS date))", sql)
    sql = ZONE_RE.sub(lambda m: "(1=1 [[AND " + m.group(1) + " = {{zone}}]])", sql)
    sql = TOVAR_RE.sub(lambda m: "(1=1 [[AND (p.prd_PrimaryCode LIKE N'%'+{{tovar}}+N'%' OR pn.d LIKE N'%'+{{tovar}}+N'%')]])", sql)
    left = re.findall(r"(?<![:\w]):[A-Za-z_]\w*", re.sub(r"'(?:[^']|'')*'", "''", sql))
    if left:
        raise ValueError("остались параметры: " + ",".join(sorted(set(left))))
    return sql


def tags_of(sql, days_default):
    tags = {}
    for name in dict.fromkeys(re.findall(r"\{\{(\w+)\}\}", sql)):
        label, ttype = PARAM_NAMES[name]
        t = {"id": str(uuid.uuid4()), "name": name, "display-name": label, "type": ttype, "required": False}
        if name == "days":
            t["default"] = days_default
        tags[name] = t
    return tags


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rebuild", action="store_true")
    a = ap.parse_args()
    base = os.environ.get("METABASE_URL") or sys.exit("задайте METABASE_URL=http://<адрес>:3001")
    key = [l.split("=", 1)[1].strip() for l in open(KEYFILE, encoding="utf-8") if l.startswith("METABASE_API_KEY=")][0]

    def call(method, path, body=None, t=180):
        req = urllib.request.Request(base + path, method=method, data=(json.dumps(body).encode() if body is not None else None),
                                     headers={"x-api-key": key, "Content-Type": "application/json"})
        try:
            r = urllib.request.urlopen(req, timeout=t)
            raw = r.read()
            return r.status, (json.loads(raw) if raw else None)
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8", "replace")
            try:
                return e.code, json.loads(raw)
            except Exception:
                return e.code, raw[:300]
        except Exception as e:
            return 0, str(e)[:200]

    st, dbs = call("GET", "/api/database")
    db_id = next(d["id"] for d in dbs.get("data", dbs) if d["name"] == DB_NAME)
    st, items = call("GET", "/api/collection/root/items?models=collection")
    existing = [i for i in (items.get("data", items) if isinstance(items, dict) else items) if i.get("name") == ROOT]
    if existing:
        if not a.rebuild:
            sys.exit(f"коллекция «{ROOT}» уже есть (id {existing[0]['id']}); для пересборки добавьте --rebuild")
        print("прежняя коллекция в корзину:", call("PUT", f"/api/collection/{existing[0]['id']}", {"archived": True})[0])
    st, root = call("POST", "/api/collection", {"name": ROOT, "description": "Отчёты и дашборды по складу LV_MERIDIAN (создано автоматически из queries/*.yaml; только чтение)."})
    root_id = root["id"]
    print("публичный доступ включён:", call("PUT", "/api/setting/enable-public-sharing", {"value": True})[0])

    sections = {}
    for p in sorted(glob.glob(os.path.join(QDIR, "*.yaml"))):
        d = yaml.safe_load(open(p, encoding="utf-8")); sections[d["section"]] = d

    public = {}      # id дашборда -> uuid публичной ссылки
    sec_public = {}  # ключ раздела -> uuid

    def publish(did):
        st, r = call("POST", f"/api/dashboard/{did}/public_link", {})
        return r.get("uuid") if st < 300 and isinstance(r, dict) else None

    stats = {"cards": 0, "models": 0, "gauges": 0, "charts": 0, "fail": []}
    content = {"root": root_id, "themes": {}}
    dash_info = {}   # theme -> [(title, id)]
    kpis = []        # (theme, card_id, name)

    def make_card(name, desc, coll, dq, display="table", viz=None, ctype="question"):
        st, r = call("POST", "/api/card", {"name": name, "description": desc or None, "collection_id": coll, "type": ctype,
                                           "display": display, "visualization_settings": viz or {}, "dataset_query": dq})
        return (r["id"] if st < 300 else None), (r if st >= 300 else None)

    TXT = {"text.align_horizontal": "center", "text.align_vertical": "middle", "dashcard.background": False}

    def new_layout():
        L = {"dcs": [], "nid": 0}

        def add(card_id, c, r, w, h, viz=None, maps=None):
            L["nid"] -= 1
            L["dcs"].append({"id": L["nid"], "card_id": card_id, "row": r, "col": c, "size_x": w, "size_y": h,
                             "visualization_settings": viz or {}, "parameter_mappings": maps or []})

        def banner(md, r, h=2, w=24, c=0):
            v = {"virtual_card": {"name": None, "display": "text", "archived": False}, "text": md}; v.update(TXT)
            add(None, c, r, w, h, v)
        return L, add, banner

    for theme, tdesc, keys in THEMES:
        tc1, tc2 = THEME_COLORS[theme]
        st, coll = call("POST", "/api/collection", {"name": theme, "description": tdesc, "parent_id": root_id})
        cid_coll = coll["id"]
        content["themes"][theme] = {"collection": cid_coll, "dashboards": {}}
        dash_info[theme] = []
        for key_s in keys:
            sec = sections.get(key_s)
            if not sec:
                stats["fail"].append(f"{key_s}: нет YAML"); continue
            short = sec["title"].split(":")[0].strip()
            days_default = 30
            dd = (sec.get("variables") or {}).get("date_from", {}).get("default")
            m = re.fullmatch(r"-(\d+)d", str(dd or ""))
            if m: days_default = int(m.group(1))
            blocks, used_tags = [], set()
            for q in sec["queries"]:
                qid, title, kind = q["id"], q["title"], q.get("kind", "")
                try:
                    sql = convert(q["sql"])
                except ValueError as e:
                    stats["fail"].append(f"{qid}: {e}"); continue
                tags = tags_of(sql, days_default)
                dq = {"database": db_id, "type": "native", "native": {"query": sql, "template-tags": tags}}
                cid, err = make_card(f"{short} · {title}", q.get("description"), cid_coll, dq)
                if cid is None:
                    stats["fail"].append(f"{qid}: создание: {str(err)[:140]}"); continue
                st, r = call("POST", f"/api/card/{cid}/query", {})
                if st >= 300 or not isinstance(r, dict) or r.get("status") != "completed" or not r.get("data"):
                    msg = (r.get("error") if isinstance(r, dict) else str(r)) or "?"
                    stats["fail"].append(f"{qid}: выполнение: {str(msg)[:160]}")
                    call("PUT", f"/api/card/{cid}", {"archived": True}); continue
                cols, rows = r["data"]["cols"], r["data"]["rows"]
                isnum = lambda c: c.get("base_type") in NUM_TYPES
                group = q.get("group") or "Прочее"
                stats["cards"] += 1
                # --- сводка без параметров: модель + тахометры
                if kind == "сводка" and not tags and len(rows) == 1:
                    call("PUT", f"/api/card/{cid}", {"type": "model"}); stats["models"] += 1
                    made = 0
                    for i, c in enumerate(cols):
                        if not isnum(c): continue
                        sdq = {"database": db_id, "type": "query", "query": {"source-table": f"card__{cid}", "fields": [["field", c["name"], {"base-type": c["base_type"]}]]}}
                        value = rows[0][i] or 0
                        sid, serr = make_card(f"{short} · {c['name']}", None, cid_coll, sdq, "gauge", gauge_viz(value, c["name"], theme), "question")
                        if sid is None: continue
                        st2, r2 = call("POST", f"/api/card/{sid}/query", {})
                        if st2 < 300 and isinstance(r2, dict) and r2.get("status") == "completed":
                            kpis.append((theme, sid, c["name"], key_s)); made += 1; stats["gauges"] += 1
                        else:
                            call("PUT", f"/api/card/{sid}", {"archived": True})
                    if made == 0:
                        blocks.append((group, "table", cid, title, 24, 4, tags))
                    continue
                # --- временной ряд
                if kind == "timeseries" and len(cols) >= 2 and any(isnum(c) for c in cols[1:]):
                    mets = [c["name"] for c in cols[1:] if isnum(c)]
                    ttl = f"{title}: {mets[0]}" if len(mets) == 1 else title
                    viz = series_color_viz({"graph.dimensions": [cols[0]["name"]], "graph.metrics": mets}, mets, theme)
                    call("PUT", f"/api/card/{cid}", {"name": f"{short} · {ttl}", "display": "line", "visualization_settings": viz})
                    blocks.append((group, "chart", cid, ttl, 12, 7, tags)); stats["charts"] += 1
                    continue
                n = len(rows)
                if len(cols) == 2 and isnum(cols[1]) and not isnum(cols[0]) and 2 <= n <= 24:
                    labels = [str(x[0]) for x in rows]; vals = [(x[1] or 0) for x in rows]
                    if n <= 6 and all(v >= 0 for v in vals) and sum(vals) > 0:
                        disp, viz = "pie", {"pie.dimension": cols[0]["name"], "pie.metric": cols[1]["name"], "pie.show_legend": True, "pie.show_total": True}
                    else:
                        disp = "row" if max(len(x) for x in labels) > 16 else "bar"
                        viz = series_color_viz({"graph.dimensions": [cols[0]["name"]], "graph.metrics": [cols[1]["name"]], "graph.show_values": True}, [cols[1]["name"]], theme)
                    call("PUT", f"/api/card/{cid}", {"display": disp, "visualization_settings": viz})
                    blocks.append((group, "chart", cid, title, 12, 7, tags)); stats["charts"] += 1
                    continue
                tv = table_viz(cols, rows, theme)
                if tv: call("PUT", f"/api/card/{cid}", {"visualization_settings": tv})
                pst, pr = call("POST", "/api/dataset", {"database": db_id, "type": "query", "query": {"source-table": f"card__{cid}", "limit": 1}})
                if kind != "сводка" and pst < 300 and isinstance(pr, dict) and pr.get("status") == "completed":
                    call("PUT", f"/api/card/{cid}", {"type": "model"}); stats["models"] += 1
                h = 5 if n <= 5 else 7 if n <= 12 else 10
                blocks.append((group, "table", cid, title, 24, h, tags))
            for b in blocks: used_tags |= set(b[6])
            # ---------- дашборд раздела
            st, dash = call("POST", "/api/dashboard", {"name": sec["title"], "collection_id": cid_coll,
                            "description": f"Раздел «{sec['title']}» (источник: дашборд Grafana {sec.get('source_dashboard', '')}). Только чтение."})
            did = dash["id"]
            L, add, banner = new_layout(); row = 0
            size = 0.5 if len(sec["title"]) <= 34 else 0.4
            banner(banner_md(sec["title"], tc1, tc2, 52, size), row, 2); row += 2
            def maps_for(card_id, tags):
                return [{"parameter_id": t, "card_id": card_id, "target": ["variable", ["template-tag", t]]} for t in tags]
            for g in dict.fromkeys(b[0] for b in blocks):
                gb = [b for b in blocks if b[0] == g]
                banner(banner_md(g, blend(tc1, 0.12), blend(tc2, 0.05), 40, 0.5), row, 2); row += 2
                charts = [b for b in gb if b[1] == "chart"]; tables = [b for b in gb if b[1] == "table"]
                for i, b in enumerate(charts):
                    add(b[2], (i % 2) * 12, row + (i // 2) * 7, b[4], b[5], {"card.title": b[3]}, maps_for(b[2], b[6]))
                row += ((len(charts) + 1) // 2) * 7
                for b in tables:
                    add(b[2], 0, row, 24, b[5], {"card.title": b[3]}, maps_for(b[2], b[6])); row += b[5]
            params = []
            if "days" in used_tags: params.append({"id": "days", "name": "За сколько дней", "slug": "days", "type": "number/=", "default": [days_default]})
            if "zone" in used_tags: params.append({"id": "zone", "name": "Зона (код)", "slug": "zone", "type": "string/="})
            if "tovar" in used_tags: params.append({"id": "tovar", "name": "Товар (код или часть названия)", "slug": "tovar", "type": "string/="})
            st, r = call("PUT", f"/api/dashboard/{did}", {"parameters": params, "dashcards": L["dcs"]})
            if st >= 300: stats["fail"].append(f"дашборд {sec['title']}: {str(r)[:200]}")
            content["themes"][theme]["dashboards"][key_s] = did
            public[did] = publish(did); sec_public[key_s] = public[did]
            dash_info[theme].append((sec["title"], did))
            print(f"  [{theme}] {sec['title']}: дашборд {did}, блоков {len(blocks)}, фильтры {[p['id'] for p in params]}")

    # ---------- общий дашборд «Ключевые показатели»: все тахометры по темам
    st, kd = call("POST", "/api/dashboard", {"name": "Ключевые показатели склада", "collection_id": root_id,
                  "description": "Все показатели-числа по темам в виде тахометров с цветными зонами. Только чтение."})
    kid = kd["id"]; L, add, banner = new_layout(); row = 0
    banner(banner_md("Ключевые показатели склада", "#1F3A5F", "#3C78B8", 52, 0.5), row, 2); row += 2
    for theme, _, _ in THEMES:
        items = [k for k in kpis if k[0] == theme]
        if not items: continue
        c1, c2 = THEME_COLORS[theme]
        banner(banner_md(theme, c1, c2, 40, 0.5), row, 2); row += 2
        for i, (_, sid, nm, ks) in enumerate(items):
            viz = {"card.title": nm}
            if sec_public.get(ks):  # клик по тахометру открывает дашборд раздела с таблицами
                viz["click_behavior"] = {"type": "link", "linkType": "url", "linkTemplate": "/public/dashboard/" + sec_public[ks], "linkTextTemplate": nm}
            add(sid, (i % 4) * 6, row + (i // 4) * 4, 6, 4, viz)
        row += ((len(items) + 3) // 4) * 4
    st, r = call("PUT", f"/api/dashboard/{kid}", {"dashcards": L["dcs"]})
    if st >= 300: stats["fail"].append(f"дашборд показателей: {str(r)[:200]}")
    content["kpi"] = kid

    public[kid] = publish(kid)

    # ---------- главная
    st, home = call("POST", "/api/dashboard", {"name": "Главная: склад LV_MERIDIAN", "collection_id": root_id,
                    "description": "Навигация по отчётам склада. Только чтение."})
    hid = home["id"]; L, add, banner = new_layout()
    banner(banner_md("Склад АО «Меридиан»: отчёты", "#1F3A5F", "#3C78B8", 56, 0.5), 0, 2)
    kl = public.get(kid)
    vz = {"virtual_card": {"name": None, "display": "text", "archived": False},
          "text": ("### [Ключевые показатели склада: тахометры →](/public/dashboard/%s)" % kl) if kl else "### Ключевые показатели", "dashcard.background": True}
    vz.update({"text.align_horizontal": "center", "text.align_vertical": "middle"})
    add(None, 0, 2, 24, 2, vz)
    for i, (theme, tdesc, _) in enumerate(THEMES):
        c1, c2 = THEME_COLORS[theme]
        links = "\n".join(f"- [{t}](/public/dashboard/{public[d]})" for t, d in dash_info[theme] if public.get(d))
        md = banner_md(theme, c1, c2, 46, 0.55, 360) + f"\n\n{tdesc}\n\n" + links
        v = {"virtual_card": {"name": None, "display": "text", "archived": False}, "text": md, "dashcard.background": True}
        add(None, (i % 3) * 8, 4 + (i // 3) * 7, 8, 7, v)
    st, r = call("PUT", f"/api/dashboard/{hid}", {"dashcards": L["dcs"]})
    if st >= 300: stats["fail"].append(f"главная: {str(r)[:200]}")
    public[hid] = publish(hid)
    content["home"] = hid

    # ---------- ссылки для просмотра: в файл секретов (ссылки публичные для всех, у кого они есть)
    names = {did: t for th in dash_info for t, did in dash_info[th]}
    names.update({kid: "Ключевые показатели склада", hid: "Главная: склад LV_MERIDIAN"})
    lf = "/opt/wms-constructor-secrets/metabase-public-links.txt"
    with open(lf, "w", encoding="utf-8") as f:
        f.write("# Публичные ссылки Metabase (просмотр без пароля, без редактирования). Не публиковать в репозитории.\n")
        for did in [hid, kid] + [d for th in dash_info for _, d in dash_info[th]]:
            if public.get(did): f.write(f"{names[did]}\t/public/dashboard/{public[did]}\n")
    os.chmod(lf, 0o600)
    json.dump(content, open(os.path.join(HERE, "content_map.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\nИТОГО: карточек {stats['cards']}, моделей {stats['models']}, тахометров {stats['gauges']}, графиков {stats['charts']}, "
          f"публичных ссылок {sum(1 for v in public.values() if v)}, проблем {len(stats['fail'])}")
    print("главная:", hid, "| показатели:", kid)
    for f in stats["fail"]: print("  ПРОБЛЕМА:", f)


main()
