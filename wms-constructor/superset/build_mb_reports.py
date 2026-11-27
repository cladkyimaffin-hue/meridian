#!/usr/bin/env python3
"""Отчёты, перенесённые из Metabase: витрины данных и дашборды Superset.

Источник запросов — отчёты Metabase (дашборды 35, 36, 37, 39, 42, 44, 46, 47).
Каждый отчёт Metabase устроен однотипно: несколько запросов, каждый возвращает
готовую таблицу с русскими заголовками столбцов. В Superset такие запросы ложатся
на виртуальный набор данных (`sql` набора = текст запроса), а на дашборде
становятся таблицами в режиме «сырых» данных (`query_mode: raw`, `all_columns`).

Почему витрина на каждый запрос, а не одна общая: в исходных отчётах разные
запросы считают разные сущности (остатки, ячейки, планы пересчёта, очереди).
Свести их в одну таблицу можно только выдумав общую гранулярность, а это
меняет цифры. Одна витрина = один запрос = те же числа, что в Metabase.

Что создаётся:
  наборы данных dm_rpt_<ключ>_<n>  (по одному на запрос);
  диаграммы «<Тема>: <Название запроса>» — таблицы;
  дашборды с slug из SPEC — по разделу отчётов.

Применяются палитры и оформление из sdesign.py (как у остальных отчётов),
включая баннер с кнопкой «← Главная» (его ставит apply_portal_chrome.py).

Скрипт идемпотентен: наборы обновляются по имени, диаграммы с префиксом темы
и дашборды с теми же slug пересоздаются.

Запуск на wmssql-analytics:
    docker cp mb_reports_fixed.json build_mb_reports.py superset:/tmp/
    docker exec superset python /tmp/build_mb_reports.py
"""

import json
import uuid

from superset.app import create_app

app = create_app()

DB_NAME = "LV_MERIDIAN (WMS)"
DATA_FILE = "/tmp/mb_reports_ss.json"

# тема -> палитра (должна совпадать с sdesign.THEMES)
PALETTE = {
    "Остатки": "t_ostatki",
    "Приходы": "t_prihody",
    "Расход и заказы": "t_rashod",
    "Задачи": "t_zadachi",
    "Движение": "t_dvizhenie",
    "Обмен с 1С": "t_obmen",
}

# slug -> (название дашборда, тема, описание)
SPEC = {
    "wms-stock-issues": ("Остатки: проблемные", "Остатки",
                         "Проблемные остатки: отрицательные количества, непригодный товар, причины резерва"),
    "wms-places": ("Места хранения", "Остатки",
                   "Ячейки склада: занятость, блокировки, типы отбора, резерв и непригодность"),
    "wms-inventory": ("Инвентаризация ячеек: покрытие и пересчёты", "Остатки",
                      "Инвентаризация: покрытие пересчётами, планы, расхождения, давность последнего пересчёта"),
    "wms-reconcile-receipts": ("Сверка приходов с 1С", "Приходы",
                               "Сверка приходов WMS с кодами из 1С: расхождения, дубли, очереди выгрузки"),
    "wms-staff-workload": ("Нагрузка по исполнителям", "Задачи",
                           "Задачи склада и журнал операций в разрезе исполнителей"),
    "wms-product-movement": ("Движение по товару", "Движение",
                             "Движение в разрезе товаров: топ по активности, месяцы, товары без движения"),
    "wms-reconcile-orders": ("Сверка расхода с 1С", "Обмен с 1С",
                             "Сверка заказов WMS с кодами из 1С: расхождения, дубли, очереди выгрузки заказов и отмен"),
    "wms-km": ("Маркировка КМ", "Обмен с 1С",
               "Маркировка: справочник КМ, загрузка из файлов, журнал импорта, объём обменных таблиц"),
}

# высота таблицы на дашборде (условные единицы Superset): короткая — 4, длинная — 8
HEIGHT_SHORT = 4


def build_query(params: dict) -> dict:
    """queries[0] для query_context в режиме «сырой» таблицы (Superset 6.1).

    Важно: в «сыром» режиме список столбцов лежит в `columns` (из all_columns).
    Если оставить `columns: []` и `metrics: []`, Superset отвечает «Пустой запрос?»
    и диаграмма не рисуется.
    """
    return {
        "columns": list(params.get("all_columns") or []),
        "metrics": [],
        "row_limit": params.get("row_limit", 1000),
        "row_offset": 0,
        "orderby": [],
        "is_timeseries": False,
        "extras": {"having": "", "where": ""},
        "filters": [],
        "annotation_layers": [],
        "series_limit": 0,
        "order_desc": False,
        "url_params": {},
        "custom_form_data": {},
        "apply_fetch_values_predicate": False,
    }


def table_params(columns: list[str], row_limit: int, palette: str) -> dict:
    """params диаграммы-таблицы в «сыром» режиме: все столбцы запроса как есть."""
    return {
        "viz_type": "table",
        "query_mode": "raw",
        "all_columns": columns,
        "metrics": [],
        "groupby": [],
        "adhoc_filters": [],
        "row_limit": row_limit,
        "order_desc": False,
        "include_search": True if len(columns) > 3 else False,
        "show_cell_bars": True,
        "color_pn": True,
        "time_range": "No filter",
        "color_scheme": palette,
    }


def main() -> None:
    data = json.load(open(DATA_FILE, encoding="utf-8"))
    by_key = {s["key"]: s for s in data["sections"]}

    with app.app_context():
        from sqlalchemy import text

        from superset import db
        from superset.connectors.sqla.models import SqlaTable
        from superset.models.core import Database
        from superset.models.dashboard import Dashboard
        from superset.models.slice import Slice

        database = db.session.query(Database).filter_by(database_name=DB_NAME).one()
        print(f"подключение: {database.id} «{database.database_name}»")

        # --- чистим прошлый прогон (только своё: префикс dm_rpt_ и наши slug)
        for dash in db.session.query(Dashboard).filter(Dashboard.slug.in_(list(SPEC))).all():
            print(f"  удаляю прежний дашборд {dash.id} ({dash.slug})")
            db.session.delete(dash)
        for ds in db.session.query(SqlaTable).filter(
                SqlaTable.table_name.like("dm_rpt_%")).all():
            for chart in db.session.query(Slice).filter_by(datasource_id=ds.id).all():
                db.session.delete(chart)
            db.session.delete(ds)
        db.session.commit()

        made_dashboards = []

        for key, (title, theme, descr) in SPEC.items():
            sec = by_key.get(key)
            if not sec:
                print(f"  !! {key}: нет данных, пропускаю")
                continue
            palette = PALETTE[theme]
            cards = sec["cards"]
            print(f"\n=== {title} ({key}) — {len(cards)} запросов ===")

            charts = []
            for n, c in enumerate(cards, start=1):
                ds_name = f"dm_rpt_{key.replace('-', '_')}_{n:02d}"
                ds = SqlaTable(
                    table_name=ds_name, schema="dbo", database_id=database.id,
                    sql=(c.get("sql_ss") or c["sql_fixed"]).strip(),
                    description=f"{title}: {c['title']} (перенесено из Metabase)",
                )
                db.session.add(ds)
                db.session.flush()
                ds.fetch_metadata()
                db.session.commit()
                cols = [col.column_name for col in ds.columns]
                if not cols:
                    print(f"  !! {c['mid']} {c['title']}: набор без колонок, пропускаю")
                    continue

                params = table_params(cols, 1000, palette)
                full = {"datasource": f"{ds.id}__table", **params}
                chart = Slice(
                    slice_name=f"{title}: {c['title']}",
                    viz_type="table",
                    datasource_type="table", datasource_id=ds.id,
                    params=json.dumps(full, ensure_ascii=False),
                    description=f"{c['title']} — перенесено из отчёта Metabase (дашборд {sec.get('mid', '')})",
                    created_by_fk=1, changed_by_fk=1,
                )
                chart.query_context = json.dumps({
                    "datasource": {"id": ds.id, "type": "table"},
                    "queries": [build_query(params)],
                    "form_data": full,
                    "result_type": "full", "result_format": "json", "force": False,
                }, ensure_ascii=False)
                db.session.add(chart)
                db.session.flush()
                charts.append((chart, c, len(cols)))
                print(f"  {chart.id:>4} {c['title'][:52]:<52} колонок={len(cols):>2} набор={ds.id}")

            if not charts:
                continue

            # --- раскладка: по одной таблице в ряд, высота зависит от числа строк
            grid = {
                "DASHBOARD_VERSION_KEY": "v2",
                "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID", "children": ["GRID_ID"]},
                "HEADER_ID": {"id": "HEADER_ID", "type": "HEADER", "meta": {"text": title}},
                "GRID_ID": {"type": "GRID", "id": "GRID_ID", "children": [], "parents": ["ROOT_ID"]},
            }
            idx = 0
            for row_no, (chart, c, ncols) in enumerate(charts, start=1):
                row_id = f"ROW-{row_no}"
                idx += 1
                cid = f"CHART-{idx}"
                h = HEIGHT_SHORT if ncols <= 6 else 6
                grid[cid] = {
                    "type": "CHART", "id": cid, "children": [],
                    "parents": ["ROOT_ID", "GRID_ID", row_id],
                    "meta": {"chartId": chart.id, "height": h, "width": 12,
                             "header_font_size": 15, "sliceName": chart.slice_name,
                             "uuid": str(uuid.uuid4())},
                }
                grid[row_id] = {
                    "type": "ROW", "id": row_id, "children": [cid],
                    "parents": ["ROOT_ID", "GRID_ID"],
                    "meta": {"background": "BACKGROUND_TRANSPARENT"},
                }
                grid["GRID_ID"]["children"].append(row_id)

            meta = {
                "color_scheme": palette, "refresh_frequency": 0, "label_colors": {},
                "timed_refresh_immune_slices": [], "expanded_slices": {},
                "shared_label_colors": [], "map_label_colors": {},
                "cross_filters_enabled": True,
            }
            dash = Dashboard(
                dashboard_title=title, slug=key,
                position_json=json.dumps(grid, ensure_ascii=False),
                json_metadata=json.dumps(meta, ensure_ascii=False),
                description=descr, published=True,
                created_by_fk=1, changed_by_fk=1,
            )
            dash.slices = [c for c, _, _ in charts]
            db.session.add(dash)
            db.session.commit()

            db.session.execute(
                text("insert into dashboard_user (user_id, dashboard_id) values (1, :d) "
                     "on conflict do nothing"), {"d": dash.id})
            db.session.execute(
                text("insert into dashboard_roles (dashboard_id, role_id) values (:d, 2) "
                     "on conflict do nothing"), {"d": dash.id})
            for chart, _, _ in charts:
                db.session.execute(
                    text("insert into slice_user (user_id, slice_id) values (1, :s) "
                         "on conflict do nothing"), {"s": chart.id})
            db.session.commit()
            made_dashboards.append((dash.id, key, title, len(charts)))
            print(f"  дашборд {dash.id}: /superset/dashboard/{key}/")

        print("\n---------------- ИТОГО ----------------")
        for did, key, title, n in made_dashboards:
            print(f"  {did:>3} {key:<24} {title:<52} диаграмм={n}")


if __name__ == "__main__":
    main()