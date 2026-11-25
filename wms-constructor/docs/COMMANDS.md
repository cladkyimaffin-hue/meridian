# Команды (классификация: [R] чтение, [W] запись/изменение, [D] удаление/остановка)

Выполнять на сервере `wmssql-analytics` под пользователем `user` в папке `/opt/meridian/wms-constructor`.

| Класс | Команда | Что делает / откат |
|---|---|---|
| [R] | `curl -s http://<адрес сервера>:8080/healthz` | проверка живости, число запросов |
| [R] | `docker ps --filter name=wms-constructor` | состояние контейнера |
| [R] | `docker logs --tail 50 wms-constructor` | журнал обращений и ошибок |
| [R] | `git status -sb` и `git log --oneline -5` (в `/opt/meridian`) | состояние репозитория |
| [R] | `docker run --rm --user root -v "$PWD":/work:ro -w /work wms-constructor:dev sh -c 'pip install -q -r requirements-dev.txt; python -m pytest -p no:cacheprovider -q'` | тесты (27), репозиторий смонтирован только для чтения |
| [W] | `docker compose up -d --build` | пересборка и запуск контейнера; откат: `git checkout` нужной версии и снова сборка |
| [W] | `printf 'BIND_ADDR=<адрес сервера>\n' > .env` | адрес публикации порта (в git не попадает, права 600) |
| [W] | `sudo ufw allow from <подсеть>/24 to any port 8080 proto tcp` | правило файрвола (если порт не открывается); откат: `sudo ufw delete allow from <подсеть>/24 to any port 8080 proto tcp` |
| [W] | `git add <файлы> && git commit -m "..." && git push origin main` | фиксация и отправка в GitHub (репозиторий публичный: перед push проверять отсутствие секретов) |
| [W] | `python tools/md_to_yaml.py ...` (см. `docs/CONVERTER.md`) | перезаписывает `queries/*.yaml` |
| [D] | `docker compose down` | остановить и удалить контейнер (образ и данные остаются) |
| [W] | `cd metabase && docker compose up -d` | запуск Metabase и PostgreSQL (секреты: `/opt/wms-constructor-secrets/metabase.env`, вне репозитория; порт 3001, адрес в `metabase/.env`) |
| [R] | `docker logs --tail 50 metabase` | журнал Metabase |
| [W] | на сервере-источнике `docker save <образ> \| gzip \| ssh -i <врем. ключ> user@<приёмник> "cat > файл"`, на приёмнике `docker load -i файл` | перенос образа при медленном Docker Hub; сверить sha256 архива и ID образа; временный ключ удалить с обоих серверов |
| [D] | `cd metabase && docker compose down -v` | остановить Metabase и УДАЛИТЬ его данные (том PostgreSQL: все сохранённые отчёты) |
| [W] | `cd superset && docker compose up -d` | запуск Superset и его PostgreSQL (секреты: `/opt/wms-constructor-secrets/superset.env`; адрес порта: `superset/.env`) |
| [W] | `SUPERSET_URL=http://<адрес>:8088 python3 superset/pilot_tasks.py --rebuild` | пересоздать пробный дашборд «Задачи склада» (старый удаляется) |
| [D] | `cd superset && docker compose down -v` | остановить Superset и УДАЛИТЬ его данные (внутренняя база: все наборы данных, диаграммы, дашборды) |
| [R] | `METABASE_URL=http://<адрес>:3001 python3 metabase/hide_unused_tables.py` | пробный прогон: сколько таблиц Metabase останется видимыми (ключ API из файла секретов) |
| [W] | `... hide_unused_tables.py --apply` / `--unhide-all --apply` | скрыть неиспользуемые таблицы / вернуть видимость всем (обратимо) |
| [W] | `METABASE_URL=http://<адрес>:3001 python3 metabase/mark_sensitive_columns.py` (`--revert` снимает) | пометить чувствительные столбцы «не показывать» |
| [W] | `METABASE_URL=http://<адрес>:3001 python3 metabase/build_content.py --rebuild` | создать коллекции, модели, карточки, тахометры, дашборды и публичные ссылки из `queries/*.yaml`; прежняя корневая коллекция уходит в корзину Metabase (ручные правки в ней теряются из рабочей области; восстановимо из корзины); ссылки пишутся в `/opt/wms-constructor-secrets/metabase-public-links.txt` |

Секреты: `/opt/wms-constructor-secrets/app.env` (права 600, вне репозитория). Создание учётной записи БД `constructor_ro`
выполнял администратор БД: `CREATE LOGIN` + `CREATE USER` + роли `db_datareader` и `db_denydatawriter` в `LV_MERIDIAN` и `MRDN_Exchange`.
