---
schema_version: "1.1"
status: "in_progress"
date_created: 2026-11-09
date_modified: 2026-11-13
maintainer: "cladkyimaffin-hue"
file_type: "commands_reference"
confidence: "Блок 1 выполнялся в сессии 2026-11-09. Блоки 2–3 и 4–6 перенесены из документов домена и чата Servers; где дословная строка запуска не сохранилась, это указано в блоке. Блоки 7–9 выполнялись в сессии 2026-11-11, блоки 10–11 — в сессиях 2026-11-12 и 2026-11-13 (значения заменены плейсхолдерами). Источники — MONITORING-PROMETHEUS-GRAFANA-SETUP-2026-001, MONITORING-WINDOWS-EXPORTER-WMSDB-2026-001 и MONITORING-VAULTWARDEN-SETUP-2026-001."
---

# COMMANDS.md — команды мониторинга (Prometheus, Grafana, Docker, Windows, MS SQL, Vaultwarden)

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

Источник — `MONITORING-PROMETHEUS-GRAFANA-SETUP-2026-001`. Полные строки для `wmsDB` — в блоке 8.

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

## 7. Prometheus: цели и проверки (`wmssql-analytics`)

Источник — `MONITORING-WINDOWS-EXPORTER-WMSDB-2026-001`; выполнялось 2026-11-11.

```bash
# [W] Добавить цель Windows-сервера в file_sd — MONITORING-WINDOWS-EXPORTER-WMSDB-2026-001 (выполнялось)
# Сначала копия файла. Prometheus подхватывает без перезапуска; цель down, пока на сервере нет exporter
cd /opt/monitoring/prometheus/targets && cp -p windows.yml windows.yml.bak-<ГГГГММДД>
printf '%s\n' '- targets: ["<IP_сервера>:9182"]' '  labels:' '    host: <имя>' '    role: mssql' >> windows.yml
```

```text
# [W] Добавить метку title (отображаемое имя) к цели — выполнялось
# Правка файла windows.yml: строка `    title: "<отображаемое имя>"` под `role: ...` нужной цели. Перед правкой копия файла. Метку host не менять: потеряется история рядов
```

```bash
# [R] Состояние целей Prometheus — выполнялось
curl -s --max-time 10 http://127.0.0.1:9090/api/v1/targets | python3 -c "import sys,json; d=json.load(sys.stdin); [print(t['labels'].get('host'), t['scrapeUrl'], t['health'], (t.get('lastError') or '')[:80]) for t in d['data']['activeTargets']]"
```

```bash
# [R] Открыт ли порт на сервере с wmssql-analytics — выполнялось
for p in 1433 9182; do timeout 5 bash -c "echo > /dev/tcp/<IP_сервера>/$p" 2>/dev/null && echo "$p OPEN" || echo "$p CLOSED"; done
```

```bash
# [R] Запрос PromQL через API (число серий и пример) — выполнялось
# Для серий с составными запросами использовать --data-urlencode
curl -s --max-time 10 --data-urlencode 'query=count({host="<имя>"})' http://127.0.0.1:9090/api/v1/query
```

## 8. wmsDB: windows_exporter (Windows, PowerShell)

Источник — `MONITORING-WINDOWS-EXPORTER-WMSDB-2026-001`; выполнялось 2026-11-11.

```text
# [R] Контрольная сумма MSI — MONITORING-WINDOWS-EXPORTER-WMSDB-2026-001 (выполнялось)
# Сравнить со строкой windows_exporter-0.32.0-amd64.msi в sha256sums.txt релиза v0.32.0 (github.com/prometheus-community/windows_exporter)
Get-FileHash 'C:\Temp\windows_exporter-0.32.0-amd64.msi' -Algorithm SHA256
```

```text
# [W] Установка MSI с коллекторами — MONITORING-WINDOWS-EXPORTER-WMSDB-2026-001 (выполнялось; свойство REMOTE_ADDR правило фаервола не создало)
# Код возврата 0, служба windows_exporter Running. В PowerShell: Start-Process msiexec.exe -ArgumentList <массив аргументов> -Wait -PassThru
msiexec.exe /i C:\Temp\windows_exporter-0.32.0-amd64.msi ENABLED_COLLECTORS=cpu,logical_disk,physical_disk,memory,net,os,service,system,tcp,mssql LISTEN_PORT=9182 /qn /norestart /l*v C:\Temp\we_install.log
```

```text
# [W] Правило Windows Firewall: вход только с адреса Prometheus — MONITORING-WINDOWS-EXPORTER-WMSDB-2026-001 (выполнялось)
# Откат: Remove-NetFirewallRule -DisplayName '<то же имя>' (по подтверждению администратора)
New-NetFirewallRule -DisplayName 'windows_exporter (Prometheus <IP_Prometheus>)' -Direction Inbound -Action Allow -Protocol TCP -LocalPort 9182 -RemoteAddress <IP_Prometheus> -Profile Any
```

```text
# [R] Адрес и порт правила — MONITORING-WINDOWS-EXPORTER-WMSDB-2026-001 (выполнялось)
# Не передавать вывод Get-NetFirewallPortFilter конвейером в Get-NetFirewallAddressFilter: ошибка AmbiguousParameterSet
$r = Get-NetFirewallRule -DisplayName 'windows_exporter (Prometheus <IP_Prometheus>)'; (Get-NetFirewallAddressFilter -AssociatedNetFirewallRule $r).RemoteAddress; (Get-NetFirewallPortFilter -AssociatedNetFirewallRule $r).LocalPort
```

```text
# [W] Дополнительные коллекторы: переустановка MSI, config.yaml с фильтрами, перезапуск службы — MONITORING-WINDOWS-EXPORTER-WMSDB-2026-001 (выполнялось)
# Перед правкой config.yaml сделать копию. Конфиг записывался после переустановки MSI, в ASCII без BOM. Пути задач планировщика в метках с прямыми слэшами
msiexec.exe /i C:\Temp\windows_exporter-0.32.0-amd64.msi ENABLED_COLLECTORS=cpu,logical_disk,physical_disk,memory,net,os,service,system,tcp,mssql,process,time,scheduled_task LISTEN_PORT=9182 /qn /norestart /l*v C:\Temp\we_install2.log
# Содержимое C:\Program Files\windows_exporter\config.yaml, затем Restart-Service windows_exporter:
#   collector:
#     process:
#       include: 'sqlservr|windows_exporter'
#     scheduled_task:
#       exclude: '/Microsoft/.*'
```

```text
# [R] Передача скрипта PowerShell через SSH-оболочку cmd без проблем с кавычками — приём (выполнялся)
# cmd режет команду по символу | внутри кавычек. Лимит командной строки cmd около 8191 символов. Строка #< CLIXML в stderr — индикатор прогресса PowerShell, не ошибка
# Шаг 1 (Linux): закодировать скрипт в UTF-16LE и base64
python3 -c "import base64,sys; print(base64.b64encode(open(sys.argv[1],encoding='utf-8').read().encode('utf-16-le')).decode())" script.ps1
# Шаг 2 (на Windows через SSH): выполнить
powershell -NoProfile -EncodedCommand <base64>
```

```text
# [R] Журнал SQL Server: последние отказы входа — MONITORING-WINDOWS-EXPORTER-WMSDB-2026-001 (выполнялось)
# Путь ERRORLOG берётся из параметров запуска службы (реестр, параметр -e). Текст причины в журнале в CP866: при чтении по SSH показывается кракозябрами
Get-Content '<путь_к_ERRORLOG>' -Tail 400 | Where-Object { $_ -match 'Login failed' } | Select-Object -Last 8
```

## 9. wmssql-analytics: sqlcmd, вход в SQL, дашборды Grafana

Источник — `MONITORING-WINDOWS-EXPORTER-WMSDB-2026-001` и `MONITORING-DASHBOARD-WMSDB-SERVER-2026-001`; выполнялось 2026-11-11.

```bash
# [W] Установить sqlcmd (go-sqlcmd) без вопросов — выполнялось (репозиторий Microsoft уже был подключён)
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y sqlcmd < /dev/null
```

```bash
# [W] Положить пароль читающего SQL-логина в файл на сервере — выполняет администратор вручную (выполнялось)
# Значение пароля вводится с клавиатуры без эха и не попадает в чат и репозиторий. Файл: владелец root, права 600; каталог права 700
sudo install -d -m 700 /opt/monitoring/secrets && read -rs -p 'Password: ' P && printf '%s' "$P" | sudo tee /opt/monitoring/secrets/<файл>.pass >/dev/null && unset P && sudo chmod 600 /opt/monitoring/secrets/<файл>.pass
```

```bash
# [R] Проверка входа читающего логина и его прав — выполнялось
# Пароль берётся из файла внутри команды через переменную окружения и не печатается. Одна попытка: каждый отказ пишется в журнал SQL Server. Если вход не прошёл, сначала прочитать причину в журнале (блок 8)
SQLCMDPASSWORD="$(sudo cat /opt/monitoring/secrets/<файл>.pass)" sqlcmd -S <IP_сервера>,1433 -U <логин> -d <база> -C -l 10 -W -s "|" -Q "SET NOCOUNT ON; SELECT SUSER_NAME(), DB_NAME(), IS_SRVROLEMEMBER('sysadmin'), HAS_PERMS_BY_NAME(NULL,NULL,'VIEW SERVER STATE'), SERVERPROPERTY('ProductVersion'), SERVERPROPERTY('Edition');" < /dev/null
```

```bash
# [R] Поиск дашбордов в Grafana через API; пароль берётся из .env и не печатается — выполнялось
# Переменная в .env называется GF_ADMIN_PASSWORD; имя учётной записи администратора Grafana — в приватном реестре
PW="$(sudo grep -E '^GF_ADMIN_PASSWORD=' /opt/monitoring/.env | cut -d= -f2-)"
curl -s --max-time 10 -u "<админ_Grafana>:$PW" 'http://127.0.0.1:3000/api/search?query=<текст>'
```

```bash
# [W] Переименовать дашборд, подключённый из файла (provisioning) — выполнялось
# Сначала копия. Менять только строку title (проверить, что она встречается один раз). uid не менять. Grafana подхватывает файл в течение минуты. Правки в интерфейсе Grafana для таких дашбордов не сохраняются
cd /opt/monitoring/grafana/dashboards && cp -p <файл>.json <файл>.json.bak-<ГГГГММДД>
grep -n '"title": "<старое имя>"' <файл>.json
sed -i '<номер_строки>s/"title": "<старое имя>"/"title": "<новое имя>"/' <файл>.json
```

```bash
# [W] Разместить дашборд, собранный генератором — MONITORING-DASHBOARD-WMSDB-SERVER-2026-001 (выполнялось)
# Новый файл рядом с остальными; существующие не затрагиваются. Откат: удалить файл. Подхват до минуты
python3 /opt/monitoring/tools/dashboards/gen_server.py /tmp/<выходной>.json && cp /tmp/<выходной>.json /opt/monitoring/grafana/dashboards/<имя>.json
```

## 10. Сервер паролей Vaultwarden (`wmssql-analytics`)

Источник — `MONITORING-VAULTWARDEN-SETUP-2026-001`; выполнялось 2026-11-12.

```bash
# [R] Проверка условий перед установкой: порты, ресурсы, время, реестры образов — MONITORING-VAULTWARDEN-SETUP-2026-001 (выполнялось)
ss -ltnH | awk '{print $4}' | sort -u
free -m | sed -n '1,2p'; df -h / | tail -1
timedatectl | grep -E 'System clock synchronized|NTP service'
for u in https://registry-1.docker.io/v2/ https://ghcr.io/v2/; do curl -4 -sS -o /dev/null -m 12 -w "$u %{http_code} %{time_total}s\n" "$u"; done
```

```bash
# [R] Какие версии образа есть в ghcr.io (анонимный токен только на чтение) — MONITORING-VAULTWARDEN-SETUP-2026-001 (выполнялось)
TOK=$(curl -s 'https://ghcr.io/token?service=ghcr.io&scope=repository:dani-garcia/vaultwarden:pull' | python3 -c 'import sys,json; print(json.load(sys.stdin)["token"])')
curl -s -H "Authorization: Bearer $TOK" 'https://ghcr.io/v2/dani-garcia/vaultwarden/tags/list?n=1000'
```

```bash
# [W] Скачать образы — MONITORING-VAULTWARDEN-SETUP-2026-001 (выполнялось; откат: docker rmi <образ>)
# Docker Hub с этого сервера нестабилен (DNS по таймауту): при ошибке повторить pull. Образ Caddy фиксировать по digest
sudo docker pull ghcr.io/dani-garcia/vaultwarden:<версия> < /dev/null
sudo docker pull caddy:2 < /dev/null
sudo docker image inspect caddy:2 --format '{{index .RepoDigests 0}}'
```

```text
# [W] Содержимое /opt/vaultwarden/docker-compose.yml (без секретов) — MONITORING-VAULTWARDEN-SETUP-2026-001 (выполнялось)
# Каталоги создать заранее: data (права 700), caddy-data, caddy-config, secrets (права 700)
name: vaultwarden
services:
  vaultwarden:
    image: ghcr.io/dani-garcia/vaultwarden:<версия>
    container_name: vaultwarden
    restart: unless-stopped
    env_file: ./vaultwarden.env
    environment:
      DOMAIN: "https://<IP_сервера>:<порт>"
      SIGNUPS_ALLOWED: "false"
      INVITATIONS_ALLOWED: "true"
      SHOW_PASSWORD_HINT: "false"
    volumes:
      - ./data:/data
    mem_limit: 256m
    networks: [vwnet]
  caddy:
    image: caddy@sha256:<digest>
    container_name: vaultwarden-caddy
    restart: unless-stopped
    ports:
      - "<порт>:<порт>"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - ./caddy-data:/data
      - ./caddy-config:/config
    mem_limit: 128m
    depends_on: [vaultwarden]
    networks: [vwnet]
networks:
  vwnet: {}
```

```text
# [W] Содержимое /opt/vaultwarden/Caddyfile — MONITORING-VAULTWARDEN-SETUP-2026-001 (выполнялось)
# default_sni нужен: без него заход по IP даёт TLS-ошибку internal error (контейнер видит свой адрес). После правки: cp -p Caddyfile Caddyfile.bak-<ГГГГММДД> и docker compose restart caddy
{
	admin off
	default_sni <IP_сервера>
}

https://<IP_сервера>:<порт> {
	tls internal
	encode zstd gzip
	reverse_proxy vaultwarden:80
}
```

```bash
# [W] Токен администратора и его хеш Argon2id без печати значений — MONITORING-VAULTWARDEN-SETUP-2026-001 (выполнялось; требуется пакет argon2)
# Токен и хеш не печатать, в том числе через sed «с маскировкой»: маскировка может не сработать. Проверять только по коду ответа и логу
umask 077
TOKEN=$(openssl rand -base64 36 | tr -d '\n')
printf '%s' "$TOKEN" > /opt/vaultwarden/secrets/admin_token.txt
HASH=$(printf '%s' "$TOKEN" | argon2 "$(openssl rand -hex 8)" -id -t 3 -m 16 -p 4 -l 32 -e)
printf "ADMIN_TOKEN='%s'\n" "$HASH" > /opt/vaultwarden/vaultwarden.env
unset TOKEN HASH
chmod 600 /opt/vaultwarden/vaultwarden.env /opt/vaultwarden/secrets/admin_token.txt
```

```bash
# [W] Запуск и пересоздание сервиса — MONITORING-VAULTWARDEN-SETUP-2026-001 (выполнялось)
# После смены vaultwarden.env нужно пересоздать контейнер (restart env_file не перечитывает). Откат: docker compose down
cd /opt/vaultwarden && sudo docker compose up -d < /dev/null
cd /opt/vaultwarden && sudo docker compose up -d --force-recreate vaultwarden < /dev/null
```

```bash
# [R] Проверка сайта и токена администратора — MONITORING-VAULTWARDEN-SETUP-2026-001 (выполнялось)
# Код 200 при верном токене (страница админки и cookie, не 303), 401 при неверном. Токен читается из файла без вывода
curl -k -sS -m 10 https://<IP_сервера>:<порт>/alive
sudo curl -k -sS -m 15 -o /dev/null -w '%{http_code}\n' --data-urlencode 'token@/opt/vaultwarden/secrets/admin_token.txt' https://<IP_сервера>:<порт>/admin
```

```bash
# [R] Корневой сертификат Caddy и сертификат сайта — MONITORING-VAULTWARDEN-SETUP-2026-001 (выполнялось)
# Корень публичный (не секрет), его нужно установить на каждый ПК. Ключ root.key лежит рядом и в копии не копируется
R=/opt/vaultwarden/caddy-data/caddy/pki/authorities/local/root.crt
sudo openssl x509 -in "$R" -noout -subject -dates -fingerprint -sha256
echo | openssl s_client -connect 127.0.0.1:<порт> -servername <IP_сервера> 2>/dev/null | openssl x509 -noout -issuer -dates -ext subjectAltName
```

```bash
# [D] Удалить файлы прежнего токена и env после ротации — MONITORING-VAULTWARDEN-SETUP-2026-001 (REQUIRES_APPROVAL; выполнялось по решению администратора 2026-11-12/13)
# shred перезаписывает файл перед удалением; восстановить удалённое нельзя
sudo shred -u <файл_env.old-ГГГГММДД> <файл_токена.old-ГГГГММДД>
```

## 11. Резервная копия базы Vaultwarden (`wmssql-analytics`)

Источник — `MONITORING-VAULTWARDEN-SETUP-2026-001`; выполнялось 2026-11-13.

```bash
# [R] Проверка шары перед настройкой — MONITORING-VAULTWARDEN-SETUP-2026-001 (выполнялось)
# Пароли и имена учётных записей из параметров монтирования не печатать: фильтровать только нужные ключи
findmnt -no FSTYPE,SIZE,USED,AVAIL /mnt/wmsbackup
findmnt -no OPTIONS /mnt/wmsbackup | tr ',' '\n' | grep -E '^(vers|file_mode|dir_mode|rw|ro)'
```

```bash
# [W] Скрипт /opt/vaultwarden/backup.sh (владелец root, права 700) — MONITORING-VAULTWARDEN-SETUP-2026-001 (выполнялось)
# Копия делается через API резервного копирования SQLite (без остановки сервиса). Ротация: оставить 7 самых новых по времени изменения, остальные удалить (решение администратора)
#!/bin/bash
set -euo pipefail
SRC=/opt/vaultwarden/data
MNT=/mnt/wmsbackup
DEST=$MNT/vaultwarden
KEEP=7
ls "$MNT" >/dev/null 2>&1 || true
mountpoint -q "$MNT" || { echo "ОШИБКА: шара $MNT не смонтирована" >&2; exit 1; }
mkdir -p "$DEST"
TMP=$(mktemp -d /var/tmp/vwbackup.XXXXXX)
trap 'rm -rf "$TMP"' EXIT
python3 - "$SRC" "$TMP" <<'PY'
import sqlite3, sys, json, os, shutil
src, tmp = sys.argv[1], sys.argv[2]
s = sqlite3.connect(os.path.join(src, 'db.sqlite3'))
d = sqlite3.connect(os.path.join(tmp, 'db.sqlite3'))
with d:
    s.backup(d)
res = d.execute('PRAGMA integrity_check').fetchone()[0]
s.close(); d.close()
if res != 'ok':
    sys.exit('ОШИБКА: integrity_check = %s' % res)
for name in ('attachments', 'sends'):
    p = os.path.join(src, name)
    if os.path.isdir(p):
        shutil.copytree(p, os.path.join(tmp, name))
cfg = os.path.join(src, 'config.json')
if os.path.isfile(cfg):
    keys = list(json.load(open(cfg)).keys())
    bad = [k for k in keys if any(w in k.lower() for w in ('pass', 'token', 'secret', 'key'))]
    if bad:
        print('config.json не включён: есть чувствительные ключи (%d)' % len(bad))
    else:
        shutil.copy2(cfg, os.path.join(tmp, 'config.json'))
        print('config.json включён')
PY
NAME="db_passwd_$(date +%d.%m.%Y).tar.gz"
( cd "$TMP" && tar -czf "$TMP/$NAME" $(ls -d db.sqlite3 attachments sends config.json 2>/dev/null) )
tar -tzf "$TMP/$NAME" >/dev/null
cp "$TMP/$NAME" "$DEST/$NAME.part"
mv -f "$DEST/$NAME.part" "$DEST/$NAME"
ls -1t "$DEST"/db_passwd_*.tar.gz | tail -n +$((KEEP+1)) | xargs -r rm -f --
echo "OK: $NAME, $(stat -c %s "$DEST/$NAME") байт; копий в папке: $(ls -1 "$DEST"/db_passwd_*.tar.gz | wc -l)"
```

```text
# [W] Служба и таймер systemd — MONITORING-VAULTWARDEN-SETUP-2026-001 (выполнялось)
# /etc/systemd/system/vaultwarden-backup.service:
[Unit]
Description=Резервная копия базы Vaultwarden на сетевую шару
After=network-online.target remote-fs.target

[Service]
Type=oneshot
ExecStart=/opt/vaultwarden/backup.sh

# /etc/systemd/system/vaultwarden-backup.timer:
[Unit]
Description=Ежедневная копия базы Vaultwarden

[Timer]
OnCalendar=*-*-* 02:00:00
Persistent=true
RandomizedDelaySec=300

[Install]
WantedBy=timers.target
```

```bash
# [W] Включить таймер и делать пробный запуск — MONITORING-VAULTWARDEN-SETUP-2026-001 (выполнялось)
# Откат: systemctl disable --now vaultwarden-backup.timer
sudo systemctl daemon-reload && sudo systemctl enable --now vaultwarden-backup.timer
sudo systemctl start vaultwarden-backup.service
sudo journalctl -u vaultwarden-backup.service -n 6 --no-pager -o cat
systemctl list-timers vaultwarden-backup.timer --no-pager
```

```bash
# [R] Проверка архива без вывода содержимого — MONITORING-VAULTWARDEN-SETUP-2026-001 (выполнялось)
# Показывает только целостность и количества строк. Восстановление из копии полностью не проверялось
tar -tzf /mnt/wmsbackup/vaultwarden/db_passwd_<ДД.ММ.ГГГГ>.tar.gz
T=$(mktemp -d /var/tmp/vwchk.XXXXXX); tar -xzf /mnt/wmsbackup/vaultwarden/db_passwd_<ДД.ММ.ГГГГ>.tar.gz -C "$T" db.sqlite3
python3 -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); print(c.execute('PRAGMA integrity_check').fetchone()[0]); [print(t, c.execute('SELECT count(*) FROM '+t).fetchone()[0]) for t in ('users','ciphers','folders')]" "$T/db.sqlite3"; sudo rm -rf "$T"
```

## Покрытие

В файле только то, что выполнено или описано в материалах. Записаны полные строки установки `windows_exporter` (`msiexec`), правила Windows Firewall и добавления цели для `wmsDB` (блоки 7–9), а также установки сервера паролей и резервной копии (блоки 10–11; в блоке 10 адрес и порт заменены плейсхолдерами). **Не записаны**, потому что дословных строк нет или они выполнялись администратором вне чата: правило `ufw`, содержимое `docker-compose.yml` и `prometheus.yml` стека мониторинга, запросы PromQL дашборда «wmsDB: Сервер» (они в генераторе `/opt/monitoring/tools/dashboards/gen_server.py` и в JSON дашборда), скрипт создания читающего SQL-логина (создан администратором), и настройка клиента Bitwarden на ПК (делает пользователь в интерфейсе). Генератор старого дашборда «ТЕСТ (wmsDB-TEST): Windows Server + MS SQL» не сохранился (INFERRED).

## Как дополнять

1. Команда попадает сюда только из обработанного документа домена с указанием его `document_id` в строке-комментарии блока.
2. Класс `[R]`/`[W]`/`[D]` ставится по наиболее опасной строке блока.
3. Секреты и конкретные значения адресов в команды не вшиваются — плейсхолдеры.
4. При каждом дополнении обновить `date_modified` и раздел «Покрытие».
