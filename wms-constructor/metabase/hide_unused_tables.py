#!/usr/bin/env python3
"""Скрывает в Metabase таблицы и представления, которых нет в queries/*.yaml (обратимо).

Видимыми остаются объекты, на которые ссылаются наши проверенные запросы (FROM/JOIN).
Скрытие в Metabase - порядок в интерфейсе, а НЕ защита данных (защита: права пользователя БД).
Ключ API читается из /opt/wms-constructor-secrets/metabase-api.env (значение не выводится).
Запуск: METABASE_URL=http://<адрес>:3001 python3 hide_unused_tables.py [--apply | --unhide-all]
Без флагов - только показывает, что было бы сделано ([R]).
"""
import argparse, glob, json, os, re, sys, urllib.error, urllib.request

KEYFILE = "/opt/wms-constructor-secrets/metabase-api.env"
HERE = os.path.dirname(os.path.abspath(__file__))
REF = re.compile(r"\b(?:FROM|JOIN)\s+((?:\[?[A-Za-z0-9_]+\]?\s*\.\s*){0,2}\[?[A-Za-z0-9_]+\]?)", re.I)


def read_key():
    for ln in open(KEYFILE, encoding="utf-8"):
        if ln.startswith("METABASE_API_KEY="):
            return ln.split("=", 1)[1].strip()
    sys.exit("нет METABASE_API_KEY")


def used_names(qdir):
    local, external = set(), set()
    for p in sorted(glob.glob(os.path.join(qdir, "*.yaml"))):
        text = open(p, encoding="utf-8").read()
        text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
        text = re.sub(r"--[^\n]*", " ", text)
        for m in REF.finditer(text):
            parts = [x.strip(" []") for x in re.split(r"\s*\.\s*", m.group(1))]
            (external if len(parts) == 3 else local).add(parts[-1].lower() if len(parts) < 3 else ".".join(parts).lower())
    return local, external


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--unhide-all", action="store_true", help="вернуть видимость всем скрытым таблицам")
    ap.add_argument("--db-name", default="LV_MERIDIAN (WMS)")
    ap.add_argument("--queries", default=os.path.join(HERE, "..", "queries"))
    a = ap.parse_args()
    base = os.environ.get("METABASE_URL") or sys.exit("задайте METABASE_URL=http://<адрес>:3001")
    key = read_key()

    def call(method, path, body=None):
        req = urllib.request.Request(base + path, method=method, data=(json.dumps(body).encode() if body is not None else None),
                                     headers={"x-api-key": key, "Content-Type": "application/json"})
        try:
            r = urllib.request.urlopen(req, timeout=180)
            raw = r.read()
            return r.status, (json.loads(raw) if raw else None)
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8", "replace")[:300]

    st, dbs = call("GET", "/api/database")
    items = dbs.get("data", dbs)
    db = next((d for d in items if d.get("name") == a.db_name), None) or sys.exit("база не найдена")
    st, md = call("GET", f"/api/database/{db['id']}/metadata?include_hidden=true")
    tables = md["tables"]
    by_name = {t["name"].lower(): t for t in tables}

    if a.unhide_all:
        ids = [t["id"] for t in tables if t.get("visibility_type")]
        print("скрытых сейчас:", len(ids))
        if a.apply and ids:
            st, r = call("PUT", "/api/table", {"ids": ids, "visibility_type": None})
            print("вернул видимость: HTTP", st)
        return

    local, external = used_names(a.queries)
    keep_ids = {by_name[n]["id"] for n in local if n in by_name}
    unmatched = sorted(n for n in local if n not in by_name)
    # связи по внешним ключам (для информации): сколько объектов в одном шаге от оставленных
    tid = {f["id"]: t["id"] for t in tables for f in t.get("fields", [])}
    nb = set()
    for t in tables:
        for f in t.get("fields", []):
            tgt = f.get("fk_target_field_id")
            if tgt and tgt in tid:
                if t["id"] in keep_ids: nb.add(tid[tgt])
                if tid[tgt] in keep_ids: nb.add(t["id"])
    hide = [t for t in tables if t["id"] not in keep_ids and t.get("visibility_type") != "hidden"]
    print(f"всего объектов: {len(tables)} | используются в запросах (останутся видимыми): {len(keep_ids)} | будет скрыто: {len(hide)}")
    print(f"ссылки на другую базу (не в Metabase, это нормально): {len(external)} | имена без совпадения (CTE, функции и т.п.): {unmatched}")
    print(f"справочно: связанных внешними ключами с оставленными, но не используемых в запросах: {len(nb - keep_ids)}")
    if a.apply:
        for i in range(0, len(hide), 400):
            chunk = [t["id"] for t in hide[i:i + 400]]
            st, r = call("PUT", "/api/table", {"ids": chunk, "visibility_type": "hidden"})
            print(f"скрыто пачкой {len(chunk)}: HTTP {st}", "" if st < 300 else r)
        with open(os.path.join(HERE, "visible_tables.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(sorted(by_name[n]["name"] for n in local if n in by_name)) + "\n")
        print("список видимых записан в metabase/visible_tables.txt")


main()
