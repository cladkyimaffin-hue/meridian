---
title: Monitoring Domain Entry Point
author: Meridian
version: 1.0
tags:
  - Monitoring
  - Prometheus
  - Grafana
---

# START-HERE.md

## Назначение

Точка входа для ИИ и администратора при работе с доменом `Monitoring`: мониторинг серверов Meridian (Prometheus, Grafana, экспортеры), прежде всего сервера `wmsDB` и MS SQL Server на нём.

Если новый чат начинается без контекста, сначала прочитать материалы из этого файла и только потом отвечать.

---

# Порядок инициализации

## Шаг 1. Структура домена

Открыть и прочитать:

- `AI-README.md`;
- `INDEX.md` или `00_Meta/registry.csv`.

## Шаг 2. Факты среды

Открыть `AI-environment_facts-meridian-monitoring.md`: серверы, стек в Docker, версии, имена метрик, подтверждённые наблюдения. Учитывать только строки со статусом `VERIFIED`.

## Шаг 3. Профильный раздел

Категории создаются вместе с первым документом (`AI-README.md`, раздел 3). Планируемые:

```text
01_Architecture/      стек Prometheus + Grafana + Docker, сеть, хранение
02_Exporters/         windows_exporter, node_exporter, цели и файрвол
03_MSSQL/             метрики SQL Server, читающий логин, пороги
04_Dashboards/        дашборды Grafana и таблица параметров
05_Alerting/          Alertmanager и уведомления (позже)
06_Troubleshooting/   инциденты и грабли
```

---

# Алгоритм поиска ответа

1. Определить объект (сервер, экспортер, дашборд, метрика).
2. Найти раздел.
3. Найти документ через `INDEX.md` или `registry.csv`.
4. Проверить YAML-метаданные.
5. Дать ответ с указанием источника.

---

# Если информации недостаточно

Запросить:

```text
Сервер (имя, IP):
Компонент (Prometheus, Grafana, экспортер, SQL):
Симптом или задача:
Что уже проверено:
Ожидаемый результат:
```

Изменяющие команды без явного запроса пользователя не выполнять. Секреты (пароль Grafana, токены, пароли SQL-логинов) в документы не переносить: указывать, где они хранятся.

---

# Основные файлы домена

```text
Monitoring/AI-README.md
Monitoring/AI-environment_facts-meridian-monitoring.md
Monitoring/INDEX.md
Monitoring/00_Meta/registry.csv
```
