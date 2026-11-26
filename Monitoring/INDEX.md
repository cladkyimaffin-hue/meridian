---
schema_version: "1.0"
date_modified: 2026-11-21
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
| [Установка сервера паролей Vaultwarden на wmssql-analytics](<01_Architecture/Установка сервера паролей Vaultwarden на wmssql-analytics.md>) | setup | completed | Vaultwarden 1.37.5 за Caddy в Docker, адрес и порт, токен администратора, клиент на ПК, ежедневная копия базы на шару, откат, решения и риски |
| [Страница-витрина дашбордов и публичные ссылки Grafana](<01_Architecture/Страница-витрина дашбордов и публичные ссылки Grafana.md>) | setup | in_progress | Страница `http://192.168.12.202` (Caddy, порт 80) со ссылками на публичные дашборды Grafana: решения администратора, устройство, токены (где хранятся), правка двух дашбордов под публичные ссылки, риски |
| [Установка windows_exporter на wmsAPP и HostWMS](<02_Exporters/Установка windows_exporter на wmsAPP и HostWMS.md>) | setup | completed | Exporter 0.32.0 на сервере приложений и на хосте Hyper-V (коллектор hyperv): только отличия от `wmsDB`, метки, проверка, откат |
| [Дашборды wmsAPP, HostWMS, Wi-Fi и wmsWiFi: состав и пороги](<04_Dashboards/Дашборды wmsAPP HostWMS Wi-Fi и wmsWiFi состав и пороги.md>) | reference | in_progress | Четыре дашборда из генераторов: разделы, пороги (предложены, не утверждены), правки по замечаниям, ошибки VHDX и ISO, ограничения |
| [Опрос точек доступа Qtech: служба wifi-ap-exporter на wmsWiFi](<02_Exporters/Опрос точек доступа Qtech служба wifi-ap-exporter на wmsWiFi.md>) | setup | completed | Опрос девяти точек по SSH раз в минуту (только чтение), ключ, служба, правило `ufw`, цели Prometheus, откат, риски |
| [Расхождение часов на точках доступа Qtech и NTP-контейнер wmsWiFi](<06_Troubleshooting/Расхождение часов на точках доступа Qtech и NTP-контейнер wmsWiFi.md>) | troubleshooting | completed | Часы точек спешили на 16 минут и отставали на 47 суток: причина в NTP-контейнере Qtech и точке `.159`, исправление, проверка, откат, что не решено |
| [Источник данных wmsDB LV_MERIDIAN в Grafana и папка Отчёты WMS](<03_MSSQL/Источник данных wmsDB LV_MERIDIAN в Grafana и папка Отчёты WMS.md>) | setup | completed | Читающий доступ Grafana к базам LV_MERIDIAN (1238 таблиц) и MRDN_Exchange (30 таблиц IFC_*), права, источник через provisioning, папка «Отчёты WMS», откат, риски |
| [Справочник таблиц LV_MERIDIAN и MRDN_Exchange для отчётов](<03_MSSQL/Справочник таблиц LV_MERIDIAN и MRDN_Exchange для отчётов.md>) | reference | in_progress | Карта таблиц WMS по темам с числом строк, подтверждённые связи, статусы заданий и расходных партий, таблицы обмена с 1С, что не проверено |

## Служебные файлы домена

- `START-HERE.md`, `AI-README.md` — вход и правила чтения.
- `AI-environment_facts-meridian-monitoring.md` — факты среды со статусами.
- `COMMANDS.md` — команды с классами [R]/[W]/[D].

## Быстрые маршруты

- **Стек и архитектура, сервер паролей, страница-витрина:** `01_Architecture/`.
- **Экспортеры и цели:** `02_Exporters/`.
- **MS SQL Server (источник данных, таблицы LV_MERIDIAN):** `03_MSSQL/`.
- **Дашборды и таблица параметров:** `04_Dashboards/`.
- **Алерты:** `05_Alerting/` (папка появится с первым документом).
- **Инциденты:** `06_Troubleshooting/`.
- **Устаревшее:** `99_Archive/`.

## Сырые материалы

Сырые чаты с учётными данными и именами учётных записей хранятся не здесь, а в приватном репозитории `meridian-secrets` (`raw-chats/Monitoring/`); правило и таблица переноса — в `../Chats/README.md`.

- Установка стека (источник первых двух документов): `meridian-secrets/raw-chats/Monitoring/Подключение серверов к cloude Prometheus и Grafana.md` (перенесён 2026-11-10); более поздний экспорт того же чата, INFERRED: `Claude-Развертывание Prometheus и Grafana на wmsDB-TEST-20261112-2226.md`.
- Установка exporter на `wmsDB`, дашборд «wmsDB: Сервер», начало установки сервера паролей (источник трёх последних документов): `meridian-secrets/raw-chats/Monitoring/Claude-Мониторинг wmsDB и разбор таблиц MS SQL-20261112-2223.md` (экспорт от 2026-11-12). Работы 2026-11-13 (завершение установки сервера паролей, резервная копия) в этот экспорт не входят: дословная выгрузка ожидается от администратора.
- Работы 2026-11-15 и 2026-11-16 (страница-витрина, exporter на wmsAPP и HostWMS, Wi-Fi, NTP): `meridian-secrets/raw-chats/Monitoring/Claude--Макет страницы-витрины аналитики-20261116-2202.md` и `Claude--Сервер паролей и веб-страница дашбордов-20261116-2202.md`. Копии этих файлов также лежат в публичной папке `Chats/` (решение администратора 2026-11-21: оставить как есть); место токенов публичных ссылок — S-009 в приватном реестре.
- Работы 2026-11-17 и 2026-11-18 (источник данных LV_MERIDIAN, папка «Отчёты WMS»): `Chats/Claude--Поиск таблиц товаров в LV_MERIDIAN-20261121-1132.md` (публичная папка; поиск по шаблонам значений секретов не нашёл) и `Chats/Claude--Проверка актуальности документа по загрузкам-20261121-1132.md` (2026-11-19 — 2026-11-20).
