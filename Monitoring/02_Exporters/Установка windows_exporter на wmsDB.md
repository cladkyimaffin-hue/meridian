---
document_id: MONITORING-WINDOWS-EXPORTER-WMSDB-2026-001
title: "Установка windows_exporter на wmsDB и подключение к Prometheus"
document_type: setup
status: completed
priority: high
date_created: 2026-11-12
date_modified: 2026-11-12
next_review: 2027-02-12
author: "Claude (по запросу cladkyimaffin-hue)"
category: 02_Exporters
tags:
  - Monitoring
  - Prometheus
  - Windows-Exporter
  - Windows-Server
  - MS-SQL
  - Configuration
ai_summary: "На боевой сервер wmsDB (192.168.12.153) установлен windows_exporter 0.32.0 с коллекторами cpu, logical_disk, physical_disk, memory, net, os, service, system, tcp, mssql, process, time, scheduled_task; порт 9182 открыт только для 192.168.12.202; цель добавлена в Prometheus, статус up. Описаны шаги, проверка, откат и грабли."
dont_repeat:
  - "MSI не создаёт правило Windows Firewall, даже с параметром REMOTE_ADDR: после установки правило нужно создать вручную, иначе порт 9182 снаружи закрыт."
  - "Не передавать в powershell -Command через SSH-оболочку cmd строки с символом | внутри кавычек (регулярные выражения): cmd режет команду по |, скрипт обрывается на синтаксической ошибке. Использовать -EncodedCommand (base64 от UTF-16LE) или файл скрипта."
  - "Пути задач планировщика в метках метрик записаны с прямыми слэшами (/Microsoft/Windows/...), а не с обратными: фильтр collector.scheduled_task.exclude должен быть '/Microsoft/.*'."
  - "Метка с именем службы в windows_service_state называется service, а не name."
  - "Аптайм берётся из windows_system_boot_time_timestamp (без _seconds) в версии 0.32."
  - "Задержка диска: windows_physical_disk_*_latency_seconds_total нужно делить на число операций (rate по reads_total или writes_total), иначе значение неверно."
  - "windows_scheduled_task_last_result_status хранит результат в метке status (one-hot: success, terminated, unknown и др.), а не в значении."
  - "Не включать коллектор process и scheduled_task без фильтров: метрик становится слишком много."
  - "Коллектора cs в 0.32 нет."
related_files:
  - MONITORING-PROMETHEUS-GRAFANA-SETUP-2026-001
  - MONITORING-DASHBOARD-WMSDB-SERVER-2026-001
schema_version: "1.1"
environment: production
hostname: wmsDB
last_verified: 2026-11-11
---

# Установка windows_exporter на wmsDB и подключение к Prometheus

## Что настраивается и зачем

На боевой сервер БД WMS `wmsDB` (192.168.12.153, Windows Server 2022 Standard, ВМ Hyper-V) установлен `windows_exporter`, чтобы Prometheus на `wmssql-analytics` (192.168.12.202) собирал метрики сервера и MS SQL Server для дашбордов Grafana. Установка сделана по образцу пилота на `wmsDB-TEST`. Доступность сервера (up/down) остаётся за Zabbix.

## Предварительные условия
- [x] Установщик `windows_exporter-0.32.0-amd64.msi` лежит в `C:\Temp` на `wmsDB` (тот же файл, что на `wmsDB-TEST`).
- [x] Контрольная сумма SHA256 установщика совпала со строкой из официального `sha256sums.txt` релиза v0.32.0 (`d48ebad7999aac5603fe01007016a0ddbcecbc1aa0ecbc51867a2416b6c60a7d`).
- [x] Администратор подтвердил установку на боевой сервер и открытие порта 9182.
- [x] С `wmssql-analytics` доступен порт 1433 `wmsDB` (нужен позже для запросов к базе; для exporter не требуется).

## Шаги установки и настройки

Все команды и классы риска — в `../COMMANDS.md`, блоки 7–9.

1. **Добавить цель в Prometheus** [W] на `wmssql-analytics`: в `/opt/monitoring/prometheus/targets/windows.yml` добавить `192.168.12.153:9182` с метками `host: wmsDB`, `role: mssql`. Копия файла перед правкой. Prometheus подхватывает file_sd без перезапуска; до установки exporter цель в состоянии down.
2. **Проверить контрольную сумму MSI** [R] (`Get-FileHash`) и сравнить с официальным файлом сумм.
3. **Установить MSI** [W] с параметрами: `ENABLED_COLLECTORS=cpu,logical_disk,physical_disk,memory,net,os,service,system,tcp,mssql`, `LISTEN_PORT=9182`, `/qn /norestart`, лог установки в `C:\Temp`. Код возврата 0, служба `windows_exporter` работает, автозапуск.
4. **Создать правило Windows Firewall** [W]: вход, TCP 9182, удалённый адрес только 192.168.12.202, все профили, имя «windows_exporter (Prometheus 192.168.12.202)». MSI правило не создал (см. «Don't repeat»).
5. **Проверить доступность** [R]: с `wmssql-analytics` порт 9182 открыт, цель в Prometheus up.
6. **Включить дополнительные коллекторы** (решение администратора) [W]: переустановить MSI с `ENABLED_COLLECTORS=...,mssql,process,time,scheduled_task`, записать `C:\Program Files\windows_exporter\config.yaml` с фильтрами и перезапустить службу `windows_exporter` (SQL Server не затрагивается):
   ```yaml
   collector:
     process:
       include: 'sqlservr|windows_exporter'
     scheduled_task:
       exclude: '/Microsoft/.*'
   ```
   Первый вариант фильтра с обратными слэшами не сработал (156 задач вместо 2); исправлен. Копия конфига: `C:\Temp\config.yaml.bak-20261111`.

## Проверка результата
- [x] Цель `wmsDB` в Prometheus: up.
- [x] Метрики идут: около 4,6 тыс. серий, из них 654 по `windows_mssql_*`; коллекторы `process` (sqlservr, windows_exporter), `time`, `scheduled_task` (2 задачи Edge) отдают данные.
- [x] Время сбора около 0,08 с.
- [x] Службы MSSQLSERVER, SQLBrowser, SQLWriter, Zabbix Agent 2, windows_exporter работают.
- [ ] Не проверялось: влияние exporter на нагрузку сервера в течение суток (наблюдать на дашборде).

## Откат
- Удалить правило: `Remove-NetFirewallRule -DisplayName 'windows_exporter (Prometheus 192.168.12.202)'` [D/W по подтверждению].
- Удалить exporter: `msiexec /x` для `windows_exporter-0.32.0-amd64.msi` или вернуть прежний список коллекторов переустановкой MSI и вернуть `config.yaml` из копии.
- Убрать цель: вернуть `windows.yml` из копии `windows.yml.bak-20261111` на `wmssql-analytics`.

## ⛔ Don't repeat
См. `dont_repeat` во фронтматтере: каждый пункт — реальная преграда этой установки.

## Связанные документы
- `MONITORING-PROMETHEUS-GRAFANA-SETUP-2026-001` — стек Prometheus и Grafana.
- `MONITORING-DASHBOARD-WMSDB-SERVER-2026-001` — дашборд «wmsDB: Сервер» и пороги.

---
*Создан 2026-11-12 по чату от 2026-11-11 (проект Servers). Секреты, токены и имена учётных записей не включены.*
