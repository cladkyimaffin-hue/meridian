#!/usr/bin/env python3
"""Помечает в Metabase чувствительные столбцы как «не показывать» (обратимо; идемпотентно).

Правило пользователя: пароли, документы, адреса, контакты, оклады и ставки сотрудников, значения КМ,
номера коробов и SSCC в конструкторе не выводятся. ВАЖНО: пометка скрывает столбец в интерфейсе Metabase,
но НЕ запрещает его читать произвольным SQL-запросом (защита на уровне БД - отдельная работа).
Ключ API: /opt/wms-constructor-secrets/metabase-api.env. Запуск: METABASE_URL=http://<адрес>:3001 python3 mark_sensitive_columns.py [--revert]
"""
import json, os, sys, urllib.error, urllib.request

SENS = {
    "LV_Users": ["usr_Password", "usr_VoicePassword"],
    "COM_Employee": ["emp_Salary", "emp_HourlyRate"],
    "COM_Person": ["per_Address", "per_Area", "per_City", "per_ZipCode", "per_Phone", "per_Mobile",
                   "per_Email", "per_IDNumber", "per_PassportNumber", "per_Memo"],
    "ANT_ExportKMBoxAggregation": ["eka_BoxNumber", "eka_KM"],
    "ANT_ExportKMBoxSplitting": ["eks_BoxNumber", "eks_KM"],
    "a_Tab_KM": ["akm_KM", "akm_BoxNumber", "akm_packSSCC"],
    "a_Tab_KM_Archive": ["akml_KM", "akml_BoxNumber", "akml_packSSCC"],
    "LV_OrderItem": ["ori_SSCC"], "LV_ReceiptItem": ["rci_SSCC"],
    "LV_StockContainer": ["stc_SSCC"], "LV_Task": ["tsk_SSCC"],
}
base = os.environ.get("METABASE_URL") or sys.exit("задайте METABASE_URL=http://<адрес>:3001")
key = [l.split("=", 1)[1].strip() for l in open("/opt/wms-constructor-secrets/metabase-api.env") if l.startswith("METABASE_API_KEY=")][0]
value = None if "--revert" in sys.argv else "sensitive"


def call(method, path, body=None):
    req = urllib.request.Request(base + path, method=method, data=(json.dumps(body).encode() if body is not None else None),
                                 headers={"x-api-key": key, "Content-Type": "application/json"})
    try:
        r = urllib.request.urlopen(req, timeout=120)
        raw = r.read()
        return r.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:200]


dbs = call("GET", "/api/database")[1]
db = next(d for d in dbs.get("data", dbs) if d["name"] == "LV_MERIDIAN (WMS)")
tables = {t["name"]: t for t in call("GET", f"/api/database/{db['id']}/metadata?include_hidden=true")[1]["tables"]}
ok = bad = 0
for tn, cols in SENS.items():
    fields = {f["name"]: f for f in tables.get(tn, {}).get("fields", [])}
    for c in cols:
        if c not in fields:
            print("не найден:", tn, c); bad += 1; continue
        st, r = call("PUT", f"/api/field/{fields[c]['id']}", {"visibility_type": value})
        ok += st < 300; bad += st >= 300
print(("снята пометка" if value is None else "помечено") + f": {ok}, ошибок/не найдено: {bad}")
