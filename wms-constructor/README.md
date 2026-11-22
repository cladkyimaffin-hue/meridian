# Конструктор запросов LV_MERIDIAN (wms-constructor)

Веб-приложение для склада АО «Меридиан» (WMS ANT Lvision): меню готовых отчётов, каждый отчёт открывается
в своей вкладке, показывается таблицей и выгружается в Excel. Только чтение.

* Язык и стек: Python 3.12, FastAPI, pyodbc (ODBC Driver 18), XlsxWriter, PyYAML; интерфейс на чистом JS (без CDN).
* Запросы лежат как данные в `queries/*.yaml` (по файлу на раздел = бывший дашборд Grafana). 101 запрос, 14 разделов.
* Запуск: Docker (`docker-compose.yml`), порт 8080. Секреты вне репозитория.

## Быстрый старт (на сервере wmssql-analytics)

1. Секреты: файл `/opt/wms-constructor-secrets/app.env` (права 600, НЕ в git). Образец переменных: `.env.example`.
2. Адрес публикации порта: файл `.env` рядом с `docker-compose.yml` со строкой `BIND_ADDR=<адрес сервера в локальной сети>` (в git не попадает).
3. Запуск: `docker compose up -d --build` (папка `/opt/meridian/wms-constructor`).
4. Проверка: `/healthz` отвечает `{"status":"ok","queries":101}`.

Все команды с классификацией [R]/[W]/[D]: `docs/COMMANDS.md`.

## Структура

| Путь | Назначение |
|---|---|
| `app/queries.py` | загрузка YAML, проверка SQL (только SELECT/WITH), подстановка `:параметров` как `?` |
| `app/db.py` | подключение, лимит строк, таймаут, преобразование значений |
| `app/excel.py` | Excel: тексты только строками (формулы не выполняются), лист «Параметры» |
| `app/main.py` | API и раздача интерфейса, заголовки безопасности |
| `app/static/` | интерфейс: меню, вкладки, параметры, таблица |
| `queries/` | описания запросов (YAML) |
| `tools/md_to_yaml.py` | одноразовый конвертер из Markdown-выгрузки запросов Grafana (`docs/CONVERTER.md`) |
| `tests/` | 27 тестов (`pytest`), к базе не обращаются |
| `docs/` | `AI-CONTEXT.md` (для нового чата), `DECISIONS.md`, `COMMANDS.md`, `ROADMAP.md` |

## Формат запроса (queries/<раздел>.yaml)

```yaml
section: stock-products          # ключ раздела
title: Остатки по товарам
variables:                       # переменные раздела: text | multiselect | date
  zone: {label: Зона, type: multiselect, options_sql: "SELECT ... AS value, ... AS label"}
  tovar: {label: "Товар", type: text}
  date_from: {label: "С даты", type: date, default: "-90d"}
queries:
  - id: stock-products.1-1
    title: "Остатки: сводка"
    group: Обзор остатков
    kind: сводка
    description: "Что показывает / Как считается / Примечание"
    sql: |
      SELECT ... WHERE z.code IN (:zone) AND created >= :date_from
```

Правила: SQL только `SELECT`/`WITH`, один оператор, без `INSERT/UPDATE/DELETE/EXEC/INTO` и т.п. (проверяется при загрузке;
при ошибке приложение не стартует). Параметры `:имя` превращаются в `?`; `IN (:zone)` разворачивается по числу значений.
Сравнение кодов между базами: `COLLATE DATABASE_DEFAULT`. Количества нельзя суммировать между единицами измерения.

## Чего не делать

* Не класть в репозиторий пароли, токены, значения КМ, номера коробов, SSCC, пароли/оклады/контакты сотрудников.
* Не добавлять запросы, изменяющие данные; произвольный SQL от пользователя не принимать.
* Не трогать контейнеры `vaultwarden*`, `portal-caddy` и чужие сервисы без отдельного решения.
