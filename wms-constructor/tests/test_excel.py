import io
import zipfile

from app.excel import build_xlsx


def test_formulas_are_not_executed():
    evil = ["=1+1", "+1", "-1", "@SUM(A1)", "=HYPERLINK(\"http://x\")"]
    data = build_xlsx("Тест", ["Колонка"], [(v,) for v in evil], [("Запрос", "=cmd")])
    z = zipfile.ZipFile(io.BytesIO(data))
    sheet = z.read("xl/worksheets/sheet1.xml").decode()
    sheet2 = z.read("xl/worksheets/sheet2.xml").decode()
    shared = z.read("xl/sharedStrings.xml").decode()
    assert "<f>" not in sheet and "<f>" not in sheet2     # формул нет
    assert "=1+1" in shared and "=cmd" in shared           # хранятся как текст
