---
document_id: MONITORING-WINDOWS-EXPORTER-WMSAPP-HOSTWMS-2026-001
title: "Установка windows_exporter на wmsAPP и HostWMS"
document_type: setup
status: completed
priority: high
date_created: 2026-11-16
date_modified: 2026-11-16
next_review: 2027-02-16
author: "Claude (по запросу cladkyimaffin-hue)"
category: 02_Exporters
tags:
  - Monitoring
  - Prometheus
  - Windows-Exporter
  - Windows-Server
  - Hyper-V
  - Configuration
ai_summary: "2026-11-15 windows_exporter 0.32.0 установлен на wmsAPP (192.168.12.152, ВМ, роль app) и HostWMS (192.168.12.151, физический хост Hyper-V с пятью ВМ, роль hyperv, дополнительный коллектор hyperv). Порт 9182 открыт только для 192.168.12.202, цели добавлены в targets/windows.yml, обе up. Описаны только отличия от установки на wmsDB: коллекторы, фильтры процессов, метки, проверка, откат."
dont_repeat:
  - "Проверка цифровой подписи MSI на этих серверах вернула UnknownError. Подлинность установщика опирается на контрольную сумму из того же релиза GitHub, откуда скачан файл; сумма из файла sha256sums.txt и из API GitHub — два источника одного релиза, не независимая проверка. Строже: сверить сумму с ПК администратора."
  - "На wmsAPP фильтр процессов содержит только windows_exporter, потому что названия процессов приложения WMS неизвестны (UNKNOWN). Не считать отсутствие панелей процессов приложения ошибкой."
  - "Коллектор hyperv с настройками по умолчанию включает 20 вложенных сборщиков и даёт около 2,5 тыс. строк метрик из 7,3 тыс.; снятие метрик на HostWMS занимает около 1,5 с. Перед добавлением других коллекторов или сокращением scrape_interval учитывать это время."
  - "Имя ВМ в Hyper-V и в метриках hyperv — wmsDB_TEST (с подчёркиванием), а имя хоста в Prometheus — wmsDB-TEST (с дефисом). Это разные имена одного сервера, а не два сервера и не конфликт."
  - "Общие грабли установки (нет правила Windows Firewall после MSI, символ | в powershell -Command через cmd, коллектора cs нет) описаны в MONITORING-WINDOWS-EXPORTER-WMSDB-2026-001 и здесь не повторяются."
related_files:
  - MONITORING-WINDOWS-EXPORTER-WMSDB-2026-001
  - MONITORING-PROMETHEUS-GRAFANA-SETUP-2026-001
schema_version: "1.1"
environment: production
last_verified: 2026-11-15
---

# Установка windows_exporter на wmsAPP и HostWMS

## Что настраивается и зачем

На сервер приложений `wmsAPP` и на физический хост Hyper-V `HostWMS` установлен `windows_exporter` 0.32.0, чтобы Prometheus на `wmssql-analytics` (192.168.12.202) собирал их метрики для дашбордов Grafana. Общая процедура, проверка суммы, правило файрвола, откат и грабли описаны в `MONITORING-WINDOWS-EXPORTER-WMSDB-2026-001`; здесь только отличия. Решения администратора 2026-11-15: порядок серверов `wmsAPP`, затем `HostWMS` (wmsAPP как проба: HostWMS — хост всех пяти ВМ), на `HostWMS` добавить сборщик Hyper-V; каждый шаг — по подтверждению.

## Серверы (VERIFIED, 2026-11-15, только чтение)

| Параметр | wmsAPP | HostWMS |
|---|---|---|
| IP | 192.168.12.152 | 192.168.12.151 |
| Тип | виртуальная машина | физический сервер (модель «Purley») |
| ОС | Windows Server 2022 Standard | Windows Server 2022 Standard |
| ОЗУ / процессоры | 5,3 ГБ / 2 | 127,1 ГБ / 32 |
| Диски | C: 99 ГБ, свободно 79 ГБ | C: 446 ГБ (свободно 400), D: 1788 ГБ (свободно 1426) |
| Время работы на дату проверки | 40,8 суток | 89,3 суток |
| Заметные службы | искомых нет | Hyper-V (`vmms`), `NginxService` |
| Роль в метках Prometheus | `app` | `hyperv` |

На `HostWMS` работают пять ВМ: `wmsAPP`, `wmsDB`, `wmsDB_TEST`, `wmsSQL-Analytics`, `wmsWiFi` (VERIFIED по метрикам Hyper-V). Оба сервера видят `github.com:443` и порт 3000 Grafana. На `HostWMS` брандмауэр в профиле «Частная сеть» был выключен до наших работ и не менялся.

## Отличия от установки на wmsDB

| Что | wmsDB | wmsAPP | HostWMS |
|---|---|---|---|
| Коллекторы | cpu, logical_disk, physical_disk, memory, net, os, service, system, tcp, mssql, process, time, scheduled_task | те же, без mssql | те же, без mssql, плюс hyperv (настройки по умолчанию, 20 вложенных сборщиков) |
| Фильтр `process` | `sqlservr\|windows_exporter` | `windows_exporter` | `vmms\|vmwp\|nginx\|windows_exporter` |
| Фильтр `scheduled_task` | исключает `/Microsoft/.*` | так же | так же |
| Метки цели | `host: wmsDB`, `role: mssql` | `host: wmsAPP`, `role: app` | `host: HostWMS`, `role: hyperv` |
| Резервная копия `windows.yml` | `windows.yml.bak-20261111` | `windows.yml.bak-20261115` | `windows.yml.bak2-20261115` |

Установщик тот же `windows_exporter-0.32.0-amd64.msi`; SHA256 совпал с файлом сумм релиза (значение — в документе про `wmsDB`). Порт 9182. Правило Windows Firewall на обоих серверах: «windows_exporter (Prometheus 192.168.12.202)», вход TCP 9182 только с 192.168.12.202. Метка `role: app` выбрана Claude (у баз стоит `mssql`), администратор подтвердил добавление цели с ней.

## Шаги установки и настройки

Выполнялось 2026-11-15. Команды и классы риска: общие строки — `../COMMANDS.md`, блоки 7–8 (отдельный блок для этих серверов будет добавлен вместе с остальными обновлениями).

### wmsAPP (15:26–15:42)

1. **Проверка релиза** [R]: релиз `v0.32.0` на GitHub, установщик и файл сумм на месте.
2. **Скачивание** [W]: папка `C:\Temp\windows_exporter`, в ней `windows_exporter-0.32.0-amd64.msi` (14 614 528 байт) и `sha256sums.txt` (404 байта); служб, правил и Prometheus не затрагивалось. Сумма совпала с файлом сумм и с данными GitHub API; проверка подписи вернула UnknownError (см. «Don't repeat»).
3. **Установка** [W]: каталог `C:\Program Files\windows_exporter` с `config.yaml` (фильтры из таблицы выше), затем установка MSI как службы с автозапуском, портом 9182 и коллекторами из таблицы; журнал `C:\Temp\windows_exporter\install.log`. Параметры установки показаны администратору заранее; атрибут установки правила брандмауэра не использовался.
4. **Правило Windows Firewall** [W]: вход TCP 9182 только с 192.168.12.202.
5. **Цель в Prometheus** [W]: в `/opt/monitoring/prometheus/targets/windows.yml` добавлена `192.168.12.152:9182` с метками из таблицы; копия до правки; перезапуск Prometheus не нужен (file_sd перечитывается раз в минуту).

### HostWMS (19:28–19:37)

1. **Скачивание и проверка** [W]/[R]: та же папка `C:\Temp\windows_exporter` (MSI, `sha256sums.txt`, журнал `install.log`). Установщик дополнительно распакован без установки в `C:\Temp\windows_exporter\extract`, чтобы по справке узнать имя сборщика Hyper-V (`hyperv`). Сумма совпала и с файлом сумм, и с данными GitHub API.
2. **Установка** [W]: каталог `C:\Program Files\windows_exporter` с `config.yaml`, служба `windows_exporter` (автозапуск, порт 9182), коллекторы из таблицы.
3. **Правило Windows Firewall** [W]: вход TCP 9182 только с 192.168.12.202.
4. **Цель в Prometheus** [W]: `192.168.12.151:9182`, метки из таблицы; копия `windows.yml.bak2-20261115`.

## Проверка результата

- [x] wmsAPP: код возврата установки 0, служба `Running`, порт 9182 слушает, `PathName` службы совпадает с образцом (`wmsDB`); `/metrics` локально отдаёт HTTP 200 (4695 строк); с `wmssql-analytics` — HTTP 200, 4241 строка `windows_*`, ответ за 0,03 с. В Prometheus цель `up`, метрики идут (первый снимок: загрузка CPU 52,3 %, память занята 67,6 %, диск C: свободно 79,1 % — снимок за 2 минуты, не оценка состояния).
- [x] HostWMS: код возврата 0, служба `Running`, порт слушает; снятие метрик на самом хосте около 1,5 с (7313 строк, из них 2471 по Hyper-V); в Prometheus цель `up`. Первые значения: загрузка процессоров хоста 5,6 %, свободная ОЗУ 62,7 %, диск C: свободно 89,6 %, D: 79,8 %; работают 5 ВМ из 5.
- [x] В Prometheus четыре цели Windows (`wmsDB-TEST`, `wmsDB`, `wmsAPP`, `HostWMS`), все `up`, ошибок сбора нет.
- [ ] Не проверено: что порт 9182 закрыт для других адресов (проверить с `wmssql-analytics` нельзя, вывод по правилу — INFERRED); нет ли в системном профиле брандмауэра более общего разрешающего правила для порта 9182 (по имени «exporter» других правил на `wmsAPP` не нашли); влияние exporter на нагрузку `HostWMS` за сутки (хост — продуктив с пятью ВМ).

## Откат

По каждому серверу (по подтверждению администратора, классы [W] и [D]):
- Остановить и удалить службу: `msiexec /x` для `windows_exporter-0.32.0-amd64.msi` (или `sc delete windows_exporter`).
- Удалить правило: `Remove-NetFirewallRule -DisplayName 'windows_exporter (Prometheus 192.168.12.202)'`.
- Удалить каталоги `C:\Program Files\windows_exporter` и `C:\Temp\windows_exporter` (на `HostWMS` в нём временная папка `extract`: её можно удалить в любой момент, сама она ничего не запускает).
- На `wmssql-analytics` вернуть `windows.yml` из копии (`windows.yml.bak-20261115` для wmsAPP; `windows.yml.bak2-20261115` для HostWMS; при откате обоих серверов вернуть копию `bak-20261111`) и подождать минуту.

## Решения и риски

- `HostWMS` — физический хост всех пяти ВМ; установка лёгкая, но затрагивает продуктив. Сначала поставлено на `wmsAPP` как проба (решение администратора).
- `wmsAPP` и `HostWMS`: служба видна в сети; доступ только с адреса Prometheus по правилу (см. «Не проверено»).
- Список ВМ для дашборда `HostWMS` задан в генераторе, а не берётся из метрик автоматически: при добавлении ВМ дашборд нужно пересобрать (см. документ о дашбордах, когда он будет добавлен).
- Назначение приложений на портах 5130, 8023, 11001 (wmsAPP) и 8443, 9000 (HostWMS) не выяснялось (UNKNOWN); какие процессы приложения нужно показывать на wmsAPP, неизвестно (UNKNOWN).

## ⛔ Don't repeat
См. `dont_repeat` во фронтматтере.

## Связанные документы
- `MONITORING-WINDOWS-EXPORTER-WMSDB-2026-001` — общая процедура установки, грабли и откат (образец).
- `MONITORING-PROMETHEUS-GRAFANA-SETUP-2026-001` — стек Prometheus и Grafana.

---
*Создан 2026-11-16 по чату «Макет страницы-витрины аналитики» (2026-11-15). Секреты, токены и имена учётных записей не включены.*
