---
schema_version: "1.0"
date_created: 2026-11-09
status: "active"
maintainer: "cladkyimaffin-hue"
---

# 🏷️ Реестр тегов (TAGS.md) — домен Monitoring

Единственный источник допустимых тегов для поля `tags` в документах домена `Monitoring/`. Теги между доменами не переиспользуются автоматически.

Правило добавления нового тега: проверить **все** группы на тег с тем же смыслом в другом написании, добавить в одну подходящую группу, записать в `CHANGELOG.md`.

## Группы тегов (первичный набор, дополняется по ходу разбора)

### Платформа и компоненты
`Monitoring` · `Prometheus` · `Grafana` · `Docker` · `Node-Exporter` · `Windows-Exporter` · `Alertmanager` · `Zabbix`

### Наблюдаемые объекты
`Windows-Server` · `Hyper-V` · `Ubuntu` · `MS-SQL`

### Метрики
`CPU` · `Memory` · `Disk` · `Network` · `Wait-Stats`

### Эксплуатация / процесс
`Dashboard` · `Alerting` · `Configuration` · `Troubleshooting` · `Security` · `Audit` · `Backup`
