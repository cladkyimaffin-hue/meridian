---
schema_version: "1.0"
status: "active"
maintainer: "cladkyimaffin-hue"
---

# 📜 CHANGELOG.md — журнал изменений конвейера (домен Monitoring)

Формат строки: `ГГГГ-ММ-ДД | тип | что сделано | кем`.

Типы событий: `bootstrap`, `schema-change`, `tag-add`, `migrate`, `new-doc`, `conflict-resolved`, `registry-fix`. Новый тип сначала добавляется в эту шапку с пояснением.

---

- 2026-11-09 | bootstrap | Создан каркас домена `Monitoring/` по образцу `MikroTik/` из репозитория `korona`: `START-HERE.md`, `AI-README.md`, `INDEX.md`, `AI-environment_facts-meridian-monitoring.md`, `00_Meta/` (`SCHEMA.md`, `TAGS.md` с первичным набором, `registry.csv` с заголовками, `CONFLICTS.md`, `TEMPLATES/`), `00_Inbox/`, `99_Archive/`. Файл фактов заполнен из контекста чата проекта Servers (2026-11-09), секреты не включены. Категории `01_...`–`06_...` создаются вместе с первыми документами | Claude (по запросу cladkyimaffin-hue)
- 2026-11-10 | new-doc | Добавлен `MONITORING-PROMETHEUS-GRAFANA-SETUP-2026-001` (категория `01_Architecture`, создана) по сырому чату `Chats/Подключение серверов к cloude Prometheus и Grafana.md`; `COMMANDS.md` расширен блоками 4–6 | Claude (по запросу cladkyimaffin-hue)
- 2026-11-10 | new-doc | Добавлен `MONITORING-NETWORK-GATEWAY-SLOW-2026-001` (категория `06_Troubleshooting`, создана) по тому же чату | Claude (по запросу cladkyimaffin-hue)
