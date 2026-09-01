### USER
ЗАДАЧА: Запустить Qtech и сделать его доступным по адресу http://192.168.12.154 (порт 80). Ошибка в браузере: ERR_CONNECTION_REFUSED.
АРХИТЕКТУРА:
VM сервер: wmswifi (IP: 192.168.12.154).
Путь к проекту: /opt/wimark/one.
Управление: Docker Compose.
Связка: Nginx (прокси) -> Docker контейнер wimark-web-client (порт 80 внутри).
ТЕКУЩИЙ СТАТУС И ПРОДЕЛАННЫЕ ДЕЙСТВИЯ:
Контейнер one-wimark-web-client-1 работает, но в исходном docker-compose.yml у него нет прямого проброса портов на хост.
За внешний доступ должен отвечать контейнер one-nginx-proxy-ssl-1 (в конфиге прописано ports: - 80:80 и 443:443). Изначально он падал с Exit 128 из-за таймаута к Let's Encrypt при старте (интернет внутри Docker-сети не работает, но для Qtech он и не нужен).
На хосте были запущены системные Nginx (занимал порт 80) и Apache2 (слушал 8090). Системный Nginx остановлен командой systemctl stop nginx.
Брандмауэр UFW активен, порты 80 и 443 разрешены (ALLOW).
В docker-compose.yml был временно добавлен проброс 80:8080 для wimark-web-client, но он был удален, так как блокировал порт 80 для nginx-proxy-ssl.
При запуске nginx-proxy-ssl возникла новая ошибка: host not found in upstream "wimark-web-client:80". Nginx внутри контейнера не может резолвить имя фронтенда.
Диагностика сетей показала, что wimark-web-client находится в сети one_default, а nginx-proxy-ssl по какой-то причине не подключен ни к одной сети Docker (вывод docker inspect пуст).
В сети one_default находятся 27 других контейнеров проекта, но nginx-proxy-ssl среди них отсутствует.
ПОСЛЕДНЕЕ ДЕЙСТВИЕ:
Выполнена команда docker compose up -d --force-recreate nginx-proxy-ssl, чтобы пересоздать контейнер и заставить его корректно подключиться к сети one_default.
СЛЕДУЮЩИЙ ШАГ:
Проверить результат выполнения последней команды. Нужно убедиться, что контейнер nginx-proxy-ssl запустился, физически подключился к сети one_default и не падает с ошибкой DNS. Для этого нужно выполнить:
docker network inspect one_default --format '{{range .Containers}}{{.Name}} {{end}}' (чтобы убедиться, что он появился в списке) и docker logs one-nginx-proxy-ssl-1 --tail 20.

### ASSISTANT
**Шаг 1 — Проверка результата пересоздания контейнера nginx-proxy-ssl**

**Объяснение/Действие:**  
Согласно вашему плану, нам необходимо убедиться, что команда `docker compose up -d --force-recreate nginx-proxy-ssl` отработала корректно и устранила проблему с сетью. Для этого нужно проверить, появился ли контейнер в сети `one_default` и отсутствуют ли ошибки DNS в его логах.

Пожалуйста, выполните на сервере (192.168.12.154) следующие команды и предоставьте их точный вывод:
1. `docker network inspect one_default --format '{{range .Containers}}{{.Name}} {{end}}'`
2. `docker logs one-nginx-proxy-ssl-1 --tail 20`
3. `docker ps -f name=nginx-proxy-ssl` (для подтверждения текущего статуса работы контейнера)

**Протокол:**  
- **Цель:** Сделать Qtech доступным по адресу http://192.168.12.154 (порт 80).  
- **Контекст:** Контейнер `nginx-proxy-ssl` ранее не был подключен к сети `one_default`, что вызывало ошибку `host not found in upstream "wimark-web-client:80"`.  
- **Последнее действие:** Пересоздание контейнера через `docker compose up -d --force-recreate nginx-proxy-ssl`.  
- **Текущий фокус:** Верификация того, что контейнер запустился и корректно подключился к сети `one_default`.

**Вопросы:**  
Какой вывод дали указанные выше команды? Жду ваш ответ, чтобы зафиксировать результат и предложить следующий микро-шаг. (Напоминаю: я не буду описывать дальнейшие действия до вашего подтверждения «ок», «продолжай» или аналогичного).

### USER
ard# docker compose up -d --force-recreate nginx-proxy-ssl
no configuration file provided: not found
root@wmswifi:/opt/Docker-dashboard# docker network inspect one_default --format '{{range .Containers}}{{.Name}} {{end}}'
one-gproxy-service-1 one-http-to-smtp-1 one-nginx-cors-1 one-radar-mw-1 one-backend-golang-1 one-rrm-daemon-golang-1 one-gapi-service-1 one-mosquitto-1 one-portal-admin-1 one-lbs-daemon-1 one-statdaemon-golang-1 one-redis-1 one-mongo-1 one-gsnmp-service-1 one-smtp-relay-1 one-configurer-golang-1 one-redirect-daemon-1 one-mongo-connector-golang-1 one-portal-frontend-1 one-ntp-1 one-radius-gw-1 one-portal-backend-1 one-portal-nginx-1 one-wimark-web-client-1 one-radar-export-mw-1 one-analytics-mw-1 one-event-monitor-golang-1
root@wmswifi:/opt/Docker-dashboard# docker logs one-nginx-proxy-ssl-1 --tail 20
  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0
curl: (7) Failed to connect to 127.0.0.1 port 80 after 0 ms: Couldn't connect to server
2026/07/17 20:29:33 [ DEBUG ] Parsing environment references in '/etc/nginx/conf.d/default.conf'
2026/07/17 20:29:33 [ DEBUG ] Parsing environment references in '/etc/nginx/conf.d/default.conf.one'
2026/07/17 20:29:33 [ DEBUG ] Parsing environment references in '/etc/nginx/conf.d/default.conf.wlc'
2026/07/17 20:29:33 [emerg] 12145#12145: host not found in upstream "wimark-web-client:80" in /etc/nginx/conf.d/default.conf:2
nginx: [emerg] host not found in upstream "wimark-web-client:80" in /etc/nginx/conf.d/default.conf:2
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0
curl: (7) Failed to connect to 127.0.0.1 port 80 after 0 ms: Couldn't connect to server
2026/07/17 20:29:34 [ DEBUG ] Parsing environment references in '/etc/nginx/conf.d/default.conf'
2026/07/17 20:29:34 [ DEBUG ] Parsing environment references in '/etc/nginx/conf.d/default.conf.one'
2026/07/17 20:29:34 [ DEBUG ] Parsing environment references in '/etc/nginx/conf.d/default.conf.wlc'
2026/07/17 20:29:34 [emerg] 12151#12151: host not found in upstream "wimark-web-client:80" in /etc/nginx/conf.d/default.conf:2
nginx: [emerg] host not found in upstream "wimark-web-client:80" in /etc/nginx/conf.d/default.conf:2
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0
curl: (7) Failed to connect to 127.0.0.1 port 80 after 0 ms: Couldn't connect to server
root@wmswifi:/opt/Docker-dashboard# docker ps -f name=nginx-proxy-ssl
CONTAINER ID   IMAGE                                           COMMAND   CREATED          STATUS          PORTS     NAMES
271527abdeae   repo.wimark.local:5000/nginx-proxy-ssl:1.11.4   "/init"   39 minutes ago   Up 30 minutes             one-nginx-proxy-ssl-1
root@wmswifi:/opt/Docker-dashboard#

### ASSISTANT
**Шаг 2 — Переход в правильную директорию и пересоздание контейнера**

**Объяснение/Действие:**  
Команда `docker compose up -d --force-recreate nginx-proxy-ssl` завершилась с ошибкой `no configuration file provided: not found`, потому что она была выполнена в директории `/opt/Docker-dashboard`. Согласно архитектуре, проект находится в `/opt/wimark/one`. 

Из-за этого контейнер `nginx-proxy-ssl` фактически не был пересоздан. Это подтверждается тремя фактами из вашего вывода:
1. Его нет в списке контейнеров сети `one_default`.
2. В логах сохраняется старая ошибка `host not found in upstream "wimark-web-client:80"`.
3. Время создания контейнера в `docker ps` осталось прежним ("39 minutes ago").

Необходимо выполнить команду пересоздания из правильной директории, где лежит `docker-compose.yml`. Выполните на сервере следующую команду:
```bash
cd /opt/wimark/one && docker compose up -d --force-recreate nginx-proxy-ssl
```

**Протокол:**  
- Текущая директория выполнения команды была неверной (`/opt/Docker-dashboard` вместо `/opt/wimark/one`).  
- Контейнер `one-nginx-proxy-ssl-1` не был обновлен и до сих пор не подключен к сети `one_default`.  
- Ошибка резолвинга имени `wimark-web-client` внутри Nginx сохраняется.  

**Вопросы:**  
Какой точный вывод даст команда `cd /opt/wimark/one && docker compose up -d --force-recreate nginx-proxy-ssl`? Жду вашего ответа, чтобы зафиксировать результат и двигаться дальше.

### USER
Он запустился но пишет такое
Осталось лицензия всего на один портал (или меньше). Если вы хотите использовать больше порталов, следует добавить лицензии. Перейти к лицензиям
Я так понял кудато 8 лицензий делось!

### ASSISTANT
**Шаг 1 — Проверка текущих лицензий в системе**

**Объяснение/Действие:**  
Интерфейс Qtech запустился и доступен, но появилась проблема с лицензированием. Сообщение говорит, что осталась лицензия только на 1 портал. 

Для диагностики нужно проверить:
1. Где хранятся лицензии в системе (обычно это файлы или записи в базе данных)
2. Не сбросились ли лицензии при перезапуске контейнеров

Сначала давайте проверим, есть ли в конфигурации проекта файлы или переменные, связанные с лицензиями. Выполните команду:
```bash
cd /opt/wimark/one && find . -type f -name "*license*" -o -name "*lic*" 2>/dev/null | head -20
```

**Протокол:**  
- Qtech доступен через веб-интерфейс
- Появилась ошибка: осталось лицензий только на 1 портал вместо ожидаемого количества
- Необходимо найти, где хранятся лицензионные данные

**Вопросы:**  
Какой вывод даст эта команда? Это поможет определить расположение лицензионных файлов.

### USER
Пусто

### ASSISTANT
**Шаг 2 — Поиск лицензий в переменных окружения и конфигурации**

**Объяснение/Действие:**  
Файлы с явным указанием "license" в имени не найдены. Лицензии могут храниться:
- В переменных окружения (в docker-compose.yml или .env файле)
- В базе данных (MongoDB/Redis)
- В конфигурационных файлах с другими именами

Проверим наличие .env файла и переменных, связанных с лицензиями. Выполните команды:
```bash
cd /opt/wimark/one && ls -la .env* 2>/dev/null
```
и
```bash
cd /opt/wimark/one && grep -i "licen" docker-compose.yml .env* 2>/dev/null | head -20
```

**Протокол:**  
- Поиск файлов с "license" в имени не дал результатов
- Лицензии, вероятно, хранятся в другом месте (переменные окружения, БД)
- Нужно проверить конфигурационные файлы проекта

**Вопросы:**  
Какой вывод дали эти команды?

### USER
 cd /opt/wimark/one && ls -la .env* 2>/dev/null
-rw------- 1 root root 455 ноя 12  2025 .env
root@wmswifi:/opt/wimark/one#
# cd /opt/wimark/one && grep -i "licen" docker-compose.yml .env* 2>/dev/null | head -20
root@wmswifi:/opt/wimark/one#

### ASSISTANT
**Шаг 3 — Изучение содержимого файла .env**

**Объяснение/Действие:**  
Поиск по слову "licen" не дал результатов, но файл `.env` существует. Нужно посмотреть его полное содержимое, чтобы понять, какие параметры окружения передаются в контейнеры. Возможно, лимит порталов задается переменной с другим названием, или там указан ключ лицензии.

Выполните команду:
```bash
cat /opt/wimark/one/.env
```

**Протокол:**  
- Файл `.env` найден, но поиск по слову "licen" в нем и в `docker-compose.yml` ничего не дал.  
- Лицензии не хранятся в явном виде в конфигурационных файлах Docker.  
- Необходимо изучить все переменные окружения проекта.

**Вопросы:**  
Какой точный вывод даст эта команда? Жду вашего ответа.

### USER
root@wmswifi:/opt/wimark/one# cat /opt/wimark/one/.env
HOSTNAME=one
SERVERNAME=wmswifi
WIMARK_DIR=/opt/wimark
DB_ADDR=mongodb://mongo
LOGLEVEL=0
LOG_LEVEL=0
MODE=sa
IPSEC_IP=10.9.0.1
LOCAL_IP=172.17.0.1
NAME=ONE
PRODUCT=one
VERSION_ID=1.14.2
VERSION_NAME="Zipped Zima"
VERSION="1.14.2 (Zipped Zima)"
BUILD_DATE="2025-08-05"
BRAND=qtech
BUNDLE=pro
COMMIT_TIME=2025-08-05T16:40:57+00:00
COMMIT_HASH=1d82e1c0bd03f834b919f18f7f3b0f1f33d58a37
HOME_URL=https://wimark.com/
BUG_REPORT_URL=https://support.wimark.com/
root@wmswifi:/opt/wimark/one#

### ASSISTANT
**Шаг 4 — Поиск лицензионных файлов в корневой директории Wimark**

**Объяснение/Действие:**  
В файле `.env` нет явных переменных, отвечающих за количество лицензий или ключи (есть только `BRAND=qtech` и `BUNDLE=pro`). В системах Wimark ONE лицензии часто хранятся не в директории проекта `/opt/wimark/one`, а в общей директории `/opt/wimark/` или в базе данных MongoDB.

Чтобы найти, где физически лежат файлы лицензий, проверим содержимое родительской директории `/opt/wimark/`. 

Выполните на сервере следующие команды:
```bash
ls -la /opt/wimark/
```
и
```bash
find /opt/wimark -maxdepth 3 -iname "*licen*" 2>/dev/null
```

**Протокол:**  
- Файл `.env` проверен, переменных с лицензиями или их лимитами в нем нет.  
- Поиск внутри `/opt/wimark/one` ранее не дал результатов.  
- Необходимо расширить область поиска на общую директорию `/opt/wimark/`, где могут храниться системные файлы лицензий.

**Вопросы:**  
Какой вывод дали эти две команды?

### USER
root@wmswifi:/opt/wimark/one# ls -la /opt/wimark/
total 44
drwxr-xr-x  9 ollama input 4096 ноя 12  2025 .
drwxr-xr-x 13 ollama input 4096 июл 10 21:12 ..
drwxr-xr-x 18 ollama input 4096 июн 30 19:04 etc
-rw-------  1 root   root  2319 ноя 12  2025 .install.lock.last
drwx------  3 root   root  4096 ноя 12  2025 logs
drwxr-xr-x  4 ollama input 4096 авг  5  2025 nms
drwx------  4 root   root  4096 июл 17 19:56 one
drwxr-xr-x  5 ollama input 4096 авг  5  2025 portal
drwxrwxrwx  5 one    one   4096 ноя 12  2025 static
drwxr-xr-x  9 root   root  4096 июн 30 19:04 volumes
-rw-------  1 root   root  2409 ноя 12  2025 wimark.log
root@wmswifi:/opt/wimark/one# find /opt/wimark -maxdepth 3 -iname "*licen*" 2>/dev/null
root@wmswifi:/opt/wimark/one#

### ASSISTANT
**Шаг 5 — Поиск лицензионных данных в системных директориях и базе данных**

**Объяснение/Действие:**  
Поиск файлов с словом "licen" на глубине до 3 уровней не дал результатов. В архитектуре Wimark ONE лицензии часто хранятся либо в специфических конфигурационных файлах внутри `/opt/wimark/etc/`, либо непосредственно в базе данных MongoDB.

Давайте сначала проверим содержимое директории `/opt/wimark/etc/`, так как там обычно лежат системные конфиги и возможные ключи. Выполните команду:
```bash
ls -la /opt/wimark/etc/
```

**Протокол:**  
- Поиск файлов с "licen" в `/opt/wimark` (до 3 уровня вложенности) не дал результатов.  
- В `.env` переменных, отвечающих за лимит порталов, нет.  
- Необходимо проверить директорию `/opt/wimark/etc/` на наличие конфигурационных или лицензионных файлов.

**Вопросы:**  
Какой вывод даст эта команда? Жду вашего ответа.

### USER

drwxr-xr-x 18 ollama input 4096 июн 30 19:04 .
drwxr-xr-x  9 ollama input 4096 ноя 12  2025 ..
drwxr-xr-x  2 ollama input 4096 ноя 12  2025 backend-golang
drwxr-xr-x  2 ollama input 4096 ноя 12  2025 configurer-golang
drwxr-xr-x  2 ollama input 4096 ноя 12  2025 event-monitor-golang
drwxr-xr-x  2 ollama input 4096 ноя 12  2025 gauth-service
drwxr-xr-x  2 ollama input 4096 ноя 12  2025 glanguage-service
drwxr-xr-x  3 ollama input 4096 ноя 12  2025 gproxy-service
drwxr-xr-x  2 ollama input 4096 ноя 12  2025 keepalived
drwxr-xr-x  2 ollama input 4096 ноя 12  2025 loki
drwxr-xr-x  2 ollama input 4096 ноя 12  2025 lsyncd
drwxr-xr-x  2 ollama input 4096 ноя 12  2025 network
drwxr-xr-x  2 ollama input 4096 июн 30 15:51 nginx-proxy-ssl
drwxr-xr-x  2 root   root  4096 июн 30 19:04 nginx-proxy-ssl.backup
drwxr-xr-x  2 ollama input 4096 ноя 12  2025 promtail
drwxr-xr-x  2 ollama input 4096 ноя 12  2025 redirect-daemon
drwxr-xr-x  2 ollama input 4096 ноя 12  2025 rsyslog
drwxr-xr-x  3 ollama input 4096 ноя 12  2025 strongswan


### ASSISTANT
**Шаг 6 — Поиск лицензионных файлов с другими расширениями и проверка томов**

**Объяснение/Действие:**  
В директории `/opt/wimark/etc/` нет явных файлов с названием, содержащим "licen". В системах Wimark ONE лицензии иногда хранятся в виде файлов с расширениями `.lic` или `.key`, либо непосредственно в базе данных MongoDB, либо в persistent-томах Docker.

Давайте расширим поиск по расширениям и проверим содержимое директории `volumes`, где хранятся постоянные данные. Выполните на сервере следующие команды:
```bash
find /opt/wimark -type f \( -name "*.lic" -o -name "*.key" \) 2>/dev/null
```
и
```bash
ls -la /opt/wimark/volumes/
```

**Протокол:**  
- Директория `/opt/wimark/etc/` проверена, явных файлов лицензий с таким именем нет.  
- Необходимо искать файлы с расширениями `.lic` или `.key`, а также проверить persistent-тома Docker.

**Вопросы:**  
Какой вывод дали эти две команды? Жду вашего ответа.

### USER
i:/opt/wimark# find /opt/wimark -type f \( -name "*.lic" -o -name "*.key" \) 2>/dev/null
/opt/wimark/portal/esia-auth/certs/key.key
root@wmswifi:/opt/wimark# ls -la /opt/wimark/volumes/
total 36
drwxr-xr-x 9 root   root  4096 июн 30 19:04 .
drwxr-xr-x 9 ollama input 4096 ноя 12  2025 ..
drwxr-xr-x 7 root   root  4096 июл 17 20:41 cert
drwxr-xr-x 7 root   root  4096 июн 30 19:05 cert.backup
drwxr-xr-x 3 root   root  4096 ноя 12  2025 redis
drwxr-xr-x 3 root   root  4096 ноя 12  2025 rsyslog
drwxr-xr-x 2 root   root  4096 дек  1  2025 strongswan
drwxr-xr-x 2 root   root  4096 ноя 12  2025 trash
drwxr-xr-x 2 root   root  4096 ноя 12  2025 troubleshooting
root@wmswifi:/opt/wimark#

### ASSISTANT
**Шаг 7 — Проверка баз данных MongoDB на наличие лицензий**

**Объяснение/Действие:**  
Файлов `.lic` или `.key` на файловой системе не найдено (найден только ключ для ESIA), и в конфигурационных файлах (`docker-compose.yml`, `.env`) упоминаний лицензий нет. В архитектуре Wimark ONE данные о лицензиях, включая лимит на количество порталов, хранятся непосредственно в базе данных MongoDB. 

Нам нужно подключиться к контейнеру `one-mongo-1` и посмотреть список баз данных, чтобы найти ту, где хранятся настройки лицензии.

Выполните на сервере следующую команду (она попробует использовать новый `mongosh`, а если его нет — старый `mongo`):
```bash
docker exec one-mongo-1 sh -c 'mongosh --quiet --eval "show dbs" || mongo --quiet --eval "show dbs"'
```

**Протокол:**  
- Поиск файлов лицензий на диске не дал результатов.  
- В `docker-compose.yml` и `.env` параметры лицензий отсутствуют.  
- Лицензии и их лимиты, вероятнее всего, записаны в MongoDB.  

**Вопросы:**  
Какой вывод даст эта команда? Жду вашего ответа.

### USER
imark/portal/esia-auth/certs# docker exec one-mongo-1 sh -c 'mongosh --quiet --eval "show dbs" || mongo --quiet --eval "show dbs"'
admin   40.00 KiB
config  36.00 KiB
local   72.00 KiB
test    22.87 MiB
root@wmswifi:/opt/wimark/portal/esia-auth/certs#

### ASSISTANT
**Шаг 8 — Проверка коллекций в базе данных `test`**

**Объяснение/Действие:**  
Вывод команды показал только системные базы данных (`admin`, `config`, `local`) и базу `test`. Стандартных баз приложения (например, `wimark`, `one`, `portal`) в списке нет. Это нестандартная ситуация, но так как интерфейс работает и отображает устройства, данные где-то хранятся. База `test` имеет размер 22.87 MiB, что указывает на наличие в ней прикладных данных.

Нам нужно посмотреть, какие коллекции (таблицы) находятся в базе `test`, чтобы найти ту, где могут храниться настройки лицензий или порталов.

Выполните на сервере следующую команду:
```bash
docker exec one-mongo-1 sh -c 'mongosh --quiet test --eval "show collections" || mongo --quiet test --eval "show collections"'
```

**Протокол:**  
- Команда `show dbs` не показала специализированных баз данных приложения.  
- Единственная пользовательская база с данными — `test` (22.87 MiB).  
- Необходимо изучить её содержимое для поиска лицензионной информации.

**Вопросы:**  
Какой вывод даст эта команда? Жду вашего ответа.

### USER

root@wmswifi:/opt/wimark/portal/esia-auth/certs# docker exec one-mongo-1 sh -c 'mongosh --quiet test --eval "show collections" || mongo --quiet test --eval "show collections"'
base_location
bss_stat_info
client_addr
client_session_info
client_stat_info
client_stats
clients
config_rule
countries
cpe_model
cpe_scan_data
cpe_session_info
cpe_stat_info
cpes
events
lbs_client_coords
lbs_client_data
lbs_client_probes
lbs_client_probes_testing
lbs_cpe_info
lbs_zones
license_log_daily
location
ntp_time_settings
operation
poll_cpe
portal_authorizations
radar_export_result
radar_probes_raw
radar_probes_real
radar_visits
radar_visits_first
redirect_sessions
snmp_general
snmp_point_state
snmp_walker
stats
troubleshooting
user
vpn_host
wlan_stat_info
wlans
wne_license_key
root@wmswifi:/opt/wimark/portal/esia-auth/certs#

### ASSISTANT
**Шаг 9 — Просмотр данных в коллекции `wne_license_key`**

**Объяснение/Действие:**  
В выводе списка коллекций мы видим две явно связанные с лицензиями таблицы: `license_log_daily` и `wne_license_key`. Коллекция `wne_license_key` (Wimark Network Equipment License Key), вероятнее всего, содержит сам ключ лицензии и ограничения на количество порталов. 

Нам нужно посмотреть, какие документы хранятся в этой коллекции. Выполните на сервере следующую команду:
```bash
docker exec one-mongo-1 sh -c 'mongosh --quiet test --eval "db.wne_license_key.find()" || mongo --quiet test --eval "db.wne_license_key.find()"'
```

**Протокол:**  
- База данных `test` содержит прикладные данные системы.  
- Найдены коллекции `license_log_daily` и `wne_license_key`, отвечающие за лицензирование.  
- Текущий фокус: получение содержимого коллекции `wne_license_key` для анализа лимитов.

**Вопросы:**  
Какой точный вывод даст эта команда? Жду вашего ответа.

### USER
/wimark/portal/esia-auth/certs# docker exec one-mongo-1 sh -c 'mongosh --quiet test --eval "db.wne_license_key.find()" || mongo --quiet test --eval "db.wne_license_key.find()"'
[
  {
    _id: 'wimark_license_key',
    key: 'DuaRW5B6IFlmCkVkqRKZOcCE+hJadD04UDu2a3EqDKXZiznAcYAaS26/cMsjIszq7+9hhqgqHgmDgFJ/x1tRLD4irtqeNB3CqX/r9Z9hMVM2jzl2MMH5Cjg3qwjMUE3vU1ZVyekQwAmspZn5LHEFhrI5b0+a7xFEelkw2rOcOBMWdsCI7KR6DlbnFHOuElXCkHIc7qW0BGsd9LxSTWgkrjLx+vrYiRfZnXllPArc3ZczKg+95nXKfSE9EDkrYQw7NCH//3R+tTXyY71/0kXldYvPvklbLu5wjp4PMBvEUAEaAc714sz0OsQ2Ms4hjbREER4fvkQCzMqS7HE/gX+ukw=='
  }
]
root@wmswifi:/opt/wimark/portal/esia-auth/certs#

### ASSISTANT
**Шаг 10 — Проверка журнала использования лицензий**

**Объяснение/Действие:**  
Мы нашли зашифрованный ключ лицензии в коллекции `wne_license_key`. Сам по себе этот текст не показывает количество доступных порталов, так как он расшифровывается и проверяется на стороне приложения Wimark. 

Однако в базе данных присутствует коллекция `license_log_daily`, которая, вероятнее всего, ведет журнал ежедневного использования, активации или списания лицензий. Проверка этой коллекции поможет понять, были ли лицензии ранее активны в полном объеме и куда они могли "деться" (например, истек срок действия, изменился аппаратный ключ сервера или лицензии были привязаны к другим сущностям).

Выполните на сервере следующую команду, чтобы посмотреть последние 10 записей в этом журнале:
```bash
docker exec one-mongo-1 sh -c 'mongosh --quiet test --eval "db.license_log_daily.find().sort({date: -1}).limit(10).toArray()" || mongo --quiet test --eval "db.license_log_daily.find().sort({date: -1}).limit(10).toArray()"'
```

**Протокол:**  
- Обнаружена коллекция `wne_license_key` с зашифрованным ключом лицензии.  
- Прямое чтение ключа не дает информации о лимите порталов.  
- Для выяснения причины исчезновения лицензий необходимо проанализировать журнал `license_log_daily`.

**Вопросы:**  
Какой точный вывод даст эта команда? Жду вашего ответа.

### USER
 || mongo --quiet test --eval "db.license_log_daily.find().sort({date: -1}).limit(10).toArray()"'
[
  {
    _id: '2025-11-27',
    cpe: 0,
    cpe_connected: 0,
    radar: 0,
    radar_connected: 0,
    heatmap: 0,
    cpe_connected_ids: [],
    radar_connected_ids: [],
    heatmap_ids: [],
    create: ISODate('2025-11-27T06:16:42.201Z'),
    create_at: Long('1764224202')
  },
  {
    _id: '2025-11-28',
    cpe: 8,
    cpe_connected: 7,
    radar: 0,
    radar_connected: 0,
    heatmap: 0,
    cpe_connected_ids: [
      '4174f9dd-648f-0785-6640-08c6b3fbee64',
      '4174f9dd-648f-0785-6640-08c6b3fbf09e',
      '4174f9dd-648f-0785-6640-08c6b3fbed08',
      '4174f9dd-648f-0785-6640-08c6b3fbed14',
      '4174f9dd-648f-0785-6640-08c6b3fbed77',
      '4174f9dd-648f-0785-6640-08c6b3fbef60',
      '4174f9dd-648f-0785-6640-08c6b3fbee91'
    ],
    radar_connected_ids: [],
    heatmap_ids: [],
    create: ISODate('2025-11-28T10:47:46.860Z'),
    create_at: Long('1764326866')
  },
  {
    _id: '2025-11-16',
    cpe: 0,
    cpe_connected: 0,
    radar: 0,
    radar_connected: 0,
    heatmap: 0,
    cpe_connected_ids: [],
    radar_connected_ids: [],
    heatmap_ids: [],
    create: ISODate('2025-11-16T14:58:32.385Z'),
    create_at: Long('1763305112')
  },
  {
    _id: '2025-11-26',
    cpe: 0,
    cpe_connected: 0,
    radar: 0,
    radar_connected: 0,
    heatmap: 0,
    cpe_connected_ids: [],
    radar_connected_ids: [],
    heatmap_ids: [],
    create: ISODate('2025-11-26T11:49:01.593Z'),
    create_at: Long('1764157741')
  },
  {
    _id: '2025-11-17',
    cpe: 0,
    cpe_connected: 0,
    radar: 0,
    radar_connected: 0,
    heatmap: 0,
    cpe_connected_ids: [],
    radar_connected_ids: [],
    heatmap_ids: [],
    create: ISODate('2025-11-17T14:58:32.387Z'),
    create_at: Long('1763391512')
  },
  {
    _id: '2025-11-15',
    cpe: 0,
    cpe_connected: 0,
    radar: 0,
    radar_connected: 0,
    heatmap: 0,
    cpe_connected_ids: [],
    radar_connected_ids: [],
    heatmap_ids: [],
    create: ISODate('2025-11-15T14:58:32.382Z'),
    create_at: Long('1763218712')
  },
  {
    _id: '2025-11-13',
    cpe: 0,
    cpe_connected: 0,
    radar: 0,
    radar_connected: 0,
    heatmap: 0,
    cpe_connected_ids: [],
    radar_connected_ids: [],
    heatmap_ids: [],
    create: ISODate('2025-11-13T14:58:32.377Z'),
    create_at: Long('1763045912')
  },
  {
    _id: '2025-11-12',
    cpe: 0,
    cpe_connected: 0,
    radar: 0,
    radar_connected: 0,
    heatmap: 0,
    cpe_connected_ids: [],
    radar_connected_ids: [],
    heatmap_ids: [],
    create: ISODate('2025-11-12T14:58:32.308Z'),
    create_at: Long('1762959512')
  },
  {
    _id: '2025-11-14',
    cpe: 0,
    cpe_connected: 0,
    radar: 0,
    radar_connected: 0,
    heatmap: 0,
    cpe_connected_ids: [],
    radar_connected_ids: [],
    heatmap_ids: [],
    create: ISODate('2025-11-14T14:58:32.380Z'),
    create_at: Long('1763132312')
  },
  {
    _id: '2025-11-25',
    cpe: 0,
    cpe_connected: 0,
    radar: 0,
    radar_connected: 0,
    heatmap: 0,
    cpe_connected_ids: [],
    radar_connected_ids: [],
    heatmap_ids: [],
    create: ISODate('2025-11-25T12:06:56.823Z'),
    create_at: Long('1764072416')
  }
]


### ASSISTANT
**Шаг 11 — Проверка логов бэкенда на ошибки валидации лицензии**

**Объяснение/Действие:**  
Журнал `license_log_daily` показывает статистику использования (например, 28 ноября было зафиксировано 8 CPE), но не объясняет, почему система утверждает, что доступна лицензия только на 1 портал.  

В архитектуре Wimark такое ограничение часто возникает, если ключ лицензии (который мы нашли в коллекции `wne_license_key`) не проходит внутреннюю валидацию. Возможные причины: изменение аппаратного идентификатора сервера (например, MAC-адреса виртуальной машины), истечение срока действия ключа или сбой при его расшифровке. В таких случаях система автоматически откатывается к базовому (демо) лимиту — 1 портал.

Чтобы понять точную причину, нам нужно посмотреть, какие сообщения о лицензии генерирует основной бэкенд при своей работе.

Выполните на сервере следующие команды:
```bash
docker logs one-backend-golang-1 2>&1 | grep -iE "license|portal" | tail -20
```
и
```bash
docker logs one-portal-backend-1 2>&1 | grep -iE "license|portal" | tail -20
```

**Протокол:**  
- Коллекция `license_log_daily` содержит историческую статистику, но не сами лимиты.  
- Ключ лицензии физически присутствует в базе данных, но система ведет себя так, будто он недействителен или урезан.  
- Текущий фокус: выявление ошибок валидации лицензии в логах сервисов.

**Вопросы:**  
Какой вывод дали эти две команды? Жду вашего ответа.

### USER
 docker logs one-backend-golang-1 2>&1 | grep -iE "license|portal" | tail -20
{"level":"debug","module":"BACKEND","request_id":"01cdce1b-1b28-476e-81c0-3e73a0c35e25","func_name":"ValidateAccessPortal","time":"2026-07-17T20:33:45Z","message":"[ValidateAccessPortal] path: /portal-admin/api/total_cost method: GET"}
{"level":"debug","module":"BACKEND","request_id":"01cdce1b-1b28-476e-81c0-3e73a0c35e25","func_name":"ValidateAccessPortal","time":"2026-07-17T20:33:45Z","message":"[ValidateAccessPortal] profiles: [] db: []"}
{"level":"debug","module":"BACKEND","request_id":"01cdce1b-1b28-476e-81c0-3e73a0c35e25","func_name":"ValidateAccessPortal","time":"2026-07-17T20:33:45Z","message":"[LogLatency] Func: ValidateAccessPortal /portal-admin/api/total_cost. Time: 543.408µs"}
{"level":"debug","module":"BACKEND","request_id":"66683ccb-47e7-483e-b85e-c304c0ddd183","func_name":"ValidateAccessPortal","time":"2026-07-17T20:33:45Z","message":"[ValidateAccessPortal] path: /portal-admin/api/range method: GET"}
{"level":"debug","module":"BACKEND","request_id":"66683ccb-47e7-483e-b85e-c304c0ddd183","func_name":"ValidateAccessPortal","time":"2026-07-17T20:33:45Z","message":"[ValidateAccessPortal] profiles: [] db: []"}
{"level":"debug","module":"BACKEND","request_id":"66683ccb-47e7-483e-b85e-c304c0ddd183","func_name":"ValidateAccessPortal","time":"2026-07-17T20:33:45Z","message":"[LogLatency] Func: ValidateAccessPortal /portal-admin/api/range. Time: 634.181µs"}
{"level":"debug","module":"BACKEND","request_id":"0680b2ac-9b42-468a-a966-cd27b156af89","func_name":"ValidateAccessPortal","time":"2026-07-17T20:33:45Z","message":"[ValidateAccessPortal] validation portal path: /portal-admin/api/total_cost"}
{"level":"debug","module":"BACKEND","request_id":"0680b2ac-9b42-468a-a966-cd27b156af89","func_name":"ValidateAccessPortal","time":"2026-07-17T20:33:45Z","message":"[ValidateAccessPortal] access control via profiles: /portal-admin/api/total_cost"}
{"level":"debug","module":"BACKEND","request_id":"0680b2ac-9b42-468a-a966-cd27b156af89","func_name":"ValidateAccessPortal","time":"2026-07-17T20:33:45Z","message":"[ValidateAccessPortal] path: /portal-admin/api/total_cost method: GET"}
{"level":"debug","module":"BACKEND","request_id":"0680b2ac-9b42-468a-a966-cd27b156af89","func_name":"ValidateAccessPortal","time":"2026-07-17T20:33:45Z","message":"[ValidateAccessPortal] profiles: [] db: []"}
{"level":"debug","module":"BACKEND","request_id":"0680b2ac-9b42-468a-a966-cd27b156af89","func_name":"ValidateAccessPortal","time":"2026-07-17T20:33:45Z","message":"[LogLatency] Func: ValidateAccessPortal /portal-admin/api/total_cost. Time: 654.627µs"}
{"level":"info","module":"BACKEND","request_id":"592deb3b-8cb0-4f43-9e63-86952d9e99c9","method":"GET","uri":"/api/portal/admin/range?start=1783630800&stop=1784321999&object=timeseries&subtype=os&with_childs=true","status":200,"latency":0.875336,"time":"2026-07-17T20:33:45Z","message":"request handled"}
{"level":"info","module":"BACKEND","request_id":"66683ccb-47e7-483e-b85e-c304c0ddd183","method":"GET","uri":"/api/portal/admin/range?start=1783630800&stop=1784321999&object=pie&subtype=os&with_childs=true","status":200,"latency":1.275646,"time":"2026-07-17T20:33:45Z","message":"request handled"}
{"level":"info","module":"BACKEND","request_id":"01cdce1b-1b28-476e-81c0-3e73a0c35e25","method":"GET","uri":"/api/portal/admin/total_cost?start=1783630800&stop=1784321999&with_childs=true","status":200,"latency":1.650274,"time":"2026-07-17T20:33:45Z","message":"request handled"}
{"level":"info","module":"BACKEND","request_id":"0680b2ac-9b42-468a-a966-cd27b156af89","method":"GET","uri":"/api/portal/admin/total_cost?start=1783026000&stop=1783630799&with_childs=true","status":200,"latency":2.357519,"time":"2026-07-17T20:33:45Z","message":"request handled"}
{"level":"debug","module":"BACKEND","request_id":"6abb679f-9dd0-4de5-ab93-3513a4de17f0","func_name":"ValidateAccessPortal","time":"2026-07-17T20:33:50Z","message":"[ValidateAccessPortal] validation portal path: /portal-admin/api/webpage"}
{"level":"debug","module":"BACKEND","request_id":"6abb679f-9dd0-4de5-ab93-3513a4de17f0","func_name":"ValidateAccessPortal","time":"2026-07-17T20:33:50Z","message":"[ValidateAccessPortal] path: /portal-admin/api/webpage method: GET"}
{"level":"debug","module":"BACKEND","request_id":"6abb679f-9dd0-4de5-ab93-3513a4de17f0","func_name":"ValidateAccessPortal","time":"2026-07-17T20:33:50Z","message":"[ValidateAccessPortal] locIds: [] db: []"}
{"level":"debug","module":"BACKEND","request_id":"6abb679f-9dd0-4de5-ab93-3513a4de17f0","func_name":"ValidateAccessPortal","time":"2026-07-17T20:33:50Z","message":"[LogLatency] Func: ValidateAccessPortal /portal-admin/api/webpage. Time: 789.475µs"}
{"level":"info","module":"BACKEND","request_id":"6abb679f-9dd0-4de5-ab93-3513a4de17f0","method":"GET","uri":"/api/portal/admin/webpage?limit=30&offset=0&sort=name&with_childs=true","status":200,"latency":2.572206,"time":"2026-07-17T20:33:50Z","message":"request handled"}
root@wmswifi:/opt/wimark/portal/esia-auth/certs# docker logs one-portal-backend-1 2>&1 | grep -iE "license|portal" | tail -20
{"timestamp":"2026-06-16T04:59:08.992783519Z","level":"DEBUG","message":"Environment config: \n{MongoAddr:mongodb://mongo MongoTimeout:20s RedisAddr:redis:6379 ServerAddr::1325 CabinetAddr::3334 SessionStepTimeout:240 AuthenType:email PrivateCabAuth:callback SessionAuthTimeout:3600 SmsGateway:http://sendmail:1001/api/sendmail?to={PHONE}\u0026from=guest@wimark.com\u0026subject=Authorization\u0026body=Code:%20{MESSAGE} CountryCode:7 PhoneDefCodes:[] AuthenTypes:[email] AuthenGWs:[http://sendmail:1001/api/sendmail?to={PHONE}\u0026from=guest@wimark.com\u0026subject=Authorization\u0026body=Code:%20{MESSAGE}] GWs:map[email:http://sendmail:1001/api/sendmail?to={PHONE}\u0026from=guest@wimark.com\u0026subject=Authorization\u0026body=Code:%20{MESSAGE}] AuthType:email SessionTimeout:300 SessionBlockTimeout:0 SwitchURL:http://redirect-daemon:1324/api/authorize RedirectURL:http://wimark.com ContentDir:/content VoucherGateway:http://sendmail:1001/api/sendmail?to={PHONE}\u0026from=guest@wimark.com\u0026subject=Authorization\u0026body=Code:%20{MESSAGE} PaymentSystems:map[] PaymentNames:[] PaymentGateway:[] ServeAddr::13255 PaymentServeAddr: HumoHashTmpl:phone=\u003cphone\u003e\u0026merchant_id=1\u0026amount=\u003camount\u003e HumoHashKey:test EnableSMSRuFrontCall:true CNATimeout:120 RadiusServeAddr::8081 Debug:false PhoneCC:992 BillingProviders:{Host: Port: Login: Password: TestMode:false Vendor: SrlsID: TimeOut:0}}\n","service":"PORTAL_BACKEND","src_file":"main.go","src_line":121}
{"timestamp":"2026-06-16T04:59:12.084157669Z","level":"INFO","message":"Connected to Mongo with address: mongodb://mongo","service":"PORTAL_BACKEND","src_file":"main.go","src_line":134}
{"timestamp":"2026-06-16T05:03:42.007279634Z","level":"INFO","message":"Version of daemon is: v1.9.6, builded: 2025-02-05T09:37:13Z, hash: abcecd1f","service":"PORTAL_BACKEND","src_file":"main.go","src_line":120}
{"timestamp":"2026-06-16T05:03:42.007932934Z","level":"DEBUG","message":"Environment config: \n{MongoAddr:mongodb://mongo MongoTimeout:20s RedisAddr:redis:6379 ServerAddr::1325 CabinetAddr::3334 SessionStepTimeout:240 AuthenType:email PrivateCabAuth:callback SessionAuthTimeout:3600 SmsGateway:http://sendmail:1001/api/sendmail?to={PHONE}\u0026from=guest@wimark.com\u0026subject=Authorization\u0026body=Code:%20{MESSAGE} CountryCode:7 PhoneDefCodes:[] AuthenTypes:[email] AuthenGWs:[http://sendmail:1001/api/sendmail?to={PHONE}\u0026from=guest@wimark.com\u0026subject=Authorization\u0026body=Code:%20{MESSAGE}] GWs:map[email:http://sendmail:1001/api/sendmail?to={PHONE}\u0026from=guest@wimark.com\u0026subject=Authorization\u0026body=Code:%20{MESSAGE}] AuthType:email SessionTimeout:300 SessionBlockTimeout:0 SwitchURL:http://redirect-daemon:1324/api/authorize RedirectURL:http://wimark.com ContentDir:/content VoucherGateway:http://sendmail:1001/api/sendmail?to={PHONE}\u0026from=guest@wimark.com\u0026subject=Authorization\u0026body=Code:%20{MESSAGE} PaymentSystems:map[] PaymentNames:[] PaymentGateway:[] ServeAddr::13255 PaymentServeAddr: HumoHashTmpl:phone=\u003cphone\u003e\u0026merchant_id=1\u0026amount=\u003camount\u003e HumoHashKey:test EnableSMSRuFrontCall:true CNATimeout:120 RadiusServeAddr::8081 Debug:false PhoneCC:992 BillingProviders:{Host: Port: Login: Password: TestMode:false Vendor: SrlsID: TimeOut:0}}\n","service":"PORTAL_BACKEND","src_file":"main.go","src_line":121}
{"timestamp":"2026-06-16T05:03:43.045706228Z","level":"INFO","message":"Connected to Mongo with address: mongodb://mongo","service":"PORTAL_BACKEND","src_file":"main.go","src_line":134}
{"timestamp":"2026-06-20T02:25:46.347913998Z","level":"INFO","message":"Version of daemon is: v1.9.6, builded: 2025-02-05T09:37:13Z, hash: abcecd1f","service":"PORTAL_BACKEND","src_file":"main.go","src_line":120}
{"timestamp":"2026-06-20T02:25:46.349065856Z","level":"DEBUG","message":"Environment config: \n{MongoAddr:mongodb://mongo MongoTimeout:20s RedisAddr:redis:6379 ServerAddr::1325 CabinetAddr::3334 SessionStepTimeout:240 AuthenType:email PrivateCabAuth:callback SessionAuthTimeout:3600 SmsGateway:http://sendmail:1001/api/sendmail?to={PHONE}\u0026from=guest@wimark.com\u0026subject=Authorization\u0026body=Code:%20{MESSAGE} CountryCode:7 PhoneDefCodes:[] AuthenTypes:[email] AuthenGWs:[http://sendmail:1001/api/sendmail?to={PHONE}\u0026from=guest@wimark.com\u0026subject=Authorization\u0026body=Code:%20{MESSAGE}] GWs:map[email:http://sendmail:1001/api/sendmail?to={PHONE}\u0026from=guest@wimark.com\u0026subject=Authorization\u0026body=Code:%20{MESSAGE}] AuthType:email SessionTimeout:300 SessionBlockTimeout:0 SwitchURL:http://redirect-daemon:1324/api/authorize RedirectURL:http://wimark.com ContentDir:/content VoucherGateway:http://sendmail:1001/api/sendmail?to={PHONE}\u0026from=guest@wimark.com\u0026subject=Authorization\u0026body=Code:%20{MESSAGE} PaymentSystems:map[] PaymentNames:[] PaymentGateway:[] ServeAddr::13255 PaymentServeAddr: HumoHashTmpl:phone=\u003cphone\u003e\u0026merchant_id=1\u0026amount=\u003camount\u003e HumoHashKey:test EnableSMSRuFrontCall:true CNATimeout:120 RadiusServeAddr::8081 Debug:false PhoneCC:992 BillingProviders:{Host: Port: Login: Password: TestMode:false Vendor: SrlsID: TimeOut:0}}\n","service":"PORTAL_BACKEND","src_file":"main.go","src_line":121}
{"timestamp":"2026-06-20T02:25:49.03959328Z","level":"INFO","message":"Connected to Mongo with address: mongodb://mongo","service":"PORTAL_BACKEND","src_file":"main.go","src_line":134}
{"timestamp":"2026-06-24T10:22:24.777177989Z","level":"INFO","message":"Version of daemon is: v1.9.6, builded: 2025-02-05T09:37:13Z, hash: abcecd1f","service":"PORTAL_BACKEND","src_file":"main.go","src_line":120}
{"timestamp":"2026-06-24T10:22:24.777577368Z","level":"DEBUG","message":"Environment config: \n{MongoAddr:mongodb://mongo MongoTimeout:20s RedisAddr:redis:6379 ServerAddr::1325 CabinetAddr::3334 SessionStepTimeout:240 AuthenType:email PrivateCabAuth:callback SessionAuthTimeout:3600 SmsGateway:http://sendmail:1001/api/sendmail?to={PHONE}\u0026from=guest@wimark.com\u0026subject=Authorization\u0026body=Code:%20{MESSAGE} CountryCode:7 PhoneDefCodes:[] AuthenTypes:[email] AuthenGWs:[http://sendmail:1001/api/sendmail?to={PHONE}\u0026from=guest@wimark.com\u0026subject=Authorization\u0026body=Code:%20{MESSAGE}] GWs:map[email:http://sendmail:1001/api/sendmail?to={PHONE}\u0026from=guest@wimark.com\u0026subject=Authorization\u0026body=Code:%20{MESSAGE}] AuthType:email SessionTimeout:300 SessionBlockTimeout:0 SwitchURL:http://redirect-daemon:1324/api/authorize RedirectURL:http://wimark.com ContentDir:/content VoucherGateway:http://sendmail:1001/api/sendmail?to={PHONE}\u0026from=guest@wimark.com\u0026subject=Authorization\u0026body=Code:%20{MESSAGE} PaymentSystems:map[] PaymentNames:[] PaymentGateway:[] ServeAddr::13255 PaymentServeAddr: HumoHashTmpl:phone=\u003cphone\u003e\u0026merchant_id=1\u0026amount=\u003camount\u003e HumoHashKey:test EnableSMSRuFrontCall:true CNATimeout:120 RadiusServeAddr::8081 Debug:false PhoneCC:992 BillingProviders:{Host: Port: Login: Password: TestMode:false Vendor: SrlsID: TimeOut:0}}\n","service":"PORTAL_BACKEND","src_file":"main.go","src_line":121}
{"timestamp":"2026-06-24T10:22:26.817185235Z","level":"INFO","message":"Connected to Mongo with address: mongodb://mongo","service":"PORTAL_BACKEND","src_file":"main.go","src_line":134}
{"timestamp":"2026-06-25T17:57:46.168346105Z","level":"INFO","message":"Version of daemon is: v1.9.6, builded: 2025-02-05T09:37:13Z, hash: abcecd1f","service":"PORTAL_BACKEND","src_file":"main.go","src_line":120}
{"timestamp":"2026-06-25T17:57:46.17025702Z","level":"DEBUG","message":"Environment config: \n{MongoAddr:mongodb://mongo MongoTimeout:20s RedisAddr:redis:6379 ServerAddr::1325 CabinetAddr::3334 SessionStepTimeout:240 AuthenType:email PrivateCabAuth:callback SessionAuthTimeout:3600 SmsGateway:http://sendmail:1001/api/sendmail?to={PHONE}\u0026from=guest@wimark.com\u0026subject=Authorization\u0026body=Code:%20{MESSAGE} CountryCode:7 PhoneDefCodes:[] AuthenTypes:[email] AuthenGWs:[http://sendmail:1001/api/sendmail?to={PHONE}\u0026from=guest@wimark.com\u0026subject=Authorization\u0026body=Code:%20{MESSAGE}] GWs:map[email:http://sendmail:1001/api/sendmail?to={PHONE}\u0026from=guest@wimark.com\u0026subject=Authorization\u0026body=Code:%20{MESSAGE}] AuthType:email SessionTimeout:300 SessionBlockTimeout:0 SwitchURL:http://redirect-daemon:1324/api/authorize RedirectURL:http://wimark.com ContentDir:/content VoucherGateway:http://sendmail:1001/api/sendmail?to={PHONE}\u0026from=guest@wimark.com\u0026subject=Authorization\u0026body=Code:%20{MESSAGE} PaymentSystems:map[] PaymentNames:[] PaymentGateway:[] ServeAddr::13255 PaymentServeAddr: HumoHashTmpl:phone=\u003cphone\u003e\u0026merchant_id=1\u0026amount=\u003camount\u003e HumoHashKey:test EnableSMSRuFrontCall:true CNATimeout:120 RadiusServeAddr::8081 Debug:false PhoneCC:992 BillingProviders:{Host: Port: Login: Password: TestMode:false Vendor: SrlsID: TimeOut:0}}\n","service":"PORTAL_BACKEND","src_file":"main.go","src_line":121}
{"timestamp":"2026-06-25T17:57:48.22744482Z","level":"INFO","message":"Connected to Mongo with address: mongodb://mongo","service":"PORTAL_BACKEND","src_file":"main.go","src_line":134}
{"timestamp":"2026-06-27T18:54:28.94546297Z","level":"INFO","message":"Version of daemon is: v1.9.6, builded: 2025-02-05T09:37:13Z, hash: abcecd1f","service":"PORTAL_BACKEND","src_file":"main.go","src_line":120}
{"timestamp":"2026-06-27T18:54:28.947731339Z","level":"DEBUG","message":"Environment config: \n{MongoAddr:mongodb://mongo MongoTimeout:20s RedisAddr:redis:6379 ServerAddr::1325 CabinetAddr::3334 SessionStepTimeout:240 AuthenType:email PrivateCabAuth:callback SessionAuthTimeout:3600 SmsGateway:http://sendmail:1001/api/sendmail?to={PHONE}\u0026from=guest@wimark.com\u0026subject=Authorization\u0026body=Code:%20{MESSAGE} CountryCode:7 PhoneDefCodes:[] AuthenTypes:[email] AuthenGWs:[http://sendmail:1001/api/sendmail?to={PHONE}\u0026from=guest@wimark.com\u0026subject=Authorization\u0026body=Code:%20{MESSAGE}] GWs:map[email:http://sendmail:1001/api/sendmail?to={PHONE}\u0026from=guest@wimark.com\u0026subject=Authorization\u0026body=Code:%20{MESSAGE}] AuthType:email SessionTimeout:300 SessionBlockTimeout:0 SwitchURL:http://redirect-daemon:1324/api/authorize RedirectURL:http://wimark.com ContentDir:/content VoucherGateway:http://sendmail:1001/api/sendmail?to={PHONE}\u0026from=guest@wimark.com\u0026subject=Authorization\u0026body=Code:%20{MESSAGE} PaymentSystems:map[] PaymentNames:[] PaymentGateway:[] ServeAddr::13255 PaymentServeAddr: HumoHashTmpl:phone=\u003cphone\u003e\u0026merchant_id=1\u0026amount=\u003camount\u003e HumoHashKey:test EnableSMSRuFrontCall:true CNATimeout:120 RadiusServeAddr::8081 Debug:false PhoneCC:992 BillingProviders:{Host: Port: Login: Password: TestMode:false Vendor: SrlsID: TimeOut:0}}\n","service":"PORTAL_BACKEND","src_file":"main.go","src_line":121}
{"timestamp":"2026-06-27T18:54:31.004571983Z","level":"INFO","message":"Connected to Mongo with address: mongodb://mongo","service":"PORTAL_BACKEND","src_file":"main.go","src_line":134}
{"timestamp":"2026-07-17T17:13:57.679320835Z","level":"INFO","message":"Version of daemon is: v1.9.6, builded: 2025-02-05T09:37:13Z, hash: abcecd1f","service":"PORTAL_BACKEND","src_file":"main.go","src_line":120}
{"timestamp":"2026-07-17T17:13:57.679641582Z","level":"DEBUG","message":"Environment config: \n{MongoAddr:mongodb://mongo MongoTimeout:20s RedisAddr:redis:6379 ServerAddr::1325 CabinetAddr::3334 SessionStepTimeout:240 AuthenType:email PrivateCabAuth:callback SessionAuthTimeout:3600 SmsGateway:http://sendmail:1001/api/sendmail?to={PHONE}\u0026from=guest@wimark.com\u0026subject=Authorization\u0026body=Code:%20{MESSAGE} CountryCode:7 PhoneDefCodes:[] AuthenTypes:[email] AuthenGWs:[http://sendmail:1001/api/sendmail?to={PHONE}\u0026from=guest@wimark.com\u0026subject=Authorization\u0026body=Code:%20{MESSAGE}] GWs:map[email:http://sendmail:1001/api/sendmail?to={PHONE}\u0026from=guest@wimark.com\u0026subject=Authorization\u0026body=Code:%20{MESSAGE}] AuthType:email SessionTimeout:300 SessionBlockTimeout:0 SwitchURL:http://redirect-daemon:1324/api/authorize RedirectURL:http://wimark.com ContentDir:/content VoucherGateway:http://sendmail:1001/api/sendmail?to={PHONE}\u0026from=guest@wimark.com\u0026subject=Authorization\u0026body=Code:%20{MESSAGE} PaymentSystems:map[] PaymentNames:[] PaymentGateway:[] ServeAddr::13255 PaymentServeAddr: HumoHashTmpl:phone=\u003cphone\u003e\u0026merchant_id=1\u0026amount=\u003camount\u003e HumoHashKey:test EnableSMSRuFrontCall:true CNATimeout:120 RadiusServeAddr::8081 Debug:false PhoneCC:992 BillingProviders:{Host: Port: Login: Password: TestMode:false Vendor: SrlsID: TimeOut:0}}\n","service":"PORTAL_BACKEND","src_file":"main.go","src_line":121}
{"timestamp":"2026-07-17T17:13:59.742734073Z","level":"INFO","message":"Connected to Mongo with address: mongodb://mongo","service":"PORTAL_BACKEND","src_file":"main.go","src_line":134}
root@wmswifi:/opt/wimark/portal/esia-auth/certs#

### ASSISTANT
**Шаг 12 — Проверка логов сервиса configurer-golang**

**Объяснение/Действие:**  
Логи `backend-golang` и `portal-backend` не содержат явных ошибок валидации лицензии в последних записях (только штатные сообщения о проверке доступа и подключении к БД). В архитектуре Wimark ONE за проверку системных ограничений, включая валидацию ключей и лимитов на количество порталов, часто отвечает сервис `configurer-golang`. 

Нам необходимо проверить его логи на наличие сообщений о неудачной проверке ключа, истечении срока действия или принудительном сбросе лимитов до базового (1 портал).

Выполните на сервере следующую команду:
```bash
docker logs one-configurer-golang-1 2>&1 | grep -iE "license|limit|portal" | tail -30
```

**Протокол:**  
- Логи `backend` и `portal-backend` не выявили явных ошибок, связанных с лицензией.  
- Ключ лицензии физически присутствует в коллекции `wne_license_key` в MongoDB.  
- Текущий фокус: выявление ошибок валидации в логах сервиса `configurer-golang`, который управляет системными настройками.

**Вопросы:**  
Какой точный вывод даст эта команда? Жду вашего ответа.

### USER
{"level":"debug","key":"DATA","value":"{\"WLANs\":{},\"CPEs\":{\"4174f9dd-648f-0785-6640-08c6b3fbf0c2\":{\"name\":\"Qtech-f0c2\",\"connected\":true,\"description\":\"\",\"model\":{\"id\":\"20b51049-5885-46b0-a7a4-7b7dd987e060\",\"name\":\"QTECH QWP-82\",\"short\":\"qtech,qwp-82\"},\"config_status\":\"ok\",\"last_error\":{\"module\":\"\",\"module_id\":\"\",\"type\":\"\",\"description\":\"\",\"recommendation\":\"\"},\"config\":{\"name\":\"\",\"description\":\"\",\"wifi\":{\"radio0\":{\"bandmode\":\"11g\",\"bandwidth\":\"HT20\",\"txpower\":\"\",\"mintxpower\":\"\",\"power\":{\"range\":[1,20],\"auto\":true},\"wlans\":[\"ceab9273-4bd8-4c4e-b544-87446cc661dd\"],\"channels\":[1,6,11],\"country\":\"RU\",\"country_ie\":0,\"maxclients\":0,\"scanningconfig\":{\"enabled\":false,\"reportperiod\":0,\"scantimeout\":0,\"scannumber\":0},\"require_mode\":\"off\",\"frequency\":\"2.4\",\"basic_rate\":\"\",\"supported_rates\":null,\"legacy_rates\":\"\",\"log_level\":\"\",\"max_inactivity\":0,\"cell_density\":0},\"radio1\":{\"bandmode\":\"11a\",\"bandwidth\":\"VHT20\",\"txpower\":\"\",\"mintxpower\":\"\",\"power\":{\"range\":[1,20],\"auto\":true},\"wlans\":[\"ceab9273-4bd8-4c4e-b544-87446cc661dd\"],\"channels\":[36,40,44,48,132,136,140,149,153,157,161,165,52,56,60,144,64],\"country\":\"RU\",\"country_ie\":0,\"maxclients\":0,\"scanningconfig\":{\"enabled\":false,\"reportperiod\":0,\"scantimeout\":0,\"scannumber\":0},\"require_mode\":\"off\",\"frequency\":\"5\",\"basic_rate\":\"\",\"supported_rates\":null,\"legacy_rates\":\"\",\"log_level\":\"\",\"max_inactivity\":0,\"cell_density\":0}},\"wired\":{\"lan\":{\"primary_vlan\":0,\"vlans\":null},\"wan\":{\"primary_vlan\":0,\"vlans\":null}},\"lbs_config\":{\"enabled\":false,\"reportperiod\":30,\"clienttimeout\":30,\"maxquiet\":5,\"maxcachequeue\":50,\"emptywatcher\":false,\"whitelist\":[],\"blacklist\":[],\"filtermode\":\"None\"},\"stats_config\":{\"enabled\":false,\"reportperiod\":30},\"log_config\":{\"log_ip\":\"\",\"log_prefix\":\"\",\"log_proto\":\"\",\"log_port\":0,\"enabled\":false},\"dhcpcap_config\":{\"msgtypefilter\":[],\"enabled\":false},\"firewall\":{\"l2_chain\":\"\",\"l3_filter\":{\"mac_list\":[],\"ip_list\":[]},\"wan_access_block\":false,\"nat_access\":false},\"firmware\":{\"file\":\"\",\"storage\":\"\",\"checksum\":\"\",\"timeout\":0,\"mode\":\"check\"},\"tunnels\":{},\"beeline_config\":{\"nas_ip\":\"192.168.12.159\"},\"wmsnmpd\":{\"default\":{\"enabled\":false,\"community\":\"\",\"location\":\"\",\"interfaces\":[]}},\"ntp_config\":{\"type\":\"timeserver\",\"enable\":true,\"servers\":[\"10.3.30.26\"]},\"wifi_lock\":false,\"gre_peer_addr\":\"\",\"net_manual\":{},\"wifi_manual\":{}},\"state\":{\"wifi\":{\"radio0\":{\"frequency\":\"2.4\",\"bandmode\":\"11g\",\"bandwidth\":\"HT20\",\"channel\":\"11\",\"txpower\":\"20\",\"enabled\":true,\"wlanstates\":{\"ceab9273-4bd8-4c4e-b544-87446cc661dd\":{\"state\":\"ENABLED\",\"virtual_iface\":\"phy0-ap0\",\"bssid\":\"08:C6:B3:0F:0C:20\"}}},\"radio1\":{\"frequency\":\"5\",\"bandmode\":\"11a\",\"bandwidth\":\"VHT20\",\"channel\":\"52\",\"txpower\":\"20\",\"enabled\":true,\"wlanstates\":{\"ceab9273-4bd8-4c4e-b544-87446cc661dd\":{\"state\":\"ENABLED\",\"virtual_iface\":\"phy1-ap0\",\"bssid\":\"08:C6:B3:0F:0C:21\"}}}},\"firmware\":{\"has_update\":false,\"current_md5\":\"\",\"version\":{\"version\":\"v1.15.2-e\",\"commit\":\"f3c33c83737d355398d2eed4d6e4eb21e2355430\",\"build\":0},\"features\":[\"acl\",\"cpeagent\",\"dhcp-cap\",\"ethernet-accounting\",\"firewall\",\"firmware\",\"get\",\"l2-portal-nft\",\"lbs\",\"logging\",\"logupload\",\"network\",\"nftables\",\"openwrt\",\"radius\",\"scanning\",\"snmp\",\"statistic\",\"tc\",\"ubus\",\"uci\",\"umdns\",\"wids\",\"wifi\",\"wired\",\"wired-support\",\"wpa3\"]},\"wan\":{\"iface\":\"lan\",\"proto\":\"static\"},\"l2tp_state\":{\"enabled\":true,\"host\":\"one\",\"host_addr\":\"192.168.12.154\",\"host_tunnel\":0,\"tunnel_type\":\"none\",\"local_addr\":\"192.168.12.159\",\"local_iface\":\"\",\"local_tunnel\":1},\"network\":{\"ipaddr\":\"192.168.12.159\",\"macaddr\":\"08:C6:B3:FB:F0:C2\",\"ipaddrs\":[{\"ipaddr\":\"192.168.12.159\",\"netmask\":\"255.255.255.\"}],\"gateway\":\"192.168.12.1\"},\"tunnels\":null,\"net_manual\":null,\"wifi_manual\":null,\"manufacturing_data\":{\"serial_number\":\"\",\"wlan_mac\":\"\"}},\"first_connection\":0,\"last_connection\":0,\"last_disconnection\":0,\"config_not_send\":false,\"latitude\":0,\"longitude\":0,\"tag\":\"\"}},\"Radius\":{},\"VPNHosts\":{},\"Controller\":{},\"CPEModel\":{\"20b51049-5885-46b0-a7a4-7b7dd987e060\":{\"name\":\"qtech,qwp-82\",\"description\":\"QTECH QWP-82\",\"caps\":{\"wifi\":{\"radio0\":{\"txpwrlist\":[{\"dbm\":0,\"mw\":1},{\"dbm\":1,\"mw\":1},{\"dbm\":2,\"mw\":1},{\"dbm\":3,\"mw\":1},{\"dbm\":4,\"mw\":2},{\"dbm\":5,\"mw\":3},{\"dbm\":6,\"mw\":3},{\"dbm\":7,\"mw\":5},{\"dbm\":8,\"mw\":6},{\"dbm\":9,\"mw\":7},{\"dbm\":10,\"mw\":10},{\"dbm\":11,\"mw\":12},{\"dbm\":12,\"mw\":15},{\"dbm\":13,\"mw\":19},{\"dbm\":14,\"mw\":25},{\"dbm\":15,\"mw\":31},{\"dbm\":16,\"mw\":39},{\"dbm\":17,\"mw\":50},{\"dbm\":18,\"mw\":63},{\"dbm\":19,\"mw\":79},{\"dbm\":20,\"mw\":100}],\"htmodelist\":{\"HE160\":false,\"HE20\":true,\"HE40\":true,\"HE80\":false,\"HE80+80\":false,\"HT20\":true,\"HT40\":true,\"NOHT\":false,\"VHT160\":false,\"VHT20\":false,\"VHT40\":false,\"VHT80\":false,\"VHT80+80\":false},\"hwmodelist\":{\"a\":false,\"ac\":false,\"ad\":false,\"ax\":true,\"b\":true,\"g\":true,\"n\":true},\"freqlist\":[{\"restricted\":false,\"mhz\":2412,\"channel\":1,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":2417,\"channel\":2,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":2422,\"channel\":3,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":2427,\"channel\":4,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":2432,\"channel\":5,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":2437,\"channel\":6,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":2442,\"channel\":7,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":2447,\"channel\":8,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":2452,\"channel\":9,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":2457,\"channel\":10,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":2462,\"channel\":11,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":2467,\"channel\":12,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":2472,\"channel\":13,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":true,\"mhz\":2484,\"channel\":14,\"max_txpower\":{\"dbm\":20,\"mw\":100}}],\"txpower_offset\":0,\"frequency\":\"2.4\"},\"radio1\":{\"txpwrlist\":[{\"dbm\":0,\"mw\":1},{\"dbm\":1,\"mw\":1},{\"dbm\":2,\"mw\":1},{\"dbm\":3,\"mw\":1},{\"dbm\":4,\"mw\":2},{\"dbm\":5,\"mw\":3},{\"dbm\":6,\"mw\":3},{\"dbm\":7,\"mw\":5},{\"dbm\":8,\"mw\":6},{\"dbm\":9,\"mw\":7},{\"dbm\":10,\"mw\":10},{\"dbm\":11,\"mw\":12},{\"dbm\":12,\"mw\":15},{\"dbm\":13,\"mw\":19},{\"dbm\":14,\"mw\":25},{\"dbm\":15,\"mw\":31},{\"dbm\":16,\"mw\":39},{\"dbm\":17,\"mw\":50},{\"dbm\":18,\"mw\":63},{\"dbm\":19,\"mw\":79},{\"dbm\":20,\"mw\":100}],\"htmodelist\":{\"HE160\":false,\"HE20\":true,\"HE40\":true,\"HE80\":true,\"HE80+80\":false,\"HT20\":true,\"HT40\":true,\"NOHT\":false,\"VHT160\":false,\"VHT20\":true,\"VHT40\":true,\"VHT80\":true,\"VHT80+80\":false},\"hwmodelist\":{\"a\":false,\"ac\":true,\"ad\":false,\"ax\":true,\"b\":false,\"g\":false,\"n\":true},\"freqlist\":[{\"restricted\":false,\"mhz\":5180,\"channel\":36,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5200,\"channel\":40,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5220,\"channel\":44,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5240,\"channel\":48,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5260,\"channel\":52,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5280,\"channel\":56,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5300,\"channel\":60,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5320,\"channel\":64,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5500,\"channel\":100,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5520,\"channel\":104,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5540,\"channel\":108,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5560,\"channel\":112,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5580,\"channel\":116,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5600,\"channel\":120,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5620,\"channel\":124,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5640,\"channel\":128,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5660,\"channel\":132,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5680,\"channel\":136,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5700,\"channel\":140,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5720,\"channel\":144,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5745,\"channel\":149,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5765,\"channel\":153,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5785,\"channel\":157,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5805,\"channel\":161,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5825,\"channel\":165,\"max_txpower\":{\"dbm\":20,\"mw\":100}}],\"txpower_offset\":0,\"frequency\":\"5\"}},\"wired\":{\"lan\":{\"switch\":\"\",\"ports\":[{\"index\":\"2\",\"num\":0,\"role\":\"lan\",\"type\":\"socket\"}]},\"wan\":{\"switch\":\"\",\"ports\":[{\"index\":\"1\",\"num\":0,\"role\":\"wan\",\"type\":\"socket\"}]}}},\"firmwares\":null,\"version\":{\"version\":\"\",\"commit\":\"\",\"build\":0}}},\"ConfigRule\":{},\"L2Chain\":{},\"CaptiveRedirect\":{},\"HotspotProfile\":{},\"BaseLocation\":{},\"RRMGroup\":{}}","time":"2026-07-17T17:14:25Z","message":"get value from context"}{"level":"debug","key":"CPE","value":"{\"name\":\"Qtech-f0c2\",\"connected\":true,\"description\":\"\",\"model\":{\"id\":\"20b51049-5885-46b0-a7a4-7b7dd987e060\",\"name\":\"QTECH QWP-82\",\"short\":\"qtech,qwp-82\"},\"config_status\":\"ok\",\"last_error\":{\"module\":\"\",\"module_id\":\"\",\"type\":\"\",\"description\":\"\",\"recommendation\":\"\"},\"config\":{\"name\":\"\",\"description\":\"\",\"wifi\":{\"radio0\":{\"bandmode\":\"11g\",\"bandwidth\":\"HT20\",\"txpower\":\"\",\"mintxpower\":\"\",\"power\":{\"range\":[1,20],\"auto\":true},\"wlans\":[\"ceab9273-4bd8-4c4e-b544-87446cc661dd\"],\"channels\":[1,6,11],\"country\":\"RU\",\"country_ie\":0,\"maxclients\":0,\"scanningconfig\":{\"enabled\":false,\"reportperiod\":0,\"scantimeout\":0,\"scannumber\":0},\"require_mode\":\"off\",\"frequency\":\"2.4\",\"basic_rate\":\"\",\"supported_rates\":null,\"legacy_rates\":\"\",\"log_level\":\"\",\"max_inactivity\":0,\"cell_density\":0},\"radio1\":{\"bandmode\":\"11a\",\"bandwidth\":\"VHT20\",\"txpower\":\"\",\"mintxpower\":\"\",\"power\":{\"range\":[1,20],\"auto\":true},\"wlans\":[\"ceab9273-4bd8-4c4e-b544-87446cc661dd\"],\"channels\":[36,40,44,48,132,136,140,149,153,157,161,165,52,56,60,144,64],\"country\":\"RU\",\"country_ie\":0,\"maxclients\":0,\"scanningconfig\":{\"enabled\":false,\"reportperiod\":0,\"scantimeout\":0,\"scannumber\":0},\"require_mode\":\"off\",\"frequency\":\"5\",\"basic_rate\":\"\",\"supported_rates\":null,\"legacy_rates\":\"\",\"log_level\":\"\",\"max_inactivity\":0,\"cell_density\":0}},\"wired\":{\"lan\":{\"primary_vlan\":0,\"vlans\":null},\"wan\":{\"primary_vlan\":0,\"vlans\":null}},\"lbs_config\":{\"enabled\":false,\"reportperiod\":30,\"clienttimeout\":30,\"maxquiet\":5,\"maxcachequeue\":50,\"emptywatcher\":false,\"whitelist\":[],\"blacklist\":[],\"filtermode\":\"None\"},\"stats_config\":{\"enabled\":false,\"reportperiod\":30},\"log_config\":{\"log_ip\":\"\",\"log_prefix\":\"\",\"log_proto\":\"\",\"log_port\":0,\"enabled\":false},\"dhcpcap_config\":{\"msgtypefilter\":[],\"enabled\":false},\"firewall\":{\"l2_chain\":\"\",\"l3_filter\":{\"mac_list\":[],\"ip_list\":[]},\"wan_access_block\":false,\"nat_access\":false},\"firmware\":{\"file\":\"\",\"storage\":\"\",\"checksum\":\"\",\"timeout\":0,\"mode\":\"check\"},\"tunnels\":{},\"beeline_config\":{\"nas_ip\":\"192.168.12.159\"},\"wmsnmpd\":{\"default\":{\"enabled\":false,\"community\":\"\",\"location\":\"\",\"interfaces\":[]}},\"ntp_config\":{\"type\":\"timeserver\",\"enable\":true,\"servers\":[\"10.3.30.26\"]},\"wifi_lock\":false,\"gre_peer_addr\":\"\",\"net_manual\":{},\"wifi_manual\":{}},\"state\":{\"wifi\":{\"radio0\":{\"frequency\":\"2.4\",\"bandmode\":\"11g\",\"bandwidth\":\"HT20\",\"channel\":\"11\",\"txpower\":\"20\",\"enabled\":true,\"wlanstates\":{\"ceab9273-4bd8-4c4e-b544-87446cc661dd\":{\"state\":\"ENABLED\",\"virtual_iface\":\"phy0-ap0\",\"bssid\":\"08:C6:B3:0F:0C:20\"}}},\"radio1\":{\"frequency\":\"5\",\"bandmode\":\"11a\",\"bandwidth\":\"VHT20\",\"channel\":\"52\",\"txpower\":\"20\",\"enabled\":true,\"wlanstates\":{\"ceab9273-4bd8-4c4e-b544-87446cc661dd\":{\"state\":\"ENABLED\",\"virtual_iface\":\"phy1-ap0\",\"bssid\":\"08:C6:B3:0F:0C:21\"}}}},\"firmware\":{\"has_update\":false,\"current_md5\":\"\",\"version\":{\"version\":\"v1.15.2-e\",\"commit\":\"f3c33c83737d355398d2eed4d6e4eb21e2355430\",\"build\":0},\"features\":[\"acl\",\"cpeagent\",\"dhcp-cap\",\"ethernet-accounting\",\"firewall\",\"firmware\",\"get\",\"l2-portal-nft\",\"lbs\",\"logging\",\"logupload\",\"network\",\"nftables\",\"openwrt\",\"radius\",\"scanning\",\"snmp\",\"statistic\",\"tc\",\"ubus\",\"uci\",\"umdns\",\"wids\",\"wifi\",\"wired\",\"wired-support\",\"wpa3\"]},\"wan\":{\"iface\":\"lan\",\"proto\":\"static\"},\"l2tp_state\":{\"enabled\":true,\"host\":\"one\",\"host_addr\":\"192.168.12.154\",\"host_tunnel\":0,\"tunnel_type\":\"none\",\"local_addr\":\"192.168.12.159\",\"local_iface\":\"\",\"local_tunnel\":1},\"network\":{\"ipaddr\":\"192.168.12.159\",\"macaddr\":\"08:C6:B3:FB:F0:C2\",\"ipaddrs\":[{\"ipaddr\":\"192.168.12.159\",\"netmask\":\"255.255.255.\"}],\"gateway\":\"192.168.12.1\"},\"tunnels\":null,\"net_manual\":null,\"wifi_manual\":null,\"manufacturing_data\":{\"serial_number\":\"\",\"wlan_mac\":\"\"}},\"first_connection\":0,\"last_connection\":0,\"last_disconnection\":0,\"config_not_send\":false,\"latitude\":0,\"longitude\":0,\"tag\":\"\"}","time":"2026-07-17T17:14:25Z","message":"get value from context"}
{"level":"debug","key":"DATA","value":"{\"WLANs\":{},\"CPEs\":{\"4174f9dd-648f-0785-6640-08c6b3fbf0c2\":{\"name\":\"Qtech-f0c2\",\"connected\":true,\"description\":\"\",\"model\":{\"id\":\"20b51049-5885-46b0-a7a4-7b7dd987e060\",\"name\":\"QTECH QWP-82\",\"short\":\"qtech,qwp-82\"},\"config_status\":\"ok\",\"last_error\":{\"module\":\"\",\"module_id\":\"\",\"type\":\"\",\"description\":\"\",\"recommendation\":\"\"},\"config\":{\"name\":\"\",\"description\":\"\",\"wifi\":{\"radio0\":{\"bandmode\":\"11g\",\"bandwidth\":\"HT20\",\"txpower\":\"\",\"mintxpower\":\"\",\"power\":{\"range\":[1,20],\"auto\":true},\"wlans\":[\"ceab9273-4bd8-4c4e-b544-87446cc661dd\"],\"channels\":[1,6,11],\"country\":\"RU\",\"country_ie\":0,\"maxclients\":0,\"scanningconfig\":{\"enabled\":false,\"reportperiod\":0,\"scantimeout\":0,\"scannumber\":0},\"require_mode\":\"off\",\"frequency\":\"2.4\",\"basic_rate\":\"\",\"supported_rates\":null,\"legacy_rates\":\"\",\"log_level\":\"\",\"max_inactivity\":0,\"cell_density\":0},\"radio1\":{\"bandmode\":\"11a\",\"bandwidth\":\"VHT20\",\"txpower\":\"\",\"mintxpower\":\"\",\"power\":{\"range\":[1,20],\"auto\":true},\"wlans\":[\"ceab9273-4bd8-4c4e-b544-87446cc661dd\"],\"channels\":[36,40,44,48,132,136,140,149,153,157,161,165,52,56,60,144,64],\"country\":\"RU\",\"country_ie\":0,\"maxclients\":0,\"scanningconfig\":{\"enabled\":false,\"reportperiod\":0,\"scantimeout\":0,\"scannumber\":0},\"require_mode\":\"off\",\"frequency\":\"5\",\"basic_rate\":\"\",\"supported_rates\":null,\"legacy_rates\":\"\",\"log_level\":\"\",\"max_inactivity\":0,\"cell_density\":0}},\"wired\":{\"lan\":{\"primary_vlan\":0,\"vlans\":null},\"wan\":{\"primary_vlan\":0,\"vlans\":null}},\"lbs_config\":{\"enabled\":false,\"reportperiod\":30,\"clienttimeout\":30,\"maxquiet\":5,\"maxcachequeue\":50,\"emptywatcher\":false,\"whitelist\":[],\"blacklist\":[],\"filtermode\":\"None\"},\"stats_config\":{\"enabled\":false,\"reportperiod\":30},\"log_config\":{\"log_ip\":\"\",\"log_prefix\":\"\",\"log_proto\":\"\",\"log_port\":0,\"enabled\":false},\"dhcpcap_config\":{\"msgtypefilter\":[],\"enabled\":false},\"firewall\":{\"l2_chain\":\"\",\"l3_filter\":{\"mac_list\":[],\"ip_list\":[]},\"wan_access_block\":false,\"nat_access\":false},\"firmware\":{\"file\":\"\",\"storage\":\"\",\"checksum\":\"\",\"timeout\":0,\"mode\":\"check\"},\"tunnels\":{},\"beeline_config\":{\"nas_ip\":\"192.168.12.159\"},\"wmsnmpd\":{\"default\":{\"enabled\":false,\"community\":\"\",\"location\":\"\",\"interfaces\":[]}},\"ntp_config\":{\"type\":\"timeserver\",\"enable\":true,\"servers\":[\"10.3.30.26\"]},\"wifi_lock\":false,\"gre_peer_addr\":\"\",\"net_manual\":{},\"wifi_manual\":{}},\"state\":{\"wifi\":{\"radio0\":{\"frequency\":\"2.4\",\"bandmode\":\"11g\",\"bandwidth\":\"HT20\",\"channel\":\"11\",\"txpower\":\"20\",\"enabled\":true,\"wlanstates\":{\"ceab9273-4bd8-4c4e-b544-87446cc661dd\":{\"state\":\"ENABLED\",\"virtual_iface\":\"phy0-ap0\",\"bssid\":\"08:C6:B3:0F:0C:20\"}}},\"radio1\":{\"frequency\":\"5\",\"bandmode\":\"11a\",\"bandwidth\":\"VHT20\",\"channel\":\"52\",\"txpower\":\"20\",\"enabled\":true,\"wlanstates\":{\"ceab9273-4bd8-4c4e-b544-87446cc661dd\":{\"state\":\"ENABLED\",\"virtual_iface\":\"phy1-ap0\",\"bssid\":\"08:C6:B3:0F:0C:21\"}}}},\"firmware\":{\"has_update\":false,\"current_md5\":\"\",\"version\":{\"version\":\"v1.15.2-e\",\"commit\":\"f3c33c83737d355398d2eed4d6e4eb21e2355430\",\"build\":0},\"features\":[\"acl\",\"cpeagent\",\"dhcp-cap\",\"ethernet-accounting\",\"firewall\",\"firmware\",\"get\",\"l2-portal-nft\",\"lbs\",\"logging\",\"logupload\",\"network\",\"nftables\",\"openwrt\",\"radius\",\"scanning\",\"snmp\",\"statistic\",\"tc\",\"ubus\",\"uci\",\"umdns\",\"wids\",\"wifi\",\"wired\",\"wired-support\",\"wpa3\"]},\"wan\":{\"iface\":\"lan\",\"proto\":\"static\"},\"l2tp_state\":{\"enabled\":true,\"host\":\"one\",\"host_addr\":\"192.168.12.154\",\"host_tunnel\":0,\"tunnel_type\":\"none\",\"local_addr\":\"192.168.12.159\",\"local_iface\":\"\",\"local_tunnel\":1},\"network\":{\"ipaddr\":\"192.168.12.159\",\"macaddr\":\"08:C6:B3:FB:F0:C2\",\"ipaddrs\":[{\"ipaddr\":\"192.168.12.159\",\"netmask\":\"255.255.255.\"}],\"gateway\":\"192.168.12.1\"},\"tunnels\":null,\"net_manual\":null,\"wifi_manual\":null,\"manufacturing_data\":{\"serial_number\":\"\",\"wlan_mac\":\"\"}},\"first_connection\":0,\"last_connection\":0,\"last_disconnection\":0,\"config_not_send\":false,\"latitude\":0,\"longitude\":0,\"tag\":\"\"}},\"Radius\":{},\"VPNHosts\":{},\"Controller\":{},\"CPEModel\":{\"20b51049-5885-46b0-a7a4-7b7dd987e060\":{\"name\":\"qtech,qwp-82\",\"description\":\"QTECH QWP-82\",\"caps\":{\"wifi\":{\"radio0\":{\"txpwrlist\":[{\"dbm\":0,\"mw\":1},{\"dbm\":1,\"mw\":1},{\"dbm\":2,\"mw\":1},{\"dbm\":3,\"mw\":1},{\"dbm\":4,\"mw\":2},{\"dbm\":5,\"mw\":3},{\"dbm\":6,\"mw\":3},{\"dbm\":7,\"mw\":5},{\"dbm\":8,\"mw\":6},{\"dbm\":9,\"mw\":7},{\"dbm\":10,\"mw\":10},{\"dbm\":11,\"mw\":12},{\"dbm\":12,\"mw\":15},{\"dbm\":13,\"mw\":19},{\"dbm\":14,\"mw\":25},{\"dbm\":15,\"mw\":31},{\"dbm\":16,\"mw\":39},{\"dbm\":17,\"mw\":50},{\"dbm\":18,\"mw\":63},{\"dbm\":19,\"mw\":79},{\"dbm\":20,\"mw\":100}],\"htmodelist\":{\"HE160\":false,\"HE20\":true,\"HE40\":true,\"HE80\":false,\"HE80+80\":false,\"HT20\":true,\"HT40\":true,\"NOHT\":false,\"VHT160\":false,\"VHT20\":false,\"VHT40\":false,\"VHT80\":false,\"VHT80+80\":false},\"hwmodelist\":{\"a\":false,\"ac\":false,\"ad\":false,\"ax\":true,\"b\":true,\"g\":true,\"n\":true},\"freqlist\":[{\"restricted\":false,\"mhz\":2412,\"channel\":1,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":2417,\"channel\":2,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":2422,\"channel\":3,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":2427,\"channel\":4,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":2432,\"channel\":5,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":2437,\"channel\":6,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":2442,\"channel\":7,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":2447,\"channel\":8,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":2452,\"channel\":9,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":2457,\"channel\":10,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":2462,\"channel\":11,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":2467,\"channel\":12,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":2472,\"channel\":13,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":true,\"mhz\":2484,\"channel\":14,\"max_txpower\":{\"dbm\":20,\"mw\":100}}],\"txpower_offset\":0,\"frequency\":\"2.4\"},\"radio1\":{\"txpwrlist\":[{\"dbm\":0,\"mw\":1},{\"dbm\":1,\"mw\":1},{\"dbm\":2,\"mw\":1},{\"dbm\":3,\"mw\":1},{\"dbm\":4,\"mw\":2},{\"dbm\":5,\"mw\":3},{\"dbm\":6,\"mw\":3},{\"dbm\":7,\"mw\":5},{\"dbm\":8,\"mw\":6},{\"dbm\":9,\"mw\":7},{\"dbm\":10,\"mw\":10},{\"dbm\":11,\"mw\":12},{\"dbm\":12,\"mw\":15},{\"dbm\":13,\"mw\":19},{\"dbm\":14,\"mw\":25},{\"dbm\":15,\"mw\":31},{\"dbm\":16,\"mw\":39},{\"dbm\":17,\"mw\":50},{\"dbm\":18,\"mw\":63},{\"dbm\":19,\"mw\":79},{\"dbm\":20,\"mw\":100}],\"htmodelist\":{\"HE160\":false,\"HE20\":true,\"HE40\":true,\"HE80\":true,\"HE80+80\":false,\"HT20\":true,\"HT40\":true,\"NOHT\":false,\"VHT160\":false,\"VHT20\":true,\"VHT40\":true,\"VHT80\":true,\"VHT80+80\":false},\"hwmodelist\":{\"a\":false,\"ac\":true,\"ad\":false,\"ax\":true,\"b\":false,\"g\":false,\"n\":true},\"freqlist\":[{\"restricted\":false,\"mhz\":5180,\"channel\":36,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5200,\"channel\":40,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5220,\"channel\":44,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5240,\"channel\":48,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5260,\"channel\":52,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5280,\"channel\":56,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5300,\"channel\":60,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5320,\"channel\":64,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5500,\"channel\":100,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5520,\"channel\":104,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5540,\"channel\":108,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5560,\"channel\":112,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5580,\"channel\":116,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5600,\"channel\":120,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5620,\"channel\":124,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5640,\"channel\":128,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5660,\"channel\":132,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5680,\"channel\":136,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5700,\"channel\":140,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5720,\"channel\":144,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5745,\"channel\":149,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5765,\"channel\":153,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5785,\"channel\":157,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5805,\"channel\":161,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5825,\"channel\":165,\"max_txpower\":{\"dbm\":20,\"mw\":100}}],\"txpower_offset\":0,\"frequency\":\"5\"}},\"wired\":{\"lan\":{\"switch\":\"\",\"ports\":[{\"index\":\"2\",\"num\":0,\"role\":\"lan\",\"type\":\"socket\"}]},\"wan\":{\"switch\":\"\",\"ports\":[{\"index\":\"1\",\"num\":0,\"role\":\"wan\",\"type\":\"socket\"}]}}},\"firmwares\":null,\"version\":{\"version\":\"\",\"commit\":\"\",\"build\":0}}},\"ConfigRule\":{},\"L2Chain\":{},\"CaptiveRedirect\":{},\"HotspotProfile\":{},\"BaseLocation\":{},\"RRMGroup\":{}}","time":"2026-07-17T17:14:25Z","message":"get value from context"}
{"level":"debug","key":"CPE","value":"{\"name\":\"Qtech-f0c2\",\"connected\":true,\"description\":\"\",\"model\":{\"id\":\"20b51049-5885-46b0-a7a4-7b7dd987e060\",\"name\":\"QTECH QWP-82\",\"short\":\"qtech,qwp-82\"},\"config_status\":\"ok\",\"last_error\":{\"module\":\"\",\"module_id\":\"\",\"type\":\"\",\"description\":\"\",\"recommendation\":\"\"},\"config\":{\"name\":\"\",\"description\":\"\",\"wifi\":{\"radio0\":{\"bandmode\":\"11g\",\"bandwidth\":\"HT20\",\"txpower\":\"\",\"mintxpower\":\"\",\"power\":{\"range\":[1,20],\"auto\":true},\"wlans\":[\"ceab9273-4bd8-4c4e-b544-87446cc661dd\"],\"channels\":[1,6,11],\"country\":\"RU\",\"country_ie\":0,\"maxclients\":0,\"scanningconfig\":{\"enabled\":false,\"reportperiod\":0,\"scantimeout\":0,\"scannumber\":0},\"require_mode\":\"off\",\"frequency\":\"2.4\",\"basic_rate\":\"\",\"supported_rates\":null,\"legacy_rates\":\"\",\"log_level\":\"\",\"max_inactivity\":0,\"cell_density\":0},\"radio1\":{\"bandmode\":\"11a\",\"bandwidth\":\"VHT20\",\"txpower\":\"\",\"mintxpower\":\"\",\"power\":{\"range\":[1,20],\"auto\":true},\"wlans\":[\"ceab9273-4bd8-4c4e-b544-87446cc661dd\"],\"channels\":[36,40,44,48,132,136,140,149,153,157,161,165,52,56,60,144,64],\"country\":\"RU\",\"country_ie\":0,\"maxclients\":0,\"scanningconfig\":{\"enabled\":false,\"reportperiod\":0,\"scantimeout\":0,\"scannumber\":0},\"require_mode\":\"off\",\"frequency\":\"5\",\"basic_rate\":\"\",\"supported_rates\":null,\"legacy_rates\":\"\",\"log_level\":\"\",\"max_inactivity\":0,\"cell_density\":0}},\"wired\":{\"lan\":{\"primary_vlan\":0,\"vlans\":null},\"wan\":{\"primary_vlan\":0,\"vlans\":null}},\"lbs_config\":{\"enabled\":false,\"reportperiod\":30,\"clienttimeout\":30,\"maxquiet\":5,\"maxcachequeue\":50,\"emptywatcher\":false,\"whitelist\":[],\"blacklist\":[],\"filtermode\":\"None\"},\"stats_config\":{\"enabled\":false,\"reportperiod\":30},\"log_config\":{\"log_ip\":\"\",\"log_prefix\":\"\",\"log_proto\":\"\",\"log_port\":0,\"enabled\":false},\"dhcpcap_config\":{\"msgtypefilter\":[],\"enabled\":false},\"firewall\":{\"l2_chain\":\"\",\"l3_filter\":{\"mac_list\":[],\"ip_list\":[]},\"wan_access_block\":false,\"nat_access\":false},\"firmware\":{\"file\":\"\",\"storage\":\"\",\"checksum\":\"\",\"timeout\":0,\"mode\":\"check\"},\"tunnels\":{},\"beeline_config\":{\"nas_ip\":\"192.168.12.159\"},\"wmsnmpd\":{\"default\":{\"enabled\":false,\"community\":\"\",\"location\":\"\",\"interfaces\":[]}},\"ntp_config\":{\"type\":\"timeserver\",\"enable\":true,\"servers\":[\"10.3.30.26\"]},\"wifi_lock\":false,\"gre_peer_addr\":\"\",\"net_manual\":{},\"wifi_manual\":{}},\"state\":{\"wifi\":{\"radio0\":{\"frequency\":\"2.4\",\"bandmode\":\"11g\",\"bandwidth\":\"HT20\",\"channel\":\"11\",\"txpower\":\"20\",\"enabled\":true,\"wlanstates\":{\"ceab9273-4bd8-4c4e-b544-87446cc661dd\":{\"state\":\"ENABLED\",\"virtual_iface\":\"phy0-ap0\",\"bssid\":\"08:C6:B3:0F:0C:20\"}}},\"radio1\":{\"frequency\":\"5\",\"bandmode\":\"11a\",\"bandwidth\":\"VHT20\",\"channel\":\"52\",\"txpower\":\"20\",\"enabled\":true,\"wlanstates\":{\"ceab9273-4bd8-4c4e-b544-87446cc661dd\":{\"state\":\"ENABLED\",\"virtual_iface\":\"phy1-ap0\",\"bssid\":\"08:C6:B3:0F:0C:21\"}}}},\"firmware\":{\"has_update\":false,\"current_md5\":\"\",\"version\":{\"version\":\"v1.15.2-e\",\"commit\":\"f3c33c83737d355398d2eed4d6e4eb21e2355430\",\"build\":0},\"features\":[\"acl\",\"cpeagent\",\"dhcp-cap\",\"ethernet-accounting\",\"firewall\",\"firmware\",\"get\",\"l2-portal-nft\",\"lbs\",\"logging\",\"logupload\",\"network\",\"nftables\",\"openwrt\",\"radius\",\"scanning\",\"snmp\",\"statistic\",\"tc\",\"ubus\",\"uci\",\"umdns\",\"wids\",\"wifi\",\"wired\",\"wired-support\",\"wpa3\"]},\"wan\":{\"iface\":\"lan\",\"proto\":\"static\"},\"l2tp_state\":{\"enabled\":true,\"host\":\"one\",\"host_addr\":\"192.168.12.154\",\"host_tunnel\":0,\"tunnel_type\":\"none\",\"local_addr\":\"192.168.12.159\",\"local_iface\":\"\",\"local_tunnel\":1},\"network\":{\"ipaddr\":\"192.168.12.159\",\"macaddr\":\"08:C6:B3:FB:F0:C2\",\"ipaddrs\":[{\"ipaddr\":\"192.168.12.159\",\"netmask\":\"255.255.255.\"}],\"gateway\":\"192.168.12.1\"},\"tunnels\":null,\"net_manual\":null,\"wifi_manual\":null,\"manufacturing_data\":{\"serial_number\":\"\",\"wlan_mac\":\"\"}},\"first_connection\":0,\"last_connection\":0,\"last_disconnection\":0,\"config_not_send\":false,\"latitude\":0,\"longitude\":0,\"tag\":\"\"}","time":"2026-07-17T17:14:25Z","message":"get value from context"}
{"level":"debug","key":"U_REQ","value":"{\"Request\":{\"cpe\":{\"4174f9dd-648f-0785-6640-08c6b3fbf0c2\":{\"name\":\"Qtech-f0c2\",\"connected\":true,\"description\":\"\",\"model\":{\"id\":\"20b51049-5885-46b0-a7a4-7b7dd987e060\",\"name\":\"QTECH QWP-82\",\"short\":\"qtech,qwp-82\"},\"config_status\":\"ok\",\"last_error\":{\"module\":\"\",\"module_id\":\"\",\"type\":\"\",\"description\":\"\",\"recommendation\":\"\"},\"config\":{\"name\":\"\",\"description\":\"\",\"wifi\":{\"radio0\":{\"bandmode\":\"11g\",\"bandwidth\":\"HT20\",\"txpower\":\"\",\"mintxpower\":\"\",\"power\":{\"range\":[1,20],\"auto\":true},\"wlans\":[\"ceab9273-4bd8-4c4e-b544-87446cc661dd\"],\"channels\":[1,6,11],\"country\":\"RU\",\"country_ie\":0,\"maxclients\":0,\"scanningconfig\":{\"enabled\":false,\"reportperiod\":0,\"scantimeout\":0,\"scannumber\":0},\"require_mode\":\"off\",\"frequency\":\"2.4\",\"basic_rate\":\"\",\"supported_rates\":null,\"legacy_rates\":\"\",\"log_level\":\"\",\"max_inactivity\":0,\"cell_density\":0},\"radio1\":{\"bandmode\":\"11a\",\"bandwidth\":\"VHT20\",\"txpower\":\"\",\"mintxpower\":\"\",\"power\":{\"range\":[1,20],\"auto\":true},\"wlans\":[\"ceab9273-4bd8-4c4e-b544-87446cc661dd\"],\"channels\":[36,40,44,48,132,136,140,149,153,157,161,165,52,56,60,144,64],\"country\":\"RU\",\"country_ie\":0,\"maxclients\":0,\"scanningconfig\":{\"enabled\":false,\"reportperiod\":0,\"scantimeout\":0,\"scannumber\":0},\"require_mode\":\"off\",\"frequency\":\"5\",\"basic_rate\":\"\",\"supported_rates\":null,\"legacy_rates\":\"\",\"log_level\":\"\",\"max_inactivity\":0,\"cell_density\":0}},\"wired\":{\"lan\":{\"primary_vlan\":0,\"vlans\":null},\"wan\":{\"primary_vlan\":0,\"vlans\":null}},\"lbs_config\":{\"enabled\":false,\"reportperiod\":30,\"clienttimeout\":30,\"maxquiet\":5,\"maxcachequeue\":50,\"emptywatcher\":false,\"whitelist\":[],\"blacklist\":[],\"filtermode\":\"None\"},\"stats_config\":{\"enabled\":false,\"reportperiod\":30},\"log_config\":{\"log_ip\":\"\",\"log_prefix\":\"\",\"log_proto\":\"\",\"log_port\":0,\"enabled\":false},\"dhcpcap_config\":{\"msgtypefilter\":[],\"enabled\":false},\"firewall\":{\"l2_chain\":\"\",\"l3_filter\":{\"mac_list\":[],\"ip_list\":[]},\"wan_access_block\":false,\"nat_access\":false},\"firmware\":{\"file\":\"\",\"storage\":\"\",\"checksum\":\"\",\"timeout\":0,\"mode\":\"check\"},\"tunnels\":{},\"beeline_config\":{\"nas_ip\":\"192.168.12.159\"},\"wmsnmpd\":{\"default\":{\"enabled\":false,\"community\":\"\",\"location\":\"\",\"interfaces\":[]}},\"ntp_config\":{\"type\":\"timeserver\",\"enable\":true,\"servers\":[\"10.3.30.26\"]},\"wifi_lock\":false,\"gre_peer_addr\":\"\",\"net_manual\":{},\"wifi_manual\":{}},\"state\":{\"wifi\":{\"radio0\":{\"frequency\":\"2.4\",\"bandmode\":\"11g\",\"bandwidth\":\"HT20\",\"channel\":\"11\",\"txpower\":\"20\",\"enabled\":true,\"wlanstates\":{\"ceab9273-4bd8-4c4e-b544-87446cc661dd\":{\"state\":\"ENABLED\",\"virtual_iface\":\"phy0-ap0\",\"bssid\":\"08:C6:B3:0F:0C:20\"}}},\"radio1\":{\"frequency\":\"5\",\"bandmode\":\"11a\",\"bandwidth\":\"VHT20\",\"channel\":\"52\",\"txpower\":\"20\",\"enabled\":true,\"wlanstates\":{\"ceab9273-4bd8-4c4e-b544-87446cc661dd\":{\"state\":\"ENABLED\",\"virtual_iface\":\"phy1-ap0\",\"bssid\":\"08:C6:B3:0F:0C:21\"}}}},\"firmware\":{\"has_update\":false,\"current_md5\":\"\",\"version\":{\"version\":\"v1.15.2-e\",\"commit\":\"f3c33c83737d355398d2eed4d6e4eb21e2355430\",\"build\":0},\"features\":[\"acl\",\"cpeagent\",\"dhcp-cap\",\"ethernet-accounting\",\"firewall\",\"firmware\",\"get\",\"l2-portal-nft\",\"lbs\",\"logging\",\"logupload\",\"network\",\"nftables\",\"openwrt\",\"radius\",\"scanning\",\"snmp\",\"statistic\",\"tc\",\"ubus\",\"uci\",\"umdns\",\"wids\",\"wifi\",\"wired\",\"wired-support\",\"wpa3\"]},\"wan\":{\"iface\":\"lan\",\"proto\":\"static\"},\"l2tp_state\":{\"enabled\":true,\"host\":\"one\",\"host_addr\":\"192.168.12.154\",\"host_tunnel\":0,\"tunnel_type\":\"none\",\"local_addr\":\"192.168.12.159\",\"local_iface\":\"\",\"local_tunnel\":1},\"network\":{\"ipaddr\":\"192.168.12.159\",\"macaddr\":\"08:C6:B3:FB:F0:C2\",\"ipaddrs\":[{\"ipaddr\":\"192.168.12.159\",\"netmask\":\"255.255.255.\"}],\"gateway\":\"192.168.12.1\"},\"tunnels\":null,\"net_manual\":null,\"wifi_manual\":null,\"manufacturing_data\":{\"serial_number\":\"\",\"wlan_mac\":\"\"}},\"first_connection\":0,\"last_connection\":0,\"last_disconnection\":0,\"config_not_send\":false,\"latitude\":0,\"longitude\":0,\"tag\":\"\"}}},\"CpeStates\":{}}","time":"2026-07-17T17:14:25Z","message":"get value from context"}
{"level":"debug","job_id":"Divesage","U_REQ":{"Request":{"cpe":{"4174f9dd-648f-0785-6640-08c6b3fbf0c2":{"name":"Qtech-f0c2","connected":true,"description":"","model":{"id":"20b51049-5885-46b0-a7a4-7b7dd987e060","name":"QTECH QWP-82","short":"qtech,qwp-82"},"config_status":"ok","last_error":{"module":"","module_id":"","type":"","description":"","recommendation":""},"config":{"name":"","description":"","wifi":{"radio0":{"bandmode":"11g","bandwidth":"HT20","txpower":"","mintxpower":"","power":{"range":[1,20],"auto":true},"wlans":["ceab9273-4bd8-4c4e-b544-87446cc661dd"],"channels":[1,6,11],"country":"RU","country_ie":0,"maxclients":0,"scanningconfig":{"enabled":false,"reportperiod":0,"scantimeout":0,"scannumber":0},"require_mode":"off","frequency":"2.4","basic_rate":"","supported_rates":null,"legacy_rates":"","log_level":"","max_inactivity":0,"cell_density":0},"radio1":{"bandmode":"11a","bandwidth":"VHT20","txpower":"","mintxpower":"","power":{"range":[1,20],"auto":true},"wlans":["ceab9273-4bd8-4c4e-b544-87446cc661dd"],"channels":[36,40,44,48,132,136,140,149,153,157,161,165,52,56,60,144,64],"country":"RU","country_ie":0,"maxclients":0,"scanningconfig":{"enabled":false,"reportperiod":0,"scantimeout":0,"scannumber":0},"require_mode":"off","frequency":"5","basic_rate":"","supported_rates":null,"legacy_rates":"","log_level":"","max_inactivity":0,"cell_density":0}},"wired":{"lan":{"primary_vlan":0,"vlans":null},"wan":{"primary_vlan":0,"vlans":null}},"lbs_config":{"enabled":false,"reportperiod":30,"clienttimeout":30,"maxquiet":5,"maxcachequeue":50,"emptywatcher":false,"whitelist":[],"blacklist":[],"filtermode":"None"},"stats_config":{"enabled":false,"reportperiod":30},"log_config":{"log_ip":"","log_prefix":"","log_proto":"","log_port":0,"enabled":false},"dhcpcap_config":{"msgtypefilter":[],"enabled":false},"firewall":{"l2_chain":"","l3_filter":{"mac_list":[],"ip_list":[]},"wan_access_block":false,"nat_access":false},"firmware":{"file":"","storage":"","checksum":"","timeout":0,"mode":"check"},"tunnels":{},"beeline_config":{"nas_ip":"192.168.12.159"},"wmsnmpd":{"default":{"enabled":false,"community":"","location":"","interfaces":[]}},"ntp_config":{"type":"timeserver","enable":true,"servers":["10.3.30.26"]},"wifi_lock":false,"gre_peer_addr":"","net_manual":{},"wifi_manual":{}},"state":{"wifi":{"radio0":{"frequency":"2.4","bandmode":"11g","bandwidth":"HT20","channel":"11","txpower":"20","enabled":true,"wlanstates":{"ceab9273-4bd8-4c4e-b544-87446cc661dd":{"state":"ENABLED","virtual_iface":"phy0-ap0","bssid":"08:C6:B3:0F:0C:20"}}},"radio1":{"frequency":"5","bandmode":"11a","bandwidth":"VHT20","channel":"52","txpower":"20","enabled":true,"wlanstates":{"ceab9273-4bd8-4c4e-b544-87446cc661dd":{"state":"ENABLED","virtual_iface":"phy1-ap0","bssid":"08:C6:B3:0F:0C:21"}}}},"firmware":{"has_update":false,"current_md5":"","version":{"version":"v1.15.2-e","commit":"f3c33c83737d355398d2eed4d6e4eb21e2355430","build":0},"features":["acl","cpeagent","dhcp-cap","ethernet-accounting","firewall","firmware","get","l2-portal-nft","lbs","logging","logupload","network","nftables","openwrt","radius","scanning","snmp","statistic","tc","ubus","uci","umdns","wids","wifi","wired","wired-support","wpa3"]},"wan":{"iface":"lan","proto":"static"},"l2tp_state":{"enabled":true,"host":"one","host_addr":"192.168.12.154","host_tunnel":0,"tunnel_type":"none","local_addr":"192.168.12.159","local_iface":"","local_tunnel":1},"network":{"ipaddr":"192.168.12.159","macaddr":"08:C6:B3:FB:F0:C2","ipaddrs":[{"ipaddr":"192.168.12.159","netmask":"255.255.255."}],"gateway":"192.168.12.1"},"tunnels":null,"net_manual":null,"wifi_manual":null,"manufacturing_data":{"serial_number":"","wlan_mac":""}},"first_connection":0,"last_connection":0,"last_disconnection":0,"config_not_send":false,"latitude":0,"longitude":0,"tag":""}}},"CpeStates":{}},"time":"2026-07-17T17:14:25Z","message":"value for upsert"}
{"level":"debug","key":"DATA","value":"{\"WLANs\":{\"ceab9273-4bd8-4c4e-b544-87446cc661dd\":{\"name\":\"\",\"ssid\":\"INDASTRY\",\"description\":\"\",\"security\":{\"type\":\"wpa2personal\",\"data\":{\"suites\":[\"aes\"],\"psk\":\"12345678\",\"nasid\":\"\",\"pmkcaching\":false,\"radiusauthentication\":[],\"hotspot20_profile\":\"\"}},\"nas_id\":null,\"nas_port_id\":\"\",\"nas_ip_address\":\"\",\"radius_acct_servers\":[],\"radius_acct_interval\":0,\"radius_acct_mirroring\":false,\"central_auth\":false,\"filtermode\":\"None\",\"whitelist\":[],\"blacklist\":[],\"firewall\":{\"l2_chain\":\"\",\"l3_filter\":{\"mac_list\":[],\"ip_list\":[]},\"wan_access_block\":false,\"nat_access\":false},\"hidden\":false,\"l2isolate\":false,\"wmm\":{\"categories\":{\"BE\":{\"cli_cw_min\":4,\"cli_cw_max\":10,\"cli_aifs\":3,\"cli_txop\":0,\"cli_acm\":false,\"ac_cw_min\":15,\"ac_cw_max\":63,\"ac_aifs\":3,\"ac_burst\":0},\"BK\":{\"cli_cw_min\":4,\"cli_cw_max\":10,\"cli_aifs\":7,\"cli_txop\":0,\"cli_acm\":false,\"ac_cw_min\":15,\"ac_cw_max\":1023,\"ac_aifs\":7,\"ac_burst\":0},\"VI\":{\"cli_cw_min\":3,\"cli_cw_max\":4,\"cli_aifs\":2,\"cli_txop\":94,\"cli_acm\":false,\"ac_cw_min\":7,\"ac_cw_max\":15,\"ac_aifs\":1,\"ac_burst\":3},\"VO\":{\"cli_cw_min\":2,\"cli_cw_max\":3,\"cli_aifs\":2,\"cli_txop\":47,\"cli_acm\":false,\"ac_cw_min\":3,\"ac_cw_max\":7,\"ac_aifs\":1,\"ac_burst\":1.5}},\"disabled\":false,\"uapsd\":false},\"speed_upload\":{\"value\":0,\"type\":\"kbit\"},\"speed_download\":{\"value\":0,\"type\":\"kbit\"},\"proxy_arp\":true,\"tunneling\":false,\"proto\":\"l2tpv3\",\"default_tunnel\":\"\",\"peer_address\":\"\",\"vlan\":0,\"vlans\":[],\"nat\":false,\"nat_network\":{\"ipaddr\":\"\",\"netmask\":\"\"},\"guest_control\":{\"captive_redirect\":\"\",\"mac_radius_auth_servers\":[]},\"beeline_accountng_type\":\"\",\"pmkcaching\":false,\"roam80211r\":false,\"ft_over_ds\":false,\"ft_psk_generate_local\":false,\"rrb_use_seq\":false,\"rrb_tunnelling\":false,\"nas_generate\":false,\"ieee80211k\":false,\"rrm_neighbor_report\":true,\"rrm_beacon_report\":false,\"ieee80211v\":false,\"wnm_sleep_mode\":false,\"bss_transition\":false,\"rssi_threshold\":-90,\"band_steering\":false,\"load_balancing\":false,\"signal_connect\":0,\"signal_stay\":-60,\"signal_strikes\":3,\"signal_poll_time\":5,\"signal_drop_reason\":3,\"option82state\":false,\"option82rid_type\":\"APMAC:SSID\",\"option82cid_type\":\"\",\"ppsk\":false,\"aaa_override\":false,\"r0kh\":[],\"r1kh\":[]}},\"CPEs\":{\"4174f9dd-648f-0785-6640-08c6b3fbf0c2\":{\"name\":\"Qtech-f0c2\",\"connected\":true,\"description\":\"\",\"model\":{\"id\":\"20b51049-5885-46b0-a7a4-7b7dd987e060\",\"name\":\"QTECH QWP-82\",\"short\":\"qtech,qwp-82\"},\"config_status\":\"ok\",\"last_error\":{\"module\":\"\",\"module_id\":\"\",\"type\":\"\",\"description\":\"\",\"recommendation\":\"\"},\"config\":{\"name\":\"\",\"description\":\"\",\"wifi\":{\"radio0\":{\"bandmode\":\"11g\",\"bandwidth\":\"HT20\",\"txpower\":\"\",\"mintxpower\":\"\",\"power\":{\"range\":[1,20],\"auto\":true},\"wlans\":[\"ceab9273-4bd8-4c4e-b544-87446cc661dd\"],\"channels\":[1,6,11],\"country\":\"RU\",\"country_ie\":0,\"maxclients\":0,\"scanningconfig\":{\"enabled\":false,\"reportperiod\":0,\"scantimeout\":0,\"scannumber\":0},\"require_mode\":\"off\",\"frequency\":\"2.4\",\"basic_rate\":\"\",\"supported_rates\":null,\"legacy_rates\":\"\",\"log_level\":\"\",\"max_inactivity\":0,\"cell_density\":0},\"radio1\":{\"bandmode\":\"11a\",\"bandwidth\":\"VHT20\",\"txpower\":\"\",\"mintxpower\":\"\",\"power\":{\"range\":[1,20],\"auto\":true},\"wlans\":[\"ceab9273-4bd8-4c4e-b544-87446cc661dd\"],\"channels\":[36,40,44,48,132,136,140,149,153,157,161,165,52,56,60,144,64],\"country\":\"RU\",\"country_ie\":0,\"maxclients\":0,\"scanningconfig\":{\"enabled\":false,\"reportperiod\":0,\"scantimeout\":0,\"scannumber\":0},\"require_mode\":\"off\",\"frequency\":\"5\",\"basic_rate\":\"\",\"supported_rates\":null,\"legacy_rates\":\"\",\"log_level\":\"\",\"max_inactivity\":0,\"cell_density\":0}},\"wired\":{\"lan\":{\"primary_vlan\":0,\"vlans\":null},\"wan\":{\"primary_vlan\":0,\"vlans\":null}},\"lbs_config\":{\"enabled\":false,\"reportperiod\":30,\"clienttimeout\":30,\"maxquiet\":5,\"maxcachequeue\":50,\"emptywatcher\":false,\"whitelist\":[],\"blacklist\":[],\"filtermode\":\"None\"},\"stats_config\":{\"enabled\":false,\"reportperiod\":30},\"log_config\":{\"log_ip\":\"\",\"log_prefix\":\"\",\"log_proto\":\"\",\"log_port\":0,\"enabled\":false},\"dhcpcap_config\":{\"msgtypefilter\":[],\"enabled\":false},\"firewall\":{\"l2_chain\":\"\",\"l3_filter\":{\"mac_list\":[],\"ip_list\":[]},\"wan_access_block\":false,\"nat_access\":false},\"firmware\":{\"file\":\"\",\"storage\":\"\",\"checksum\":\"\",\"timeout\":0,\"mode\":\"check\"},\"tunnels\":{},\"beeline_config\":{\"nas_ip\":\"192.168.12.159\"},\"wmsnmpd\":{\"default\":{\"enabled\":false,\"community\":\"\",\"location\":\"\",\"interfaces\":[]}},\"ntp_config\":{\"type\":\"timeserver\",\"enable\":true,\"servers\":[\"10.3.30.26\"]},\"wifi_lock\":false,\"gre_peer_addr\":\"\",\"net_manual\":{},\"wifi_manual\":{}},\"state\":{\"wifi\":{\"radio0\":{\"frequency\":\"2.4\",\"bandmode\":\"11g\",\"bandwidth\":\"HT20\",\"channel\":\"11\",\"txpower\":\"20\",\"enabled\":true,\"wlanstates\":{\"ceab9273-4bd8-4c4e-b544-87446cc661dd\":{\"state\":\"ENABLED\",\"virtual_iface\":\"phy0-ap0\",\"bssid\":\"08:C6:B3:0F:0C:20\"}}},\"radio1\":{\"frequency\":\"5\",\"bandmode\":\"11a\",\"bandwidth\":\"VHT20\",\"channel\":\"52\",\"txpower\":\"20\",\"enabled\":true,\"wlanstates\":{\"ceab9273-4bd8-4c4e-b544-87446cc661dd\":{\"state\":\"ENABLED\",\"virtual_iface\":\"phy1-ap0\",\"bssid\":\"08:C6:B3:0F:0C:21\"}}}},\"firmware\":{\"has_update\":false,\"current_md5\":\"\",\"version\":{\"version\":\"v1.15.2-e\",\"commit\":\"f3c33c83737d355398d2eed4d6e4eb21e2355430\",\"build\":0},\"features\":[\"acl\",\"cpeagent\",\"dhcp-cap\",\"ethernet-accounting\",\"firewall\",\"firmware\",\"get\",\"l2-portal-nft\",\"lbs\",\"logging\",\"logupload\",\"network\",\"nftables\",\"openwrt\",\"radius\",\"scanning\",\"snmp\",\"statistic\",\"tc\",\"ubus\",\"uci\",\"umdns\",\"wids\",\"wifi\",\"wired\",\"wired-support\",\"wpa3\"]},\"wan\":{\"iface\":\"lan\",\"proto\":\"static\"},\"l2tp_state\":{\"enabled\":true,\"host\":\"one\",\"host_addr\":\"192.168.12.154\",\"host_tunnel\":0,\"tunnel_type\":\"none\",\"local_addr\":\"192.168.12.159\",\"local_iface\":\"\",\"local_tunnel\":1},\"network\":{\"ipaddr\":\"192.168.12.159\",\"macaddr\":\"08:C6:B3:FB:F0:C2\",\"ipaddrs\":[{\"ipaddr\":\"192.168.12.159\",\"netmask\":\"255.255.255.\"}],\"gateway\":\"192.168.12.1\"},\"tunnels\":null,\"net_manual\":null,\"wifi_manual\":null,\"manufacturing_data\":{\"serial_number\":\"\",\"wlan_mac\":\"\"}},\"first_connection\":0,\"last_connection\":0,\"last_disconnection\":0,\"config_not_send\":false,\"latitude\":0,\"longitude\":0,\"tag\":\"\"}},\"Radius\":{},\"VPNHosts\":{\"one\":{\"hostname\":\"one\",\"os_uuid\":\"one\",\"interfaces\":[\"eth0\"],\"state\":\"CONNECTED\",\"interfaces_details\":[{\"name\":\"eth0\",\"type\":\"device\",\"hw_addr\":\"00:15:5d:aa:b6:02\"}]}},\"Controller\":{},\"CPEModel\":{\"20b51049-5885-46b0-a7a4-7b7dd987e060\":{\"name\":\"qtech,qwp-82\",\"description\":\"QTECH QWP-82\",\"caps\":{\"wifi\":{\"radio0\":{\"txpwrlist\":[{\"dbm\":0,\"mw\":1},{\"dbm\":1,\"mw\":1},{\"dbm\":2,\"mw\":1},{\"dbm\":3,\"mw\":1},{\"dbm\":4,\"mw\":2},{\"dbm\":5,\"mw\":3},{\"dbm\":6,\"mw\":3},{\"dbm\":7,\"mw\":5},{\"dbm\":8,\"mw\":6},{\"dbm\":9,\"mw\":7},{\"dbm\":10,\"mw\":10},{\"dbm\":11,\"mw\":12},{\"dbm\":12,\"mw\":15},{\"dbm\":13,\"mw\":19},{\"dbm\":14,\"mw\":25},{\"dbm\":15,\"mw\":31},{\"dbm\":16,\"mw\":39},{\"dbm\":17,\"mw\":50},{\"dbm\":18,\"mw\":63},{\"dbm\":19,\"mw\":79},{\"dbm\":20,\"mw\":100}],\"htmodelist\":{\"HE160\":false,\"HE20\":true,\"HE40\":true,\"HE80\":false,\"HE80+80\":false,\"HT20\":true,\"HT40\":true,\"NOHT\":false,\"VHT160\":false,\"VHT20\":false,\"VHT40\":false,\"VHT80\":false,\"VHT80+80\":false},\"hwmodelist\":{\"a\":false,\"ac\":false,\"ad\":false,\"ax\":true,\"b\":true,\"g\":true,\"n\":true},\"freqlist\":[{\"restricted\":false,\"mhz\":2412,\"channel\":1,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":2417,\"channel\":2,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":2422,\"channel\":3,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":2427,\"channel\":4,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":2432,\"channel\":5,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":2437,\"channel\":6,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":2442,\"channel\":7,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":2447,\"channel\":8,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":2452,\"channel\":9,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":2457,\"channel\":10,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":2462,\"channel\":11,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":2467,\"channel\":12,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":2472,\"channel\":13,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":true,\"mhz\":2484,\"channel\":14,\"max_txpower\":{\"dbm\":20,\"mw\":100}}],\"txpower_offset\":0,\"frequency\":\"2.4\"},\"radio1\":{\"txpwrlist\":[{\"dbm\":0,\"mw\":1},{\"dbm\":1,\"mw\":1},{\"dbm\":2,\"mw\":1},{\"dbm\":3,\"mw\":1},{\"dbm\":4,\"mw\":2},{\"dbm\":5,\"mw\":3},{\"dbm\":6,\"mw\":3},{\"dbm\":7,\"mw\":5},{\"dbm\":8,\"mw\":6},{\"dbm\":9,\"mw\":7},{\"dbm\":10,\"mw\":10},{\"dbm\":11,\"mw\":12},{\"dbm\":12,\"mw\":15},{\"dbm\":13,\"mw\":19},{\"dbm\":14,\"mw\":25},{\"dbm\":15,\"mw\":31},{\"dbm\":16,\"mw\":39},{\"dbm\":17,\"mw\":50},{\"dbm\":18,\"mw\":63},{\"dbm\":19,\"mw\":79},{\"dbm\":20,\"mw\":100}],\"htmodelist\":{\"HE160\":false,\"HE20\":true,\"HE40\":true,\"HE80\":true,\"HE80+80\":false,\"HT20\":true,\"HT40\":true,\"NOHT\":false,\"VHT160\":false,\"VHT20\":true,\"VHT40\":true,\"VHT80\":true,\"VHT80+80\":false},\"hwmodelist\":{\"a\":false,\"ac\":true,\"ad\":false,\"ax\":true,\"b\":false,\"g\":false,\"n\":true},\"freqlist\":[{\"restricted\":false,\"mhz\":5180,\"channel\":36,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5200,\"channel\":40,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5220,\"channel\":44,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5240,\"channel\":48,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5260,\"channel\":52,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5280,\"channel\":56,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5300,\"channel\":60,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5320,\"channel\":64,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5500,\"channel\":100,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5520,\"channel\":104,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5540,\"channel\":108,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5560,\"channel\":112,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5580,\"channel\":116,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5600,\"channel\":120,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5620,\"channel\":124,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5640,\"channel\":128,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5660,\"channel\":132,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5680,\"channel\":136,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5700,\"channel\":140,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5720,\"channel\":144,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5745,\"channel\":149,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5765,\"channel\":153,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5785,\"channel\":157,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5805,\"channel\":161,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5825,\"channel\":165,\"max_txpower\":{\"dbm\":20,\"mw\":100}}],\"txpower_offset\":0,\"frequency\":\"5\"}},\"wired\":{\"lan\":{\"switch\":\"\",\"ports\":[{\"index\":\"2\",\"num\":0,\"role\":\"lan\",\"type\":\"socket\"}]},\"wan\":{\"switch\":\"\",\"ports\":[{\"index\":\"1\",\"num\":0,\"role\":\"wan\",\"type\":\"socket\"}]}}},\"firmwares\":null,\"version\":{\"version\":\"\",\"commit\":\"\",\"build\":0}}},\"ConfigRule\":{},\"L2Chain\":{},\"CaptiveRedirect\":{},\"HotspotProfile\":{},\"BaseLocation\":{},\"RRMGroup\":{}}","time":"2026-07-17T17:14:25Z","message":"get value from context"}


{"level":"debug","key":"CPE","value":"{\"name\":\"Qtech-f0c2\",\"connected\":true,\"description\":\"\",\"model\":{\"id\":\"20b51049-5885-46b0-a7a4-7b7dd987e060\",\"name\":\"QTECH QWP-82\",\"short\":\"qtech,qwp-82\"},\"config_status\":\"ok\",\"last_error\":{\"module\":\"\",\"module_id\":\"\",\"type\":\"\",\"description\":\"\",\"recommendation\":\"\"},\"config\":{\"name\":\"\",\"description\":\"\",\"wifi\":{\"radio0\":{\"bandmode\":\"11g\",\"bandwidth\":\"HT20\",\"txpower\":\"\",\"mintxpower\":\"\",\"power\":{\"range\":[1,20],\"auto\":true},\"wlans\":[\"ceab9273-4bd8-4c4e-b544-87446cc661dd\"],\"channels\":[1,6,11],\"country\":\"RU\",\"country_ie\":0,\"maxclients\":0,\"scanningconfig\":{\"enabled\":false,\"reportperiod\":0,\"scantimeout\":0,\"scannumber\":0},\"require_mode\":\"off\",\"frequency\":\"2.4\",\"basic_rate\":\"\",\"supported_rates\":null,\"legacy_rates\":\"\",\"log_level\":\"\",\"max_inactivity\":0,\"cell_density\":0},\"radio1\":{\"bandmode\":\"11a\",\"bandwidth\":\"VHT20\",\"txpower\":\"\",\"mintxpower\":\"\",\"power\":{\"range\":[1,20],\"auto\":true},\"wlans\":[\"ceab9273-4bd8-4c4e-b544-87446cc661dd\"],\"channels\":[36,40,44,48,132,136,140,149,153,157,161,165,52,56,60,144,64],\"country\":\"RU\",\"country_ie\":0,\"maxclients\":0,\"scanningconfig\":{\"enabled\":false,\"reportperiod\":0,\"scantimeout\":0,\"scannumber\":0},\"require_mode\":\"off\",\"frequency\":\"5\",\"basic_rate\":\"\",\"supported_rates\":null,\"legacy_rates\":\"\",\"log_level\":\"\",\"max_inactivity\":0,\"cell_density\":0}},\"wired\":{\"lan\":{\"primary_vlan\":0,\"vlans\":null},\"wan\":{\"primary_vlan\":0,\"vlans\":null}},\"lbs_config\":{\"enabled\":false,\"reportperiod\":30,\"clienttimeout\":30,\"maxquiet\":5,\"maxcachequeue\":50,\"emptywatcher\":false,\"whitelist\":[],\"blacklist\":[],\"filtermode\":\"None\"},\"stats_config\":{\"enabled\":false,\"reportperiod\":30},\"log_config\":{\"log_ip\":\"\",\"log_prefix\":\"\",\"log_proto\":\"\",\"log_port\":0,\"enabled\":false},\"dhcpcap_config\":{\"msgtypefilter\":[],\"enabled\":false},\"firewall\":{\"l2_chain\":\"\",\"l3_filter\":{\"mac_list\":[],\"ip_list\":[]},\"wan_access_block\":false,\"nat_access\":false},\"firmware\":{\"file\":\"\",\"storage\":\"\",\"checksum\":\"\",\"timeout\":0,\"mode\":\"check\"},\"tunnels\":{},\"beeline_config\":{\"nas_ip\":\"192.168.12.159\"},\"wmsnmpd\":{\"default\":{\"enabled\":false,\"community\":\"\",\"location\":\"\",\"interfaces\":[]}},\"ntp_config\":{\"type\":\"timeserver\",\"enable\":true,\"servers\":[\"10.3.30.26\"]},\"wifi_lock\":false,\"gre_peer_addr\":\"\",\"net_manual\":{},\"wifi_manual\":{}},\"state\":{\"wifi\":{\"radio0\":{\"frequency\":\"2.4\",\"bandmode\":\"11g\",\"bandwidth\":\"HT20\",\"channel\":\"11\",\"txpower\":\"20\",\"enabled\":true,\"wlanstates\":{\"ceab9273-4bd8-4c4e-b544-87446cc661dd\":{\"state\":\"ENABLED\",\"virtual_iface\":\"phy0-ap0\",\"bssid\":\"08:C6:B3:0F:0C:20\"}}},\"radio1\":{\"frequency\":\"5\",\"bandmode\":\"11a\",\"bandwidth\":\"VHT20\",\"channel\":\"52\",\"txpower\":\"20\",\"enabled\":true,\"wlanstates\":{\"ceab9273-4bd8-4c4e-b544-87446cc661dd\":{\"state\":\"ENABLED\",\"virtual_iface\":\"phy1-ap0\",\"bssid\":\"08:C6:B3:0F:0C:21\"}}}},\"firmware\":{\"has_update\":false,\"current_md5\":\"\",\"version\":{\"version\":\"v1.15.2-e\",\"commit\":\"f3c33c83737d355398d2eed4d6e4eb21e2355430\",\"build\":0},\"features\":[\"acl\",\"cpeagent\",\"dhcp-cap\",\"ethernet-accounting\",\"firewall\",\"firmware\",\"get\",\"l2-portal-nft\",\"lbs\",\"logging\",\"logupload\",\"network\",\"nftables\",\"openwrt\",\"radius\",\"scanning\",\"snmp\",\"statistic\",\"tc\",\"ubus\",\"uci\",\"umdns\",\"wids\",\"wifi\",\"wired\",\"wired-support\",\"wpa3\"]},\"wan\":{\"iface\":\"lan\",\"proto\":\"static\"},\"l2tp_state\":{\"enabled\":true,\"host\":\"one\",\"host_addr\":\"192.168.12.154\",\"host_tunnel\":0,\"tunnel_type\":\"none\",\"local_addr\":\"192.168.12.159\",\"local_iface\":\"\",\"local_tunnel\":1},\"network\":{\"ipaddr\":\"192.168.12.159\",\"macaddr\":\"08:C6:B3:FB:F0:C2\",\"ipaddrs\":[{\"ipaddr\":\"192.168.12.159\",\"netmask\":\"255.255.255.\"}],\"gateway\":\"192.168.12.1\"},\"tunnels\":null,\"net_manual\":null,\"wifi_manual\":null,\"manufacturing_data\":{\"serial_number\":\"\",\"wlan_mac\":\"\"}},\"first_connection\":0,\"last_connection\":0,\"last_disconnection\":0,\"config_not_send\":false,\"latitude\":0,\"longitude\":0,\"tag\":\"\"}","time":"2026-07-17T17:14:25Z","message":"get value from context"}
{"level":"debug","key":"CPE_META","value":"{\"ModelName\":\"QTECH QWP-82\",\"ModelId\":\"qtech,qwp-82\",\"Caps\":{\"wifi\":{\"radio0\":{\"txpwrlist\":[{\"dbm\":0,\"mw\":1},{\"dbm\":1,\"mw\":1},{\"dbm\":2,\"mw\":1},{\"dbm\":3,\"mw\":1},{\"dbm\":4,\"mw\":2},{\"dbm\":5,\"mw\":3},{\"dbm\":6,\"mw\":3},{\"dbm\":7,\"mw\":5},{\"dbm\":8,\"mw\":6},{\"dbm\":9,\"mw\":7},{\"dbm\":10,\"mw\":10},{\"dbm\":11,\"mw\":12},{\"dbm\":12,\"mw\":15},{\"dbm\":13,\"mw\":19},{\"dbm\":14,\"mw\":25},{\"dbm\":15,\"mw\":31},{\"dbm\":16,\"mw\":39},{\"dbm\":17,\"mw\":50},{\"dbm\":18,\"mw\":63},{\"dbm\":19,\"mw\":79},{\"dbm\":20,\"mw\":100}],\"htmodelist\":{\"HE160\":false,\"HE20\":true,\"HE40\":true,\"HE80\":false,\"HE80+80\":false,\"HT20\":true,\"HT40\":true,\"NOHT\":false,\"VHT160\":false,\"VHT20\":false,\"VHT40\":false,\"VHT80\":false,\"VHT80+80\":false},\"hwmodelist\":{\"a\":false,\"ac\":false,\"ad\":false,\"ax\":true,\"b\":true,\"g\":true,\"n\":true},\"freqlist\":[{\"restricted\":false,\"mhz\":2412,\"channel\":1,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":2417,\"channel\":2,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":2422,\"channel\":3,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":2427,\"channel\":4,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":2432,\"channel\":5,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":2437,\"channel\":6,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":2442,\"channel\":7,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":2447,\"channel\":8,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":2452,\"channel\":9,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":2457,\"channel\":10,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":2462,\"channel\":11,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":2467,\"channel\":12,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":2472,\"channel\":13,\"max_txpower\":{\"dbm\":20,\"mw\":100}}],\"txpower_offset\":0,\"frequency\":\"2.4\"},\"radio1\":{\"txpwrlist\":[{\"dbm\":0,\"mw\":1},{\"dbm\":1,\"mw\":1},{\"dbm\":2,\"mw\":1},{\"dbm\":3,\"mw\":1},{\"dbm\":4,\"mw\":2},{\"dbm\":5,\"mw\":3},{\"dbm\":6,\"mw\":3},{\"dbm\":7,\"mw\":5},{\"dbm\":8,\"mw\":6},{\"dbm\":9,\"mw\":7},{\"dbm\":10,\"mw\":10},{\"dbm\":11,\"mw\":12},{\"dbm\":12,\"mw\":15},{\"dbm\":13,\"mw\":19},{\"dbm\":14,\"mw\":25},{\"dbm\":15,\"mw\":31},{\"dbm\":16,\"mw\":39},{\"dbm\":17,\"mw\":50},{\"dbm\":18,\"mw\":63},{\"dbm\":19,\"mw\":79},{\"dbm\":20,\"mw\":100}],\"htmodelist\":{\"HE160\":false,\"HE20\":true,\"HE40\":true,\"HE80\":true,\"HE80+80\":false,\"HT20\":true,\"HT40\":true,\"NOHT\":false,\"VHT160\":false,\"VHT20\":true,\"VHT40\":true,\"VHT80\":true,\"VHT80+80\":false},\"hwmodelist\":{\"a\":false,\"ac\":true,\"ad\":false,\"ax\":true,\"b\":false,\"g\":false,\"n\":true},\"freqlist\":[{\"restricted\":false,\"mhz\":5180,\"channel\":36,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5200,\"channel\":40,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5220,\"channel\":44,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5240,\"channel\":48,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5260,\"channel\":52,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5280,\"channel\":56,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5300,\"channel\":60,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5320,\"channel\":64,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5660,\"channel\":132,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5680,\"channel\":136,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5700,\"channel\":140,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5720,\"channel\":144,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5745,\"channel\":149,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5765,\"channel\":153,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5785,\"channel\":157,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5805,\"channel\":161,\"max_txpower\":{\"dbm\":20,\"mw\":100}},{\"restricted\":false,\"mhz\":5825,\"channel\":165,\"max_txpower\":{\"dbm\":20,\"mw\":100}}],\"txpower_offset\":0,\"frequency\":\"5\"}},\"wired\":{\"lan\":{\"switch\":\"\",\"ports\":[{\"index\":\"2\",\"num\":0,\"role\":\"lan\",\"type\":\"socket\"}]},\"wan\":{\"switch\":\"\",\"ports\":[{\"index\":\"1\",\"num\":0,\"role\":\"wan\",\"type\":\"socket\"}]}}},\"Uci\":{\"wimark\":{\".firmware\":{\"checksum\":\"\",\"file\":\"\",\"mode\":\"check\",\"storage\":\"\",\"timeout\":\"\"},\"broker\":{\"desc\":\"\",\"name\":\"Qtech-f0c2\",\"tunneliface\":\"ipsec_lo\",\"tunneluuid\":\"one\"},\"cfg052e8a\":{\"host\":\"192.168.12.154\"},\"dhcpcap\":{\".type\":\"dhcpcap\",\"crud_op\":\"\",\"enabled\":\"false\",\"model_name\":\"\",\"receiver\":\"\",\"receiver_id\":\"\",\"typefilter\":[\"ACK\",\"OFFER\"]},\"lbs\":{\".type\":\"lbs\",\"clear_delta\":\"30\",\"clear_timeout\":\"30\",\"crud_op\":\"\",\"empty_watcher\":\"false\",\"enabled\":\"false\",\"macfilter\":\"disable\",\"maclist\":null,\"max_cache_queue\":\"50\",\"max_quiet\":\"5\",\"model_name\":\"\",\"receiver\":\"\",\"receiver_id\":\"\",\"report_timeout\":\"30\"},\"logupload\":{\".type\":\"logupload\",\"debug\":\"false\",\"enabled\":\"false\",\"logupload_host\":\"10.3.30.26\",\"logupload_port\":\"514\",\"retry_interval\":\"5\"},\"radio0\":{\".type\":\"scanning\",\"enabled\":\"false\",\"report_timeout\":\"\",\"scan_timeout\":\"\",\"scan_times\":\"\"},\"radio1\":{\".type\":\"scanning\",\"enabled\":\"false\",\"report_timeout\":\"\",\"scan_timeout\":\"\",\"scan_times\":\"\"},\"statistic\":{\".type\":\"statistic\",\"crud_op\":\"\",\"enabled\":\"false\",\"model_name\":\"\",\"receiver\":\"\",\"receiver_id\":\"\",\"tag\":\"\",\"timeout\":\"30\"},\"wsmd\":{\"enabled\":\"\",\"timeout\":\"\"}},\"wireless\":{\"radio0\":{\".type\":\"wifi-device\",\"channel\":\"auto\",\"channels\":[\"1\",\"6\",\"11\"],\"country\":\"RU\",\"country_ie\":\"1\",\"disabled\":\"\",\"hostapd_options\":\"vendor_elements=851e00008f000f00ff03190051746563682d6630633200000000000000000000\",\"htmode\":\"HT20\",\"hwmode\":\"11g\",\"noscan\":\"0\",\"require_mode\":\"\",\"rssi_reject_assoc_rssi\":\"-90\",\"txpower\":\"\"},\"radio0ceab9273_4bd8_4c4e_b544_87446cc661dd\":{\".type\":\"wifi-iface\",\"acct_interval\":\"600\",\"auth_cache\":\"false\",\"band_steering\":\"false\",\"bss_transition\":\"0\",\"central\":\"0\",\"dae_client\":\"\",\"dae_port\":\"\",\"dae_secret\":\"\",\"device\":\"radio0\",\"disassoc_low_ack\":\"0\",\"encryption\":\"psk2+aes\",\"ft_over_ds\":\"0\",\"ft_psk_generate_local\":\"0\",\"hidden\":\"false\",\"ieee80211k\":\"false\",\"ieee80211r\":\"false\",\"ieee80211v\":\"false\",\"isolate\":\"false\",\"key\":\"12345678\",\"macaddr\":\"08:c6:b3:0f:0c:20\",\"macfilter\":\"disable\",\"max_inactivity\":\"180\",\"mesh_fwding\":\"\",\"mesh_id\":\"\",\"mode\":\"ap\",\"nasid\":\"wimark\",\"network\":\"lan\",\"ownip\":\"10.3.30.26\",\"pmk_r1_push\":\"\",\"ppsk\":\"\",\"proxy_arp\":\"1\",\"rrb_use_seq\":\"0\",\"rrm_beacon_report\":\"1\",\"rrm_neighbor_report\":\"1\",\"signal_connect\":\"\",\"signal_drop_reason\":\"3\",\"signal_poll_time\":\"5\",\"signal_stay\":\"-60\",\"signal_strikes\":\"3\",\"ssid\":\"INDASTRY\",\"uapsd\":\"false\",\"ubus_acct_interval\":\"30\",\"uuid\":\"ceab9273-4bd8-4c4e-b544-87446cc661dd\",\"wmm\":\"true\",\"wmm_ac_be_acm\":\"false\",\"wmm_ac_be_aifs\":\"3\",\"wmm_ac_be_cwmax\":\"10\",\"wmm_ac_be_cwmin\":\"4\",\"wmm_ac_be_txop\":\"\",\"wmm_ac_bk_acm\":\"false\",\"wmm_ac_bk_aifs\":\"7\",\"wmm_ac_bk_cwmax\":\"10\",\"wmm_ac_bk_cwmin\":\"4\",\"wmm_ac_bk_txop\":\"\",\"wmm_ac_vi_acm\":\"false\",\"wmm_ac_vi_aifs\":\"2\",\"wmm_ac_vi_cwmax\":\"4\",\"wmm_ac_vi_cwmin\":\"3\",\"wmm_ac_vi_txop\":\"94\",\"wmm_ac_vo_acm\":\"false\",\"wmm_ac_vo_aifs\":\"2\",\"wmm_ac_vo_cwmax\":\"3\",\"wmm_ac_vo_cwmin\":\"2\",\"wmm_ac_vo_txop\":\"47\",\"wmm_tx_be_aifs\":\"3\",\"wmm_tx_be_burst\":\"0.0\",\"wmm_tx_be_cwmax\":\"9223372036854775808\",\"wmm_tx_be_cwmin\":\"32767\",\"wmm_tx_bk_aifs\":\"7\",\"wmm_tx_bk_burst\":\"0.0\",\"wmm_tx_bk_cwmax\":\"+Inf\",\"wmm_tx_bk_cwmin\":\"32767\",\"wmm_tx_vi_aifs\":\"1\",\"wmm_tx_vi_burst\":\"3.0\",\"wmm_tx_vi_cwmax\":\"32767\",\"wmm_tx_vi_cwmin\":\"127\",\"wmm_tx_vo_aifs\":\"1\",\"wmm_tx_vo_burst\":\"1.5\",\"wmm_tx_vo_cwmax\":\"127\",\"wmm_tx_vo_cwmin\":\"7\",\"wnm_sleep_mode\":\"0\"},\"radio1\":{\".type\":\"wifi-device\",\"channel\":\"auto\",\"channels\":[\"36\",\"40\",\"44\",\"48\",\"132\",\"136\",\"140\",\"149\",\"153\",\"157\",\"161\",\"165\",\"52\",\"56\",\"60\",\"144\",\"64\"],\"country\":\"RU\",\"country_ie\":\"1\",\"disabled\":\"\",\"hostapd_options\":\"vendor_elements=851e00008f000f00ff03190051746563682d6630633200000000000000000000\",\"htmode\":\"VHT20\",\"hwmode\":\"11a\",\"noscan\":\"0\",\"require_mode\":\"\",\"rssi_reject_assoc_rssi\":\"-90\",\"txpower\":\"\"},\"radio1ceab9273_4bd8_4c4e_b544_87446cc661dd\":{\".type\":\"wifi-iface\",\"acct_interval\":\"600\",\"auth_cache\":\"false\",\"band_steering\":\"false\",\"bss_transition\":\"0\",\"central\":\"0\",\"dae_client\":\"\",\"dae_port\":\"\",\"dae_secret\":\"\",\"device\":\"radio1\",\"disassoc_low_ack\":\"0\",\"encryption\":\"psk2+aes\",\"ft_over_ds\":\"0\",\"ft_psk_generate_local\":\"0\",\"hidden\":\"false\",\"ieee80211k\":\"false\",\"ieee80211r\":\"false\",\"ieee80211v\":\"false\",\"isolate\":\"false\",\"key\":\"12345678\",\"macaddr\":\"08:c6:b3:0f:0c:21\",\"macfilter\":\"disable\",\"max_inactivity\":\"180\",\"mesh_fwding\":\"\",\"mesh_id\":\"\",\"mode\":\"ap\",\"nasid\":\"wimark\",\"network\":\"lan\",\"ownip\":\"10.3.30.26\",\"pmk_r1_push\":\"\",\"ppsk\":\"\",\"proxy_arp\":\"1\",\"rrb_use_seq\":\"0\",\"rrm_beacon_report\":\"1\",\"rrm_neighbor_report\":\"1\",\"signal_connect\":\"\",\"signal_drop_reason\":\"3\",\"signal_poll_time\":\"5\",\"signal_stay\":\"-60\",\"signal_strikes\":\"3\",\"ssid\":\"INDASTRY\",\"uapsd\":\"false\",\"ubus_acct_interval\":\"30\",\"uuid\":\"ceab9273-4bd8-4c4e-b544-87446cc661dd\",\"wmm\":\"true\",\"wmm_ac_be_acm\":\"false\",\"wmm_ac_be_aifs\":\"3\",\"wmm_ac_be_cwmax\":\"10\",\"wmm_ac_be_cwmin\":\"4\",\"wmm_ac_be_txop\":\"\",\"wmm_ac_bk_acm\":\"false\",\"wmm_ac_bk_aifs\":\"7\",\"wmm_ac_bk_cwmax\":\"10\",\"wmm_ac_bk_cwmin\":\"4\",\"wmm_ac_bk_txop\":\"\",\"wmm_ac_vi_acm\":\"false\",\"wmm_ac_vi_aifs\":\"2\",\"wmm_ac_vi_cwmax\":\"4\",\"wmm_ac_vi_cwmin\":\"3\",\"wmm_ac_vi_txop\":\"94\",\"wmm_ac_vo_acm\":\"false\",\"wmm_ac_vo_aifs\":\"2\",\"wmm_ac_vo_cwmax\":\"3\",\"wmm_ac_vo_cwmin\":\"2\",\"wmm_ac_vo_txop\":\"47\",\"wmm_tx_be_aifs\":\"3\",\"wmm_tx_be_burst\":\"0.0\",\"wmm_tx_be_cwmax\":\"9223372036854775808\",\"wmm_tx_be_cwmin\":\"32767\",\"wmm_tx_bk_aifs\":\"7\",\"wmm_tx_bk_burst\":\"0.0\",\"wmm_tx_bk_cwmax\":\"+Inf\",\"wmm_tx_bk_cwmin\":\"32767\",\"wmm_tx_vi_aifs\":\"1\",\"wmm_tx_vi_burst\":\"3.0\",\"wmm_tx_vi_cwmax\":\"32767\",\"wmm_tx_vi_cwmin\":\"127\",\"wmm_tx_vo_aifs\":\"1\",\"wmm_tx_vo_burst\":\"1.5\",\"wmm_tx_vo_cwmax\":\"127\",\"wmm_tx_vo_cwmin\":\"7\",\"wnm_sleep_mode\":\"0\"}},\"system\":{\".system\":{\".type\":\"system\",\"hostname\":\"Qtech-f0c2\",\"log_ip\":\"\",\"log_port\":\"\",\"log_prefix\":\"\",\"log_proto\":\"\",\"log_remote\":\"false\"},\"ntp\":{\".type\":\"timeserver\",\"enabled\":\"true\",\"server\":[\"10.3.30.26\"]}},\"network\":{\"alan\":{\".type\":\"interface\",\"proto\":\"static\"},\"ipsec_lo\":{\".type\":\"interface\",\"proto\":\"static\"},\"lan\":{\".type\":\"interface\",\"ipv6\":\"0\",\"proto\":\"static\"},\"loopback\":{\".type\":\"interface\",\"proto\":\"static\"},\"wimark_portal\":{\".type\":\"interface\",\"ifname\":\"lo\",\"proto\":\"static\"},\"wwan\":{\".type\":\"interface\",\"proto\":\"wwan\"}},\"wmsnmpd\":{\"default\":{\".anonymous\":false,\".index\":0,\".name\":\"default\",\".type\":\"wmsnmpd\",\"auth\":\"0\",\"contact\":\"WiMark router \\u003cinfo@wimark.com\\u003e\",\"debug\":\"0\",\"disks\":[\"/overlay\",\"/tmp\"],\"enabled\":\"false\",\"ipv6\":\"0\",\"lua_folders\":[\"/lib/snmpd\"],\"mib_timeout\":\"30\"}}},\"Packages\":{\"base-files\":\"1-r22-0d559a38d9\",\"busybox\":\"1.36.1-1\",\"ca-bundle\":\"20230311-1\",\"cgi-io\":\"2022-08-10-901b0f04-21\",\"chat\":\"2.4.9.git-2021-01-04-4\",\"comgt\":\"0.32-35\",\"comgt-ncm\":\"0.32-35\",\"cpeagent\":\"v2.4.3-1\",\"curl\":\"8.7.1-r1\",\"dhcpoptinj\":\"v3.0.4-1\",\"dnsmasq\":\"2.90-2\",\"dropbear\":\"2022.82-6\",\"ebtables-legacy\":\"2018-06-27-48cff25d-1\",\"ethtool\":\"6.3-1\",\"firewall4\":\"2023-09-01-598d9fbb-1\",\"fstools\":\"2023-02-28-bfe882d5-1\",\"fwtool\":\"2019-11-12-8f7fe925-1\",\"getrandom\":\"2022-08-13-4c7b720b-2\",\"gre\":\"13\",\"hostapd-common\":\"2023-09-08-e5ccbfc6-7\",\"hostapd-utils\":\"2023-09-08-e5ccbfc6-7\",\"ip-bridge\":\"6.3.0-1\",\"ip-full\":\"6.3.0-1\",\"ip6tables-nft\":\"1.8.8-2\",\"iptables-mod-extra\":\"1.8.8-2\",\"iptables-mod-ipopt\":\"1.8.8-2\",\"iptables-mod-ipsec\":\"1.8.8-2\",\"iptables-mod-nfqueue\":\"1.8.8-2\",\"iptables-mod-physdev\":\"1.8.8-2\",\"iptables-nft\":\"1.8.8-2\",\"iw\":\"5.19-1\",\"iwinfo\":\"2023-07-01-ca79f641-1\",\"jansson4\":\"2.14-3\",\"jshn\":\"2023-05-23-75a3b870-1\",\"jsonfilter\":\"2024-01-23-594cfa86-1\",\"kernel\":\"5.15.155-1-8d30c13536..e84\",\"kmod-asn1-decoder\":\"5.15.155-1\",\"kmod-br-netfilter\":\"5.15.155-1\",\"kmod-cfg80211\":\"5.15.155+6.6.15-1\",\"kmod-crypto-acompress\":\"5.15.155-1\",\"kmod-crypto-aead\":\"5.15.155-1\",\"kmod-crypto-authenc\":\"5.15.155-1\",\"kmod-crypto-cbc\":\"5.15.155-1\",\"kmod-crypto-ccm\":\"5.15.155-1\",\"kmod-crypto-cmac\":\"5.15.155-1\",\"kmod-crypto-crc32c\":\"5.15.155-1\",\"kmod-crypto-ctr\":\"5.15.155-1\",\"kmod-crypto-deflate\":\"5.15.155-1\",\"kmod-crypto-des\":\"5.15.155-1\",\"kmod-crypto-echainiv\":\"5.15.155-1\",\"kmod-crypto-gcm\":\"5.15.155-1\",\"kmod-crypto-gf128\":\"5.15.155-1\",\"kmod-crypto-ghash\":\"5.15.155-1\",\"kmod-crypto-hash\":\"5.15.155-1\",\"kmod-crypto-hmac\":\"5.15.155-1\",\"kmod-crypto-hw-eip93\":\"5.15.155+ca08387b-1\",\"kmod-crypto-manager\":\"5.15.155-1\",\"kmod-crypto-md5\":\"5.15.155-1\",\"kmod-crypto-null\":\"5.15.155-1\",\"kmod-crypto-rng\":\"5.15.155-1\",\"kmod-crypto-seqiv\":\"5.15.155-1\",\"kmod-crypto-sha1\":\"5.15.155-1\",\"kmod-crypto-sha256\":\"5.15.155-1\",\"kmod-crypto-sha512\":\"5.15.155-1\",\"kmod-ebtables\":\"5.15.155-1\",\"kmod-ebtables-ipv4\":\"5.15.155-1\",\"kmod-gpio-button-hotplug\":\"5.15.155-3\",\"kmod-gre\":\"5.15.155-1\",\"kmod-gre6\":\"5.15.155-1\",\"kmod-hwmon-core\":\"5.15.155-1\",\"kmod-ifb\":\"5.15.155-1\",\"kmod-ip6-tunnel\":\"5.15.155-1\",\"kmod-ip6tables\":\"5.15.155-1\",\"kmod-ipsec\":\"5.15.155-1\",\"kmod-ipsec4\":\"5.15.155-1\",\"kmod-ipsec6\":\"5.15.155-1\",\"kmod-ipt-core\":\"5.15.155-1\",\"kmod-ipt-extra\":\"5.15.155-1\",\"kmod-ipt-ipopt\":\"5.15.155-1\",\"kmod-ipt-ipsec\":\"5.15.155-1\",\"kmod-ipt-nfqueue\":\"5.15.155-1\",\"kmod-ipt-physdev\":\"5.15.155-1\",\"kmod-iptunnel\":\"5.15.155-1\",\"kmod-iptunnel4\":\"5.15.155-1\",\"kmod-iptunnel6\":\"5.15.155-1\",\"kmod-l2tp\":\"5.15.155-1\",\"kmod-l2tp-eth\":\"5.15.155-1\",\"kmod-l2tp-ip\":\"5.15.155-1\",\"kmod-leds-gpio\":\"5.15.155-1\",\"kmod-lib-crc-ccitt\":\"5.15.155-1\",\"kmod-lib-crc32c\":\"5.15.155-1\",\"kmod-lib-lzo\":\"5.15.155-1\",\"kmod-lib-textsearch\":\"5.15.155-1\",\"kmod-lib-zlib-deflate\":\"5.15.155-1\",\"kmod-lib-zlib-inflate\":\"5.15.155-1\",\"kmod-libphy\":\"5.15.155-1\",\"kmod-mac80211\":\"5.15.155+6.6.15-1\",\"kmod-mdio-devres\":\"5.15.155-1\",\"kmod-mii\":\"5.15.155-1\",\"kmod-mt76-connac\":\"5.15.155+2023-09-11-f..d-2\",\"kmod-mt76-core\":\"5.15.155+2023-09-11-f..d-2\",\"kmod-mt7915-firmware\":\"5.15.155+2023-09-11-f..d-2\",\"kmod-mt7915e\":\"5.15.155+2023-09-11-f..d-2\",\"kmod-net-selftests\":\"5.15.155-1\",\"kmod-nf-conncount\":\"5.15.155-1\",\"kmod-nf-conntrack\":\"5.15.155-1\",\"kmod-nf-conntrack6\":\"5.15.155-1\",\"kmod-nf-flow\":\"5.15.155-1\",\"kmod-nf-ipt\":\"5.15.155-1\",\"kmod-nf-ipt6\":\"5.15.155-1\",\"kmod-nf-log\":\"5.15.155-1\",\"kmod-nf-log6\":\"5.15.155-1\",\"kmod-nf-nat\":\"5.15.155-1\",\"kmod-nf-nathelper-extra\":\"5.15.155-1\",\"kmod-nf-reject\":\"5.15.155-1\",\"kmod-nf-reject6\":\"5.15.155-1\",\"kmod-nf-socket\":\"5.15.155-1\",\"kmod-nf-tproxy\":\"5.15.155-1\",\"kmod-nfnetlink\":\"5.15.155-1\",\"kmod-nfnetlink-queue\":\"5.15.155-1\",\"kmod-nft-arp\":\"5.15.155-1\",\"kmod-nft-bridge\":\"5.15.155-1\",\"kmod-nft-compat\":\"5.15.155-1\",\"kmod-nft-connlimit\":\"5.15.155-1\",\"kmod-nft-core\":\"5.15.155-1\",\"kmod-nft-dup-inet\":\"5.15.155-1\",\"kmod-nft-fib\":\"5.15.155-1\",\"kmod-nft-nat\":\"5.15.155-1\",\"kmod-nft-netdev\":\"5.15.155-1\",\"kmod-nft-offload\":\"5.15.155-1\",\"kmod-nft-queue\":\"5.15.155-1\",\"kmod-nft-socket\":\"5.15.155-1\",\"kmod-nft-tproxy\":\"5.15.155-1\",\"kmod-nft-xfrm\":\"5.15.155-1\",\"kmod-nls-base\":\"5.15.155-1\",\"kmod-phy-ax88796b\":\"5.15.155-1\",\"kmod-ppp\":\"5.15.155-1\",\"kmod-pppoe\":\"5.15.155-1\",\"kmod-pppox\":\"5.15.155-1\",\"kmod-sched-core\":\"5.15.155-1\",\"kmod-scsi-core\":\"5.15.155-1\",\"kmod-slhc\":\"5.15.155-1\",\"kmod-thermal\":\"5.15.155-1\",\"kmod-tun\":\"5.15.155-1\",\"kmod-udptunnel4\":\"5.15.155-1\",\"kmod-udptunnel6\":\"5.15.155-1\",\"kmod-usb-acm\":\"5.15.155-1\",\"kmod-usb-core\":\"5.15.155-1\",\"kmod-usb-net\":\"5.15.155-1\",\"kmod-usb-net-asix\":\"5.15.155-1\",\"kmod-usb-net-asix-ax88179\":\"5.15.155-1\",\"kmod-usb-net-cdc-ether\":\"5.15.155-1\",\"kmod-usb-net-cdc-mbim\":\"5.15.155-1\",\"kmod-usb-net-cdc-ncm\":\"5.15.155-1\",\"kmod-usb-net-huawei-cdc-ncm\":\"5.15.155-1\",\"kmod-usb-net-ipheth\":\"5.15.155-1\",\"kmod-usb-net-qmi-wwan\":\"5.15.155-1\",\"kmod-usb-net-rndis\":\"5.15.155-1\",\"kmod-usb-net-sierrawireless\":\"5.15.155-1\",\"kmod-usb-serial\":\"5.15.155-1\",\"kmod-usb-serial-option\":\"5.15.155-1\",\"kmod-usb-serial-sierrawireless\":\"5.15.155-1\",\"kmod-usb-serial-wwan\":\"5.15.155-1\",\"kmod-usb-storage\":\"5.15.155-1\",\"kmod-usb-wdm\":\"5.15.155-1\",\"l2tpv3\":\"v4.0.0-1\",\"libatomic1\":\"12.3.0-4\",\"libblobmsg-json20230523\":\"2023-05-23-75a3b870-1\",\"libbpf1\":\"1.2.2-1\",\"libc\":\"1.2.4-4\",\"libcap\":\"2.69-1\",\"libcares\":\"1.27.0-1\",\"libcurl4\":\"8.7.1-r1\",\"libelf1\":\"0.189-1\",\"libevent2-7\":\"2.1.12-1\",\"libgcc1\":\"12.3.0-4\",\"libgmp10\":\"6.2.1-1\",\"libimobiledevice\":\"1.3.0-2\",\"libiptext-nft0\":\"1.8.8-2\",\"libiptext0\":\"1.8.8-2\",\"libiptext6-0\":\"1.8.8-2\",\"libiwinfo-data\":\"2023-07-01-ca79f641-1\",\"libiwinfo-lua\":\"2023-07-01-ca79f641-1\",\"libiwinfo20230701\":\"2023-07-01-ca79f641-1\",\"libjson-c5\":\"0.16-3\",\"libjson-script20230523\":\"2023-05-23-75a3b870-1\",\"liblua5.1.5\":\"5.1.5-11\",\"liblucihttp-lua\":\"2023-03-15-9b5b683f-1\",\"liblucihttp-ucode\":\"2023-03-15-9b5b683f-1\",\"liblucihttp0\":\"2023-03-15-9b5b683f-1\",\"libmbedtls12\":\"2.28.7-2\",\"libmnl0\":\"1.0.5-1\",\"libmosquitto-ssl\":\"2.0.18-2\",\"libnetfilter-queue1\":\"1.0.5-4\",\"libnfnetlink0\":\"1.0.2-1\",\"libnftnl11\":\"1.2.6-1\",\"libnghttp2-14\":\"1.57.0-1\",\"libnl-tiny1\":\"2023-07-27-bc92a280-1\",\"libopenssl-conf\":\"3.0.13-1\",\"libopenssl-legacy\":\"3.0.13-1\",\"libopenssl3\":\"3.0.13-1\",\"libpcap1\":\"1.10.4-1\",\"libplist\":\"2.2.0-3\",\"libpthread\":\"1.2.4-4\",\"librt\":\"1.2.4-4\",\"libubox-lua\":\"2023-05-23-75a3b870-1\",\"libubox20230523\":\"2023-05-23-75a3b870-1\",\"libubus-lua\":\"2023-06-05-f787c97b-1\",\"libubus20230605\":\"2023-06-05-f787c97b-1\",\"libuci-lua\":\"df15dbb1-1\",\"libuci20130104\":\"df15dbb1-1\",\"libuclient20201210\":\"2023-04-13-007d9454-1\",\"libucode20230711\":\"2023-11-07-a6e75e02-1\",\"libusb-1.0-0\":\"1.0.26-3\",\"libusbmuxd\":\"2.0.2-1\",\"libustream-mbedtls20201210\":\"2023-02-25-498f6e26-1\",\"libxml2\":\"2.11.4-1\",\"libxtables12\":\"1.8.8-2\",\"lldpd\":\"1.0.17-1\",\"logd\":\"2022-08-13-4c7b720b-2\",\"lua\":\"5.1.5-11\",\"lua-bit32\":\"5.3.0-1\",\"lua-mosquitto\":\"0.4.1-1\",\"luaposix\":\"35.1-1\",\"luasocket\":\"3.1.0-1\",\"luci\":\"git-24.327.84347-ef27870\",\"luci-app-cpeagent\":\"git-25.194.51065-7e8613e-1\",\"luci-app-firewall\":\"git-24.327.84347-ef27870\",\"luci-app-opkg\":\"git-24.327.84347-ef27870\",\"luci-app-wmsnmpd\":\"git-25.194.51065-7e8613e-1\",\"luci-base\":\"git-24.327.84347-ef27870\",\"luci-compat\":\"git-24.327.84347-ef27870\",\"luci-compat-tool-status\":\"git-25.194.51065-7e8613e-1\",\"luci-i18n-base-ru\":\"git-24.327.84347-ef27870\",\"luci-i18n-cpeagent-ru\":\"git-25.194.51065-7e8613e-1\",\"luci-i18n-firewall-ru\":\"git-24.327.84347-ef27870\",\"luci-i18n-opkg-ru\":\"git-24.327.84347-ef27870\",\"luci-i18n-wmsnmpd-ru\":\"git-25.194.51065-7e8613e-1\",\"luci-lib-base\":\"git-24.327.84347-ef27870\",\"luci-lib-ip\":\"git-24.327.84347-ef27870\",\"luci-lib-ipkg\":\"git-24.327.84347-ef27870\",\"luci-lib-jsonc\":\"git-24.327.84347-ef27870\",\"luci-lib-nixio\":\"git-24.327.84347-ef27870\",\"luci-light\":\"git-24.327.84347-ef27870\",\"luci-lua-runtime\":\"git-24.327.84347-ef27870\",\"luci-mod-admin-full\":\"git-24.327.84347-ef27870\",\"luci-mod-network\":\"git-24.327.84347-ef27870\",\"luci-mod-status\":\"git-24.327.84347-ef27870\",\"luci-mod-system\":\"git-24.327.84347-ef27870\",\"luci-proto-ipv6\":\"git-24.327.84347-ef27870\",\"luci-proto-ppp\":\"git-24.327.84347-ef27870\",\"luci-ssl\":\"git-24.327.84347-ef27870\",\"luci-theme-bootstrap\":\"git-24.327.84347-ef27870\",\"luci-theme-qtech-1907\":\"git-25.194.51065-7e8613e-1\",\"mtd\":\"26\",\"netifd\":\"2024-01-04-c18cc79d-2\",\"nftables-json\":\"1.0.8-1\",\"odhcp6c\":\"2023-05-12-bcd28363-20\",\"odhcpd-ipv6only\":\"2023-10-24-d8118f6e-1\",\"openwrt-keyring\":\"2022-03-25-62471e69-2\",\"opkg\":\"2022-02-24-d038e5b6-2\",\"ppp\":\"2.4.9.git-2021-01-04-4\",\"ppp-mod-pppoe\":\"2.4.9.git-2021-01-04-4\",\"procd\":\"2023-06-25-2db83655-2\",\"procd-seccomp\":\"2023-06-25-2db83655-2\",\"procd-ujail\":\"2023-06-25-2db83655-2\",\"px5g-mbedtls\":\"10\",\"resolveip\":\"2\",\"rpcd\":\"2023-07-01-c07ab2f9-1\",\"rpcd-mod-file\":\"2023-07-01-c07ab2f9-1\",\"rpcd-mod-iwinfo\":\"2023-07-01-c07ab2f9-1\",\"rpcd-mod-luci\":\"20240305-1\",\"rpcd-mod-rrdns\":\"20170710\",\"rpcd-mod-ucode\":\"2023-07-01-c07ab2f9-1\",\"rrm-nr\":\"v1.1.1-1\",\"shadow-common\":\"4.8.1-3\",\"shadow-groupadd\":\"4.8.1-3\",\"shadow-useradd\":\"4.8.1-3\",\"shadow-utils\":\"4.8.1-3\",\"strongswan\":\"5.9.11-2\",\"strongswan-charon\":\"5.9.11-2\",\"strongswan-ipsec\":\"5.9.11-2\",\"strongswan-minimal\":\"5.9.11-2\",\"strongswan-mod-aes\":\"5.9.11-2\",\"strongswan-mod-gmp\":\"5.9.11-2\",\"strongswan-mod-hmac\":\"5.9.11-2\",\"strongswan-mod-kernel-netlink\":\"5.9.11-2\",\"strongswan-mod-mgf1\":\"5.9.11-2\",\"strongswan-mod-openssl\":\"5.9.11-2\",\"strongswan-mod-pem\":\"5.9.11-2\",\"strongswan-mod-pubkey\":\"5.9.11-2\",\"strongswan-mod-random\":\"5.9.11-2\",\"strongswan-mod-sha1\":\"5.9.11-2\",\"strongswan-mod-socket-default\":\"5.9.11-2\",\"strongswan-mod-stroke\":\"5.9.11-2\",\"strongswan-mod-updown\":\"5.9.11-2\",\"strongswan-mod-x509\":\"5.9.11-2\",\"strongswan-mod-xcbc\":\"5.9.11-2\",\"sudo\":\"1.9.14p3-1\",\"tc-tiny\":\"6.3.0-1\",\"tcpdump\":\"4.99.4-1\",\"ubi-utils\":\"2.1.5-1\",\"ubox\":\"2022-08-13-4c7b720b-2\",\"ubus\":\"2023-06-05-f787c97b-1\",\"ubusd\":\"2023-06-05-f787c97b-1\",\"uci\":\"df15dbb1-1\",\"uclient-fetch\":\"2023-04-13-007d9454-1\",\"ucode\":\"2023-11-07-a6e75e02-1\",\"ucode-mod-fs\":\"2023-11-07-a6e75e02-1\",\"ucode-mod-html\":\"1\",\"ucode-mod-lua\":\"1\",\"ucode-mod-math\":\"2023-11-07-a6e75e02-1\",\"ucode-mod-nl80211\":\"2023-11-07-a6e75e02-1\",\"ucode-mod-rtnl\":\"2023-11-07-a6e75e02-1\",\"ucode-mod-ubus\":\"2023-11-07-a6e75e02-1\",\"ucode-mod-uci\":\"2023-11-07-a6e75e02-1\",\"ucode-mod-uloop\":\"2023-11-07-a6e75e02-1\",\"uhttpd\":\"2023-06-25-34a8a74d-2\",\"uhttpd-mod-ubus\":\"2023-06-25-34a8a74d-2\",\"umbim\":\"2022-08-13-146bc77c-24\",\"umdns\":\"2024-03-04-7c675979-1\",\"uqmi\":\"2022-10-20-c8c9f105-1\",\"urandom-seed\":\"3\",\"urngd\":\"2023-11-01-44365eb1-1\",\"usb-modeswitch\":\"2022-02-24-3c8595a4-1\",\"usign\":\"2020-05-23-f1f65026-1\",\"uuid\":\"0.2.0-1\",\"wimark-baseconfig\":\"v12.2.0-1\",\"wimark-cli\":\"v1.2.13-1\",\"wimark-reboot\":\"v1.0.0-1\",\"wimark-selfupgrade\":\"v8.0.0-1\",\"wimark-stdlib-lua\":\"v1.0.2-1\",\"wireless-regdb\":\"2024.01.23-1\",\"wmcap\":\"v1.0.2-1\",\"wmsnmpd\":\"v2.0.6-1\",\"wpad-openssl\":\"2023-09-08-e5ccbfc6-7\",\"wtm\":\"v1.1.0-1\",\"wwan\":\"2019-04-29-6\",\"xtables-nft\":\"1.8.8-2\",\"zlib\":\"1.2.13-1\"},\"Statics\":{\"acl\":{\"version\":\"1.15\",\"commit\":\"e\",\"build\":2},\"cpeagent\":{\"version\":\"1.15\",\"commit\":\"f3c33c83737d355398d2eed4d6e4eb21e2355430\",\"build\":2},\"dhcp-cap\":{\"version\":\"1.15\",\"commit\":\"e\",\"build\":2},\"eth_acct\":{\"version\":\"1.15\",\"commit\":\"e\",\"build\":2},\"firmware\":{\"version\":\"1.15\",\"commit\":\"e\",\"build\":2},\"get\":{\"version\":\"1.15\",\"commit\":\"e\",\"build\":2},\"l2portal\":{\"version\":\"1.15\",\"commit\":\"e\",\"build\":2},\"lbs\":{\"version\":\"1.15\",\"commit\":\"e\",\"build\":2},\"logging\":{\"version\":\"1.15\",\"commit\":\"e\",\"build\":2},\"netfilter\":{\"version\":\"1.15\",\"commit\":\"e\",\"build\":2},\"network\":{\"version\":\"1.15\",\"commit\":\"e\",\"build\":2},\"ntp\":{\"version\":\"1.15\",\"commit\":\"e\",\"build\":2},\"scanning\":{\"version\":\"1.15\",\"commit\":\"e\",\"build\":2},\"services\":{\"version\":\"1.15\",\"commit\":\"e\",\"build\":2},\"snmp\":{\"version\":\"1.15\",\"commit\":\"e\",\"build\":2},\"statistic\":{\"version\":\"1.15\",\"commit\":\"e\",\"build\":2},\"system\":{\"version\":\"1.15\",\"commit\":\"e\",\"build\":2},\"tc\":{\"version\":\"1.15\",\"commit\":\"e\",\"build\":2},\"uci\":{\"version\":\"1.15\",\"commit\":\"f3c33c83737d355398d2eed4d6e4eb21e2355430\",\"build\":2},\"wids\":{\"version\":\"1.15\",\"commit\":\"e\",\"build\":2},\"wifi\":{\"version\":\"1.15\",\"commit\":\"e\",\"build\":2}}}","time":"2026-07-17T17:14:25Z","message":"get value from context"}
ink-queue\":\"5.15.155-1\",\"kmod-nft-arp\":\"5.15.155-1\",\"kmod-nft-bridge\":\"5.15.155-1\",\"kmod-nft-compat\":\"5.15.155-1\",\"kmod-nft-connlimit\":\"5.15.155-1\",\"kmod-nft-core\":\"5.15.155-1\",\"kmod-nft-dup-inet\":\"5.15.155-1\",\"kmod-nft-fib\":\"5.15.155-1\",\"kmod-nft-nat\":\"5.15.155-1\",\"kmod-nft-netdev\":\"5.15.155-1\",\"kmod-nft-offload\":\"5.15.155-1\",\"kmod-nft-queue\":\"5.15.155-1\",\"kmod-nft-socket\":\"5.15.155-1\",\"kmod-nft-tproxy\":\"5.15.155-1\",\"kmod-nft-xfrm\":\"5.15.155-1\",\"kmod-nls-base\":\"5.15.155-1\",\"kmod-phy-ax88796b\":\"5.15.155-1\",\"kmod-ppp\":\"5.15.155-1\",\"kmod-pppoe\":\"5.15.155-1\",\"kmod-pppox\":\"5.15.155-1\",\"kmod-sched-core\":\"5.15.155-1\",\"kmod-scsi-core\":\"5.15.155-1\",\"kmod-slhc\":\"5.15.155-1\",\"kmod-thermal\":\"5.15.155-1\",\"kmod-tun\":\"5.15.155-1\",\"kmod-udptunnel4\":\"5.15.155-1\",\"kmod-udptunnel6\":\"5.15.155-1\",\"kmod-usb-acm\":\"5.15.155-1\",\"kmod-usb-core\":\"5.15.155-1\",\"kmod-usb-net\":\"5.15.155-1\",\"kmod-usb-net-asix\":\"5.15.155-1\",\"kmod-usb-net-asix-ax88179\":\"5.15.155-1\",\"kmod-usb-net-cdc-ether\":\"5.15.155-1\",\"kmod-usb-net-cdc-mbim\":\"5.15.155-1\",\"kmod-usb-net-cdc-ncm\":\"5.15.155-1\",\"kmod-usb-net-huawei-cdc-ncm\":\"5.15.155-1\",\"kmod-usb-net-ipheth\":\"5.15.155-1\",\"kmod-usb-net-qmi-wwan\":\"5.15.155-1\",\"kmod-usb-net-rndis\":\"5.15.155-1\",\"kmod-usb-net-sierrawireless\":\"5.15.155-1\",\"kmod-usb-serial\":\"5.15.155-1\",\"kmod-usb-serial-option\":\"5.15.155-1\",\"kmod-usb-serial-sierrawireless\":\"5.15.155-1\",\"kmod-usb-serial-wwan\":\"5.15.155-1\",\"kmod-usb-storage\":\"5.15.155-1\",\"kmod-usb-wdm\":\"5.15.155-1\",\"l2tpv3\":\"v4.0.0-1\",\"libatomic1\":\"12.3.0-4\",\"libblobmsg-json20230523\":\"2023-05-23-75a3b870-1\",\"libbpf1\":\"1.2.2-1\",\"libc\":\"1.2.4-4\",\"libcap\":\"2.69-1\",\"libcares\":\"1.27.0-1\",\"libcurl4\":\"8.7.1-r1\",\"libelf1\":\"0.189-1\",\"libevent2-7\":\"2.1.12-1\",\"libgcc1\":\"12.3.0-4\",\"libgmp10\":\"6.2.1-1\",\"libimobiledevice\":\"1.3.0-2\",\"libiptext-nft0\":\"1.8.8-2\",\"libiptext0\":\"1.8.8-2\",\"libiptext6-0\":\"1.8.8-2\",\"libiwinfo-data\":\"2023-07-01-ca79f641-1\",\"libiwinfo-lua\":\"2023-07-01-ca79f641-1\",\"libiwinfo20230701\":\"2023-07-01-ca79f641-1\",\"libjson-c5\":\"0.16-3\",\"libjson-script20230523\":\"2023-05-23-75a3b870-1\",\"liblua5.1.5\":\"5.1.5-11\",\"liblucihttp-lua\":\"2023-03-15-9b5b683f-1\",\"liblucihttp-ucode\":\"2023-03-15-9b5b683f-1\",\"liblucihttp0\":\"2023-03-15-9b5b683f-1\",\"libmbedtls12\":\"2.28.7-2\",\"libmnl0\":\"1.0.5-1\",\"libmosquitto-ssl\":\"2.0.18-2\",\"libnetfilter-queue1\":\"1.0.5-4\",\"libnfnetlink0\":\"1.0.2-1\",\"libnftnl11\":\"1.2.6-1\",\"libnghttp2-14\":\"1.57.0-1\",\"libnl-tiny1\":\"2023-07-27-bc92a280-1\",\"libopenssl-conf\":\"3.0.13-1\",\"libopenssl-legacy\":\"3.0.13-1\",\"libopenssl3\":\"3.0.13-1\",\"libpcap1\":\"1.10.4-1\",\"libplist\":\"2.2.0-3\",\"libpthread\":\"1.2.4-4\",\"librt\":\"1.2.4-4\",\"libubox-lua\":\"2023-05-23-75a3b870-1\",\"libubox20230523\":\"2023-05-23-75a3b870-1\",\"libubus-lua\":\"2023-06-05-f787c97b-1\",\"libubus20230605\":\"2023-06-05-f787c97b-1\",\"libuci-lua\":\"df15dbb1-1\",\"libuci20130104\":\"df15dbb1-1\",\"libuclient20201210\":\"2023-04-13-007d9454-1\",\"libucode20230711\":\"2023-11-07-a6e75e02-1\",\"libusb-1.0-0\":\"1.0.26-3\",\"libusbmuxd\":\"2.0.2-1\",\"libustream-mbedtls20201210\":\"2023-02-25-498f6e26-1\",\"libxml2\":\"2.11.4-1\",\"libxtables12\":\"1.8.8-2\",\"lldpd\":\"1.0.17-1\",\"logd\":\"2022-08-13-4c7b720b-2\",\"lua\":\"5.1.5-11\",\"lua-bit32\":\"5.3.0-1\",\"lua-mosquitto\":\"0.4.1-1\",\"luaposix\":\"35.1-1\",\"luasocket\":\"3.1.0-1\",\"luci\":\"git-24.327.84347-ef27870\",\"luci-app-cpeagent\":\"git-25.194.51065-7e8613e-1\",\"luci-app-firewall\":\"git-24.327.84347-ef27870\",\"luci-app-opkg\":\"git-24.327.84347-ef27870\",\"luci-app-wmsnmpd\":\"git-25.194.51065-7e8613e-1\",\"luci-base\":\"git-24.327.84347-ef27870\",\"luci-compat\":\"git-24.327.84347-ef27870\",\"luci-compat-tool-status\":\"git-25.194.51065-7e8613e-1\",\"luci-i18n-base-ru\":\"git-24.327.84347-ef27870\",\"luci-i18n-cpeagent-ru\":\"git-25.194.51065-7e8613e-1\",\"luci-i18n-firewall-ru\":\"git-24.327.84347-ef27870\",\"luci-i18n-opkg-ru\":\"git-24.327.84347-ef27870\",\"luci-i18n-wmsnmpd-ru\":\"git-25.194.51065-7e8613e-1\",\"luci-lib-base\":\"git-24.327.84347-ef27870\",\"luci-lib-ip\":\"git-24.327.84347-ef27870\",\"luci-lib-ipkg\":\"git-24.327.84347-ef27870\",\"luci-lib-jsonc\":\"git-24.327.84347-ef27870\",\"luci-lib-nixio\":\"git-24.327.84347-ef27870\",\"luci-light\":\"git-24.327.84347-ef27870\",\"luci-lua-runtime\":\"git-24.327.84347-ef27870\",\"luci-mod-admin-full\":\"git-24.327.84347-ef27870\",\"luci-mod-network\":\"git-24.327.84347-ef27870\",\"luci-mod-status\":\"git-24.327.84347-ef27870\",\"luci-mod-system\":\"git-24.327.84347-ef27870\",\"luci-proto-ipv6\":\"git-24.327.84347-ef27870\",\"luci-proto-ppp\":\"git-24.327.84347-ef27870\",\"luci-ssl\":\"git-24.327.84347-ef27870\",\"luci-theme-bootstrap\":\"git-24.327.84347-ef27870\",\"luci-theme-qtech-1907\":\"git-25.194.51065-7e8613e-1\",\"mtd\":\"26\",\"netifd\":\"2024-01-04-c18cc79d-2\",\"nftables-json\":\"1.0.8-1\",\"odhcp6c\":\"2023-05-12-bcd28363-20\",\"odhcpd-ipv6only\":\"2023-10-24-d8118f6e-1\",\"openwrt-keyring\":\"2022-03-25-62471e69-2\",\"opkg\":\"2022-02-24-d038e5b6-2\",\"ppp\":\"2.4.9.git-2021-01-04-4\",\"ppp-mod-pppoe\":\"2.4.9.git-2021-01-04-4\",\"procd\":\"2023-06-25-2db83655-2\",\"procd-seccomp\":\"2023-06-25-2db83655-2\",\"procd-ujail\":\"2023-06-25-2db83655-2\",\"px5g-mbedtls\":\"10\",\"resolveip\":\"2\",\"rpcd\":\"2023-07-01-c07ab2f9-1\",\"rpcd-mod-file\":\"2023-07-01-c07ab2f9-1\",\"rpcd-mod-iwinfo\":\"2023-07-01-c07ab2f9-1\",\"rpcd-mod-luci\":\"20240305-1\",\"rpcd-mod-rrdns\":\"20170710\",\"rpcd-mod-ucode\":\"2023-07-01-c07ab2f9-1\",\"rrm-nr\":\"v1.1.1-1\",\"shadow-common\":\"4.8.1-3\",\"shadow-groupadd\":\"4.8.1-3\",\"shadow-useradd\":\"4.8.1-3\",\"shadow-utils\":\"4.8.1-3\",\"strongswan\":\"5.9.11-2\",\"strongswan-charon\":\"5.9.11-2\",\"strongswan-ipsec\":\"5.9.11-2\",\"strongswan-minimal\":\"5.9.11-2\",\"strongswan-mod-aes\":\"5.9.11-2\",\"strongswan-mod-gmp\":\"5.9.11-2\",\"strongswan-mod-hmac\":\"5.9.11-2\",\"strongswan-mod-kernel-netlink\":\"5.9.11-2\",\"strongswan-mod-mgf1\":\"5.9.11-2\",\"strongswan-mod-openssl\":\"5.9.11-2\",\"strongswan-mod-pem\":\"5.9.11-2\",\"strongswan-mod-pubkey\":\"5.9.11-2\",\"strongswan-mod-random\":\"5.9.11-2\",\"strongswan-mod-sha1\":\"5.9.11-2\",\"strongswan-mod-socket-default\":\"5.9.11-2\",\"strongswan-mod-stroke\":\"5.9.11-2\",\"strongswan-mod-updown\":\"5.9.11-2\",\"strongswan-mod-x509\":\"5.9.11-2\",\"strongswan-mod-xcbc\":\"5.9.11-2\",\"sudo\":\"1.9.14p3-1\",\"tc-tiny\":\"6.3.0-1\",\"tcpdump\":\"4.99.4-1\",\"ubi-utils\":\"2.1.5-1\",\"ubox\":\"2022-08-13-4c7b720b-2\",\"ubus\":\"2023-06-05-f787c97b-1\",\"ubusd\":\"2023-06-05-f787c97b-1\",\"uci\":\"df15dbb1-1\",\"uclient-fetch\":\"2023-04-13-007d9454-1\",\"ucode\":\"2023-11-07-a6e75e02-1\",\"ucode-mod-fs\":\"2023-11-07-a6e75e02-1\",\"ucode-mod-html\":\"1\",\"ucode-mod-lua\":\"1\",\"ucode-mod-math\":\"2023-11-07-a6e75e02-1\",\"ucode-mod-nl80211\":\"2023-11-07-a6e75e02-1\",\"ucode-mod-rtnl\":\"2023-11-07-a6e75e02-1\",\"ucode-mod-ubus\":\"2023-11-07-a6e75e02-1\",\"ucode-mod-uci\":\"2023-11-07-a6e75e02-1\",\"ucode-mod-uloop\":\"2023-11-07-a6e75e02-1\",\"uhttpd\":\"2023-06-25-34a8a74d-2\",\"uhttpd-mod-ubus\":\"2023-06-25-34a8a74d-2\",\"umbim\":\"2022-08-13-146bc77c-24\",\"umdns\":\"2024-03-04-7c675979-1\",\"uqmi\":\"2022-10-20-c8c9f105-1\",\"urandom-seed\":\"3\",\"urngd\":\"2023-11-01-44365eb1-1\",\"usb-modeswitch\":\"2022-02-24-3c8595a4-1\",\"usign\":\"2020-05-23-f1f65026-1\",\"uuid\":\"0.2.0-1\",\"wimark-baseconfig\":\"v12.2.0-1\",\"wimark-cli\":\"v1.2.13-1\",\"wimark-reboot\":\"v1.0.0-1\",\"wimark-selfupgrade\":\"v8.0.0-1\",\"wimark-stdlib-lua\":\"v1.0.2-1\",\"wireless-regdb\":\"2024.01.23-1\",\"wmcap\":\"v1.0.2-1\",\"wmsnmpd\":\"v2.0.6-1\",\"wpad-openssl\":\"2023-09-08-e5ccbfc6-7\",\"wtm\":\"v1.1.0-1\",\"wwan\":\"2019-04-29-6\",\"xtables-nft\":\"1.8.8-2\",\"zlib\":\"1.2.13-1\"},\"Statics\":{\"acl\":{\"version\":\"1.15\",\"commit\":\"e\",\"build\":2},\"cpeagent\":{\"version\":\"1.15\",\"commit\":\"f3c33c83737d355398d2eed4d6e4eb21e2355430\",\"build\":2},\"dhcp-cap\":{\"version\":\"1.15\",\"commit\":\"e\",\"build\":2},\"eth_acct\":{\"version\":\"1.15\",\"commit\":\"e\",\"build\":2},\"firmware\":{\"version\":\"1.15\",\"commit\":\"e\",\"build\":2},\"get\":{\"version\":\"1.15\",\"commit\":\"e\",\"build\":2},\"l2portal\":{\"version\":\"1.15\",\"commit\":\"e\",\"build\":2},\"lbs\":{\"version\":\"1.15\",\"commit\":\"e\",\"build\":2},\"logging\":{\"version\":\"1.15\",\"commit\":\"e\",\"build\":2},\"netfilter\":{\"version\":\"1.15\",\"commit\":\"e\",\"build\":2},\"network\":{\"version\":\"1.15\",\"commit\":\"e\",\"build\":2},\"ntp\":{\"version\":\"1.15\",\"commit\":\"e\",\"build\":2},\"scanning\":{\"version\":\"1.15\",\"commit\":\"e\",\"build\":2},\"services\":{\"version\":\"1.15\",\"commit\":\"e\",\"build\":2},\"snmp\":{\"version\":\"1.15\",\"commit\":\"e\",\"build\":2},\"statistic\":{\"version\":\"1.15\",\"commit\":\"e\",\"build\":2},\"system\":{\"version\":\"1.15\",\"commit\":\"e\",\"build\":2},\"tc\":{\"version\":\"1.15\",\"commit\":\"e\",\"build\":2},\"uci\":{\"version\":\"1.15\",\"commit\":\"f3c33c83737d355398d2eed4d6e4eb21e2355430\",\"build\":2},\"wids\":{\"version\":\"1.15\",\"commit\":\"e\",\"build\":2},\"wifi\":{\"version\":\"1.15\",\"commit\":\"e\",\"build\":2}}}","time":"2026-07-17T17:14:26Z","message":"get value from context"}
{"level":"debug","key":"EXCHANGE","value":"{\"Request\":{\"T\":{\"SenderModule\":\"CONFIG\",\"SenderID\":\"\",\"ReceiverModule\":\"CPE\",\"ReceiverID\":\"4174f9dd-648f-0785-6640-08c6b3fbf0c2\",\"RequestID\":\"ea3258ac-925f-43da-88c1-0adb44ee5bd7\",\"Operation\":\"JSONRPC\",\"Tag\":\"\"},\"M\":{\"Contents\":[{\"jsonrpc\":\"2.0\",\"method\":\"uci:open_config\",\"id\":1},{\"jsonrpc\":\"2.0\",\"method\":\"uci:set\",\"params\":{\"wimark\":[\".redirect\",\".eth_acct\",\".wsmd\"],\"wireless\":[\".radius\"]},\"id\":2},{\"jsonrpc\":\"2.0\",\"method\":\"wifi:clear\",\"id\":3},{\"jsonrpc\":\"2.0\",\"method\":\"network:clean_l2tp\",\"params\":[true],\"id\":4},{\"jsonrpc\":\"2.0\",\"method\":\"acl:l2_clear_uci\",\"id\":5},{\"jsonrpc\":\"2.0\",\"method\":\"network:l2ap\",\"id\":6},{\"jsonrpc\":\"2.0\",\"method\":\"uci:set\",\"params\":{\"wimark\":{\".firmware\":{\"checksum\":\"\",\"file\":\"\",\"mode\":\"check\",\"storage\":\"\",\"timeout\":\"\"},\"broker\":{\"desc\":\"\",\"name\":\"Qtech-f0c2\"},\"dhcpcap\":{\".type\":\"dhcpcap\",\"crud_op\":\"\",\"enabled\":\"false\",\"model_name\":\"\",\"receiver\":\"\",\"receiver_id\":\"\",\"typefilter\":[\"ACK\",\"OFFER\"]},\"lbs\":{\".type\":\"lbs\",\"clear_delta\":\"30\",\"clear_timeout\":\"30\",\"crud_op\":\"\",\"empty_watcher\":\"false\",\"enabled\":\"false\",\"macfilter\":\"disable\",\"maclist\":null,\"max_cache_queue\":\"50\",\"max_quiet\":\"5\",\"model_name\":\"\",\"receiver\":\"\",\"receiver_id\":\"\",\"report_timeout\":\"30\"},\"logupload\":{\".type\":\"logupload\",\"debug\":\"false\",\"enabled\":\"false\",\"logupload_host\":\"10.3.30.26\",\"logupload_port\":\"514\",\"retry_interval\":\"5\"},\"radio0\":{\".type\":\"scanning\",\"enabled\":\"false\",\"report_timeout\":\"\",\"scan_timeout\":\"\",\"scan_times\":\"\"},\"radio1\":{\".type\":\"scanning\",\"enabled\":\"false\",\"report_timeout\":\"\",\"scan_timeout\":\"\",\"scan_times\":\"\"},\"statistic\":{\".type\":\"statistic\",\"crud_op\":\"\",\"enabled\":\"false\",\"model_name\":\"\",\"receiver\":\"\",\"receiver_id\":\"\",\"tag\":\"\",\"timeout\":\"30\"},\"wsmd\":{\"enabled\":\"\",\"timeout\":\"\"}},\"wireless\":{\"radio0\":{\".type\":\"wifi-device\",\"channel\":\"auto\",\"channels\":[1,6,11],\"country\":\"RU\",\"country_ie\":\"1\",\"disabled\":\"\",\"hostapd_options\":\"vendor_elements=851e00008f000f00ff03190051746563682d6630633200000000000000000000\",\"htmode\":\"HT20\",\"hwmode\":\"11g\",\"noscan\":\"0\",\"require_mode\":\"\",\"rssi_reject_assoc_rssi\":\"-90\",\"txpower\":\"\"},\"radio1\":{\".type\":\"wifi-device\",\"channel\":\"auto\",\"channels\":[36,40,44,48,132,136,140,149,153,157,161,165,52,56,60,144,64],\"country\":\"RU\",\"country_ie\":\"1\",\"disabled\":\"\",\"hostapd_options\":\"vendor_elements=851e00008f000f00ff03190051746563682d6630633200000000000000000000\",\"htmode\":\"VHT20\",\"hwmode\":\"11a\",\"noscan\":\"0\",\"require_mode\":\"\",\"rssi_reject_assoc_rssi\":\"-90\",\"txpower\":\"\"}},\"system\":{\".system\":{\".type\":\"system\",\"hostname\":\"Qtech-f0c2\",\"log_ip\":\"\",\"log_port\":\"\",\"log_prefix\":\"\",\"log_proto\":\"\",\"log_remote\":\"false\"},\"ntp\":{\".type\":\"timeserver\",\"enabled\":\"true\",\"server\":[\"10.3.30.26\"]}},\"network\":{},\"wmsnmpd\":{\"default\":{\"enabled\":\"false\",\"community\":\"\",\"location\":\"\",\"listen_interface\":\"\",\"interfaces\":[]}}},\"id\":7},{\"jsonrpc\":\"2.0\",\"method\":\"network:wan_access\",\"params\":[true,[\"lan\",\"\"]],\"id\":8},{\"jsonrpc\":\"2.0\",\"method\":\"wifi:add\",\"params\":{\"radio0ceab9273_4bd8_4c4e_b544_87446cc661dd\":{\".type\":\"wifi-iface\",\"ssid\":\"INDASTRY\",\"uuid\":\"ceab9273-4bd8-4c4e-b544-87446cc661dd\",\"device\":\"radio0\",\"hidden\":\"false\",\"mode\":\"ap\",\"auth_cache\":\"false\",\"ieee80211r\":\"false\",\"ieee80211k\":\"false\",\"ieee80211v\":\"false\",\"rrm_neighbor_report\":\"1\",\"rrm_beacon_report\":\"1\",\"wnm_sleep_mode\":\"0\",\"bss_transition\":\"0\",\"network\":\"lan\",\"macfilter\":\"disable\",\"proxy_arp\":\"1\",\"central\":\"0\",\"isolate\":\"false\",\"ownip\":\"10.3.30.26\",\"macaddr\":\"08:c6:b3:0f:0c:20\",\"ubus_acct_interval\":\"30\",\"nasid\":\"wimark\",\"acct_interval\":\"600\",\"encryption\":\"psk2+aes\",\"key\":\"12345678\",\"wmm\":\"true\",\"uapsd\":\"false\",\"wmm_tx_bk_aifs\":\"7\",\"wmm_tx_bk_cwmin\":\"32767\",\"wmm_tx_bk_cwmax\":\"+Inf\",\"wmm_tx_bk_burst\":\"0.0\",\"wmm_tx_be_aifs\":\"3\",\"wmm_tx_be_cwmin\":\"32767\",\"wmm_tx_be_cwmax\":\"9223372036854775808\",\"wmm_tx_be_burst\":\"0.0\",\"wmm_tx_vi_aifs\":\"1\",\"wmm_tx_vi_cwmin\":\"127\",\"wmm_tx_vi_cwmax\":\"32767\",\"wmm_tx_vi_burst\":\"3.0\",\"wmm_tx_vo_aifs\":\"1\",\"wmm_tx_vo_cwmin\":\"7\",\"wmm_tx_vo_cwmax\":\"127\",\"wmm_tx_vo_burst\":\"1.5\",\"wmm_ac_bk_aifs\":\"7\",\"wmm_ac_bk_cwmin\":\"4\",\"wmm_ac_bk_cwmax\":\"10\",\"wmm_ac_bk_txop\":\"\",\"wmm_ac_bk_acm\":\"false\",\"wmm_ac_be_aifs\":\"3\",\"wmm_ac_be_cwmin\":\"4\",\"wmm_ac_be_cwmax\":\"10\",\"wmm_ac_be_txop\":\"\",\"wmm_ac_be_acm\":\"false\",\"wmm_ac_vi_aifs\":\"2\",\"wmm_ac_vi_cwmin\":\"3\",\"wmm_ac_vi_cwmax\":\"4\",\"wmm_ac_vi_txop\":\"94\",\"wmm_ac_vi_acm\":\"false\",\"wmm_ac_vo_aifs\":\"2\",\"wmm_ac_vo_cwmin\":\"2\",\"wmm_ac_vo_cwmax\":\"3\",\"wmm_ac_vo_txop\":\"47\",\"wmm_ac_vo_acm\":\"false\",\"max_inactivity\":\"180\",\"disassoc_low_ack\":\"0\",\"mesh_id\":\"\",\"mesh_fwding\":\"\",\"band_steering\":\"false\",\"ft_over_ds\":\"0\",\"dae_client\":\"\",\"dae_secret\":\"\",\"dae_port\":\"\",\"signal_connect\":\"\",\"signal_stay\":\"-60\",\"signal_strikes\":\"3\",\"signal_poll_time\":\"5\",\"signal_drop_reason\":\"3\",\"pmk_r1_push\":\"\",\"ft_psk_generate_local\":\"0\",\"rrb_use_seq\":\"0\",\"ppsk\":\"\"},\"radio1ceab9273_4bd8_4c4e_b544_87446cc661dd\":{\".type\":\"wifi-iface\",\"ssid\":\"INDASTRY\",\"uuid\":\"ceab9273-4bd8-4c4e-b544-87446cc661dd\",\"device\":\"radio1\",\"hidden\":\"false\",\"mode\":\"ap\",\"auth_cache\":\"false\",\"ieee80211r\":\"false\",\"ieee80211k\":\"false\",\"ieee80211v\":\"false\",\"rrm_neighbor_report\":\"1\",\"rrm_beacon_report\":\"1\",\"wnm_sleep_mode\":\"0\",\"bss_transition\":\"0\",\"network\":\"lan\",\"macfilter\":\"disable\",\"proxy_arp\":\"1\",\"central\":\"0\",\"isolate\":\"false\",\"ownip\":\"10.3.30.26\",\"macaddr\":\"08:c6:b3:0f:0c:21\",\"ubus_acct_interval\":\"30\",\"nasid\":\"wimark\",\"acct_interval\":\"600\",\"encryption\":\"psk2+aes\",\"key\":\"12345678\",\"wmm\":\"true\",\"uapsd\":\"false\",\"wmm_tx_bk_aifs\":\"7\",\"wmm_tx_bk_cwmin\":\"32767\",\"wmm_tx_bk_cwmax\":\"+Inf\",\"wmm_tx_bk_burst\":\"0.0\",\"wmm_tx_be_aifs\":\"3\",\"wmm_tx_be_cwmin\":\"32767\",\"wmm_tx_be_cwmax\":\"9223372036854775808\",\"wmm_tx_be_burst\":\"0.0\",\"wmm_tx_vi_aifs\":\"1\",\"wmm_tx_vi_cwmin\":\"127\",\"wmm_tx_vi_cwmax\":\"32767\",\"wmm_tx_vi_burst\":\"3.0\",\"wmm_tx_vo_aifs\":\"1\",\"wmm_tx_vo_cwmin\":\"7\",\"wmm_tx_vo_cwmax\":\"127\",\"wmm_tx_vo_burst\":\"1.5\",\"wmm_ac_bk_aifs\":\"7\",\"wmm_ac_bk_cwmin\":\"4\",\"wmm_ac_bk_cwmax\":\"10\",\"wmm_ac_bk_txop\":\"\",\"wmm_ac_bk_acm\":\"false\",\"wmm_ac_be_aifs\":\"3\",\"wmm_ac_be_cwmin\":\"4\",\"wmm_ac_be_cwmax\":\"10\",\"wmm_ac_be_txop\":\"\",\"wmm_ac_be_acm\":\"false\",\"wmm_ac_vi_aifs\":\"2\",\"wmm_ac_vi_cwmin\":\"3\",\"wmm_ac_vi_cwmax\":\"4\",\"wmm_ac_vi_txop\":\"94\",\"wmm_ac_vi_acm\":\"false\",\"wmm_ac_vo_aifs\":\"2\",\"wmm_ac_vo_cwmin\":\"2\",\"wmm_ac_vo_cwmax\":\"3\",\"wmm_ac_vo_txop\":\"47\",\"wmm_ac_vo_acm\":\"false\",\"max_inactivity\":\"180\",\"disassoc_low_ack\":\"0\",\"mesh_id\":\"\",\"mesh_fwding\":\"\",\"band_steering\":\"false\",\"ft_over_ds\":\"0\",\"dae_client\":\"\",\"dae_secret\":\"\",\"dae_port\":\"\",\"signal_connect\":\"\",\"signal_stay\":\"-60\",\"signal_strikes\":\"3\",\"signal_poll_time\":\"5\",\"signal_drop_reason\":\"3\",\"pmk_r1_push\":\"\",\"ft_psk_generate_local\":\"0\",\"rrb_use_seq\":\"0\",\"ppsk\":\"\"}},\"id\":9},{\"jsonrpc\":\"2.0\",\"method\":\"acl:l3\",\"params\":[null],\"id\":10},{\"jsonrpc\":\"2.0\",\"method\":\"uci:apply_config\",\"id\":11},{\"jsonrpc\":\"2.0\",\"method\":\"tc:configure\",\"id\":12},{\"jsonrpc\":\"2.0\",\"method\":\"services:wmsnmpd\",\"id\":13},{\"jsonrpc\":\"2.0\",\"method\":\"services:umdns\",\"id\":14}]},\"Retain\":false,\"Error\":null,\"ReqID\":\"\"},\"Response\":{\"T\":{\"SenderModule\":\"CPE\",\"SenderID\":\"4174f9dd-648f-0785-6640-08c6b3fbf0c2\",\"ReceiverModule\":\"CONFIG\",\"ReceiverID\":\"\",\"RequestID\":\"ea3258ac-925f-43da-88c1-0adb44ee5bd7\"},\"M\":{\"Contents\":[{\"jsonrpc\":\"2.0\",\"id\":1},{\"jsonrpc\":\"2.0\",\"result\":true,\"id\":2},{\"jsonrpc\":\"2.0\",\"id\":3},{\"jsonrpc\":\"2.0\",\"id\":4},{\"jsonrpc\":\"2.0\",\"id\":5},{\"jsonrpc\":\"2.0\",\"id\":6},{\"jsonrpc\":\"2.0\",\"id\":7},{\"jsonrpc\":\"2.0\",\"id\":8},{\"jsonrpc\":\"2.0\",\"id\":9},{\"jsonrpc\":\"2.0\",\"result\":true,\"id\":10},{\"jsonrpc\":\"2.0\",\"result\":[{\"method\":\"acl:l2_from_uci\",\"result\":null},{\"method\":\"services:dhcpoptinj\",\"result\":null},{\"method\":\"network:reload\",\"result\":null}],\"id\":11},{\"jsonrpc\":\"2.0\",\"result\":{\"phy0-ap0\":{\"device\":\"radio0\",\"download\":\"no limit\",\"ssid\":\"INDASTRY\",\"upload\":\"no limit\"},\"phy1-ap0\":{\"device\":\"radio1\",\"download\":\"no limit\",\"ssid\":\"INDASTRY\",\"upload\":\"no limit\"}},\"id\":12},{\"jsonrpc\":\"2.0\",\"id\":13},{\"jsonrpc\":\"2.0\",\"id\":14}]},\"Retain\":false,\"Error\":null,\"ReqID\":\"ea3258ac-925f-43da-88c1-0adb44ee5bd7\"}}","time":"2026-07-17T17:14:29Z","message":"get value from context"}
{"level":"debug","key":"JSONRPC_RSP","value":"[{\"jsonrpc\":\"2.0\",\"id\":1},{\"jsonrpc\":\"2.0\",\"result\":true,\"id\":2},{\"jsonrpc\":\"2.0\",\"id\":3},{\"jsonrpc\":\"2.0\",\"id\":4},{\"jsonrpc\":\"2.0\",\"id\":5},{\"jsonrpc\":\"2.0\",\"id\":6},{\"jsonrpc\":\"2.0\",\"id\":7},{\"jsonrpc\":\"2.0\",\"id\":8},{\"jsonrpc\":\"2.0\",\"id\":9},{\"jsonrpc\":\"2.0\",\"result\":true,\"id\":10},{\"jsonrpc\":\"2.0\",\"result\":[{\"method\":\"acl:l2_from_uci\",\"result\":null},{\"method\":\"services:dhcpoptinj\",\"result\":null},{\"method\":\"network:reload\",\"result\":null}],\"id\":11},{\"jsonrpc\":\"2.0\",\"result\":{\"phy0-ap0\":{\"device\":\"radio0\",\"download\":\"no limit\",\"ssid\":\"INDASTRY\",\"upload\":\"no limit\"},\"phy1-ap0\":{\"device\":\"radio1\",\"download\":\"no limit\",\"ssid\":\"INDASTRY\",\"upload\":\"no limit\"}},\"id\":12},{\"jsonrpc\":\"2.0\",\"id\":13},{\"jsonrpc\":\"2.0\",\"id\":14}]","time":"2026-07-17T17:14:29Z","message":"get value from context"}
{"level":"debug","key":"JSONRPC_RSP","value":"[{\"jsonrpc\":\"2.0\",\"result\":null,\"id\":1},{\"jsonrpc\":\"2.0\",\"result\":true,\"id\":2},{\"jsonrpc\":\"2.0\",\"result\":null,\"id\":3},{\"jsonrpc\":\"2.0\",\"result\":null,\"id\":4},{\"jsonrpc\":\"2.0\",\"result\":null,\"id\":5},{\"jsonrpc\":\"2.0\",\"result\":null,\"id\":6},{\"jsonrpc\":\"2.0\",\"result\":null,\"id\":7},{\"jsonrpc\":\"2.0\",\"result\":null,\"id\":8},{\"jsonrpc\":\"2.0\",\"result\":null,\"id\":9},{\"jsonrpc\":\"2.0\",\"result\":true,\"id\":10},{\"jsonrpc\":\"2.0\",\"result\":[{\"method\":\"acl:l2_from_uci\",\"result\":null},{\"method\":\"services:dhcpoptinj\",\"result\":null},{\"method\":\"network:reload\",\"result\":null}],\"id\":11},{\"jsonrpc\":\"2.0\",\"result\":{\"phy0-ap0\":{\"device\":\"radio0\",\"download\":\"no limit\",\"ssid\":\"INDASTRY\",\"upload\":\"no limit\"},\"phy1-ap0\":{\"device\":\"radio1\",\"download\":\"no limit\",\"ssid\":\"INDASTRY\",\"upload\":\"no limit\"}},\"id\":12},{\"jsonrpc\":\"2.0\",\"result\":null,\"id\":13},{\"jsonrpc\":\"2.0\",\"result\":null,\"id\":14}]","time":"2026-07-17T17:14:29Z","message":"get value from context"}
{"level":"debug","key":"CPE","value":"{\"name\":\"Qtech-f0c2\",\"connected\":true,\"description\":\"\",\"model\":{\"id\":\"20b51049-5885-46b0-a7a4-7b7dd987e060\",\"name\":\"QTECH QWP-82\",\"short\":\"qtech,qwp-82\"},\"config_status\":\"ok\",\"last_error\":{\"module\":\"\",\"module_id\":\"\",\"type\":\"\",\"description\":\"\",\"recommendation\":\"\"},\"config\":{\"name\":\"\",\"description\":\"\",\"wifi\":{\"radio0\":{\"bandmode\":\"11g\",\"bandwidth\":\"HT20\",\"txpower\":\"\",\"mintxpower\":\"\",\"power\":{\"range\":[1,20],\"auto\":true},\"wlans\":[\"ceab9273-4bd8-4c4e-b544-87446cc661dd\"],\"channels\":[1,6,11],\"country\":\"RU\",\"country_ie\":0,\"maxclients\":0,\"scanningconfig\":{\"enabled\":false,\"reportperiod\":0,\"scantimeout\":0,\"scannumber\":0},\"require_mode\":\"off\",\"frequency\":\"2.4\",\"basic_rate\":\"\",\"supported_rates\":null,\"legacy_rates\":\"\",\"log_level\":\"\",\"max_inactivity\":0,\"cell_density\":0},\"radio1\":{\"bandmode\":\"11a\",\"bandwidth\":\"VHT20\",\"txpower\":\"\",\"mintxpower\":\"\",\"power\":{\"range\":[1,20],\"auto\":true},\"wlans\":[\"ceab9273-4bd8-4c4e-b544-87446cc661dd\"],\"channels\":[36,40,44,48,132,136,140,149,153,157,161,165,52,56,60,144,64],\"country\":\"RU\",\"country_ie\":0,\"maxclients\":0,\"scanningconfig\":{\"enabled\":false,\"reportperiod\":0,\"scantimeout\":0,\"scannumber\":0},\"require_mode\":\"off\",\"frequency\":\"5\",\"basic_rate\":\"\",\"supported_rates\":null,\"legacy_rates\":\"\",\"log_level\":\"\",\"max_inactivity\":0,\"cell_density\":0}},\"wired\":{\"lan\":{\"primary_vlan\":0,\"vlans\":null},\"wan\":{\"primary_vlan\":0,\"vlans\":null}},\"lbs_config\":{\"enabled\":false,\"reportperiod\":30,\"clienttimeout\":30,\"maxquiet\":5,\"maxcachequeue\":50,\"emptywatcher\":false,\"whitelist\":[],\"blacklist\":[],\"filtermode\":\"None\"},\"stats_config\":{\"enabled\":false,\"reportperiod\":30},\"log_config\":{\"log_ip\":\"\",\"log_prefix\":\"\",\"log_proto\":\"\",\"log_port\":0,\"enabled\":false},\"dhcpcap_config\":{\"msgtypefilter\":[],\"enabled\":false},\"firewall\":{\"l2_chain\":\"\",\"l3_filter\":{\"mac_list\":[],\"ip_list\":[]},\"wan_access_block\":false,\"nat_access\":false},\"firmware\":{\"file\":\"\",\"storage\":\"\",\"checksum\":\"\",\"timeout\":0,\"mode\":\"check\"},\"tunnels\":{},\"beeline_config\":{\"nas_ip\":\"192.168.12.159\"},\"wmsnmpd\":{\"default\":{\"enabled\":false,\"community\":\"\",\"location\":\"\",\"interfaces\":[]}},\"ntp_config\":{\"type\":\"timeserver\",\"enable\":true,\"servers\":[\"10.3.30.26\"]},\"wifi_lock\":false,\"gre_peer_addr\":\"\",\"net_manual\":{},\"wifi_manual\":{}},\"state\":{\"wifi\":{\"radio0\":{\"frequency\":\"2.4\",\"bandmode\":\"11g\",\"bandwidth\":\"HT20\",\"channel\":\"11\",\"txpower\":\"20\",\"enabled\":true,\"wlanstates\":{\"ceab9273-4bd8-4c4e-b544-87446cc661dd\":{\"state\":\"ENABLED\",\"virtual_iface\":\"phy0-ap0\",\"bssid\":\"08:C6:B3:0F:0C:20\"}}},\"radio1\":{\"frequency\":\"5\",\"bandmode\":\"11a\",\"bandwidth\":\"VHT20\",\"channel\":\"52\",\"txpower\":\"20\",\"enabled\":true,\"wlanstates\":{\"ceab9273-4bd8-4c4e-b544-87446cc661dd\":{\"state\":\"ENABLED\",\"virtual_iface\":\"phy1-ap0\",\"bssid\":\"08:C6:B3:0F:0C:21\"}}}},\"firmware\":{\"has_update\":false,\"current_md5\":\"\",\"version\":{\"version\":\"v1.15.2-e\",\"commit\":\"f3c33c83737d355398d2eed4d6e4eb21e2355430\",\"build\":0},\"features\":[\"acl\",\"cpeagent\",\"dhcp-cap\",\"ethernet-accounting\",\"firewall\",\"firmware\",\"get\",\"l2-portal-nft\",\"lbs\",\"logging\",\"logupload\",\"network\",\"nftables\",\"openwrt\",\"radius\",\"scanning\",\"snmp\",\"statistic\",\"tc\",\"ubus\",\"uci\",\"umdns\",\"wids\",\"wifi\",\"wired\",\"wired-support\",\"wpa3\"]},\"wan\":{\"iface\":\"lan\",\"proto\":\"static\"},\"l2tp_state\":{\"enabled\":true,\"host\":\"one\",\"host_addr\":\"192.168.12.154\",\"host_tunnel\":0,\"tunnel_type\":\"none\",\"local_addr\":\"192.168.12.159\",\"local_iface\":\"\",\"local_tunnel\":1},\"network\":{\"ipaddr\":\"192.168.12.159\",\"macaddr\":\"08:C6:B3:FB:F0:C2\",\"ipaddrs\":[{\"ipaddr\":\"192.168.12.159\",\"netmask\":\"255.255.255.\"}],\"gateway\":\"192.168.12.1\"},\"tunnels\":null,\"net_manual\":null,\"wifi_manual\":null,\"manufacturing_data\":{\"serial_number\":\"\",\"wlan_mac\":\"\"}},\"first_connection\":0,\"last_connection\":0,\"last_disconnection\":0,\"config_not_send\":false,\"latitude\":0,\"longitude\":0,\"tag\":\"\"}","time":"2026-07-17T17:14:29Z","message":"get value from context"}
{"level":"debug","key":"U_REQ","value":"{\"Request\":{},\"CpeStates\":{\"4174f9dd-648f-0785-6640-08c6b3fbf0c2\":{\"name\":\"Qtech-f0c2\",\"connected\":true,\"description\":\"\",\"model\":{\"id\":\"20b51049-5885-46b0-a7a4-7b7dd987e060\",\"name\":\"QTECH QWP-82\",\"short\":\"qtech,qwp-82\"},\"config_status\":\"ok\",\"last_error\":{\"module\":\"\",\"module_id\":\"\",\"type\":\"\",\"description\":\"\",\"recommendation\":\"\"},\"config\":{\"name\":\"\",\"description\":\"\",\"wifi\":{\"radio0\":{\"bandmode\":\"11g\",\"bandwidth\":\"HT20\",\"txpower\":\"\",\"mintxpower\":\"\",\"power\":{\"range\":[1,20],\"auto\":true},\"wlans\":[\"ceab9273-4bd8-4c4e-b544-87446cc661dd\"],\"channels\":[1,6,11],\"country\":\"RU\",\"country_ie\":0,\"maxclients\":0,\"scanningconfig\":{\"enabled\":false,\"reportperiod\":0,\"scantimeout\":0,\"scannumber\":0},\"require_mode\":\"off\",\"frequency\":\"2.4\",\"basic_rate\":\"\",\"supported_rates\":null,\"legacy_rates\":\"\",\"log_level\":\"\",\"max_inactivity\":0,\"cell_density\":0},\"radio1\":{\"bandmode\":\"11a\",\"bandwidth\":\"VHT20\",\"txpower\":\"\",\"mintxpower\":\"\",\"power\":{\"range\":[1,20],\"auto\":true},\"wlans\":[\"ceab9273-4bd8-4c4e-b544-87446cc661dd\"],\"channels\":[36,40,44,48,132,136,140,149,153,157,161,165,52,56,60,144,64],\"country\":\"RU\",\"country_ie\":0,\"maxclients\":0,\"scanningconfig\":{\"enabled\":false,\"reportperiod\":0,\"scantimeout\":0,\"scannumber\":0},\"require_mode\":\"off\",\"frequency\":\"5\",\"basic_rate\":\"\",\"supported_rates\":null,\"legacy_rates\":\"\",\"log_level\":\"\",\"max_inactivity\":0,\"cell_density\":0}},\"wired\":{\"lan\":{\"primary_vlan\":0,\"vlans\":null},\"wan\":{\"primary_vlan\":0,\"vlans\":null}},\"lbs_config\":{\"enabled\":false,\"reportperiod\":30,\"clienttimeout\":30,\"maxquiet\":5,\"maxcachequeue\":50,\"emptywatcher\":false,\"whitelist\":[],\"blacklist\":[],\"filtermode\":\"None\"},\"stats_config\":{\"enabled\":false,\"reportperiod\":30},\"log_config\":{\"log_ip\":\"\",\"log_prefix\":\"\",\"log_proto\":\"\",\"log_port\":0,\"enabled\":false},\"dhcpcap_config\":{\"msgtypefilter\":[],\"enabled\":false},\"firewall\":{\"l2_chain\":\"\",\"l3_filter\":{\"mac_list\":[],\"ip_list\":[]},\"wan_access_block\":false,\"nat_access\":false},\"firmware\":{\"file\":\"\",\"storage\":\"\",\"checksum\":\"\",\"timeout\":0,\"mode\":\"check\"},\"tunnels\":{},\"beeline_config\":{\"nas_ip\":\"192.168.12.159\"},\"wmsnmpd\":{\"default\":{\"enabled\":false,\"community\":\"\",\"location\":\"\",\"interfaces\":[]}},\"ntp_config\":{\"type\":\"timeserver\",\"enable\":true,\"servers\":[\"10.3.30.26\"]},\"wifi_lock\":false,\"gre_peer_addr\":\"\",\"net_manual\":{},\"wifi_manual\":{}},\"state\":{\"wifi\":{\"radio0\":{\"frequency\":\"2.4\",\"bandmode\":\"11g\",\"bandwidth\":\"HT20\",\"channel\":\"11\",\"txpower\":\"20\",\"enabled\":true,\"wlanstates\":{\"ceab9273-4bd8-4c4e-b544-87446cc661dd\":{\"state\":\"ENABLED\",\"virtual_iface\":\"phy0-ap0\",\"bssid\":\"08:C6:B3:0F:0C:20\"}}},\"radio1\":{\"frequency\":\"5\",\"bandmode\":\"11a\",\"bandwidth\":\"VHT20\",\"channel\":\"52\",\"txpower\":\"20\",\"enabled\":true,\"wlanstates\":{\"ceab9273-4bd8-4c4e-b544-87446cc661dd\":{\"state\":\"ENABLED\",\"virtual_iface\":\"phy1-ap0\",\"bssid\":\"08:C6:B3:0F:0C:21\"}}}},\"firmware\":{\"has_update\":false,\"current_md5\":\"\",\"version\":{\"version\":\"v1.15.2-e\",\"commit\":\"f3c33c83737d355398d2eed4d6e4eb21e2355430\",\"build\":0},\"features\":[\"acl\",\"cpeagent\",\"dhcp-cap\",\"ethernet-accounting\",\"firewall\",\"firmware\",\"get\",\"l2-portal-nft\",\"lbs\",\"logging\",\"logupload\",\"network\",\"nftables\",\"openwrt\",\"radius\",\"scanning\",\"snmp\",\"statistic\",\"tc\",\"ubus\",\"uci\",\"umdns\",\"wids\",\"wifi\",\"wired\",\"wired-support\",\"wpa3\"]},\"wan\":{\"iface\":\"lan\",\"proto\":\"static\"},\"l2tp_state\":{\"enabled\":true,\"host\":\"one\",\"host_addr\":\"192.168.12.154\",\"host_tunnel\":0,\"tunnel_type\":\"none\",\"local_addr\":\"192.168.12.159\",\"local_iface\":\"\",\"local_tunnel\":1},\"network\":{\"ipaddr\":\"192.168.12.159\",\"macaddr\":\"08:C6:B3:FB:F0:C2\",\"ipaddrs\":[{\"ipaddr\":\"192.168.12.159\",\"netmask\":\"255.255.255.\"}],\"gateway\":\"192.168.12.1\"},\"tunnels\":null,\"net_manual\":null,\"wifi_manual\":null,\"manufacturing_data\":{\"serial_number\":\"\",\"wlan_mac\":\"\"}},\"first_connection\":0,\"last_connection\":0,\"last_disconnection\":0,\"config_not_send\":false,\"latitude\":0,\"longitude\":0,\"tag\":\"\"}}}","time":"2026-07-17T17:14:29Z","message":"get value from context"}
{"level":"debug","job_id":"Divesage","U_REQ":{"Request":{},"CpeStates":{"4174f9dd-648f-0785-6640-08c6b3fbf0c2":{"name":"Qtech-f0c2","connected":true,"description":"","model":{"id":"20b51049-5885-46b0-a7a4-7b7dd987e060","name":"QTECH QWP-82","short":"qtech,qwp-82"},"config_status":"ok","last_error":{"module":"","module_id":"","type":"","description":"","recommendation":""},"config":{"name":"","description":"","wifi":{"radio0":{"bandmode":"11g","bandwidth":"HT20","txpower":"","mintxpower":"","power":{"range":[1,20],"auto":true},"wlans":["ceab9273-4bd8-4c4e-b544-87446cc661dd"],"channels":[1,6,11],"country":"RU","country_ie":0,"maxclients":0,"scanningconfig":{"enabled":false,"reportperiod":0,"scantimeout":0,"scannumber":0},"require_mode":"off","frequency":"2.4","basic_rate":"","supported_rates":null,"legacy_rates":"","log_level":"","max_inactivity":0,"cell_density":0},"radio1":{"bandmode":"11a","bandwidth":"VHT20","txpower":"","mintxpower":"","power":{"range":[1,20],"auto":true},"wlans":["ceab9273-4bd8-4c4e-b544-87446cc661dd"],"channels":[36,40,44,48,132,136,140,149,153,157,161,165,52,56,60,144,64],"country":"RU","country_ie":0,"maxclients":0,"scanningconfig":{"enabled":false,"reportperiod":0,"scantimeout":0,"scannumber":0},"require_mode":"off","frequency":"5","basic_rate":"","supported_rates":null,"legacy_rates":"","log_level":"","max_inactivity":0,"cell_density":0}},"wired":{"lan":{"primary_vlan":0,"vlans":null},"wan":{"primary_vlan":0,"vlans":null}},"lbs_config":{"enabled":false,"reportperiod":30,"clienttimeout":30,"maxquiet":5,"maxcachequeue":50,"emptywatcher":false,"whitelist":[],"blacklist":[],"filtermode":"None"},"stats_config":{"enabled":false,"reportperiod":30},"log_config":{"log_ip":"","log_prefix":"","log_proto":"","log_port":0,"enabled":false},"dhcpcap_config":{"msgtypefilter":[],"enabled":false},"firewall":{"l2_chain":"","l3_filter":{"mac_list":[],"ip_list":[]},"wan_access_block":false,"nat_access":false},"firmware":{"file":"","storage":"","checksum":"","timeout":0,"mode":"check"},"tunnels":{},"beeline_config":{"nas_ip":"192.168.12.159"},"wmsnmpd":{"default":{"enabled":false,"community":"","location":"","interfaces":[]}},"ntp_config":{"type":"timeserver","enable":true,"servers":["10.3.30.26"]},"wifi_lock":false,"gre_peer_addr":"","net_manual":{},"wifi_manual":{}},"state":{"wifi":{"radio0":{"frequency":"2.4","bandmode":"11g","bandwidth":"HT20","channel":"11","txpower":"20","enabled":true,"wlanstates":{"ceab9273-4bd8-4c4e-b544-87446cc661dd":{"state":"ENABLED","virtual_iface":"phy0-ap0","bssid":"08:C6:B3:0F:0C:20"}}},"radio1":{"frequency":"5","bandmode":"11a","bandwidth":"VHT20","channel":"52","txpower":"20","enabled":true,"wlanstates":{"ceab9273-4bd8-4c4e-b544-87446cc661dd":{"state":"ENABLED","virtual_iface":"phy1-ap0","bssid":"08:C6:B3:0F:0C:21"}}}},"firmware":{"has_update":false,"current_md5":"","version":{"version":"v1.15.2-e","commit":"f3c33c83737d355398d2eed4d6e4eb21e2355430","build":0},"features":["acl","cpeagent","dhcp-cap","ethernet-accounting","firewall","firmware","get","l2-portal-nft","lbs","logging","logupload","network","nftables","openwrt","radius","scanning","snmp","statistic","tc","ubus","uci","umdns","wids","wifi","wired","wired-support","wpa3"]},"wan":{"iface":"lan","proto":"static"},"l2tp_state":{"enabled":true,"host":"one","host_addr":"192.168.12.154","host_tunnel":0,"tunnel_type":"none","local_addr":"192.168.12.159","local_iface":"","local_tunnel":1},"network":{"ipaddr":"192.168.12.159","macaddr":"08:C6:B3:FB:F0:C2","ipaddrs":[{"ipaddr":"192.168.12.159","netmask":"255.255.255."}],"gateway":"192.168.12.1"},"tunnels":null,"net_manual":null,"wifi_manual":null,"manufacturing_data":{"serial_number":"","wlan_mac":""}},"first_connection":0,"last_connection":0,"last_disconnection":0,"config_not_send":false,"latitude":0,"longitude":0,"tag":""}}},"time":"2026-07-17T17:14:29Z","message":"value for upsert"}



### ASSISTANT
**Шаг 13 — Проверка логов сервиса gauth-service**

**Объяснение/Действие:**  
Предоставленный вывод логов `configurer-golang` содержит только штатные сообщения об обмене конфигурацией с точкой доступа (CPE) и не содержит ошибок, связанных с лицензией. 

В архитектуре Wimark ONE за проверку валидности лицензионных ключей, их привязку к аппаратному обеспечению сервера и ограничение функционала часто отвечает сервис `gauth-service`. Нам необходимо проверить его логи на наличие сообщений о невалидности ключа, истечении срока действия или несоответствии аппаратному идентификатору (например, MAC-адресу или UUID виртуальной машины).

Выполните на сервере следующую команду:
```bash
docker logs one-gauth-service-1 2>&1 | grep -iE "license|limit|portal|error|warn" | tail -30
```

**Протокол:**  
- Логи `configurer-golang` не выявили проблем с лицензией (только штатный обмен данными).  
- Ключ лицензии физически присутствует в MongoDB, но система ведет себя так, будто он недействителен.  
- Текущий фокус: выявление ошибок валидации лицензии в логах сервиса `gauth-service`.

**Вопросы:**  
Какой точный вывод даст эта команда? Жду вашего ответа.

### USER

root@wmswifi:/opt/wimark/portal/esia-auth/certs# docker logs one-gauth-service-1 2>&1 | grep -iE "license|limit|portal|error|warn" | tail -30
Error response from daemon: No such container: one-gauth-service-1
root@wmswifi:/opt/wimark/portal/esia-auth/certs#


### ASSISTANT
**Шаг 14 — Глобальный поиск упоминаний лицензии в логах всех контейнеров**

**Объяснение/Действие:**  
Контейнер `one-gauth-service-1` отсутствует в системе (возможно, он называется иначе, не запущен или его функции выполняет другой сервис). Чтобы исключить дальнейшие догадки, выполним автоматизированный поиск по логам *всех* запущенных контейнеров на предмет слов "license" или "лиценз". Это точно укажет, какой именно сервис проверяет, отклоняет или ограничивает ключ.

Выполните на сервере следующую команду:
```bash
for c in $(docker ps --format '{{.Names}}'); do echo "--- $c ---"; docker logs $c 2>&1 | grep -iE "license|лиценз" | tail -3; done
```

**Протокол:**  
- Контейнер `one-gauth-service-1` не найден (`No such container`).  
- Необходимо идентифицировать реальный сервис, отвечающий за валидацию лицензий, через глобальный поиск по логам всех активных контейнеров.  

**Вопросы:**  
Какой вывод даст эта команда? Жду вашего ответа.

### USER
for c in $(docker ps --format '{{.Names}}'); do echo "--- $c ---"; docker logs $c 2>&1 | grep -iE "license|лиценз" | tail -3; done
--- one-nginx-proxy-ssl-1 ---
192.168.12.43 - - [17/Jul/2026:20:32:55 +0000] "POST /api/license HTTP/2.0" 200 280 "https://192.168.12.154/dashboard" "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 YaBrowser/26.6.0.0 Safari/537.36" "-"
192.168.12.43 - - [17/Jul/2026:20:33:09 +0000] "POST /api/license HTTP/2.0" 200 280 "https://192.168.12.154/system" "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 YaBrowser/26.6.0.0 Safari/537.36" "-"
192.168.12.43 - - [17/Jul/2026:20:33:23 +0000] "POST /api/license_log_daily HTTP/2.0" 200 643 "https://192.168.12.154/system" "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 YaBrowser/26.6.0.0 Safari/537.36" "-"
--- one-wimark-web-client-1 ---
--- one-backend-golang-1 ---
{"level":"debug","module":"BACKEND","request_id":"d5362515-29d1-43be-99f8-c22df2908e76","time":"2026-07-17T20:33:23Z","message":"[LogLatency] Func: Marshalling time /api/license_log_daily. Time:170.982µs"}
{"level":"debug","module":"BACKEND","request_id":"d5362515-29d1-43be-99f8-c22df2908e76","time":"2026-07-17T20:33:23Z","message":"[LogLatency] Func: CommonRead /api/license_log_daily. Time: 2.000206ms"}
{"level":"info","module":"BACKEND","request_id":"d5362515-29d1-43be-99f8-c22df2908e76","method":"POST","uri":"/api/license_log_daily","status":200,"latency":2.582689,"time":"2026-07-17T20:33:23Z","message":"request handled"}
--- one-redis-1 ---
--- ai-middleware ---
--- mssql-exporter ---
--- node-exporter ---
--- llama-server ---
--- grafana ---
--- open-webui ---
--- metabase ---
--- portainer ---
--- superset_app ---
--- superset_worker_beat ---
--- superset_worker ---
--- superset_db ---
--- superset_cache ---
--- one-nginx-cors-1 ---
--- one-portal-nginx-1 ---
--- one-radar-export-mw-1 ---
--- one-lbs-daemon-1 ---
--- one-radar-mw-1 ---
--- one-redirect-daemon-1 ---
--- one-rrm-daemon-golang-1 ---
--- one-configurer-golang-1 ---
--- one-statdaemon-golang-1 ---
--- one-analytics-mw-1 ---
--- one-gsnmp-service-1 ---
--- one-mongo-connector-golang-1 ---
--- one-radius-gw-1 ---
--- one-event-monitor-golang-1 ---
--- one-tunnel-manager-1 ---
--- one-ntp-1 ---
--- one-mongo-1 ---
--- one-strongswan-1 ---
--- one-portal-frontend-1 ---
--- one-http-to-smtp-1 ---
--- one-portal-backend-1 ---
--- one-smtp-relay-1 ---
--- one-portal-admin-1 ---
--- one-mosquitto-1 ---
--- one-gapi-service-1 ---
--- one-gproxy-service-1 ---
root@wmswifi:/opt/wimark/portal/esia-auth/certs#

### ASSISTANT
**Шаг 15 — Детальный анализ ответов API лицензий**

**Объяснение/Действие:**  
Запросы к API лицензий проходят успешно (статус 200), но мы не видим содержания ответов. Backend обрабатывает запросы `/api/license` и `/api/license_log_daily`, но в логах нет явных ошибок. 

Теперь нужно проверить, что именно возвращает бэкенд в ответе на запрос лицензии. Для этого включим более детальное логирование или посмотрим на последние логи backend-golang в контексте работы с лицензиями.

Выполните на сервере следующую команду, чтобы увидеть последние 50 строк логов backend-golang без фильтрации:
```bash
docker logs one-backend-golang-1 --tail 50 2>&1 | grep -A 5 -B 5 "license"
```

**Протокол:**  
- Запросы к `/api/license` и `/api/license_log_daily` возвращают статус 200 (успешно).  
- В логах nginx-proxy-ssl и backend-golang нет явных ошибок валидации лицензии.  
- Текущий фокус: получение детальной информации о том, что именно возвращает бэкенд в ответе на запрос лицензии.

**Вопросы:**  
Какой вывод даст эта команда? Жду вашего ответа.

### USER
rts# docker logs one-backend-golang-1 --tail 50 2>&1 | grep -A 5 -B 5 "license"
root@wmswifi:/opt/wimark/portal/esia-auth/certs#
Я прислал скрин он не чем не помежет тебе?

### ASSISTANT
**Шаг 16 — Анализ ответа API и поиск дополнительных коллекций в MongoDB**

**Объяснение/Действие:**  
Скриншот очень полезен: он подтверждает точный текст ошибки в интерфейсе («Осталось лицензия всего на один портал...»). 

Тот факт, что `grep` по логам бэкенда не дал результатов, а nginx показывает статус `200 OK` для запросов `/api/license`, означает, что бэкенд **не считает это ошибкой**. Он успешно отрабатывает запрос, но возвращает фронтенду JSON-ответ, в котором лимит порталов действительно указан как 1 (или ключ не расшифровался, и система откатилась к демо-лимитам).

Чтобы понять, откуда бэкенд берет это ограничение, нам нужно увидеть все доступные коллекции в базе данных `test`, так как мы могли пропустить коллекцию с настройками системы (например, `settings`, `system_config` или `license_state`), где хранится уже расшифрованное или вычисленное состояние лицензии.

Выполните на сервере следующую команду, чтобы получить полный список всех коллекций в базе `test`:
```bash
docker exec one-mongo-1 sh -c 'mongosh --quiet test --eval "db.getCollectionNames()" || mongo --quiet test --eval "db.getCollectionNames()"'
```

**Протокол:**  
- Скриншот подтверждает текст ошибки в UI.  
- Бэкенд отвечает `200 OK` на запросы `/api/license`, явных ошибок (error/warn) в логах нет.  
- Система работает штатно, но с демо-ограничением (1 портал), вероятно, из-за того, что ключ не прошел валидацию или не расшифровался.  
- Текущий фокус: поиск коллекции в MongoDB, которая хранит текущие лимиты системы.

**Вопросы:**  
Какой вывод даст эта команда? Жду вашего ответа.

### USER
docker exec one-mongo-1 sh -c 'mongosh --quiet test --eval "db.getCollectionNames()" || mongo --quiet test --eval "db.getCollectionNames()"'
[
  'countries',
  'lbs_client_data',
  'location',
  'cpe_scan_data',
  'client_stat_info',
  'portal_authorizations',
  'client_session_info',
  'user',
  'operation',
  'radar_visits',
  'clients',
  'lbs_client_probes_testing',
  'cpe_model',
  'radar_probes_raw',
  'stats',
  'client_addr',
  'radar_visits_first',
  'lbs_cpe_info',
  'snmp_point_state',
  'base_location',
  'bss_stat_info',
  'vpn_host',
  'radar_export_result',
  'snmp_walker',
  'cpe_stat_info',
  'lbs_zones',
  'wne_license_key',
  'cpe_session_info',
  'wlans',
  'lbs_client_probes',
  'events',
  'config_rule',
  'ntp_time_settings',
  'redirect_sessions',
  'poll_cpe',
  'client_stats',
  'wlan_stat_info',
  'snmp_general',
  'radar_probes_real',
  'lbs_client_coords',
  'license_log_daily',
  'cpes',
  'troubleshooting'
]
root@wmswifi:/opt/wimark/portal/esia-auth/certs#

### ASSISTANT
**Шаг 17 — Проверка аппаратной привязки лицензии (MAC-адрес)**

**Объяснение/Действие:**  
Список коллекций в MongoDB подтверждает, что отдельных таблиц с "настройками лимитов" нет. Бэкенд успешно отвечает `200 OK` на запросы к `/api/license`, но интерфейс показывает лимит в 1 портал. 

Это классическое поведение системы Wimark, когда лицензионный ключ не проходит проверку привязки к "железу" сервера. Чаще всего это происходит, если изменился MAC-адрес виртуальной машины (например, после клонирования, восстановления из бэкапа, миграции на другой хост или замены виртуального сетевого адаптера). В таком случае система не генерирует критических ошибок в логах, а просто откатывается к базовому демо-лимиту (1 портал).

Проверим текущие MAC-адреса сетевых интерфейсов сервера. Выполните команду:
```bash
ip link show | grep link/ether
```

**Протокол:**  
- Специализированных коллекций с настройками лимитов в MongoDB не обнаружено.  
- Бэкенд валидирует запросы к API лицензий успешно (статус 200), но возвращает лимит 1.  
- Текущая гипотеза: лицензия привязана к MAC-адресу, который не совпадает с оригинальным.

**Вопросы:**  
1. Какой вывод даст эта команда?  
2. Виртуальная машина `wmswifi` недавно клонировалась, восстанавливалась из бэкапа или менялись её сетевые адаптеры?  

Жду вашего ответа.

### USER
 ip link show | grep link/ether
    link/ether 00:15:5d:aa:b6:02 brd ff:ff:ff:ff:ff:ff
    link/ether 4e:4d:0a:a9:81:9a brd ff:ff:ff:ff:ff:ff
    link/ether 56:54:f9:94:38:48 brd ff:ff:ff:ff:ff:ff
    link/ether 22:60:53:be:bc:bf brd ff:ff:ff:ff:ff:ff
    link/ether 2a:19:89:46:15:90 brd ff:ff:ff:ff:ff:ff
    link/ether da:34:92:96:45:d2 brd ff:ff:ff:ff:ff:ff
    link/ether a2:85:ff:d2:7b:8b brd ff:ff:ff:ff:ff:ff
    link/ether 66:b0:a4:da:69:c4 brd ff:ff:ff:ff:ff:ff
    link/ether 46:1c:1d:f9:34:92 brd ff:ff:ff:ff:ff:ff
    link/ether fa:47:a6:34:f3:22 brd ff:ff:ff:ff:ff:ff link-netnsid 0
    link/ether 5a:28:45:d4:38:56 brd ff:ff:ff:ff:ff:ff link-netnsid 1
    link/ether 6a:33:ba:9b:8c:17 brd ff:ff:ff:ff:ff:ff link-netnsid 3
    link/ether 6a:fd:83:45:4d:66 brd ff:ff:ff:ff:ff:ff link-netnsid 5
    link/ether 82:1b:d7:41:f0:3a brd ff:ff:ff:ff:ff:ff link-netnsid 6
    link/ether d6:6a:75:c5:6a:2f brd ff:ff:ff:ff:ff:ff link-netnsid 7
    link/ether c2:2b:b8:bd:6d:9f brd ff:ff:ff:ff:ff:ff link-netnsid 8
    link/ether 1a:14:08:01:cc:ca brd ff:ff:ff:ff:ff:ff link-netnsid 9
    link/ether 96:48:a3:ee:c6:17 brd ff:ff:ff:ff:ff:ff link-netnsid 10
    link/ether fe:b5:56:71:12:e1 brd ff:ff:ff:ff:ff:ff link-netnsid 11
    link/ether ea:0e:8e:74:02:bd brd ff:ff:ff:ff:ff:ff link-netnsid 12
    link/ether fa:f3:04:7a:ed:26 brd ff:ff:ff:ff:ff:ff link-netnsid 13
    link/ether 62:60:9d:51:39:dc brd ff:ff:ff:ff:ff:ff link-netnsid 14
    link/ether aa:3b:92:2f:cb:62 brd ff:ff:ff:ff:ff:ff link-netnsid 15
    link/ether 82:83:45:ed:e0:00 brd ff:ff:ff:ff:ff:ff link-netnsid 17
    link/ether 32:e8:03:a9:f9:68 brd ff:ff:ff:ff:ff:ff link-netnsid 18
    link/ether f2:49:1f:30:22:1a brd ff:ff:ff:ff:ff:ff link-netnsid 19
    link/ether f6:77:b8:93:f9:18 brd ff:ff:ff:ff:ff:ff link-netnsid 20
    link/ether d2:2d:96:61:64:e0 brd ff:ff:ff:ff:ff:ff link-netnsid 21
    link/ether 92:a1:c7:e0:0f:f8 brd ff:ff:ff:ff:ff:ff link-netnsid 22
    link/ether aa:9c:ae:2e:11:4e brd ff:ff:ff:ff:ff:ff link-netnsid 23
    link/ether 16:2e:46:4e:17:f3 brd ff:ff:ff:ff:ff:ff link-netnsid 24
    link/ether 06:6d:5c:88:78:1a brd ff:ff:ff:ff:ff:ff link-netnsid 25
    link/ether 4e:fa:f4:4a:f3:68 brd ff:ff:ff:ff:ff:ff link-netnsid 27
    link/ether 96:63:88:72:be:60 brd ff:ff:ff:ff:ff:ff link-netnsid 28
    link/ether 8a:14:2c:e2:71:70 brd ff:ff:ff:ff:ff:ff link-netnsid 29
    link/ether 0a:d3:98:b9:95:b3 brd ff:ff:ff:ff:ff:ff link-netnsid 4
    link/ether 9a:57:cf:6c:e9:46 brd ff:ff:ff:ff:ff:ff link-netnsid 30
    link/ether be:dc:26:70:0a:ec brd ff:ff:ff:ff:ff:ff link-netnsid 2
    link/ether b2:48:62:74:69:cc brd ff:ff:ff:ff:ff:ff link-netnsid 31
    link/ether 76:55:6f:08:73:cd brd ff:ff:ff:ff:ff:ff link-netnsid 32
    link/ether 02:29:85:52:fa:e2 brd ff:ff:ff:ff:ff:ff link-netnsid 33
    link/ether 42:d4:05:84:ae:33 brd ff:ff:ff:ff:ff:ff link-netnsid 34
    link/ether 9a:aa:d2:0d:29:63 brd ff:ff:ff:ff:ff:ff link-netnsid 36
    link/ether 6a:60:96:b7:ee:1a brd ff:ff:ff:ff:ff:ff link-netnsid 38
    link/ether 2a:b2:1b:92:55:9f brd ff:ff:ff:ff:ff:ff link-netnsid 37
    link/ether 26:c1:bd:93:53:c7 brd ff:ff:ff:ff:ff:ff link-netnsid 39
    link/ether f2:4e:75:64:5b:02 brd ff:ff:ff:ff:ff:ff link-netnsid 16
    link/ether 2a:48:10:0d:22:21 brd ff:ff:ff:ff:ff:ff link-netnsid 35
    link/ether 06:58:b0:8e:fa:8d brd ff:ff:ff:ff:ff:ff link-netnsid 26
    link/ether 56:39:29:bf:70:54 brd ff:ff:ff:ff:ff:ff link-netnsid 40
root@wmswifi:/opt/wimark/portal/esia-auth/certs#
Виртуальная машина wmswifi недавно клонировалась, восстанавливалась из бэкапа или менялись её сетевые адаптеры? - нет! Только перезагрузки, смена числа vCPU

### ASSISTANT
**Шаг 18 — Детальный анализ документа лицензии в MongoDB**

**Объяснение/Действие:**  
Вывод `ip link show` показывает множество MAC-адресов, что типично для хоста с Docker-контейнерами. Первый адрес `00:15:5d:aa:b6:02` — это основной сетевой интерфейс хоста (Hyper-V адаптер). Вы подтвердили, что ВМ не клонировалась и сетевые адаптеры не менялись, только перезагрузки и изменение vCPU.

Поскольку изменение vCPU не влияет на MAC-адрес, проблема, скорее всего, не в аппаратной привязке. Нам нужно более детально изучить документ лицензии в MongoDB — возможно, там есть дополнительные поля (дата окончания, количество порталов, статус), которые мы не увидели при простом выводе.

Выполните на сервере следующую команду для получения полной информации о документе лицензии в формате JSON:
```bash
docker exec one-mongo-1 sh -c 'mongosh --quiet test --eval "JSON.stringify(db.wne_license_key.findOne(), null, 2)" || mongo --quiet test --eval "printjson(db.wne_license_key.findOne())"'
```

**Протокол:**  
- MAC-адрес хоста: `00:15:5d:aa:b6:02` (Hyper-V виртуальный адаптер)
- ВМ не клонировалась, сетевые адаптеры не менялись
- Изменение vCPU не должно влиять на лицензию
- Текущий фокус: получение полной структуры документа лицензии из MongoDB

**Вопросы:**  
Какой вывод даст эта команда? Жду вашего ответа.

### USER
 docker exec one-mongo-1 sh -c 'mongosh --quiet test --eval "JSON.stringify(db.wne_license_key.findOne(), null, 2)" || mongo --quiet test --eval "printjson(db.wne_license_key.findOne())"'
{
  "_id": "wimark_license_key",
  "key": "DuaRW5B6IFlmCkVkqRKZOcCE+hJadD04UDu2a3EqDKXZiznAcYAaS26/cMsjIszq7+9hhqgqHgmDgFJ/x1tRLD4irtqeNB3CqX/r9Z9hMVM2jzl2MMH5Cjg3qwjMUE3vU1ZVyekQwAmspZn5LHEFhrI5b0+a7xFEelkw2rOcOBMWdsCI7KR6DlbnFHOuElXCkHIc7qW0BGsd9LxSTWgkrjLx+vrYiRfZnXllPArc3ZczKg+95nXKfSE9EDkrYQw7NCH//3R+tTXyY71/0kXldYvPvklbLu5wjp4PMBvEUAEaAc714sz0OsQ2Ms4hjbREER4fvkQCzMqS7HE/gX+ukw=="
}
root@wmswifi:/opt/wimark/portal/esia-auth/certs#

### ASSISTANT
**Шаг 19 — Проверка системного идентификатора (machine-id / UUID)**

**Объяснение/Действие:**  
Ключ лицензии в MongoDB хранится в зашифрованном виде и не содержит явных параметров лимита в открытом виде. Бэкенд не выдает явных ошибок в логах, а просто возвращает фронтенду лимит в 1 портал (демо-режим), когда валидация ключа не проходит.

Лицензии Wimark часто привязываются не только к MAC-адресу, но и к системному UUID хоста (`/etc/machine-id` или `product_uuid`). Изменение количества vCPU в некоторых гипервизорах (особенно Hyper-V, на что указывает первый MAC-адрес `00:15:5d...`) иногда может приводить к изменению системного UUID при перезагрузке, если конфигурация виртуальной машины была изменена на уровне гипервизора. Также нельзя исключать, что сам ключ в базе данных был случайно перезаписан или поврежден.

Проверим текущие системные идентификаторы хоста. Выполните на сервере следующие команды:
```bash
cat /etc/machine-id
```
и
```bash
cat /sys/class/dmi/id/product_uuid 2>/dev/null || echo "Недоступно"
```

**Протокол:**  
- Ключ лицензии в MongoDB содержит только зашифрованную строку.  
- Бэкенд работает штатно, но возвращает лимит 1 (признак сбоя валидации ключа).  
- Изменение vCPU могло повлиять на системный UUID, к которому привязана лицензия.  

**Вопросы:**  
1. Какой вывод дали эти две команды?  
2. Есть ли у вас возможность проверить (например, в старых логах, бэкапах или документации), совпадает ли текущая зашифрованная строка ключа в базе данных с той, что вы вводили при первоначальной активации?  

Жду вашего ответа.

### USER
ia-auth/certs# cat /etc/machine-id
e1cd075e902c4b4c9e5c2c1254d3db76
root@wmswifi:/opt/wimark/portal/esia-auth/certs# cat /sys/class/dmi/id/product_uuid 2>/dev/null || echo "Недоступно"
41219b94-67b4-4c4d-8506-bcfae8254fe3
root@wmswifi:/opt/wimark/portal/esia-auth/certs#

### ASSISTANT
**Шаг 20 — Прямой запрос к API лицензии для получения сырого JSON-ответа**

**Объяснение/Действие:**  
Мы получили системные идентификаторы (`machine-id` и `product_uuid`). Поскольку бэкенд не выдает явных ошибок в логи, но возвращает лимит в 1 портал, нам нужно увидеть, *что именно* бэкенд отвечает на запрос лицензии. В сыром JSON-ответе часто содержатся поля вроде `"status": "invalid"`, `"max_portals": 1` или `"reason": "machine_id_mismatch"`, которые точно укажут причину.

Выполните на сервере следующую команду, чтобы сделать прямой запрос к API через локальный Nginx (который проксирует запросы на бэкенд):
```bash
curl -s -k https://127.0.0.1/api/license | jq .
```
*(Если утилита `jq` не установлена, просто выполните `curl -s -k https://127.0.0.1/api/license`)*

**Протокол:**  
- Системный `machine-id`: `e1cd075e902c4b4c9e5c2c1254d3db76`  
- Системный `product_uuid`: `41219b94-67b4-4c4d-8506-bcfae8254fe3`  
- ВМ не клонировалась, менялись только vCPU и были перезагрузки.  
- Текущий фокус: получение точного JSON-ответа от бэкенда о состоянии лицензии для выявления скрытой причины сброса лимита.

**Вопросы:**  
Какой точный вывод даст эта команда? Жду вашего ответа.

### USER
curl -s -k https://127.0.0.1/api/license | jq .
{
  "message": "missing or malformed jwt"
}
root@wmswifi:/opt/wimark/portal/esia-auth/certs# curl -s -k https://127.0.0.1/api/license
{"message":"missing or malformed jwt"}
root@wmswifi:/opt/wimark/portal/esia-auth/certs#

### ASSISTANT
**Шаг 21 — Поиск коллекции с настройками системы или состояния лицензии в MongoDB**

**Объяснение/Действие:**  
Запрос к API без JWT-токена ожидаемо вернул ошибку авторизации (`missing or malformed jwt`), так как это защищенный эндпоинт. Чтобы увидеть реальные лимиты, которые сейчас "видит" система, нам нужно найти в базе данных коллекцию, где хранится *расшифрованное* или текущее состояние лицензии (например, `system_config`, `settings`, `license_state` или похожее). 

Ранее мы видели в `license_log_daily`, что 28 ноября система корректно учитывала 8 CPE. Значит, где-то хранится текущий активный лимит.

Выполните на сервере следующую команду, чтобы отфильтровать список коллекций по ключевым словам:
```bash
docker exec one-mongo-1 sh -c 'mongosh --quiet test --eval "db.getCollectionNames().filter(n => n.includes(\"license\") || n.includes(\"config\") || n.includes(\"setting\") || n.includes(\"system\") || n.includes(\"state\"))"'
```

**Протокол:**  
- Прямой `curl` к `/api/license` требует аутентификации (JWT), поэтому мы не можем получить ответ так просто.  
- Исторические данные (`license_log_daily` от 28.11.2025) показывают, что система ранее корректно работала с 8 CPE.  
- Текущий фокус: найти в MongoDB коллекцию, которая хранит текущие расшифрованные лимиты системы.

**Вопросы:**  
Какой вывод даст эта команда? Жду вашего ответа.

### USER

root@wmswifi:/opt/wimark/portal/esia-auth/certs# docker exec one-mongo-1 sh -c 'mongosh --quiet test --eval "db.getCollectionNames().filter(n => n.includes(\"license\") || n.includes(\"config\") || n.includes(\"setting\") || n.includes(\"system\") || n.includes(\"state\"))"'
[
  'snmp_point_state',
  'wne_license_key',
  'config_rule',
  'ntp_time_settings',
  'license_log_daily'
]
root@wmswifi:/opt/wimark/portal/esia-auth/certs#

### ASSISTANT
**Шаг 22 — Проверка коллекции `config_rule` на наличие лицензионных настроек**

**Объяснение/Действие:**  
Из отфильтрованного списка коллекций мы видим, что специализированных таблиц вроде `system_config` или `license_state` нет. Остаётся коллекция `config_rule`, которая в некоторых версиях Wimark может хранить глобальные правила или переопределения настроек, включая лицензионные квоты.

Давайте проверим, есть ли в ней документы, связанные с лицензиями или лимитами порталов. Выполните на сервере команду:
```bash
docker exec one-mongo-1 sh -c 'mongosh --quiet test --eval "db.config_rule.find({\$or: [{name: /\$regex/i}, {key: /\$regex/i}, {value: /\$regex/i}]}).toArray()" || mongo --quiet test --eval "db.config_rule.find().toArray()"'
```
*(Примечание: если первая часть с regex вызовет ошибку в старой версии mongo, сработает fallback на простой вывод всех правил, их там обычно немного).*

**Протокол:**  
- Отфильтрованный список коллекций не содержит явных таблиц состояния лицензии, кроме уже проверенных `wne_license_key` и `license_log_daily`.  
- Мы проверили логи, переменные окружения, системные идентификаторы (`machine-id`, `product_uuid`).  
- Прямой запрос к API требует JWT-токен.  
- **Важное замечание по контексту:** Мы прошли уже 21 шаг диагностики. Согласно вашим строгим правилам, я должен предупредить: объём накопленной информации становится большим, и риск упустить деталь растёт. Если этот шаг не даст ответа, я настоятельно рекомендую резюмировать всё найденное и, возможно, начать новый чат с чётким дампом текущих данных для свежего взгляда.

**Вопросы:**  
Какой вывод даст эта команда? Жду вашего ответа.

### USER
esia-auth/certs# docker exec one-mongo-1 sh -c 'mongosh --quiet test --eval "db.config_rule.find({\$or: [{name: /\$regex/i}, {key: /\$regex/i}, {value: /\$regex/i}]}).toArray()" || mongo --quiet test --eval "db.config_rule.find().toArray()"'
[]
root@wmswifi:/opt/wimark/portal/esia-auth/certs#

### ASSISTANT
**Шаг 23 — Проверка журналов инициализации бэкенда на предмет демо-режима**

**Объяснение/Действие:**  
Коллекция `config_rule` пуста. Мы исчерпали основные места хранения явных настроек лимитов. 

Текущая гипотеза: бэкенд успешно считывает зашифрованный ключ из `wne_license_key`, но при его проверке (валидации срока действия, аппаратной привязки или целостности) происходит тихий сбой. В результате система не генерирует критическую ошибку (поэтому в логах нет `error`), а просто откатывается к жестко заданному по умолчанию демо-лимиту (1 портал).

Чтобы подтвердить это, нам нужно посмотреть не на запросы в реальном времени, а на момент **запуска** сервиса `backend-golang`. Часто при старте система логирует состояние лицензии: "License valid", "License expired, falling back to demo mode" или "Default limit: 1".

Выполните на сервере следующую команду, чтобы посмотреть первые 50 строк лога бэкенда (момент его инициализации):
```bash
docker logs one-backend-golang-1 2>&1 | head -50 | grep -iE "license|demo|default|valid|init"
```

**⚠️ ВАЖНОЕ ПРЕДУПРЕЖДЕНИЕ О КОНТЕКСТЕ:**  
Мы провели уже 22 шага глубокой диагностики. Объём накопленной информации становится очень большим, и риск того, что важные детали начнут выпадать из моего анализа, возрастает. Если этот шаг не даст явного указания на причину, я настоятельно рекомендую сделать паузу, резюмировать все найденные факты (ключ в Mongo есть, ошибок в логах нет, лимит 1) и, возможно, начать новый чат с этим кратким дампом для "свежего взгляда".

**Протокол:**  
- `config_rule` в MongoDB пуст.  
- Явных файлов или переменных с лимитами не найдено.  
- Гипотеза: тихий сбой валидации ключа приводит к откату на демо-лимит (1 портал) без записи ошибки в лог.  

**Вопросы:**  
1. Какой вывод даст эта команда?  
2. Согласны ли вы с тем, что если этот шаг не даст ответа, нам стоит подвести итог и начать новый чат для избежания потери контекста?

### USER
Составь полный протокол действий, объяснений и контекст чата для перехода в новую сессию

### ASSISTANT
**Шаг 24 — Формирование полного протокола для переноса в новую сессию**

**Объяснение/Действие:**  
В соответствии с правилом контроля контекста, мы фиксируем весь накопленный массив данных в структурированном виде. Скопируйте текст ниже (от «НАЧАЛО ПРОТОКОЛА» до «КОНЕЦ ПРОТОКОЛА») и вставьте его в первое сообщение нового чата. Это позволит новому экземпляру ИИ мгновенно понять архитектуру, историю действий и избежать повторения уже проверенных тупиковых веток.

---
**НАЧАЛО ПРОТОКОЛА ДЛЯ НОВОЙ СЕССИИ**

**1. Архитектура и окружение:**
- Хост: VM `wmswifi`, IP: `192.168.12.154` (Hyper-V, менялось только кол-во vCPU и были перезагрузки, клонирования/замены сетевых карт не было).
- Путь к проекту: `/opt/wimark/one`.
- Управление: Docker Compose.
- Ключевые контейнеры: `one-nginx-proxy-ssl-1`, `one-wimark-web-client-1`, `one-backend-golang-1`, `one-mongo-1`.

**2. Текущая проблема:**
В веб-интерфейсе Qtech (Wimark ONE) отображается предупреждение: "Осталось лицензия всего на один портал (или меньше)". Ожидается, что лицензий должно быть больше (исторически система работала с 8 CPE).

**3. Уже выполненные действия и их результаты (НЕ ПОВТОРЯТЬ):**
- **Сеть Docker:** Исправлена. Контейнер `nginx-proxy-ssl` успешно пересоздан из директории `/opt/wimark/one` и подключен к сети `one_default`. Ошибка DNS `host not found in upstream` устранена. Веб-интерфейс доступен.
- **Поиск файлов лицензий:** Рекурсивный поиск `*licen*`, `*.lic`, `*.key` в `/opt/wimark` и `/opt/wimark/one` не дал результатов (кроме ключа ESIA).
- **Конфигурация:** Файлы `.env` и `docker-compose.yml` проверены. Переменных, задающих лимит порталов или ключ лицензии, в них нет.
- **База данных MongoDB (БД `test`):**
  - Найдена коллекция `wne_license_key`. Содержит 1 документ: `{ _id: 'wimark_license_key', key: 'DuaRW5B6IFlmCkVkqRKZOcCE+...[длинная base64 строка]...' }`.
  - Найдена коллекция `license_log_daily`. Подтверждает, что 28.11.2025 система корректно видела и учитывала 8 подключенных CPE.
  - Коллекция `config_rule` проверена и пуста.
  - Других коллекций с настройками лимитов (`system_config`, `license_state` и т.п.) не существует.
- **Логи контейнеров:** Проверены логи `one-backend-golang-1`, `one-portal-backend-1`, `one-configurer-golang-1` с фильтрацией по `license`, `limit`, `portal`, `error`, `warn`. Явных ошибок валидации лицензии нет. Запросы к `/api/license` и `/api/license_log_daily` возвращают HTTP 200 OK.
- **Прямой API запрос:** `curl -s -k https://127.0.0.1/api/license` возвращает `{"message":"missing or malformed jwt"}` (требуется авторизация).
- **Аппаратная привязка:** Проверены `machine-id` (`e1cd075e902c4b4c9e5c2c1254d3db76`) и `product_uuid` (`41219b94-67b4-4c4d-8506-bcfae8254fe3`). Пользователь подтвердил, что они не менялись намеренно.

**4. Текущая гипотеза:**
Зашифрованный ключ присутствует в БД, но при его проверке бэкендом происходит "тихий" сбой (например, истечение срока, несовпадение скрытого хэша окружения или повреждение ключа). Система не генерирует критическую ошибку в лог, а молча откатывается к жестко заданному демо-лимиту (1 портал).

**5. Задача для новой сессии:**
Предложить следующие конкретные шаги для диагностики причины сброса лимита до 1 портала или способы принудительного обновления/перерегистрации лицензионного ключа в Wimark ONE, учитывая, что стандартные логи молчат.

**КОНЕЦ ПРОТОКОЛА**
---

**Протокол (что зафиксировано):**  
- Полная история диагностики от проблемы с DNS до анализа MongoDB и логов задокументирована.  
- Подготовлен компактный и структурированный контекст для бесшовного продолжения работы в новом чате.  

**Вопросы:**  
Подтвердите, что вы скопировали этот текст. Готов ли я завершить текущую сессию, или у вас есть уточнения перед переходом? (Жду вашего подтверждения «ок» или начала работы в новом чате).
