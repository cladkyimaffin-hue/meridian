"""Заполнение query_context у диаграмм Superset.

Зачем: Superset 6 не отдаёт данные сохранённой диаграммы, если у неё пустой
`slices.query_context` — API отвечает `Chart has no query context saved. Please save the chart again.`
Диаграммы, созданные скриптом (а не через браузер), сохраняются без этого поля.

Скрипт собирает query_context из `params` диаграммы: datasource, queries, form_data.
Поддерживаются оба режима таблицы: агрегированный (groupby + metrics) и «сырой»
(`query_mode: raw`, `all_columns`).

Запуск на wmssql-analytics:
    docker cp backfill_query_context.py superset:/tmp/
    docker exec superset python /tmp/backfill_query_context.py

Скрипт идемпотентен: диаграммы с непустым query_context не трогаются.
Перезапись всех: запустить с аргументом --force.
"""

import json
import sys

from superset.app import create_app

app = create_app()

FORCE = "--force" in sys.argv


def build_queries(params: dict) -> list[dict]:
    """Собрать список query-объектов из params диаграммы."""
    viz = params.get("viz_type")

    if params.get("query_mode") == "raw":
        columns = list(params.get("all_columns") or [])
        metrics: list[dict] = []
        row_limit = params.get("row_limit", 1000)
    elif viz == "table":
        columns = list(params.get("groupby") or [])
        metrics = params.get("metrics") or []
        row_limit = params.get("row_limit", 100)
    else:
        columns = [params["x_axis"]] if params.get("x_axis") else []
        metrics = params.get("metrics") or ([params["metric"]] if params.get("metric") else [])
        row_limit = params.get("row_limit", 100)

    return [
        {
            "columns": columns,
            "metrics": metrics,
            "row_limit": row_limit,
            "row_offset": 0,
            "orderby": [],
            "is_timeseries": bool(params.get("granularity_sqla")),
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
        from superset import db
        from superset.models.slice import Slice

        fixed = 0
        for chart in db.session.query(Slice).all():
            if chart.query_context and not FORCE:
                continue
            if not chart.params or not chart.datasource_id:
                print(f"пропуск {chart.id} {chart.slice_name}: нет params или datasource")
                continue

            params = json.loads(chart.params)
            chart.query_context = json.dumps(
                {
                    "datasource": {"id": chart.datasource_id, "type": "table"},
                    "queries": build_queries(params),
                    "form_data": params,
                    "result_type": "full",
                    "result_format": "json",
                    "force": False,
                },
                ensure_ascii=False,
            )
            fixed += 1
            print(f"query_context -> {chart.id} {chart.slice_name}")

        db.session.commit()
        print(f"обновлено диаграмм: {fixed}")


if __name__ == "__main__":
    main()
