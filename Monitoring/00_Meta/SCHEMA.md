---
schema_version: "1.1"
date_created: 2026-11-09
date_modified: 2026-11-09
status: "active"
maintainer: "cladkyimaffin-hue"
---

# 📐 SCHEMA.md — доменные дополнения (Monitoring)

Общее ядро схемы (обязательные 15 полей, опциональный блок, формат `document_id`, принцип эволюции, история версий) находится в [`../../SCHEMA.md`](../../SCHEMA.md). Этот файл содержит только то, что зависит от домена `Monitoring/`. При противоречии приоритет у корневого файла; расхождение записывается в `CONFLICTS.md`.

## category

Имя целевой папки домена `Monitoring/`; список — в `AI-README.md` этого домена, раздел 3.

## Доменные значения опциональных полей

Значения `node`, `hostname`, `target_system` для серверов берутся из файла фактов домена (`AI-environment_facts-meridian-monitoring.md`) и в этом файле не дублируются.

## Теги и реестр

Теги — только из `TAGS.md` этого домена, `document_id` проверяются по `registry.csv` этого домена.
