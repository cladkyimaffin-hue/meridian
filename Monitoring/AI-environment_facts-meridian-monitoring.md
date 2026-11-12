---
schema_version: "1.0"
date_created: 2026-11-09
date_modified: 2026-11-12
status: "active"
maintainer: "cladkyimaffin-hue"
confidence: "факты собраны в чатах проекта Servers 2026-11-09, 2026-11-11 и 2026-11-12 (команды на серверах и чтение источников); со слов администратора помечены отдельно; секреты и имена учётных записей не включены"
---

# AI-environment_facts-meridian-monitoring.md

Факты о мониторинге Meridian. Источник истины для сверки при обработке документов домена (`../AI-INSTRUCTIONS.md`, раздел 8, шаг 5). Состояние серверов указано на 2026-11-09, 2026-11-11 и 2026-11-12 (дата проверки у каждого факта) и может измениться.

Пометки: `VERIFIED` — проверено командой или чтением источника в чате; `ADMIN` — со слов администратора; `INFERRED` — вывод; `OPEN` — не решено.

## Серверы

| Сервер | IP | Что это | Статус факта |
|---|---|---|---|
| `wmssql-analytics` | 192.168.12.202 | Ubuntu 24.04, ВМ Hyper-V; 8 vCPU; память 4 ГБ динамическая (мин. 2048 МБ, макс. 6144 МБ, буфер 20%); диск `/` около 96 ГБ (занято 24% на 2026-11-11). Здесь Prometheus и Grafana. Решение администратора 2026-11-12: здесь же будут сервер паролей и веб-сервер со ссылками на дашборды | VERIFIED, ADMIN |
| `wmsDB-TEST` | 192.168.12.201 | Windows Server 2022 Standard, ВМ Hyper-V; 2 vCPU, 3,4 ГБ RAM; MSSQLSERVER и Zabbix Agent 2; тестовый, пилотный. Не Linux, как считалось ранее. Остаётся в Grafana (решение администратора 2026-11-11) | VERIFIED, ADMIN |
| `wmsDB` | 192.168.12.153 | Windows Server 2022 Standard, ВМ Hyper-V; 14 vCPU; домен BRIG; аптайм 113,3 суток на 2026-11-11; диски C: 99 ГБ (72,8% свободно), D: 500 ГБ (98,5% свободно); службы MSSQLSERVER, SQLBrowser, SQLWriter, Zabbix Agent 2, windows_exporter, W32Time (служба времени, под наблюдением, работает на 2026-11-12); службы SQL Server Agent нет. ОЗУ: 19,7 ГБ по проверке 2026-11-09 и 21 691 834 368 байт по метрике exporter 2026-11-11, расхождение не разбиралось (OPEN); свободно около 24% | VERIFIED |

- Zabbix server работает на другом сервере (ADMIN). Порт агентов Zabbix 10050 не конфликтует с портом windows_exporter 9182 (VERIFIED).
- Сеть `wmssql-analytics`: шлюз по умолчанию 192.168.12.176 (netplan), DNS 192.168.0.65, IPv6 не маршрутизируется. Сетевая шара `/mnt/wmsbackup` = `//192.168.12.157/Publick` (CIFS) (VERIFIED).
- SQL Server на `wmsDB`: версия 15.0.2000.5 (SQL Server 2019), редакция Standard, смешанный режим входа; порт 1433 с `wmssql-analytics` открыт; в базе LV_MERIDIAN 1238 таблиц (VERIFIED 2026-11-11).
- Читающий SQL-логин для Grafana создан администратором: роль db_datareader и VIEW DEFINITION в LV_MERIDIAN. Вход с `wmssql-analytics` работает; не sysadmin; право VIEW SERVER STATE не выдано (VERIFIED 2026-11-11). Имя логина и пароль хранятся только в приватном `meridian-secrets`. Пароль заменён администратором 2026-11-11; запись в приватном реестре совпадает с новым паролем (ADMIN, 2026-11-12).
- SSH-учётная запись на `wmsDB` входа в SQL не имеет (VERIFIED). Журнал SQL Server (`MSSQL15.MSSQLSERVER\MSSQL\Log\ERRORLOG`) фиксирует отказы входа: SSH-учётной записи (2026-11-06 и 2026-11-09) и читающего логина при неверном пароле (2026-11-11, до замены пароля) (VERIFIED).

## Стек на `wmssql-analytics`

- Каталог стека `/opt/monitoring`: `docker-compose.yml`, `.env` (права 600, содержит секреты, в репозиторий не переносится), `prometheus/prometheus.yml`, `prometheus/targets/windows.yml` и `mssql.yml` (file_sd, подхватываются без перезапуска), `grafana/provisioning/` (источник Prometheus с uid `prometheus`, провайдер дашбордов), `grafana/dashboards/`, `tools/dashboards/` (генератор дашборда, создан 2026-11-11), `secrets/` (права 700; файл пароля читающего SQL-логина, права 600, владелец root) (VERIFIED).
- Docker CE 29.9.3, Compose v5.7.0 (репозиторий Docker, принудительно по IPv4). Образы: `prom/prometheus:v3.5.0`, `grafana/grafana:12.2.0`, `prom/node-exporter:latest` (VERIFIED).
- Prometheus: только `127.0.0.1:9090`, хранение 30 дней или 20 ГБ, лимит памяти 1 ГБ. Grafana: порт 3000 для сети, лимит 512 МБ, регистрация выключена. node_exporter: host-сеть, порт 9100. Сеть compose 172.30.0.0/24; правило ufw: 172.30.0.0/24 к порту 9100/tcp (VERIFIED).
- Клиент `sqlcmd` v1.5.0 (go-sqlcmd) установлен из репозитория Microsoft 2026-11-11 (VERIFIED).
- Цели в `windows.yml` (VERIFIED 2026-11-11): `192.168.12.201:9182` (`host: wmsDB-TEST`, `role: mssql`, `title: ТЕСТ (wmsDB-TEST)`) и `192.168.12.153:9182` (`host: wmsDB`, `role: mssql`). Обе цели up. Копии файла: `windows.yml.bak-20261111`, `windows.yml.bak2-20261111`.
- Пароль администратора Grafana хранится на сервере в `/opt/monitoring/.env` (переменная `GF_ADMIN_PASSWORD`). Пароль был показан в открытом чате; администратор решил пароли не менять (ADMIN, 2026-11-11), хранить только в приватном репозитории.
- Дашборды (папка Monitoring, подключены из файлов, обновление раз в 60 с, правки в интерфейсе не сохраняются): Node Exporter Full (grafana.com id 1860); «ТЕСТ (wmsDB-TEST): Windows Server + MS SQL» (uid `win-mssql`, файл `windows-mssql.json`, переименован 2026-11-11, копия до правки `windows-mssql.json.bak-20261111`); «wmsDB: Сервер» (uid `wmsdb-server`, файл `wmsdb-server.json`, 31 панель, пороги утверждены 2026-11-12, копии `wmsdb-server.json.bak-20261112` и `gen_server.py.bak-20261112`; см. `MONITORING-DASHBOARD-WMSDB-SERVER-2026-001`) (VERIFIED).
- В Grafana 12.2.0 эндпоинт public-dashboards отвечает (на запрос для дашборда без публичной ссылки вернул 404 NotFound), значит, функция доступна (INFERRED; не проверялась в работе).
- Zabbix остаётся для up/down, Prometheus для производительности и трендов; алерты в Prometheus пока не настраивались (ADMIN).

## windows_exporter на `wmsDB-TEST`

- Версия 0.32.0 (MSI, SHA256 проверен по `sha256sums.txt`); выбрана версия старше двух недель, а не 0.32.1. Служба `windows_exporter`, автозапуск, порт 9182 (VERIFIED).
- Коллекторы: `cpu,logical_disk,physical_disk,memory,net,os,service,system,tcp,mssql`. Коллектора `cs` в 0.32 нет: служба падала с ошибкой `unknown collector cs`; параметры исправлены в `ImagePath` службы (VERIFIED).
- Правило Windows Firewall «windows_exporter (Prometheus 192.168.12.202)»: вход TCP 9182 только с 192.168.12.202. MSI правило автоматически не создаёт (VERIFIED).
- В `C:\Temp` остались MSI, лог и файл контрольных сумм (VERIFIED).

## windows_exporter на `wmsDB`

- Версия 0.32.0 (тот же MSI из `C:\Temp`, SHA256 `d48ebad7999aac5603fe01007016a0ddbcecbc1aa0ecbc51867a2416b6c60a7d` совпал с официальным `sha256sums.txt`). Служба `windows_exporter`, автозапуск, порт 9182 (VERIFIED 2026-11-11).
- Коллекторы: `cpu,logical_disk,physical_disk,memory,net,os,service,system,tcp,mssql,process,time,scheduled_task`. Фильтры в `C:\Program Files\windows_exporter\config.yaml`: `process` только `sqlservr|windows_exporter`, `scheduled_task` исключает `/Microsoft/.*` (VERIFIED).
- Правило Windows Firewall «windows_exporter (Prometheus 192.168.12.202)»: вход TCP 9182 только с 192.168.12.202, все профили; создано вручную, MSI правило не создал (VERIFIED).
- Метрики идут: около 4,6 тыс. серий, из них 654 по `windows_mssql_*`; время сбора около 0,08 с (VERIFIED). В `C:\Temp`: MSI, `we_install.log`, `we_install2.log`, `config.yaml.bak-20261111`.
- Имена метрик в 0.32, нужные для дашбордов: `windows_cpu_time_seconds_total{mode="idle"}`, `windows_memory_physical_total_bytes`, `windows_memory_physical_free_bytes`, `windows_memory_available_bytes`, `windows_logical_disk_free_bytes`, `windows_logical_disk_size_bytes`, `windows_physical_disk_{read,write}_latency_seconds_total` (делить на `..._reads_total` или `..._writes_total`), `windows_physical_disk_requests_queued`, `windows_system_processor_queue_length`, `windows_system_boot_time_timestamp`, `windows_service_state{service="...",state="running"}`, `windows_net_*`, `windows_tcp_*`, `windows_process_cpu_time_seconds_total`, `windows_process_working_set_bytes`, `windows_time_computed_time_offset_seconds`, `windows_scheduled_task_last_result_status{status="..."}` (one-hot по метке `status`), `windows_mssql_*`. Старые дашборды с grafana.com под эти имена обычно не подходят (VERIFIED).

## Эксплуатационные наблюдения

- Сеть `wmssql-analytics` была почти непригодна (2–6 КБ/с) через шлюз 192.168.12.176; через 192.168.12.1 около 760 КБ/с. После увеличения скорости роутера администратором работает нормально (VERIFIED, ADMIN). Доступ в Telegram с этой машины через оба шлюза недоступен (VERIFIED на дату проверки).
- `apt`/`dpkg` без терминала зависают на вопросах debconf: запускать с `< /dev/null` и `DEBIAN_FRONTEND=noninteractive`; после прерывания apt выполнить `dpkg --configure -a` (VERIFIED).
- Не использовать `pkill -f '<текст>'` внутри собственной команды: убивает свою же оболочку (VERIFIED).
- SSH-оболочка на Windows — `cmd`: нет `head` и `uname`; вывод в CP866 портится, для текста использовать `powershell -Command` с UTF-8. Строки с символом `|` в кавычках (регулярные выражения) через `powershell -Command` ломаются: использовать `-EncodedCommand` (VERIFIED, см. `COMMANDS.md`, блок 8).

## Проверка условий для сервера паролей на `wmssql-analytics` (VERIFIED 2026-11-12, только чтение)

- Порты 80 и 443 не заняты; `ufw` их уже разрешает.
- Ресурсы: ОЗУ всего 3,9 ГБ, доступно около 2,9 ГБ; диск `/`: свободно 69 ГБ из 96. Синхронизация времени (NTP) активна.
- Реестры образов: GitHub и `ghcr.io` отвечают быстро (около 0,3 с); Docker Hub отвечает медленно (около 10 с). Образ Vaultwarden предполагается брать из `ghcr.io`, образ Caddy лежит в Docker Hub.
- `ufw` разрешает порт 8765 из любого места (на нём слушает `ai-grafana-analyst`; нужна ли служба и защищена ли паролем, UNKNOWN); также разрешены порты 8443, 8081 и 8090, на которых ничего не слушает (остатки прежних установок, INFERRED).
- Не проверено: фактическая скорость скачивания образов; совместимость версий Vaultwarden и Web-Vault для этой среды (основа — заметки из `korona`).
- Решение администратора 2026-11-12: устанавливать сервер паролей сразу, к рискам из раздела «Известные риски» вернуться позже (ADMIN). Установка начата: скачивание образа Caddy остановилось из-за ошибки DNS при обращении к Docker Hub; причина не установлена, установка не завершена (на момент экспорта чата).

## Порядок работ (решение администратора, 2026-11-11 и 2026-11-12)

1. `wmsDB`: дашборд сервера готов, пороги утверждены (2026-11-12); дашборд MS SQL Server: параметры и триггеры обсудить, выделить основные, главные и критические (ещё не обсуждалось); бизнес-дашборды по таблицам LV_MERIDIAN (движение товаров, статистика) делать позже, отдельно.
2. Решение от 2026-11-12: сначала установка сервера паролей и веб-сервера со ссылками на дашборды (первые ссылки — уже готовые дашборды), затем настройка следующих серверов.
3. `wmsAPP`.
4. `wmsWiFi`: система Wi-Fi (Qtech), 10 точек доступа разместить на дашбордах (подход: `snmp_exporter`, см. открытые вопросы).
5. `HostWMS` (хост Hyper-V).
6. Сервер паролей по образцу korona (Vaultwarden): устанавливается на `wmssql-analytics` (решение администратора 2026-11-12); сначала сервер, затем клиент на пользовательском ПК, не на сервере.
7. Веб-сервер со ссылками на дашборды (требования администратора, 2026-11-12): устанавливать на `wmssql-analytics`; на сайте для каждого дашборда аннотация, картинка основных полей и ссылка на дашборд только для чтения (без редактирования), для просмотра динамических параметров. Способ доступа только для чтения и способ получения картинок не выбраны (OPEN).

Справка по образцу (чтение репозитория `korona`, `Proxmox/07_Vaultwarden` и чат о настройке пользователей, 2026-11-11): Vaultwarden 1.37.2 с Web-Vault (версия 2026.7.0 несовместима, использовалась v2025.12.2) за Caddy; `ADMIN_TOKEN` только в формате Argon2id (лучше командой `vaultwarden hash`, в `EnvironmentFile` символы `$` не удваивать); HTTPS обязателен, иначе браузер блокирует Web Crypto; свободную регистрацию отключить, приглашения включить; расширение Bitwarden нужно направить на свой сервер; при самоподписанном сертификате Caddy (`tls internal`) Chrome даёт `Failed to fetch`: на клиент нужно установить именно корневой сертификат, не промежуточный (ADMIN, не проверялось для meridian).

## Известные риски (проверка 2026-11-12 подтвердила пункты ниже; решение: вернуться к ним после установки сервера паролей)

- VERIFIED 2026-11-12: на `wmssql-analytics` выдано расширение `sudo` без пароля для рабочей учётной записи; по окончании работ удалить файл в `/etc/sudoers.d/`.
- VERIFIED 2026-11-12: в двух скриптах в домашнем каталоге на `wmssql-analytics` токен Telegram лежит открытым текстом (три строки с адресом бота, значение в чате не показывалось); служба `ai-grafana-analyst` слушает `0.0.0.0:8765`, `ufw` разрешает порт из любого места.
- VERIFIED 2026-11-12: вход по SSH паролем на `wmssql-analytics` разрешён.
- VERIFIED 2026-11-12: Grafana работает без TLS (порт 3000).
- INFERRED: сервер паролей на том же сервере, что и мониторинг, повышает ценность этого сервера как цели; отдельная ВМ чище, но требует ресурсов Hyper-V (администратор выбрал этот сервер).

## Открытые вопросы

- OPEN: дашборд «wmsDB: MS SQL Server»: параметры и триггеры (основные, главные, критические) обсудить; для долгих запросов, блокировок и возраста бэкапов нужно право VIEW SERVER STATE и чтение `msdb` у читающего логина (не выдано).
- OPEN: алерты (Alertmanager, Telegram) после накопления истории; затем Synology и Qtech Wi-Fi через `snmp_exporter`.
- OPEN: расхождение по объёму ОЗУ `wmsDB` (19,7 ГБ и 21 691 834 368 байт).
- OPEN: веб-сервер со ссылками: как обеспечить доступ только для чтения (учётная запись роли Viewer, анонимный Viewer или публичные дашборды Grafana), как делать картинки (рендер из Grafana или скриншоты по расписанию; учесть память 4 ГБ), TLS для порта 3000 и сайта, кто будет просматривать.
- OPEN: сервер паролей: порты и адрес доступа, сертификат (личный CA и его установка на ПК), кто и сколько пользователей, резервное копирование базы паролей; завершение установки (образ Caddy, DNS).
- OPEN: публичность репозитория `meridian`; место файла про SSTP VPN в корне.

---
*Создан 2026-11-09 из контекста чата проекта Servers; обновлён 2026-11-12 по чатам от 2026-11-11 и 2026-11-12. Секреты, токены и имена учётных записей не включены.*
