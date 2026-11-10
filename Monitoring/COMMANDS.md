---
schema_version: "1.1"
status: "in_progress"
date_created: 2026-11-09
date_modified: 2026-11-10
maintainer: "cladkyimaffin-hue"
file_type: "commands_reference"
confidence: "Блок 1 выполнялся в сессии 2026-11-09. Блоки 2–3 и 4–6 перенесены из документов домена и чата Servers; где дословная строка запуска не сохранилась, это указано в блоке. Источник документов — MONITORING-PROMETHEUS-GRAFANA-SETUP-2026-001."
---

# COMMANDS.md — команды мониторинга (Prometheus, Grafana, Docker, Windows, MS SQL)

Справочник команд, к которым нужно возвращаться, отдельно от описаний. Команды остаются и в своих документах (там контекст, ожидаемый вывод и ограничения), здесь — быстрый доступ, сгруппированный по задачам.

## Как пользоваться

Каждый блок начинается со строки-комментария: `[класс] что делает — источник`.

Классы риска:

- **[R]** — только чтение. Безопасно выполнять для диагностики.
- **[W]** — меняет конфигурацию или состояние системы. Перед выполнением проверить текущее состояние и знать откат.
- **[D]** — разрушающая или необратимая. Только по явному подтверждению администратора (метка `REQUIRES_APPROVAL`, см. `../AI-INSTRUCTIONS.md`, раздел 3).

Правила:

- **Блок с несколькими командами — перечень, а не скрипт.** Выполнять нужные строки по одной, кроме блоков с пометкой «по порядку».
- `<угловые скобки>` — плейсхолдер, подставить своё значение. Адреса, имена серверов и порты брать из `AI-environment_facts-meridian-monitoring.md` или из свежего вывода, не из этого файла.
- **Секреты (пароли, токены, ключи) здесь не хранятся.**
- Источник указан как `document_id` из `00_Meta/registry.csv` или как «сессия».

---

## 1. Диагностика сервера и доступа к GitHub (Ubuntu, `wmssql-analytics`)

```bash
# [R] Есть ли git и какой версии — сессия 2026-11-09 (выполнялось)
# Ожидается: путь /usr/bin/git и строка версии
command -v git && git --version
```

```bash
# [R] Разрешается ли имя github.com — сессия 2026-11-09 (выполнялось)
# Пустой вывод означает проблему с DNS
getent hosts github.com
```

```bash
# [R] Доходит ли HTTPS до GitHub и с какой скоростью ответа — сессия 2026-11-09 (выполнялось)
# Ожидается http_code=200. -4 — принудительно IPv4: IPv6 на этом сервере не маршрутизируется
curl -4 -sS -o /dev/null -m 15 -w "http_code=%{http_code} time=%{time_total}s\n" https://github.com
```

```bash
# [R] Настроен ли git и есть ли ключи для записи — сессия 2026-11-09 (выполнялось)
# На дату проверки: ~/.gitconfig, ~/.git-credentials и SSH-ключа для GitHub не было
git config --global --list
ls -l ~/.git-credentials
ls ~/.ssh
```

```bash
# [R] Публичный репозиторий читается без авторизации — сессия 2026-11-09 (выполнялось)
# Временный клон удалять сразу после работы. GIT_TERMINAL_PROMPT=0 — не зависать на запросе логина
GIT_TERMINAL_PROMPT=0 git clone --depth 1 https://github.com/<владелец>/<репозиторий>.git /tmp/<временная_папка>
```

```bash
# [R] Поиск признаков секретов в клоне без вывода значений — сессия 2026-11-09 (выполнялось)
# Показывает только имена файлов и число строк (-c), значения не печатает. Список шаблонов — минимум, не гарантия отсутствия секретов
grep -rIEc --exclude-dir=.git -e '[Pp]assword[[:space:]]*[=:]|[Пп]ароль[[:space:]]*[=:]|Password=|BEGIN [A-Z ]*PRIVATE KEY|Bearer [A-Za-z0-9._-]{20,}' . | grep -v ':0$'
```

```bash
# [W] Удалить отпечаток github.com из known_hosts, добавленный при проверке SSH-входа — сессия 2026-11-09 (не запускалась)
# Проверка `ssh -o StrictHostKeyChecking=accept-new git@github.com` добавила запись в ~/.ssh/known_hosts; безвредно, но можно убрать
ssh-keygen -R github.com
```

## 2. Linux: пакеты без терминала (apt/dpkg)

Источник — описание в чате Servers 2026-11-09 и `MONITORING-PROMETHEUS-GRAFANA-SETUP-2026-001`: без терминала `apt`/`dpkg` зависают на вопросах debconf. Дословная строка запуска не сохранилась, приём записан по сути. При узком списке разрешённых `sudo`-команд переменную окружения через `env` задать нельзя.

```bash
# [W] Установка пакета без вопросов — приём из чата (дословно не сохранён)
# < /dev/null — чтобы stdin не ждал ввода; DEBIAN_FRONTEND=noninteractive — без диалогов debconf
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y <пакет> < /dev/null
```

```bash
# [W] Довести настройку пакетов после прерванного apt — рекомендация из чата
# Прерванная установка оставляет пакеты в недонастроенном состоянии
sudo dpkg --configure -a
```

```bash
# [W] Внутри собственной команды не использовать pkill -f '<текст>' — предупреждение из чата
# pkill -f совпадает с полной строкой запуска, включая строку с текстом шаблона, и убивает оболочку, в которой выполняется.
# Сначала найти PID и завершить по номеру:
pgrep -af '<текст>'
kill <PID>
```

## 3. Windows (SSH-оболочка cmd, `wmsDB`, `wmsDB-TEST`)

Источник — описание в чате Servers: оболочка SSH на Windows — `cmd` (нет `head`, `uname`), вывод в CP866 искажается; для текста нужен `powershell -Command` с UTF-8. Дословные строки запуска не сохранились.

```text
# [R] Обёртка для чтения текста без кракозябр — приём из чата (дословно не сохранён)
# Внутри кавычек — команда PowerShell, вывод переводится в UTF-8
powershell -Command "[Console]::OutputEncoding=[Text.Encoding]::UTF8; <команда PowerShell>"
```

```text
# [R] Состояние службы windows_exporter — имя службы из чата; дословный запуск не сохранён
# Ожидается Running, автозапуск Automatic. Данные сервера — в AI-environment_facts-meridian-monitoring.md
Get-Service windows_exporter | Format-List Name, Status, StartType
```

## 4. Docker и стек мониторинга (`wmssql-analytics`)

Источник — `MONITORING-PROMETHEUS-GRAFANA-SETUP-2026-001`.

```bash
# [R] Что осталось от Docker: образы, тома, занятое место — MONITORING-PROMETHEUS-GRAFANA-SETUP-2026-001
docker system df
docker volume ls
```

```bash
# [R] Размер каталогов старого Docker — MONITORING-PROMETHEUS-GRAFANA-SETUP-2026-001
sudo du -sh /var/lib/docker /var/lib/containerd
```

```bash
# [W] Каталог стека, чтобы конфиги не требовали root — MONITORING-PROMETHEUS-GRAFANA-SETUP-2026-001 (команда из чата)
sudo mkdir -p /opt/monitoring && sudo chown user:user /opt/monitoring
```

```bash
# [W] Запуск и остановка стека, по одной строке — MONITORING-PROMETHEUS-GRAFANA-SETUP-2026-001
# down без ключа -v тома не удаляет, история Prometheus сохраняется
cd /opt/monitoring && docker compose up -d
cd /opt/monitoring && docker compose down
```

```bash
# [W] Проверка Docker после установки — MONITORING-PROMETHEUS-GRAFANA-SETUP-2026-001
# Скачивает образ и запускает контейнер
docker run hello-world
```

```bash
# [D] Удалить все неиспользуемые образы — MONITORING-PROMETHEUS-GRAFANA-SETUP-2026-001 (REQUIRES_APPROVAL)
# Образы из недоступного реестра вернуть будет нечем
docker image prune -a
```

```bash
# [R] SSH-туннель к Prometheus, который слушает только 127.0.0.1:9090 — MONITORING-PROMETHEUS-GRAFANA-SETUP-2026-001
# Затем открыть http://localhost:9090. В PuTTY: Connection, SSH, Tunnels
ssh -L 9090:127.0.0.1:9090 user@<адрес_сервера>
```

## 5. Удаление ненужных пакетов и пользователей (`wmssql-analytics`)

Источник — `MONITORING-PROMETHEUS-GRAFANA-SETUP-2026-001`. Выполнялось 2026-11-09 по решению администратора без бэкапа.

```bash
# [D] Удалить PostgreSQL 16 вместе с данными — MONITORING-PROMETHEUS-GRAFANA-SETUP-2026-001 (REQUIRES_APPROVAL)
# По порядку. При работе без терминала использовать приём из блока 2. Удаляет и базу
sudo apt-get purge postgresql-16 postgresql-client-16 postgresql-common postgresql-client-common
sudo apt-get autoremove --purge
```

```bash
# [D] Удалить пользователей ОС — MONITORING-PROMETHEUS-GRAFANA-SETUP-2026-001 (REQUIRES_APPROVAL)
# Предложено в чате; на 2026-11-09 пользователи zabbix и postgres остались
sudo userdel zabbix
sudo userdel postgres
```

```bash
# [W] Остановить службу systemd — MONITORING-PROMETHEUS-GRAFANA-SETUP-2026-001
# Так остановлены остаточные процессы Zabbix; дословное имя службы в чате не приведено
sudo systemctl stop <служба>
```

## 6. windows_exporter и проверка метрик

Источник — `MONITORING-PROMETHEUS-GRAFANA-SETUP-2026-001`.

```text
# [W] Свойства установки MSI windows_exporter 0.32 — MONITORING-PROMETHEUS-GRAFANA-SETUP-2026-001
# Полная строка msiexec в материалах не сохранилась; сохранены свойства. Коллектора cs в 0.32 нет. mssql добавлять только на сервере с SQL Server
# После установки: правило Windows Firewall — вход TCP 9182 только с адреса сервера Prometheus
ENABLED_COLLECTORS=cpu,logical_disk,physical_disk,memory,net,os,service,system,tcp
LISTEN_PORT=9182
```

```text
# [R] Проверка метрики в Grafana: Explore, источник Prometheus — MONITORING-PROMETHEUS-GRAFANA-SETUP-2026-001
windows_mssql_genstats_user_connections
```

## Покрытие

В файле только то, что выполнено или описано в материалах. **Не записаны**, потому что дословных строк нет: полная команда установки `windows_exporter` (`msiexec`), правило Windows Firewall, правило `ufw`, содержимое `docker-compose.yml` и `prometheus.yml`, запросы PromQL дашборда, скрипт создания читающего SQL-логина. Их нужно добавить после обработки соответствующих материалов.

## Как дополнять

1. Команда попадает сюда только из обработанного документа домена с указанием его `document_id` в строке-комментарии блока.
2. Класс `[R]`/`[W]`/`[D]` ставится по наиболее опасной строке блока.
3. Секреты и конкретные значения адресов в команды не вшиваются — плейсхолдеры.
4. При каждом дополнении обновить `date_modified` и раздел «Покрытие».
