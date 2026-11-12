---
schema_version: "1.0"
status: "active"
maintainer: "cladkyimaffin-hue"
---

# 📜 CHANGELOG.md — журнал изменений конвейера (домен Monitoring)

Формат строки: `ГГГГ-ММ-ДД | тип | что сделано | кем`.

Типы событий: `bootstrap`, `schema-change`, `tag-add`, `migrate`, `new-doc`, `conflict-resolved`, `registry-fix`, `update-doc` (обновление существующего документа или служебного файла по изменениям в среде). Новый тип сначала добавляется в эту шапку с пояснением.

---

- 2026-11-09 | bootstrap | Создан каркас домена `Monitoring/` по образцу `MikroTik/` из репозитория `korona`: `START-HERE.md`, `AI-README.md`, `INDEX.md`, `AI-environment_facts-meridian-monitoring.md`, `00_Meta/` (`SCHEMA.md`, `TAGS.md` с первичным набором, `registry.csv` с заголовками, `CONFLICTS.md`, `TEMPLATES/`), `00_Inbox/`, `99_Archive/`. Файл фактов заполнен из контекста чата проекта Servers (2026-11-09), секреты не включены. Категории `01_...`–`06_...` создаются вместе с первыми документами | Claude (по запросу cladkyimaffin-hue)
- 2026-11-10 | new-doc | Добавлен `MONITORING-PROMETHEUS-GRAFANA-SETUP-2026-001` (категория `01_Architecture`, создана) по сырому чату `Chats/Подключение серверов к cloude Prometheus и Grafana.md`; `COMMANDS.md` расширен блоками 4–6 | Claude (по запросу cladkyimaffin-hue)
- 2026-11-10 | new-doc | Добавлен `MONITORING-NETWORK-GATEWAY-SLOW-2026-001` (категория `06_Troubleshooting`, создана) по тому же чату | Claude (по запросу cladkyimaffin-hue)
- 2026-11-12 | new-doc | Добавлен `MONITORING-WINDOWS-EXPORTER-WMSDB-2026-001` (категория `02_Exporters`, создана) по чату проекта Servers от 2026-11-11 | Claude (по запросу cladkyimaffin-hue)
- 2026-11-12 | new-doc | Добавлен `MONITORING-DASHBOARD-WMSDB-SERVER-2026-001` (категория `04_Dashboards`, создана) по тому же чату | Claude (по запросу cladkyimaffin-hue)
- 2026-11-12 | update-doc | `AI-environment_facts-meridian-monitoring.md`: состояние `wmsDB` (exporter, SQL Server, читающий логин), цели Prometheus, `sqlcmd`, дашборды, решения администратора, порядок работ по серверам, план сервера паролей; `COMMANDS.md`: блоки 7–9, обновлено «Покрытие»; `INDEX.md`: две записи и исправлена ссылка на сырой чат установки стека (перенесён в приватный репозиторий 2026-11-10) | Claude (по запросу cladkyimaffin-hue)
- 2026-11-12 | update-doc | `MONITORING-DASHBOARD-WMSDB-SERVER-2026-001` и файл фактов: утверждены пороги (рассинхрон времени 5 с и 60 с; очередь диска состоянием в связке с задержкой), в «Службы» добавлена W32Time; зафиксированы решения администратора: сервер паролей на `wmssql-analytics`, веб-страница со ссылками на дашборды только для просмотра | Claude (по запросу cladkyimaffin-hue)
- 2026-11-12 | update-doc | `AI-environment_facts-meridian-monitoring.md`: добавлен раздел проверки условий для сервера паролей на `wmssql-analytics` (порты, ресурсы, реестры образов, лишние правила `ufw`), риски переведены в VERIFIED, записано решение администратора «установить сразу, к рискам вернуться позже», установка не завершена (образ Caddy, DNS) | Claude (по запросу cladkyimaffin-hue), источник: экспорт чата «Мониторинг wmsDB и разбор таблиц MS SQL» от 2026-11-12
