"""Витрина остатков и параллельный дашборд Superset (LV_MERIDIAN).

Что создаёт:
  1. виртуальный набор данных `dm_stock` (SQL ниже) на подключении «LV_MERIDIAN (WMS)»;
  2. четыре диаграммы: тахометр «всего единиц», bar по зонам, «свободно/резерв», таблица товаров;
  3. дашборд «Остатки склада (параллельный отчёт)», slug `wms-stock-parallel`.

Скрипт идемпотентен: диаграммы с префиксом «Остатки (параллельно)» и дашборд с этим slug
пересоздаются, остальные объекты не затрагиваются.

Запуск на wmssql-analytics:
    docker cp build_stock_dashboard.py superset:/tmp/
    docker exec superset python /tmp/build_stock_dashboard.py

После создания диаграмм при необходимости прогнать `backfill_query_context.py`
(здесь query_context пишется сразу, но если Superset обновится — пригодится).

Проверено 2026-11-25: 399 строк остатка, итог 58 230 единиц, 14 зон,
анонимный просмотр дашборда — HTTP 200.
"""

import json
import uuid

from superset.app import create_app

app = create_app()

DATASET_SQL = """SELECT s.stk_ID AS stock_id,
       l.loc_Code AS loc_code,
       ISNULL(z.zon_code, N'-') AS zone_code,
       ISNULL(z.zon_Description, N'Без зоны') AS zone,
       p.prd_PrimaryCode AS product_code,
       ISNULL(pl.prdl_Description, N'-') AS product_name,
       ISNULL(ul.untl_Description, N'-') AS unit,
       CAST(s.stk_CUQuantity AS float) AS qty,
       CAST(s.stk_CUQuantityFree AS float) AS qty_free,
       CAST(s.stk_CUQuantity - s.stk_CUQuantityFree AS float) AS qty_reserved
FROM dbo.LV_Stock s
JOIN dbo.LV_Location l ON l.loc_ID = s.stk_LocationID
OUTER APPLY (SELECT TOP 1 zz.zon_Description, zz.zon_code
             FROM dbo.LV_LocZone lz JOIN dbo.LV_Zone zz ON zz.zon_ID = lz.lzn_ZoneID
             WHERE lz.lzn_LocationID = l.loc_ID) z
JOIN dbo.LV_Product p ON p.prd_ID = s.stk_ProductID
LEFT JOIN dbo.LV_ProductLang pl ON pl.prdl_ProductID = p.prd_ID AND pl.prdl_LanguageID = 4
LEFT JOIN dbo.LV_ItemUnit iu ON iu.itu_ID = s.stk_CUItemUnitID
LEFT JOIN dbo.LV_Unit u ON u.unt_ID = iu.itu_UnitID
LEFT JOIN dbo.LV_UnitLang ul ON ul.untl_UnitID = u.unt_ID AND ul.untl_LanguageID = 4
"""

DB_NAME = "LV_MERIDIAN (WMS)"
DASH_SLUG = "wms-stock-parallel"
CHART_PREFIX = "Остатки (параллельно)"


def build_queries(params: dict) -> list[dict]:
    columns = [params["x_axis"]] if params.get("x_axis") else list(params.get("groupby") or [])
    metrics = params.get("metrics") or ([params["metric"]] if params.get("metric") else [])
    return [
        {
            "columns": columns,
            "metrics": metrics,
            "row_limit": params.get("row_limit", 100),
            "row_offset": 0,
            "orderby": [],
            "is_timeseries": False,
            "extras": {"having": "", "where": ""},
            "filters": [],
            "annotation_layers": [],
            "series_limit": 0,
            "order_desc": bool(params.get("order_desc", True)),
            "url_params": {},
            "custom_form_data": {},
            "apply_fetch_values_predicate": False,
        }
    ]


def main() -> None:
    with app.app_context():
        from sqlalchemy import text

        from superset import db
        from superset.connectors.sqla.models import SqlaTable
        from superset.models.core import Database
        from superset.models.dashboard import Dashboard
        from superset.models.slice import Slice

        database = db.session.query(Database).filter_by(database_name=DB_NAME).one()

        dataset = (
            db.session.query(SqlaTable)
            .filter_by(table_name="dm_stock", schema="dbo", database_id=database.id)
            .one_or_none()
        )
        if dataset is None:
            dataset = SqlaTable(
                table_name="dm_stock",
                schema="dbo",
                database_id=database.id,
                sql=DATASET_SQL,
                description="Витрина остатков LV_Stock: товар, локация, зона, единица, количество/свободно/резерв",
            )
            db.session.add(dataset)
            db.session.flush()
            print(f"набор данных создан: id={dataset.id}")
        else:
            print(f"набор данных уже есть: id={dataset.id}")

        # чистим предыдущий прогон только своего
        for chart in db.session.query(Slice).filter(Slice.slice_name.like(CHART_PREFIX + "%")).all():
            db.session.delete(chart)
        for dash in db.session.query(Dashboard).filter_by(slug=DASH_SLUG).all():
            db.session.delete(dash)
        db.session.commit()

        def make_chart(name: str, viz: str, params: dict) -> Slice:
            full = {"datasource": f"{dataset.id}__table", "viz_type": viz, **params}
            chart = Slice(
                slice_name=name,
                viz_type=viz,
                datasource_type="table",
                datasource_id=dataset.id,
                params=json.dumps(full, ensure_ascii=False),
                description="Параллельный отчёт по остаткам (LV_MERIDIAN)",
                created_by_fk=1,
                changed_by_fk=1,
            )
            chart.query_context = json.dumps(
                {
                    "datasource": {"id": dataset.id, "type": "table"},
                    "queries": build_queries(params),
                    "form_data": full,
                    "result_type": "full",
                    "result_format": "json",
                    "force": False,
                },
                ensure_ascii=False,
            )
            db.session.add(chart)
            db.session.flush()
            print(f"диаграмма {chart.id}: {name}")
            return chart

        m_qty = {"expressionType": "SIMPLE", "column": {"column_name": "qty"},
                 "aggregate": "SUM", "label": "Количество"}
        m_free = {"expressionType": "SIMPLE", "column": {"column_name": "qty_free"},
                  "aggregate": "SUM", "label": "Свободно"}
        m_res = {"expressionType": "SIMPLE", "column": {"column_name": "qty_reserved"},
                 "aggregate": "SUM", "label": "Резерв"}

        charts = [
            make_chart(f"{CHART_PREFIX}: всего единиц", "gauge_chart", {
                "metric": m_qty, "groupby": [], "adhoc_filters": [], "row_limit": 10,
                "min_val": 0, "max_val": 100000,
                "start_angle": 225, "end_angle": -45,
                "color_scheme": "t_ostatki", "font_size": 16, "number_format": "SMART_NUMBER",
                "show_pointer": True, "animation": True, "show_axis_tick": False,
                "show_split_line": False, "split_number": 3, "show_progress": True, "overlap": True,
                "intervals": "30000,45000,60000",
            }),
            make_chart(f"{CHART_PREFIX}: по зонам", "echarts_timeseries_bar", {
                "x_axis": "zone", "metrics": [m_qty], "groupby": [], "adhoc_filters": [],
                "row_limit": 50, "color_scheme": "t_ostatki", "orientation": "vertical",
                "show_legend": True, "legendType": "scroll", "legendOrientation": "top",
                "show_value": True, "x_axis_sort_asc": False, "xAxisLabelRotation": 45,
                "y_axis_format": "SMART_NUMBER", "rich_tooltip": True, "show_toolbar": True,
            }),
            make_chart(f"{CHART_PREFIX}: свободно и резерв", "echarts_timeseries_bar", {
                "x_axis": "zone", "metrics": [m_free, m_res], "groupby": [], "adhoc_filters": [],
                "row_limit": 50, "color_scheme": "t_ostatki", "orientation": "vertical",
                "show_legend": True, "legendType": "scroll", "legendOrientation": "top",
                "show_value": False, "x_axis_sort_asc": False, "xAxisLabelRotation": 45,
                "y_axis_format": "SMART_NUMBER", "rich_tooltip": True, "show_toolbar": True,
            }),
            make_chart(f"{CHART_PREFIX}: товары", "table", {
                "groupby": ["product_code", "product_name", "unit"],
                "metrics": [m_qty, m_free], "adhoc_filters": [], "row_limit": 100,
                "order_desc": True, "show_cell_bars": True, "color_pn": True,
                "timeseries_limit_metric": m_qty,
            }),
        ]

        grid = {
            "DASHBOARD_VERSION_KEY": "v2",
            "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID", "children": ["GRID_ID"]},
            "HEADER_ID": {"id": "HEADER_ID", "type": "HEADER",
                          "meta": {"text": "Остатки склада (параллельный отчёт)"}},
            "GRID_ID": {"type": "GRID", "id": "GRID_ID",
                        "children": ["ROW-1", "ROW-2"], "parents": ["ROOT_ID"]},
            "ROW-1": {"type": "ROW", "id": "ROW-1", "children": ["CHART-1", "CHART-2"],
                      "parents": ["ROOT_ID", "GRID_ID"], "meta": {"background": "BACKGROUND_TRANSPARENT"}},
            "ROW-2": {"type": "ROW", "id": "ROW-2", "children": ["CHART-3", "CHART-4"],
                      "parents": ["ROOT_ID", "GRID_ID"], "meta": {"background": "BACKGROUND_TRANSPARENT"}},
        }
        for i, chart in enumerate(charts, start=1):
            row = "ROW-1" if i <= 2 else "ROW-2"
            grid[f"CHART-{i}"] = {
                "type": "CHART", "id": f"CHART-{i}", "children": [],
                "parents": ["ROOT_ID", "GRID_ID", row],
                "meta": {"chartId": chart.id, "height": 50, "width": 6,
                         "header_font_size": 15, "sliceName": chart.slice_name,
                         "uuid": str(uuid.uuid4())},
            }

        dash = Dashboard(
            dashboard_title="Остатки склада (параллельный отчёт)",
            slug=DASH_SLUG,
            position_json=json.dumps(grid, ensure_ascii=False),
            json_metadata=json.dumps(
                {
                    "color_scheme": "t_ostatki", "refresh_frequency": 0,
                    "label_colors": {}, "timed_refresh_immune_slices": [],
                    "expanded_slices": {}, "shared_label_colors": [],
                    "map_label_colors": {}, "cross_filters_enabled": True,
                },
                ensure_ascii=False,
            ),
            description="Параллельная витрина остатков по dm_stock",
            published=True,
            created_by_fk=1,
            changed_by_fk=1,
        )
        dash.slices = charts
        db.session.add(dash)
        db.session.commit()

        # владелец — admin (иначе дашборд не виден в списках этому пользователю)
        db.session.execute(
            text("insert into dashboard_user (user_id, dashboard_id) values (1, :d) "
                 "on conflict do nothing"),
            {"d": dash.id},
        )
        for chart in charts:
            db.session.execute(
                text("insert into slice_user (user_id, slice_id) values (1, :s) "
                     "on conflict do nothing"),
                {"s": chart.id},
            )
        db.session.commit()

        print(f"дашборд {dash.id} /superset/dashboard/{DASH_SLUG}/ — {len(charts)} диаграммы")


if __name__ == "__main__":
    main()
