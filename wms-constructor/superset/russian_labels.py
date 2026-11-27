#!/usr/bin/env python3
"""Русские подписи полей витрин — из словаря самой базы LV_MERIDIAN.

Зачем: в таблицах Superset заголовок колонки берётся из `verbose_name` поля
набора данных. Пока его нет, показываются латинские ключи витрины
(`order_code`, `zone_code`), и отчёт выглядит «полуанглийским».

Откуда слова: из словаря сообщений системы — `LV_Messages`, колонка
`msg_Greek` при `msg_languageID = 4` (русский). Проверено запросом к базе
2026-11-27: `Code → Код`, `OrderType → Тип расходного заказа`,
`InputDate → Дата ввода`, `LocZone → Зона ячеек`, `Operations → Операции`,
`Quantity → Количество`, `NetWeight → Вес нетто`, `Supplier → Поставщик`.

ВАЖНО, чтобы не повторить аварию: подпись ставится ТОЛЬКО в `verbose_name`
колонки. Имена полей в `params` диаграмм (`x_axis`, `groupby`, `metrics`)
остаются латинскими — Superset отправляет их прямо в SQL, и подстановка
русской подписи даёт `Invalid column name 'Статус'`. Подпись — это метка для
человека, а не имя колонки в запросе.

Скрипт идемпотентен: перечитывает колонки из SQL витрины и заново расставляет
подписи; диаграммы не трогает вовсе.

Запуск на wmssql-analytics:
    docker cp russian_labels.py superset:/tmp/
    docker exec superset python /tmp/russian_labels.py
"""

import sys

from superset.app import create_app

app = create_app()

# поле витрины -> (русская подпись, откуда слово в словаре базы)
LABELS = {
    # --- остатки (dm_stock)
    "stock_id": ("Идентификатор остатка", "Stock"),
    "loc_code": ("Код ячейки", "Location + Code"),
    "zone_code": ("Код зоны", "LocZone"),
    "zone": ("Зона ячеек", "LocZone"),
    "product_code": ("Код товара", "Code"),
    "product_name": ("Наименование товара", "Product + Name"),
    "unit": ("Единица измерения", "Unit"),
    "qty": ("Количество", "Quantity"),
    "qty_free": ("Свободный остаток", "Quantity"),
    "qty_reserved": ("Резерв", "Quantity"),
    # --- приходы
    "receipt_id": ("Идентификатор прихода", "Receipt"),
    "receipt_code": ("Номер прихода", "Receipt + Code"),
    "receipt_type": ("Тип прихода", "Receipt + Type"),
    "receipt_type_code": ("Код типа прихода", "Receipt + Type"),
    "supplier": ("Поставщик", "Supplier"),
    "input_datetime": ("Дата и время ввода", "InputDate"),
    "input_day": ("Дата ввода", "InputDate"),
    "actual_day": ("Фактическая дата", "ExpectedDate"),
    "expected_day": ("Ожидаемая дата", "ExpectedDate"),
    "status": ("Статус", "Status"),
    "line_count": ("Строк в документе", "LineCount"),
    "lines_with_items": ("Строк с товаром", "LineCount"),
    "net_weight": ("Вес нетто", "NetWeight"),
    "line_id": ("Идентификатор строки", "LineCount"),
    "expected_qty": ("Ожидаемое количество", "Quantity"),
    "actual_qty": ("Фактическое количество", "Quantity"),
    "retained_qty": ("Удержано", "Quantity"),
    # --- расход
    "order_id": ("Идентификатор заказа", "Order"),
    "order_code": ("Номер заказа", "Order + Code"),
    "order_type": ("Тип расходного заказа", "OrderType"),
    "order_type_code": ("Код типа заказа", "OrderType"),
    "customer": ("Клиент", "Customer"),
    "expected_ship_day": ("Ожидаемая дата отгрузки", "ExpShipDate"),
    "order_value": ("Стоимость заказа", "Value"),
    "shipped_qty": ("Отгружено", "Quantity"),
    # --- движение
    "log_id": ("Идентификатор операции", "Transaction"),
    "log_datetime": ("Дата и время операции", "InputDate"),
    "day": ("Дата операции", "rpt_Day"),
    "hour_of_day": ("Час операции", "InputDate"),
    "operation": ("Операция", "Transaction"),
    "operation_code": ("Код операции", "Transaction + Code"),
    "location_code": ("Код ячейки", "Location + Code"),
    "user_login": ("Пользователь", "User"),
    "qty_abs": ("Количество по модулю", "Quantity"),
    # --- обмен с 1С
    "queue_id": ("Идентификатор записи", "—"),
    "direction_ru": ("Направление обмена", "—"),
    "direction_no": ("Код направления", "—"),
    "queue_ru": ("Очередь", "—"),
    "message_type": ("Тип сообщения", "Type"),
    "request_datetime": ("Дата и время запроса", "InputDate"),
    "request_day": ("Дата запроса", "InputDate"),
    "complete_datetime": ("Дата и время обработки", "InputDate"),
    "tries": ("Попыток обработки", "—"),
    "state": ("Состояние записи", "Status"),
    "state_no": ("Код состояния", "Status"),
    "status_code": ("Код статуса обмена", "Status"),
    "age_days": ("Возраст, дней", "—"),
    "error_text": ("Текст ошибки", "Ошибка"),
    "error_group": ("Причина ошибки", "Ошибка"),
}

METRIC_LABELS = {"count": "Количество"}

DATASETS = (
    "dm_stock", "dm_movement", "dm_receipts", "dm_receipt_lines",
    "dm_orders", "dm_order_lines", "dm_exchange_queue", "dm_exchange_errors",
)


def main() -> None:
    with app.app_context():
        from superset import db
        from superset.connectors.sqla.models import SqlaTable

        datasets = (db.session.query(SqlaTable)
                    .filter(SqlaTable.table_name.in_(DATASETS)).all())
        if not datasets:
            sys.exit("витрины не найдены")

        total_named = 0
        total_cols = 0
        for ds in datasets:
            ds.fetch_metadata()
            db.session.commit()
            named = 0
            for col in ds.columns:
                label = LABELS.get(col.column_name)
                if label:
                    col.verbose_name = label[0]
                    named += 1
            for m in ds.metrics:
                if m.metric_name in METRIC_LABELS:
                    m.verbose_name = METRIC_LABELS[m.metric_name]
            db.session.commit()
            total_named += named
            total_cols += len(ds.columns)
            print(f"  {ds.table_name}: колонок {len(ds.columns)}, подписано {named}")

        print(f"\nИтого подписано полей: {total_named} из {total_cols}")

        # Самопроверка: все диаграммы должны по-прежнему отдавать данные —
        # подписи не должны влиять на запросы.
        import json
        import os
        import re

        app.config["WTF_CSRF_ENABLED"] = False
        client = app.test_client()
        html = client.get("/login/").data.decode("utf-8", "ignore")
        m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html)
        client.post("/login/", data={"username": "admin", "password": os.environ.get("ADMIN_PASSWORD"),
                                     "csrf_token": m.group(1) if m else "", "provider": "db"},
                    follow_redirects=True)
        charts = client.get("/api/v1/chart/?q=" + json.dumps({"page_size": 500})).get_json()
        bad = []
        for c in charts["result"]:
            res = client.get(f"/api/v1/chart/{c['id']}/data/?format=json")
            j = res.get_json() or {}
            row = (j.get("result") or [{}])[0] if isinstance(j.get("result"), list) else {}
            err = row.get("error") or (None if res.status_code == 200 else j.get("message"))
            if err or not (row.get("data") or []):
                bad.append((c["id"], c.get("slice_name"), str(err)[:160] or "0 строк"))
        print()
        if bad:
            print(f"ПРОБЛЕМЫ ({len(bad)}):")
            for b in bad:
                print("  ", b)
        else:
            print(f"Самопроверка: все {len(charts['result'])} диаграмм отдают данные.")


if __name__ == "__main__":
    main()