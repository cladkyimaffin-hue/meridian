#!/usr/bin/env python3
"""Сборка русских переводов интерфейса Superset внутри контейнера.

Почему это нужно: в образе лежит только исходник перевода
(`/app/superset/translations/ru/LC_MESSAGES/messages.po`), а Superset читает:
  * строки интерфейса (React) — `messages.json`, отдаётся по
    `/superset/language_pack/<lang>/`;
  * серверные строки — скомпилированный `messages.mo` (Flask-Babel).
Пока их нет, даже при `BABEL_DEFAULT_LOCALE = "ru"` на странице остаются
английские подписи «Filters and controls», «No filter», «Apply filters».

Формат messages.json — НЕ плоский словарь, а gettext-структура i18next:

    {"domain": "superset",
     "locale_data": {"superset": {
         "": {"domain": "superset", "lang": "ru", "plural_forms": "..."},
         "No filter": ["Без фильтрации"], ...}}}

Фронтенд читает его как `locale_data[domain][msgid][0]`; плоский словарь
приводит к «Cannot read properties of undefined (reading '')» и откату на
английский (проверено в консоли браузера). Тот же формат даёт штатный
`po2json`, которого в образе нет, — поэтому структура собирается здесь.

`pybabel compile` не годится: в поставляемом .po есть 13 записей с
несовместимыми подстановками (например «Duplicate folder name: %s» переведено
как «Дублировать роль %(name)s»), и компилятор отказывается собирать файл
целиком. Поэтому .mo пишется через babel напрямую, с `abort_invalid=False`:
битые записи пропускаются, остальные попадают в каталог.

Скрипт идемпотентен: файлы собираются из .po при каждом запуске.

Запуск на wmssql-analytics:
    docker cp build_translations.py superset:/tmp/
    docker exec -u root superset python /tmp/build_translations.py
    docker restart superset
"""

import ast
import json
import os
import sys

BASE = "/app/superset/translations"
LOCALES = ("ru",)
PROBES = ("No filter", "Apply filters", "Filters and controls", "Clear all", "Filters")


def parse_po(path):
    """Разбирает .po без polib (в образе его нет).

    Возвращает {msgid: msgstr} для переведённых непустых строк. Plural-формы и
    записи с контекстом в словарь интерфейса не попадают: i18next работает с
    простыми парами «строка → строка», а серверные plural-формы берёт из .mo.
    """
    entries = {}
    msgid, msgctxt, msgstr = None, None, None
    mode = None

    def flush():
        nonlocal msgid, msgctxt, msgstr
        # контекстные записи не смешиваем с обычными: ключ в i18next без контекста
        if msgid and msgstr and not msgctxt:
            entries[msgid] = msgstr
        msgid, msgctxt, msgstr = None, None, None

    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n")
            if not line.strip():
                flush()
                mode = None
                continue
            if line.startswith("#"):
                continue
            if line.startswith("msgctxt "):
                flush()
                msgctxt = ast.literal_eval(line[8:].strip())
                mode = "ctxt"
            elif line.startswith("msgid "):
                msgid = ast.literal_eval(line[6:].strip())
                mode = "id"
            elif line.startswith("msgid_plural "):
                mode = "plural"
            elif line.startswith("msgstr "):
                msgstr = ast.literal_eval(line[7:].strip())
                mode = "str"
            elif line.startswith("msgstr["):
                mode = "plural"
            elif line.startswith('"'):
                piece = ast.literal_eval(line.strip())
                if mode == "id":
                    msgid = (msgid or "") + piece
                elif mode == "str":
                    msgstr = (msgstr or "") + piece
                elif mode == "ctxt":
                    msgctxt = (msgctxt or "") + piece
    flush()
    return entries


def compile_mo(po, mo):
    """Собирает .mo, пропуская записи с несовместимыми подстановками."""
    from babel.messages.mofile import write_mo
    from babel.messages.pofile import read_po

    with open(po, "rb") as src:
        catalog = read_po(src, locale="ru", abort_invalid=False)
    with open(mo, "wb") as dst:
        write_mo(dst, catalog)
    return len(catalog)


def gettext_pack(locale, entries):
    """Собирает messages.json в формате i18next/gettext (как po2json)."""
    return {
        "domain": "superset",
        "locale_data": {
            "superset": {
                "": {
                    "domain": "superset",
                    "lang": locale,
                    "plural_forms": "nplurals=3; plural=(n%10==1 && n%100!=11 ? 0 : "
                                    "n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2)",
                },
                # i18next ждёт МАССИВ вариантов: [перевод] (+ формы множественного)
                **{msgid: [msgstr] for msgid, msgstr in entries.items()},
            }
        },
    }


def main():
    for locale in LOCALES:
        msgs = os.path.join(BASE, locale, "LC_MESSAGES")
        po = os.path.join(msgs, "messages.po")
        mo = os.path.join(msgs, "messages.mo")
        js = os.path.join(msgs, "messages.json")
        if not os.path.exists(po):
            sys.exit(f"нет файла перевода: {po}")

        entries = parse_po(po)
        with open(js, "w", encoding="utf-8") as f:
            json.dump(gettext_pack(locale, entries), f, ensure_ascii=False, sort_keys=True)
        total = compile_mo(po, mo)

        print(f"{locale}: словарь интерфейса {len(entries)} строк "
              f"(messages.json {os.path.getsize(js)} Б), "
              f"каталог .mo {total} записей ({os.path.getsize(mo)} Б)")
        for probe in PROBES:
            print(f"    {probe!r} -> {entries.get(probe, '— нет перевода —')}")


if __name__ == "__main__":
    main()
