---
schema_version: "1.0"
date_modified: 2026-11-12
status: "active"
maintainer: "cladkyimaffin-hue"
file_type: "navigation_index"
source_of_truth: "00_Meta/registry.csv"
---

# Индекс папки: Monitoring

## Назначение

Человекочитаемая навигация по документам домена `Monitoring`. Машиночитаемый источник списка — `00_Meta/registry.csv`; метаданные проверяются по `00_Meta/SCHEMA.md`, допустимые теги — по `00_Meta/TAGS.md`.

## Документы

| Документ | Тип | Статус | Назначение |
|---|---|---|---|
| [Установка стека Prometheus и Grafana на wmssql-analytics](01_Architecture/%D0%A3%D1%81%D1%82%D0%B0%D0%BD%D0%BE%D0%B2%D0%BA%D0%B0%20%D1%81%D1%82%D0%B5%D0%BA%D0%B0%20Prometheus%20%D0%B8%20Grafana%20%D0%BD%D0%B0%20wmssql-analytics.md) | setup | in_progress | Как развёрнуты Prometheus, Grafana, node_exporter и windows_exporter, что удалено с сервера, как добавить Windows-сервер |
| [Медленная сеть wmssql-analytics через шлюз 192.168.12.176](06_Troubleshooting/%D0%9C%D0%B5%D0%B4%D0%BB%D0%B5%D0%BD%D0%BD%D0%B0%D1%8F%20%D1%81%D0%B5%D1%82%D1%8C%20wmssql-analytics%20%D1%87%D0%B5%D1%80%D0%B5%D0%B7%20%D1%88%D0%BB%D1%8E%D0%B7%20192.168.12.176.md) | troubleshooting | completed | Загрузки шли 2–6 КБ/с через шлюз .176; диагностика и решение |
| [Установка windows_exporter на wmsDB и подключение к Prometheus](<02_Exporters/Установка windows_exporter на wmsDB.md>) | setup | completed | Установка exporter 0.32.0 на `wmsDB`, коллекторы, правило файрвола, цель в Prometheus, откат, грабли |
| [Дашборд «wmsDB: Сервер»: параметры и пороги](<04_Dashboards/Дашборд wmsDB Сервер параметры и пороги.md>) | reference | in_progress | Состав дашборда, три уровня триггеров, таблица порогов, базовые значения, расположение файла и генератора |

## Служебные файлы домена

- `START-HERE.md`, `AI-README.md` — вход и правила чтения.
- `AI-environment_facts-meridian-monitoring.md` — факты среды со статусами.
- `COMMANDS.md` — команды с классами [R]/[W]/[D].

## Быстрые маршруты

- **Стек и архитектура:** `01_Architecture/`.
- **Экспортеры и цели:** `02_Exporters/`.
- **MS SQL Server:** `03_MSSQL/` (папка появится с первым документом).
- **Дашборды и таблица параметров:** `04_Dashboards/`.
- **Алерты:** `05_Alerting/` (папка появится с первым документом).
- **Инциденты:** `06_Troubleshooting/`.
- **Устаревшее:** `99_Archive/`.

## Сырые материалы

Сырые чаты с учётными данными и именами учётных записей хранятся не здесь, а в приватном репозитории `meridian-secrets` (`raw-chats/`); правило и таблица переноса — в `../Chats/README.md`.

- Сырой чат установки стека (источник первых двух документов): `meridian-secrets/raw-chats/Monitoring/Подключение серверов к cloude Prometheus и Grafana.md` (перенесён 2026-11-10).
- Чат 2026-11-11 (установка exporter на `wmsDB`, дашборд «wmsDB: Сервер»): источник двух последних документов; дословная выгрузка ожидается от администратора и кладётся в приватный репозиторий.
