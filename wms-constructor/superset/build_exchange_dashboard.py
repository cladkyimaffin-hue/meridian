"""Витрины «Обмен с 1С» и их дашборд в Superset.

Источник — база обмена `MRDN_Exchange` (та же учётная запись `constructor_ro`,
что и у LV_MERIDIAN; проверено чтением очередей). Что создаётся:

  dm_exchange_queue   — записи очередей импорта и экспорта с расшифровкой
                        направления, типа сообщения, состояния и возраста;
  dm_exchange_errors  — только записи в ошибке (для разбора причин);
  дашборд «Обмен с 1С: очереди и ошибки», slug `wms-exchange`.

Почему витрины, а не прямые таблицы: в очередях лежат коды состояний
(`eqi_ImportStatus`, `eqe_ExportLED`), а для отчёта нужны человеческие подписи
(«В ошибке», «Не выгружено в 1С», «Обработано»). Расшифровка сделана в SQL,
чтобы одна и та же логика использовалась всеми диаграммами.

Скрипт идемпотентен: наборы данных обновляются по имени, диаграммы с префиксом
«Обмен:» и дашборд с этим slug пересоздаются.

Запуск на wmssql-analytics:
    docker cp build_exchange_dashboard.py superset:/tmp/
    docker exec superset python /tmp/build_exchange_dashboard.py

Проверено 2026-11-27: 32 798 записей импорта (1 478 в ошибке), 370 записей
экспорта (все не выгружены), 18 типов сообщений, последняя запись импорта —
2026-11-27 15:14.
"""

import json
import uuid

from superset.app import create_app

app = create_app()

DB_NAME = "LV_MERIDIAN (WMS)"
DASH_SLUG = "wms-exchange"
CHART_PREFIX = "Обмен:"

# Направление в справочнике: 1 — из 1С в WMS, 2 — из WMS в 1С.
# Состояние записи импорта: ошибка важнее статуса; иначе ImportLED=1 и
# CompleteDate заполнена — обработана, иначе ждёт обработки.
# У экспорта отдельного статуса нет: заполненная ExportLED означает «выгружено».
QUEUE_SQL = """
WITH q AS (
    SELECT N'1С → WMS' AS direction_ru, 1 AS direction_no,
           N'Импорт' AS queue_ru,
           i.eqi_ID AS queue_id,
           i.eqi_TypeID AS type_id,
           t.eqt_Name AS message_type,
           t.eqt_Direction AS type_direction,
           i.eqi_RequestDate AS request_datetime,
           i.eqi_CompleteDate AS complete_datetime,
           i.eqi_TryNumber AS tries,
           i.eqi_ErrorLED AS error_led,
           i.eqi_ErrorMessage AS error_message,
           CAST(ISNULL(i.eqi_ImportLED, 0) AS int) AS done_led,
           i.eqi_ImportStatus AS status_code
    FROM MRDN_Exchange.dbo.IFC_ExchangeQueueImport i
    LEFT JOIN MRDN_Exchange.dbo.IFC_ExchangeQueueType t ON t.eqt_ID = i.eqi_TypeID
    UNION ALL
    SELECT N'WMS → 1С', 2, N'Экспорт',
           e.eqe_ID,
           e.eqe_TypeID,
           t.eqt_Name,
           t.eqt_Direction,
           e.eqe_RequestDate,
           e.eqe_CompleteDate,
           CAST(NULL AS int),
           e.eqe_ErrorLED,
           e.eqe_ErrorMessage,
           CAST(ISNULL(e.eqe_ExportLED, 0) AS int),
           CAST(NULL AS int)
    FROM MRDN_Exchange.dbo.IFC_ExchangeQueueExport e
    LEFT JOIN MRDN_Exchange.dbo.IFC_ExchangeQueueType t ON t.eqt_ID = e.eqe_TypeID
)
SELECT q.queue_id,
       q.direction_ru,
       q.direction_no,
       q.queue_ru,
       ISNULL(q.message_type, N'(тип не указан)') AS message_type,
       q.request_datetime,
       CAST(q.request_datetime AS date) AS request_day,
       q.complete_datetime,
       q.tries,
       CASE WHEN q.error_led = 1 THEN N'В ошибке'
            WHEN q.done_led = 1 THEN N'Обработано'
            ELSE N'Ждёт обработки' END AS state,
       CASE WHEN q.error_led = 1 THEN 3
            WHEN q.done_led = 1 THEN 1
            ELSE 2 END AS state_no,
       ISNULL(q.status_code, -1) AS status_code,
       DATEDIFF(day, q.request_datetime, GETDATE()) AS age_days,
       LEFT(ISNULL(q.error_message, N''), 200) AS error_text
FROM q
"""

# Витрина ошибок: только записи в ошибке, с группой причины (шаблоны текста
# взяты из queries/exchange.yaml, чтобы отчёт и конструктор объясняли одно и то же).
ERRORS_SQL = """
SELECT q.queue_id,
       q.direction_ru,
       q.queue_ru,
       q.message_type,
       q.request_datetime,
       q.age_days,
       q.tries,
       LEFT(ISNULL(q.error_text, N''), 160) AS error_text,
       CASE
           WHEN LTRIM(RTRIM(ISNULL(q.error_text, N''))) = N'' THEN N'Текст ошибки не указан'
           WHEN q.error_text LIKE N'%units : UnitCode%' THEN N'Единица измерения не найдена в сопоставлении (код 1С)'
           WHEN q.error_text LIKE N'%за 10 попыток%' THEN N'Не удалось загрузить строку за 10 попыток'
           WHEN q.error_text LIKE N'%already linked to another item%' THEN N'Штрихкод уже привязан к другому товару'
           WHEN q.error_text LIKE N'%already exists%' OR q.error_text LIKE N'%уже присутству%' THEN N'Документ или заказ уже существует'
           WHEN q.error_text LIKE N'%не найден в%' THEN N'Код не найден в справочнике'
           WHEN q.error_text LIKE N'%Нет расхода в LVision%' THEN N'Нет расхода в WMS (обновление заголовка)'
           WHEN q.error_text LIKE N'%Склад получатель%' THEN N'Некорректный код атрибута «Склад получатель»'
           WHEN q.error_text LIKE N'%Марки некорректные%' OR q.error_text LIKE N'%Дубликаты марок%'
                OR q.error_text LIKE N'%принятые KM%' OR q.error_text LIKE N'%Для поставки нет приходов%'
                OR q.error_text LIKE N'%Марки еще не приняты%' OR q.error_text LIKE N'%AA0akm_RecATR%'
                THEN N'Маркировка (КМ): некорректные, дубликаты или не приняты'
           WHEN q.error_text LIKE N'%усечены%' THEN N'Данные длиннее поля (усечение)'
           WHEN q.error_text LIKE N'%Ошибка в данных%' THEN N'Ошибка в данных'
           ELSE N'Прочие ошибки'
       END AS error_group
FROM (
    SELECT i.eqi_ID AS queue_id,
           N'1С → WMS' AS direction_ru,
           N'Импорт' AS queue_ru,
           ISNULL(t.eqt_Name, N'(тип не указан)') AS message_type,
           i.eqi_RequestDate AS request_datetime,
           DATEDIFF(day, i.eqi_RequestDate, GETDATE()) AS age_days,
           i.eqi_TryNumber AS tries,
           i.eqi_ErrorMessage AS error_text
    FROM MRDN_Exchange.dbo.IFC_ExchangeQueueImport i
    LEFT JOIN MRDN_Exchange.dbo.IFC_ExchangeQueueType t ON t.eqt_ID = i.eqi_TypeID
    WHERE i.eqi_ErrorLED = 1
    UNION ALL
    SELECT e.eqe_ID, N'WMS → 1С', N'Экспорт',
           ISNULL(t.eqt_Name, N'(тип не указан)'),
           e.eqe_RequestDate,
           DATEDIFF(day, e.eqe_RequestDate, GETDATE()),
           CAST(NULL AS int),
           e.eqe_ErrorMessage
    FROM MRDN_Exchange.dbo.IFC_ExchangeQueueExport e
    LEFT JOIN MRDN_Exchange.dbo.IFC_ExchangeQueueType t ON t.eqt_ID = e.eqe_TypeID
    WHERE e.eqe_ErrorLED = 1
) q
"""

DATASETS = [
    ("dm_exchange_queue", QUEUE_SQL, "request_datetime",
     "Записи очередей обмена с 1С (импорт и экспорт): направление, тип сообщения, "
     "состояние, возраст, число попыток"),
    ("dm_exchange_errors", ERRORS_SQL, "request_datetime",
     "Записи обмена с 1С в ошибке: группа причины по тексту ошибки, возраст, попытки"),
]


def sql_metric(expr, label):
    return {"expressionType": "SQL", "sqlExpression": expr, "label": label, "hasCustomLabel": True}


def count(label):
    return sql_metric("COUNT(1)", label)


def build_query(form_data):
    """queries[0] для query_context (правила Superset 6.1.0, см. build_operation_dashboards.py)."""
    columns = []
    x_axis = form_data.get("x_axis")
    if x_axis:
        columns.append(x_axis)
    columns.extend(form_data.get("groupby") or [])
    metrics = list(form_data.get("metrics") or [])
    if not metrics and form_data.get("metric"):
        metrics = [form_data["metric"]]
    return {
        "columns": columns,
        "metrics": metrics,
        "row_limit": form_data.get("row_limit", 100),
        "row_offset": 0,
        "orderby": [],
        "is_timeseries": False,
        "extras": {"having": "", "where": ""},
        "filters": [],
        "annotation_layers": [],
        "series_limit": 0,
        "order_desc": bool(form_data.get("order_desc", True)),
        "url_params": {},
        "custom_form_data": {},
        "apply_fetch_values_predicate": False,
    }


def bignum(name, metric, subheader=""):
    return name, {
        "viz_type": "big_number_total", "metric": metric, "adhoc_filters": [],
        "subheader": subheader, "header_font_size": 0.4, "subheader_font_size": 0.125,
        "y_axis_format": "SMART_NUMBER", "time_range": "No filter",
        "color_scheme": "t_obmen",
    }


def bar(name, x_axis, metrics, *, groupby=None, row_limit=50, horizontal=False,
        show_value=True):
    return name, {
        "viz_type": "echarts_timeseries_bar", "x_axis": x_axis,
        "groupby": groupby or [], "metrics": metrics, "adhoc_filters": [],
        "row_limit": row_limit, "orientation": "horizontal" if horizontal else "vertical",
        "show_legend": True, "legendType": "scroll", "legendOrientation": "top",
        "show_value": show_value, "x_axis_sort_asc": False, "xAxisLabelRotation": 45,
        "y_axis_format": "SMART_NUMBER", "rich_tooltip": True, "show_toolbar": True,
        "order_desc": True, "time_range": "No filter", "color_scheme": "t_obmen",
    }


def trend(name, dttm_col, metrics):
    return name, {
        "viz_type": "echarts_timeseries_line", "x_axis": dttm_col, "groupby": [],
        "metrics": metrics, "adhoc_filters": [], "row_limit": 5000,
        "x_axis_time_format": "smart_date", "show_legend": True, "legendOrientation": "top",
        "markerEnabled": True, "markerSize": 6, "area": True, "opacity": 0.25,
        "rich_tooltip": True, "show_toolbar": True, "y_axis_format": "SMART_NUMBER",
        "order_desc": False, "time_range": "No filter", "color_scheme": "t_obmen",
    }


def table(name, groupby, metrics, *, row_limit=200):
    return name, {
        "viz_type": "table", "query_mode": "aggregate", "groupby": groupby,
        "metrics": metrics, "adhoc_filters": [], "row_limit": row_limit,
        "order_desc": True, "show_cell_bars": True, "color_pn": True,
        "timeseries_limit_metric": metrics[0] if metrics else None,
        "time_range": "No filter",
    }


def main() -> None:
    with app.app_context():
        from sqlalchemy import text

        from superset import db
        from superset.connectors.sqla.models import SqlaTable
        from superset.models.core import Database
        from superset.models.dashboard import Dashboard
        from superset.models.slice import Slice

        database = db.session.query(Database).filter_by(database_name=DB_NAME).one()
        print(f"подключение: {database.id} «{database.database_name}»")

        datasets = {}
        for table_name, sql, dttm, description in DATASETS:
            ds = (db.session.query(SqlaTable)
                  .filter_by(table_name=table_name, schema="dbo", database_id=database.id)
                  .one_or_none())
            if ds is None:
                ds = SqlaTable(table_name=table_name, schema="dbo",
                               database_id=database.id, sql=sql.strip(),
                               description=description, main_dttm_col=dttm)
                db.session.add(ds)
                db.session.flush()
                print(f"  набор {table_name}: создан id={ds.id}")
            else:
                ds.sql = sql.strip()
                ds.description = description
                ds.main_dttm_col = dttm
                print(f"  набор {table_name}: обновлён id={ds.id}")
            db.session.commit()
            ds.fetch_metadata()
            db.session.commit()
            if ds.main_dttm_col != dttm:
                ds.main_dttm_col = dttm
                db.session.commit()
            datasets[table_name] = ds
            print(f"    колонок: {len(ds.columns)}")

        q = datasets["dm_exchange_queue"]
        e = datasets["dm_exchange_errors"]

        total = count("Записей")
        specs = [
            (q, *bignum("Обмен: всего записей в очередях", total,
                        "записи импорта и экспорта")),
            (e, *bignum("Обмен: в ошибке", count("В ошибке"),
                        "записи с признаком ошибки")),
            (q, *bar("Обмен: по состоянию", "state", [total], horizontal=True)),
            (q, *bar("Обмен: по направлению", "direction_ru", [total])),
            (q, *bar("Обмен: по типам сообщений", "message_type", [total],
                     horizontal=True, row_limit=25)),
            (q, *trend("Обмен: записи по дням", "request_day", [total])),
            (e, *bar("Обмен: ошибки по причинам", "error_group",
                     [count("Записей")], horizontal=True, row_limit=20)),
            (e, *bar("Обмен: ошибки по типам сообщений", "message_type",
                     [count("Записей")], horizontal=True, row_limit=20)),
            (e, *table("Обмен: записи в ошибке", ["message_type", "error_group", "age_days", "tries"],
                       [count("Записей")], row_limit=200)),
        ]

        for chart in db.session.query(Slice).filter(
                Slice.slice_name.like(CHART_PREFIX + "%")).all():
            db.session.delete(chart)
        for dash in db.session.query(Dashboard).filter_by(slug=DASH_SLUG).all():
            db.session.delete(dash)
        db.session.commit()

        created = []
        for dataset, name, params in specs:
            full = {"datasource": f"{dataset.id}__table", **params}
            chart = Slice(
                slice_name=name, viz_type=params["viz_type"], datasource_type="table",
                datasource_id=dataset.id, params=json.dumps(full, ensure_ascii=False),
                description=f"{name} — витрина {dataset.table_name} (MRDN_Exchange)",
                created_by_fk=1, changed_by_fk=1,
            )
            chart.query_context = json.dumps({
                "datasource": {"id": dataset.id, "type": "table"},
                "queries": [build_query(params)],
                "form_data": full, "result_type": "full", "result_format": "json",
                "force": False,
            }, ensure_ascii=False)
            db.session.add(chart)
            db.session.flush()
            created.append(chart)
            print(f"  диаграмма {chart.id}: {name}")

        by_name = {c.slice_name: c for c in created}

        layout = [
            [("Обмен: всего записей в очередях", 4), ("Обмен: в ошибке", 4),
             ("Обмен: по направлению", 4)],
            [("Обмен: записи по дням", 12)],
            [("Обмен: по состоянию", 5), ("Обмен: по типам сообщений", 7)],
            [("Обмен: ошибки по причинам", 6), ("Обмен: ошибки по типам сообщений", 6)],
            [("Обмен: записи в ошибке", 12)],
        ]

        grid = {
            "DASHBOARD_VERSION_KEY": "v2",
            "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID", "children": ["GRID_ID"]},
            "HEADER_ID": {"id": "HEADER_ID", "type": "HEADER",
                          "meta": {"text": "Обмен с 1С: очереди и ошибки"}},
            "GRID_ID": {"type": "GRID", "id": "GRID_ID", "children": [], "parents": ["ROOT_ID"]},
        }
        dash_slices = []
        idx = 0
        for row_no, row in enumerate(layout, start=1):
            row_id = f"ROW-{row_no}"
            children = []
            for name, width in row:
                idx += 1
                cid = f"CHART-{idx}"
                chart = by_name[name]
                grid[cid] = {
                    "type": "CHART", "id": cid, "children": [],
                    "parents": ["ROOT_ID", "GRID_ID", row_id],
                    "meta": {"chartId": chart.id, "height": 50, "width": width,
                             "header_font_size": 15, "sliceName": name,
                             "uuid": str(uuid.uuid4())},
                }
                children.append(cid)
                dash_slices.append(chart)
            grid[row_id] = {"type": "ROW", "id": row_id, "children": children,
                            "parents": ["ROOT_ID", "GRID_ID"],
                            "meta": {"background": "BACKGROUND_TRANSPARENT"}}
            grid["GRID_ID"]["children"].append(row_id)

        meta = {
            "color_scheme": "t_obmen", "refresh_frequency": 0, "label_colors": {},
            "timed_refresh_immune_slices": [], "expanded_slices": {},
            "shared_label_colors": [], "map_label_colors": {},
            "cross_filters_enabled": True,
            "native_filter_configuration": [
                {
                    "id": "NATIVE_FILTER-period", "name": "Период",
                    "filterType": "filter_time",
                    "targets": [{"datasetId": d.id} for d in datasets.values()],
                    "defaultValue": "No filter",
                    "scope": {"rootPath": ["ROOT_ID"], "excluded": []},
                    "controlValues": {"enableEmptyFilter": False},
                    "cascadeParentIds": [], "type": "NATIVE_FILTER",
                }
            ],
        }

        dash = Dashboard(
            dashboard_title="Обмен с 1С: очереди и ошибки", slug=DASH_SLUG,
            position_json=json.dumps(grid, ensure_ascii=False),
            json_metadata=json.dumps(meta, ensure_ascii=False),
            description="Очереди обмена с 1С: объём, состояние, ошибки и их причины",
            published=True, created_by_fk=1, changed_by_fk=1,
        )
        dash.slices = dash_slices
        db.session.add(dash)
        db.session.commit()

        for sql in (
            "insert into dashboard_user (user_id, dashboard_id) values (1, :d) on conflict do nothing",
        ):
            db.session.execute(text(sql), {"d": dash.id})
        # Анонимный просмотр при DASHBOARD_RBAC держится на dashboard_roles
        db.session.execute(
            text("insert into dashboard_roles (dashboard_id, role_id) values (:d, 2) on conflict do nothing"),
            {"d": dash.id})
        for chart in created:
            db.session.execute(
                text("insert into slice_user (user_id, slice_id) values (1, :s) on conflict do nothing"),
                {"s": chart.id})
        db.session.commit()

        print(f"\nдашборд {dash.id}: /superset/dashboard/{DASH_SLUG}/ ({len(created)} диаграмм)")

        # --- самопроверка тем же путём, что браузер ------------------------
        import os
        import re

        app.config["WTF_CSRF_ENABLED"] = False
        client = app.test_client()
        html = client.get("/login/").data.decode("utf-8", "ignore")
        csrf = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html)
        client.post("/login/", data={"username": "admin", "password": os.environ.get("ADMIN_PASSWORD"),
                                     "csrf_token": csrf.group(1) if csrf else "", "provider": "db"},
                    follow_redirects=True)

        bad = []
        print()
        for chart in created:
            res = client.get(f"/api/v1/chart/{chart.id}/data/?format=json")
            j = res.get_json() or {}
            row = (j.get("result") or [{}])[0] if isinstance(j.get("result"), list) else {}
            err = row.get("error") or (None if res.status_code == 200 else j.get("message"))
            rows = len(row.get("data") or [])
            if err or rows == 0:
                bad.append((chart.slice_name, f"http={res.status_code} err={err} rows={rows}"))
                print(f"  [ПЛОХО] {chart.id} {chart.slice_name}: {err or '0 строк'}")
            else:
                print(f"  [ok {rows:>4}] {chart.id} {chart.slice_name}")

        print()
        if bad:
            print(f"ПРОБЛЕМЫ ({len(bad)}):")
            for name, why in bad:
                print(f"  - {name}: {why}")
        else:
            print(f"Проверка пройдена: все {len(created)} диаграмм отдают данные.")


if __name__ == "__main__":
    main()
