#!/usr/bin/env python3
"""Заранее раскрашивает подписи метрик, чтобы отчёт не просил запись цветов.

Что происходит: при открытии отчёта фронтенд Superset сам пытается сохранить
цвета подписей — `PUT /api/v1/dashboard/<id>/colors`. Анониму эта запись
запрещена (портал закрывает всё, кроме чтения), поэтому в консоли появляется
403, а таблицы остаются без цветных полос на числовых колонках.

Лечение без ослабления прав: цвета подписей записываются заранее, от имени
администратора. Тогда фронтенду нечего сохранять и запрос не появляется.

Запуск на wmssql-analytics:
    docker cp paint_labels.py superset:/tmp/
    docker exec superset python /tmp/paint_labels.py
"""

import json

from superset.app import create_app

app = create_app()

# палитра темы -> цвета для подписей (те же, что у графиков)
PALETTES = {
    "t_ostatki": ["#2D6CB5", "#6FB1F0", "#BFD9F5"],
    "t_prihody": ["#2E8B3E", "#7CCB80", "#C9EACC"],
    "t_rashod": ["#D9730D", "#F7B05E", "#FBE0BC"],
    "t_zadachi": ["#6C3FB0", "#B08EE3", "#DCCBF4"],
    "t_dvizhenie": ["#13867F", "#5CCBC2", "#BDEBE7"],
    "t_obmen": ["#B23A48", "#EE8497", "#F8CDD5"],
}

SLUGS = ("wms-stock-parallel", "wms-receipts", "wms-orders",
         "tasks-pilot", "wms-movement", "wms-exchange")


def main() -> None:
    with app.app_context():
        from superset import db
        from superset.models.dashboard import Dashboard

        for slug in SLUGS:
            dash = db.session.query(Dashboard).filter_by(slug=slug).first()
            if dash is None:
                print(f"  {slug}: нет дашборда")
                continue
            meta = json.loads(dash.json_metadata or "{}")
            scheme = meta.get("color_scheme") or "t_ostatki"
            palette = PALETTES.get(scheme, PALETTES["t_ostatki"])

            # какие подписи метрик вообще встречаются в диаграммах отчёта
            labels = []
            for chart in dash.slices:
                params = json.loads(chart.params or "{}")
                for m in params.get("metrics") or []:
                    if isinstance(m, dict) and m.get("label") and m["label"] not in labels:
                        labels.append(m["label"])
                m = params.get("metric")
                if isinstance(m, dict) and m.get("label") and m["label"] not in labels:
                    labels.append(m["label"])
            labels = [lab for lab in labels if lab and lab != "—"]

            meta["shared_label_colors"] = labels
            meta["label_colors"] = {lab: palette[i % len(palette)] for i, lab in enumerate(labels)}
            meta["color_scheme_domain"] = palette
            dash.json_metadata = json.dumps(meta, ensure_ascii=False)
            db.session.commit()
            print(f"  {slug}: раскрашено подписей {len(labels)} — {', '.join(labels) or '—'}")


if __name__ == "__main__":
    main()