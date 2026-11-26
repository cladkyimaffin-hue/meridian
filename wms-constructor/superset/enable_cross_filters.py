#!/usr/bin/env python3
"""Включает «Emit cross filter» у диаграмм на дашбордах склада.

Зачем: в Superset клик по строке таблицы/столбцу графика пересчитывает остальные
диаграммы только если у диаграммы-источника включён emit_filter. В наших
наборах этот флаг не выставлялся, поэтому клик ничего не делал.

Скрипт идемпотентен: проходит по дашбордам с заданными slug и включает флаг
в params диаграмм и в form_data сохранённого query_context.

Запуск на wmssql-analytics:
    docker cp enable_cross_filters.py superset:/tmp/
    docker exec superset python /tmp/enable_cross_filters.py
"""

import json

from superset.app import create_app

app = create_app()

SLUGS = ("wms-stock-parallel", "tasks-pilot", "wms-movement", "wms-receipts", "wms-orders")


def patch(obj: dict) -> bool:
    if obj.get("emit_filter") is True:
        return False
    obj["emit_filter"] = True
    return True


def main() -> None:
    with app.app_context():
        from superset import db
        from superset.models.dashboard import Dashboard

        total = 0
        for slug in SLUGS:
            dash = db.session.query(Dashboard).filter_by(slug=slug).one_or_none()
            if dash is None:
                print(f"  {slug}: нет такого дашборда, пропускаю")
                continue
            changed = []
            for chart in dash.slices:
                params = json.loads(chart.params or "{}")
                touched = patch(params)
                if touched:
                    chart.params = json.dumps(params, ensure_ascii=False)
                if chart.query_context:
                    ctx = json.loads(chart.query_context)
                    form = ctx.get("form_data") or {}
                    if patch(form):
                        ctx["form_data"] = form
                        chart.query_context = json.dumps(ctx, ensure_ascii=False)
                        touched = True
                if touched:
                    changed.append(chart.slice_name)
            db.session.commit()
            total += len(changed)
            print(f"  {slug}: включено у {len(changed)} из {len(dash.slices)}")
            for name in changed:
                print(f"      {name}")

        print(f"\nИтого изменено диаграмм: {total}")


if __name__ == "__main__":
    main()
