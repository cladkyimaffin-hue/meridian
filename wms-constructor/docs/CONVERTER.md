# Конвертер запросов Grafana -> YAML

Файл `tools/md_to_yaml.py` превращает Markdown-выгрузку запросов дашбордов в `queries/<раздел>.yaml`.
Исходный файл и папка с JSON дашбордов монтируются **только для чтения** [R]; запись идёт только в `queries/` [W].

```bash
# [W] перезаписывает queries/*.yaml (ручные правки в них будут потеряны; после ручных правок конвертер не запускать)
docker run --rm --user "$(id -u):$(id -g)" -v "$PWD":/work -v /opt/monitoring/work:/in:ro \
  -v /opt/monitoring/grafana/dashboards-reports:/dash:ro -w /work wms-constructor:dev \
  python tools/md_to_yaml.py --md /in/sql_queries_dashboards_2026-11-20.md --dashboards /dash --out queries
```

Замены: `$__timeFilter(X)` -> `X >= :date_from AND X < DATEADD(day, 1, :date_to)`;
`$__timeGroup(Alias)(X,1d)` -> `CAST(X AS date)` (`AS [Дата]`); `N${имя:sqlstring}` и `$имя` -> `:имя`.
