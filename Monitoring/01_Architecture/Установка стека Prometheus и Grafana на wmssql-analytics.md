---
document_id: "MONITORING-PROMETHEUS-GRAFANA-SETUP-2026-001"
title: "Установка стека Prometheus и Grafana на wmssql-analytics"
document_type: "setup"
status: "in_progress"
priority: "high"
date_created: 2026-11-10
date_modified: 2026-11-10
next_review: 2026-12-10
author: "Claude (по запросу cladkyimaffin-hue)"
category: "01_Architecture"
tags: ["Monitoring", "Prometheus", "Grafana", "Docker", "Node-Exporter", "Windows-Exporter", "Ubuntu", "Hyper-V", "Configuration"]
ai_summary: "Как и почему на сервере wmssql-analytics (192.168.12.202) развёрнуты Prometheus, Grafana и node_exporter в Docker Compose, что удалено с сервера, как подключён windows_exporter на wmsDB-TEST, какие дашборды есть и как добавить новый Windows-сервер. Пароли не приводятся."
dont_repeat: ["Не запускать apt/dpkg без < /dev/null и DEBIAN_FRONTEND=noninteractive: зависает на вопросах debconf", "Не ставить Docker и не скачивать образы, пока сеть wmssql-analytics идёт через шлюз 192.168.12.176 с низкой скоростью (см. MONITORING-NETWORK-GATEWAY-SLOW-2026-001)", "Образы repo.wimark.local:5000/... удалены, реестр недоступен: вернуть их нечем", "Не считать wmsDB-TEST Linux-машиной: это Windows Server 2022", "Не использовать готовые дашборды grafana.com под windows_exporter 0.32: имена метрик другие; ID 14510 и 14292 не проверены", "Не открывать Prometheus (9090) в сеть: у него нет аутентификации", "Не использовать sa и SSH-учётную запись для метрик SQL: нужен отдельный читающий логин"]
related_files: ["MONITORING-NETWORK-GATEWAY-SLOW-2026-001"]
schema_version: "1.1"
node: "wmssql-analytics"
last_verified: 2026-11-09
confidentiality: "public"
---

# Установка стека Prometheus и Grafana на wmssql-analytics

## Что настраивается и зачем

Стек мониторинга производительности серверов Meridian: Prometheus (сбор метрик), Grafana (дашборды) и node_exporter в Docker Compose на `wmssql-analytics`; на Windows-серверах работает `windows_exporter`. Zabbix остаётся для контроля доступности (up/down), Prometheus и Grafana — для производительности и трендов (подход администратора). Данные о серверах и версиях — в `AI-environment_facts-meridian-monitoring.md`.

Источник: сырой чат `Chats/Подключение серверов к cloude Prometheus и Grafana.md` (события 2026-11-07…09). Пометки: VERIFIED — проверено командой в чате; ADMIN — решение или слова администратора; INFERRED — вывод.

## Решения администратора (ADMIN)

- Prometheus и Grafana ставить на `wmssql-analytics`, в Docker; Grafana — новая, с чистого листа, на этом же сервере.
- Zabbix server и PostgreSQL с этой машины удалить (Zabbix работает на другом сервере); бэкап PostgreSQL не делать; Apache удалить.
- В Docker оставить только нужное, остальное удалить.
- Сначала всё установить, затем объяснить, как работать.
- Мониторинг пока ограничить сервером `wmsDB`; `wmsDB-TEST` был пилотным.

## Предварительные условия

- [ ] Сделан checkpoint ВМ в Hyper-V (рекомендация: раньше на ней работал Zabbix с PostgreSQL).
- [ ] Памяти достаточно: гость видит около 4 ГБ (динамическая память; поле минимума при работающей ВМ менять нельзя, нужна остановка). В чате рекомендовалось минимум 4096 МБ, максимум 6144 МБ; фактические значения — в файле фактов.
- [ ] Загрузки из интернета идут нормально (см. `MONITORING-NETWORK-GATEWAY-SLOW-2026-001`).
- [ ] Расширенные права sudo выданы только на время работ и должны быть отозваны по завершении (подробности — в приватном реестре).

## Шаги установки и настройки (как выполнено)

1. **Очистка сервера (VERIFIED).** Остаточные процессы Zabbix server (пакеты удалены 4 августа, процессы работали без бинарника) остановлены. `postgresql-16`, `postgresql-client-16`, `postgresql-common`, `postgresql-client-common` и `apache2` удалены с purge; данные PostgreSQL удалены без бэкапа (ADMIN). Порты 5432, 8090, 10051 больше не слушаются. Пользователи ОС `zabbix` и `postgres` остались.
2. **Docker (VERIFIED).** Docker CE 29.9.3 и Compose v5.7.0 из репозитория Docker (apt принудительно по IPv4), служба в автозапуске, `docker run hello-world` прошёл, пользователь в группе `docker`.
3. **Чистка Docker (ADMIN, VERIFIED).** Удалено около 5 ГБ: образы Wimark (`repo.wimark.local:5000/...`, 31 шт.), `ai-middleware`, `awaragi/prometheus-mssql-exporter`, mongo, postgres:17, redis:7, portainer-ce, старые тома и сети. Остались 3 образа: `prom/prometheus:v3.5.0`, `grafana/grafana:12.2.0`, `prom/node-exporter:latest`.
4. **Стек `/opt/monitoring` (VERIFIED).** `docker-compose.yml`, `.env` (права 600, секреты), `prometheus/prometheus.yml`, `prometheus/targets/windows.yml` и `mssql.yml` (file_sd, подхватываются без перезапуска), `grafana/provisioning/` (источник Prometheus с uid `prometheus`, провайдер дашбордов), `grafana/dashboards/`. Prometheus слушает только `127.0.0.1:9090`, хранение 30 дней или 20 ГБ, лимит памяти 1 ГБ. Grafana — порт 3000 для сети, лимит 512 МБ, регистрация выключена, версия 12.2.0. node_exporter — host-сеть, порт 9100. Сеть compose 172.30.0.0/24; правило ufw разрешает этой подсети доступ к 9100/tcp.
5. **windows_exporter на wmsDB-TEST (VERIFIED).** Версия 0.32.0 (MSI, SHA256 сверен с `sha256sums.txt`; выбрана версия старше двух недель, а не 0.32.1). Служба `windows_exporter`, автозапуск, порт 9182. Коллекторы: `cpu,logical_disk,physical_disk,memory,net,os,service,system,tcp,mssql`. Коллектора `cs` в 0.32 нет, служба падала с `unknown collector cs`, параметры запуска исправлены. Правило Windows Firewall: вход TCP 9182 только с 192.168.12.202 (MSI правило не создаёт). Цель в `windows.yml` с метками `host` и `role`. Метрики MSSQL собирает сам `windows_exporter`, отдельный экспортер и пароль не нужны.
6. **Дашборды Grafana (VERIFIED).** Папка Monitoring: Node Exporter Full (grafana.com 1860) и собственный «Windows Server + MS SQL» (28 панелей, 39 запросов проверены на реальных данных; переменная `host`). Старые дашборды grafana.com под имена метрик 0.32 не подходят. Дашборд будет разделён на «wmsDB: Сервер» и «wmsDB: MS SQL Server» (см. файл фактов, открытые вопросы).

## Доступ

- **Grafana:** `http://192.168.12.202:3000`, логин `admin`. Пароль хранится на сервере в `/opt/monitoring/.env`, в документах не приводится. Смена пароля при первом входе: профиль → Change password.
- **Prometheus:** без аутентификации и только на `127.0.0.1:9090`. Доступ через SSH-туннель (команда — в `COMMANDS.md`), затем `http://localhost:9090`. Нужен для диагностики: Status → Targets (какие серверы UP/DOWN), вкладка Graph для проверки PromQL.
- **Свои запросы:** Grafana → Explore → источник Prometheus, например `windows_mssql_genstats_user_connections`.

## Как добавить ещё один Windows-сервер

1. Установить на него `windows_exporter` (MSI) со свойствами `ENABLED_COLLECTORS=cpu,logical_disk,physical_disk,memory,net,os,service,system,tcp` (плюс `mssql`, если на сервере SQL Server) и `LISTEN_PORT=9182`.
2. Открыть в Windows Firewall TCP 9182 только для 192.168.12.202.
3. Добавить адрес `IP:9182` с меткой `host` в `/opt/monitoring/prometheus/targets/windows.yml`. Перезапуск не нужен, через минуту сервер появится в Targets.

## Состояние wmsDB-TEST на момент настройки (VERIFIED, 2026-11-09)

CPU меньше 1%, память занята на 71% (всего 3,4 ГБ), SQL Server использует около 450 МБ при цели 1,4 ГБ, блокировок и deadlock нет. Память стоит держать под наблюдением.

## Проверка результата

- [x] Prometheus собирает метрики с трёх целей (wmssql-analytics, wmsDB-TEST, сам Prometheus), все в статусе up.
- [x] Источник Prometheus подключён в Grafana автоматически, дашборды импортированы.
- [x] `docker run hello-world` прошёл.
- [ ] windows_exporter на `wmsDB` (192.168.12.153) не установлен.
- [ ] Алерты (Alertmanager, Telegram) не настроены, ждут накопления истории.

## ⛔ Don't repeat

- Не запускать `apt`/`dpkg` без `< /dev/null` и `DEBIAN_FRONTEND=noninteractive`: удаление PostgreSQL зависло на вопросе debconf, потребовалась `dpkg --configure -a`.
- Не ставить Docker и не качать образы через шлюз 192.168.12.176, пока он медленный (2–6 КБ/с).
- Образы из `repo.wimark.local:5000` вернуть нечем: реестр не резолвится с этой машины.
- `wmsDB-TEST` — не Linux, а Windows Server 2022.
- Не брать дашборды grafana.com 14510 и 14292 без проверки; для Linux использовать 1860.
- Не публиковать Prometheus (9090) без аутентификации.
- Для метрик уровня баз SQL нужен отдельный читающий логин, а не `sa` и не SSH-учётная запись.

## Связанные документы

- MONITORING-NETWORK-GATEWAY-SLOW-2026-001
