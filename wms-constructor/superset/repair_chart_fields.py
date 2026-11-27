#!/usr/bin/env python3
"""Возврат правильных имён полей в диаграммах после ошибочного переименования.

Что случилось: первый вариант `russian_labels.py` переписывал в `params`
диаграмм сами имена полей (`order_code` → «Номер заказа»). Superset отправляет
в базу именно эти имена, и SQL Server отвечал
`Invalid column name 'Статус'` — отчёт перестал строиться.

Здесь обратная операция: по таблице LABELS (русская подпись → настоящее поле
витрины) имена полей возвращаются на место. Подписи при этом остаются там, где
им место, — в `verbose_name` колонок набора данных (их ставит
`russian_labels.py`).

Скрипт идемпотентен и безопасен при повторном запуске: если в `params` уже
стоят настоящие имена, менять нечего.

Запуск на wmssql-analytics:
    docker cp repair_chart_fields.py superset:/tmp/
    docker exec superset python /tmp/repair_chart_fields.py
"""

import json
import os
import re
import sys

from superset.app import create_app

app = create_app()

# русская подпись -> настоящее имя поля витрины (обратная карта russian_labels)
REVERSE = {
    "Идентификатор остатка": "stock_id",
    "Код ячейки": None,          # loc_code и location_code — решается по набору
    "Код зоны": "zone_code",
    "Зона ячеек": "zone",
    "Код товара": "product_code",
    "Наименование товара": "product_name",
    "Единица измерения": "unit",
    "Количество": "qty",
    "Свободный остаток": "qty_free",
    "Резерв": "qty_reserved",
    "Идентификатор прихода": "receipt_id",
    "Номер прихода": "receipt_code",
    "Тип прихода": "receipt_type",
    "Код типа прихода": "receipt_type_code",
    "Поставщик": "supplier",
    "Дата и время ввода": "input_datetime",
    "Дата ввода": "input_day",
    "Фактическая дата": "actual_day",
    "Ожидаемая дата": "expected_day",
    "Статус": "status",
    "Строк в документе": "line_count",
    "Строк с товаром": "lines_with_items",
    "Вес нетто": "net_weight",
    "Идентификатор строки": "line_id",
    "Ожидаемое количество": "expected_qty",
    "Фактическое количество": "actual_qty",
    "Удержано": "retained_qty",
    "Идентификатор заказа": "order_id",
    "Номер заказа": "order_code",
    "Тип расходного заказа": "order_type",
    "Код типа заказа": "order_type_code",
    "Клиент": "customer",
    "Ожидаемая дата отгрузки": "expected_ship_day",
    "Стоимость заказа": "order_value",
    "Отгружено": "shipped_qty",
    "Идентификатор операции": "log_id",
    "Дата и время операции": "log_datetime",
    "Дата операции": "day",
    "Час операции": "hour_of_day",
    "Операция": "operation",
    "Код операции": "operation_code",
    "Пользователь": "user_login",
    "Количество по модулю": "qty_abs",
    "Идентификатор записи": "queue_id",
    "Направление обмена": "direction_ru",
    "Код направления": "direction_no",
    "Очередь": "queue_ru",
    "Тип сообщения": "message_type",
    "Дата и время запроса": "request_datetime",
    "Дата запроса": "request_day",
    "Дата и время обработки": "complete_datetime",
    "Попыток обработки": "tries",
    "Состояние записи": "state",
    "Код состояния": "state_no",
    "Код статуса обмена": "status_code",
    "Возраст, дней": "age_days",
    "Текст ошибки": "error_text",
    "Причина ошибки": "error_group",
}

# «Код ячейки» зависит от набора: в остатках это loc_code, в движении — location_code
PER_DATASET = {
    "loc_code": "Код ячейки",
    "location_code": "Код ячейки",
}


def login(client):
    app.config["WTF_CSRF_ENABLED"] = False
    html = client.get("/login/").data.decode("utf-8", "ignore")
    m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html)
    client.post("/login/", data={"username": "admin", "password": os.environ.get("ADMIN_PASSWORD"),
                                 "csrf_token": m.group(1) if m else "", "provider": "db"},
                follow_redirects=True)


def main() -> None:
    with app.app_context():
        from superset import db
        from superset.connectors.sqla.models import SqlaTable

        # набор -> {подпись: поле}, где подпись уникальна внутри набора
        dataset_cols = {}
        for ds in db.session.query(SqlaTable).filter(
                SqlaTable.table_name.like("dm_%")).all():
            mapping = {}
            for col in ds.columns:
                label = (col.verbose_name or "").strip()
                if label:
                    mapping.setdefault(label, set()).add(col.column_name)
            dataset_cols[ds.id] = {k: next(iter(v)) for k, v in mapping.items() if len(v) == 1}

        client = app.test_client()
        login(client)

        charts = client.get("/api/v1/chart/?q=" + json.dumps({"page_size": 500})).get_json()
        fixed = 0
        skipped = 0
        for c in charts["result"]:
            ds_id = c.get("datasource_id")
            table_map = dataset_cols.get(ds_id, {})
            params = json.loads(c.get("params") or "{}")

            def real_name(v):
                if not isinstance(v, str):
                    return v
                if v in table_map:            # подпись, известная в этом наборе
                    return table_map[v]
                if v in REVERSE and REVERSE[v]:
                    return REVERSE[v]
                return v

            before = json.dumps(params, ensure_ascii=False)
            for key in ("x_axis", "granularity_sqla"):
                params[key] = real_name(params.get(key))
            for key in ("groupby", "all_columns"):
                vals = params.get(key)
                if isinstance(vals, list):
                    params[key] = [real_name(v) for v in vals]
            for key in ("metrics", "metric", "timeseries_limit_metric"):
                vals = params.get(key)
                items = vals if isinstance(vals, list) else ([vals] if isinstance(vals, dict) else [])
                for m in items:
                    if not isinstance(m, dict):
                        continue
                    if isinstance(m.get("column"), dict):
                        cn = m["column"].get("column_name")
                        if cn in table_map:
                            m["column"]["column_name"] = table_map[cn]
                    if isinstance(m.get("sqlExpression"), str) and "[" in m["sqlExpression"]:
                        m["sqlExpression"] = re.sub(
                            r"\[([^\]]+)\]",
                            lambda mm: "[" + (table_map.get(mm.group(1)) or mm.group(1)) + "]",
                            m["sqlExpression"])
            after = json.dumps(params, ensure_ascii=False)
            if before == after:
                skipped += 1
                continue

            body = {"params": after}
            ctx = json.loads(c["query_context"]) if c.get("query_context") else None
            if ctx:
                form = ctx.get("form_data") or {}
                for key in ("x_axis", "groupby", "metrics", "metric",
                            "granularity_sqla", "all_columns"):
                    if key in params:
                        form[key] = params[key]
                ctx["form_data"] = form
                body["query_context"] = json.dumps(ctx, ensure_ascii=False)
            r = client.put(f"/api/v1/chart/{c['id']}", json=body,
                           headers={"Referer": "http://localhost"})
            if r.status_code < 300:
                fixed += 1
                print(f"  диаграмма {c['id']} {c.get('slice_name')}: имена полей восстановлены")
            else:
                print(f"  диаграмма {c['id']} {c.get('slice_name')}: ОШИБКА {r.status_code} "
                      f"{str(r.get_json())[:150]}")

        print(f"\nИсправлено диаграмм: {fixed}, без изменений: {skipped}")

        # проверка: каждая диаграмма должна отдавать данные
        print()
        bad = []
        for c in charts["result"]:
            res = client.get(f"/api/v1/chart/{c['id']}/data/?format=json")
            j = res.get_json() or {}
            row = (j.get("result") or [{}])[0] if isinstance(j.get("result"), list) else {}
            err = row.get("error") or (None if res.status_code == 200 else j.get("message"))
            rows = len(row.get("data") or [])
            if err or rows == 0:
                bad.append((c["id"], c.get("slice_name"), str(err)[:160] or "0 строк"))
        if bad:
            print(f"ПРОБЛЕМЫ ({len(bad)}):")
            for b in bad:
                print("  ", b)
        else:
            print(f"Все {len(charts['result'])} диаграмм отдают данные.")


if __name__ == "__main__":
    main()