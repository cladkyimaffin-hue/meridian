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

Секреты: `/opt/wms-constructor-secrets/app.env` (права 600, вне репозитория). Создание учётной записи БД `constructor_ro`
выполнял администратор БД: `CREATE LOGIN` + `CREATE USER` + роли `db_datareader` и `db_denydatawriter` в `LV_MERIDIAN` и `MRDN_Exchange`.
