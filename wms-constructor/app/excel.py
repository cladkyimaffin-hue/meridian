"""Выгрузка в Excel. Все текстовые значения пишутся как строки: формулы из данных не выполняются."""
from __future__ import annotations

import datetime as dt
import decimal
import io
import math
import re

import xlsxwriter

_ILLEGAL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def _clean(s: str) -> str:
    return _ILLEGAL.sub("", s)


def _sheet_name(title: str, fallback: str = "Данные") -> str:
    name = re.sub(r"[\[\]:*?/\\]", " ", title).strip().strip("'") or fallback
    return name[:31]


def build_xlsx(title: str, columns: list[str], rows: list[tuple], info: list[tuple[str, str]]) -> bytes:
    bio = io.BytesIO()
    wb = xlsxwriter.Workbook(
        bio,
        {
            "in_memory": True,
            "strings_to_formulas": False,
            "strings_to_numbers": False,
            "strings_to_urls": False,
            "remove_timezone": True,
        },
    )
    head = wb.add_format({"bold": True, "bg_color": "#E7EDF5", "border": 1, "text_wrap": True, "valign": "top"})
    f_dt = wb.add_format({"num_format": "yyyy-mm-dd hh:mm:ss"})
    f_d = wb.add_format({"num_format": "yyyy-mm-dd"})

    data_name = _sheet_name(title)
    ws = wb.add_worksheet(data_name)
    widths = [min(max(len(c), 8), 60) for c in columns]
    for c, name in enumerate(columns):
        ws.write_string(0, c, _clean(name), head)

    for r, row in enumerate(rows, start=1):
        for c, v in enumerate(row):
            if v is None:
                continue
            if isinstance(v, bool):
                ws.write_boolean(r, c, v)
            elif isinstance(v, (int, float, decimal.Decimal)):
                num = float(v)
                if math.isfinite(num):
                    ws.write_number(r, c, num)
                else:
                    ws.write_string(r, c, str(v))
            elif isinstance(v, dt.datetime):
                ws.write_datetime(r, c, v, f_dt)
            elif isinstance(v, dt.date):
                ws.write_datetime(r, c, dt.datetime.combine(v, dt.time()), f_d)
            elif isinstance(v, (bytes, bytearray, memoryview)):
                ws.write_string(r, c, "<двоичные данные>")
            else:
                s = _clean(str(v))
                ws.write_string(r, c, s)
                if r <= 200:
                    widths[c] = min(max(widths[c], len(s)), 60)
    for c, w in enumerate(widths):
        ws.set_column(c, c, w + 2)
    if columns:
        ws.autofilter(0, 0, len(rows), len(columns) - 1)
    ws.freeze_panes(1, 0)

    pname = "Параметры" if data_name != "Параметры" else "Параметры выгрузки"
    wp = wb.add_worksheet(pname)
    wp.set_column(0, 0, 28)
    wp.set_column(1, 1, 80)
    for i, (k, v) in enumerate(info):
        wp.write_string(i, 0, _clean(k), head)
        wp.write_string(i, 1, _clean(v))
    wb.close()
    return bio.getvalue()
