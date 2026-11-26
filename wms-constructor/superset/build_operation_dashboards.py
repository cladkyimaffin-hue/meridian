"""Витрины «Движение», «Приходы», «Расход» и их дашборды в Superset.

Что создаёт:
  наборы данных (virtual datasets на подключении «LV_MERIDIAN (WMS)»):
    dm_movement      — строки журнала LV_LogStock с расшифровками;
    dm_receipts      — приходы на уровне документа;
    dm_receipt_lines — строки приходов с единицей измерения;
    dm_orders        — расходные заказы на уровне документа;
    dm_order_lines   — строки заказов с единицей измерения;
  три дашборда:
    «Движение товара» /wms-movement/
    «Приходы»         /wms-receipts/
    «Расход»          /wms-orders/

Почему количества разнесены на уровень строки: в базе четыре единицы
(Штука(и), Пара, метр, Комплект), и суммировать их между собой нельзя.
Поэтому на дашбордах количество всегда выводится либо в разрезе единицы,
либо не выводится вовсе (считаются документы и операции).

Скрипт идемпотентен: повторный запуск пересоздаёт наборы данных с теми же
именами (SQL обновляется), а диаграммы с префиксами «Движение:», «Приходы:»,
«Расход:» и дашборды с теми же slug — заново.

Запуск на wmssql-analytics:
    docker cp build_operation_dashboards.py superset:/tmp/
    docker exec superset python /tmp/build_operation_dashboards.py
"""

import json
import uuid

from superset.app import create_app

app = create_app()

DB_NAME = "LV_MERIDIAN (WMS)"

MOVEMENT_SQL = """
SELECT g.log_ID AS log_id,
       g.log_DateTime AS log_datetime,
       CAST(g.log_DateTime AS date) AS day,
       DATEPART(hour, g.log_DateTime) AS hour_of_day,
       LTRIM(RTRIM(ISNULL(m.msg_Greek, tt.trt_MessageCode))) AS operation,
       tt.trt_Code AS operation_code,
       ISNULL(p.prd_PrimaryCode, '-') AS product_code,
       ISNULL(pl.prdl_Description, '-') AS product_name,
       ISNULL(l.loc_Code, '-') AS location_code,
       ISNULL(z.zon_code, '-') AS zone_code,
       ISNULL(ul.untl_Description, '-') AS unit,
       CAST(ls.lsk_CUQuantity AS float) AS qty,
       ABS(CAST(ls.lsk_CUQuantity AS float)) AS qty_abs,
       ISNULL(uu.usr_Login, '-') AS user_login
FROM dbo.LV_LogStock ls
JOIN dbo.LV_Log g ON g.log_ID = ls.lsk_LogID
LEFT JOIN dbo.LV_TransactionType tt ON tt.trt_ID = g.log_TransactionTypeID
LEFT JOIN dbo.LV_Messages m ON m.msg_code = tt.trt_MessageCode AND m.msg_languageID = 4
LEFT JOIN dbo.LV_Product p ON p.prd_ID = ls.lsk_ProductID
LEFT JOIN dbo.LV_ProductLang pl ON pl.prdl_ProductID = p.prd_ID AND pl.prdl_LanguageID = 4
LEFT JOIN dbo.LV_Location l ON l.loc_ID = ls.lsk_LocationID
OUTER APPLY (SELECT TOP 1 zz.zon_code FROM dbo.LV_LocZone lz
             JOIN dbo.LV_Zone zz ON zz.zon_ID = lz.lzn_ZoneID
             WHERE lz.lzn_LocationID = l.loc_ID) z
LEFT JOIN dbo.LV_ItemUnit iu ON iu.itu_ID = ls.lsk_ItemUnitID
LEFT JOIN dbo.LV_Unit u ON u.unt_ID = iu.itu_UnitID
LEFT JOIN dbo.LV_UnitLang ul ON ul.untl_UnitID = u.unt_ID AND ul.untl_LanguageID = 4
LEFT JOIN dbo.LV_Users uu ON uu.usr_ID = g.log_UserID
"""

RECEIPTS_SQL = """
SELECT r.rct_ID AS receipt_id,
       r.rct_Code AS receipt_code,
       LTRIM(RTRIM(ISNULL(t.rtt_Description, '-'))) AS receipt_type,
       ISNULL(t.rtt_Code, '-') AS receipt_type_code,
       ISNULL(NULLIF(c.cmp_FullName, ''),
              ISNULL(c.cmp_ShortName, ISNULL(s.spl_Code, '-'))) AS supplier,
       r.rct_InputDate AS input_datetime,
       CAST(r.rct_InputDate AS date) AS input_day,
       CAST(r.rct_ActualDate AS date) AS actual_day,
       CAST(r.rct_ExpectedDate AS date) AS expected_day,
       LTRIM(RTRIM(ISNULL(m.msg_Greek, ps.pst_MessageCode))) AS status,
       r.rct_LineCount AS line_count,
       ISNULL(it.lines, 0) AS lines_with_items,
       CAST(ISNULL(r.rct_NetWeight, 0) AS float) AS net_weight
FROM dbo.LV_Receipt r
LEFT JOIN dbo.LV_ReceiptType t ON t.rtt_ID = r.rct_TypeID
LEFT JOIN dbo.LV_Supplier s ON s.spl_ID = r.rct_SupplierID
LEFT JOIN dbo.LV_Company c ON c.cmp_ID = s.spl_CompanyID
LEFT JOIN dbo.LV_ProgressStatus ps ON ps.pst_ID = r.rct_ProgressID
LEFT JOIN dbo.LV_Messages m ON m.msg_code = ps.pst_MessageCode AND m.msg_languageID = 4
OUTER APPLY (SELECT COUNT(*) lines FROM dbo.LV_ReceiptItem i
             WHERE i.rci_ReceiptID = r.rct_ID) it
"""

RECEIPT_LINES_SQL = """
SELECT i.rci_ID AS line_id,
       r.rct_Code AS receipt_code,
       r.rct_InputDate AS input_datetime,
       CAST(r.rct_InputDate AS date) AS input_day,
       LTRIM(RTRIM(ISNULL(t.rtt_Description, '-'))) AS receipt_type,
       ISNULL(p.prd_PrimaryCode, '-') AS product_code,
       ISNULL(pl.prdl_Description, '-') AS product_name,
       ISNULL(ul.untl_Description, '-') AS unit,
       CAST(ISNULL(i.rci_ExpQuantity, 0) AS float) AS expected_qty,
       CAST(ISNULL(i.rci_ActQuantity, 0) AS float) AS actual_qty,
       CAST(ISNULL(i.rci_RetainedQuantity, 0) AS float) AS retained_qty
FROM dbo.LV_ReceiptItem i
JOIN dbo.LV_Receipt r ON r.rct_ID = i.rci_ReceiptID
LEFT JOIN dbo.LV_ReceiptType t ON t.rtt_ID = r.rct_TypeID
LEFT JOIN dbo.LV_Product p ON p.prd_ID = i.rci_ProductID
LEFT JOIN dbo.LV_ProductLang pl ON pl.prdl_ProductID = p.prd_ID AND pl.prdl_LanguageID = 4
LEFT JOIN dbo.LV_ItemUnit iu ON iu.itu_ID = i.rci_ActItemUnitID
LEFT JOIN dbo.LV_Unit u ON u.unt_ID = iu.itu_UnitID
LEFT JOIN dbo.LV_UnitLang ul ON ul.untl_UnitID = u.unt_ID AND ul.untl_LanguageID = 4
"""

ORDERS_SQL = """
SELECT o.ord_ID AS order_id,
       o.ord_Code AS order_code,
       LTRIM(RTRIM(ISNULL(t.ort_Description, '-'))) AS order_type,
       ISNULL(t.ort_Code, '-') AS order_type_code,
       ISNULL(NULLIF(c.cmp_FullName, ''),
              ISNULL(c.cmp_ShortName, ISNULL(u.cus_Code, '-'))) AS customer,
       o.ord_InputDate AS input_datetime,
       CAST(o.ord_InputDate AS date) AS input_day,
       CAST(o.ord_ExpShipDate AS date) AS expected_ship_day,
       LTRIM(RTRIM(ISNULL(m.msg_Greek, st.ors_MessageCode))) AS status,
       o.ord_LineCount AS line_count,
       ISNULL(it.lines, 0) AS lines_with_items,
       CAST(ISNULL(o.ord_Value, 0) AS float) AS order_value
FROM dbo.LV_Order o
LEFT JOIN dbo.LV_OrderType t ON t.ort_ID = o.ord_TypeID
LEFT JOIN dbo.LV_Customer u ON u.cus_ID = o.ord_CustomerID
LEFT JOIN dbo.LV_Company c ON c.cmp_ID = u.cus_CompanyID
LEFT JOIN dbo.LV_OrderStatus st ON st.ors_ID = o.ord_StatusID
LEFT JOIN dbo.LV_Messages m ON m.msg_code = st.ors_MessageCode AND m.msg_languageID = 4
OUTER APPLY (SELECT COUNT(*) lines FROM dbo.LV_OrderItem oi
             WHERE oi.ori_OrderID = o.ord_ID) it
"""

ORDER_LINES_SQL = """
SELECT oi.ori_ID AS line_id,
       o.ord_Code AS order_code,
       o.ord_InputDate AS input_datetime,
       CAST(o.ord_InputDate AS date) AS input_day,
       LTRIM(RTRIM(ISNULL(t.ort_Description, '-'))) AS order_type,
       ISNULL(p.prd_PrimaryCode, '-') AS product_code,
       ISNULL(pl.prdl_Description, '-') AS product_name,
       ISNULL(ul.untl_Description, '-') AS unit,
       CAST(ISNULL(oi.ori_Quantity, 0) AS float) AS qty,
       CAST(ISNULL(si.ship_qty, 0) AS float) AS shipped_qty
FROM dbo.LV_OrderItem oi
JOIN dbo.LV_Order o ON o.ord_ID = oi.ori_OrderID
LEFT JOIN dbo.LV_OrderType t ON t.ort_ID = o.ord_TypeID
LEFT JOIN dbo.LV_Product p ON p.prd_ID = oi.ori_ProductID
LEFT JOIN dbo.LV_ProductLang pl ON pl.prdl_ProductID = p.prd_ID AND pl.prdl_LanguageID = 4
LEFT JOIN dbo.LV_ItemUnit iu ON iu.itu_ID = oi.ori_ItemUnitID
LEFT JOIN dbo.LV_Unit u ON u.unt_ID = iu.itu_UnitID
LEFT JOIN dbo.LV_UnitLang ul ON ul.untl_UnitID = u.unt_ID AND ul.untl_LanguageID = 4
OUTER APPLY (SELECT SUM(s2.osi_Quantity) ship_qty FROM dbo.LV_OrderShipItem s2
             WHERE s2.osi_OrderItemID = oi.ori_ID) si
"""

DATASETS = [
    ("dm_movement", MOVEMENT_SQL, "log_datetime",
     "Строки журнала операций LV_LogStock: дата, тип операции, товар, локация, зона, единица, количество"),
    ("dm_receipts", RECEIPTS_SQL, "input_datetime",
     "Приходы LV_Receipt на уровне документа: тип, поставщик, даты, статус, число строк"),
    ("dm_receipt_lines", RECEIPT_LINES_SQL, "input_datetime",
     "Строки приходов с товаром и единицей: ожидаемое, фактическое, удержанное количество"),
    ("dm_orders", ORDERS_SQL, "input_datetime",
     "Расходные заказы LV_Order на уровне документа: тип, клиент, даты, статус"),
    ("dm_order_lines", ORDER_LINES_SQL, "input_datetime",
     "Строки заказов с товаром и единицей: заказано и отгружено"),
]


# --- метрики -------------------------------------------------------------
# Только SQL-выражения: SIMPLE-метрика с column=None (например COUNT по всему
# набору) валит компиляцию SQLAlchemy «Cannot compile Column object until its
# 'name' is assigned». SQL-выражение работает всегда и читается человеком.

def sql_metric(expr, label):
    return {
        "expressionType": "SQL",
        "sqlExpression": expr,
        "label": label,
        "hasCustomLabel": True,
    }


def count(label="Количество"):
    return sql_metric("COUNT(1)", label)


def cdistinct(col, label):
    return sql_metric(f"COUNT(DISTINCT [{col}])", label)


def total(col, label):
    return sql_metric(f"SUM([{col}])", label)


# --- построение запроса для query_context --------------------------------

def build_query(form_data):
    """Собирает queries[0] для query_context.

    Два правила, найденные на практике (Superset 6.1.0):
      1. extras.time_range сюда НЕ кладём: API отвергает его как неизвестное
         поле ("Unknown field") и диаграмма отдаёт 400.
      2. Колонки группировки = x_axis + groupby. Если положить только groupby,
         график схлопывается в одну строку (проверено: «по типам операций»
         отдавал 1 строку вместо 17).
    Тренды строятся как обычная группировка по колонке-дате (is_timeseries
    false): режим timeseries требует main_dttm_col и падает с
    «Datetime column not provided as part table configuration».
    """
    is_ts = form_data.get("is_timeseries", False)
    if is_ts:
        columns = ["__timestamp"]
    else:
        columns = []
        x_axis = form_data.get("x_axis")
        if x_axis:
            columns.append(x_axis)
        columns.extend(form_data.get("groupby") or [])
    # big_number_total хранит метрику в поле "metric", остальные — в "metrics"
    metrics = list(form_data.get("metrics") or [])
    if not metrics and form_data.get("metric"):
        metrics = [form_data["metric"]]
    extras = {"having": "", "where": ""}
    return {
        "columns": columns,
        "metrics": metrics,
        "row_limit": form_data.get("row_limit", 100),
        "row_offset": 0,
        # orderby оставляем пустым: API отвергает непарный формат
        # («Length must be 2»), а сортировку по дате Superset делает сам
        "orderby": [],
        "is_timeseries": is_ts,
        "extras": extras,
        "filters": [],
        "annotation_layers": [],
        "series_limit": 0,
        "order_desc": bool(form_data.get("order_desc", True)),
        "url_params": {},
        "custom_form_data": {},
        "apply_fetch_values_predicate": False,
    }


# --- описания диаграмм ---------------------------------------------------

def bar(name, x_axis, metrics, *, groupby=None, row_limit=50, color=None,
        horizontal=False, show_value=True, prefix=""):
    p = {
        "viz_type": "echarts_timeseries_bar",
        "x_axis": x_axis,
        "groupby": groupby or [],
        "metrics": metrics,
        "adhoc_filters": [],
        "row_limit": row_limit,
        "orientation": "horizontal" if horizontal else "vertical",
        "show_legend": True,
        "legendType": "scroll",
        "legendOrientation": "top",
        "show_value": show_value,
        "x_axis_sort_asc": False,
        "xAxisLabelRotation": 45,
        "y_axis_format": "SMART_NUMBER",
        "rich_tooltip": True,
        "show_toolbar": True,
        "order_desc": True,
        "time_range": "No filter",
    }
    if color:
        p["color_scheme"] = color
    return f"{prefix}{name}", p


def trend(name, dttm_col, metrics, *, grain="P1D", color=None, prefix="", groupby=None):
    """Линия по дате. Строится как группировка по колонке-дате, без режима
    timeseries: у виртуального набора без main_dttm_col режим падает.
    Колонка должна быть уже усечена до дня (day / input_day) — иначе Superset
    группирует по секундам и «по дням» отдаёт тысячи точек."""
    p = {
        "viz_type": "echarts_timeseries_line",
        "x_axis": dttm_col,
        "groupby": groupby or [],
        "metrics": metrics,
        "adhoc_filters": [],
        "row_limit": 5000,
        "x_axis_time_format": "smart_date",
        "show_legend": True,
        "legendOrientation": "top",
        "markerEnabled": True,
        "markerSize": 6,
        "area": True,
        "opacity": 0.25,
        "rich_tooltip": True,
        "show_toolbar": True,
        "y_axis_format": "SMART_NUMBER",
        "order_desc": False,
        "time_range": "No filter",
    }
    if color:
        p["color_scheme"] = color
    return f"{prefix}{name}", p


def bignum(name, metric, *, subheader="", color=None, prefix=""):
    p = {
        "viz_type": "big_number_total",
        "metric": metric,
        "adhoc_filters": [],
        "subheader": subheader,
        "header_font_size": 0.4,
        "subheader_font_size": 0.125,
        "y_axis_format": "SMART_NUMBER",
        "time_range": "No filter",
    }
    if color:
        p["color_scheme"] = color
    return f"{prefix}{name}", p


def table(name, groupby, metrics, *, row_limit=200, groupby_label="", prefix=""):
    """Таблица в агрегатном режиме: все колонки, кроме метрик, уходят в groupby."""
    p = {
        "viz_type": "table",
        "query_mode": "aggregate",
        "groupby": groupby,
        "metrics": metrics,
        "adhoc_filters": [],
        "row_limit": row_limit,
        "order_desc": True,
        "show_cell_bars": True,
        "color_pn": True,
        "timeseries_limit_metric": metrics[0] if metrics else None,
        "time_range": "No filter",
    }
    if groupby_label:
        p["groupby_label"] = groupby_label
    return f"{prefix}{name}", p


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
            ds = (
                db.session.query(SqlaTable)
                .filter_by(table_name=table_name, schema="dbo", database_id=database.id)
                .one_or_none()
            )
            if ds is None:
                ds = SqlaTable(
                    table_name=table_name,
                    schema="dbo",
                    database_id=database.id,
                    sql=sql.strip(),
                    description=description,
                    main_dttm_col=dttm,
                )
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

        # --- диаграммы ---------------------------------------------------

        U_OP = "Операций"
        specs = []

        m = datasets["dm_movement"]
        specs += [
            (m, *bignum("Движение: всего операций", cdistinct("log_id", "Операций"),
                        subheader="уникальных операций в журнале")),
            (m, *trend("Движение: операции по дням", "day",
                       [count(U_OP)], color="t_dvizhenie")),
            (m, *bar("Движение: по типам операций", "operation",
                     [count(U_OP)], horizontal=True, color="t_dvizhenie")),
            (m, *bar("Движение: по зонам", "zone_code",
                     [count(U_OP)], color="t_dvizhenie")),
            (m, *bar("Движение: по сотрудникам", "user_login",
                     [count(U_OP)], horizontal=True, color="t_dvizhenie")),
            (m, *bar("Движение: количество по операциям и единицам", "operation",
                     [total("qty_abs", "Количество")], groupby=["unit"],
                     color="t_dvizhenie", show_value=False)),
            (m, *table("Движение: строки журнала",
                       ["day", "operation", "product_code", "unit",
                        "location_code", "zone_code", "user_login"],
                       [total("qty", "Количество")], row_limit=200)),
        ]

        r = datasets["dm_receipts"]
        rl = datasets["dm_receipt_lines"]
        specs += [
            (r, *bignum("Приходы: всего документов", count("Приходов"),
                        subheader="строки LV_Receipt")),
            (r, *bar("Приходы: по типам", "receipt_type",
                     [count("Приходов")], horizontal=True, color="t_prihody")),
            (r, *bar("Приходы: по статусам", "status",
                     [count("Приходов")], color="t_prihody")),
            (r, *trend("Приходы: по дням", "input_day",
                       [count("Приходов")], color="t_prihody")),
            (r, *bar("Приходы: топ поставщиков", "supplier",
                     [count("Приходов")], horizontal=True, row_limit=15,
                     color="t_prihody")),
            (r, *table("Приходы: список документов",
                       ["receipt_code", "receipt_type", "supplier",
                        "input_day", "status", "line_count"],
                       [count("Строк")], row_limit=300)),
            (rl, *bar("Приходы: ожидаемое количество по типам и единицам",
                      "receipt_type", [total("expected_qty", "Ожидается")],
                      groupby=["unit"], color="t_prihody", show_value=False)),
            (rl, *table("Приходы: строки",
                        ["receipt_code", "product_code", "unit",
                         "expected_qty", "actual_qty"],
                        [count("Строк")], row_limit=300)),
        ]

        o = datasets["dm_orders"]
        ol = datasets["dm_order_lines"]
        specs += [
            (o, *bignum("Расход: всего заказов", count("Заказов"),
                        subheader="строки LV_Order")),
            (o, *bar("Расход: по типам", "order_type",
                     [count("Заказов")], horizontal=True, color="t_rashod")),
            (o, *bar("Расход: по статусам", "status",
                     [count("Заказов")], color="t_rashod")),
            (o, *trend("Расход: по дням", "input_day",
                       [count("Заказов")], color="t_rashod")),
            (o, *bar("Расход: топ клиентов", "customer",
                     [count("Заказов")], horizontal=True, row_limit=15,
                     color="t_rashod")),
            (o, *table("Расход: список заказов",
                       ["order_code", "order_type", "customer",
                        "input_day", "status", "line_count"],
                       [count("Строк")], row_limit=300)),
            (ol, *bar("Расход: заказанное количество по типам и единицам",
                      "order_type", [total("qty", "Заказано")],
                      groupby=["unit"], color="t_rashod", show_value=False)),
            (ol, *table("Расход: строки",
                        ["order_code", "product_code", "unit", "qty", "shipped_qty"],
                        [count("Строк")], row_limit=300)),
        ]

        prefixes = ("Движение:", "Приходы:", "Расход:")
        for chart in db.session.query(Slice).filter(
                Slice.slice_name.like("Движение:%")
                | Slice.slice_name.like("Приходы:%")
                | Slice.slice_name.like("Расход:%")
        ).all():
            db.session.delete(chart)
        for slug in ("wms-movement", "wms-receipts", "wms-orders"):
            for dash in db.session.query(Dashboard).filter_by(slug=slug).all():
                db.session.delete(dash)
        db.session.commit()

        created = []
        for dataset, name, params in specs:
            full = {"datasource": f"{dataset.id}__table", **params}
            chart = Slice(
                slice_name=name,
                viz_type=params["viz_type"],
                datasource_type="table",
                datasource_id=dataset.id,
                params=json.dumps(full, ensure_ascii=False),
                description=f"{name} — витрина {dataset.table_name} (LV_MERIDIAN)",
                created_by_fk=1,
                changed_by_fk=1,
            )
            chart.query_context = json.dumps(
                {
                    "datasource": {"id": dataset.id, "type": "table"},
                    "queries": [build_query(params)],
                    "form_data": full,
                    "result_type": "full",
                    "result_format": "json",
                    "force": False,
                },
                ensure_ascii=False,
            )
            db.session.add(chart)
            db.session.flush()
            created.append(chart)
            print(f"  диаграмма {chart.id}: {name}")

        by_name = {c.slice_name: c for c in created}

        def make_dashboard(title, slug, description, layout, color):
            """layout: список строк, каждая — список (имя диаграммы, ширина)."""
            grid = {
                "DASHBOARD_VERSION_KEY": "v2",
                "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID", "children": ["GRID_ID"]},
                "HEADER_ID": {"id": "HEADER_ID", "type": "HEADER",
                              "meta": {"text": title}},
                "GRID_ID": {"type": "GRID", "id": "GRID_ID",
                            "children": [], "parents": ["ROOT_ID"]},
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
                grid[row_id] = {
                    "type": "ROW", "id": row_id, "children": children,
                    "parents": ["ROOT_ID", "GRID_ID"],
                    "meta": {"background": "BACKGROUND_TRANSPARENT"},
                }
                grid["GRID_ID"]["children"].append(row_id)

            meta = {
                "color_scheme": color,
                "refresh_frequency": 0,
                "label_colors": {},
                "timed_refresh_immune_slices": [],
                "expanded_slices": {},
                "shared_label_colors": [],
                "map_label_colors": {},
                "cross_filters_enabled": True,
            }
            ds_ids = sorted({c.datasource_id for c in dash_slices})
            meta["native_filter_configuration"] = [
                {
                    "id": "NATIVE_FILTER-period",
                    "name": "Период",
                    "filterType": "filter_time",
                    "targets": [{"datasetId": i} for i in ds_ids],
                    "defaultValue": "No filter",
                    "scope": {"rootPath": ["ROOT_ID"], "excluded": []},
                    "controlValues": {"enableEmptyFilter": False},
                    "cascadeParentIds": [],
                    "type": "NATIVE_FILTER",
                }
            ]

            dash = Dashboard(
                dashboard_title=title,
                slug=slug,
                position_json=json.dumps(grid, ensure_ascii=False),
                json_metadata=json.dumps(meta, ensure_ascii=False),
                description=description,
                published=True,
                created_by_fk=1,
                changed_by_fk=1,
            )
            dash.slices = dash_slices
            db.session.add(dash)
            db.session.flush()
            return dash

        d1 = make_dashboard(
            "Движение товара", "wms-movement",
            "Журнал операций склада: типы, зоны, сотрудники, количество по единицам",
            [
                [("Движение: всего операций", 4), ("Движение: по зонам", 8)],
                [("Движение: операции по дням", 12)],
                [("Движение: по типам операций", 6), ("Движение: по сотрудникам", 6)],
                [("Движение: количество по операциям и единицам", 12)],
                [("Движение: строки журнала", 12)],
            ],
            "t_dvizhenie",
        )
        d2 = make_dashboard(
            "Приходы", "wms-receipts",
            "Приходные документы: типы, поставщики, статусы, строки по единицам",
            [
                [("Приходы: всего документов", 4), ("Приходы: по статусам", 8)],
                [("Приходы: по дням", 12)],
                [("Приходы: по типам", 6), ("Приходы: топ поставщиков", 6)],
                [("Приходы: ожидаемое количество по типам и единицам", 12)],
                [("Приходы: список документов", 12)],
                [("Приходы: строки", 12)],
            ],
            "t_prihody",
        )
        d3 = make_dashboard(
            "Расход", "wms-orders",
            "Расходные заказы: типы, клиенты, статусы, строки по единицам",
            [
                [("Расход: всего заказов", 4), ("Расход: по статусам", 8)],
                [("Расход: по дням", 12)],
                [("Расход: по типам", 6), ("Расход: топ клиентов", 6)],
                [("Расход: заказанное количество по типам и единицам", 12)],
                [("Расход: список заказов", 12)],
                [("Расход: строки", 12)],
            ],
            "t_rashod",
        )
        db.session.commit()

        for dash in (d1, d2, d3):
            db.session.execute(
                text("insert into dashboard_user (user_id, dashboard_id) values (1, :d) "
                     "on conflict do nothing"),
                {"d": dash.id},
            )
            # Анонимный просмотр при DASHBOARD_RBAC держится на таблице
            # dashboard_roles: без записи для роли Public дашборд отдаёт 302
            # на /login/. Права datasource_access при этом не нужны —
            # достаточно роли Public на сам дашборд (проверено на
            # wms-stock-parallel, который открывается анонимно).
            db.session.execute(
                text("insert into dashboard_roles (dashboard_id, role_id) values (:d, 2) "
                     "on conflict do nothing"),
                {"d": dash.id},
            )
        for chart in created:
            db.session.execute(
                text("insert into slice_user (user_id, slice_id) values (1, :s) "
                     "on conflict do nothing"),
                {"s": chart.id},
            )
        db.session.commit()

        print()
        for dash in (d1, d2, d3):
            print(f"дашборд {dash.id}: /superset/dashboard/{dash.slug}/ "
                  f"({len(dash.slices)} диаграмм)")

        # --- самопроверка через настоящий API -----------------------------
        # Раньше проверка шла через QueryContextFactory, но она собирала запрос
        # из пустого queries=[{}] и всегда возвращала «Empty query?» — то есть
        # не проверяла ничего. Здесь идём тем же путём, что браузер.
        print()
        import os
        import re

        app.config["WTF_CSRF_ENABLED"] = False
        client = app.test_client()
        html = client.get("/login/").data.decode("utf-8", "ignore")
        csrf = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html)
        client.post(
            "/login/",
            data={"username": "admin", "password": os.environ.get("ADMIN_PASSWORD"),
                  "csrf_token": csrf.group(1) if csrf else "", "provider": "db"},
            follow_redirects=True,
        )
        me = (client.get("/api/v1/me/").get_json() or {}).get("result", {})
        print(f"вход в API: {me.get('username')} (аноним: {me.get('is_anonymous')})")

        bad = []
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

        # --- анонимный доступ к дашбордам (как увидит пользователь) -------
        print()
        anon = app.test_client()
        for dash in (d1, d2, d3):
            res = anon.get(f"/superset/dashboard/{dash.slug}/")
            status = "ok" if res.status_code == 200 else f"ПЛОХО http={res.status_code}"
            print(f"  анонимно {dash.slug}: {status}")


if __name__ == "__main__":
    main()
