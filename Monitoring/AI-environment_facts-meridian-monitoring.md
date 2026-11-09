---
schema_version: "1.0"
date_created: 2026-11-09
date_modified: 2026-11-09
status: "active"
maintainer: "cladkyimaffin-hue"
confidence: "факты собраны в чате проекта Servers 2026-11-09 (команды на серверах и чтение источников); со слов администратора помечены отдельно; секреты не включены"
---

# AI-environment_facts-meridian-monitoring.md

Факты о мониторинге Meridian. Источник истины для сверки при обработке документов домена (`../AI-INSTRUCTIONS.md`, раздел 8, шаг 5). Состояние серверов указано на 2026-11-09 и может измениться.

Пометки: `VERIFIED` — проверено командой или чтением источника в чате; `ADMIN` — со слов администратора; `INFERRED` — вывод; `OPEN` — не решено.

## Серверы

| Сервер | IP | Что это | Статус факта |
|---|---|---|---|
| `wmssql-analytics` | 192.168.12.202 | Ubuntu 24.04, ВМ Hyper-V; 8 vCPU; память 4 ГБ динамическая (мин. 2048 МБ, макс. 6144 МБ, буфер 20%); диск `/` около 96 ГБ. Здесь Prometheus и Grafana | VERIFIED |
| `wmsDB-TEST` | 192.168.12.201 | Windows Server 2022 Standard, ВМ Hyper-V; 2 vCPU, 3,4 ГБ RAM; MSSQLSERVER и Zabbix Agent 2; тестовый, пилотный. Не Linux, как считалось ранее | VERIFIED |
| `wmsDB` | 192.168.12.153 | Windows Server 2022 Standard, ВМ Hyper-V; 14 vCPU, 19,7 ГБ RAM; аптайм 111 дней на дату проверки; домен BRIG; диски C: 99 ГБ (72 свободно), D: 500 ГБ (493 свободно); службы MSSQLSERVER, SQLBrowser, SQLWriter, Zabbix Agent 2; службы SQL Server Agent не видно; windows_exporter на дату проверки не установлен | VERIFIED |

- Zabbix server работает на другом сервере (ADMIN). Порт агентов Zabbix 10050 не конфликтует с портом windows_exporter 9182 (VERIFIED).
- Сеть `wmssql-analytics`: шлюз по умолчанию 192.168.12.176 (netplan), DNS 192.168.0.65, IPv6 не маршрутизируется. Сетевая шара `/mnt/wmsbackup` = `//192.168.12.157/Publick` (CIFS) (VERIFIED).
- Доступ к SQL Server: SSH-учётная запись на `wmsDB` входа в SQL не имеет (VERIFIED). Читающий SQL-логин для мониторинга не создан (OPEN).

## Стек на `wmssql-analytics`

- Каталог стека `/opt/monitoring`: `docker-compose.yml`, `.env` (права 600, содержит секреты, в репозиторий не переносится), `prometheus/prometheus.yml`, `prometheus/targets/windows.yml` и `mssql.yml` (file_sd, подхватываются без перезапуска), `grafana/provisioning/` (источник Prometheus с uid `prometheus`, провайдер дашбордов), `grafana/dashboards/` (VERIFIED).
- Docker CE 29.9.3, Compose v5.7.0 (репозиторий Docker, принудительно по IPv4). Образы: `prom/prometheus:v3.5.0`, `grafana/grafana:12.2.0`, `prom/node-exporter:latest` (VERIFIED).
- Prometheus: только `127.0.0.1:9090`, хранение 30 дней или 20 ГБ, лимит памяти 1 ГБ. Grafana: порт 3000 для сети, лимит 512 МБ, регистрация выключена. node_exporter: host-сеть, порт 9100. Сеть compose 172.30.0.0/24; правило ufw: 172.30.0.0/24 к порту 9100/tcp (VERIFIED).
- Пароль администратора Grafana хранится на сервере в `/opt/monitoring/.env`. Он был показан в открытом чате, поэтому подлежит смене (OPEN).
- Дашборды: Node Exporter Full (grafana.com id 1860) и собственный «Windows Server + MS SQL» (uid `win-mssql`, 28 панелей, переменная `host`), файл `windows-mssql.json` в `grafana/dashboards/` (VERIFIED). Генератор дашборда был во временной папке и может быть утерян (INFERRED).
- Zabbix остаётся для up/down, Prometheus для производительности и трендов; алерты в Prometheus пока не настраивались (ADMIN).

## windows_exporter на `wmsDB-TEST`

- Версия 0.32.0 (MSI, SHA256 проверен по `sha256sums.txt`); выбрана версия старше двух недель, а не 0.32.1. Служба `windows_exporter`, автозапуск, порт 9182 (VERIFIED).
- Коллекторы: `cpu,logical_disk,physical_disk,memory,net,os,service,system,tcp,mssql`. Коллектора `cs` в 0.32 нет: служба падала с ошибкой `unknown collector cs`; параметры исправлены в `ImagePath` службы (VERIFIED).
- Правило Windows Firewall «windows_exporter (Prometheus 192.168.12.202)»: вход TCP 9182 только с 192.168.12.202. MSI правило автоматически не создаёт (VERIFIED).
- Цель в `windows.yml`: `192.168.12.201:9182`, метки `host: wmsDB-TEST`, `role: mssql` (VERIFIED). В `C:\Temp` остались MSI, лог и файл контрольных сумм (VERIFIED).
- Имена метрик в 0.32, использованные в дашборде: `windows_cpu_time_seconds_total{mode="idle"}`, `windows_memory_physical_total_bytes`, `windows_memory_physical_free_bytes`, `windows_logical_disk_free_bytes`, `windows_logical_disk_size_bytes`, `windows_physical_disk_read_latency_seconds_total`, `windows_net_bytes_received_total`, `windows_tcp_connections_established`, `windows_system_processor_queue_length`, `windows_mssql_*` (до 654 серий: sqlstats, bufman, genstats, locks, memmgr, databases, transactions, accessmethods, waitstats). Старые дашборды с grafana.com под эти имена обычно не подходят (VERIFIED).

## Эксплуатационные наблюдения

- Сеть `wmssql-analytics` была почти непригодна (2–6 КБ/с) через шлюз 192.168.12.176; через 192.168.12.1 около 760 КБ/с. После увеличения скорости роутера администратором работает нормально (VERIFIED, ADMIN). Доступ в Telegram с этой машины через оба шлюза недоступен (VERIFIED на дату проверки).
- `apt`/`dpkg` без терминала зависают на вопросах debconf: запускать с `< /dev/null` и `DEBIAN_FRONTEND=noninteractive`; после прерывания apt выполнить `dpkg --configure -a` (VERIFIED).
- Не использовать `pkill -f '<текст>'` внутри собственной команды: убивает свою же оболочку (VERIFIED).
- SSH-оболочка на Windows — `cmd`: нет `head` и `uname`; вывод в CP866 портится, для текста использовать `powershell -Command` с UTF-8 (VERIFIED).

## Открытые вопросы

- OPEN: судьба `wmsDB-TEST` в Grafana: убрать или оставить отдельным дашбордом «Тест».
- OPEN: установка windows_exporter на `wmsDB` (те же параметры, без коллектора `cs`, правило файрвола только для 192.168.12.202, цель в `windows.yml`).
- OPEN: два дашборда «wmsDB: Сервер» и «wmsDB: MS SQL Server» на русском, у каждой панели заполнено поле `description`.
- OPEN: таблица параметров с порогами (норма, предупреждение, критично, действие, влияние на WMS); пороги уточнить после 1–2 недель наблюдений.
- OPEN: читающий SQL-логин (права `VIEW SERVER STATE`, чтение `msdb`) для возраста бэкапов, состояния баз, долгих запросов, блокировок.
- OPEN: алерты (Alertmanager, Telegram) после накопления истории; затем Synology и Qtech Wi-Fi через `snmp_exporter`.

---
*Создан 2026-11-09 из контекста чата проекта Servers. Секреты, токены и учётные записи не включены.*
